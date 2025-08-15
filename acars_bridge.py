import os
import time
import re
import shutil
from flask import Flask, jsonify, send_file
from threading import Thread

app = Flask(__name__)

LOG_DIR = os.path.dirname(os.path.abspath(__file__))
TMP_FILE = os.path.join(LOG_DIR, "log_temp.txt")

aircraft_data = {}

log_pattern = re.compile(r"(\d{8}-\d{4})-log")
timestamp_pattern = re.compile(r"\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+\]")

current_block = []
current_flight = None


def find_latest_log():
    logs = [f for f in os.listdir(LOG_DIR) if log_pattern.match(f)]
    if not logs:
        return None
    logs.sort(reverse=True)
    return os.path.join(LOG_DIR, logs[0])


def process_log(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                parse_log_line(line)
    except Exception as e:
        print(f"[ERROR] Failed to read log: {e}")


def convert_coord(value, hemi, is_lon=False):
    """
    Converts ACARS coordinate (degrees+min, degrees+min+sec or decimal/1000) to decimal degrees.
    """
    value = value.strip()
    decimal = None

    # Detect decimal/1000 format (e.g., 15544 -> 15.544°)
    if len(value) in (5, 6) and "." not in value:
        try:
            decimal = int(value) / 1000.0
        except ValueError:
            pass

    # Degrees + minutes + seconds (DDMMSS or DDDMMSS)
    if decimal is None and len(value) >= (3 if is_lon else 2) + 4:
        deg_digits = 3 if is_lon else 2
        deg = int(value[0:deg_digits])
        minutes = int(value[deg_digits:deg_digits+2])
        seconds = float(value[deg_digits+2:]) if len(value) > deg_digits+2 else 0
        decimal = deg + (minutes / 60.0) + (seconds / 3600.0)

    # Degrees + decimal minutes (DDMMm or DDDMMm)
    if decimal is None and len(value) >= (3 if is_lon else 2) + 2:
        deg_digits = 3 if is_lon else 2
        deg = int(value[0:deg_digits])
        minutes = float(value[deg_digits:])
        decimal = deg + (minutes / 60.0)

    if decimal is None:
        return None

    if hemi in ("S", "W"):
        decimal = -decimal
    return decimal


def parse_log_line(line):
    """Groups complete messages and detects coordinates in multiple formats."""
    global aircraft_data, current_block, current_flight

    stripped = line.strip()
    if not stripped:
        return

    # Start of block
    if stripped.startswith("SOURCE:"):
        current_block = [stripped]
        current_flight = None
        return

    # Inside block
    if current_block is not None:
        current_block.append(stripped)

        # Flight ID and REG
        if "Flight ID:" in stripped:
            parts = stripped.split()
            try:
                flight_index = parts.index("ID:") + 1
            except ValueError:
                return
            flight_id = parts[flight_index]
            reg = parts[flight_index + 2] if flight_index + 2 < len(parts) else "???"
            current_flight = flight_id

            if flight_id not in aircraft_data:
                aircraft_data[flight_id] = {
                    "reg": reg,
                    "msgs": [],
                    "last_seen": time.time(),
                    "lat": None,
                    "lon": None
                }
            aircraft_data[flight_id]["last_seen"] = time.time()

        # Format 1: old DDMM.mm[NS],DDDMM.mm[EW]
        match_old = re.search(r"(\d{2})(\d{2}\.\d+)([NS]),(\d{3})(\d{2}\.\d+)([EW])", stripped)
        if match_old and current_flight:
            lat_deg = int(match_old.group(1))
            lat_min = float(match_old.group(2))
            lat_hem = match_old.group(3)
            lon_deg = int(match_old.group(4))
            lon_min = float(match_old.group(5))
            lon_hem = match_old.group(6)

            lat = lat_deg + lat_min / 60.0
            lon = lon_deg + lon_min / 60.0
            if lat_hem == "S":
                lat = -lat
            if lon_hem == "W":
                lon = -lon

            aircraft_data[current_flight]["lat"] = lat
            aircraft_data[current_flight]["lon"] = lon

        # Format 2: new DDMMSS[NS]DDDMMSS[EW]
        match_new = re.search(r"(\d{4,6})([NS])(\d{5,7})([EW])", stripped)
        if match_new and current_flight:
            lat_val = match_new.group(1)
            lat_hem = match_new.group(2)
            lon_val = match_new.group(3)
            lon_hem = match_new.group(4)

            lat = convert_coord(lat_val, lat_hem, is_lon=False)
            lon = convert_coord(lon_val, lon_hem, is_lon=True)
            if lat is not None and lon is not None:
                aircraft_data[current_flight]["lat"] = lat
                aircraft_data[current_flight]["lon"] = lon

        # Format 3: POS[NS]xxxxx[EW]xxxxxx (decimal degrees /1000)
        match_pos = re.search(r"POS([NS])(\d{5})([EW])(\d{6})", stripped)
        if match_pos and current_flight:
            lat_hem = match_pos.group(1)
            lat_val = match_pos.group(2)
            lon_hem = match_pos.group(3)
            lon_val = match_pos.group(4)

            lat = convert_coord(lat_val, lat_hem, is_lon=False)
            lon = convert_coord(lon_val, lon_hem, is_lon=True)
            if lat is not None and lon is not None:
                aircraft_data[current_flight]["lat"] = lat
                aircraft_data[current_flight]["lon"] = lon

        # End of block
        if timestamp_pattern.search(stripped) and current_flight:
            msg_text = "\n".join(current_block)
            aircraft_data[current_flight]["msgs"].append(msg_text)
            current_block = []
            current_flight = None


@app.route("/")
def index():
    return send_file("acarsdeco_mapa.html")


@app.route("/data.json")
def data_json():
    planes = []
    for fid, info in aircraft_data.items():
        plane = {
            "flight": fid,
            "reg": info["reg"],
            "msgs_count": len(info["msgs"]),
            "last_seen": info["last_seen"]
        }
        if info["lat"] and info["lon"]:
            plane["lat"] = info["lat"]
            plane["lon"] = info["lon"]
        planes.append(plane)
    return jsonify({"planes": planes})


@app.route("/messages/<flight>")
def messages(flight):
    msgs = aircraft_data.get(flight, {}).get("msgs", [])
    return jsonify({"flight": flight, "messages": msgs})


def log_checker():
    last_file = None
    while True:
        new_log = find_latest_log()
        if not new_log:
            print("[WARN] No log found.")
        else:
            if new_log != last_file:
                print(f"[INFO] New log detected: {new_log}")
                last_file = new_log
            try:
                shutil.copy2(new_log, TMP_FILE)
                process_log(TMP_FILE)
            except Exception as e:
                print(f"[ERROR] Failed to copy/read log: {e}")
        time.sleep(15)


if __name__ == "__main__":
    Thread(target=log_checker, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)
