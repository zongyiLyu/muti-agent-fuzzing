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
    from roles.rule_descriptions_act import TEAM, ANALYST, PYTHON_DEVELOPER, TESTER
    OUTPUT_PATH = args.output_path
    args.max_round=3
    intents=[]
    # intents.append('triples_sum_to_zero takes a list of integers as an input. it returns True if there are three distinct elements in the list that sum to zero, and False otherwise.')
    x='''
      def truncate_number(number: float) -> float:
    """ Given a positive floating point number, it can be decomposed into
    and integer part (largest integer smaller than given number) and decimals
    (leftover part always smaller than 1).

    Return the decimal part of the number.
    >>> truncate_number(3.5)
    0.5
    """
"""

     '''
    intents.append(x)
    # intents.append('Write a simple Flappy Bird Game')
    # intents.append('Write a classic and simple Flappy Bird Game')
    # intents.append('Write a funny and simple Flappy Bird Game')
    # intents.append('')
    # intents.append('')
    need_second_round, finally_pass=0,0
    with open(OUTPUT_PATH, 'w+') as f:
        for intent in intents:
            session = Session(TEAM, ANALYST, PYTHON_DEVELOPER, TESTER,requirement=intent, model=args.model, majority=args.majority, 
                                            max_tokens=args.max_tokens, temperature=args.temperature, 
                                            top_p=args.top_p, max_round=args.max_round, before_func='')
                            
            code, session_history, a, b = session.run_session(need_second_round, finally_pass)
            solution = {
                    'completion': code,
                    'session_history': session_history,
                }
            f.write(json.dumps(solution) + '\n')
            f.flush()
            
        # with open('output.txt', 'w') as file: 
        #     file.write(code)
        #     file.write("plan")
        #     file.write(session_history["plan"])
        #     for xx in session_history.keys():

        #         if xx=="plan":
        #             continue
        #         for yy in xx.keys():
        #             file.write(yy)
        #             file.write(xx[yy])
