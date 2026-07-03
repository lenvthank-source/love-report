import json

# Sign name to position mapping (1-indexed from Aries)
SIGN_TO_POSITION = {
    "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4,
    "Leo": 5, "Virgo": 6, "Libra": 7, "Scorpio": 8,
    "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12,
}

def ordinal(n):
    """Return ordinal string for a number (1st, 2nd, 3rd, 4th, ...)."""
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def parse_vedastro_to_english(filename="scratch/vedastro_output.json", person_name="Aarav"):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if data.get("Status") != "Pass":
        print("Invalid VedAstro JSON status.")
        return
        
    planets_list = data["Payload"]["AllPlanetData"]
    
    sentences = []
    sentences.append(f"=== Astrological Placements for {person_name} (parsed from VedAstro JSON) ===")
    
    for entry in planets_list:
        for planet_name, details in entry.items():
            # Get Sign
            rasi_sign = details.get("PlanetRasiD1Sign", {}).get("Name", "Unknown Rasi")
            
            # Use sign position (1-indexed from Aries) instead of house relative to ascendant
            position = SIGN_TO_POSITION.get(rasi_sign, 0)
            
            # Get Nakshatra / Constellation
            nakshatra = details.get("PlanetConstellation", "Unknown Nakshatra")
            
            # Check Retrograde
            is_retro = details.get("IsPlanetRetrograde", "False") == "True"
            retro_str = " in retrograde" if is_retro else ""
            
            # Combust status
            is_combust = details.get("IsPlanetCombust", "False") == "True"
            combust_str = " (combust)" if is_combust else ""
            
            # Build English sentence
            sentence = f"{person_name} has {planet_name}{retro_str}{combust_str} placed in the {ordinal(position)} position in the zodiac sign of {rasi_sign} (Nakshatra: {nakshatra})."
            sentences.append(sentence)
            
            # Additional conditions
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

    # Write parsed text out
    output_text = "\n".join(sentences)
    output_path = "scratch/parsed_vedastro_mumbai.txt"
    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write(output_text)
    
    print("--- PARSED ASTROLOGICAL ENGLISH TEXT ---")
    print(output_text)
    print("----------------------------------------")
    print(f"English sentences successfully saved to {output_path}")

if __name__ == "__main__":
    parse_vedastro_to_english()
