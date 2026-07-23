import os
import csv
import io
from datetime import datetime
from threading import Lock
from flask import Flask, request, jsonify, Response
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
    "device_connected": False,
    "last_device_message": None,
    "recording_state": "idle",
}

buffer = {
    "ankle": {"x": [], "y": [], "z": []},
    "thigh": {"x": [], "y": [], "z": []},
    "hip": {"x": [], "y": [], "z": []},
}


@app.get("/")
def root():
    return jsonify({
        "message": "FOG backend is running",
        "health": "/api/health",
        "status": "/api/status",
    })


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


@app.get("/api/latest-samples")
def get_latest_samples():
    try:
        limit = int(request.args.get("limit", "80"))
    except ValueError:
        limit = 80

    limit = max(1, min(limit, 300))

    with buffer_lock:
        recent = {
            sensor: {
                axis: buffer[sensor][axis][-limit:]
                for axis in ["x", "y", "z"]
            }
            for sensor in ["ankle", "thigh", "hip"]
        }

    return jsonify(recent)


@app.get("/api/export")
def export_data():
    with buffer_lock:
        if not buffer["ankle"]["x"]:
            return jsonify({"error": "no data available to export"}), 400

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["sample_index", "ankle_x", "ankle_y", "ankle_z", "thigh_x", "thigh_y", "thigh_z", "hip_x", "hip_y", "hip_z"])

        max_len = len(buffer["ankle"]["x"])
        for idx in range(max_len):
            writer.writerow([
                idx,
                buffer["ankle"]["x"][idx],
                buffer["ankle"]["y"][idx],
                buffer["ankle"]["z"][idx],
                buffer["thigh"]["x"][idx],
                buffer["thigh"]["y"][idx],
                buffer["thigh"]["z"][idx],
                buffer["hip"]["x"][idx],
                buffer["hip"]["y"][idx],
                buffer["hip"]["z"][idx],
            ])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=imu_export.csv"
    return response


@app.post("/api/reset-buffer")
def reset_buffer():
    with buffer_lock:
        for sensor in ["ankle", "thigh", "hip"]:
            for axis in ["x", "y", "z"]:
                buffer[sensor][axis].clear()

        status["samples_received"] = 0
        status["buffer_size"] = 0
        status["recording_state"] = "idle"
        status["last_updated"] = datetime.now().isoformat()
        status["device_connected"] = False
        status["last_device_message"] = None

    return jsonify({"message": "buffer reset"})


@app.post("/api/data")
def receive_data():
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"error": "json body required"}), 400

    samples = payload if isinstance(payload, list) else [payload]

    try:
        now = datetime.now().isoformat()
        with buffer_lock:
            for item in samples:
                for sensor in ["ankle", "thigh", "hip"]:
                    if sensor not in item:
                        raise ValueError(f"missing sensor {sensor}")
                    for axis in ["x", "y", "z"]:
                        if axis not in item[sensor]:
                            raise ValueError(f"missing axis {sensor}.{axis}")
                        buffer[sensor][axis].append(float(item[sensor][axis]))

                status["samples_received"] += 1
                status["buffer_size"] = len(buffer["ankle"]["x"])
                status["last_updated"] = now
                status["device_connected"] = True
                status["last_device_message"] = now
                status["recording_state"] = "recording"

        return jsonify({"message": "data accepted", "samples_received": len(samples)})
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
