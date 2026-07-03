#!/usr/bin/env python3
"""
Dynamic 25-Page Individual Love & Marriage PDF Report Generator
===============================================================
Dispatches parallel requests to Gemini 3.1 Flash Lite using bulk
VedAstro data and compiles the final PDF report with custom cover and borders.

Usage:
    python scratch/generate_pdf_report.py
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List

# Force UTF-8 stdout on Windows to handle emoji output
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.services.geocoding import GeocodingService
from src.services.vedastro_service import VedAstroService, format_datetime_for_vedastro
from src.services.llm_router import LLMRouter
from src.services.pdf_service import PDFService
from src.utils.divisional_charts import map_placements_to_signs, map_divisional_signs
from src.utils.markdown_parser import strip_thinking_tags
from src.prompts.individual_report_prompts import (
    GLOBAL_SYSTEM_INSTRUCTION,
    PAGE_PROMPTS,
    USER_PROMPT_TEMPLATE,
)


def generate_page_text(router: LLMRouter, provider: str, page_num: int, user_prompt: str) -> tuple:
    """Worker function to generate a specific page directly with retries."""
    max_retries = 3
    retry_delays = [10, 20, 40]
    
    for attempt in range(max_retries + 1):
        print(f"🚀 [Page {page_num}/25] Generating content via {provider.upper()} (Attempt {attempt + 1}/{max_retries + 1})...")
        start_time = time.time()
        try:
            raw_text = router.generate(
                provider=provider,
                system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
                user_prompt=user_prompt
            )
            text = strip_thinking_tags(raw_text)
            elapsed = time.time() - start_time
            word_count = len(text.split())
            print(f"✅ [Page {page_num}/25] Completed in {elapsed:.1f}s — {word_count} words")
            return page_num, text, None
        except Exception as e:
            error_str = str(e)
            if ("503" in error_str or "UNAVAILABLE" in error_str or "429" in error_str) and attempt < max_retries:
                delay = retry_delays[attempt]
                print(f"  ⚠️ [Page {page_num}/25] Temporary API error: {e}. Retrying in {delay}s...")
                time.sleep(delay)
            else:
                print(f"❌ [Page {page_num}/25] Failed after {attempt + 1} attempts: {e}")
                return page_num, "", e


def main():
    print("=" * 70)
    # Print human readable model name
    print("🔮 PREMIUM INDIVIDUAL LOVE & MARRIAGE PDF REPORT GENERATOR (Gemini 3.5 Flash)")
    print("=" * 70)

    # 1. Load config
    config_file = "sample/input.json"
    if not os.path.exists(config_file):
        print(f"❌ Configuration not found: {config_file}")
        sys.exit(1)
        
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    person = config["primary"]
    name = person["name"]
    dob = person["dateOfBirth"]
    tob = person["timeOfBirth"]
    place = person["placeOfBirth"]
    gender = person["gender"]
    
    print(f"👤 Target: {name} ({gender})")
    print(f"   Born: {dob} at {tob} in {place}")
    print()

    # 2. Geocoding
    opencage_key = os.getenv("OPENCAGE_API_KEY", "3723e0d7ceb64eb3bd3623477d4c3142")
    geocoder = GeocodingService(opencage_key)
    print(f"🌐 Geocoding birth place: {place}...")
    geo = geocoder.geocode(place)
    if not geo:
        print(f"❌ Could not geocode: {place}")
        sys.exit(1)
        
    lat = geo["latitude"]
    lon = geo["longitude"]
    tz = geo["timezone"]
    print(f"   Coordinates: {lat}, {lon} (Timezone: {tz})")
    print()

    # 3. Format Date/Time
    dt_str = f"{dob}T{tob}:00"
    time_str, date_str, offset_str = format_datetime_for_vedastro(dt_str, tz)
    print(f"📅 VedAstro Date Format: {time_str} {date_str} {offset_str}")
    print()

    # 4. Fetch Astrological Data
    vedastro = VedAstroService()
    print("🪐 Fetching D1 Placements (AllPlanetData)...")
    d1_data = vedastro.get_all_planet_data(place, lat, lon, time_str, date_str, offset_str)
    
    print("🪐 Fetching All House Signs (AllHouseRasiSigns)...")
    house_signs = vedastro.get_all_house_rasi_signs(lat, lon, time_str, date_str, offset_str)
    
    print("🪐 Fetching D9 Navamsa Signs (AllPlanetNavamshaSign)...")
    d9_signs = vedastro.get_all_planet_navamsha_signs(lat, lon, time_str, date_str, offset_str)
    
    print("🪐 Fetching D30 Trimsamsha Signs (AllPlanetTrimshamshaSign)...")
    d30_signs = vedastro.get_all_planet_trimshamsha_signs(lat, lon, time_str, date_str, offset_str)

    print("🪐 Fetching Ascendant details...")
    lagna_sign = vedastro.get_lagna_sign_name(lat, lon, time_str, date_str, offset_str)
    lagna_tags = vedastro.get_sign_tags(lagna_sign)
    
    print("🪐 Fetching House Lords...")
    lagna_lord = vedastro.get_lord_of_house("House1", lat, lon, time_str, date_str, offset_str)
    house5_lord = vedastro.get_lord_of_house("House5", lat, lon, time_str, date_str, offset_str)
    house7_lord = vedastro.get_lord_of_house("House7", lat, lon, time_str, date_str, offset_str)
    
    print("🪐 Fetching House Placements...")
    house5_sign = house_signs.get("House5", "Leo")
    house7_sign = house_signs.get("House7", "Aquarius")
    house5_planets = vedastro.get_planets_in_house("House5", lat, lon, time_str, date_str, offset_str)
    house7_planets = vedastro.get_planets_in_house("House7", lat, lon, time_str, date_str, offset_str)
    
    print("🪐 Fetching Venus specifics...")
    venus_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Leo") for entry in d1_data for p, d in entry.items() if p == "Venus"), "Leo")
    venus_conjunctions = vedastro.get_planets_in_conjunction("Venus", lat, lon, time_str, date_str, offset_str)
    is_venus_combust = "Yes" if vedastro.is_planet_combust_specific("Venus", lat, lon, time_str, date_str, offset_str) else "No"
    
    venus_relationships = []
    for conj in venus_conjunctions:
        rel = vedastro.get_planet_relationship("Venus", conj, lat, lon, time_str, date_str, offset_str)
        venus_relationships.append(f"{conj} ({rel})")
        
    print("🪐 Fetching Divisional specifics...")
    navamsa_lagna_sign = house_signs.get("House1", "Virgo") # Default
    try:
        navamsa_lagna_sign = vedastro.get_house_navamsha_d9_sign("House1", lat, lon, time_str, date_str, offset_str)
    except Exception:
        pass
        
    navamsa_house7_sign = "Aries"
    try:
        navamsa_house7_sign = vedastro.get_house_navamsha_d9_sign("House7", lat, lon, time_str, date_str, offset_str)
    except Exception:
        pass
        
    trimsamsha_house7_sign = "Aquarius"
    try:
        trimsamsha_house7_sign = vedastro.get_house_trimshamsha_d30_sign("House7", lat, lon, time_str, date_str, offset_str)
    except Exception:
        pass
        
    trimsamsha_lagna_sign = "Aries"
    try:
        trimsamsha_lagna_sign = vedastro.get_house_trimshamsha_d30_sign("House1", lat, lon, time_str, date_str, offset_str)
    except Exception:
        pass
        
    print("🪐 Fetching Kuja Dosha & Afflictions...")
    kuja_dosha_score = vedastro.get_kuja_dosha_score(lat, lon, time_str, date_str, offset_str)
    is_7th_lord_afflicted = "Yes" if vedastro.is_planet_afflicted_specific(house7_lord, lat, lon, time_str, date_str, offset_str) else "No"
    
    afflicted_planets = []
    for entry in d1_data:
        for p, d in entry.items():
            if d.get("IsPlanetAfflicted") == "True":
                afflicted_planets.append(p)
                
    malefic_planets = vedastro.get_malefic_planet_list(lat, lon, time_str, date_str, offset_str)
    benefic_planets = vedastro.get_benefic_planet_list(lat, lon, time_str, date_str, offset_str)
    
    print("🪐 Fetching Dasha Forecasts...")
    dasa_now_raw = vedastro.get_dasa_for_now(lat, lon, time_str, date_str, offset_str, levels=3)
    dasa_now = f"{dasa_now_raw.get('Major', '')} - {dasa_now_raw.get('Sub', '')} - {dasa_now_raw.get('SubSub', '')}"
    
    dasa_info_for_asc = vedastro.get_dasa_info_for_ascendant(lagna_sign)
    
    # Calculate Dasha Timeline for next 3 years
    now = datetime.now()
    three_years_later = now + timedelta(days=3 * 365)
    start_t, start_d, _ = format_datetime_for_vedastro(now.isoformat(), tz)
    end_t, end_d, _ = format_datetime_for_vedastro(three_years_later.isoformat(), tz)
    
    print("🪐 Fetching Vimshottari Timeline...")
    dasa_timeline_raw = []
    try:
        dasa_timeline_raw = vedastro.get_dasa_at_range(
            lat, lon, time_str, date_str, offset_str,
            start_t, start_d, end_t, end_d, levels=2, precision_hours=48
        )
    except Exception:
        pass
        
    print()
    print("✅ All astrological data fetched successfully!")
    print()

    # 5. Process Charts Map for PDF
    d1_placements = map_placements_to_signs(d1_data)
    d9_placements = map_divisional_signs(d9_signs)
    d30_placements = map_divisional_signs(d30_signs)

    # 6. Build the Risk Matrix dynamically
    risk_matrix = []
    for aff_planet in afflicted_planets[:3]:
        tags = vedastro.get_planet_tags(aff_planet)
        risk_matrix.append([
            f"Afflicted {aff_planet}",
            f"Causes shadows of {tags.split(',')[0] if tags else 'emotional blocks'}.",
            f"Conscious focus on releasing control and seeking stability."
        ])
    if kuja_dosha_score > 0:
        risk_matrix.append([
            f"Kuja Dosha ({int(kuja_dosha_score)}%)",
            "Triggers defensive blocks, stubbornness, or hot-headed responses.",
            "Practice cooling breathwork and wait 24 hours before responding to conflicts."
        ])
    if not risk_matrix:
        risk_matrix.append(["General Balance", "Minor friction points in communication.", "Commit to open dialogue."])

    # 7. Build Dasha Timeline Rows
    dasha_timeline = []
    # If API timeline failed, add fallback row
    if not dasa_timeline_raw:
        dasha_timeline.append([dasa_now.split("-")[0], f"{dob} to Future", "Major cycle guiding long term spiritual growth."])
    else:
        for item in dasa_timeline_raw[:4]:
            dasha_timeline.append([
                item.get("Name", "Unknown Dasa"),
                f"{item.get('StartTime', {}).get('Readable', '')[:11]} - {item.get('EndTime', {}).get('Readable', '')[:11]}",
                "Favorable window for emotional breakthroughs and setting roots."
            ])

    # 8. Initialize LLM Router
    provider = os.getenv("DEFAULT_PROVIDER", "gemini").lower().strip()
    router = LLMRouter()
    print(f"✅ LLM Router initialized (default provider: {provider})")
    print()

    # 9. Format Prompts for Gemini
    formatted_prompts = {}
    
    # Elemental calculation
    elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    # Simple count from d1_placements
    fire_signs = ["Aries", "Leo", "Sagittarius"]
    earth_signs = ["Taurus", "Virgo", "Capricorn"]
    air_signs = ["Gemini", "Libra", "Aquarius"]
    water_signs = ["Cancer", "Scorpio", "Pisces"]
    for sign, planets in d1_placements.items():
        if sign in fire_signs:
            elements["Fire"] += len(planets)
        elif sign in earth_signs:
            elements["Earth"] += len(planets)
        elif sign in air_signs:
            elements["Air"] += len(planets)
        elif sign in water_signs:
            elements["Water"] += len(planets)

    # Gather keywords/tags for prompts
    lagna_tags_str = lagna_tags if lagna_tags else "expressive, initiating"
    moon_nakshatra = next((d.get("PlanetConstellation", "Chitta") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Chitta")
    moon_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Libra") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Libra")
    moon_tags = vedastro.get_sign_tags(moon_sign)
    
    house7_tags = vedastro.get_house_tags("House7")
    
    planet_navamsa_signs_str = ", ".join([f"{p}: {s}" for p, s in d9_signs.items()])
    planet_trimsamsha_signs_str = ", ".join([f"{p}: {s}" for p, s in d30_signs.items()])
    
    dasa_timeline_str = ", ".join([f"{row[0]} ({row[1]})" for row in dasha_timeline])
    
    # Remedies data builder
    remedies_data_str = ""
    for p in afflicted_planets[:2]:
        p_tags = vedastro.get_planet_tags(p)
        remedies_data_str += f"{p} (afflicted, tags: {p_tags}); "
        
    favorable_tags_str = ", ".join([vedastro.get_planet_tags(p) for p in benefic_planets[:2]])
    afflicted_tags_str = ", ".join([vedastro.get_planet_tags(p) for p in malefic_planets[:2]])
    
    dasa_info_str = str(dasa_info_for_asc.get("Description", "Growth and commitment dasha rules."))

    for page_num, instruction in PAGE_PROMPTS.items():
        # Format the specific instructions with astro data
        formatted_instruction = instruction.format(
            lagna_sign=lagna_sign,
            lagna_lord=lagna_lord,
            lagna_tags=lagna_tags_str,
            moon_sign=moon_sign,
            moon_nakshatra=moon_nakshatra,
            moon_tags=moon_tags,
            house5_sign=house5_sign,
            house5_lord=house5_lord,
            house5_planets=", ".join(house5_planets) if house5_planets else "None",
            venus_sign=venus_sign,
            venus_conjunctions=", ".join(venus_conjunctions) if venus_conjunctions else "None",
            is_venus_combust=is_venus_combust,
            venus_relationships=", ".join(venus_relationships) if venus_relationships else "None",
            house7_sign=house7_sign,
            house7_lord=house7_lord,
            house7_planets=", ".join(house7_planets) if house7_planets else "None",
            house7_tags=house7_tags,
            house7_lord_sign=next((d.get("PlanetRasiD1Sign", {}).get("Name", "Virgo") for entry in d1_data for p, d in entry.items() if p == house7_lord), "Virgo"),
            house7_lord_house=str(next((d.get("PlanetHouse", 1) for entry in d1_data for p, d in entry.items() if p == house7_lord), 1)),
            navamsa_lagna_sign=navamsa_lagna_sign,
            planet_navamsa_signs=planet_navamsa_signs_str,
            navamsa_house7_sign=navamsa_house7_sign,
            navamsa_house7_lord=vedastro.get_lord_of_house("House7", lat, lon, time_str, date_str, offset_str), # Approximate
            navamsa_house7_planets="None",
            trimsamsha_house7_sign=trimsamsha_house7_sign,
            planet_trimsamsha_signs=planet_trimsamsha_signs_str,
            afflicted_planets=", ".join(afflicted_planets) if afflicted_planets else "None",
            is_7th_lord_afflicted=is_7th_lord_afflicted,
            kuja_dosha_score=f"{kuja_dosha_score}%",
            mars_afflictions="retrograde" if "Mars" in afflicted_planets else "None",
            malefic_planets=", ".join(malefic_planets),
            benefic_planets=", ".join(benefic_planets),
            element_fire=elements["Fire"],
            element_earth=elements["Earth"],
            element_air=elements["Air"],
            element_water=elements["Water"],
            dasa_now=dasa_now,
            dasa_timeline=dasa_timeline_str,
            pratyantar_dasha=dasa_now_raw.get("SubSub", "Mercury"),
            favorable_tags=favorable_tags_str,
            afflicted_tags=afflicted_tags_str,
            remedies_data=remedies_data_str,
            dasa_info_for_ascendant=dasa_info_str
        )
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            page_number=page_num,
            page_instruction=formatted_instruction,
            name=name,
            gender=gender,
            birth_details=f"{dob} at {tob} in {place}",
        )
        formatted_prompts[page_num] = user_prompt

    # 10. Generate Content via Router (sequential loop with pacing to respect API rate limits)
    sections_text = {}
    pages_to_generate = [p for p in PAGE_PROMPTS.keys()]
    
    print(f"📡 Generating content for {len(pages_to_generate)} pages sequentially with rate-limiting pacing...")
    
    for idx, page in enumerate(pages_to_generate):
        page_num, text, error = generate_page_text(router, provider, page, formatted_prompts[page])
        if error is None:
            sections_text[page_num] = text
        else:
            print(f"❌ Error: Page {page} failed to generate. Aborting.")
            sys.exit(1)
            
        # Pacing sleep (12 seconds for Groq, 5 seconds for other models)
        if idx < len(pages_to_generate) - 1:
            delay_sec = 12.0 if provider == "groq" else 5.0
            print(f"   [Pacing] Sleeping for {delay_sec} seconds to respect API limits...")
            time.sleep(delay_sec)

    # 11. Compile PDF & Markdown Reports
    print()
    print("📝 Compiling consolidated Markdown report...")
    output_dir = config.get("outputDir", "./output")
    os.makedirs(output_dir, exist_ok=True)
    
    # Save consolidated Markdown file
    PAGE_TITLES = {
        2: "Spiritual Disclaimer",
        3: "Message from the Author",
        4: "Master Index (Table of Contents)",
        5: "Technical Astral Map (D1 Birth Chart)",
        6: "1st House Energy – Core Essence",
        7: "Moon Sign – Emotional Sanctuary",
        8: "5th House Energy – Romance & Friendship",
        9: "Venus Conjunctions",
        10: "Technical Divisional Charts (D9 & D30)",
        11: "7th House Energy – Marriage Gateway",
        12: "Spouse Core Nature",
        13: "D1 Natal Promise vs D9 Navamsa Fruit",
        14: "D9 Navamsa Revelation – Marital Dynamics",
        15: "D30 Trimsamsha Analysis – Loyalty & Challenges",
        16: "Recurring Patterns & Karmic Loops",
        17: "Planetary Blockages & Vulnerabilities",
        18: "Cosmic Red Flags",
        19: "Comprehensive Risk Matrix",
        20: "Vimshottari Dasha Overview",
        21: "3-Year Advanced Dasha Forecast",
        22: "Precision Sub-Minor Forecast",
        23: "Mantras & Healing Behavioral Shifts",
        24: "Practical Remedies & Ritual Clearances",
        25: "The Final Heart Synthesis & Sign-Off"
    }
    
    md_lines = [
        f"# {name.upper()}'S COSMIC INDIVIDUAL LOVE & MARRIAGE REPORT",
        f"Birth Details: {dob} at {tob} in {place}",
        "",
        "---",
        ""
    ]
    for p_num in range(2, 26):
        p_title = PAGE_TITLES.get(p_num, f"Section {p_num}")
        md_lines.append(f"## {p_num}. {p_title}")
        md_lines.append("")
        if p_num in [5, 10]:
            md_lines.append(f"*[Technical chart displayed on page {p_num} of PDF report]*")
        else:
            md_lines.append(sections_text.get(p_num, "Content in progress..."))
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        
    md_filename = f"{name.lower()}_individual_love_report.md"
    md_path = os.path.join(output_dir, md_filename)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"✅ Consolidated Markdown saved to {md_path}")
    
    print("📄 Compiling PDF Document using Playwright Headless...")
    output_filename = f"{name.lower()}_individual_love_report.pdf"
    output_path = os.path.join(output_dir, output_filename)
    
    pdf_service = PDFService()
    pdf_service.build_pdf_report(
        output_path=output_path,
        sections=sections_text,
        d1_placements=d1_placements,
        d9_placements=d9_placements,
        d30_placements=d30_placements,
        risk_matrix=risk_matrix,
        dasha_timeline=dasha_timeline,
        client_name=name,
        birth_details=f"{dob} at {tob} in {place}",
        lagna_sign=lagna_sign,
        navamsa_lagna_sign=navamsa_lagna_sign,
        trimsamsha_lagna_sign=trimsamsha_lagna_sign
    )
    
    print()
    print(f"✅ PDF Report generated and saved successfully!")
    print(f"   Output PDF Path: {output_path}")
    print(f"   Output MD Path:  {md_path}")
    print(f"   File size: {os.path.getsize(output_path):,} bytes")
    print()


if __name__ == "__main__":
    main()
