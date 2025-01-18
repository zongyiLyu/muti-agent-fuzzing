python ../main_fuzz_passAt10.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path /data/zlyuaj/muti-agent/fuzzing/output_mutated/original/code_round_0_with_score.jsonl \
    --output_path ../output_fuzzing_one_per_time/pass@10/split_input/sentence_level/ \
    --do_fuzz 0  \
    --only_consider_passed_cases 0 --mutate_method random \
    --num_generate 10 \
    --alpha 2 \
    --clean_data 1 \
    --num_round 10000 \
    --calc_analyst 1 \
    --mutate_level sentence \
    --split_input 1 \
    --with_reference 1 \
    --llm_critic gpt4 \
    --save_seed 1 --output_file_name analyst_score_2-1_original_plan_cleaned_data_gpt4_reference | tee output_fuzz_pass@10_analyst_score_2-1_original_plan_gpt4_reference_2.txt 
    # --majority 5 \
    
