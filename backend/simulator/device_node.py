"""Pretends to be the sensor box installed at ONE plot: posts readings with the plot's device key, like the real box will.
Run from backend/ with DEVICE_KEY set in that terminal only (create the key in the admin screen: Edit farm, Sensor box key).

Normal box:
    python -m simulator.device_node --scenario normal --interval 60 --base-url http://127.0.0.1:8000

A box with a dead sensor (the others keep reporting). Choose any of soil_moisture, temperature, humidity, leaf_wetness, npk:
    python -m simulator.device_node --dead soil_moisture
    python -m simulator.device_node --dead npk

Send only temperature and humidity and let the server work out leaf wetness:
    python -m simulator.device_node --dead leaf_wetness

Send N, P and K too (the plot must have the NPK setting on): --npk ok, or low_nitrogen, low_phosphorus, low_potassium.
Stop it with Ctrl+C."""
import argparse
import json
import logging
import os
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.services.sensor import STRESS_CLASSES, generate_reading  # noqa: E402
from simulator.multi_farm import NPK_CHOICES, npk_reading  # noqa: E402

log = logging.getLogger("device_node")
DEAD_CHOICES = ["soil_moisture", "temperature", "humidity", "leaf_wetness", "npk"]
FIRMWARE = "sim-0.1"


def post(base_url, key, path, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"X-Device-Key": key}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{base_url.rstrip('/')}{path}", data=data, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def main():
    p = argparse.ArgumentParser(description="Simulated sensor box for one plot, using a device key.")
    p.add_argument("--base-url", default=os.environ.get("API_BASE_URL", "http://127.0.0.1:8000"))
    p.add_argument("--key", default=os.environ.get("DEVICE_KEY", ""))
    p.add_argument("--scenario", default="normal", choices=STRESS_CLASSES)
    p.add_argument("--interval", type=float, default=60.0, help="seconds between readings (default 60)")
    p.add_argument("--dead", default="", help=f"comma list of sensors that report nothing, from {DEAD_CHOICES}")
    p.add_argument("--npk", choices=NPK_CHOICES, default="", help="send N, P and K values")
    p.add_argument("--battery", type=float, default=100.0, help="starting battery percent; drops a little each reading")
    p.add_argument("--rounds", type=int, default=0, help="stop after this many readings (0 = until Ctrl+C)")
    args = p.parse_args()
    if not args.key:
        sys.exit("Set DEVICE_KEY in this terminal first.")
    dead = {s.strip() for s in args.dead.split(",") if s.strip()}
    bad = dead - set(DEAD_CHOICES)
    if bad:
        sys.exit(f"Unknown sensor(s) {sorted(bad)}. Choose from {DEAD_CHOICES}.")
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    try:
        who = post(args.base_url, args.key, "/device/whoami")
    except urllib.error.HTTPError as exc:
        sys.exit(f"The server refused this key ({exc.code}). Check the key and that it has not been replaced or revoked.")
    log.info("Box for plot '%s'. Posting every %s s. Ctrl+C to stop.", who["farm_name"], args.interval)
    if args.npk and not who["has_npk_sensor"]:
        sys.exit("This plot does not have the NPK setting on, so it cannot take N, P and K values.")

    rng = random.Random()
    battery, count = args.battery, 0
    try:
        while True:
            reading = generate_reading(args.scenario, "loam", rng)
            if args.npk and "npk" not in dead:
                reading.update(npk_reading(args.npk, rng))
            for sensor in dead - {"npk"}:
                reading.pop(sensor, None)
            reading["battery_percent"] = round(max(0.0, battery), 1)
            reading["firmware"] = FIRMWARE
            try:
                saved = post(args.base_url, args.key, "/device/readings", reading)
                log.info("sent %s; server leaf wetness=%s", sorted(k for k in reading if k not in ("firmware",)), saved.get("leaf_wetness"))
            except urllib.error.HTTPError as exc:
                log.error("Server said %s: %s", exc.code, exc.read().decode()[:200])
            battery -= 0.05
            count += 1
            if args.rounds and count >= args.rounds:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log.info("Stopped.")


if __name__ == "__main__":
    main()
