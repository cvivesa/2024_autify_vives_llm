from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import pipeline
import torch

model = "codellama/CodeLlama-7b-hf"
print(torch.__version__)
print(torch.cuda.is_available())
'''tokenizer = AutoTokenizer.from_pretrained(model)
pipeline = transformers.pipeline(
    "text-generation",
    model=model,
    tokenizer= tokenizer,
    torch_dtype=torch.float16,
    device_map="auto",
    max_length = 200
)
sequences = pipeline(
    'def get_factorial(i: int):\n    """<FILL_ME>\n    return result',
    do_sample=True,
    top_k=10,
    temperature=0.1,
    top_p=0.95,
    num_return_sequences=1,
    eos_token_id=tokenizer.eos_token_id,
    max_length=200,
)

for seq in sequences:
    print(f"Result: {seq['generated_text']}")'''
'''generator = pipeline("text-generation",model="codellama/CodeLlama-7b-hf",torch_dtype=torch.float16, device_map="auto")
print(generator('def remove_non_ascii(s: str) -> str:\n    """ <FILL_ME>\n    return result', max_new_tokens = 128))'''
'''tokenizer = AutoTokenizer.from_pretrained("codellama/CodeLlama-7b-hf")
model = AutoModelForCausalLM.from_pretrained("codellama/CodeLlama-7b-hf")
PROMPT = '''def remove_non_ascii(s: str) -> str:
    """ <FILL_ME>
    return result
'''
input_ids = tokenizer(PROMPT, return_tensors="pt")["input_ids"]
generated_ids = model.generate(input_ids, max_new_tokens=128)
filling = tokenizer.batch_decode(generated_ids[:, input_ids.shape[1]:], skip_special_tokens = True)[0]
print(PROMPT.replace("<FILL_ME>", filling))'''
