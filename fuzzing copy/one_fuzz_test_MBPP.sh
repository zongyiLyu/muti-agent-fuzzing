python main_fuzz_passAt10_baseDataset.py --dataset MBPP \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path /data/zlyuaj/muti-agent/fuzzing/data/MBPP_ET_simple.jsonl \
    --output_path ./output_fuzzing_one_per_time/test/ \
    --do_fuzz 0  \
    --only_consider_passed_cases 0 --mutate_method random \
    --num_generate 10 \
    --clean_data 1 \
    --dataset_type MBPP \
    --num_round 1000 \
    --calc_analyst 1 \
    --output_file_name MBPP_all_result \
    | tee output_fuzz_test_select.txt 
    # --majority 5 \
    
