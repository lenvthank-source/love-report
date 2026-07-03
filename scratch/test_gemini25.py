import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hello, give me a 1 sentence greeting.",
    )
    print(f"Success on gemini-2.5-flash: {response.text.strip()}")
except Exception as e:
    print(f"Failed on gemini-2.5-flash: {e}")
