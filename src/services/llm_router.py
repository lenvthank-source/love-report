import os
import openai
from typing import Optional
from src.services.gemini_service import GeminiService

class LLMRouter:
    def __init__(self):
        gemini_key = os.getenv("GEMINI_API_KEY")
        self.gemini_service = None
        if gemini_key:
            self.gemini_service = GeminiService(api_key=gemini_key, model="gemini-3.1-flash-lite")

    def generate(self, provider: str, system_instruction: str, user_prompt: str, model: Optional[str] = None) -> str:
        provider = provider.lower().strip()
        
        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("Gemini API key is not configured (GEMINI_API_KEY).")
            model_code = model if model else "gemini-3.1-flash-lite"
            service = GeminiService(api_key=api_key, model=model_code)
            return service.generate_report_direct(
                system_instruction=system_instruction,
                contents="",
                user_prompt=user_prompt
            )
            
        elif provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("Groq API key is not configured (GROQ_API_KEY).")
            model_code = model if model else "openai/gpt-oss-120b"
            client = openai.OpenAI(
                base_url="https://api.groq.com/openai/v1",
                api_key=api_key
            )
            extra_body = {}
            if "qwen" in model_code.lower():
                extra_body["reasoning_format"] = "hidden"
            response = client.chat.completions.create(
                model=model_code,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4096,
                extra_body=extra_body
            )
            return response.choices[0].message.content
            
        elif provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError("OpenRouter API key is not configured (OPENROUTER_API_KEY).")
            model_code = model if model else "google/gemma-4-31b-it:free"
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )
            extra_body = {}
            if "qwen" in model_code.lower():
                extra_body["include_reasoning"] = False
            response = client.chat.completions.create(
                model=model_code,
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
            
        else:
            raise ValueError(f"Unknown AI provider: '{provider}'. Available options: gemini, groq, openrouter.")
