from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

model_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_id)

# quant to half precision to lighten GPU load
model = AutoModelForCausalLM.from_pretrained(
    model_id, torch_dtype=torch.float16, device_map="auto"
)
messages = [
    {"role": "user", "content": "What is your favourite condiment?"},
    {
        "role": "assistant",
        "content": "Well, I'm quite partial to a good squeeze of fresh lemon juice. It adds just the right amount of zesty flavour to whatever I'm cooking up in the kitchen!",
    },
    {"role": "user", "content": "Do you have mayonnaise recipes?"},
]

inputs = tokenizer.apply_chat_template(messages, return_tensors="pt").to("cuda")

outputs = model.generate(inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))

torch.cuda_is
