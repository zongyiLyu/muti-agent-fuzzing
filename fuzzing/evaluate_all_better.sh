for i in {7..9}
do
python evaluate/all_evaluate.py \
    --input_path /data/zlyuaj/muti-agent/fuzzing/output_mutated/better/code_round_${i}.jsonl \
    --output_path output_result/better/
done