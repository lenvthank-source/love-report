import os
import sys
import time
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

# Force UTF-8 stdout on Windows to handle emoji output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.services.gemini_service import GeminiService
from src.prompts.love_report_v3 import (
    GLOBAL_SYSTEM_INSTRUCTION,
    ASTROLOGY_REFERENCE_GUIDE,
    PART_USER_PROMPTS,
)


def load_astrology_data(filepath: str) -> str:
    """Load the parsed astrology text file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def generate_part(gemini: GeminiService, cache_name: Optional[str], part_num: int, global_system_instruction: str, combined_context: str) -> tuple:
    """Worker function to generate a specific part using the context cache (or direct fallback)."""
    print(f"🚀 [Part {part_num}/4] Starting API request...")
    start_time = time.time()
    try:
        user_prompt = PART_USER_PROMPTS[part_num]
        if cache_name:
            text = gemini.generate_report_cached(cache_name=cache_name, user_prompt=user_prompt)
        else:
            text = gemini.generate_report_direct(
                system_instruction=global_system_instruction,
                contents=combined_context,
                user_prompt=user_prompt
            )
        elapsed = time.time() - start_time
        word_count = len(text.split())
        print(f"✅ [Part {part_num}/4] Completed in {elapsed:.1f}s — {word_count} words")
        return part_num, text, None
    except Exception as e:
        print(f"❌ [Part {part_num}/4] Failed: {e}")
        return part_num, "", e


def generate_report():
    print("=" * 60)
    print("🔮 PARALLEL PREMIUM LOVE REPORT GENERATOR (V3)")
    print("=" * 60)
    
    # 1. Load astrology data
    astro_file = "scratch/parsed_english_astrology.txt"
    if not os.path.exists(astro_file):
        print(f"❌ Astrology data file not found: {astro_file}")
        sys.exit(1)
        
    astrology_data = load_astrology_data(astro_file)
    print(f"✅ Loaded astrology data ({len(astrology_data)} chars)")
    print()
    
    # 2. Initialize Gemini service
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        sys.exit(1)
        
    gemini = GeminiService(api_key=api_key, model="gemini-3.1-flash-lite")
    print(f"✅ Gemini service initialized (model: gemini-3.1-flash-lite)")
    print()
    
    cache_name = None
    parts = {}
    
    # Create the combined context for fallback direct generation
    combined_context = f"""
---BEGIN SYSTEM REFERENCE & INSTRUCTIONS---
{GLOBAL_SYSTEM_INSTRUCTION}
---END SYSTEM REFERENCE & INSTRUCTIONS---

---BEGIN ASTROLOGICAL REFERENCE GUIDE---
{ASTROLOGY_REFERENCE_GUIDE}
---END ASTROLOGICAL REFERENCE GUIDE---

---BEGIN INDIVIDUAL ASTROLOGY DATA---
{astrology_data}
---END INDIVIDUAL ASTROLOGY DATA---
"""
    
    try:
        # 3. Create context cache
        start_cache_time = time.time()
        try:
            cache_name = gemini.create_astrology_cache(
                global_system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
                astrology_data=astrology_data,
                reference_guide=ASTROLOGY_REFERENCE_GUIDE
            )
            print(f"  ⏱️ Cache preparation took {time.time() - start_cache_time:.1f}s")
        except Exception as cache_err:
            print(f"  ℹ️ Context Caching not supported on this API key tier ({cache_err}).")
            print("     Falling back to direct context-passing for parallel workers.")
            cache_name = None
        print()
        
        # 4. Run 4 parallel requests
        print("📡 Dispatching 4 parallel requests to Gemini API...")
        print()
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    generate_part, 
                    gemini, 
                    cache_name, 
                    i, 
                    GLOBAL_SYSTEM_INSTRUCTION, 
                    combined_context
                )
                for i in [1, 2, 3, 4]
            ]
            
            for future in as_completed(futures):
                part_num, text, error = future.result()
                if error is None:
                    parts[part_num] = text
                    
        # 5. Verify and Assemble
        if len(parts) < 4:
            print(f"❌ Error: Only {len(parts)}/4 parts generated successfully. Aborting save.")
            return
            
        full_report = ""
        for part_num in sorted(parts.keys()):
            if part_num > 1:
                full_report += "\n\n"
            full_report += parts[part_num]
            
        total_words = len(full_report.split())
        estimated_pages = total_words / 300
        
        print()
        print(f"{'=' * 60}")
        print(f"📊 REPORT SUMMARY")
        print(f"{'=' * 60}")
        print(f"  Total words:    {total_words:,}")
        print(f"  Est. pages:     {estimated_pages:.1f}")
        print(f"  Parts generated: {len(parts)}/4")
        print()
        
        # Save output
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "dev_ishita_report.md")
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_report)
            
        print(f"✅ Report saved to: {output_path}")
        print(f"   File size: {os.path.getsize(output_path):,} bytes")
        print()
        
        # Validate sections
        validate_report(full_report)
        
    finally:
        # 6. Delete cache resource
        if cache_name:
            gemini.delete_cache(cache_name)


def validate_report(report: str):
    """Quick validation of the generated report."""
    print(f"{'─' * 50}")
    print("🔍 VALIDATION")
    print(f"{'─' * 50}")
    
    expected_keywords = [
        "Cosmic Cover",
        "DNA Card",
        "Blueprint",
        "Nakshatra",
        "Attachment",
        "Love Language",
        "Shadow",
        "Emotional Intelligence",
        "Compatibility",
        "Persona",
        "Conflict",
        "Ex Analysis",
        "Obsession",
        "Texting",
        "Intimacy",
        "Money",
        "Trigger",
        "Power Dynamic",
        "Long Term",
        "Forecast",
        "Ritual",
        "Final",
    ]
    
    report_lower = report.lower()
    found = 0
    missing = []
    for kw in expected_keywords:
        if kw.lower() in report_lower:
            found += 1
        else:
            missing.append(kw)
            
    print(f"  Sections found: {found}/{len(expected_keywords)}")
    if missing:
        print(f"  ⚠️  Possibly missing: {', '.join(missing)}")
    else:
        print("  🎉 All 22 premium sections validated!")
    print()


if __name__ == "__main__":
    generate_report()
