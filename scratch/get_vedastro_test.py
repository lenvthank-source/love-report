import json
import requests

def fetch_vedastro_data():
    url = "https://api.vedastro.org/api/Calculate/AllPlanetData"
    payload = {
      "PlanetName": {
        "Name": "All"
      },
      "Time": {
        "StdTime": "14:30 25/10/1992 +05:30",
        "TimeZone": "+05:30",
        "Location": {
          "Name": "Mumbai",
          "Longitude": 72.8777,
          "Latitude": 19.076
        }
      }
    }
    
    print("Calling VedAstro POST AllPlanetData...")
    headers = {"Content-Type": "application/json", "x-api-key": "FreeAPIUser"}
    res = requests.post(url, json=payload, headers=headers)
    res.raise_for_status()
    
    output_path = "scratch/vedastro_output.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(res.json(), f, indent=2)
    print(f"Saved VedAstro payload to {output_path}")

    # Now let's parse this exact file directly and save to scratch/parsed_vedastro_mumbai.txt
    planets_list = res.json()["Payload"]["AllPlanetData"]
    sentences = []
    sentences.append("=== Astrological Placements for Aarav (1992 Mumbai Profile - parsed from VedAstro JSON) ===")
    for entry in planets_list:
        for planet_name, details in entry.items():
            rasi_sign = details.get("PlanetRasiD1Sign", {}).get("Name", "Unknown Rasi")
            house_str = details.get("HousePlanetOccupiesBasedOnSign", "House1")
            house_num = house_str.replace("House", "")
            nakshatra = details.get("PlanetConstellation", "Unknown Nakshatra")
            
            is_retro = details.get("IsPlanetRetrograde", "False") == "True"
            retro_str = " in retrograde" if is_retro else ""
            
            is_combust = details.get("IsPlanetCombust", "False") == "True"
            combust_str = " (combust)" if is_combust else ""
            
            sentence = f"Aarav has {planet_name}{retro_str}{combust_str} placed in the {house_num}th house in the zodiac sign of {rasi_sign} (Nakshatra: {nakshatra})."
            sentences.append(sentence)
            
    parsed_text = "\n".join(sentences)
    parsed_path = "scratch/parsed_vedastro_mumbai.txt"
    with open(parsed_path, "w", encoding="utf-8") as out_f:
        out_f.write(parsed_text)
    print(f"Saved parsed text to {parsed_path}")

if __name__ == "__main__":
    fetch_vedastro_data()

