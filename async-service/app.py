from flask import Flask, request, jsonify, make_response
import re
import uuid
import json
from db import init_db, create_task, get_task
from tasks import send_task_to_queue

app = Flask(__name__)
init_db()

ID_PATTERN = re.compile(r"^[a-zA-Z0-9]{6,}$")

@app.route("/api/v1/equipment/cpe/<string:equipment_id>", methods=["POST"])
def create_config_task(equipment_id):
    if not ID_PATTERN.match(equipment_id):
        return jsonify({"code": 404, "message": "The requested equipment is not found"}), 404

    try:
        data = request.get_json()
        parameters = data.get("parameters")
        if not parameters or not parameters.get("username") or not parameters.get("password"):
            raise ValueError("Missing required parameters: username and password")
        if "vlan" in parameters and not isinstance(parameters["vlan"], int):
            raise ValueError("VLAN must be an integer")
        if "interfaces" in parameters and not all(isinstance(i, int) for i in parameters["interfaces"]):
            raise ValueError("Interfaces must be a list of integers")

        task_id = str(uuid.uuid4())
        create_task(task_id, equipment_id, json.dumps(parameters))
        send_task_to_queue(task_id, equipment_id, parameters)

        return jsonify({"code": 200, "taskId": task_id}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": "Internal provisioning exception"}), 500

@app.route("/api/v1/equipment/cpe/<string:equipment_id>/task/<string:task_id>", methods=["GET"])
def get_task_status(equipment_id, task_id):
    if not ID_PATTERN.match(equipment_id):
        return jsonify({"code": 404, "message": "The requested equipment is not found"}), 404

    try:
        status = get_task(task_id)
        if not status:
            return jsonify({"code": 404, "message": "The requested task is not found"}), 404

        if status == "completed":
            return jsonify({"code": 200, "message": "Completed"}), 200
        else:
            response = make_response(json.dumps({"code": 204, "message": "Task is still running"}), 204)
            response.headers['Content-Type'] = 'application/json'
            return response
    except Exception as e:
        return jsonify({"code": 500, "message": "Internal provisioning exception"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, ssl_context=("cert/cert.pem", "cert/key.pem"))
