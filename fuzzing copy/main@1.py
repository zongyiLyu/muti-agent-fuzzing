import os
import copy
import json
import argparse
import tqdm

from session import Session
from datasets import load_dataset, load_from_disk
from utils import prompt_split_humaneval, find_method_name, code_split, build_test_method
from evaluate_result import evaluate_all
from main_mutate import mutate_all

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', type=str, default='humaneval')
parser.add_argument('--lang', type=str, default='python')
parser.add_argument('--output_path', type=str, default='output.jsonl')
parser.add_argument('--input_path', type=str, default='data/HumanEval_test_case_ET.jsonl')
parser.add_argument('--mutate_method', type=str, default='expand_1')

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

    # load dataset
    INPUTPATH=args.input_path
    loaded_dataset=[]
    with open(INPUTPATH, 'r') as f:
        # 导入输出
        loaded_dataset = [json.loads(line) for line in f]
        print(len(loaded_dataset))


    if '%' in args.mutate_method:
        mutate_methods=args.mutate_method.split('%')
    else:
        mutate_methods=[args.mutate_method]


    no_pass=[]
    twice=[]
    finally_pass=0
    need_second_round=0
    # need_second_round: 3
    # finally_pass: 162
    pass_1 = []
    scores=[]
    already_finish=set()
    last_dataset = ''
    fail_list=[]
    threshold=3*len(mutate_methods)+1
    for i in range(threshold):
        print('----'*10+'round: '+str(i)+'---'*10)

        cur_mutate_method=mutate_methods[i%len(mutate_methods)-1]
        if i!=0 :
            print('---'*10+'Begin Mutating: '+cur_mutate_method+'---'*10)
            last_dataset = loaded_dataset
            mutated_output_path=args.output_path+cur_mutate_method+'_round_'+str(i)+'.jsonl'
            loaded_dataset = mutate_all(loaded_dataset,mutated_output_path,cur_mutate_method)

        handled_solutions=[]
        code_output_path=args.output_path+'code'+'_round_'+str(i)+'.jsonl'
        # if not os.path.exists(code_output_path):
        #     os.mkdir(code_output_path)
        with open(code_output_path, 'w+') as f:
            for idx, task in enumerate(loaded_dataset):
                
                # print('***'*40)
                print('handling task: '+str(idx))
                
                p,q=finally_pass,need_second_round
                if args.dataset == 'humaneval':
                    method_name = task['entry_point']
                    before_func = prompt_split_humaneval(task['prompt'],method_name)
                    intent = task['prompt']
                    # print('prompt:')
                    # print(intent)
                    
                    test = task['test']

                try:
                    # 进行分工流程在这里，输入了prompt为intent
                    session = Session(TEAM, ANALYST, PYTHON_DEVELOPER, TESTER,requirement=intent, model=args.model, majority=args.majority, 
                                    max_tokens=args.max_tokens, temperature=args.temperature, 
                                    top_p=args.top_p, max_round=args.max_round, before_func=before_func)
                    code, session_history, need_second_round, finally_pass= session.run_session(need_second_round,finally_pass)
                    if p!=finally_pass:
                        no_pass.append(idx)
                    if q!=need_second_round:
                        twice.append(idx)



                
                except RuntimeError as e:
                    print(str(e))
                    print("task-%d fail"%(task['task_id']))
                    fail_list.append(task['task_id'])
                    continue

                
                # print('need_second_round: '+str(need_second_round))
                # print('finally_pass: '+str(finally_pass))

                # if  code == "error":
                #     continue

                entry_point = find_method_name(code)
                
                solution = {
                    'task_id': task['task_id'],
                    'prompt': task['prompt'],
                    'test': test,
                    'entry_point': entry_point,
                    'completion': code,
                    'session_history': session_history,
                    # 'no_pass':no_pass,
                    # 'need_second_chance':twice
                }
                
                
                f.write(json.dumps(solution) + '\n')
                f.flush()



                handled_solutions.append(solution)
                # if idx>2:
                #     break
        # print('solutions:')
        # print(handled_solutions)
        ans,score=evaluate_all(handled_solutions,args.dataset,args.mutate_method)
        pass_1.append(ans)
        scores.append(score)
        # [0.8125] [1.0, 1.0, 0.165, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0101, 1.0, 1.0, 0.0, 0.0342, 0.6214, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2529, 1.0, 1.0, 1.0, 1.0, 1.0]
        # [0.8125] [1.0, 0.0145, 0.165, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0088, 0.4017, 0.6214, 1.0, 1.0, 1.0, 1.0, 1.0, 0.4923, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2529, 1.0, 1.0, 1.0, 1.0, 1.0]
        print(ans,score,score.count(1)/len(score))


        # if i>0:
        #     last_score = scores[-2]
        #     cur_score = scores[-1]
        #     for j in range(len(last_score)):
        #         if last_score[j]<cur_score[j]:
        #             # print('not better!')
        #             loaded_dataset[j]=last_dataset[j]


            
        # print(pass_1)
        # print(scores)        
        # print(no_pass)
        # print(twice)



# SystemLog: [2024-11-04 20:53:11][evaluate.evaluation][INFO] - {'pass@1': 1.0}
# [1.0] [1.0, 1.0, 0.165, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] 0.9166666666666666
# SystemLog: [2024-11-04 20:55:02][evaluate.evaluation][INFO] - {'pass@1': 1.0}
# [1.0] [1.0, 1.0, 0.165, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] 0.9166666666666666