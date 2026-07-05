import os
import openai
from typing import Optional
from src.config.env import get_settings

class LLMRouter:
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openrouter_api_key
        self.model_code = settings.openrouter_model

    def generate(self, provider: str, system_instruction: str, user_prompt: str, model: Optional[str] = None) -> str:
        """
        Generates content using the OpenRouter API provider.
        Ignores provider argument and uses OPENROUTER_MODEL from settings unless overridden.
        """
        model_to_use = model if model else self.model_code
        
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key
        )
        
        extra_body = {}
        if "qwen" in model_to_use.lower():
            extra_body["include_reasoning"] = False
            
        response = client.chat.completions.create(
            model=model_to_use,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=4096,
            extra_headers={
                "HTTP-Referer": "https://github.com/google-antigravity",
                "X-Title": "Vedic Astrology Report Engine"
            },
            extra_body=extra_body
        )
        return response.choices[0].message.content
