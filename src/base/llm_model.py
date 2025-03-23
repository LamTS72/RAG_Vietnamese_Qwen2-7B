import torch
from configparser import ConfigParser
from langchain_openai import ChatOpenAI

# Set OpenAI's API key and API base to use vLLM's API server.
config = ConfigParser()
config.read("config.ini")

openai_api_key = config.get("key", "openai_key")
openai_api_base = config.get("api", "chat_url") + "/v1"

def get_llm(model_name="Qwen/Qwen2.5-1.5B-Instruct",temp=0, max_tokens=1024):
    llm = ChatOpenAI(
        api_key="EMPTY",
        base_url=openai_api_base,
        model=model_name,
        temperature=temp,
        max_tokens=max_tokens
    )
    return llm

