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
parser.add_argument('--num_round', type=int, default=3)
parser.add_argument('--num_generate', type=int, default=1)
parser.add_argument('--do_fuzz', type=bool, default=True)

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


    cur_score=[1.0, 1.0, 0.165, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.6929, 0.0664, 0.0315, 0.7325, 0.9915, 1.233, 1.0, 1.0, 1.0, 1.0, 0.8248, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9587, 0.3276, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.669, 1.0, 0.9921, 0.5084, 1.0, 0.1098, 1.0, 1.0, 0.1143, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0992, 1.0, 1.0, 0.9906, 0.7278, 0.9849, 0.9765, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9452, 0.8012, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.8964, 0.8815, 0.2639, 1.0, 1.0, 0.97, 0.4123, 1.0, 0.0, 0.6038, 1.0, 0.9826, 0.7172, 0.9952, 0.7, 0.6517, 0.2897, 1.0, 0.2692, 0.9925, 0.8853, 0.0074, 0.9074, 0.96, 0.9054, 0.4987, 0.7928, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9041, 0.2708, 0.9189, 0.4534, 0.9516, 1.0, 0.8116, 1.0, 0.0031, 1.0, 1.0, 0.7069, 0.9359, 0.2113, 1.0, 0.9121, 1.0, 0.8671, 0.2547, 0.7, 0.9496, 0.9182, 0.0721, 0.0, 0.9118, 0.7, 1.0, 0.9788, 0.8396, 1.0, 0.5839, 0.0977, 1.0, 0.8016, 1.0, 0.159, 1.0, 0.9977, 0.3962, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9463, 1.0, 1.0, 0.854, 0.9798, 1.0, 1.0, 1.0, 0.0894, 0.7062, 1.0, 1.0, 0.0917]


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
    threshold=args.num_round*len(mutate_methods)
    print(threshold)
    for i in range(threshold):
        print('----'*10+'round: '+str(i)+'---'*10)

        cur_mutate_method=mutate_methods[i%len(mutate_methods)]
        print(args.do_fuzz)
        if args.do_fuzz:
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
                codes=[]
                session_historys=[]
                if args.dataset == 'humaneval':
                    method_name = task['entry_point']
                    before_func = prompt_split_humaneval(task['prompt'],method_name)
                    intent = task['prompt']
                    # print('prompt:')
                    # print(intent)
                    
                    test = task['test']

                try:
                    # 进行分工流程在这里，输入了prompt为intent
                    for cnt in range(args.num_generate-1):
                        session = Session(TEAM, ANALYST, PYTHON_DEVELOPER, TESTER,requirement=intent, model=args.model, majority=args.majority, 
                                    max_tokens=args.max_tokens, temperature=args.temperature, 
                                    top_p=args.top_p, max_round=args.max_round, before_func=before_func)
                        code, session_history, need_second_round, finally_pass= session.run_session(need_second_round,finally_pass)
                        codes.append(code)
                        session_historys.append(session_history)

                    session = Session(TEAM, ANALYST, PYTHON_DEVELOPER, TESTER,requirement=intent, model=args.model, majority=args.majority, 
                                    max_tokens=args.max_tokens, temperature=args.temperature, 
                                    top_p=args.top_p, max_round=args.max_round, before_func=before_func)
                    code, session_history, need_second_round, finally_pass= session.run_session(need_second_round,finally_pass)
                    if p!=finally_pass:
                        no_pass.append(idx)
                    if q!=need_second_round:
                        twice.append(idx)
                    
                    codes.append(code)
                    session_historys.append(session_history)
                    
                        



                
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
                    'completions':codes,
                    'session_history': session_history,
                    'session_historys': session_historys,
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
        ans,avg_score,score,avg_passes,total_passes=evaluate_all(handled_solutions,args.dataset,args.output_path,args.num_generate,i)
        pass_1.append(ans)
        scores.append(score)
        # [0.8125] [1.0, 1.0, 0.165, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0101, 1.0, 1.0, 0.0, 0.0342, 0.6214, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2529, 1.0, 1.0, 1.0, 1.0, 1.0]
        # [0.8125] [1.0, 0.0145, 0.165, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0088, 0.4017, 0.6214, 1.0, 1.0, 1.0, 1.0, 1.0, 0.4923, 1.0, 1.0, 1.0, 1.0, 1.0, 0.2529, 1.0, 1.0, 1.0, 1.0, 1.0]
        print(ans,avg_score)
        print(avg_passes)
        print(score)
        print(total_passes)
        


        if i>0 :
            last_score = scores[-2]
            cur_score = scores[-1]
            for j in range(len(last_score)):
                # 如果本次得分大于上一次得分，就保留上一次的得分
                if last_score[j]<cur_score[j]:
                    # print('not better!')
                    loaded_dataset[j]=last_dataset[j]


            
        # print(pass_1)
        # print(scores)        
        # print(no_pass)
        # print(twice)



# SystemLog: [2024-11-04 20:53:11][evaluate.evaluation][INFO] - {'pass@1': 1.0}
# [1.0] [1.0, 1.0, 0.165, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] 0.9166666666666666
# SystemLog: [2024-11-04 20:55:02][evaluate.evaluation][INFO] - {'pass@1': 1.0}
# [1.0] [1.0, 1.0, 0.165, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] 0.9166666666666666