# update check_models.py
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GOOGLE_API_KEY"),
    http_options=types.HttpOptions(api_version="v1")
)

print("ALL available models:")
for model in client.models.list():
    print(f"  {model.name}")