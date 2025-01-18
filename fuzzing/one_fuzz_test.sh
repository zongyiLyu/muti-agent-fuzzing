
python main_fuzz_passAt10.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path /data/zlyuaj/muti-agent/fuzzing/output_mutated/original/code_round_0_with_score.jsonl \
    --output_path ./output_fuzzing_one_per_time/test/ \
    --do_fuzz 0  \
    --only_consider_passed_cases 0 --mutate_method random \
    --num_generate 1 \
    --clean_data 1 \
    --num_round 1000 \
    --calc_analyst 1 \
    --calc_original_plan 1 \
    --split_input 1\
    --mutate_level whole \
    --output_file_name output_fuzz_test_select \
    | tee output_fuzz_test_select.txt 
    # --majority 5 \
    
