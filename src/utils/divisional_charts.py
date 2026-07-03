from typing import Dict, Any, List

def map_placements_to_signs(placements_list: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Groups planets by their zodiac sign.
    Input format: List of Dicts, e.g., [{'Sun': {'PlanetRasiD1Sign': {'Name': 'Libra'}}}]
    Output format: {'Libra': ['Sun'], 'Aries': ['Moon'], ...}
    """
    signs_map = {
        "Aries": [], "Taurus": [], "Gemini": [], "Cancer": [],
        "Leo": [], "Virgo": [], "Libra": [], "Scorpio": [],
        "Sagittarius": [], "Capricorn": [], "Aquarius": [], "Pisces": []
    }
    
    for entry in placements_list:
        for planet_name, details in entry.items():
            # Format planet names as standard abbreviations (e.g. Sun -> Su, Moon -> Mo)
            abbrev = {
                "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
                "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"
            }.get(planet_name, planet_name[:2])
            
            rasi_sign = details.get("PlanetRasiD1Sign", {}).get("Name", None)
            if rasi_sign in signs_map:
                signs_map[rasi_sign].append(abbrev)
                
    return signs_map

def map_divisional_signs(signs_dict: Dict[str, str]) -> Dict[str, List[str]]:
    """
    Groups planets by sign from a bulk divisional API result.
    Input: {'Sun': 'Libra', 'Moon': 'Aries', ...}
    Output: {'Libra': ['Su'], 'Aries': ['Mo'], ...}
    """
    signs_map = {
        "Aries": [], "Taurus": [], "Gemini": [], "Cancer": [],
        "Leo": [], "Virgo": [], "Libra": [], "Scorpio": [],
        "Sagittarius": [], "Capricorn": [], "Aquarius": [], "Pisces": []
    }
    
    abbrevs = {
        "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
        "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"
    }
    
    for planet_name, sign in signs_dict.items():
        # Match standard planet names (handle case-insensitive keys)
        std_name = None
        for key in abbrevs:
            if key.lower() == planet_name.lower():
                std_name = key
                break
        if not std_name:
            continue
            
        abbrev = abbrevs[std_name]
        # Capitalize sign to match standard sign keys
        sign_cap = sign.capitalize() if isinstance(sign, str) else ""
        if sign_cap in signs_map:
            signs_map[sign_cap].append(abbrev)
            
    return signs_map
