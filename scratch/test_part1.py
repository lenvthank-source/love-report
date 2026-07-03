import os
import sys
from google import genai
from google.genai import types
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.prompts.love_report_v2 import SYSTEM_PROMPT_PART1, USER_PROMPT_TEMPLATE_V2, PART_INSTRUCTIONS, WORD_TARGETS

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

with open("scratch/parsed_english_astrology.txt", "r", encoding="utf-8") as f:
    astrology_data = f.read()

user_prompt = USER_PROMPT_TEMPLATE_V2.format(
    part_number=1,
    part_instruction=PART_INSTRUCTIONS[1],
    astrology_data=astrology_data,
    word_target=WORD_TARGETS[1],
)

print(f"System Prompt Length: {len(SYSTEM_PROMPT_PART1)} chars")
print(f"User Prompt Length: {len(user_prompt)} chars")

configs = [
    ("Thinking Medium", types.ThinkingConfig(thinking_level="medium")),
    ("Thinking Low", types.ThinkingConfig(thinking_level="low")),
    ("No thinking_config", None),
]

for name, t_config in configs:
    print(f"\n--- Testing Config: {name} ---")
    try:
        config_args = {
            "system_instruction": SYSTEM_PROMPT_PART1,
            "temperature": 1.0,
            "max_output_tokens": 10000,
        }
        if t_config:
            config_args["thinking_config"] = t_config
            
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(**config_args)
        )
        print(f"Success! Response word count: {len(response.text.split())}")
        print(f"Preview: {response.text[:200]}...")
        break # stop if one succeeds
    except Exception as e:
        print(f"Failed: {e}")
