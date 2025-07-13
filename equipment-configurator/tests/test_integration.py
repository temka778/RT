import pytest
import requests
import time

BASE_URL = "https://localhost:5001"

@pytest.fixture
def client():
    return requests.Session()

def test_configure_equipment_success(client):
    payload = {
        "timeoutInSeconds": 14,
        "parameters": {
            "username": "admin",
            "password": "admin",
            "vlan": 534,
            "interfaces": [1, 2, 3, 4]
        }
    }
    start_time = time.time()
    response = client.post(f"{BASE_URL}/api/v1/equipment/cpe/ABC12345", json=payload, verify=False)
    assert response.status_code == 200
    assert response.json() == {"code": 200, "message": "success"}
    assert time.time() - start_time >= 60

def test_configure_equipment_invalid_id(client):
    response = client.post(f"{BASE_URL}/api/v1/equipment/cpe/123", json={}, verify=False)
    assert response.status_code == 404
    assert response.json() == {"code": 404, "message": "The requested equipment is not found"}

def test_configure_equipment_missing_parameters(client):
    payload = {"timeoutInSeconds": 14, "parameters": {}}
    response = client.post(f"{BASE_URL}/api/v1/equipment/cpe/ABC12345", json=payload, verify=False)
    assert response.status_code == 500
    assert response.json() == {"code": 500, "message": "Internal provisioning exception"}
