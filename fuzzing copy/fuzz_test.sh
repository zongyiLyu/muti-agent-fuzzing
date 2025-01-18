python main.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path data/HumanEval_test_case_ET_simple.jsonl \
    --output_path ./output_mutated/test/ \
    --do_fuzz 0  \
    --mutate_method random \
    --num_generate 2 \
    --num_round 1 \
    | tee output_test.txt 
    # --majority 5 \
    
