import os
import sys
import re
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Add project root to python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.geocoding import GeocodingService
from src.services.vedastro_service import VedAstroService, format_datetime_for_vedastro
from src.services.pdf_service import PDFService
from src.utils.divisional_charts import map_placements_to_signs, map_divisional_signs

def parse_markdown_report(md_path: str):
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Extract metadata
    name_match = re.search(r'#\s+(.+?)\'S\s+COSMIC', content, re.IGNORECASE)
    details_match = re.search(r'Birth Details:\s*(.+?)\s+at\s+(.+?)\s+in\s+(.+?)(?:\n|$)', content, re.IGNORECASE)
    
    if not name_match or not details_match:
        raise ValueError("Could not parse Name or Birth Details from the markdown file header.")
        
    name = name_match.group(1).strip().capitalize()
    dob = details_match.group(1).strip()
    tob = details_match.group(2).strip()
    place = details_match.group(3).strip()
    
    # Extract sections
    sections = {}
    
    # Split by horizontal rule
    parts = re.split(r'\n---+\n', content)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Match header like: "## 6. 1st House Energy – Core Essence"
        header_match = re.match(r'^##\s*(\d+)\.\s*(.+?)(?:\n(.*)|$)', part, re.DOTALL)
        if header_match:
            page_num = int(header_match.group(1))
            body_text = header_match.group(3).strip() if header_match.group(3) else ""
            sections[page_num] = body_text
            
    return name, dob, tob, place, sections

async def main():
    if len(sys.argv) < 2:
        print("Usage: python scratch/compile_from_markdown.py <path_to_markdown_file>")
        sys.exit(1)
        
    md_path = sys.argv[1]
    if not os.path.exists(md_path):
        print(f"Error: File not found: {md_path}")
        sys.exit(1)
        
    print(f"[Info] Parsing Markdown report: {md_path}...")
    name, dob, tob, place, sections = parse_markdown_report(md_path)
    print(f"   Client Name:   {name}")
    print(f"   Birth Details: {dob} at {tob} in {place}")
    print(f"   Parsed Pages:  {list(sections.keys())}")
    
    print("\n[Geocoding] Geocoding birth place...")
    geocoder = GeocodingService(os.getenv("OPENCAGE_API_KEY"))
    geo = geocoder.geocode(place)
    if not geo:
        raise ValueError(f"Could not geocode location: '{place}'")
    lat = geo["latitude"]
    lng = geo["longitude"]
    tz = geo["timezone"]
    print(f"   Coordinates: Lat={lat}, Lng={lng}, Timezone={tz}")
    
    print("\n[VedAstro] Fetching planetary coordinates from VedAstro...")
    vedastro = VedAstroService()
    dt_str = f"{dob}T{tob}:00"
    time_str, date_str, offset_str = format_datetime_for_vedastro(dt_str, tz)
    
    d1_data = vedastro.get_all_planet_data(place, lat, lng, time_str, date_str, offset_str)
    d9_signs = vedastro.get_all_planet_navamsha_signs(lat, lng, time_str, date_str, offset_str)
    d30_signs = vedastro.get_all_planet_trimshamsha_signs(lat, lng, time_str, date_str, offset_str)
    
    lagna_sign = vedastro.get_lagna_sign_name(lat, lng, time_str, date_str, offset_str)
    print(f"   D1 Ascendant (Lagna) Sign: {lagna_sign}")
    
    navamsa_lagna_sign = "Aries"
    try:
        navamsa_lagna_sign = vedastro.get_house_navamsha_d9_sign("House1", lat, lng, time_str, date_str, offset_str)
    except Exception:
        pass
    print(f"   D9 Navamsa Lagna Sign: {navamsa_lagna_sign}")
    
    trimsamsha_lagna_sign = "Aries"
    try:
        trimsamsha_lagna_sign = vedastro.get_house_trimshamsha_d30_sign("House1", lat, lng, time_str, date_str, offset_str)
    except Exception:
        pass
    print(f"   D30 Trimsamsha Lagna Sign: {trimsamsha_lagna_sign}")
    
    d1_placements = map_placements_to_signs(d1_data)
    d9_placements = map_divisional_signs(d9_signs)
    d30_placements = map_divisional_signs(d30_signs)
    
    # Calculate elemental balance
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
            
    # Calculate Kuja Dosha Score
    kuja_dosha_score = vedastro.get_kuja_dosha_score(lat, lng, time_str, date_str, offset_str)
    manglik_score = kuja_dosha_score
    
    risk_matrix = [
        ["Fiery Impulsivity (Fire Score)", f"{elements['Fire']}/9 planets in Fire signs", "Cultivate slow, conscious pauses before responding."],
        ["Vulnerability/Communication (Air/Water)", f"Air: {elements['Air']}, Water: {elements['Water']}", "Incorporate daily emotional journaling."],
        ["Kuja Dosha Tension (Mars)", f"{manglik_score}% affliction score", "Chant protective mantras and keep cool during conflicts."]
    ]
    
    # Dasha Timeline
    dasha_timeline = [
        ["Venus Antardasha (7th House)", "2024 - 2025", "Romantic expansion, relationship commitments, and emotional honesty."],
        ["Mars Antardasha (5th House)", "2025 - 2026", "Spontaneous heart energy, romantic pursuits, and creative spark."],
        ["Jupiter Antardasha (2nd House)", "2026 - 2027", "Deepened security, value alignment, and mutual relationship support."]
    ]
    
    print("\n[PDF] Compiling PDF using Playwright compiler...")
    pdf_path = md_path.replace(".md", ".pdf")
    
    pdf_service = PDFService()
    await asyncio.to_thread(
        pdf_service.build_pdf_report,
        output_path=pdf_path,
        sections=sections,
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
    print(f"\n[Success] Compilation complete! Saved to {pdf_path}")

if __name__ == "__main__":
    asyncio.run(main())
