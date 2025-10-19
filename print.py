# TODO maybe implement i18n

from colorama import Back
from datetime import datetime, timedelta

def print_trip_details(trip):
    print(f"Trip ID:             {trip.get('tripId')}")
    print(f"Startzeit:           {datetime.fromtimestamp(trip.get('tripStartTimestampLocal')/1000).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Endzeit:             {datetime.fromtimestamp(trip.get('tripEndTimestampLocal')/1000).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Distanz (km):        {trip.get('kilometers'):.2f}")
    print(f"Durchschnitt (km/h): {trip.get('avgKilometersPerHour'):.2f}")
    print(f"Fahrzeit:            {str(timedelta(seconds=trip.get('seconds')))}")
    print(f"Standzeit:           {str(timedelta(seconds=trip.get('secondsOfIdling')))}")
    print("Scores:")
    print_scores(trip)



def print_scores(scores):
    overall = scores.get("tripScores").get("scores").get("overall") if scores.get("tripScores") else scores.get("scores").get("overall")
    speeding = scores.get("tripScores").get("scores").get("speeding") if scores.get("tripScores") else scores.get("scores").get("speeding")
    braking = scores.get("tripScores").get("scores").get("harsh.braking") if scores.get("tripScores") else scores.get("scores").get("harsh.braking")
    acceleration = scores.get("tripScores").get("scores").get("harsh.acceleration") if scores.get("tripScores") else scores.get("scores").get("harsh.acceleration")
    cornering = scores.get("tripScores").get("scores").get("harsh.cornering") if scores.get("tripScores") else scores.get("scores").get("harsh.cornering")
    payd = scores.get("tripScores").get("scores").get("payd") if scores.get("tripScores") else scores.get("scores").get("payd")

    print(f"Gesamtscore:           {score_color(overall)}{overall}{Back.RESET}")
    print(f"Bremsverhalten:        {score_color(braking)}{braking}{Back.RESET}")
    print(f"Beschleunigung:        {score_color(acceleration)}{acceleration}{Back.RESET}")
    print(f"Kurvenfahrverhalten:   {score_color(cornering)}{cornering}{Back.RESET}")
    print(f"Geschwindigkeit:       {score_color(speeding)}{speeding}{Back.RESET}")
    print(f"Tag, Zeit, Straßenart: {score_color(payd)}{payd}{Back.RESET}")

def print_badge(badge):
    match badge.get("badgeType"):
        case "MONTH":
            print(f"{datetime.fromtimestamp(badge.get('date')/1000).strftime('%B %Y')}: {badge_color(badge)}")
        case "DAY":
            print(f"{datetime.fromtimestamp(badge.get('date')/1000).strftime('%Y-%m-%d')}: {badge_color(badge)}")


def score_color(score):
    thresholds = [
        (90, Back.YELLOW),
        (80, Back.LIGHTWHITE_EX),
        (70, Back.LIGHTRED_EX),
        (50, Back.LIGHTBLUE_EX),
        (0, Back.RED),
    ]
    return next(color for threshold, color in thresholds if score >= threshold)

def badge_color(badge):
    match badge.get("level"):
        case 1:
            return f"{Back.YELLOW}GOLD{Back.RESET}"
        case 2:
            return f"{Back.LIGHTWHITE_EX}SILBER{Back.RESET}"
        case 3:
            return f"{Back.LIGHTRED_EX}BRONZE{Back.RESET}"
        case 5:
            return f"{Back.RED}ROT{Back.RESET}"
        case _:
            return f"{Back.BLUE}BLAU{Back.RESET}"