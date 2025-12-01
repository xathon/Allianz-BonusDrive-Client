import pytest
from unittest.mock import patch, MagicMock
from allianz_bonusdrive_client.client import BonusdriveAPIClient


@pytest.fixture
def mock_session():
    with patch("requests.Session") as MockSession:
        yield MockSession.return_value

@pytest.fixture
def api_client(mock_session):
    return BonusdriveAPIClient(
        base_url="https://example.com",
        email="test@example.com",
        password="password123",
    )

def test_request_tgt_returns_tgt(api_client, mock_session):
    mock_session.post.return_value.status_code = 201
    mock_session.post.return_value.text = "mock_tgt_token"

    result = api_client.request_tgt()

    assert result == "mock_tgt_token"
    assert api_client.tgt == "mock_tgt_token"

def test_request_tgt_without_credentials():
    client = BonusdriveAPIClient(
        base_url="https://example.com",
        email=None,
        password=None,
    )
    
    with pytest.raises(ValueError, match="Please provide your username and password"):
        client.request_tgt()

def test_authenticate_success(api_client, mock_session):
    # First post returns 201 for TGT, second post returns 200 for Service Ticket
    tgt_response = MagicMock()
    tgt_response.status_code = 201
    tgt_response.text = "mock_tgt"
    
    st_response = MagicMock()
    st_response.status_code = 200
    st_response.text = "mock_st"
    st_response.cookies = {}
    
    cookies_response = MagicMock()
    cookies_response.status_code = 200
    cookies_response.cookies = {}
    
    mock_session.post.side_effect = [tgt_response, st_response, cookies_response]
    mock_session.get.return_value.status_code = 200
    mock_session.get.return_value.json.return_value = {"userId": 12345}

    api_client.authenticate()

    assert api_client.authenticated is True
    assert api_client.tgt == "mock_tgt"
    assert api_client.userId == 12345

def test_authenticate_failure(api_client, mock_session):
    mock_session.post.return_value.status_code = 401

    with pytest.raises(RuntimeError):
        api_client.authenticate()

def test_get_trips(api_client, mock_session):
    api_client.authenticated = True
    api_client.userId = 12345
    mock_session.get.return_value.status_code = 200
    mock_session.get.return_value.json.return_value = {"items": [{
        "trip": {
            "tripId": "trip1",
            "vehicle": {
                "vehicleId": "v1",
                "make": "TestMake",
                "model": "TestModel"
            },
            "user": {
                "userId": "u1",
                "publicDisplayName": "Test User",
                "firstName": "Test",
                "lastName": "User"
            },
            "tripScores": {
                "scores": {
                    "over.speeding": 100,
                    "speeding": 100,
                    "distracted.driving": 100,
                    "payd": 100,
                    "overall": 100,
                    "harsh.cornering": 100,
                    "harsh.acceleration": 100,
                    "harsh.braking": 100,
                    "mileage": 100
                },
                "scoreType": "daily"
            },
            "tripStartTimestampUtc": "2023-01-01T00:00:00Z",
            "tripEndTimestampUtc": "2023-01-01T01:00:00Z",
            "tripStartTimestampLocal": "2023-01-01T01:00:00",
            "tripEndTimestampLocal": "2023-01-01T02:00:00",
            "tripProcessingEndTimestampUtc": "2023-01-01T01:05:00Z",
            "kilometers": 50.0,
            "avgKilometersPerHour": 50.0,
            "maxKilometersPerHour": 100.0,
            "seconds": 3600,
            "secondsOfIdling": 60,
            "timeZoneOffsetMillis": 3600000,
            "tripStatus": "COMPLETED",
            "transportMode": "CAR",
            "transportModeMessageKey": "car",
            "geometry": "",
            "reconstructedStartGeometry": "",
            "tripStartStatus": "STARTED",
            "verified": True,
            "hasAlerts": False,
            "tripScore": 100,
            "eventsCount": 0,
            "private": False,
            "tripUUID": "uuid123",
            "purpose": "COMMUTE"
        }
    }]}

    trips = api_client.get_trips()

    assert len(trips) == 1
    assert trips[0].tripId == "trip1"

def test_get_trips_not_authenticated(api_client):
    api_client.authenticated = False

    with pytest.raises(RuntimeError, match="Client is not authenticated"):
        api_client.get_trips()

def test_get_vehicleId(api_client, mock_session):
    api_client.authenticated = True
    api_client.userId = 12345
    mock_session.get.return_value.status_code = 200
    mock_session.get.return_value.json.return_value = [{"vehicleId": "vehicle123"}]

    vehicle_id = api_client.get_vehicleId()

    assert vehicle_id == "vehicle123"

def test_get_badges(api_client, mock_session):
    
    api_client.authenticated = True
    api_client.userId = 12345
    with patch.object(api_client, "get_vehicleId", return_value="vehicle123"):

        mock_session.get.return_value.status_code = 200
        mock_session.get.return_value.json.return_value = []

        badges = api_client.get_badges()

        assert badges == []

def test_get_badges_invalid_type(api_client):
    api_client.authenticated = True

    with pytest.raises(ValueError, match="type must be either 'monthly' or 'daily'"):
        api_client.get_badges(type="invalid")

def test_get_scores(api_client, mock_session):
    api_client.authenticated = True
    api_client.userId = 12345
    with patch.object(api_client, "get_vehicleId", return_value="vehicle123"):
        mock_session.get.return_value.status_code = 200
        mock_session.get.return_value.json.return_value = []

        scores = api_client.get_scores()

        assert scores == []

def test_get_scores_invalid_dates(api_client):
    api_client.authenticated = True

    with pytest.raises(ValueError, match="startDate must be before endDate"):
        api_client.get_scores(startDate="2023-10-10", endDate="2023-10-09")

def test_get_trip_details(api_client, mock_session):
    api_client.authenticated = True
    api_client.userId = 12345
    with patch.object(api_client, "get_vehicleId", return_value="vehicle123"):
        mock_session.get.return_value.status_code = 200
        mock_session.get.return_value.json.return_value = {
            "tripId": "trip123",
            "vehicle": {
                "vehicleId": "v1",
                "make": "TestMake",
                "model": "TestModel"
            },
            "user": {
                "userId": "u1",
                "publicDisplayName": "Test User",
                "firstName": "Test",
                "lastName": "User"
            },
            "tripScores": {
                "scores": {
                    "over.speeding": 100,
                    "speeding": 100,
                    "distracted.driving": 100,
                    "payd": 100,
                    "overall": 100,
                    "harsh.cornering": 100,
                    "harsh.acceleration": 100,
                    "harsh.braking": 100,
                    "mileage": 100
                },
                "scoreType": "daily"
            },
            "tripStartTimestampUtc": "2023-01-01T00:00:00Z",
            "tripEndTimestampUtc": "2023-01-01T01:00:00Z",
            "tripStartTimestampLocal": "2023-01-01T01:00:00",
            "tripEndTimestampLocal": "2023-01-01T02:00:00",
            "tripProcessingEndTimestampUtc": "2023-01-01T01:05:00Z",
            "kilometers": 50.0,
            "avgKilometersPerHour": 50.0,
            "maxKilometersPerHour": 100.0,
            "seconds": 3600,
            "secondsOfIdling": 60,
            "timeZoneOffsetMillis": 3600000,
            "tripStatus": "COMPLETED",
            "transportMode": "CAR",
            "transportModeMessageKey": "car",
            "geometry": "",
            "reconstructedStartGeometry": "",
            "tripStartStatus": "STARTED",
            "verified": True,
            "hasAlerts": False,
            "tripScore": 100,
            "eventsCount": 0,
            "private": False,
            "tripUUID": "uuid123",
            "purpose": "COMMUTE"
        }

        trip_details = api_client.get_trip_details(tripId="trip123")

        assert trip_details.tripId == "trip123"