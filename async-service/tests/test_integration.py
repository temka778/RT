import pytest
import requests
import pika
import json

BASE_URL = "https://localhost:5002"
RABBIT_URL = "amqp://guest:guest@localhost/"

@pytest.fixture
def client():
    return requests.Session()

def test_create_config_task(client):
    payload = {
        "parameters": {
            "username": "admin",
            "password": "admin",
            "vlan": 534,
            "interfaces": [1, 2, 3, 4]
        }
    }
    response = client.post(f"{BASE_URL}/api/v1/equipment/cpe/ABC12345", json=payload, verify=False)
    assert response.status_code == 200
    assert "taskId" in response.json()
    assert response.json()["code"] == 200

def test_get_task_status_running(client):
    payload = {
        "parameters": {
            "username": "admin",
            "password": "admin",
            "vlan": 534,
            "interfaces": [1, 2, 3, 4]
        }
    }
    response = client.post(f"{BASE_URL}/api/v1/equipment/cpe/ABC12345", json=payload, verify=False)
    task_id = response.json()["taskId"]
    response = client.get(f"{BASE_URL}/api/v1/equipment/cpe/ABC12345/task/{task_id}", verify=False)
    assert response.status_code == 204
    assert response.json() == {"code": 204, "message": "Task is still running"}

def test_get_task_status_not_found(client):
    response = client.get(f"{BASE_URL}/api/v1/equipment/cpe/ABC12345/task/invalid-task", verify=False)
    assert response.status_code == 404
    assert response.json() == {"code": 404, "message": "The requested task is not found"}

def test_rabbitmq_publish():
    connection = pika.BlockingConnection(pika.URLParameters(RABBIT_URL))
    channel = connection.channel()
    channel.queue_declare(queue="task_dispatcher", durable=True)
    message = json.dumps({
        "task_id": "test-task",
        "equipment_id": "ABC12345",
        "parameters": {"username": "admin", "password": "admin"}
    })
    channel.basic_publish(
        exchange='',
        routing_key="task_dispatcher",
        body=message,
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()
    assert True
