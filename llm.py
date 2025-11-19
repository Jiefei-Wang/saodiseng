# This script will be called whenever we need LLM access
from openai import OpenAI

client = OpenAI(base_url="http://localhost:1234/v1",
    api_key='test')
model_name = "qwen3-30b-a3b-instruct-2507"