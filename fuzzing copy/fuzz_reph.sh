python main.py --dataset humaneval \
    --signature \
    --model gpt-3.5-turbo-0301 \
    --input_path data/HumanEval_test_case_ET.jsonl \
    --output_path ./output_mutated/rephrase/ \
    --mutate_method rephrase \
    --num_generate 5 \
    --num_round 3 \
    | tee output_rephrase.txt 
