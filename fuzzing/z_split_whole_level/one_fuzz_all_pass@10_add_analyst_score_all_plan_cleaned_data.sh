python ../main_fuzz_passAt10.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path /data/zlyuaj/muti-agent/fuzzing/output_mutated/original/code_round_0_with_score.jsonl \
    --output_path ../output_fuzzing_one_per_time/pass@10/split_input/whole_level/ \
    --do_fuzz 0  \
    --only_consider_passed_cases 0 --mutate_method random \
    --num_generate 10 \
    --num_round 10000 \
    --clean_data 1 \
    --calc_analyst 1 \
    --calc_relative_reward 1 \
    --mutate_level whole \
    --split_input 1 \
    --save_seed 1 --output_file_name analyst_score_all_plan_cleaned_data  | tee output_fuzz_pass@10_analyst_score_all_plan_cleaned_data_3.txt 
    # --majority 5 \
    
