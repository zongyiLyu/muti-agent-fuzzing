python ../main_fuzz_passAt10.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path /data/zlyuaj/muti-agent/fuzzing/output_mutated/original/code_round_0_with_score.jsonl \
    --output_path ../output_fuzzing_one_per_time/pass@10/split_input/sentence_level/ \
    --mutate_method random \
    --num_generate 10 \
    --num_round 10000 \
    --clean_data 1 \
    --beta 0.01\
    --mutate_level sentence \
    --split_input 1 \
    --output_file_name save_seed_by_passes_cleaned_data_0.01 --save_seed 1 | tee output_fuzz_pass@10_save_seed_by_passes_cleaned_data_0.01_1 .txt 
    # --majority 5 \
    
