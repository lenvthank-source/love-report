import os
import requests
import zoneinfo
from datetime import datetime
from typing import Dict, Any, Optional, List
from src.cache.file_cache import FileCache

def format_datetime_for_vedastro(dt_str: str, timezone_name: str):
    """
    Parses dt_str (e.g., '1995-11-20T10:30:00') and timezone_name (e.g., 'Asia/Kolkata')
    and returns (time_str, date_str, offset_str).
    """
    dt = datetime.fromisoformat(dt_str)
    try:
        tz = zoneinfo.ZoneInfo(timezone_name)
        # Since dt_str is local time of birth, localize it directly:
        dt_localized = dt.replace(tzinfo=tz)
    except Exception:
        dt_localized = dt.replace(tzinfo=zoneinfo.ZoneInfo("UTC"))
        
    time_str = dt_localized.strftime("%H:%M")
    date_str = dt_localized.strftime("%d/%m/%Y")
    
    offset = dt_localized.strftime("%z")
    if offset:
        offset_str = f"{offset[:3]}:{offset[3:]}"
    else:
        offset_str = "+00:00"
        
    return time_str, date_str, offset_str

def clean_api_val(val: Any) -> Any:
    if isinstance(val, dict):
        if "Name" in val:
            return val["Name"]
    elif isinstance(val, list):
        return [clean_api_val(item) for item in val]
    return val

class VedAstroService:
    def __init__(self, api_key: Optional[str] = None, cache_dir: str = ".cache"):
        self.api_key = api_key or os.getenv("VEDASTRO_API_KEY") or "FreeAPIUser"
        self.cache = FileCache(cache_dir=cache_dir)
        self.base_url = "https://api.vedastro.org/api"

    def _make_request(self, endpoint: str) -> Any:
        # Prepend the APIKey to the URL path if the endpoint is a Calculation endpoint
        # e.g., "Calculate/..." becomes "APIKey/YOUR_KEY/Calculate/..."
        if endpoint.startswith("Calculate/") and self.api_key:
            url = f"{self.base_url}/APIKey/{self.api_key}/{endpoint}"
        else:
            url = f"{self.base_url}/{endpoint}"
        
        # Check cache
        cached_val = self.cache.get(url)
        if cached_val is not None:
            return cached_val

        headers = {"x-api-key": self.api_key}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get("Status") == "Pass":
            payload = data.get("Payload")
            # Cache the payload
            self.cache.set(url, payload)
            return payload
        else:
            raise RuntimeError(f"VedAstro API error for {url}: {data}")

    def _make_post_request(self, endpoint: str, payload: Dict[str, Any]) -> Any:
        url = f"{self.base_url}/{endpoint}"
            
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
        
        # Simple caching based on url + payload string
        cache_key = f"{url}:{str(payload)}"
        cached_val = self.cache.get(cache_key)
        if cached_val is not None:
            return cached_val
            
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if data.get("Status") == "Pass":
            payload_data = data.get("Payload")
            self.cache.set(cache_key, payload_data)
            return payload_data
        else:
            raise RuntimeError(f"VedAstro API POST error for {url}: {data}")

    # --- EXISTING METHODS (FOR BACKWARD COMPATIBILITY) ---

    def get_planet_sign(self, planet: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> str:
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        long_deg = self.get_planet_longitude(planet, lat, lon, time_str, date_str, offset_str)
        sign_idx = int(long_deg / 30) % 12
        return signs[sign_idx]

    def get_planet_house(self, planet: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> int:
        planet_sign = self.get_planet_sign(planet, lat, lon, time_str, date_str, offset_str)
        asc_sign = self.get_house_sign("House1", lat, lon, time_str, date_str, offset_str)
        
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        try:
            p_idx = signs.index(planet_sign)
            a_idx = signs.index(asc_sign)
            return ((p_idx - a_idx) % 12) + 1
        except ValueError:
            return 1

    def get_planet_nakshatra(self, planet: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> str:
        endpoint = f"Calculate/PlanetConstellation/PlanetName/{planet}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        try:
            return clean_api_val(res.get("PlanetConstellation", "Unknown"))
        except (KeyError, TypeError):
            return "Unknown"

    def get_planet_longitude(self, planet: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> float:
        endpoint = f"Calculate/PlanetNirayanaLongitude/PlanetName/{planet}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        try:
            return float(res["PlanetNirayanaLongitude"]["TotalDegrees"])
        except (KeyError, TypeError):
            return 0.0

    def get_house_sign(self, house: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> str:
        endpoint = f"Calculate/HouseSignName/HouseName/{house}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        try:
            return clean_api_val(res.get("HouseSignName", "Aries"))
        except (KeyError, TypeError):
            return "Aries"

    def get_house_longitude(self, house: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> float:
        endpoint = f"Calculate/HouseLongitude/HouseName/{house}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        try:
            val = res["HouseLongitude"]
            for part in val.split(","):
                if "Middle:" in part:
                    return float(part.split("Middle:")[1].strip())
            return 0.0
        except (KeyError, TypeError, IndexError, ValueError):
            return 0.0

    def is_planet_retrograde(self, planet: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> bool:
        endpoint = f"Calculate/IsPlanetRetrograde/PlanetName/{planet}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        try:
            return str(res["IsPlanetRetrograde"]).strip().lower() == "true"
        except (KeyError, TypeError):
            return False

    def get_match_report(self, lat1: float, lon1: float, time1: str, date1: str, offset1: str,
                         lat2: float, lon2: float, time2: str, date2: str, offset2: str) -> Dict[str, Any]:
        endpoint = f"Calculate/MatchReport/Location/{lat1},{lon1}/Time/{time1}/{date1}/{offset1}/Location/{lat2},{lon2}/Time/{time2}/{date2}/{offset2}/Ayanamsa/LAHIRI"
        return self._make_request(endpoint)

    # --- NEW INDIVIDUAL & DIVISIONAL METHODS ---

    def get_all_planet_data(self, place: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> List[Dict[str, Any]]:
        """Call AllPlanetData bulk endpoint."""
        endpoint = "Calculate/AllPlanetData"
        payload = {
            "PlanetName": {"Name": "All"},
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
        res = self._make_post_request(endpoint, payload)
        return res.get("AllPlanetData", [])

    def get_all_house_rasi_signs(self, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> Dict[str, str]:
        endpoint = f"Calculate/AllHouseRasiSigns/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        # Clean dictionary values
        return {k: clean_api_val(v) for k, v in res.items()}

    def get_all_planet_navamsha_signs(self, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> Dict[str, str]:
        endpoint = f"Calculate/AllPlanetNavamshaSign/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return {k: clean_api_val(v) for k, v in res.items()}

    def get_all_planet_trimshamsha_signs(self, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> Dict[str, str]:
        endpoint = f"Calculate/AllPlanetTrimshamshaSign/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return {k: clean_api_val(v) for k, v in res.items()}

    def get_lagna_sign_name(self, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> str:
        endpoint = f"Calculate/LagnaSignName/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return clean_api_val(res.get("LagnaSignName", "Aries"))

    def get_lord_of_house(self, house: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> str:
        endpoint = f"Calculate/LordOfHouse/HouseName/{house}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return clean_api_val(res.get("LordOfHouse", "Mars"))

    def get_planets_in_house(self, house: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> List[str]:
        endpoint = f"Calculate/PlanetsInHouseBasedOnSign/HouseName/{house}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        raw_list = res.get("PlanetsInHouseBasedOnSign", [])
        return [clean_api_val(p) for p in raw_list]

    def get_planets_in_conjunction(self, planet: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> List[str]:
        endpoint = f"Calculate/PlanetsInConjunction/PlanetName/{planet}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        raw_list = res.get("PlanetsInConjunction", [])
        return [clean_api_val(p) for p in raw_list]

    def get_planet_relationship(self, planet1: str, planet2: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> str:
        endpoint = f"Calculate/PlanetCombinedRelationshipWithPlanet/PlanetName/{planet1}/PlanetName/{planet2}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return clean_api_val(res.get("PlanetCombinedRelationshipWithPlanet", "Neutral"))

    def is_planet_combust_specific(self, planet: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> bool:
        endpoint = f"Calculate/IsPlanetCombust/PlanetName/{planet}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return str(res.get("IsPlanetCombust", "False")).strip().lower() == "true"

    def get_house_navamsha_d9_sign(self, house: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> str:
        endpoint = f"Calculate/HouseNavamshaD9Sign/HouseName/{house}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return clean_api_val(res.get("HouseNavamshaD9Sign", "Aries"))

    def get_house_trimshamsha_d30_sign(self, house: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> str:
        endpoint = f"Calculate/HouseTrimshamshaD30Sign/HouseName/{house}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return clean_api_val(res.get("HouseTrimshamshaD30Sign", "Aries"))

    def is_planet_afflicted_specific(self, planet: str, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> bool:
        endpoint = f"Calculate/IsPlanetAfflicted/PlanetName/{planet}/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return str(res.get("IsPlanetAfflicted", "False")).strip().lower() == "true"

    def get_kuja_dosha_score(self, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> float:
        endpoint = f"Calculate/KujaDosaScore/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return float(res.get("KujaDosaScore", 0.0))

    def get_malefic_planet_list(self, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> List[str]:
        endpoint = f"Calculate/MaleficPlanetListForLagna/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        raw_list = res.get("MaleficPlanetListForLagna", [])
        return [clean_api_val(p) for p in raw_list]

    def get_benefic_planet_list(self, lat: float, lon: float, time_str: str, date_str: str, offset_str: str) -> List[str]:
        endpoint = f"Calculate/BeneficPlanetList/Location/{lat},{lon}/Time/{time_str}/{date_str}/{offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        raw_list = res.get("BeneficPlanetList", [])
        return [clean_api_val(p) for p in raw_list]


    def get_dasa_at_range(self, lat: float, lon: float, birth_time_str: str, birth_date_str: str, birth_offset_str: str,
                          start_time_str: str, start_date_str: str, end_time_str: str, end_date_str: str,
                          levels: int = 2, precision_hours: int = 24) -> Dict[str, Any]:
        payload = {
            "birthTime": {
                "StdTime": f"{birth_time_str} {birth_date_str} {birth_offset_str}",
                "Location": {
                    "Name": "Empty",
                    "Longitude": lon,
                    "Latitude": lat
                }
            },
            "startTime": {
                "StdTime": f"{start_time_str} {start_date_str} {birth_offset_str}",
                "Location": {
                    "Name": "Empty",
                    "Longitude": lon,
                    "Latitude": lat
                }
            },
            "endTime": {
                "StdTime": f"{end_time_str} {end_date_str} {birth_offset_str}",
                "Location": {
                    "Name": "Empty",
                    "Longitude": lon,
                    "Latitude": lat
                }
            },
            "levels": levels,
            "precisionHours": precision_hours
        }
        res = self._make_post_request("Calculate/DasaAtRange", payload)
        return res.get("DasaAtRange") or {}

    def get_dasa_for_now(self, lat: float, lon: float, birth_time_str: str, birth_date_str: str, birth_offset_str: str, levels: int = 3) -> Dict[str, Any]:
        endpoint = f"Calculate/DasaForNow/Levels/{levels}/Location/{lat},{lon}/Time/{birth_time_str}/{birth_date_str}/{birth_offset_str}/Ayanamsa/LAHIRI"
        res = self._make_request(endpoint)
        return res.get("DasaForNow", {})

    def get_dasa_info_for_ascendant(self, ascendant: str) -> Dict[str, Any]:
        endpoint = f"Calculate/GetDasaInfoForAscendant/ZodiacName/{ascendant}"
        return self._make_request(endpoint)

    def get_planet_tags(self, planet: str) -> str:
        endpoint = f"Calculate/GetPlanetTags/PlanetName/{planet}"
        res = self._make_request(endpoint)
        return res.get("GetPlanetTags", "")

    def get_house_tags(self, house: str) -> str:
        endpoint = f"Calculate/GetHouseTags/HouseName/{house}"
        res = self._make_request(endpoint)
        return res.get("GetHouseTags", "")

    def get_sign_tags(self, sign: str) -> str:
        endpoint = f"Calculate/GetSignTags/ZodiacName/{sign}"
        res = self._make_request(endpoint)
        return res.get("GetSignTags", "")
