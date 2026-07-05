from typing import Dict, Any
from src.services.vedastro_service import format_datetime_for_vedastro, VedAstroService

SIGN_TO_INDEX = {
    "Mesha": 1, "Aries": 1,
    "Vrishabha": 2, "Taurus": 2,
    "Mithuna": 3, "Gemini": 3,
    "Karka": 4, "Cancer": 4,
    "Simha": 5, "Leo": 5,
    "Kanya": 6, "Virgo": 6,
    "Tula": 7, "Libra": 7,
    "Vrischika": 8, "Scorpio": 8,
    "Dhanu": 9, "Sagittarius": 9,
    "Makara": 10, "Capricorn": 10,
    "Kumbha": 11, "Aquarius": 11,
    "Meena": 12, "Pisces": 12
}

def map_person_astrology(
    service: VedAstroService,
    name: str,
    dt_str: str,
    lat: float,
    lon: float,
    timezone_name: str
) -> Dict[str, Any]:
    """
    Fetches raw astrology data from VedAstro API and maps it to the standard format.
    """
    time_str, date_str, offset_str = format_datetime_for_vedastro(dt_str, timezone_name)
    
    # 1. Fetch Ascendant (House1)
    asc_sign = service.get_house_sign("House1", lat, lon, time_str, date_str, offset_str)
    asc_long = service.get_house_longitude("House1", lat, lon, time_str, date_str, offset_str)
    
    # 2. Fetch planets
    planets = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"]
    planetary_positions = []
    
    planet_data = {}
    for p in planets:
        sign = service.get_planet_sign(p, lat, lon, time_str, date_str, offset_str)
        long = service.get_planet_longitude(p, lat, lon, time_str, date_str, offset_str)
        retro = service.is_planet_retrograde(p, lat, lon, time_str, date_str, offset_str) if p not in ["Rahu", "Ketu"] else True
        nakshatra = service.get_planet_nakshatra(p, lat, lon, time_str, date_str, offset_str)
        
        # House in the context is mapped to the sign index
        sign_idx = SIGN_TO_INDEX.get(sign, 1)
        
        pos = {
            "name": p,
            "sign": sign,
            "house": sign_idx,
            "degree": long % 30,
            "nakshatra": nakshatra,
            "nakshatraLord": "",
            "isRetrograde": retro
        }
        planetary_positions.append(pos)
        planet_data[p] = pos

    # Add Ascendant to positions list
    asc_sign_idx = SIGN_TO_INDEX.get(asc_sign, 1)
    planetary_positions.append({
        "name": "Ascendant",
        "sign": asc_sign,
        "house": asc_sign_idx,
        "degree": asc_long % 30,
        "nakshatra": "",
        "nakshatraLord": "",
        "isRetrograde": False
    })
    
    moon_info = planet_data.get("Moon", {})
    venus_info = planet_data.get("Venus", {})
    mars_info = planet_data.get("Mars", {})

    return {
        "name": name,
        "sunSign": planet_data.get("Sun", {}).get("sign", ""),
        "moonSign": moon_info.get("sign", ""),
        "ascendant": asc_sign,
        "nakshatra": moon_info.get("nakshatra", ""),
        "venusSign": venus_info.get("sign", ""),
        "venusHouse": venus_info.get("house", 1),
        "marsSign": mars_info.get("sign", ""),
        "marsHouse": mars_info.get("house", 1),
        "seventhHouseLord": "Unknown Lord",
        "mangalDosha": {
            "present": False,
            "severity": "none",
            "cancellation": []
        },
        "planetaryPositions": planetary_positions
    }

def map_astrological_context(
    service: VedAstroService,
    primary_name: str,
    primary_dt: str,
    primary_lat: float,
    primary_lon: float,
    primary_tz: str,
    secondary_name: str,
    secondary_dt: str,
    secondary_lat: float,
    secondary_lon: float,
    secondary_tz: str
) -> Dict[str, Any]:
    """
    Coordinates raw API calls and maps them into the full AstrologicalContext structure.
    """
    primary_ctx = map_person_astrology(service, primary_name, primary_dt, primary_lat, primary_lon, primary_tz)
    secondary_ctx = map_person_astrology(service, secondary_name, secondary_dt, secondary_lat, secondary_lon, secondary_tz)
    
    # Calculate match report
    time1, date1, offset1 = format_datetime_for_vedastro(primary_dt, primary_tz)
    time2, date2, offset2 = format_datetime_for_vedastro(secondary_dt, secondary_tz)
    
    try:
        match_data = service.get_match_report(
            primary_lat, primary_lon, time1, date1, offset1,
            secondary_lat, secondary_lon, time2, date2, offset2
        )
        guna_score = match_data.get("KutaScore", 0)
        verdict_desc = match_data.get("Summary", {}).get("ScoreSummary", "No summary available.")
    except Exception as e:
        guna_score = 0
        verdict_desc = f"Match calculations failed: {e}"
        
    verdict_type = "good" if guna_score >= 18 else "bad"
    
    compatibility = {
        "totalGunaScore": guna_score,
        "kutaScores": [],
        "verdict": {
            "type": verdict_type,
            "description": verdict_desc
        }
    }
    
    return {
        "primary": primary_ctx,
        "secondary": secondary_ctx,
        "compatibility": compatibility
    }
