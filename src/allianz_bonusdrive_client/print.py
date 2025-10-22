# TODO maybe implement i18n

from colorama import Back
from datetime import datetime, timedelta

from allianz_bonusdrive_client.utils.dataclasses import Trip, Scores, Badge

def print_trip_details(trip: Trip):
    print(f"Trip ID:             {trip.tripId}")
    print(f"Startzeit:           {datetime.fromtimestamp(trip.tripStartTimestampLocal / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
    if trip.start_point_string:
        print(f"Startort:            {trip.start_point_string}")
    print(f"Endzeit:             {datetime.fromtimestamp(trip.tripEndTimestampLocal / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
    if trip.end_point_string:
        print(f"Endort:              {trip.end_point_string}")
    print(f"Distanz (km):        {trip.kilometers:.2f}")
    print(f"Durchschnitt (km/h): {trip.avgKilometersPerHour:.2f}")
    print(f"Fahrzeit:            {str(timedelta(seconds=trip.seconds))}")
    print(f"Standzeit:           {str(timedelta(seconds=trip.secondsOfIdling))}")
    print("Scores:")
    print_scores(trip.tripScores.scores)

def print_scores(scores: Scores):
    print(f"Gesamtscore:           {score_color(scores.overall)}{scores.overall}{Back.RESET}")
    print(f"Bremsverhalten:        {score_color(scores.harsh_braking)}{scores.harsh_braking}{Back.RESET}")
    print(f"Beschleunigung:        {score_color(scores.harsh_acceleration)}{scores.harsh_acceleration}{Back.RESET}")
    print(f"Kurvenfahrverhalten:   {score_color(scores.harsh_cornering)}{scores.harsh_cornering}{Back.RESET}")
    print(f"Geschwindigkeit:       {score_color(scores.speeding)}{scores.speeding}{Back.RESET}")
    print(f"Tag, Zeit, Straßenart: {score_color(scores.payd)}{scores.payd}{Back.RESET}")

def print_badge(badge: Badge):
    match badge.badgeType:
        case "MONTH":
            print(f"{datetime.fromtimestamp(badge.date / 1000).strftime('%B %Y')}: {badge_color(badge)}")
        case "DAY":
            print(f"{datetime.fromtimestamp(badge.date / 1000).strftime('%Y-%m-%d')}: {badge_color(badge)}")

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
    match badge.level:
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