"""Posts simulated sensor readings for every farm of one farmer account, on a timer.
Run from backend/ with SIM_PHONE and SIM_PASSWORD set in that terminal only:
    python -m simulator.multi_farm --interval 120 --base-url http://127.0.0.1:8000
Each farm uses its own soil type and starts at a different point of the scenario cycle, so farms show different readings.
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
from simulator.run import AuthClient, post_reading  # noqa: E402

log = logging.getLogger("multi_farm")


def get_farms(base_url, auth):
    for attempt in range(2):
        req = urllib.request.Request(f"{base_url.rstrip('/')}/farms", headers=auth.auth_header())
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and attempt == 0:
                auth.invalidate()
                continue
            raise


def main():
    p = argparse.ArgumentParser(description="Simulated sensor readings for all farms of one farmer account.")
    p.add_argument("--interval", type=float, default=120.0, help="seconds between rounds (default 120)")
    p.add_argument("--base-url", default=os.environ.get("API_BASE_URL", "http://127.0.0.1:8000"))
    p.add_argument("--phone", default=os.environ.get("SIM_PHONE", ""))
    p.add_argument("--password", default=os.environ.get("SIM_PASSWORD", ""))
    args = p.parse_args()
    if not args.phone or not args.password:
        sys.exit("Set SIM_PHONE and SIM_PASSWORD in this terminal first.")

    auth = AuthClient(args.base_url, args.phone, args.password)
    auth.token()
    rng = random.Random()
    tick = 0
    log.info("Posting for every farm of this account every %s s. Press Ctrl+C to stop.", args.interval)
    try:
        while True:
            try:
                farms = get_farms(args.base_url, auth)
                if not farms:
                    log.warning("This account has no farms yet.")
                for i, farm in enumerate(farms):
                    scenario = STRESS_CLASSES[(tick + i) % len(STRESS_CLASSES)]
                    reading = generate_reading(scenario, farm.get("soil_type") or "loam", rng)
                    post_reading(args.base_url, farm["id"], reading, auth, scenario=f"{farm['name'][:14]}:{scenario}")
            except Exception:
                log.exception("This round failed; trying again next round")
            tick += 1
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log.info("Stopped.")


if __name__ == "__main__":
    main()