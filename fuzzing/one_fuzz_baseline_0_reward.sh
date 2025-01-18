python main_fuzz_baseline_0_reward.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path data/HumanEval_test_case_ET.jsonl \
    --output_path ./output_fuzzing_one_per_time/all/ \
    --do_fuzz 0  \
    --mutate_method random \
    --num_generate 10 \
    --num_round 1000 \
    | tee output_fuzz_baseline_0_reward.txt 
    # --majority 5 \
    
