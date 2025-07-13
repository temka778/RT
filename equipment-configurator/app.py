from flask import Flask, request, jsonify
import re
import asyncio

app = Flask(__name__)

ID_PATTERN = re.compile(r"^[a-zA-Z0-9]{6,}$")

async def simulate_provisioning():
    await asyncio.sleep(60)
    return {"code": 200, "message": "success"}

def run_async(coroutine):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)

@app.route('/api/v1/equipment/cpe/<string:equipment_id>', methods=['POST'])
def configure_equipment(equipment_id):
    if not ID_PATTERN.match(equipment_id):
        return jsonify({"code": 404, "message": "The requested equipment is not found"}), 404

    try:
        data = request.get_json()
        timeout = data.get("timeoutInSeconds", 10)
        parameters = data.get("parameters", {})

        if not parameters.get("username") or not parameters.get("password"):
            raise ValueError("Missing required parameters: username and password")
        if "vlan" in parameters and not isinstance(parameters["vlan"], int):
            raise ValueError("VLAN must be an integer")
        if "interfaces" in parameters and not all(isinstance(i, int) for i in parameters["interfaces"]):
            raise ValueError("Interfaces must be a list of integers")

        result = run_async(simulate_provisioning())
        return jsonify(result), result["code"]

    except Exception as e:
        return jsonify({"code": 500, "message": "Internal provisioning exception"}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5001, ssl_context=("cert/cert.pem", "cert/key.pem"))
