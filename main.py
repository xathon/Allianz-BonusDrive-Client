import argparse
import json
from client import APIClient
from constants import BASE_URL
from dotenv import load_dotenv
import os
from colorama import init

from print import print_trip_details, print_badge

# Load environment variables from .env file
load_dotenv()

# Colorama
init(autoreset=True)

parser = argparse.ArgumentParser(
    prog="Allianz BonusDrive Client",
    description="API Client for Allianz BonusDrive"
)
parser.add_argument("action",choices=["last-trip","badges-daily","badges-monthly","scores","details","trips"], help="Action to perform")
parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")

TGT = os.getenv("TGT") # TODO check how long the TGT is valid

if not TGT:
    EMAIL = input("Enter your email: ")
    PASSWORD = input("Enter your password: ")
else:
    EMAIL = ""
    PASSWORD = ""

if __name__ == "__main__":
    client = APIClient(BASE_URL, EMAIL, PASSWORD, TGT)

    # Authenticate the client
    client.authenticate()

    args = parser.parse_args()
    match args.action:
        case "last-trip":
            trip = client.get_trips(amount=1)[0]
            print_trip_details(trip["trip"]) if not args.verbose else print(json.dumps(trip, indent=4))
        case "trips":
            trips = client.get_trips(amount=8)
            for trip in trips:
                print_trip_details(trip["trip"]) if not args.verbose else print(json.dumps(trip, indent=4))
                print("-" * 20)
        case "badges-daily":
            badges = client.get_badges(type="daily")
            for badge in badges:
                print_badge(badge) if not args.verbose else print(json.dumps(badges, indent=4))
                print("-" * 20)
        case "badges-monthly":
            badges = client.get_badges(type="monthly")
            for badge in badges:
                print_badge(badge) if not args.verbose else print(json.dumps(badges, indent=4))
                print("-" * 20)
        case "scores": # this is probably not useful since the scores are already included in trips, but hey, the API endpoint exists, so why not
            scores = client.get_scores()
            print(json.dumps(scores , indent=4))
        case "details":
            trip = client.get_trip_details(tripId=None) # Pass None to get the latest trip, TODO make parameter for tripId
            print(trip)
        case _:
            print("Unknown action")