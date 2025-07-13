from flask import Flask, request, jsonify
import re
import time
from threading import Thread

app = Flask(__name__)

ID_PATTERN = re.compile(r"^[a-zA-Z0-9]{6,}$")

@app.route('/api/v1/equipment/cpe/<string:equipment_id>', methods=['POST'])
def configure_equipment(equipment_id):
    if not ID_PATTERN.match(equipment_id):
        return jsonify({"code": 404, "message": "The requested equipment is not found"}), 404

    data = request.get_json()

    try:
        timeout = data.get("timeoutInSeconds", 10)
        parameters = data.get("parameters", {})

        if not parameters.get("username") or not parameters.get("password"):
            raise ValueError("Missing required parameters")

        time.sleep(60)

        return jsonify({"code": 200, "message": "success"}), 200

    except Exception as e:
        return jsonify({"code": 500, "message": "Internal provisioning exception"}), 500


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, ssl_context=("cert/cert.pem", "cert/key.pem"))
