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

# EXPAND_1_SENTANCE='''
# I will give you a coding question prompt, with several test cases. You are required to add a sentence to the end of the description part of the question template, and return the whole question. Do not make any other explanation nor have beginning or ending indicator in your answer. 
# Here is the question:
# '''

ADD_1_SENTANCE_AT_END='''
I will give you a coding question prompt, with several test cases. You are required to add a sentence to the end of the description part of the question template, and return the whole question. Do not make any change to the other part of the question. Do not make any change to the meaning of the question. You should not change the input format and output format. Do not make any other explanation nor have beginning or ending indicator in your answer. 
RETURN THE COMPLETED QUESTION!
Here is the question:
'''


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


CONDENSE_ONE_SENTENCE='''
I will give you a coding question prompt, with several test cases. You are required to randomly choose one sentence from the question description, condense the sentence and delete useless information in the sentence. Do not make any change to other sentences.
Also, you should maintain the overall meaning of the question.
You SHOULD NOT delete the test cases or before function in the templete!! 
Do not make any change to the meaning of the question. You should not change the input format and output format. 
Do not make any other explanation nor have beginning or ending indicator in your answer. 
Only return the whole question after your mutation.
Here is the question:
'''

CONDENSE_TWO_SENTENCE_INTO_ONE = '''
I will give you a coding question prompt, with several test cases. You are required to randomly choose two consecutive sentences from the question description and condense them into one sentence. Do not make any change to other sentences. If there is only one sentence in the question description, do not make any change to it.
Also, you should maintain the overall meaning of the question.
You SHOULD NOT delete the test cases or before function in the templete!! 
Do not make any change to the meaning of the question. You should not change the input format and output format. 
Do not make any other explanation nor have beginning or ending indicator in your answer. 
Only return the whole question after your mutation.
Here is the question:
'''

EXPAND_ONE_SENTENCE_INTO_TWO = '''
I will give you a coding question prompt, with several test cases. You are required to randomly choose one sentence from the question description and expand it into two sentences. Do not make any change to other sentences. 
Also, you should maintain the overall meaning of the question.
You SHOULD NOT delete the test cases or before function in the templete!! 
Do not make any change to the meaning of the question. You should not change the input format and output format. 
Do not make any other explanation nor have beginning or ending indicator in your answer. 
Only return the whole question after your mutation.
Here is the question:
'''

EXPAND_ONE_SENTENCE = '''
I will give you a coding question prompt, with several test cases. You are required to randomly choose ONE sentence from the question description, add more useful information to the sentence. Do not make any change to other sentences.
Also, you should maintain the overall meaning of the question.
You SHOULD NOT delete the test cases or before function in the templete!! 
Do not make any change to the meaning of the question. You should not change the input format and output format. 
Do not make any other explanation nor have beginning or ending indicator in your answer. 
Only return the whole question after your mutation.
Here is the question:
'''

REPHRASE_ONE_SENTENCE = '''
I will give you a coding question prompt, with several test cases. You are required to randomly choose ONE sentence from the question description, and use other words to rewrite the sentence. Do not make any change to other sentences.
Also, you should maintain the overall meaning of the question.
You SHOULD NOT delete the test cases or before function in the templete!! 
Do not make any change to the meaning of the question. You should not change the input format and output format. 
Do not make any other explanation nor have beginning or ending indicator in your answer. 
Only return the whole question after your mutation.
Here is the question:
'''

NL_ADD_1_SENTANCE_AT_END='''
I will give you a coding question prompt. You are required to add a sentence to the end of the description part of the question template, and return the whole question. 
Do not make any other explanation nor have beginning or ending indicator in your answer. 
Return the whole question after your mutation!
Here is the question:
'''


NL_EXPAND_ALL='''
I will give you a coding question prompt. There are natural language description between code method name and test cases. You are required to expand the natural language description part of the question template.
Do not make any change to the meaning of the question. Do not make any other explanation nor have beginning or ending indicator in your answer. 
Return the whole question after your mutation!
Here is the question:
'''

NL_SHORTEN='''
I will give you a coding question prompt. You are required to condense sentences you think are too long and delete the meaningless sentence. Also, you should maintain the overall meaning of the question. 
Do not make any other explanation nor have beginning or ending indicator in your answer.
Return the whole question after your mutation! 
Here is the question:
'''

NL_REPHRASE='''
I will give you a coding question prompt. You are required to rephrase the question while maintaining the overall meaning. Do not make any change to the meaning of the question. 
Do not make any other explanation nor have beginning or ending indicator in your answer. 
Return the whole question after your mutation!
Here is the question:
'''


NL_CONDENSE_ONE_SENTENCE='''
I will give you a coding question prompt. You are required to randomly choose one sentence from the question description, condense the sentence and delete useless information in the sentence. Do not make any change to other sentences.
Also, you should maintain the overall meaning of the question.
Do not make any change to the meaning of the question. 
Do not make any other explanation nor have beginning or ending indicator in your answer. 
Return the whole question after your mutation!
Here is the question:
'''

NL_CONDENSE_TWO_SENTENCE_INTO_ONE = '''
I will give you a coding question prompt. You are required to randomly choose two consecutive sentences from the question description and condense them into one sentence. Do not make any change to other sentences. If there is only one sentence in the question description, do not make any change to it.
Also, you should maintain the overall meaning of the question.
Do not make any change to the meaning of the question. 
Do not make any other explanation nor have beginning or ending indicator in your answer. 
Return the whole question after your mutation!
Here is the question:
'''

NL_EXPAND_ONE_SENTENCE_INTO_TWO = '''
I will give you a coding question prompt. You are required to randomly choose one sentence from the question description and expand it into two sentences. Do not make any change to other sentences. 
Also, you should maintain the overall meaning of the question.
Do not make any change to the meaning of the question. 
Do not make any other explanation nor have beginning or ending indicator in your answer. 
Return the whole question after your mutation!
Here is the question:
'''

NL_EXPAND_ONE_SENTENCE = '''
I will give you a coding question prompt. You are required to randomly choose ONE sentence from the question description, add more useful information to the sentence. Do not make any change to other sentences.
Also, you should maintain the overall meaning of the question.
Do not make any change to the meaning of the question. 
Do not make any other explanation nor have beginning or ending indicator in your answer.
Return the whole question after your mutation!
Here is the question:
'''

NL_REPHRASE_ONE_SENTENCE = '''
I will give you a coding question prompt. You are required to randomly choose ONE sentence from the question description, and use other words to rewrite the sentence. Do not make any change to other sentences.
Also, you should maintain the overall meaning of the question.
Do not make any change to the meaning of the question. 
Return the whole question after your mutation!
Do not make any other explanation nor have beginning or ending indicator in your answer. 
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

def mutate(model,prompt,mutate_prompt):
    prompt=mutate_prompt+prompt
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


mutate_prompt_map = {'add_1_sentence_at_end':ADD_1_SENTANCE_AT_END,'rephrase':REPHRASE,'shorten':SHORTEN, 'expand_one':EXPAND_ONE_SENTENCE,'condense_one':CONDENSE_ONE_SENTENCE,'expand_one2two':EXPAND_ONE_SENTENCE_INTO_TWO,'condense_two2one':CONDENSE_TWO_SENTENCE_INTO_ONE,'rephrase_one':REPHRASE_ONE_SENTENCE}
mutate_prompt_nl_map = {'add_1_sentence_at_end':NL_ADD_1_SENTANCE_AT_END,'rephrase':NL_REPHRASE,'shorten':NL_SHORTEN, 'expand_one':NL_EXPAND_ONE_SENTENCE,'condense_one':NL_CONDENSE_ONE_SENTENCE,'expand_one2two':NL_EXPAND_ONE_SENTENCE_INTO_TWO,'condense_two2one':NL_CONDENSE_TWO_SENTENCE_INTO_ONE,'rephrase_one':NL_REPHRASE_ONE_SENTENCE}

mutate_methods=['add_1_sentence_at_end','rephrase','shorten','expand_one','condense_one','expand_one2two','condense_two2one','rephrase_one']
# mutate_methods = mutate_methods[3:]


def mutate_one(seed,args,mutate_method='random',model='gpt-4o'):
    mutate_methods=['add_1_sentence_at_end','rephrase','shorten','expand_one','condense_one','expand_one2two','condense_two2one','rephrase_one']
    intent = seed.solution['prompt']
    # print(intent)
    mutated_prompt=''
    if mutate_method == 'random':
        if args.mutate_level == 'whole':
            mutate_methods = mutate_methods[:3]
        elif args.mutate_level == 'sentence':
            # print(11111)
            mutate_methods = mutate_methods[3:]
        mutate_method = mutate_methods[random.randint(0,len(mutate_methods)-1)]

    if mutate_method not in mutate_prompt_map.keys():
        print('not implemented')
        raise NotImplementedError

    prompt4mutation = mutate_prompt_map[mutate_method]
    
    mutated_prompt = mutate(model,intent,prompt4mutation)[0]

    while 'def ' not in mutated_prompt:
        print('改变了prompt的结构!!!')
        mutated_prompt = mutate(model,intent,prompt4mutation)[0]

    new_solution=copy.deepcopy(seed.solution)
    new_solution['prompt'] = mutated_prompt
    # print('-'*100)
    # print(intent)
    # print('-'*100)
    # print(mutated_prompt)
    # print('-'*100)
    ans=PromptNode(solution=new_solution,parent=seed)
    return ans,mutate_method


def mutate_one_nl(seed,args,mutate_method='random',model='gpt-4o'):
    mutate_methods=['add_1_sentence_at_end','rephrase','shorten','expand_one','condense_one','expand_one2two','condense_two2one','rephrase_one']
    intent = seed.solution['nl']
    # print(intent)
    mutated_nl=''
    if mutate_method == 'random':
        if args.mutate_level == 'whole':
            mutate_methods = mutate_methods[:3]
        elif args.mutate_level == 'sentence':
            # print(11111)
            mutate_methods = mutate_methods[3:]
        mutate_method = mutate_methods[random.randint(0,len(mutate_methods)-1)]
    if mutate_method not in mutate_prompt_nl_map.keys():
        print('not implemented')
        raise NotImplementedError

    prompt4mutation = mutate_prompt_nl_map[mutate_method]
    
    mutated_nl = mutate(model,intent,prompt4mutation)[0]


    new_solution=copy.deepcopy(seed.solution)
    new_solution['prompt'] = seed.solution['func']+'\t\n\'\'\''+mutated_nl+'\n'+seed.solution['examples'] +'\'\'\''
    print('-'*50)
    print(mutate_method)
    print()
    print(seed.solution['prompt'])
    print('-'*50)
    print(new_solution['prompt'])
    print('-'*50)

    ans=PromptNode(solution=new_solution,parent=seed)
    return ans,mutate_method
        

mutate_prompt_nl_map = {'add_1_sentence_at_end':NL_ADD_1_SENTANCE_AT_END,'rephrase':NL_REPHRASE,'shorten':NL_SHORTEN, 'expand_one':NL_EXPAND_ONE_SENTENCE,'condense_one':NL_CONDENSE_ONE_SENTENCE,'expand_one2two':NL_EXPAND_ONE_SENTENCE_INTO_TWO,'condense_two2one':NL_CONDENSE_TWO_SENTENCE_INTO_ONE,'rephrase_one':NL_REPHRASE_ONE_SENTENCE}       
def test_mutate(intent):
    mutate_prompt = NL_CONDENSE_ONE_SENTENCE
    mutated_prompt = mutate('gpt-4o',intent,mutate_prompt)
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
# "from typing import List\n\n\ndef separate_paren_groups(paren_string: str) -> List[str]:\n    \"\"\" Input to this function is a string containing multiple groups of nested parentheses. Your goal is to\n    separate those group into separate strings and return the list of those.\n    Separate groups are balanced (each open brace is properly closed) and not nested within each other\n    Ignore any spaces in the input string.\n    >>> separate_paren_groups('( ) (( )) (( )( ))')\n    ['()', '(())', '(()())']\n    \"\"\"\n"
# '''
# # input = '''
# # "from typing import List\n\n\ndef mean_absolute_deviation(numbers: List[float]) -> float:\n    \"\"\" For a given list of input numbers, calculate Mean Absolute Deviation\n    around the mean of this dataset.\n    Mean Absolute Deviation is the average absolute difference between each\n    element and a centerpoint (mean in this case):\n    MAD = average | x - x_mean |\n    >>> mean_absolute_deviation([1.0, 2.0, 3.0, 4.0])\n    1.0\n    \"\"\"\n"
# # '''

# input ='''
# from typing import List\n\ndef separate_paren_groups(paren_string: str) -> List[str]:\n    """ Input to this function is a string containing multiple groups of nested parentheses, which you need to separate into separate strings and return the list of those. Separate groups are balanced (each open brace is properly closed) and not nested within each other. Ignore any spaces in the input string.\n    >>> separate_paren_groups(\'( ) (( )) (( )( ))\')\n    [\'()\', \'(())\', \'(()())\']\n    """\n
# '''

input ='''
You have been tasked to write a function that receives \n    a hexadecimal number as a string and counts the number of hexadecimal \n    digits that are primes (prime number, or a prime, is a natural number \n    greater than 1 that is not a product of two smaller natural numbers).\n    Hexadecimal digits are 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D, E, F.\n    Prime numbers are 2, 3, 5, 7, 11, 13, 17,...\n    So you have to determine a number of the following digits: 2, 3, 5, 7, \n    B (=decimal 11), D (=decimal 13).\n    Note: you may assume the input is always correct or empty string, \n    and symbols A,B,C,D,E,F are always uppercase.\n '''
# ['from typing import List\n\ndef separate_paren_groups(paren_string: str) -> List[str]:\n    """ This function takes as input a string with several groups of nested parentheses, and your task is to split them into individual strings and return those as a list. Separate groups are balanced (each open brace is properly closed) and not nested within each other. Ignore any spaces in the input string.\n    >>> separate_paren_groups(\'( ) (( )) (( )( ))\')\n    [\'()\', \'(())\', \'(()())\']\n    """']
print(test_mutate(input))