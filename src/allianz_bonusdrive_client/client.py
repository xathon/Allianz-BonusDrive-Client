import requests
from urllib.parse import urlencode
from requests.cookies import RequestsCookieJar
from datetime import datetime, timedelta
import polyline

from .utils.photon import PhotonClient

# logging.basicConfig(level=print)


class BonusdriveAPIClient:
    def __init__(
        self, base_url: str, email: str, password: str, tgt: str | None = None
    ):
        self.base_url = base_url
        self.username = email
        self.password = password
        self.tgt = tgt
        self.session = requests.Session()
        self.session.cookies = (
            RequestsCookieJar()
        )  # Use RequestsCookieJar to store cookies
        self.authenticated = False

        # Default headers
        self.headers = {
            "Accept": "*/*",
            "Accept-Encoding": "gzip",
            "Accept-Language": "en-US",
            "App-Version": "4.1.0",
            "Connection": "Keep-Alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Host": self.base_url.replace("https://", "").replace("http://", ""),
            "Platform": "Android",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 13; Pixel 5 Build/TQ3A.230901.001)",
            "X-Requested-With": "XMLHttpRequest",
        }

    def authenticate(self):
        """Authenticate the user and store session cookies."""
        if not self.tgt:
            # Step 1: Get TGT
            try:
                tgt_response = self.session.post(
                    f"{self.base_url}/cas/rest/v1/rbtickets",
                    data=urlencode({"username": self.username, "password": self.password}),
                    headers=self.headers,
                )
                tgt_response.raise_for_status()
                if tgt_response.status_code != 200:
                    raise RuntimeError("Authentication failed")
                self.tgt = tgt_response.text.strip()
            except requests.RequestException as e:
                raise RuntimeError("Authentication failed") from e

        # Step 2: Use TGT to get Service Ticket (ST)
        try:
            st_response = self.session.post(
                f"{self.base_url}/cas/rest/v1/rbtickets/tgt",
                data=urlencode(
                    {
                        "ticketGrantingTicketId": self.tgt,
                        "service": f"{self.base_url}/ipaid/",
                    }
                ),
                headers=self.headers,
                cookies=self.session.cookies,  # Use cookies from the cookiejar
            )
            st_response.raise_for_status()
            if st_response.status_code != 200:
                raise RuntimeError("Failed to obtain Service Ticket")
            service_ticket = st_response.text.strip()
        except requests.RequestException as e:
            raise RuntimeError("Failed to obtain Service Ticket") from e
        self.session.cookies.update(st_response.cookies)
        self.headers.pop("Content-Type", None)

        # Step 3: Use ST to set cookies
        cookies_response = self.session.post(
            f"{self.base_url}/ipaid/",
            data={"ticket": service_ticket},
            headers=self.headers,
            cookies=self.session.cookies,  # Use cookies from the cookiejar
            allow_redirects=False,  # Follow the redirect to capture the cookie
        )
        self.session.cookies.update(cookies_response.cookies)

        userId_response = self.session.get(
            f"{self.base_url}/ipaid/api/v2/session",
            headers=self.headers,
            cookies=self.session.cookies,  # Use cookies from the cookiejar
        )
        userId_response.raise_for_status()

        self.userId = userId_response.json().get("userId")
        self.session.cookies.set("User-ID", str(self.userId))

        # Store cookies in the RequestsCookieJar
        self.session.cookies.update(cookies_response.cookies)
        self.authenticated = True

    def get_trips(self, amount: int = 10, offset: int = 0):
        """Query the trips endpoint and return the JSON response."""
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated. Call authenticate() first."
            )

        url = f"{self.base_url}/ipaid/api/v2/users/{self.userId}/logbook/trips?offset={offset}&limit={amount}&sort=local_startdate%3Bdesc&expand=vehicle&expand=user"
        response = self.session.get(
            url,
            headers={
                "Accept-Encoding": "gzip",
                "Accept-Language": "en-US",
                "Connection": "Keep-Alive",
                "Platform": "Android",
                "User-Agent": "okhttp/4.12.0",
            },
            cookies=self.session.cookies,
        )
        response.raise_for_status()
        return response.json()["items"]

    def get_vehicleId(self):
        """Query the vehicles endpoint and return the Id of the first vehicle."""
        # If you have multiple vehicles, you need to adjust this method
        # or buy me a second car, so I'll need it myself
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated. Call authenticate() first."
            )

        url = f"{self.base_url}/ipaid/api/v2/users/{self.userId}/vehicles"
        response = self.session.get(
            url,
            headers={
                "Accept-Encoding": "gzip",
                "Accept-Language": "en-US",
                "Connection": "Keep-Alive",
                "Platform": "Android",
                "User-Agent": "okhttp/4.12.0",
            },
            cookies=self.session.cookies,
        )
        response.raise_for_status()
        if not response.json():
            raise RuntimeError("No vehicles found for the authenticated user.")
        return response.json()[0]["vehicleId"]

    def get_badges(
        self,
        type: str = "daily",
        endDate: str = datetime.today().strftime("%Y-%m-%d"),
        startDate: str = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d"),
    ):
        """Query the badges endpoint and return the JSON response."""
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated. Call authenticate() first."
            )
        if type not in ["monthly", "daily"]:
            raise ValueError("type must be either 'monthly' or 'daily'")
        if datetime.strptime(startDate, "%Y-%m-%d") > datetime.strptime(
            endDate, "%Y-%m-%d"
        ):
            raise ValueError("startDate must be before endDate")

        vehicleId = self.get_vehicleId()

        url = f"{self.base_url}/ipaid/api/v2/vehicles/{vehicleId}/badges?endDate={endDate}&startDate={startDate}&type={type}"
        response = self.session.get(
            url,
            headers={
                "Accept-Encoding": "gzip",
                "Accept-Language": "en-US",
                "Connection": "Keep-Alive",
                "Platform": "Android",
                "User-Agent": "okhttp/4.12.0",
            },
            cookies=self.session.cookies,
        )
        response.raise_for_status()
        return response.json()

    def get_scores(
        self,
        endDate: str = datetime.today().strftime("%Y-%m-%d"),
        startDate: str = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d"),
    ):
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated. Call authenticate() first."
            )
        if datetime.strptime(startDate, "%Y-%m-%d") > datetime.strptime(
            endDate, "%Y-%m-%d"
        ):
            raise ValueError("startDate must be before endDate")

        vehicleId = self.get_vehicleId()

        url = f"{self.base_url}/ipaid/api/v2/vehicles/{vehicleId}/scores?endDate={endDate}&startDate={startDate}"
        response = self.session.get(
            url,
            headers={
                "Accept-Encoding": "gzip",
                "Accept-Language": "en-US",
                "Connection": "Keep-Alive",
                "Platform": "Android",
                "User-Agent": "okhttp/4.12.0",
            },
            cookies=self.session.cookies,
        )
        response.raise_for_status()
        return response.json()

    def get_trip_details(self, tripId: str | None, photon: PhotonClient | None):
        """Query the trip details endpoint and return the JSON response."""
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated. Call authenticate() first."
            )
        if not tripId:
            tripId = self.get_trips(amount=1)[0]["trip"]["tripId"]

        vehicleId = self.get_vehicleId()
        url = f"{self.base_url}/ipaid/api/v2/vehicles/{vehicleId}/trips/{tripId}?expand=events&expand=points&expand=scores&expand=user&expand=vehicle&expand=alerts"
        response = self.session.get(
            url,
            headers={
                "Accept-Encoding": "gzip",
                "Accept-Language": "en-US",
                "Connection": "Keep-Alive",
                "Platform": "Android",
                "User-Agent": "okhttp/4.12.0",
            },
            cookies=self.session.cookies,
        )
        response.raise_for_status()
        resp = response.json()
        if photon:
            polyline_points = resp.get("geometry")
            if polyline_points:
                decoded_points = polyline.decode(polyline_points, 6)
                resp["decoded_geometry"] = decoded_points
        return resp
