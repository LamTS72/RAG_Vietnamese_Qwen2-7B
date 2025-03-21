import torch
from configparser import ConfigParser
from langchain_openai import ChatOpenAI
# Set OpenAI's API key and API base to use vLLM's API server.
config = ConfigParser()
config.read("config.ini")

openai_api_key = config.get("key", "openai_key")
openai_api_base = "https://openrouter.ai/api/v1"

def get_llm(model_name="qwen/qwen-2-7b-instruct:free",temp=0, max_tokens=500):
    llm = ChatOpenAI(
        api_key=openai_api_key,
        base_url=openai_api_base,
        model=model_name,
        temperature=temp,
        max_tokens=max_tokens
    )
    return llm
