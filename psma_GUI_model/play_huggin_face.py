import transformers
import torch
from huggingface_hub import login
import asyncio
from transformers import AutoTokenizer, AutoModelForCausalLM

# Safely handle asyncio event loop to prevent conflicts with Streamlit
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        print("Event loop is running, creating a new one for model loading")
        asyncio.set_event_loop(asyncio.new_event_loop())
except RuntimeError:
    # No event loop exists, create a new one
    asyncio.set_event_loop(asyncio.new_event_loop())

token_path="/workspaces/practical_radio_ai/hugging_face_key.txt"
with open(token_path, "r") as file:
    token = file.read().strip()
    
login(token=token)

# model_name = "meta-llama/Meta-Llama-3-8B-Instruct"
# model_name = "ibm-granite/granite-3.1-3b-a800m-instruct"
model_name = "ibm-granite/granite-3.2-8b-instruct-preview"
# model_name = "huihui-ai/granite-3.2-2b-instruct-abliterated"
#granite with uncertanity https://huggingface.co/ibm-granite/granite-uncertainty-3.0-8b-lora

#"unsloth/Llama-3.2-3B-Instruct-bnb-4bit"


model = AutoModelForCausalLM.from_pretrained(
    model_name, device_map="cuda"
)#, load_in_4bit=True
tokenizer = AutoTokenizer.from_pretrained(model_name, padding_side="left")
tokenizer.pad_token = tokenizer.eos_token  # Most LLMs don't have a pad token by default
model_inputs = tokenizer(
    ["A list of colors: red, blue", "Portugal is"], return_tensors="pt", padding=True
).to("cuda")
generated_ids = model.generate(**model_inputs)
res=tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
print(res)


