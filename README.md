# Allianz BonusDrive Client

API Client to query your BonusDrive data. 

BonusDrive is a vehicle telematics application used by Allianz Germany to track driving behavior and routes. The code probably works similarily for every customer of IMS Driving Change (such as ADAC, Zurich, Aviva, etc., ), but you'll have to find that out for yourself.

The project is still in development.

## Features

- **Authentication:** Log in with your credentials.
- **Latest Trip Query:** Retrieve information about your most recent trip.
- **Badges:** Get your recent badges, either daily or monthly
- **Scores:** Get more detailed scores per trip (overall and subscores)
- **Trip details:** All the info you can get about your latest trip, including scores, map geometry, distance, speed, ...
- **Photon lookup:** Specify the URL to a Photon database to get a lookup on your start and end address
- ... more soonTM, probably

## Getting Started
You can use this either as a stand-alone cli client or as a library for use in other programs.

### Library
Either get the latest from git:
```
pip install git+https://github.com/xathon/Allianz-Bonusdrive-Client.git
```
Or use PyPI:
```
pip install allianz-bonusdrive-client
```

As a library, you can just do:
```python
from allianz_bonusdrive_client import BonusdriveAPIClient
base_url = "https://example.com"  # Replace with the actual base URL
email = "user@example.com"        # Replace with the user's email
password = "securepassword"       # Replace with the user's password. Optional if TGT is provided.
tgt = None                        # Optional: Provide a TGT if available

# Create an instance of the client
client = BonusdriveAPIClient(base_url, email, password, tgt)

# Authenticate the client
client.authenticate()

# do whatever you want
```

### CLI
From PyPI:
```
pip install allianz-bonusdrive-client[cli]
```

Then you can run the client:
```
$ python3 -m allianz_bonusdrive_client.cli -h
usage: Allianz BonusDrive Client [-h] [--geo-lookup] [--raw] [-v] {last-trip,badges-daily,badges-monthly,scores,details,trips}
```
On first start, the client should ask you for your BonusDrive email (use the one you tracked the trips with, that's not necessarily the same as the car owner's account!) and password. It then requests a TGT and stores it in .env, it will be used in the future. Alternatively, provide a TGT by setting the environment variable.

## Disclaimers
- This project pretends to be the BonusDrive app, using HTTP headers. This a) may break at any point and b) is very much not intended behavior and might be against ToS, no idea. Try to keep your API requests low. I'm not responsible if anything happens to your account, insurance contract, Club Penguin membership, yada yada.
- I haven't yet found out how long a TGT is valid, or if it expires at any point. STs are invalidated after each use (successful or not), good job!
- LLMs have been involved in creating and debugging this program. I *mostly* know what I'm doing, so that should be fine? See above for my responsibilities.
- This program, unfortunately, is written in Python. The only reason for this is because I want to integrate it into Home Assistant/HACS at some point. Once this is complete. Probably. (Update: [done!](https://github.com/xathon/Allianz-BonusDrive-HomeAssistant))

## License

This project is licensed under the MIT License.
