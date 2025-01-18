python main.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path data/HumanEval_test_case_ET.jsonl \
    --do_fuzz false  \
    --output_path ./output_mutated/worse/ \
    --mutate_method random \
    --num_generate 5 \
    --num_round 10 | tee output_random_worse.txt 
    # --majority 5 \
    
