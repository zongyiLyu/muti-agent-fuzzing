python main_fuzz_passAt10.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path /data/zlyuaj/muti-agent/fuzzing/output_mutated/original/code_round_0_with_score.jsonl \
    --output_path ./output_fuzzing_one_per_time/pass@10/ \
    --do_fuzz 0  \
    --mutate_method random \
    --num_generate 10 \
    --num_round 1000 \
    --save_seed 0 | tee output_fuzz_pass@10_no_save_seed_clean_data_2.txt 
    # --majority 5 \
    
