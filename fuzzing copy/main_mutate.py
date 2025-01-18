import os
import copy
import json
import argparse
import tqdm
import random
from session import Session
from datasets import load_dataset, load_from_disk
from utils import prompt_split_humaneval, find_method_name, code_split, build_test_method
import copy
# from main_fuzz_passAt10 import PromptNode
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
        self.finish = False
        

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
I will give you a coding question prompt, with several test cases. You are required to condense sentences you think are too long and delete the meaningless sentence. Also, you should maintain the overall meaning of the template and SHOULD NOT delete the test cases in the templete. Do not make any change to the meaning of the question. You should not change the input format and output format. Do not make any other explanation nor have beginning or ending indicator in your answer. 
Here is the question:
'''

REPHRASE='''
I will give you a coding question prompt, with several test cases. You are required to rephrase sentences in the natural language description part while remaining other sentences unchanged. Also, you should maintain the overall meaning of the template and SHOULD NOT delete the test cases. Do not make any change to the meaning of the question. You should not change the input format and output format. Do not make any other explanation nor have beginning or ending indicator in your answer. 
Here is the question:
'''

CHANGE_IDENTIFIER_FUNCNAME = '''
I will give you a coding question prompt, with several test cases. You are required to change the identifier of the given code into random strings, while remaining other sentences unchanged. Do not change the function name! Also, you should maintain the overall meaning of the template and SHOULD NOT delete the test cases. Do not make any change to the meaning of the question. You should not change the input format and output format. Do not make any other explanation nor have beginning or ending indicator in your answer. 
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

def mutate_all_method(model,prompt):
    return 
def mutate_change_identifier_funcname(model,prompt):
    prompt=CHANGE_IDENTIFIER_FUNCNAME+prompt
    # print(prompt)
    message = [
        {"role": "user", "content": prompt}
    ]
    
    completions = []
    try:      
        requested_completions=1
        max_tokens=512
        temperature=1
        num_completions=1
        response = client.chat.completions.create(
        model=model,
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature,
        n=requested_completions
        )
        completions.extend([choice.message.content for choice in response.choices])
        if len(completions) >= num_completions:
            return completions[:num_completions]
    except openai.RateLimitError as e:
        time.sleep(min(i**2, 60))
    raise RuntimeError('Failed to call GPT API') 
def mutate_expand_1_sentence(model,prompt):
    prompt=EXPAND_1_SENTANCE+prompt
    # print(prompt)
    message = [
        {"role": "user", "content": prompt}
    ]
    
    completions = []
    try:      
        requested_completions=1
        max_tokens=512
        temperature=1
        num_completions=1
        response = client.chat.completions.create(
        model=model,
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature,
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
        temperature=1
        num_completions=1
        response = client.chat.completions.create(
        model=model,
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature,
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
        temperature=1
        num_completions=1
        response = client.chat.completions.create(
        model=model,
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature,
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
        temperature=1
        num_completions=1
        response = client.chat.completions.create(
        model=model,
        messages=message,
        max_tokens=max_tokens,
        temperature=temperature,
        n=requested_completions
        )
        completions.extend([choice.message.content for choice in response.choices])
        if len(completions) >= num_completions:
            return completions[:num_completions]
    except openai.RateLimitError as e:
        time.sleep(min(i**2, 60))
    raise RuntimeError('Failed to call GPT API')


mutate_method_map = {'expand_1':mutate_expand_1_sentence,'rephrase':mutate_rephrase,'shorten':mutate_shorten,'change_name':mutate_change_identifier_funcname, 'expand_all':mutate_expand_all}
mutate_methods=['expand_1','rephrase','shorten']

def mutate_all(loaded_dataset, output_path,mutate_method,model='gpt-4o'):
    with open(output_path, 'w+') as f:
        for idx, task in enumerate(loaded_dataset):
            print('mutating: '+str(idx))
            intent = task['prompt']
            # print(intent)
            mutated_prompt=''

            


            if mutate_method == 'shorten':
                mutated_prompt = mutate_shorten(model,intent)
            elif mutate_method == 'expand_1':
                # print('in expand_1')
                mutated_prompt = mutate_expand_1_sentence(model,intent)
            elif mutate_method == 'expand_all':
                mutated_prompt = mutate_expand_all(model,intent)
            elif mutate_method == 'rephrase':
                mutated_prompt = mutate_rephrase(model,intent)
            elif mutate_method == 'random':
                mutated_prompt = mutate_methods[random.randint(0,3)](model,intent)
            else:
                print('not implemented')
                break
            solution={'prompt':mutated_prompt[0]}
            f.write(json.dumps(solution) + '\n')
            f.flush()
            # print(mutated_prompt[0])
            loaded_dataset[idx]['prompt']=mutated_prompt[0]
            # if idx>2:
            #     break
        return loaded_dataset
    

def mutate_one(seed,mutate_method='random',model='gpt-4o'):
    
    intent = seed.solution['prompt']
    # print(intent)
    mutated_prompt=''
    if mutate_method == 'random':
        mutate_method = mutate_methods[random.randint(0,len(mutate_methods)-1)]
        
    if mutate_method not in mutate_method_map.keys():
        print('not implemented')
        raise NotImplementedError
    mutated_prompt = mutate_method_map[mutate_method](model,intent)


    new_solution=copy.deepcopy(seed.solution)
    new_solution['prompt'] = mutated_prompt[0]
    print(mutated_prompt)
    ans=PromptNode(solution=new_solution,parent=seed)
    return ans,mutate_method
        
            
def test_mutate(intent):
    mutated_prompt = mutate_rephrase('gpt-35-turbo',intent)
    return mutated_prompt

# input = '''
# def has_close_elements(numbers: List[float], threshold: float) -> bool:
#     """ Check if in given list of numbers, are any two numbers closer to each other than
#     given threshold.
#     >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
#     False
#     >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
#     True
#     """
# '''

# input = '''
# def has_close_elements(numbers: List[float], threshold: float) -> bool:\n    """ Determine if there are any two numbers in the provided list that are closer together than the specified threshold.\n    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n    False\n    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n    True\n
# '''
# print(test_mutate(input))