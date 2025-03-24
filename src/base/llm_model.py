import torch
from configparser import ConfigParser
from langchain_openai import ChatOpenAI
import os


# Set OpenAI's API key and API base to use vLLM's API server.
config = ConfigParser()
config.read("config.ini")

openai_api_key = config.get("key", "openai_key")
openai_api_base = config.get("api", "chat_url") + "/v1"

# Configure LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = config.get("key", "langsmith_key", fallback="")
os.environ["LANGCHAIN_PROJECT"] = config.get("langsmith", "project_name", fallback="rag-vietnamese")
def get_llm(model_name="Qwen/Qwen2.5-1.5B-Instruct",temp=0, max_tokens=1024):
    # llm = ChatOpenAI(
    #     api_key="EMPTY",
    #     base_url=openai_api_base,
    #     model=model_name,
    #     temperature=temp,
    #     max_tokens=max_tokens
    # )
    llm = ChatOpenAI(
        api_key="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",
        base_url="https://openrouter.ai/api/v1",
        model="qwen/qwen-2.5-72b-instruct:free",
        temperature=temp,
        max_tokens=max_tokens
    )
    return llm

