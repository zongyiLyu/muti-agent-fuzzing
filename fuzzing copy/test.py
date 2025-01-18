# at this step, you should be able to use huggingface inference and vllm inference, here we do a quick test
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '1,2' # specify which GPU(s) to be used
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from vllm import LLM
from vllm import SamplingParams

model_path = "meta-llama/Llama-2-7b-chat-hf"
tokenizer = AutoTokenizer.from_pretrained(model_path, padding_side='left', use_fast=False) # use_fast=False here for Llama
tokenizer.pad_token = tokenizer.eos_token

# load the model
sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=512,
            )

model_vllm = LLM(model=model_path, gpu_memory_utilization=0.85)  # it will automatically use the first GPU, if you would like to use multi-GPU, plz refer to vllm documentation
model_hf = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16, device_map='cuda:1').eval()
LLAMA2_PROMPT = {
    "description": "Llama 2 chat one shot prompt",
    "prompt": '''[INST] <<SYS>>
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe.  Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.
<</SYS>>

{instruction} [/INST] '''
}

prompt = ["What is the capital of France?", "What is the capital of Germany?", "What is the capital of Italy?"]

llama_input = []
for i in range(len(prompt)):
    llama_input.append(LLAMA2_PROMPT['prompt'].format(instruction=prompt[i]))

#vllm inference
vllm_output = model_vllm.generate(llama_input, sampling_params=sampling_params)
for output in vllm_output:
    generated_text = output.outputs[0].text
    print(f"Generated text by vllm: {generated_text!r}")

#huggingface inference
input_ids = tokenizer(llama_input, padding=True, return_tensors="pt")
input_ids['input_ids'] = input_ids['input_ids'].to('cuda:1')
input_ids['attention_mask'] = input_ids['attention_mask'].to('cuda:1')
num_input_tokens = input_ids['input_ids'].shape[1]
outputs = model_hf.generate(input_ids['input_ids'],attention_mask=input_ids['attention_mask'].half(),
                         max_new_tokens=512, do_sample=False, pad_token_id=tokenizer.pad_token_id)
generation = tokenizer.batch_decode(outputs[:, num_input_tokens:], skip_special_tokens=True)
print(generation)