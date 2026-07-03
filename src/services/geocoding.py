from typing import Dict, Any, Optional
from opencage.geocoder import OpenCageGeocode

class GeocodingService:
    def __init__(self, api_key: str):
        """Initializes the OpenCage geocoding service with the provided API key."""
        if not api_key:
            raise ValueError("OpenCage API key must be provided.")
        self.geocoder = OpenCageGeocode(api_key)

    def geocode(self, location_name: str) -> Optional[Dict[str, Any]]:
        """
        Geocodes a location name to extract latitude, longitude, timezone, and formatted address.

        Args:
            location_name: Name of the place (e.g., 'Tokyo, Japan')

        Returns:
            Dict containing 'latitude', 'longitude', 'timezone', and 'formatted' address,
            or None if no results are found.
        """
        try:
            results = self.geocoder.geocode(location_name)
            if not results:
                return None

            first_result = results[0]
            geometry = first_result.get("geometry", {})
            annotations = first_result.get("annotations", {})
            timezone_info = annotations.get("timezone", {})

            return {
                "latitude": geometry.get("lat"),
                "longitude": geometry.get("lng"),
                "timezone": timezone_info.get("name"),
                "formatted": first_result.get("formatted"),
            }
        except Exception as e:
            raise RuntimeError(f"Geocoding failed for '{location_name}': {e}")
