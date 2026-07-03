import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Listing models:")
for model in client.models.list():
    if "flash" in model.name or "thinking" in model.name:
        print(f"Model: {model.name}, supported_actions: {model.supported_actions}")
