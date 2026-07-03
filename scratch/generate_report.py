#!/usr/bin/env python3
"""
Premium 25-Page Love Compatibility Report Generator
====================================================
Reads parsed astrology text and generates a full report via
3 sequential Gemini 3.5 Flash (thinking) API calls.

Usage:
    python scratch/generate_report.py
"""

import os
import sys
import time
import io

# Force UTF-8 stdout on Windows to handle emoji output
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.services.gemini_service import GeminiService
from src.prompts.love_report_v2 import (
    SYSTEM_PROMPT_PART1,
    SYSTEM_PROMPT_PART2,
    SYSTEM_PROMPT_PART3,
    USER_PROMPT_TEMPLATE_V2,
    PART_INSTRUCTIONS,
    WORD_TARGETS,
)


def load_astrology_data(filepath: str) -> str:
    """Load the parsed astrology text file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def build_user_prompt(part_number: int, astrology_data: str) -> str:
    """Build the user prompt for a specific part."""
    return USER_PROMPT_TEMPLATE_V2.format(
        part_number=part_number,
        part_instruction=PART_INSTRUCTIONS[part_number],
        astrology_data=astrology_data,
        word_target=WORD_TARGETS[part_number],
    )


def generate_full_report():
    """Generate the complete 25-page report in 3 sequential API calls."""
    
    print("=" * 60)
    print("🔮 PREMIUM LOVE COMPATIBILITY REPORT GENERATOR")
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
    
    gemini = GeminiService(api_key=api_key, model="gemini-3.5-flash")
    print(f"✅ Gemini service initialized (model: gemini-3.5-flash)")
    print()
    
    # 3. Generate 3 parts sequentially
    system_prompts = {
        1: SYSTEM_PROMPT_PART1,
        2: SYSTEM_PROMPT_PART2,
        3: SYSTEM_PROMPT_PART3,
    }
    
    parts = {}
    total_words = 0
    
    for part_num in [1, 2, 3]:
        print(f"{'─' * 50}")
        print(f"📝 PART {part_num} of 3 — Sections {get_section_range(part_num)}")
        print(f"{'─' * 50}")
        
        system_prompt = system_prompts[part_num]
        user_prompt = build_user_prompt(part_num, astrology_data)
        
        # Retry with backoff — model fallback happens inside GeminiService
        max_retries = 3
        retry_delays = [60, 120, 180]
        success = False
        
        for attempt in range(max_retries + 1):
            start_time = time.time()
            try:
                text = gemini.generate_report_part(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    part_label=f"Part {part_num}" + (f" (retry {attempt})" if attempt > 0 else "")
                )
                elapsed = time.time() - start_time
                word_count = len(text.split())
                total_words += word_count
                
                parts[part_num] = text
                print(f"  ⏱️  Generated in {elapsed:.1f}s")
                print()
                success = True
                break
                
            except Exception as e:
                error_str = str(e)
                if ("503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str) and attempt < max_retries:
                    delay = retry_delays[attempt]
                    print(f"  ⚠️  Model overloaded/rate-limited (attempt {attempt + 1}/{max_retries + 1}). Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    print(f"  ❌ FATAL: Part {part_num} failed after {attempt + 1} attempts: {e}")
                    print("  Saving whatever we have so far...")
                    break
        
        if not success:
            break
        
        # Delay between calls to avoid rate limiting
        if part_num < 3:
            print("  ⏳ Pausing 60s before next part...")
            time.sleep(60)
    
    # 4. Concatenate and save
    print(f"{'=' * 60}")
    print(f"📊 REPORT SUMMARY")
    print(f"{'=' * 60}")
    
    full_report = ""
    for part_num in sorted(parts.keys()):
        if part_num > 1:
            full_report += "\n\n"
        full_report += parts[part_num]
    
    total_words = len(full_report.split())
    total_chars = len(full_report)
    estimated_pages = total_words / 300  # ~300 words per page
    
    print(f"  Total words:    {total_words:,}")
    print(f"  Total chars:    {total_chars:,}")
    print(f"  Est. pages:     {estimated_pages:.1f}")
    print(f"  Parts generated: {len(parts)}/3")
    print()
    
    # 5. Save output (only if we generated something)
    if not parts:
        print("❌ No parts generated. Skipping file save to preserve any existing report.")
        return
    
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "aarav_meera_report.md")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_report)
    
    print(f"✅ Report saved to: {output_path}")
    print(f"   File size: {os.path.getsize(output_path):,} bytes")
    print()
    
    # 6. Quick validation
    validate_report(full_report)


def get_section_range(part_num: int) -> str:
    """Get human-readable section range for a part."""
    ranges = {1: "1-8", 2: "9-16", 3: "17-22"}
    return ranges.get(part_num, "?")


def validate_report(report: str):
    """Quick validation of the generated report."""
    print(f"{'─' * 50}")
    print("🔍 VALIDATION")
    print(f"{'─' * 50}")
    
    # Check for key section headers (flexible matching)
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
    
    # Check for correct Aarav data
    if "7th position" in report or "7th" in report:
        print("  ✅ Aarav's 7th position reference found")
    else:
        print("  ⚠️  Aarav's 7th position reference not found — verify manually")
    
    if "libra" in report_lower or "tula" in report_lower:
        print("  ✅ Libra/Tula sign reference found")
    else:
        print("  ⚠️  Libra/Tula reference not found — verify manually")
    
    print()
    print("🎉 DONE! Open the report to review.")


if __name__ == "__main__":
    generate_full_report()
