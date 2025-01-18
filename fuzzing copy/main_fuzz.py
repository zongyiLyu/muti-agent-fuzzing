import os
import copy
import json
import argparse
import tqdm
import numpy as np
import time

from session import Session
from datasets import load_dataset, load_from_disk
from utils import prompt_split_humaneval, find_method_name, code_split, build_test_method
from evaluate_result import evaluate_all,evaluate_one
from main_mutate import mutate_all,mutate_one
from collections import defaultdict

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

class PromptNode:
    def __init__(self,
                 solution,
                 score=0,
                 passes=0,
                 parent: 'PromptNode' = None):

        self.solution = solution


        self.visited_num = 0
        self.score=score
        self.passes=passes
        self.reward_score=0
        

        self.parent: 'PromptNode' = parent
        self.child: 'list[PromptNode]' = []
        self.level: int = 0 if parent is None else parent.level + 1

        self._index: int = None

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, index: int):
        self._index = index
        if self.parent is not None:
            self.parent.child.append(self)

    # @property
    # def num_jailbreak(self):
    #     return sum(self.results)

    # @property
    # def num_reject(self):
    #     return len(self.results) - sum(self.results)

    # @property
    # def num_query(self):
    #     return len(self.results)




class MCTSExploreSelectPolicy:
    def __init__(self,  initial_seed_len=0,ratio=0.5, alpha=0.1, beta=0.2):

        self.step = 0
        self.mctc_select_path: 'list[PromptNode]' = []
        self.last_choice_index = None
        self.rewards = []
        self.initial_seed_len= initial_seed_len
        self.ratio = ratio  # balance between exploration and exploitation
        self.alpha = alpha  # penalty for level
        self.beta = beta   # minimal reward after penalty

    def select(self,prompt_nodes) -> PromptNode:
        self.step += 1
        if len(prompt_nodes) > len(self.rewards):
            self.rewards.extend(
                [0 for _ in range(len(prompt_nodes) - len(self.rewards))])

        self.mctc_select_path.clear()
        # 第一步一定是在初始的种子里选
        initial_prompts_nodes = prompt_nodes[:self.initial_seed_len]
        cur = max(
            initial_prompts_nodes,
            key=lambda pn:
            self.rewards[pn.index] / (pn.visited_num + 1) +
            self.ratio * np.sqrt(2 * np.log(self.step) /
                                 (pn.visited_num + 0.01))
        )
        self.mctc_select_path.append(cur)

        while len(cur.child) > 0:
            if np.random.rand() < self.alpha:
                break
            cur = max(
                cur.child,
                key=lambda pn:
                self.rewards[pn.index] / (pn.visited_num + 1) +
                self.ratio * np.sqrt(2 * np.log(self.step) /
                                     (pn.visited_num + 0.01))
            )
            self.mctc_select_path.append(cur)

        for pn in self.mctc_select_path:
            pn.visited_num += 1

        self.last_choice_index = cur.index
        return cur

    def update(self, prompt_nodes: 'list[PromptNode]',all_prompt_nodes):
        # succ_num = sum([prompt_node.num_jailbreak
        #                 for prompt_node in prompt_nodes])

        # 新的得分
        succ_num = sum([prompt_node.reward_score
                        for prompt_node in prompt_nodes])
        
        print('last_choice_index:'+ str(self.last_choice_index))
        print('reward: '+str(succ_num))
        # print(self.mctc_select_path)
        last_choice_node = all_prompt_nodes[self.last_choice_index]
        for prompt_node in reversed(self.mctc_select_path):
            # 这里reward的计算其实是： jailbreak的概率 * （1-深度*0.1）
            reward = succ_num / len(prompt_nodes)
            self.rewards[prompt_node.index] += reward * \
                max(self.beta, (1 - 0.1 * last_choice_node.level))
        

def record(args,prompt_nodes,initial_seed_num):
    max_score=1
    max_passes=1000
    worst_scores=[max_score]*initial_seed_num
    worst_passes=[max_passes]*initial_seed_num
    for prompt_node in prompt_nodes:
        task_id=int(prompt_node.solution['task_id'].split('/')[-1])
        worst_scores[task_id]=min(worst_scores[task_id],prompt_node.score)
        worst_passes[task_id]=min(worst_passes[task_id],prompt_node.passes)
    
    print('worst_scores')
    print(worst_scores)
    print('worst_passes')
    print(worst_passes)
    worst_avg_score=round(sum(worst_scores)/len(worst_scores),4)
    print(worst_avg_score)
    total_passes=sum(worst_passes)
    print(sum(worst_passes))

    initial_avg_score=round(sum(initial_score)/len(worst_scores),4)
    initial_total_passes=sum(initial_passes)

    score_difference=worst_avg_score-initial_avg_score
    passes_difference=total_passes-initial_total_passes

    final_reuslt_output_path=args.output_path+'final_result.jsonl'
    with open(final_reuslt_output_path, 'a') as f:
        result={
            'worst_avg_scores':worst_avg_score,
            'final_total_passes':total_passes,
            'initial_avg_score':initial_avg_score,
            'initial_total_passes':initial_total_passes,
            'score_difference':score_difference,
            'passes_difference':passes_difference,
            'worst_scores':worst_scores,
            'worst_passes':worst_passes

        }
        f.write(json.dumps(result) + '\n')
        f.flush()


if __name__ == '__main__':
    from roles.rule_descriptions_actc import TEAM, ANALYST, PYTHON_DEVELOPER, TESTER

    # load dataset
    INPUTPATH=args.input_path
    loaded_dataset=[]
    with open(INPUTPATH, 'r') as f:
        # 导入输出
        loaded_dataset = [json.loads(line) for line in f]
    
    
    args.output_path+=f'results-{time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())}/'
    os.mkdir(args.output_path)
    print(args.output_path)


    if '%' in args.mutate_method:
        mutate_methods=args.mutate_method.split('%')
    else:
        mutate_methods=[args.mutate_method]

    initial_seed = loaded_dataset
    initial_seed_num=len(loaded_dataset)

    initial_score=[1.0, 1.0, 0.165, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.6929, 0.0664, 0.0315, 0.7325, 0.9915, 1.233, 1.0, 1.0, 1.0, 1.0, 0.8248, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9587, 0.3276, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.669, 1.0, 0.9921, 0.5084, 1.0, 0.1098, 1.0, 1.0, 0.1143, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0992, 1.0, 1.0, 0.9906, 0.7278, 0.9849, 0.9765, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9452, 0.8012, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.8964, 0.8815, 0.2639, 1.0, 1.0, 0.97, 0.4123, 1.0, 0.0, 0.6038, 1.0, 0.9826, 0.7172, 0.9952, 0.7, 0.6517, 0.2897, 1.0, 0.2692, 0.9925, 0.8853, 0.0074, 0.9074, 0.96, 0.9054, 0.4987, 0.7928, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9041, 0.2708, 0.9189, 0.4534, 0.9516, 1.0, 0.8116, 1.0, 0.0031, 1.0, 1.0, 0.7069, 0.9359, 0.2113, 1.0, 0.9121, 1.0, 0.8671, 0.2547, 0.7, 0.9496, 0.9182, 0.0721, 0.0, 0.9118, 0.7, 1.0, 0.9788, 0.8396, 1.0, 0.5839, 0.0977, 1.0, 0.8016, 1.0, 0.159, 1.0, 0.9977, 0.3962, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9463, 1.0, 1.0, 0.854, 0.9798, 1.0, 1.0, 1.0, 0.0894, 0.7062, 1.0, 1.0, 0.0917]
    initial_passes=[105.0, 69.0, 17.0, 91.0, 105.0, 110.0, 99.0, 106.0, 94.0, 59.6, 7.7, 4.0, 67.9, 116.0, 127.0, 48.0, 128.3, 129.0, 132.0, 99.8, 130.0, 130.0, 87.0, 94.0, 33.0, 72.8, 22.0, 126.0, 87.0, 112.0, 96.0, 70.0, 0.0, 106.8, 126.0, 125.0, 58.2, 127.0, 125.0, 6.5, 126.0, 10.2, 85.0, 126.0, 15.2, 73.0, 74.0, 111.0, 131.0, 120.0, 12.5, 133.0, 126.0, 105.0, 81.0, 32.4, 80.9, 113.0, 100.0, 105.0, 102.0, 79.0, 99.0, 30.0, 108.7, 76.5, 113.0, 115.0, 99.0, 141.0, 107.0, 114.0, 103.0, 102.0, 107.0, 51.9, 86.2, 19.0, 105.9, 30.0, 105.6, 43.7, 136.0, 0.1, 73.7, 95.0, 113.0, 54.6, 83.0, 56.5, 57.1, 31.0, 131.0, 35.0, 133.0, 110.4, 1.0, 98.0, 52.8, 129.8, 39.5, 88.0, 116.0, 119.0, 131.0, 106.0, 30.0, 111.6, 26.0, 106.0, 72.2, 118.0, 135.0, 116.1, 120.0, 0.1, 113.0, 133.0, 89.8, 87.0, 30.0, 133.0, 124.0, 73.0, 133.7, 34.0, 77.0, 127.0, 95.6, 8.2, 0.0, 95.0, 84.7, 120.0, 134.1, 89.0, 124.0, 65.9, 29.7, 16.0, 121.3, 126.1, 8.0, 133.0, 129.7, 42.0, 102.0, 98.0, 102.0, 133.0, 137.0, 85.8, 132.0, 135.0, 112.2, 77.8, 132.0, 134.0, 137.0, 28.2, 86.9, 128.0, 131.0, 11.1]
    initial_score=initial_score[:initial_seed_num]
    initial_passes=initial_passes[:initial_seed_num]
    prompt_nodes = [
            PromptNode(initial_seed[i],initial_score[i],initial_passes[i]) for i in range(len(initial_seed))
        ]
    for i, prompt_node in enumerate(prompt_nodes):
        prompt_node.index = i
    
    
    select_policy = MCTSExploreSelectPolicy(len(prompt_nodes))


    fail_list=[]
    threshold=args.num_round*len(mutate_methods)
    
    for idx in range(threshold):
        print('----'*10+'round: '+str(idx)+'---'*10)

        print('-'*10+'selecting seed'+'-'*10)
        seed = select_policy.select(prompt_nodes)
        print('current seed index:' + str(seed.index))

        # print(seed.score)
        # print(seed.reward_score)


        print('-'*10+'mutating'+'-'*10)
        mutated_seed = mutate_one(seed,mutate_method=args.mutate_method)
        # print(seed.solution['prompt'])
        # print(mutated_results)
        print('-'*10+'evaluating mutated seed'+'-'*10)


        
        # if not os.path.exists(code_output_path):
        #     os.mkdir(code_output_path)
        score, passes=-1,-1
        task=mutated_seed.solution
        code_output_path=args.output_path+'code'+'_round_'+str(idx)+'.jsonl'
        with open(code_output_path, 'w+') as f:
            codes=[]
            session_historys=[]
            intent=task['prompt']
            method_name = task['entry_point']
            before_func = prompt_split_humaneval(task['prompt'],method_name)
            need_second_round, finally_pass=0,0
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
            
            score, passes,passAt1, passAt10 = evaluate_one(task,args.num_generate)
            mutated_seed.score=score
            mutated_seed.passes=passes
            entry_point = find_method_name(code)
                    
            
            
            f.write(json.dumps(task) + '\n')
            f.flush()
        




        mutated_seed.solution=task

        print('-'*10+'updating'+'-'*10)
        print(seed.score,mutated_seed.score)
        # print(seed.solution['prompt'])
        # print(mutated_seed.solution['prompt'])
        if seed.score>mutated_seed.score:
            # 实际的得分是减少的分数
            mutated_seed.reward_score = seed.score - mutated_seed.score
            mutated_seed.index = len(prompt_nodes)
            prompt_nodes.append(mutated_seed)
            
        else:
            mutated_seed.reward_score=0

        print('len(prompt_nodes): '+str(len(prompt_nodes)))
        print('reward before fuzzing')
        print(select_policy.rewards)
        select_policy.update([mutated_seed],prompt_nodes)
        print('reward after fuzzing')
        print(select_policy.rewards)

        

        output_file = args.output_path + 'log.txt'
        with open(output_file,'a') as f:
            f.write('round:'+str(idx)+'\n')
            f.write('current node number: '+str(len(prompt_nodes))+'\n')
            f.write('old score: '+str(seed.score) + ' ,new score: '+str(mutated_seed.score) + '\n')
            f.write('seed prompt:\n ' + seed.solution['prompt']+'\n')
            f.write('mutated prompt:\n' + mutated_seed.solution['prompt']+'\n\n\n\n')
        
        if (idx-1) % 100 ==0:
            record(args,prompt_nodes,initial_seed_num)



            

    print('fuzzing finished!')
    print('total prompt nodes number:' + str(len(prompt_nodes)))


    node_output_path=args.output_path+'final_node.jsonl'
    with open(node_output_path, 'w+') as f:
        for prompt_node in prompt_nodes:
            result={
                'task_id':prompt_node.solution['task_id'],
                'prompt':prompt_node.solution['prompt'],
                'score':prompt_node.score,
                'passes':prompt_node.passes

            }
            f.write(json.dumps(result) + '\n')
            f.flush()

    record(args,prompt_nodes,initial_seed_num)

    

        
    

