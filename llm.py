# This script will be called whenever we need LLM access
from openai import OpenAI
import dotenv
import os

dotenv.load_dotenv(override=True)

client = OpenAI(base_url="http://localhost:1234/v1",
    api_key='test')
model_name = "qwen3-30b-a3b-instruct-2507"


# client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
# model_name = "gpt-5-mini-2025-08-07"