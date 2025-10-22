import pytest
from unittest.mock import patch
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

def test_authenticate_success(api_client, mock_session):
    mock_session.post.return_value.status_code = 200
    mock_session.post.return_value.text = "mock_tgt"
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
    mock_session.get.return_value.json.return_value = {"items": [{"trip": "trip1"}]}

    trips = api_client.get_trips()

    assert trips == [{"trip": "trip1"}]

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
        mock_session.get.return_value.json.return_value = {"badges": []}

        badges = api_client.get_badges()

        assert badges == {"badges": []}

def test_get_badges_invalid_type(api_client):
    api_client.authenticated = True

    with pytest.raises(ValueError, match="type must be either 'monthly' or 'daily'"):
        api_client.get_badges(type="invalid")

def test_get_scores(api_client, mock_session):
    api_client.authenticated = True
    api_client.userId = 12345
    with patch.object(api_client, "get_vehicleId", return_value="vehicle123"):
        mock_session.get.return_value.status_code = 200
        mock_session.get.return_value.json.return_value = {"scores": []}

        scores = api_client.get_scores()

        assert scores == {"scores": []}

def test_get_scores_invalid_dates(api_client):
    api_client.authenticated = True

    with pytest.raises(ValueError, match="startDate must be before endDate"):
        api_client.get_scores(startDate="2023-10-10", endDate="2023-10-09")

def test_get_trip_details(api_client, mock_session):
    api_client.authenticated = True
    api_client.userId = 12345
    with patch.object(api_client, "get_vehicleId", return_value="vehicle123"):
        mock_session.get.return_value.status_code = 200
        mock_session.get.return_value.json.return_value = {"trip": "details"}

        trip_details = api_client.get_trip_details(tripId="trip123", photon=None)

        assert trip_details == {"trip": "details"}