import json
import os
file_names=os.listdir('.')

results=[]
for file_path in file_names:
    if 'results'  not in file_path:
        continue
    result_file = file_path + '/final_result.jsonl'
    with open(result_file,'r') as f:
        result = [json.loads(line) for line in f]
        result = [result[i] for i in range(len(result)) if i%2==1]
        results.append(result)
print(results)
print([i[-1] for i in results])
