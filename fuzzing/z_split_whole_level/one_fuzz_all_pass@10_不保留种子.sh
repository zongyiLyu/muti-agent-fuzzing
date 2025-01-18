python ../main_fuzz_passAt10.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo \
    --input_path /data/zlyuaj/muti-agent/fuzzing/output_mutated/original/code_round_0_with_score.jsonl \
    --output_path ../output_fuzzing_one_per_time/pass@10/split_input/whole_level/ \
    --do_fuzz 0  \
    --mutate_method random \
    --num_generate 10 \
    --num_round 10000 \
    --mutate_level whole \
    --split_input 1 \
    --save_seed 0 --clean_data 1 --output_file_name no_save_seed_cleaned_data | tee output_fuzz_pass@10_no_save_seed_cleaned_data.txt 
    # --majority 5 \
    
