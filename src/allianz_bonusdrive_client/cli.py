import argparse
from datetime import datetime
import json
from dotenv import load_dotenv
import os
from colorama import init

from .client import BonusdriveAPIClient
from .utils.constants import BASE_URL
from .print import print_scores, print_trip_details, print_badge
from importlib.metadata import version
# Load environment variables from .env file
load_dotenv()

# Colorama
init(autoreset=True)

parser = argparse.ArgumentParser(
    prog="Allianz BonusDrive Client",
    description=f"API Client for Allianz BonusDrive, version {version('allianz-bonusdrive-client')}",
)
parser.add_argument("action",choices=["last-trip","badges-daily","badges-monthly","scores","details","trips"], help="Action to perform")
#parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
parser.add_argument("--geo-lookup", "-g", action="store_true", help="Enable geolocation lookup using Photon API (for last-trip and trips actions)")
parser.add_argument("--raw", "-r", action="store_true", help="Output raw JSON data")
parser.add_argument('-v', '--version', action='version', version=version('allianz-bonusdrive-client'))

TGT = os.getenv("TGT") # TODO check how long the TGT is valid
PHOTON_URL = os.getenv("PHOTON_URL")

if not TGT:
    EMAIL = input("Enter your email: ")
    PASSWORD = input("Enter your password: ")
else:
    EMAIL = ""
    PASSWORD = ""

if __name__ == "__main__":
    client = BonusdriveAPIClient(BASE_URL, EMAIL, PASSWORD, TGT, PHOTON_URL)

    # Authenticate the client
    client.authenticate()

    args = parser.parse_args()
    match args.action:
        case "last-trip":
            if args.raw:
                trip = client.get_trips_raw(amount=1)[0]["trip"]
                if args.geo_lookup:
                    trip = client.get_trip_details(tripId=trip["tripId"])
                print(json.dumps(trip, indent=4))
                exit(0)
            trip = client.get_trips(amount=1)[0]
            if args.geo_lookup:
                trip = client.get_trip_details(tripId=trip.tripId)
            print_trip_details(trip)
        case "trips":
            if args.raw:
                trips = client.get_trips_raw(amount=8)
                for trip in trips:
                    if args.geo_lookup:
                        trip = client.get_trip_details(tripId=trip["trip"]["tripId"])
                    print(json.dumps(trips, indent=4))
                    print("-" * 20)
                exit(0)
            trips = client.get_trips(amount=8)
            for trip in trips:
                if args.geo_lookup:
                    trip = client.get_trip_details(tripId=trip.tripId)
                print_trip_details(trip)
                print("-" * 20)
        case "badges-daily":
            if args.raw:
                badges = client.get_badges_raw(type="daily")
                print(json.dumps(badges, indent=4))
                exit(0)
            badges = client.get_badges(type="daily")
            for badge in badges:
                print_badge(badge)
                print("-" * 20)
        case "badges-monthly":
            if args.raw:
                badges = client.get_badges_raw(type="monthly")
                print(json.dumps(badges, indent=4))
                exit(0)
            badges = client.get_badges(type="monthly")
            for badge in badges:
                print_badge(badge)
                print("-" * 20)
        case "scores": # this is probably not useful since the scores are already included in trips, but hey, the API endpoint exists, so why not
            if args.raw:
                scores = client.get_scores_raw()
                print(json.dumps(scores, indent=4))
                exit(0)
            scores = client.get_scores()
            for score_date, scores in scores.items(): # pyright: ignore[reportAttributeAccessIssue]
                print(f"Datum: {datetime.fromtimestamp(int(score_date) / 1000).strftime('%Y-%m-%d')}")
                print_scores(scores)
        case "details":
            if args.raw:
                trip = client.get_trip_details(tripId=None) # Pass None to get the latest trip, TODO make parameter for tripId
                print(json.dumps(trip, indent=4))
                exit(0)
            trip = client.get_trip_details(tripId=None) # Pass None to get the latest trip, TODO make parameter for tripId
            print_trip_details(trip)
        case _:
            print("Unknown action")