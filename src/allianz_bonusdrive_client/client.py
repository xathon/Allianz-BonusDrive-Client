import requests
from urllib.parse import urlencode
from requests.cookies import RequestsCookieJar
from datetime import datetime, timedelta
import polyline

from .utils.photon import PhotonClient
from .utils.dataclasses import (
    Trip,
    Vehicle,
    User,
    TripScores,
    Scores,
    Badge,
    BadgeLevel,
)

# logging.basicConfig(level=print)


class BonusdriveAPIClient:
    def __init__(
        self,
        base_url: str,
        email: str | None,
        password: str | None,
        tgt: str | None = None,
        photon_url: str | None = None,
    ):
        self.base_url = base_url
        self.username = email
        self.password = password
        self.tgt = tgt
        self.photon = PhotonClient(photon_url) if photon_url else None
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

    def request_tgt(self) -> str:
        """Request a new TGT using the provided username and password.
        
        Returns:
            str: The TGT token string.
        """
        if not self.username or not self.password:
            raise ValueError(
                "Please provide your username and password to request a TGT"
            )
        try:
            tgt_response = self.session.post(
                f"{self.base_url}/cas/rest/v1/rbtickets",
                data=urlencode(
                    {
                        "username": self.username,
                        "password": self.password,
                        "rememberMe": "true",
                    }
                ),
                headers=self.headers,
            )
            tgt_response.raise_for_status()
            if tgt_response.status_code != 201:
                raise RuntimeError("Failed to obtain TGT")
            self.tgt = tgt_response.text.strip()
            return self.tgt
        except requests.RequestException as e:
            raise RuntimeError("Failed to obtain TGT") from e

    def _handle_response(self, response, retry_func, *args, **kwargs):
        """Handle response and re-authenticate on 401 errors.
        
        Args:
            response: The HTTP response object.
            retry_func: The function to retry after re-authentication.
            *args: Positional arguments to pass to retry_func.
            **kwargs: Keyword arguments to pass to retry_func.
            
        Returns:
            A tuple (should_return, result) where should_return is True if the
            caller should return result immediately (due to retry).
        """
        if response.status_code == 401:
            self.authenticated = False
            self.authenticate()
            return (True, retry_func(*args, **kwargs))
        return (False, response)

    def authenticate(self):
        """Authenticate the user and store session cookies."""
        if not self.tgt:
            self.request_tgt()

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
            if st_response.status_code == 404:
                # TGT is invalid, re-authenticate and retry
                self.tgt = None
                self.authenticate()
                return
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

    def get_trips_raw(self, amount: int = 10, offset: int = 0) -> list[dict]:
        """Query the trips endpoint and return the raw JSON response."""
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated. Call authenticate() first."
            )

        url = f"{self.base_url}/ipaid/api/v2/users/{self.userId}/logbook/trips?offset={offset}&limit={amount}&sort=local_startdate%3Bdesc&expand=vehicle&expand=user&expand=events&expand=points&expand=scores&expand=alerts"
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
        retried, result = self._handle_response(response, self.get_trips_raw, amount, offset)
        if retried:
            return result
        response = result
        response.raise_for_status()
        trips_data = response.json()["items"]
        return trips_data

    def get_trips(self, amount: int = 10, offset: int = 0) -> list[Trip]:
        trips_data = [item["trip"] for item in self.get_trips_raw(amount, offset)]

        trips = []
        for trip_data in trips_data:
            vehicle_data = trip_data["vehicle"]
            user_data = trip_data["user"]
            trip_scores_data = trip_data["tripScores"]

            vehicle = Vehicle(
                vehicleId=vehicle_data["vehicleId"],
                make=vehicle_data["make"],
                model=vehicle_data["model"],
                nickname=vehicle_data.get("nickname"),
                year=vehicle_data.get("year"),
                plate=vehicle_data.get("plate"),
                avatar=vehicle_data.get("avatar"),
                accountId=vehicle_data.get("accountId"),
                accountNumber=vehicle_data.get("accountNumber"),
                policyInceptionDate=vehicle_data.get("policyInceptionDate"),
                policyStartDate=vehicle_data.get("policyStartDate"),
                extraAccountId=vehicle_data.get("extraAccountId"),
                extraAccountNumber=vehicle_data.get("extraAccountNumber"),
            )

            user = User(
                userId=user_data["userId"],
                publicDisplayName=user_data["publicDisplayName"],
                avatar=user_data.get("avatar"),
                sharedInformation=user_data.get("sharedInformation"),
                associatedUsers=user_data.get("associatedUsers"),
                account=user_data.get("account"),
                userRole=user_data.get("userRole"),
                accountRole=user_data.get("accountRole"),
                firstName=user_data["firstName"],
                lastName=user_data["lastName"],
            )

            scores_data = trip_scores_data["scores"]
            scores = Scores(
                over_speeding=scores_data["over.speeding"],
                speeding=scores_data["speeding"],
                distracted_driving=scores_data["distracted.driving"],
                payd=scores_data["payd"],
                overall=scores_data["overall"],
                harsh_cornering=scores_data["harsh.cornering"],
                harsh_acceleration=scores_data["harsh.acceleration"],
                harsh_braking=scores_data["harsh.braking"],
                mileage=scores_data["mileage"],
            )

            trip_scores = TripScores(
                scores=scores,
                scoreType=trip_scores_data["scoreType"],
            )

            trip = Trip(
                events=trip_data.get("events"),
                tripId=trip_data["tripId"],
                tripStartTimestampUtc=trip_data["tripStartTimestampUtc"],
                tripEndTimestampUtc=trip_data["tripEndTimestampUtc"],
                tripStartTimestampLocal=trip_data["tripStartTimestampLocal"],
                tripEndTimestampLocal=trip_data["tripEndTimestampLocal"],
                tripProcessingEndTimestampUtc=trip_data[
                    "tripProcessingEndTimestampUtc"
                ],
                kilometers=trip_data["kilometers"],
                avgKilometersPerHour=trip_data["avgKilometersPerHour"],
                maxKilometersPerHour=trip_data["maxKilometersPerHour"],
                seconds=trip_data["seconds"],
                secondsOfIdling=trip_data["secondsOfIdling"],
                timeZoneOffsetMillis=trip_data["timeZoneOffsetMillis"],
                tripStatus=trip_data["tripStatus"],
                pois=trip_data.get("pois"),
                transportMode=trip_data["transportMode"],
                transportModeMessageKey=trip_data["transportModeMessageKey"],
                transportModeReason=trip_data.get("transportModeReason"),
                geometry=trip_data["geometry"],
                snappedGeometry=trip_data.get("snappedGeometry", []),
                reconstructedStartGeometry=trip_data["reconstructedStartGeometry"],
                tripStartStatus=trip_data["tripStartStatus"],
                verified=trip_data["verified"],
                hasAlerts=trip_data["hasAlerts"],
                alerts=trip_data.get("alerts"),
                vehicle=vehicle,
                user=user,
                device=trip_data.get("device"),
                tripScores=trip_scores,
                milStatus=trip_data.get("milStatus"),
                dtcCount=trip_data.get("dtcCount"),
                tripScore=trip_data["tripScore"],
                eventsCount=trip_data["eventsCount"],
                private=trip_data["private"],
                tripUUID=trip_data["tripUUID"],
                purpose=trip_data["purpose"],
                decoded_geometry=None,
                start_point_string=None,
                end_point_string=None,
            )
            trips.append(trip)

        return trips

    def get_vehicleId(self) -> str:
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
        retried, result = self._handle_response(response, self.get_vehicleId)
        if retried:
            return result
        response = result
        response.raise_for_status()
        if not response.json():
            raise RuntimeError("No vehicles found for the authenticated user.")
        return response.json()[0]["vehicleId"]


    def get_badges_raw(
        self,
        type: str = "daily",
        endDate: str = datetime.today().strftime("%Y-%m-%d"),
        startDate: str = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d"),
    ) -> list[dict]:
        """Query the badges endpoint and return the raw JSON response."""
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
        retried, result = self._handle_response(response, self.get_badges_raw, type, endDate, startDate)
        if retried:
            return result
        response = result
        response.raise_for_status()
        badges_data = response.json()
        return badges_data

    def get_badges(
        self,
        type: str = "daily",
        endDate: str = datetime.today().strftime("%Y-%m-%d"),
        startDate: str = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d"),
    ) -> list[Badge]:
        """Query the badges endpoint and return a list of Badge dataclass instances."""
        
        badges_data = self.get_badges_raw(type, endDate, startDate)

        badges = []
        for badge_data in badges_data:
            used_badge_levels_data = badge_data.get("usedBadgeLevels", [])
            used_badge_levels = [
                BadgeLevel(
                    level=level_data["level"],
                    minimumValue=level_data["minimumValue"],
                    maximumValue=level_data["maximumValue"],
                )
                for level_data in used_badge_levels_data
            ]

            badge = Badge(
                badgeType=badge_data["badgeType"],
                level=badge_data["level"],
                pointsAwarded=badge_data["pointsAwarded"],
                date=badge_data["date"],
                state=badge_data["state"],
                usedBadgeLevels=used_badge_levels,
            )
            badges.append(badge)

        return badges

    def get_scores_raw(
        self,
        endDate: str = datetime.today().strftime("%Y-%m-%d"),
        startDate: str = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d"),
    ) -> list[dict]:
        """Query the scores endpoint and return the raw JSON response."""
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
        retried, result = self._handle_response(response, self.get_scores_raw, endDate, startDate)
        if retried:
            return result
        response = result
        response.raise_for_status()
        # TODO this may return 204 if no scores are available in the given date range
        scores = response.json() if response.status_code != 204 else []
        return scores

    def get_scores(
        self,
        endDate: str = datetime.today().strftime("%Y-%m-%d"),
        startDate: str = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d"),
    ) -> dict[(str, Scores)] | dict | list:
        
        scores = self.get_scores_raw(endDate, startDate)
        if scores == []:
            return scores
        returned_scores = {}
        for score in scores:

            returned_scores[score.get("date")] = Scores(
                overall=score.get("score", 0.0),
                over_speeding=score.get("componentScores")
                .get("over.speeding") # pyright: ignore[reportOptionalMemberAccess]
                .get("score", 0.0),
                harsh_braking=score.get("componentScores")
                .get("harsh.braking") # pyright: ignore[reportOptionalMemberAccess]
                .get("score", 0.0),
                harsh_acceleration=score.get("componentScores")
                .get("harsh.acceleration") # pyright: ignore[reportOptionalMemberAccess]
                .get("score", 0.0),
                harsh_cornering=score.get("componentScores")
                .get("harsh.cornering") # pyright: ignore[reportOptionalMemberAccess]
                .get("score", 0.0),
                payd=score.get("componentScores").get("payd").get("score", 0.0), # pyright: ignore[reportOptionalMemberAccess]
                speeding=score.get("componentScores").get("speeding").get("score", 0.0), # pyright: ignore[reportOptionalMemberAccess]
                distracted_driving=score.get("componentScores")
                .get("distracted.driving") # pyright: ignore[reportOptionalMemberAccess]
                .get("score", 0.0),
                mileage=score.get("componentScores").get("mileage").get("score", 0.0), # pyright: ignore[reportOptionalMemberAccess]
            )
        return returned_scores

    def get_trip_details(self, tripId: str | None) -> Trip:
        """Query the trip details endpoint and return the JSON response."""
        if not self.authenticated:
            raise RuntimeError(
                "Client is not authenticated. Call authenticate() first."
            )
        if not tripId:
            tripId = self.get_trips(amount=1)[0].tripId

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
        retried, result = self._handle_response(response, self.get_trip_details, tripId)
        if retried:
            return result
        response = result
        response.raise_for_status()
        if response.status_code != 200:
            raise RuntimeError("Failed to obtain trip details")
        trip_data = response.json()
        
        polyline_points = trip_data.get("geometry")
        if polyline_points:
            decoded_points = polyline.decode(polyline_points, 6)
            trip_data["decoded_geometry"] = decoded_points
            if decoded_points:
                start_point_coordinates = decoded_points[0]
                start_name = ""
                end_point_coordinates = decoded_points[-1]
                end_name = ""
                if self.photon:
                    try:
                        start_geo = self.photon.reverse_geocode(
                            start_point_coordinates[0], start_point_coordinates[1]
                        )
                    except Exception:
                        start_geo = None
                    # in Rust this would have been a single question mark. :(
                    if isinstance(start_geo, dict):
                        features = start_geo.get("features") or []
                        if features and isinstance(features, list) and features[0]:
                            props = features[0].get("properties") or {}
                            start_name = props.get("name") or f"{props.get("street")} {props.get("housenumber") or ""}" or ""
                            start_city = props.get("city") or ""
                            start_country = props.get("country") or ""
                    start_point_string = ""
                    if start_name != "":
                        start_point_string = f"{start_name}"
                    if start_city != "":
                        if start_point_string != "":
                            start_point_string += f", {start_city}"
                        else:
                            start_point_string = f"{start_city}"
                    if start_country != "":
                        if start_point_string != "":
                            start_point_string += f", {start_country}"
                        else:
                            start_point_string = f"{start_country}"
                    trip_data["start_point_string"] = start_point_string
                    try:
                        end_geo = self.photon.reverse_geocode(
                            end_point_coordinates[0], end_point_coordinates[1]
                        )
                    except Exception:
                        end_geo = None
                    if isinstance(end_geo, dict):
                        features = end_geo.get("features") or []
                        if features and isinstance(features, list) and features[0]:
                            props = features[0].get("properties") or {}
                            end_name = props.get("name") or f"{props.get("street")} {props.get("housenumber") or ""}" or ""
                            end_city = props.get("city")
                            end_country = props.get("country")
                    trip_data["end_point_string"] = (
                        f"{end_name}, {end_city}, {end_country}"
                    )
                else:
                    lat, lon = start_point_coordinates
                    trip_data["start_point_string"] = f"{'N' if lat >= 0 else 'S'}{abs(lat):.6f}, {'E' if lon >= 0 else 'W'}{abs(lon):.6f}"

                    lat_e, lon_e = end_point_coordinates
                    trip_data["end_point_string"] = f"{'N' if lat_e >= 0 else 'S'}{abs(lat_e):.6f}, {'E' if lon_e >= 0 else 'W'}{abs(lon_e):.6f}"

        vehicle_data = trip_data["vehicle"]
        user_data = trip_data["user"]
        trip_scores_data = trip_data["tripScores"]

        vehicle = Vehicle(
            vehicleId=vehicle_data["vehicleId"],
            make=vehicle_data["make"],
            model=vehicle_data["model"],
            nickname=vehicle_data.get("nickname"),
            year=vehicle_data.get("year"),
            plate=vehicle_data.get("plate"),
            avatar=vehicle_data.get("avatar"),
            accountId=vehicle_data.get("accountId"),
            accountNumber=vehicle_data.get("accountNumber"),
            policyInceptionDate=vehicle_data.get("policyInceptionDate"),
            policyStartDate=vehicle_data.get("policyStartDate"),
            extraAccountId=vehicle_data.get("extraAccountId"),
            extraAccountNumber=vehicle_data.get("extraAccountNumber"),
        )

        user = User(
            userId=user_data["userId"],
            publicDisplayName=user_data["publicDisplayName"],
            avatar=user_data.get("avatar"),
            sharedInformation=user_data.get("sharedInformation"),
            associatedUsers=user_data.get("associatedUsers"),
            account=user_data.get("account"),
            userRole=user_data.get("userRole"),
            accountRole=user_data.get("accountRole"),
            firstName=user_data["firstName"],
            lastName=user_data["lastName"],
        )

        scores_data = trip_scores_data["scores"]
        scores = Scores(
            over_speeding=scores_data["over.speeding"],
            speeding=scores_data["speeding"],
            distracted_driving=scores_data["distracted.driving"],
            payd=scores_data["payd"],
            overall=scores_data["overall"],
            harsh_cornering=scores_data["harsh.cornering"],
            harsh_acceleration=scores_data["harsh.acceleration"],
            harsh_braking=scores_data["harsh.braking"],
            mileage=scores_data["mileage"],
        )

        trip_scores = TripScores(
            scores=scores,
            scoreType=trip_scores_data["scoreType"],
        )

        trip = Trip(
            events=trip_data.get("events"),
            tripId=trip_data["tripId"],
            tripStartTimestampUtc=trip_data["tripStartTimestampUtc"],
            tripEndTimestampUtc=trip_data["tripEndTimestampUtc"],
            tripStartTimestampLocal=trip_data["tripStartTimestampLocal"],
            tripEndTimestampLocal=trip_data["tripEndTimestampLocal"],
            tripProcessingEndTimestampUtc=trip_data["tripProcessingEndTimestampUtc"],
            kilometers=trip_data["kilometers"],
            avgKilometersPerHour=trip_data["avgKilometersPerHour"],
            maxKilometersPerHour=trip_data["maxKilometersPerHour"],
            seconds=trip_data["seconds"],
            secondsOfIdling=trip_data["secondsOfIdling"],
            timeZoneOffsetMillis=trip_data["timeZoneOffsetMillis"],
            tripStatus=trip_data["tripStatus"],
            pois=trip_data.get("pois"),
            transportMode=trip_data["transportMode"],
            transportModeMessageKey=trip_data["transportModeMessageKey"],
            transportModeReason=trip_data.get("transportModeReason"),
            geometry=trip_data["geometry"],
            snappedGeometry=trip_data.get("snappedGeometry", []),
            reconstructedStartGeometry=trip_data["reconstructedStartGeometry"],
            tripStartStatus=trip_data["tripStartStatus"],
            verified=trip_data["verified"],
            hasAlerts=trip_data["hasAlerts"],
            alerts=trip_data.get("alerts"),
            vehicle=vehicle,
            user=user,
            device=trip_data.get("device"),
            tripScores=trip_scores,
            milStatus=trip_data.get("milStatus"),
            dtcCount=trip_data.get("dtcCount"),
            tripScore=trip_data["tripScore"],
            eventsCount=trip_data["eventsCount"],
            private=trip_data["private"],
            tripUUID=trip_data["tripUUID"],
            purpose=trip_data["purpose"],
            decoded_geometry=trip_data.get("decoded_geometry"),
            start_point_string=trip_data.get("start_point_string"),
            end_point_string=trip_data.get("end_point_string"),
        )
        return trip
