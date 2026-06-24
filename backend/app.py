import json
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

#finding the .env file in the parent directory of the current file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

#Three constants Flask uses throughout BUREAU_PORT reads your port from .env
BUREAU_PORT = int(os.environ.get("BUREAU_PORT", 8000))
#This is the address of your Triage agent, Flask sends user descriptions here
TRIAGE_URL = f"http://127.0.0.1:{BUREAU_PORT}/triage"
#added this for demo for the frontend to know if it should show the demo mode banner instead of calling the APIs
DEMO_MODE=os.environ.get("DEMO_MODE", "false").lower() == "true"
#Also added this for demo, a separate file path for demo results 
DEMO_RESULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "demo_result.json")
#The file path where pathfinder writts its result, and flask reads it back to give to the frontnd
RESULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "result.json")

app = Flask(__name__)
CORS(app)


#A helper function that saves data to result.json
#os.makedirs creates the directory if it doesn't exist, and json.dump writes the data to the file with indentation for readability
#json.dump... writes the dictionary as formatted JSON with 2 space indentation
def write_result(data: dict) -> None:
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w") as f:
        json.dump(data, f, indent=2)

#Main Endpoint- the one React calls when the user click "Find my plan B"
#silent=True means if parsing fails, return None instead of crashing, if the user sent nothing
@app.route("/api/plan", methods=["POST"])
def submit_plan():
    data = request.get_json(silent=True) or {}
    description = data.get("description", "").strip()
    
    if not description:
        return jsonify({"status": "error", "error": "description is required"}), 400
    #Only runs this branch when deployed, skips it locally
    if DEMO_MODE:
        #checking if our demo path exits or not
        if os.path.exists(DEMO_RESULT_PATH):
            #reads presaved real result
            with open(DEMO_RESULT_PATH) as f:
                demo_data = json.load(f)
            #write it to result.json immediately so that it could get "status":"done"
            write_result(demo_data)
        else:
            write_result({
                "status":"error",
                "error":"Demo result file not found. "
            })
        return jsonify({"status":"processing"})

    write_result({"status": "processing"})

    #Flask forwards the user's description to Triage agent
    #timeout=30 means giving up after 30 seconds if the agent doesn't respond
    #raise_for_status() throws an exception if the agent returned a 4xx/5xx error code
    #except block catches any network problem and saves a clean error message to result.json so the frontend shows a friendly error instead of freezing

    try:
        triage_response = requests.post(TRIAGE_URL, json={"description": description}, timeout=30)
        triage_response.raise_for_status()
        body = triage_response.json()
    except requests.RequestException as exc:
        write_result({"status": "error", "error": f"triage_agent unreachable: {exc}"})
        return jsonify({"status": "error", "error": str(exc)}), 502

    #Even if the HTTP request succeeded, the Triage agent might return {"status": "error"}(like when Claude extraction fails)
    if body.get("status") == "error":
        write_result({"status": "error", "error": body.get("error", "triage failed")})
        return jsonify({"status": "error", "error": body.get("error")}), 502
    #this tells React "we've started, now keep polling"
    return jsonify({"status": "processing"})


#React polls this every few seconds asking "are we done yet?" 
#if result.json doesn't exist yet, return "processing" 
#if it does exist, read it and return its contents as JSON
@app.route("/api/plan/status", methods=["GET"])
def get_status():
    if not os.path.exists(RESULT_PATH):
        return jsonify({"status": "processing"})
    with open(RESULT_PATH) as f:
        return jsonify(json.load(f))

#Only runs the server when execute this file directly(app.py)
#Gets the port from .env or defaults to 5002
if __name__ == "__main__":
    port = int(os.environ.get("FLASK_BACKEND_PORT", 5002))
    app.run(port=port, debug=True)
