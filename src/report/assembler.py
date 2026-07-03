from typing import Dict, Any, Tuple
from src.config.schema import BirthDetails
from src.services.geocoding import GeocodingService
from src.services.vedastro_service import VedAstroService
from src.services.gemini_service import GeminiService
from src.report.data_mapper import map_astrological_context
from src.prompts.love_report import COSMIC_ORACLE_SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

def format_iso_dt(date_str: str, time_str: str) -> str:
    """Format date and time to ISO 8601 format."""
    if len(time_str.split(":")) == 2:
        time_str = f"{time_str}:00"
    return f"{date_str}T{time_str}"

def assemble_report(
    primary: BirthDetails,
    secondary: BirthDetails,
    opencage_api_key: str,
    gemini_api_key: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Orchestrates the entire report creation workflow:
    1. Geocodes both individuals' birth places.
    2. Calls VedAstro API for planetary and compatibility metrics.
    3. Maps response data.
    4. Generates the final Gemini report.
    
    Returns:
        A tuple of (generated_report_markdown, astrological_context_dict).
    """
    # 1. Geocoding
    geocoder = GeocodingService(opencage_api_key)
    
    primary_geo = geocoder.geocode(primary.placeOfBirth)
    if not primary_geo:
        raise ValueError(f"Could not geocode primary location: {primary.placeOfBirth}")
        
    secondary_geo = geocoder.geocode(secondary.placeOfBirth)
    if not secondary_geo:
        raise ValueError(f"Could not geocode secondary location: {secondary.placeOfBirth}")

    # 2. DateTime Formatting
    primary_dt = format_iso_dt(primary.dateOfBirth, primary.timeOfBirth)
    secondary_dt = format_iso_dt(secondary.dateOfBirth, secondary.timeOfBirth)

    # 3. VedAstro calculations & Data Mapping
    vedastro = VedAstroService()
    
    context = map_astrological_context(
        service=vedastro,
        primary_name=primary.name,
        primary_dt=primary_dt,
        primary_lat=primary_geo["latitude"],
        primary_lon=primary_geo["longitude"],
        primary_tz=primary_geo["timezone"],
        secondary_name=secondary.name,
        secondary_dt=secondary_dt,
        secondary_lat=secondary_geo["latitude"],
        secondary_lon=secondary_geo["longitude"],
        secondary_tz=secondary_geo["timezone"]
    )

    # 4. Prepare User Prompt for Gemini
    primary_data = context["primary"]
    secondary_data = context["secondary"]
    compat_data = context["compatibility"]
    
    # Helper to retrieve planet info
    def get_planet_info(person_data: Dict[str, Any], name: str) -> Dict[str, Any]:
        for pos in person_data["planetaryPositions"]:
            if pos["name"] == name:
                return pos
        return {}

    p_venus = get_planet_info(primary_data, "Venus")
    p_mars = get_planet_info(primary_data, "Mars")
    s_venus = get_planet_info(secondary_data, "Venus")
    s_mars = get_planet_info(secondary_data, "Mars")

    user_prompt = USER_PROMPT_TEMPLATE.format(
        primary_name=primary_data["name"],
        primary_sun=primary_data["sunSign"],
        primary_moon=primary_data["moonSign"],
        primary_ascendant=primary_data["ascendant"],
        primary_nakshatra=primary_data["nakshatra"],
        primary_venus_sign=p_venus.get("sign", ""),
        primary_venus_house=p_venus.get("house", 1),
        primary_mars_sign=p_mars.get("sign", ""),
        primary_mars_house=p_mars.get("house", 1),
        
        secondary_name=secondary_data["name"],
        secondary_sun=secondary_data["sunSign"],
        secondary_moon=secondary_data["moonSign"],
        secondary_ascendant=secondary_data["ascendant"],
        secondary_nakshatra=secondary_data["nakshatra"],
        secondary_venus_sign=s_venus.get("sign", ""),
        secondary_venus_house=s_venus.get("house", 1),
        secondary_mars_sign=s_mars.get("sign", ""),
        secondary_mars_house=s_mars.get("house", 1),
        
        guna_score=compat_data["totalGunaScore"],
        verdict_description=compat_data["verdict"]["description"]
    )

    # 5. Call Gemini Service
    gemini = GeminiService(api_key=gemini_api_key)
    report = gemini.generate_report(COSMIC_ORACLE_SYSTEM_PROMPT, user_prompt)
    
    return report, context
