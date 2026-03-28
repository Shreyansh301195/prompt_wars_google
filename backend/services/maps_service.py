"""
JeevanSetu.AI — Google Maps Service
Geocoding and nearby location search for action plans.
"""

import logging
import httpx
from typing import Optional

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


class MapsService:
    """Google Maps Geocoding and Places API integration."""

    def __init__(self):
        self.settings = get_settings()
        self.available = self.settings.is_maps_available
        if self.available:
            logger.info("✅ Google Maps service initialized")
        else:
            logger.warning("⚠️ Google Maps not available (no API key)")

    async def geocode(self, address: str) -> dict:
        """
        Convert address to coordinates using Google Geocoding API.
        
        Returns:
            dict with 'lat', 'lng', 'formatted_address'
        """
        if not self.available:
            return {"lat": 0, "lng": 0, "error": "Maps API not available"}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/geocode/json",
                    params={
                        "address": address,
                        "key": self.settings.google_maps_api_key
                    }
                )
                response.raise_for_status()
                data = response.json()

                if data["status"] == "OK" and data["results"]:
                    result = data["results"][0]
                    location = result["geometry"]["location"]
                    return {
                        "lat": location["lat"],
                        "lng": location["lng"],
                        "formatted_address": result["formatted_address"]
                    }

                return {"lat": 0, "lng": 0, "error": f"Geocoding failed: {data['status']}"}

        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return {"lat": 0, "lng": 0, "error": str(e)}

    async def find_nearby(self, lat: float, lng: float, 
                          place_type: str = "hospital",
                          radius: int = 5000) -> list[dict]:
        """
        Find nearby places using Google Places API.
        
        Args:
            lat, lng: Center coordinates
            place_type: Type of place (hospital, fire_station, police, pharmacy)
            radius: Search radius in meters
            
        Returns:
            list of place dicts with name, lat, lng, address, rating
        """
        if not self.available:
            return []

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://maps.googleapis.com/maps/api/place/nearbysearch/json",
                    params={
                        "location": f"{lat},{lng}",
                        "radius": radius,
                        "type": place_type,
                        "key": self.settings.google_maps_api_key
                    }
                )
                response.raise_for_status()
                data = response.json()

                places = []
                for result in data.get("results", [])[:5]:  # Limit to 5
                    place_location = result.get("geometry", {}).get("location", {})
                    places.append({
                        "name": result.get("name", "Unknown"),
                        "lat": place_location.get("lat", 0),
                        "lng": place_location.get("lng", 0),
                        "address": result.get("vicinity", ""),
                        "type": place_type,
                        "rating": result.get("rating", 0),
                        "open_now": result.get("opening_hours", {}).get("open_now", None)
                    })

                return places

        except Exception as e:
            logger.error(f"Nearby search error: {e}")
            return []

    async def get_directions_url(self, origin_lat: float, origin_lng: float,
                                  dest_lat: float, dest_lng: float) -> str:
        """Generate a Google Maps directions URL."""
        return (
            f"https://www.google.com/maps/dir/{origin_lat},{origin_lng}/"
            f"{dest_lat},{dest_lng}"
        )


# Singleton
_maps_service: Optional[MapsService] = None


def get_maps_service() -> MapsService:
    global _maps_service
    if _maps_service is None:
        _maps_service = MapsService()
    return _maps_service
