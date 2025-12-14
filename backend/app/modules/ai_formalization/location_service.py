"""
Location service for finding real office addresses using Google Places API.
Provides addresses, phone numbers, and opening hours for government offices.
"""

import urllib.parse
from typing import Any

import httpx

from app.core.config import settings


class OfficeInfo:
    """Information about a government office."""

    def __init__(
        self,
        name: str,
        address: str,
        phone: str | None = None,
        opening_hours: str | None = None,
        google_maps_link: str | None = None,
        coordinates: dict[str, float] | None = None,
    ):
        self.name = name
        self.address = address
        self.phone = phone
        self.opening_hours = opening_hours
        self.google_maps_link = google_maps_link
        self.coordinates = coordinates

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for prompt."""
        return {
            "name": self.name,
            "address": self.address,
            "phone": self.phone,
            "opening_hours": self.opening_hours,
            "google_maps_link": self.google_maps_link,
            "coordinates": self.coordinates,
        }


class LocationService:
    """Service for finding government office locations using Google Places API."""

    def __init__(self, api_key: str | None = None):
        """
        Initialize location service.

        Args:
            api_key: Google Places API key. If None, uses GOOGLE_PLACES_API_KEY from env.
        """
        self.api_key = api_key or getattr(settings, "google_places_api_key", None)
        self.base_url = "https://maps.googleapis.com/maps/api/place"

    async def _search_place(
        self, query: str, location: str | None = None
    ) -> dict[str, Any] | None:
        """
        Search for a place using Google Places API Text Search.

        Args:
            query: Search query (e.g., "Emater Barra Mansa RJ")
            location: Optional location bias (e.g., "Barra Mansa, RJ, Brazil")

        Returns:
            Place details dict or None if not found
        """
        if not self.api_key:
            return None

        try:
            params = {
                "query": query,
                "key": self.api_key,
                "language": "pt-BR",
            }
            if location:
                params["location"] = location

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/textsearch/json", params=params
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "OK" and data.get("results"):
                    # Get first result
                    place = data["results"][0]
                    place_id = place.get("place_id")

                    # Get detailed information
                    details = await self._get_place_details(place_id)
                    if details:
                        return {**place, **details}

                    return place

        except Exception as e:
            print(f"Error searching place: {e}")
            return None

        return None

    async def _get_place_details(self, place_id: str) -> dict[str, Any] | None:
        """
        Get detailed information about a place.

        Args:
            place_id: Google Places place_id

        Returns:
            Place details dict or None
        """
        if not self.api_key:
            return None

        try:
            params = {
                "place_id": place_id,
                "key": self.api_key,
                "language": "pt-BR",
                "fields": "formatted_address,formatted_phone_number,opening_hours,geometry",
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/details/json", params=params
                )
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "OK" and data.get("result"):
                    return data["result"]

        except Exception as e:
            print(f"Error getting place details: {e}")
            return None

        return None

    def _create_maps_link(self, address: str) -> str:
        """
        Create Google Maps link for an address.

        Args:
            address: Full address string

        Returns:
            Google Maps search URL
        """
        encoded = urllib.parse.quote_plus(address)
        return f"https://www.google.com/maps/search/?api=1&query={encoded}"

    async def find_emater_office(
        self, city: str, state: str
    ) -> OfficeInfo | None:
        """
        Find Emater office for a city/state.

        Args:
            city: City name
            state: State abbreviation (e.g., "RJ", "SP")

        Returns:
            OfficeInfo or None if not found
        """
        # Try different search queries
        queries = [
            f"Emater {city} {state}",
            f"Emater-Rio {city} {state}",
            f"Empresa de Assistência Técnica {city} {state}",
        ]

        for query in queries:
            result = await self._search_place(query, location=f"{city}, {state}, Brazil")
            if result:
                address = result.get("formatted_address") or result.get("vicinity", "")
                phone = result.get("formatted_phone_number") or result.get(
                    "international_phone_number"
                )
                opening_hours = None
                if result.get("opening_hours") and result["opening_hours"].get(
                    "weekday_text"
                ):
                    opening_hours = ", ".join(
                        result["opening_hours"]["weekday_text"][:5]
                    )  # Monday-Friday

                geometry = result.get("geometry", {})
                coordinates = None
                if geometry.get("location"):
                    coordinates = {
                        "lat": geometry["location"].get("lat"),
                        "lng": geometry["location"].get("lng"),
                    }

                maps_link = self._create_maps_link(address)

                return OfficeInfo(
                    name=f"Emater {city}/{state}",
                    address=address,
                    phone=phone,
                    opening_hours=opening_hours,
                    google_maps_link=maps_link,
                    coordinates=coordinates,
                )

        return None

    async def find_receita_federal(
        self, city: str, state: str
    ) -> OfficeInfo | None:
        """
        Find Receita Federal office for a city/state.

        Args:
            city: City name
            state: State abbreviation

        Returns:
            OfficeInfo or None if not found
        """
        queries = [
            f"Receita Federal {city} {state}",
            f"RFB {city} {state}",
        ]

        for query in queries:
            result = await self._search_place(query, location=f"{city}, {state}, Brazil")
            if result:
                address = result.get("formatted_address") or result.get("vicinity", "")
                phone = result.get("formatted_phone_number") or "146"
                opening_hours = None
                if result.get("opening_hours") and result["opening_hours"].get(
                    "weekday_text"
                ):
                    opening_hours = ", ".join(
                        result["opening_hours"]["weekday_text"][:5]
                    )

                geometry = result.get("geometry", {})
                coordinates = None
                if geometry.get("location"):
                    coordinates = {
                        "lat": geometry["location"].get("lat"),
                        "lng": geometry["location"].get("lng"),
                    }

                maps_link = self._create_maps_link(address)

                return OfficeInfo(
                    name=f"Receita Federal {city}/{state}",
                    address=address,
                    phone=phone,
                    opening_hours=opening_hours,
                    google_maps_link=maps_link,
                    coordinates=coordinates,
                )

        return None

    async def find_sindicato_rural(
        self, city: str, state: str
    ) -> OfficeInfo | None:
        """
        Find Sindicato Rural office for a city/state.

        Args:
            city: City name
            state: State abbreviation

        Returns:
            OfficeInfo or None if not found
        """
        queries = [
            f"Sindicato Trabalhadores Rurais {city} {state}",
            f"Sindicato Rural {city} {state}",
            f"STR {city} {state}",
        ]

        for query in queries:
            result = await self._search_place(query, location=f"{city}, {state}, Brazil")
            if result:
                address = result.get("formatted_address") or result.get("vicinity", "")
                phone = result.get("formatted_phone_number")
                opening_hours = None
                if result.get("opening_hours") and result["opening_hours"].get(
                    "weekday_text"
                ):
                    opening_hours = ", ".join(
                        result["opening_hours"]["weekday_text"][:5]
                    )

                geometry = result.get("geometry", {})
                coordinates = None
                if geometry.get("location"):
                    coordinates = {
                        "lat": geometry["location"].get("lat"),
                        "lng": geometry["location"].get("lng"),
                    }

                maps_link = self._create_maps_link(address)

                return OfficeInfo(
                    name=f"Sindicato dos Trabalhadores Rurais {city}/{state}",
                    address=address,
                    phone=phone,
                    opening_hours=opening_hours,
                    google_maps_link=maps_link,
                    coordinates=coordinates,
                )

        return None

    async def find_secretaria_agricultura(
        self, city: str, state: str
    ) -> OfficeInfo | None:
        """
        Find Secretaria Municipal de Agricultura for a city/state.

        Args:
            city: City name
            state: State abbreviation

        Returns:
            OfficeInfo or None if not found
        """
        queries = [
            f"Secretaria Agricultura {city} {state}",
            f"Secretaria Municipal Agricultura {city} {state}",
            f"Prefeitura {city} {state} Secretaria Agricultura",
        ]

        for query in queries:
            result = await self._search_place(query, location=f"{city}, {state}, Brazil")
            if result:
                address = result.get("formatted_address") or result.get("vicinity", "")
                phone = result.get("formatted_phone_number") or "156"
                opening_hours = None
                if result.get("opening_hours") and result["opening_hours"].get(
                    "weekday_text"
                ):
                    opening_hours = ", ".join(
                        result["opening_hours"]["weekday_text"][:5]
                    )

                geometry = result.get("geometry", {})
                coordinates = None
                if geometry.get("location"):
                    coordinates = {
                        "lat": geometry["location"].get("lat"),
                        "lng": geometry["location"].get("lng"),
                    }

                maps_link = self._create_maps_link(address)

                return OfficeInfo(
                    name=f"Secretaria Municipal de Agricultura {city}/{state}",
                    address=address,
                    phone=phone,
                    opening_hours=opening_hours,
                    google_maps_link=maps_link,
                    coordinates=coordinates,
                )

        return None
