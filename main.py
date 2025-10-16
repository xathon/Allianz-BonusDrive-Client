import argparse
from client import APIClient
from constants import BASE_URL
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

parser = argparse.ArgumentParser(
    prog="Allianz BonusDrive Client",
    description="API Client for Allianz BonusDrive"
)
parser.add_argument("action",choices=["last-trip","badges","scores","details"], help="Action to perform")

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
            print(trip)
        case "badges":
            badges = client.get_badges()
            print(badges)
        case "scores":
            scores = client.get_scores()
            print(scores)
        case "details":
            trip = client.get_trip_details(tripId=None) # Pass None to get the latest trip, TODO make parameter for tripId
            print(trip)
        case _:
            print("Unknown action")