#!/usr/bin/env python3
"""
Parallel Premium Love Compatibility Report Generator (V4)
=========================================================
Uses Gemini 3.1 Flash Lite to generate the report using 5 parallel
requests, with dynamic name injection and a casual, personal tone.

Usage:
    python scratch/generate_parallel_report_v4.py
"""

import os
import sys
import time
import io
import json
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
from src.prompts.love_report_v4 import (
    GLOBAL_SYSTEM_INSTRUCTION,
    PART_USER_PROMPTS,
    USER_PROMPT_TEMPLATE_V4,
)


def load_astrology_data(filepath: str) -> str:
    """Load the parsed astrology text file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def generate_part(gemini: GeminiService, part_num: int, user_prompt: str) -> tuple:
    """Worker function to generate a specific part directly with retries."""
    max_retries = 3
    retry_delays = [10, 20, 40]
    
    for attempt in range(max_retries + 1):
        print(f"🚀 [Part {part_num}/5] Starting API request (Attempt {attempt + 1}/{max_retries + 1})...")
        start_time = time.time()
        try:
            text = gemini.generate_report_direct(
                system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
                contents="",  # Everything is passed in the formatted user prompt
                user_prompt=user_prompt
            )
            elapsed = time.time() - start_time
            word_count = len(text.split())
            print(f"✅ [Part {part_num}/5] Completed in {elapsed:.1f}s — {word_count} words")
            return part_num, text, None
        except Exception as e:
            error_str = str(e)
            if ("503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str) and attempt < max_retries:
                delay = retry_delays[attempt]
                print(f"  ⚠️ [Part {part_num}/5] Temporary API error: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"❌ [Part {part_num}/5] Failed after {attempt + 1} attempts: {e}")
                return part_num, "", e


def generate_report():
    print("=" * 60)
    print("🔮 PARALLEL PREMIUM LOVE REPORT GENERATOR (V4 — 5 PARTS)")
    print("=" * 60)
    
    # 1. Load config birth details
    config_file = "sample/input.json"
    if not os.path.exists(config_file):
        print(f"❌ Input configuration not found: {config_file}")
        sys.exit(1)
        
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    p1 = config["primary"]["name"]
    p2 = config["secondary"]["name"]
    p1_details = f"{config['primary']['gender']}, born {config['primary']['dateOfBirth']} at {config['primary']['timeOfBirth']} in {config['primary']['placeOfBirth']}"
    p2_details = f"{config['secondary']['gender']}, born {config['secondary']['dateOfBirth']} at {config['secondary']['timeOfBirth']} in {config['secondary']['placeOfBirth']}"
    
    print(f"👥 Couples: {p1} & {p2}")
    print(f"   {p1}: {p1_details}")
    print(f"   {p2}: {p2_details}")
    print()
    
    # 2. Load astrology data
    astro_file = "scratch/parsed_english_astrology.txt"
    if not os.path.exists(astro_file):
        print(f"❌ Astrology data file not found: {astro_file}")
        sys.exit(1)
        
    astrology_data = load_astrology_data(astro_file)
    print(f"✅ Loaded astrology data ({len(astrology_data)} chars)")
    print()
    
    # 3. Initialize Gemini service
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        sys.exit(1)
        
    gemini = GeminiService(api_key=api_key, model="gemini-3.1-flash-lite")
    print(f"✅ Gemini service initialized (model: gemini-3.1-flash-lite)")
    print()
    
    parts = {}
    
    # 4. Prepare dynamic prompts
    formatted_prompts = {}
    for part_num, instruction in PART_USER_PROMPTS.items():
        formatted_instruction = instruction.format(
            partner1=p1,
            partner2=p2,
            partner1_details=p1_details,
            partner2_details=p2_details
        )
        user_prompt = USER_PROMPT_TEMPLATE_V4.format(
            part_number=part_num,
            part_instruction=formatted_instruction,
            partner1=p1,
            partner1_details=p1_details,
            partner2=p2,
            partner2_details=p2_details,
            astrology_data=astrology_data
        )
        formatted_prompts[part_num] = user_prompt
        
    # 5. Dispatch 5 parallel requests
    print("📡 Dispatching 5 parallel requests to Gemini API...")
    print()
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(generate_part, gemini, i, formatted_prompts[i])
            for i in [1, 2, 3, 4, 5]
        ]
        
        for future in as_completed(futures):
            part_num, text, error = future.result()
            if error is None:
                parts[part_num] = text
                
    # 6. Verify and Assemble
    if len(parts) < 5:
        print(f"❌ Error: Only {len(parts)}/5 parts generated successfully. Aborting save.")
        sys.exit(1)
        
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
    print(f"  Parts generated: {len(parts)}/5")
    print()
    
    # Save output
    output_dir = config.get("outputDir", "./output")
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"{p1.lower()}_{p2.lower()}_report.md"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_report)
        
    print(f"✅ Report saved to: {output_path}")
    print(f"   File size: {os.path.getsize(output_path):,} bytes")
    print()
    
    # Validate sections
    validate_report(full_report)


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
