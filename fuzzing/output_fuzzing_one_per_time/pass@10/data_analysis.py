import json
import os
file_names=os.listdir('.')
file_names=['results-2024-12-01-23-54-17']
for file_name in file_names:
    if 'py' in file_name:
        continue
    # file_name='0-reward-no-save-seed'
    data_path= '/data/zlyuaj/muti-agent/fuzzing/output_fuzzing_one_per_time/pass@10/{}/'.format(file_name)
    no_pass=[]
    for i in range(1000):
        cur_data_path=data_path+'code_round_{}.jsonl'.format(i)
        with open(cur_data_path, 'r') as f:
            datas = [json.loads(line) for line in f]
            for data in datas:
                # print(data)
                if not data['passed']:
                    no_pass.append(data)
    original_dataset=[]
    with open('/data/zlyuaj/muti-agent/fuzzing/data/HumanEval_test_case_ET.jsonl', 'r') as f:
        # 导入输出
        original_dataset = [json.loads(line) for line in f] 


    loaded_dataset=[]
    with open('/data/zlyuaj/muti-agent/fuzzing/output_mutated/original/code_round_0.jsonl', 'r') as f:
        # 导入输出
        loaded_dataset = [json.loads(line) for line in f]             
    # task_id=int(prompt_node.solution['task_id'].split('/')[-1])
    print(len(no_pass))
    for no_pass_data in no_pass:
        task_id=int(no_pass_data['task_id'].split('/')[-1])


        output_path='/data/zlyuaj/muti-agent/fuzzing/case_study/{}/{}.txt'.format(file_name,task_id)
        if not os.path.exists('/data/zlyuaj/muti-agent/fuzzing/case_study/{}'.format(file_name)):
            os.mkdir('/data/zlyuaj/muti-agent/fuzzing/case_study/{}'.format(file_name))
        with open(output_path,'w+') as f:
            f.write('-'*30+'\n')
            f.write(str(task_id))
            f.write('\n')

            f.write('-'*30+'\n')
            f.write('original prompt'+'\n')
            f.write('-'*30+'\n')
            f.write(loaded_dataset[task_id]['prompt']+'\n')

            f.write('-'*30+'\n')
            f.write('mutated prompt'+'\n')
            f.write('-'*30+'\n')
            f.write(no_pass_data['prompt']+'\n')

            f.write('-'*30+'\n')
            f.write('canonical solution'+'\n')
            f.write('-'*30+'\n')
            f.write(original_dataset[task_id]['canonical_solution']+'\n')

            
            for i  in range(len(loaded_dataset[task_id]['completions'])):
                completion = loaded_dataset[task_id]['completions'][i]
                history = loaded_dataset[task_id]['session_historys'][i]
                f.write('-'*30+'\n')
                f.write('original solutions {}'.format(i)+'\n')
                f.write('-'*30+'\n')
                f.write(history['plan']+'\n')
                f.write('-'*30+'\n')
                f.write(completion+'\n')
                # 写一个即可
                # if task_id!=55:
                #     break

            f.write('*'*100+'\n')

            f.write('-'*30+'\n')
            f.write('mutated solutions'+'\n')
            for i  in range(len(no_pass_data['completions'])):
                completion = no_pass_data['completions'][i]
                history = no_pass_data['session_historys'][i]
                f.write('-'*30+'\n')
                f.write('mutated solutions {}'.format(i)+'\n')
                f.write('-'*30+'\n')
                f.write(history['plan']+'\n')
                f.write('-'*30+'\n')
                f.write(completion+'\n')

            f.write('-'*30+'\n')
            f.write('scores'+'\n')
            f.write(str(no_pass_data['scores'])+'\n')
            f.write(str(no_pass_data['pass_test_cases_num'])+'\n')
            
            f.close()

    # break

    