import os
import json
from datetime import datetime
from threading import Lock
from flask import Flask, request, jsonify
from inference import run_inference

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

buffer_lock = Lock()
status = {
    "running": True,
    "mode": "collect",
    "samples_received": 0,
    "last_prediction": None,
    "buffer_size": 0,
    "sampling_rate": 64,
    "last_updated": None,
}

buffer = {
    "ankle": {"x": [], "y": [], "z": []},
    "thigh": {"x": [], "y": [], "z": []},
    "hip": {"x": [], "y": [], "z": []},
}


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/status")
def get_status():
    with buffer_lock:
        data = dict(status)
        data["buffer_size"] = len(buffer["ankle"]["x"])
        data["last_updated"] = datetime.now().isoformat()
    return jsonify(data)


@app.post("/api/data")
def receive_data():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"error": "json body required"}), 400

    try:
        with buffer_lock:
            for sensor in ["ankle", "thigh", "hip"]:
                for axis in ["x", "y", "z"]:
                    buffer[sensor][axis].append(float(payload[sensor][axis]))
            status["samples_received"] += 1
            status["buffer_size"] = len(buffer["ankle"]["x"])
            status["last_updated"] = datetime.now().isoformat()
        return jsonify({"message": "data accepted"})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/predict")
def predict():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"error": "json body required"}), 400

    result = run_inference(payload)
    with buffer_lock:
        status["last_prediction"] = result
        status["mode"] = "detect"
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5050"))
    host = os.getenv("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=False)
