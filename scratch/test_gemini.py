import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

configs = [
    ("Default (No Thinking Config)", None),
    ("Thinking Low", types.ThinkingConfig(thinking_level="low")),
    ("Thinking Medium", types.ThinkingConfig(thinking_level="medium")),
]

for name, t_config in configs:
    print(f"\nTesting: {name}")
    try:
        config_args = {
            "temperature": 1.0,
            "max_output_tokens": 1000,
        }
        if t_config:
            config_args["thinking_config"] = t_config
            
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents="Hello, give me a 1 sentence greeting.",
            config=types.GenerateContentConfig(**config_args)
        )
        print(f"Success! Response: {response.text.strip()}")
    except Exception as e:
        print(f"Failed: {e}")
