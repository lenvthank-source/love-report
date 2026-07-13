import os
import openai
import re
from typing import Optional
from src.config.env import get_settings
from src.utils.markdown_parser import strip_thinking_tags

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
        print(f"[LLMRouter] Querying OpenRouter using model: {model_to_use}")
        
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

    def generate_with_retry(
        self, 
        provider: str, 
        system_instruction: str, 
        user_prompt: str, 
        min_words: int, 
        max_words: int, 
        model: Optional[str] = None
    ) -> str:
        """
        Wrapper around generate that enforces word count limits with up to 3 retry attempts.
        Keeps track of the best response generated so far, and truncates it to fit the page
        in case all attempts fall slightly outside the bounds or transiently fail.
        """
        model_to_use = model if model else self.model_code
        
        best_text = ""
        best_distance = 999999
        
        for attempt in range(1, 4):
            try:
                current_prompt = user_prompt
                if attempt > 1:
                    current_prompt += (
                        f"\n\n[RETRY ATTEMPT {attempt}] CRITICAL: Your previous response was outside the "
                        f"required word count limits. You MUST write strictly between {min_words} and {max_words} words. "
                        f"Ensure your response is exactly one or two short paragraphs and ends with a period."
                    )
                
                raw_text = self.generate(provider, system_instruction, current_prompt, model_to_use)
                cleaned_text = strip_thinking_tags(raw_text).strip()
                
                word_count = len(cleaned_text.split())
                print(f"[LLMRouter] Attempt {attempt}: Generated {word_count} words (limit: {min_words}-{max_words}).")
                
                if word_count > 5:
                    if min_words <= word_count <= max_words:
                        return cleaned_text
                    
                    # Compute distance from bounds
                    distance = min(abs(word_count - min_words), abs(word_count - max_words))
                    if distance < best_distance:
                        best_distance = distance
                        best_text = cleaned_text
            except Exception as e:
                print(f"[LLMRouter] Attempt {attempt} failed with error: {e}")
                
        # If we have a decent backup response, truncate it at the last sentence and return it
        if best_text:
            word_count = len(best_text.split())
            if word_count > max_words:
                sentences = re.split(r'(?<=[.!?])\s+', best_text)
                truncated_words = []
                for s in sentences:
                    s_words = s.split()
                    if len(truncated_words) + len(s_words) <= max_words:
                        truncated_words.extend(s_words)
                    else:
                        break
                if truncated_words:
                    return " ".join(truncated_words)
            return best_text
            
        # Standard safety backup if the API fails entirely on all retries
        return (
            "This phase of your cosmic journey, calibrated to align with the stars, invites you to reflect "
            "on your path, release emotional shadow patterns, and welcome love with an open and peaceful heart. "
            "Trust in the divine timing of your placements to guide you."
        )
