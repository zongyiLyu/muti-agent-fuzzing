python main_fuzz_passAt10.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path /data/zlyuaj/muti-agent/fuzzing/output_mutated/original/code_round_0_with_score.jsonl \
    --output_path ./output_fuzzing_one_per_time/pass@10/ \
    --do_fuzz 0  \
    --only_consider_passed_cases 0 --mutate_method random \
    --num_generate 10 \
    --alpha 1 \
    --clean_data 1 \
    --num_round 1000 \
    --calc_analyst 1 \
    --save_seed 1 | tee output_fuzz_pass@10_analyst_score_1-1_all_plan_cleaned_data_0_threshlod-2.txt 
    # --majority 5 \
    
