import json

def ordinal(n):
    """Return ordinal string for a number (1st, 2nd, 3rd, 4th, ...)."""
    n = int(n)
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def parse_prokerala_to_english(filename="scratch/prokerala_output.json", person_name="Aarav"):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if data.get("status") != "ok":
        print("Invalid Prokerala JSON status.")
        return
        
    planets_list = data["data"]["planet_position"]
    
    sentences = []
    sentences.append(f"=== Astrological Placements for {person_name} (Parsed from Prokerala) ===")
    
    for p in planets_list:
        name = p["name"]
        if name == "Ascendant":
            continue
            
        rasi_name = p["rasi"]["name"]
        
        # Use the "position" field directly from Prokerala JSON.
        # This is the sign position (1-indexed from Aries: Aries=1, Taurus=2, ..., Libra=7, etc.)
        position = p["position"]
        
        is_retro = p.get("is_retrograde", False)
        retro_str = " in retrograde" if is_retro else ""
        
        # Format degrees
        degree = p.get("degree", 0)
        
        sentence = f"{person_name} has {name}{retro_str} placed in the {ordinal(position)} position in the zodiac sign of {rasi_name} (at {degree:.2f}°)."
        sentences.append(sentence)

    output_text = "\n".join(sentences)
    output_path = "scratch/parsed_prokerala_astrology.txt"
    with open(output_path, "w", encoding="utf-8") as out_f:
        out_f.write(output_text)
        
    print("--- PARSED PROKERALA ENGLISH TEXT ---")
    print(output_text)
    print("-------------------------------------")
    print(f"Prokerala parsed text saved to {output_path}")

if __name__ == "__main__":
    parse_prokerala_to_english()
