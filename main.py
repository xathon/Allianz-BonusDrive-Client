from client import APIClient
from constants import BASE_URL
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

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

    trips = client.get_trips()
    print(trips)