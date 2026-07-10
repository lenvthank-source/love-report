import os
import sys
import asyncio
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Reconfigure stdout for UTF-8 to support terminal emojis
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# Add src folder to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

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

async def main():
    load_dotenv()
    
    name = "Dev"
    gender = "Male"
    dob = "1999-10-15"
    tob = "18:52"
    place = "Delhi, India"
    provider = "openrouter"
    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-5.4-mini")
    
    print(f"🔮 Generating Premium Individual Love Report for {name} ({gender})...")
    print(f"   Born: {dob} at {tob} in {place}")
    
    # 1. Geocode birth place
    opencage_key = os.getenv("OPENCAGE_API_KEY", "3723e0d7ceb64eb3bd3623477d4c3142")
    geocoder = GeocodingService(opencage_key)
    geo = geocoder.geocode(place)
    if not geo:
        raise ValueError(f"Could not geocode location: '{place}'")
    
    lat = geo["latitude"]
    lon = geo["longitude"]
    tz = geo["timezone"]
    dt_str = f"{dob}T{tob}:00"
    time_str, date_str, offset_str = format_datetime_for_vedastro(dt_str, tz)
    
    # 2. Fetch astrological data
    print("🪐 Querying astrological calculations from VedAstro...")
    vedastro = VedAstroService()
    d1_data = vedastro.get_all_planet_data(place, lat, lon, time_str, date_str, offset_str)
    house_signs = vedastro.get_all_house_rasi_signs(lat, lon, time_str, date_str, offset_str)
    d9_signs = vedastro.get_all_planet_navamsha_signs(lat, lon, time_str, date_str, offset_str)
    d30_signs = vedastro.get_all_planet_trimshamsha_signs(lat, lon, time_str, date_str, offset_str)
    
    lagna_sign = vedastro.get_lagna_sign_name(lat, lon, time_str, date_str, offset_str)
    lagna_tags = vedastro.get_sign_tags(lagna_sign)
    lagna_lord = vedastro.get_lord_of_house("House1", lat, lon, time_str, date_str, offset_str)
    house5_lord = vedastro.get_lord_of_house("House5", lat, lon, time_str, date_str, offset_str)
    house7_lord = vedastro.get_lord_of_house("House7", lat, lon, time_str, date_str, offset_str)
    
    house5_sign = house_signs.get("House5", "Leo")
    house7_sign = house_signs.get("House7", "Aquarius")
    house5_planets = vedastro.get_planets_in_house("House5", lat, lon, time_str, date_str, offset_str)
    house7_planets = vedastro.get_planets_in_house("House7", lat, lon, time_str, date_str, offset_str)
    
    venus_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Leo") for entry in d1_data for p, d in entry.items() if p == "Venus"), "Leo")
    venus_conjunctions = vedastro.get_planets_in_conjunction("Venus", lat, lon, time_str, date_str, offset_str)
    is_venus_combust = "Yes" if vedastro.is_planet_combust_specific("Venus", lat, lon, time_str, date_str, offset_str) else "No"
    
    venus_relationships = []
    for conj in venus_conjunctions:
        rel = vedastro.get_planet_relationship("Venus", conj, lat, lon, time_str, date_str, offset_str)
        venus_relationships.append(f"{conj} ({rel})")
        
    navamsa_lagna_sign = house_signs.get("House1", "Virgo")
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
        
    kuja_dosha_score = vedastro.get_kuja_dosha_score(lat, lon, time_str, date_str, offset_str)
    is_7th_lord_afflicted = "Yes" if vedastro.is_planet_afflicted_specific(house7_lord, lat, lon, time_str, date_str, offset_str) else "No"
    
    afflicted_planets = []
    for entry in d1_data:
        for p, d in entry.items():
            if d.get("IsPlanetAfflicted") == "True":
                afflicted_planets.append(p)
                
    malefic_planets = vedastro.get_malefic_planet_list(lat, lon, time_str, date_str, offset_str)
    benefic_planets = vedastro.get_benefic_planet_list(lat, lon, time_str, date_str, offset_str)
    
    dasa_now_raw = vedastro.get_dasa_for_now(lat, lon, time_str, date_str, offset_str, levels=3)
    dasa_now = f"{dasa_now_raw.get('Major', '')} - {dasa_now_raw.get('Sub', '')} - {dasa_now_raw.get('SubSub', '')}"
    
    dasa_info_for_asc = vedastro.get_dasa_info_for_ascendant(lagna_sign)
    
    now = datetime.now()
    ten_years_later = now + timedelta(days=10 * 365)
    start_t, start_d, _ = format_datetime_for_vedastro(now.isoformat(), tz)
    end_t, end_d, _ = format_datetime_for_vedastro(ten_years_later.isoformat(), tz)
    
    dasa_timeline_raw = []
    try:
        dasa_timeline_raw = vedastro.get_dasa_at_range(
            lat, lon, time_str, date_str, offset_str,
            start_t, start_d, end_t, end_d, levels=2, precision_hours=48
        )
    except Exception:
        pass
        
    d1_placements = map_placements_to_signs(d1_data)
    d9_placements = map_divisional_signs(d9_signs)
    d30_placements = map_divisional_signs(d30_signs)
    
    elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
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
        
    dasha_timeline = []
    if not dasa_timeline_raw:
        dasha_timeline.append([dasa_now.split("-")[0], f"{dob} to Future", "Major cycle guiding long term spiritual growth."])
    else:
        import re
        current_year = now.year
        for major_name, major_val in dasa_timeline_raw.items():
            sub_dasas = major_val.get("SubDasas") or {}
            for sub_name, sub_val in sub_dasas.items():
                start_readable = sub_val.get("Start", "")
                end_readable = sub_val.get("End", "")
                
                # Extract year
                match = re.search(r'\b(19|20)\d{2}\b', start_readable)
                dasha_year = int(match.group(0)) if match else 0
                
                if dasha_year >= current_year:
                    start_date = start_readable[6:16] if len(start_readable) >= 16 else start_readable
                    end_date = end_readable[6:16] if len(end_readable) >= 16 else end_readable
                    dasha_timeline.append([
                        f"{major_name} - {sub_name}",
                        f"{start_date} - {end_date}",
                        "Favorable window for emotional breakthroughs and setting roots."
                    ])
                    if len(dasha_timeline) >= 3:
                        break
            if len(dasha_timeline) >= 3:
                break
        
        if not dasha_timeline:
            dasha_timeline.append([dasa_now.split("-")[0], f"{dob} to Future", "Major cycle guiding long term spiritual growth."])
            
    lagna_tags_str = lagna_tags if lagna_tags else "expressive, initiating"
    moon_nakshatra = next((d.get("PlanetConstellation", "Chitta") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Chitta")
    moon_sign = next((d.get("PlanetRasiD1Sign", {}).get("Name", "Libra") for entry in d1_data for p, d in entry.items() if p == "Moon"), "Libra")
    moon_tags = vedastro.get_sign_tags(moon_sign)
    house7_tags = vedastro.get_house_tags("House7")
    planet_navamsa_signs_str = ", ".join([f"{p}: {s}" for p, s in d9_signs.items()])
    planet_trimsamsha_signs_str = ", ".join([f"{p}: {s}" for p, s in d30_signs.items()])
    dasa_timeline_str = ", ".join([f"{row[0]} ({row[1]})" for row in dasha_timeline])
    
    remedies_data_str = ""
    for p in afflicted_planets[:2]:
        p_tags = vedastro.get_planet_tags(p)
        remedies_data_str += f"{p} (afflicted, tags: {p_tags}); "
        
    favorable_tags_str = ", ".join([vedastro.get_planet_tags(p) for p in benefic_planets[:2]])
    afflicted_tags_str = ", ".join([vedastro.get_planet_tags(p) for p in malefic_planets[:2]])
    dasa_info_str = str(dasa_info_for_asc.get("Description", "Growth and commitment dasha rules."))
    
    router = LLMRouter()
    sections_text = {}
    pages_to_generate = [p for p in PAGE_PROMPTS.keys()]
    
    print(f"📡 Generating content for {len(pages_to_generate)} pages sequentially...")
    
    async def fetch_page(page, prompt):
        print(f"🚀 Generating page {page}...")
        raw_text = await asyncio.to_thread(
            router.generate,
            provider=provider,
            system_instruction=GLOBAL_SYSTEM_INSTRUCTION,
            user_prompt=prompt,
            model=model
        )
        print(f"✅ Page {page} completed.")
        return page, strip_thinking_tags(raw_text)

    tasks = []
    for idx, page in enumerate(pages_to_generate):
        instruction = PAGE_PROMPTS[page].format(
            lagna_sign=lagna_sign, lagna_lord=lagna_lord, lagna_tags=lagna_tags_str,
            moon_sign=moon_sign, moon_nakshatra=moon_nakshatra, moon_tags=moon_tags,
            house5_sign=house5_sign, house5_lord=house5_lord,
            house5_planets=", ".join(house5_planets) if house5_planets else "None",
            venus_sign=venus_sign,
            venus_conjunctions=", ".join(venus_conjunctions) if venus_conjunctions else "None",
            is_venus_combust=is_venus_combust,
            venus_relationships=", ".join(venus_relationships) if venus_relationships else "None",
            house7_sign=house7_sign, house7_lord=house7_lord,
            house7_planets=", ".join(house7_planets) if house7_planets else "None",
            house7_tags=house7_tags,
            house7_lord_sign=next((d.get("PlanetRasiD1Sign", {}).get("Name", "Virgo") for entry in d1_data for p, d in entry.items() if p == house7_lord), "Virgo"),
            house7_lord_house=str(next((d.get("PlanetHouse", 1) for entry in d1_data for p, d in entry.items() if p == house7_lord), 1)),
            navamsa_lagna_sign=navamsa_lagna_sign, planet_navamsa_signs=planet_navamsa_signs_str,
            navamsa_house7_sign=navamsa_house7_sign, navamsa_house7_lord="Saturn", navamsa_house7_planets="None",
            trimsamsha_house7_sign=trimsamsha_house7_sign, planet_trimsamsha_signs=planet_trimsamsha_signs_str,
            afflicted_planets=", ".join(afflicted_planets) if afflicted_planets else "None",
            is_7th_lord_afflicted=is_7th_lord_afflicted, kuja_dosha_score=f"{kuja_dosha_score}%",
            mars_afflictions="retrograde" if "Mars" in afflicted_planets else "None",
            malefic_planets=", ".join(malefic_planets), benefic_planets=", ".join(benefic_planets),
            element_fire=elements["Fire"], element_earth=elements["Earth"],
            element_air=elements["Air"], element_water=elements["Water"],
            dasa_now=dasa_now, dasa_timeline=dasa_timeline_str,
            pratyantar_dasha=dasa_now_raw.get("SubSub", "Mercury"),
            favorable_tags=favorable_tags_str, afflicted_tags=afflicted_tags_str,
            remedies_data=remedies_data_str, dasa_info_for_ascendant=dasa_info_str
        )
        
        user_prompt = USER_PROMPT_TEMPLATE.format(
            page_number=page, page_instruction=instruction,
            name=name, gender=gender,
            birth_details=f"{dob} at {tob} in {place}"
        )
        
        task = asyncio.create_task(fetch_page(page, user_prompt))
        tasks.append(task)
        await asyncio.sleep(0.5) # small spacing
        
    results = await asyncio.gather(*tasks)
    for page, text in results:
        sections_text[page] = text
        
    # Write Markdown file
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    md_path = os.path.join(output_dir, "dev_individual_love_report.md")
    print(f"📝 Writing markdown to {md_path}...")
    
    # Format consolidated markdown
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {name.upper()}'S COSMIC BLUEPRINT\n\n")
        f.write(f"Birth Details: {dob} at {tob} in {place}\n\n")
        f.write("---\n\n")
        for page in sorted(sections_text.keys()):
            f.write(f"## {page}. Section Title\n\n")
            f.write(f"{sections_text[page]}\n\n")
            f.write("---\n\n")
            
    print(f"📄 Compiling PDF overlay via PDFService...")
    pdf_path = os.path.join(output_dir, "dev_individual_love_report.pdf")
    pdf_service = PDFService()
    pdf_service.build_pdf_report(
        output_path=pdf_path,
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
        trimsamsha_lagna_sign=trimsamsha_lagna_sign,
        client_dob=dob,
        client_tob=tob,
        client_pob=place,
    )
    print(f"🎉 SUCCESS! Report compiled at {pdf_path}")

if __name__ == "__main__":
    asyncio.run(main())
