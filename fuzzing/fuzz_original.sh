python main.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path data/HumanEval_test_case_ET.jsonl \
    --do_fuzz 0  \
    --output_path ./output_mutated/original/ \
    --mutate_method no \
    --num_generate 10 \
    --num_round 1 | tee output_test_original_dataset.txt 
    # --majority 5 \
    
