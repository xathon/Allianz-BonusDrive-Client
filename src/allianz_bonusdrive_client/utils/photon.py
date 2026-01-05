import requests

class PhotonClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "AllianzBonusDriveClient/1.0",
        }

    def reverse_geocode(self, latitude: float, longitude: float) -> dict:
        """Perform reverse geocoding using the Photon API."""
        response = self.session.get(
            f"{self.base_url}/reverse",
            params={"lat": latitude, "lon": longitude},
            headers=self.headers,
        )
        response.raise_for_status()
        return response.json()