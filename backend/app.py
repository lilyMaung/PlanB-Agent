import json
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

BUREAU_PORT = int(os.environ.get("BUREAU_PORT", 8000))
TRIAGE_URL = f"http://127.0.0.1:{BUREAU_PORT}/triage"
RESULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "result.json")

app = Flask(__name__)
CORS(app)


def write_result(data: dict) -> None:
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w") as f:
        json.dump(data, f, indent=2)


@app.route("/api/plan", methods=["POST"])
def submit_plan():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    if not description:
        return jsonify({"status": "error", "error": "description is required"}), 400

    write_result({"status": "processing"})

    try:
        triage_response = requests.post(TRIAGE_URL, json={"description": description}, timeout=30)
        triage_response.raise_for_status()
        body = triage_response.json()
    except requests.RequestException as exc:
        write_result({"status": "error", "error": f"triage_agent unreachable: {exc}"})
        return jsonify({"status": "error", "error": str(exc)}), 502

    if body.get("status") == "error":
        write_result({"status": "error", "error": body.get("error", "triage failed")})
        return jsonify({"status": "error", "error": body.get("error")}), 502

    return jsonify({"status": "processing"})


@app.route("/api/plan/status", methods=["GET"])
def get_status():
    if not os.path.exists(RESULT_PATH):
        return jsonify({"status": "processing"})
    with open(RESULT_PATH) as f:
        return jsonify(json.load(f))


if __name__ == "__main__":
    port = int(os.environ.get("FLASK_BACKEND_PORT", 5002))
    app.run(port=port, debug=True)
