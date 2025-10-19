# Allianz BonusDrive Client

API Client to query your BonusDrive data. 

BonusDrive is a vehicle telematics application used by Allianz Germany to track driving behavior and routes. The code probably works similarily for every customer of IMS Driving Change (such as ADAC, Zurich, Aviva, etc., ), but you'll have to find that out for yourself.

The project is still in development. Currently authentication works, and you can query some data about your latest trip, but it just dumps some JSON onto your CLI.

## Features

- **Authentication:** Log in with your credentials.
- **Latest Trip Query:** Retrieve information about your most recent trip.
- **Badges:** Get your recent badges, either daily or monthly
- **Scores:** Get more detailed scores per trip (overall and subscores)
- **Trip details:** All the info you can get about your latest trip, including scores, map geometry, distance, speed, ...
- **Photon lookup:** Specify the URL to a Photon database in your .env file to get a lookup on your start and end address
- ... more soonTM, probably

## Getting Started
On first start, the client should ask you for your BonusDrive email (use the one you tracked the trips with, that's not necessarily the same as the car owner's account!) and password. It then requests a TGT and stores it in .env, it will be used in the future.

## Disclaimers
- This project pretends to be the BonusDrive app, using HTTP headers. This a) may break at any point and b) is very much not intended behavior and might be against ToS, no idea. Try to keep your API requests low. I'm not responsible if anything happens to your account, insurance contract, Club Penguin membership, yada yada.
- I haven't yet found out how long a TGT is valid, or if it expires at any point. STs are invalidated after each use (successful or not), good job!
- LLMs have been involved in creating and debugging this program. I *mostly* know what I'm doing, so that should be fine? See above for my responsibilities.
- This program, unfortunately, is written in Python. The only reason for this is because I want to integrate it into Home Assistant/HACS at some point. Once this is complete. Probably.

## License

This project is licensed under the MIT License.
