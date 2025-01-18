import os
import copy
import json
import argparse
import tqdm
import numpy as np
import time
import random
import torch
import torch.nn.functional as F
os.environ["TOKENIZERS_PARALLELISM"] = "false"
from session import Session
from datasets import load_dataset, load_from_disk
from utils import prompt_split_humaneval, find_method_name, code_split, build_test_method
from evaluate_result import evaluate_all,evaluate_one,evaluate_one_MBPP
from main_mutate import mutate_all,mutate_one
from collections import defaultdict
from concurrent.futures import as_completed, ProcessPoolExecutor
import multiprocessing

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', type=str, default='humaneval')
parser.add_argument('--lang', type=str, default='python')
parser.add_argument('--output_path', type=str, default='output.jsonl')
parser.add_argument('--input_path', type=str, default='data/HumanEval_test_case_ET.jsonl')
parser.add_argument('--mutate_method', type=str, default='random')
parser.add_argument('--dataset_type', type=str, default='HumanEval')
parser.add_argument('--output_file_name', type=str, default='test')
parser.add_argument('--num_round', type=int, default=3)
parser.add_argument('--num_generate', type=int, default=1)
parser.add_argument('--do_fuzz', type=bool, default=True)
parser.add_argument('--save_seed', type=int , default=1)
parser.add_argument('--recover', type=int, default=0)
parser.add_argument('--reward_ratio', type=int, default=1)
parser.add_argument('--calc_analyst', type=int, default=0)
parser.add_argument('--calc_final_result', type=int, default=1)
parser.add_argument('--save_all_seed', type=int, default=0)
parser.add_argument('--clean_data', type=int, default=0)
parser.add_argument('--set_threshold_analyst', type=int, default=1)
parser.add_argument('--calc_relative_reward', type=int, default=1)

parser.add_argument('--only_consider_passed_cases', type=int, default=0)
parser.add_argument('--alpha', type=float, default=0.25)


parser.add_argument('--signature', action='store_true')
parser.add_argument('--model', type=str, default='gpt-3.5-turbo-0301')
parser.add_argument('--max_round', type=int, default=2)

parser.add_argument('--max_tokens', type=int, default=512) 
parser.add_argument('--majority', type=int, default=1)
parser.add_argument('--temperature', type=float, default=0.0)
parser.add_argument('--top_p', type=float, default=0.95)

parser.add_argument('--fail_list', type=list, default=[])
parser.add_argument('--append', action='store_true')
parser.add_argument('--verbose', action='store_true')
parser.add_argument("--timeout", type=float, default=10, help="how many seconds to wait during execution for each test case")
args = parser.parse_args()

if __name__ == '__main__':
    from roles.rule_descriptions_actc import TEAM, ANALYST, PYTHON_DEVELOPER, TESTER

    
    
    initial_output_path=args.output_path
    args.output_path=initial_output_path+'results-'+args.output_file_name+'/'
    x=2
    while os.path.exists(args.output_path):
        args.output_path=initial_output_path+'results-'+args.output_file_name+'_'+str(x)+'/'
        x+=1
    os.mkdir(args.output_path)
    print(args.output_path)
    print(args)




    # load dataset
    INPUTPATH=args.input_path
    loaded_dataset=[]
    with open(INPUTPATH, 'r') as f:
        # 导入输出
        loaded_dataset = [json.loads(line) for line in f]
    

    prompt_nodes=[]
    passAt10s=[]

    initial_seed = loaded_dataset
    initial_seed_num=len(loaded_dataset)


    # text, code, task_id, test_list, entry_point

    fail_list = []
    output_path = args.output_path + 'MBPP_all_result.jsonl'
    with open(output_path, 'w+') as f:
        for idx,task in enumerate(loaded_dataset):
            codes=[]
            session_historys=[]
            intent=task['text']
            method_name = task['entry_point']
            before_func = ''
            intent = 'def {}(): \'\'\''.format(method_name)+ intent + '\'\'\''
            print(intent)
            need_second_round, finally_pass=0,0
            try:
                # 进行分工流程在这里，输入了prompt为intent
                futures = []
                with ProcessPoolExecutor() as executor:
                    for cnt in range(args.num_generate):
                        session = Session(TEAM, ANALYST, PYTHON_DEVELOPER, TESTER,requirement=intent, model=args.model, majority=args.majority, 
                                    max_tokens=args.max_tokens, temperature=args.temperature, 
                                    top_p=args.top_p, max_round=args.max_round, before_func=before_func)
                        future= executor.submit(session.run_session,need_second_round,finally_pass)
                        futures.append(future)
                for _, future in enumerate(as_completed(futures)):
                    # print(future.result())
                    code, session_history, need_second_round, finally_pass=future.result()
                    codes.append(code)
                    session_historys.append(session_history)


            except RuntimeError as e:
                print(str(e))
                print("task-%d fail"%(task['task_id']))
                fail_list.append(task['task_id'])
                continue
            

            task['completion']=code
            task['completions']=codes
            task['session_history']=session_history
            task['session_historys']=session_historys
            
            # score是所有生成的代码在test case上的平均得分
            # passes是通过所有测试的代码数量（1-10）
            score, passes,passAt1, passAt10= evaluate_one_MBPP(task,args.num_generate)
            # mutated_seed.score=score

            task['pass'] = passAt10
            task['round']=idx
            entry_point = find_method_name(code)

            passAt10s.append(passAt10)
                    
            
            
            f.write(json.dumps(task) + '\n')
            f.flush()
            if idx%100==0:
                print('current round: '+str(idx))
                print('current pass@10: '+ str(passAt10s.count(True)/len(passAt10s)))
    print('-'*100)
    print('final_result: '+str(passAt10s.count(True)/len(passAt10s)))
       

    

        
    

