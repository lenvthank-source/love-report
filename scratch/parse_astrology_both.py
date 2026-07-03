import json
import requests
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.geocoding import GeocodingService
from src.services.vedastro_service import format_datetime_for_vedastro
from dotenv import load_dotenv

load_dotenv()

# Sign name to position mapping (1-indexed from Aries)
# VedAstro uses English names, Prokerala uses Sanskrit names
SIGN_TO_POSITION = {
    # English names (VedAstro)
    "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4,
    "Leo": 5, "Virgo": 6, "Libra": 7, "Scorpio": 8,
    "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12,
    # Sanskrit names (Prokerala)
    "Mesha": 1, "Vrishabha": 2, "Mithuna": 3, "Karka": 4,
    "Simha": 5, "Kanya": 6, "Tula": 7, "Vrischika": 8,
    "Dhanu": 9, "Makara": 10, "Kumbha": 11, "Meena": 12,
}

def get_sign_position(sign_name):
    """Get the sign position (1-indexed from Aries) from a sign name."""
    return SIGN_TO_POSITION.get(sign_name, 0)

def ordinal(n):
    """Return ordinal string for a number (1st, 2nd, 3rd, 4th, ...)."""
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def fetch_and_parse():
    # Load input config
    with open("sample/input.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    opencage_key = os.getenv("OPENCAGE_API_KEY", "3723e0d7ceb64eb3bd3623477d4c3142")
    geocoder = GeocodingService(opencage_key)
    
    sentences = []
    
    for key in ["primary", "secondary"]:
        person = config[key]
        name = person["name"]
        dob = person["dateOfBirth"]
        tob = person["timeOfBirth"]
        place = person["placeOfBirth"]
        
        print(f"Geocoding {name} ({place})...")
        geo = geocoder.geocode(place)
        if not geo:
            print(f"Could not geocode {place}")
            continue
            
        lat = geo["latitude"]
        lon = geo["longitude"]
        tz = geo["timezone"]
        
        # Format date for VedAstro
        dt_str = f"{dob}T{tob}:00"
        time_str, date_str, offset_str = format_datetime_for_vedastro(dt_str, tz)
        
        # Build payload for VedAstro AllPlanetData
        url = "https://api.vedastro.org/api/Calculate/AllPlanetData"
        payload = {
            "PlanetName": {
                "Name": "All"
            },
            "Time": {
                "StdTime": f"{time_str} {date_str.replace('-', '/')} {offset_str}",
                "TimeZone": offset_str,
                "Location": {
                    "Name": place.split(",")[0],
                    "Longitude": lon,
                    "Latitude": lat
                }
            }
        }
        
        print(f"Fetching VedAstro AllPlanetData for {name}...")
        headers = {"Content-Type": "application/json", "x-api-key": "FreeAPIUser"}
        res = requests.post(url, json=payload, headers=headers)
        res.raise_for_status()
        data = res.json()
        
        if data.get("Status") != "Pass":
            print(f"VedAstro API call failed for {name}: {data}")
            continue
            
        planets_list = data["Payload"]["AllPlanetData"]
        
        sentences.append(f"=== Astrological Placements for {name} ===")
        for entry in planets_list:
            for planet_name, details in entry.items():
                rasi_sign = details.get("PlanetRasiD1Sign", {}).get("Name", "Unknown Rasi")
                
                # Use sign position (1-indexed from Aries) to match Prokerala's "position" field
                # e.g. Libra -> 7, Scorpio -> 8, etc.
                position = get_sign_position(rasi_sign)
                
                nakshatra = details.get("PlanetConstellation", "Unknown Nakshatra")
                
                is_retro = details.get("IsPlanetRetrograde", "False") == "True"
                retro_str = " in retrograde" if is_retro else ""
                
                is_combust = details.get("IsPlanetCombust", "False") == "True"
                combust_str = " (combust)" if is_combust else ""
                
                sentence = f"{name} has {planet_name}{retro_str}{combust_str} placed in the {ordinal(position)} position in the zodiac sign of {rasi_sign} (Nakshatra: {nakshatra})."
                sentences.append(sentence)
                
                if details.get("IsPlanetAfflicted") == "True":
                    sentences.append(f"  - This placement of {planet_name} is afflicted.")
                if details.get("IsPlanetExalted") == "True":
                    sentences.append(f"  - {planet_name} is in exalted strength.")
                elif details.get("IsPlanetDebilitated") == "True":
                    sentences.append(f"  - {planet_name} is debilitated.")
                
                if details.get("IsPlanetInEnemyHouse") == "True":
                    sentences.append(f"  - {planet_name} sits in an enemy house.")
                elif details.get("IsPlanetInFriendHouse") == "True":
                    sentences.append(f"  - {planet_name} sits in a friendly house.")
                elif details.get("IsPlanetInOwnHouse") == "True":
                    sentences.append(f"  - {planet_name} sits in its own house.")
        sentences.append("") # empty line

    # Write parsed text out
    output_text = "\n".join(sentences)
    output_path = "scratch/parsed_english_astrology.txt"
    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write(output_text)
    
    print("--- PARSED ASTROLOGICAL ENGLISH TEXT ---")
    print(output_text)
    print("----------------------------------------")
    print(f"English sentences successfully saved to {output_path}")

if __name__ == "__main__":
    fetch_and_parse()
