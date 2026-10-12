import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
api_key = os.environ.get("GROQ_API_KEY")
from groq import Groq

client = Groq(api_key=api_key)

models_to_try = [
    "llama-3.2-1b-preview",
    "llama-3.2-3b-preview",
    "llama-3.1-8b-instant",
    "llama-3.1-70b-versatile",
    "llama3-70b-8192",
    "gemma2-9b-it",
    "mixtral-8x7b-32768",
    "qwen/qwen3.8-27b",
    "allam-2-7b"
]

for model in models_to_try:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=10
        )
        print(f"SUCCESS with {model}: {response.choices[0].message.content}")
        break
    except Exception as e:
        print(f"FAILED with {model}: {str(e)}")
