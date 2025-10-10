import requests
import logging
from urllib.parse import urlencode
from requests.cookies import RequestsCookieJar

# logging.basicConfig(level=print)


class APIClient:
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
        print(f"headers: {self.headers.items()}")
        if not self.tgt:
            # Step 1: Get TGT
            tgt_response = self.session.post(
                f"{self.base_url}/cas/rest/v1/rbtickets",
                data=urlencode({"username": self.username, "password": self.password}),
                headers=self.headers,
            )
            tgt_response.raise_for_status()
            self.tgt = tgt_response.text.strip()

        # Step 2: Use TGT to get Service Ticket (ST)
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
        service_ticket = st_response.text.strip()
        print(f"Cookies in TGT request: {st_response.cookies.get_dict()}")
        self.session.cookies.update(st_response.cookies)
        self.headers.pop("Content-Type", None)
        print(f"Service Ticket: {service_ticket}")

        # Step 3: Use ST to set cookies
        cookies_response = self.session.post(
            f"{self.base_url}/ipaid/",
            data={"ticket": service_ticket},
            headers=self.headers,
            cookies=self.session.cookies,  # Use cookies from the cookiejar
            allow_redirects=False,  # Follow the redirect to capture the cookie
        )
        print(cookies_response.cookies.get_dict())
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
        return response.json()["items"][0]
