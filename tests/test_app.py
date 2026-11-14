from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


TEST_ACTIVITIES = {
    "Test Activity": {
        "description": "An activity for API tests",
        "schedule": "Mondays",
        "max_participants": 3,
        "participants": ["existing@mergington.edu"],
    }
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(TEST_ACTIVITIES))
    with TestClient(app_module.app) as test_client:
        yield test_client


def activity_url(activity_name):
    return f"/activities/{quote(activity_name, safe='')}/signup"


def test_root_redirects_to_static_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == TEST_ACTIVITIES


def test_signup_adds_participant(client):
    email = "new@mergington.edu"

    response = client.post(activity_url("Test Activity"), params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Test Activity"}
    assert email in app_module.activities["Test Activity"]["participants"]


def test_signup_returns_404_for_unknown_activity(client):
    response = client.post(activity_url("Unknown Activity"), params={"email": "new@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client):
    email = "existing@mergington.edu"

    response = client.delete(activity_url("Test Activity"), params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Test Activity"}
    assert email not in app_module.activities["Test Activity"]["participants"]


def test_unregister_returns_404_for_unknown_activity(client):
    response = client.delete(activity_url("Unknown Activity"), params={"email": "someone@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_returns_404_for_unregistered_participant(client):
    response = client.delete(activity_url("Test Activity"), params={"email": "unknown@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Participant is not signed up for this activity"}
