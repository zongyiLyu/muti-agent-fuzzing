import os
import copy
import json
import argparse
import tqdm

from session import Session
from datasets import load_dataset, load_from_disk
from utils import prompt_split_humaneval, find_method_name, code_split, build_test_method

parser = argparse.ArgumentParser()
parser.add_argument('--dataset', type=str, default='humaneval')
parser.add_argument('--lang', type=str, default='python')
parser.add_argument('--output_path', type=str, default='output.jsonl')
parser.add_argument('--task', type=str, default='shorten')

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


EXPAND_1_SENTANCE='''
I will give you a coding question prompt, with several test cases. You are required to add a sentence to the end of the description part of the question template, and return the whole question. Do not make any change to the other part of the question. Do not make any change to the meaning of the question. You should not change the input format and output format. Do not make any other explanation nor have beginning or ending indicator in your answer. 
RETURN THE COMPLETED QUESTION!
Here is the question:
'''
# EXPAND_1_SENTANCE='''
# I will give you a coding question prompt, with several test cases. You are required to add a sentence to the end of the description part of the question template, and return the whole question. Do not make any other explanation nor have beginning or ending indicator in your answer. 
# Here is the question:
# '''

EXPAND_ALL='''
I will give you a coding question prompt, with several test cases. There are natural language description between code method name and test cases. You are required to expand the natural language description part of the question template. Do not make any change to the code and test cases. Do not make any change to the meaning of the question. Do not make any other explanation nor have beginning or ending indicator in your answer. 
YOU CAN ONLY EXPAND THE NATURAL LANGUAGE PART, DO NOT MAKE ANY CHANGE TO OTHER PART!
Here is the question:
'''

SHORTEN='''
I will give you a coding question prompt, with several test cases. You are required to condense sentences you think are too long while remaining other sentences unchanged. Also, you should maintain the overall meaning of the template and SHOULD NOT delete the test cases in the templete. Do not make any change to the meaning of the question. You should not change the input format and output format. Do not make any other explanation nor have beginning or ending indicator in your answer. 
Here is the question:
'''

REPHRASE='''
I will give you a coding question prompt, with several test cases. You are required to rephrase sentences in the natural language description part while remaining other sentences unchanged. Also, you should maintain the overall meaning of the template and SHOULD NOT delete the test cases. Do not make any change to the meaning of the question. You should not change the input format and output format. Do not make any other explanation nor have beginning or ending indicator in your answer. 
Here is the question:
'''


import openai
from openai import OpenAI
from openai import AzureOpenAI
# client = OpenAI(
#     # 输入转发API Key
#     api_key="sk-NsLLS6Bbm06SDgbx3BJkyHsEys50pj9TqlZB7PrIJHFSIzmI",
#     base_url="https://api.chatanywhere.com.cn/v1"
# )

client = AzureOpenAI(
        azure_endpoint = "https://hkust.azure-api.net", 
        api_key="b234b6eb250e445d8151e8e5710dadde",  
        api_version="2024-02-01"
    )
# client = OpenAI(
#     # 输入转发API Key
#     api_key="sk-NsLLS6Bbm06SDgbx3BJkyHsEys50pj9TqlZB7PrIJHFSIzmI",
#     base_url="https://api.chatanywhere.com.cn/v1"
# )


def mutate_all_method(model,prompt):
    return 
def mutate_expand_1_sentence(model,prompt):
    prompt=EXPAND_1_SENTANCE+prompt
    message = [
        {"role": "user", "content": prompt}
    ]
    completions = []
    try:      
        requested_completions=1
        max_tokens=512
        temperature=0
        top_p=0.95
        num_completions=1
        response = client.chat.completions.create(
        model=model,
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n=requested_completions
        )
        completions.extend([choice.message.content for choice in response.choices])
        if len(completions) >= num_completions:
            return completions[:num_completions]
    except openai.RateLimitError as e:
        time.sleep(min(i**2, 60))
    raise RuntimeError('Failed to call GPT API') 
def mutate_expand_all(model,prompt):
    prompt=EXPAND_ALL+prompt
    message = [
        {"role": "user", "content": prompt}
    ]
    completions = []
    try:      
        requested_completions=1
        max_tokens=512
        temperature=0
        top_p=0.95
        num_completions=1
        response = client.chat.completions.create(
        model=model,
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n=requested_completions
        )
        completions.extend([choice.message.content for choice in response.choices])
        if len(completions) >= num_completions:
            return completions[:num_completions]
    except openai.RateLimitError as e:
        time.sleep(min(i**2, 60))
    raise RuntimeError('Failed to call GPT API') 
def mutate_rephrase(model,prompt):
    prompt=REPHRASE+prompt
    message = [
        {"role": "user", "content": prompt}
    ]
    completions = []
    try:      
        requested_completions=1
        max_tokens=512
        temperature=0
        top_p=0.95
        num_completions=1
        response = client.chat.completions.create(
        model=model,
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n=requested_completions
        )
        completions.extend([choice.message.content for choice in response.choices])
        if len(completions) >= num_completions:
            return completions[:num_completions]
    except openai.RateLimitError as e:
        time.sleep(min(i**2, 60))
    raise RuntimeError('Failed to call GPT API') 
def mutate_shorten(model,prompt):
    prompt=SHORTEN+prompt
    message = [
        {"role": "user", "content": prompt}
    ]
    completions = []
    try:      
        requested_completions=1
        max_tokens=512
        temperature=0
        top_p=0.95
        num_completions=1
        response = client.chat.completions.create(
        model=model,
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n=requested_completions
        )
        completions.extend([choice.message.content for choice in response.choices])
        if len(completions) >= num_completions:
            return completions[:num_completions]
    except openai.RateLimitError as e:
        time.sleep(min(i**2, 60))
    raise RuntimeError('Failed to call GPT API')

OUTPUT_PATH = args.output_path
model='gpt-4o'

dataset = load_dataset("openai_humaneval")
dataset_key = ["test"]
# print(dataset_key)
with open(OUTPUT_PATH, 'w+') as f:
    for key in dataset_key:
        for idx, task in enumerate(dataset[key]):
            print('mutating: '+str(idx))
            intent = task['prompt']
            # print(intent)
            mutated_prompt=''
            if args.task == 'shorten':
                mutated_prompt = mutate_shorten(model,intent)
            elif args.task == 'expand_1':
                mutated_prompt = mutate_expand_1_sentence(model,intent)
            elif args.task == 'expand_all':
                mutated_prompt = mutate_expand_all(model,intent)
            elif args.task == 'rephrase':
                mutated_prompt = mutate_rephrase(model,intent)
            else:
                print('not implemented')
                break
            solution={'prompt':mutated_prompt}
            f.write(json.dumps(solution) + '\n')
            f.flush()
        
            


# print(mutate_shorten(model,prompt))
# print(mutate_expand_1_sentence(model,prompt))
# print(mutate_expand_all(model,prompt))
# print(mutate_rephrase(model,prompt))



# completion = client.chat.completions.create(
#     model="gpt-3.5-turbo-1106",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant."},
#         {"role": "user", "content": "你是谁!"}
#     ],
#     logprobs=True,

#     stream=False  # 是否开启流式输出
# )


# if __name__ == '__main__':
#     from roles.rule_descriptions_actc import TEAM, ANALYST, PYTHON_DEVELOPER, TESTER

#     OUTPUT_PATH = args.output_path

#     # load dataset
#     if args.dataset == 'humaneval':
#         if args.lang == 'python':
#             dataset = load_dataset("openai_humaneval")
#             dataset_key = ["test"]

#     no_pass=[]
#     twice=[]
#     finally_pass=0
#     need_second_round=0
#     # need_second_round: 3
#     # finally_pass: 162
#     with open(OUTPUT_PATH, 'w+') as f:
#         for key in dataset_key:
#             # pbar = tqdm.tqdm(dataset[key], total=len(dataset[key]))
#             # for idx, task in enumerate(pbar):
#             for idx, task in enumerate(dataset[key]):
#                 print('***'*40)
#                 print('handling task: '+str(idx+1))
#                 p,q=finally_pass,need_second_round
#                 if args.dataset == 'humaneval':
#                     method_name = task['entry_point']
#                     before_func, signature, intent, public_test_case = prompt_split_humaneval(task['prompt'],method_name)
#                     args.signature = True
#                     if args.signature:
#                         intent = task['prompt']
                    
#                     test = task['test']

#                 try:
#                     # 进行分工流程在这里，输入了prompt为intent
#                     session = Session(TEAM, ANALYST, PYTHON_DEVELOPER, TESTER,requirement=intent, model=args.model, majority=args.majority, 
#                                     max_tokens=args.max_tokens, temperature=args.temperature, 
#                                     top_p=args.top_p, max_round=args.max_round, before_func=before_func)
#                     code, session_history, need_second_round, finally_pass= session.run_session(need_second_round,finally_pass)
#                     if p!=finally_pass:
#                         no_pass.append(idx)
#                     if q!=need_second_round:
#                         twice.append(idx)



                
#                 except RuntimeError as e:
#                     print(str(e))
#                     print("task-%d fail"%(task['task_id']))
#                     fail_list.append(task['task_id'])
#                     continue
#                 print('need_second_round: '+str(need_second_round))
#                 print('finally_pass: '+str(finally_pass))

#                 if  code == "error":
#                     continue

#                 entry_point = find_method_name(code)
#                 solution = {
#                     'task_id': task['task_id'],
#                     'prompt': before_func+"\n",
#                     'test': test,
#                     'entry_point': entry_point,
#                     'completion': code,
#                     'session_history': session_history,
#                     'no_pass':no_pass,
#                     'need_second_chance':twice
#                 }
#                 f.write(json.dumps(solution) + '\n')
#                 f.flush()
#         print(no_pass)
#         print(twice)
