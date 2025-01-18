for i in {8..9}
do
python evaluate/all_evaluate.py \
    --input_path /data/zlyuaj/muti-agent/fuzzing/output_mutated/run/code_round_${i}.jsonl \
    --output_path output_result/run/
done