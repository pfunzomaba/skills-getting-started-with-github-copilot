import pytest
import src.app as app_module
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch):
    test_activities = {
        "Chess Club": {
            "description": "Play chess",
            "schedule": "Fridays",
            "max_participants": 12,
            "participants": ["existing@mergington.edu"],
        },
        "Art Club": {
            "description": "Make art",
            "schedule": "Thursdays",
            "max_participants": 18,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", test_activities)

    with TestClient(app_module.app) as test_client:
        yield test_client


def test_root_redirects_to_homepage(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_available_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == ["existing@mergington.edu"]
    assert response.json()["Art Club"]["participants"] == []


def test_signup_adds_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up new@mergington.edu for Chess Club"
    }
    assert "new@mergington.edu" in client.get("/activities").json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "new@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_participant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Unregistered existing@mergington.edu from Chess Club"
    }
    assert "existing@mergington.edu" not in client.get("/activities").json()["Chess Club"]["participants"]


def test_unregister_rejects_unregistered_participant(client):
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "missing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown Club/signup",
        params={"email": "existing@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
