from typing import Optional, List
from google import genai
from google.genai import types
from src.config.env import get_settings

class GeminiService:
    def __init__(self, api_key: Optional[str] = None, model: str = 'gemini-3.1-flash-lite'):
        """Initializes the Gemini service using Google GenAI SDK."""
        settings = get_settings()
        key = api_key or settings.gemini_api_key
        self.client = genai.Client(api_key=key)
        self.model = model

    def create_astrology_cache(self, global_system_instruction: str, astrology_data: str, reference_guide: str) -> str:
        """
        Creates a context cache containing the system instruction, the astrological data,
        and the astrology reference guide.
        """
        print(f"  📦 Creating Context Cache for model {self.model}...")
        
        # Combine the reference guide and astrology data into the cache contents
        combined_context = f"""
---BEGIN SYSTEM REFERENCE & INSTRUCTIONS---
{global_system_instruction}
---END SYSTEM REFERENCE & INSTRUCTIONS---

---BEGIN ASTROLOGICAL REFERENCE GUIDE---
{reference_guide}
---END ASTROLOGICAL REFERENCE GUIDE---

---BEGIN INDIVIDUAL ASTROLOGY DATA---
{astrology_data}
---END INDIVIDUAL ASTROLOGY DATA---
"""
        
        try:
            cache = self.client.caches.create(
                model=self.model,
                config=types.CreateCachedContentConfig(
                    system_instruction=global_system_instruction,
                    contents=[
                        types.Content(
                            role="user",
                            parts=[types.Part.from_text(text=combined_context)]
                        )
                    ],
                    ttl="900s",  # Keep alive for 15 minutes to allow parallel execution and assembly
                    display_name="love_report_astrology_cache"
                )
            )
            print(f"  ✅ Cache created successfully: {cache.name}")
            return cache.name
        except Exception as e:
            raise RuntimeError(f"Failed to create Gemini Context Cache: {e}")

    def generate_report_cached(self, cache_name: str, user_prompt: str) -> str:
        """
        Generates content referencing a context cache using the thinking model.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    temperature=1.0,
                    max_output_tokens=65536,
                    cached_content=cache_name,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="medium"
                    ),
                ),
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API cached generation failed: {e}")

    def generate_report_direct(self, system_instruction: str, contents: str, user_prompt: str) -> str:
        """
        Generates content directly without referencing a cache.
        """
        combined_contents = f"{contents}\n\n{user_prompt}"
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=combined_contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=1.0,
                    max_output_tokens=65536,
                    thinking_config=types.ThinkingConfig(
                        thinking_level="medium"
                    ),
                ),
            )
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini API direct generation failed: {e}")

    def delete_cache(self, cache_name: str):
        """Deletes the specified context cache to clean up resources."""
        print(f"  🗑️ Cleaning up Context Cache: {cache_name}...")
        try:
            self.client.caches.delete(name=cache_name)
            print("  ✅ Context Cache deleted successfully.")
        except Exception as e:
            print(f"  ⚠️ Warning: Failed to delete Context Cache {cache_name}: {e}")
