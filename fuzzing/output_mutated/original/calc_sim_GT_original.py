import json


from sentence_transformers import SentenceTransformer, util
import random
import torch
import torch.nn.functional as F

import openai
from openai import OpenAI
from openai import AzureOpenAI
import time
import os

# semantic_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

PROMPT_REFERENCE='''
Score the following coding plan with respect to the coding question and reference plan on a continuous scale from 0 to 100, where a score of zero means "no help to solve the question" and score of one hundred means "perfect plan for solving the coding question"
coding question: <question>
reference plan: <ref_plan>
target plan: <tgt_plan>
Only output the score, do not make any explaination
Score:
'''

PROMPT_NO_REFERENCE='''
Score the following coding plan with respect to the coding question on a continuous scale from 0 to 100, where a score of zero means "no help to solve the question" and score of one hundred means "perfect plan for solving the coding question"
coding question: <question>
target plan: <tgt_plan>
Only output the score, do not make any explaination
Score:
'''

def call_chatgpt(prompt, model='gpt-35-turbo', stop=None, temperature=0., top_p=1.0,
        max_tokens=128, echo=False, majority_at=None):
    # print('$$$'*200)
    # print('in call gpt')
    # print(model)
    # client = OpenAI()
    client = AzureOpenAI(
    azure_endpoint = "https://hkust.azure-api.net", 
    api_key="b234b6eb250e445d8151e8e5710dadde",  
    api_version="2024-02-01"
    )

    # client = AzureOpenAI(
    # azure_endpoint = "https://hkust.azure-api.net", 
    # api_key="b8927c969e8147ea8404003613bbddb6",  
    # api_version="2024-02-01"
    # )
    num_completions = majority_at if majority_at is not None else 1
    num_completions_batch_size = 10

    completions = []
    for i in range(20 * (num_completions // num_completions_batch_size + 1)):
        
        try:
            # print('***'*30)
            # print(prompt)
            requested_completions = min(num_completions_batch_size, num_completions - len(completions))
            # print(client.api_key)
            # print(client.base_url)
            # print(max_tokens,temperature,top_p,requested_completions)
            response = client.chat.completions.create(
            model=model,
            messages=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            n=requested_completions
            )
            while not response:
                client.chat.completions.create(
                    model=model,
                    messages=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    n=requested_completions
                    )
            completions.extend([choice.message.content for choice in response.choices])
            # print(completions[0])
            # print('*'*30)
            if len(completions) >= num_completions:
                return completions[:num_completions]
        except openai.RateLimitError as e:
            time.sleep(min(i**2, 60))
    raise RuntimeError('Failed to call GPT API')


lines = []
models=['gpt-35-turbo','gpt-4o']
with open ('code_round_0_with_score.jsonl','r') as f:
    lines = [json.loads(line) for line in f]
    for idx,task in enumerate(lines):
        print('handling task {}'.format(idx))
        original_plan = []
        for his in task['session_historys']:
            original_plan.append(his['plan'])
        GT_plan  = task['canonical_plan']


        for model in models:
            scores=[]

            for plan in original_plan:
                prompt=PROMPT_REFERENCE.replace('<question>',task['prompt']).replace('<ref_plan>',GT_plan[0]).replace('<tgt_plan>',plan)
                
                input_prompt = message = [
                    {"role": "user", "content": prompt}
                ]
                score=call_chatgpt(input_prompt,model)[0]
                score = int(score)
                scores.append(score)
                # print(score)
                # break
            mean_score1=sum(scores)/len(scores)
            scores=[]
            for plan in original_plan:
                prompt=PROMPT_NO_REFERENCE.replace('<question>',task['prompt']).replace('<tgt_plan>',plan)
                input_prompt = message = [
                    {"role": "user", "content": prompt}
                ]
                score=call_chatgpt(input_prompt,model)[0]
                score = int(score)
                scores.append(score)
                # print(score)
                # break
            mean_score2=sum(scores)/len(scores)
            lines[idx]['plan_score_'+model]=[mean_score1,mean_score2]

with open('a.jsonl','w+') as f:
    for line in lines:
        f.write(json.dumps(line) + '\n')

        # print('task No. {}, score = {}'. format(idx,mean_score))
        # seed_plans = original_plan
        # mutated_seed_plans =GT_plan
        # seed_plans=semantic_model.encode(seed_plans, convert_to_tensor=True)
        # mutated_seed_plans=semantic_model.encode(mutated_seed_plans, convert_to_tensor=True)
        # seed_plans = F.normalize(seed_plans, dim = 1)
        # mutated_seed_plans = F.normalize(mutated_seed_plans, dim = 1)
        # similarity = torch.einsum("ab,cb->ac",seed_plans,mutated_seed_plans)
        # similarity=torch.mean(similarity)
        # similarity = float(similarity)

