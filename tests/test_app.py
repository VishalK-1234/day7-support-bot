
import pytest

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_chat_returns_a_reply(client):
    response = client.post(
        "/chat",
        json={"customer_email": "ravi.kumar@example.com", "message": "Hello"},
        headers={"Authorization": "Bearer demo-token-ravi"}
    )
    assert response.status_code == 200
    assert "reply" in response.get_json()


def test_order_status(client):
    response = client.post(
        "/chat",
        json={"customer_email": "ravi.kumar@example.com", "message": "Where is my order 10231?"},
        headers={"Authorization": "Bearer demo-token-ravi"}
    )
    assert response.get_json()["action_result"] == "Shipped"


def test_unknown_order(client):
    response = client.post(
        "/chat",
        json={"customer_email": "priya.s@example.com", "message": "What is the status of order 99999?"},
        headers={"Authorization": "Bearer demo-token-priya"}
    )
    assert response.get_json()["action_result"] == "Order not found"


def test_missing_token(client):
    response = client.post(
        "/chat",
        json={"customer_email": "ravi.kumar@example.com", "message": "Hello"}
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"


def test_wrong_customer_token(client):
    response = client.post(
        "/chat",
        json={"customer_email": "priya.s@example.com", "message": "Please close my account"},
        headers={"Authorization": "Bearer demo-token-ravi"}
    )
    assert response.status_code == 401
    assert response.get_json()["error"] == "Unauthorized"
