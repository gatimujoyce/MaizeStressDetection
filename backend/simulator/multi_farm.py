"""Posts simulated sensor readings for every farm of one farmer account, on a timer.
Run from backend/ with SIM_PHONE and SIM_PASSWORD set in that terminal only.

Default (as before): each farm cycles through the scenarios, one reading per farm every --interval seconds.
    python -m simulator.multi_farm --interval 120 --base-url http://127.0.0.1:8000

Hold a scenario per farm (farms are taken in name order; the list repeats if there are more farms):
    python -m simulator.multi_farm --hold heat_stress,normal,drought_stress

Replay a day quickly: reading times start --replay-hours ago and advance --step-minutes per round, so a full
24 hour window builds up in about a minute. Once the replay catches up with the clock it continues live.
    python -m simulator.multi_farm --interval 3 --replay-hours 24 --step-minutes 60 --hold heat_stress,normal,waterlogging_risk

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
from datetime import datetime, timedelta, timezone
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.services.sensor import STRESS_CLASSES, generate_reading  # noqa: E402
from simulator.run import AuthClient  # noqa: E402

log = logging.getLogger("multi_farm")


def api(base_url, path, auth, payload=None):
    """GET (payload None) or POST JSON; one retry after a 401 with a fresh token."""
    for attempt in range(2):
        headers = dict(auth.auth_header())
        data = None
        if payload is not None:
            data = json.dumps(payload).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(f"{base_url.rstrip('/')}{path}", data=data, headers=headers)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and attempt == 0:
                auth.invalidate()
                continue
            raise


def parse_hold(text):
    names = [s.strip() for s in (text or "").split(",") if s.strip()]
    bad = [n for n in names if n not in STRESS_CLASSES]
    if bad:
        sys.exit(f"Unknown scenario(s) {bad}. Choose from {STRESS_CLASSES}.")
    return names


def main():
    p = argparse.ArgumentParser(description="Simulated sensor readings for all farms of one farmer account.")
    p.add_argument("--interval", type=float, default=120.0, help="seconds between rounds (default 120)")
    p.add_argument("--base-url", default=os.environ.get("API_BASE_URL", "http://127.0.0.1:8000"))
    p.add_argument("--phone", default=os.environ.get("SIM_PHONE", ""))
    p.add_argument("--password", default=os.environ.get("SIM_PASSWORD", ""))
    p.add_argument("--hold", default="", help=f"comma list of scenarios held per farm, from {STRESS_CLASSES}")
    p.add_argument("--replay-hours", type=float, default=0.0,
                   help="start the reading times this many hours ago and move forward until caught up")
    p.add_argument("--step-minutes", type=float, default=60.0,
                   help="simulated minutes between readings while replaying (default 60)")
    p.add_argument("--rounds", type=int, default=0, help="stop after this many rounds (0 = run until Ctrl+C)")
    args = p.parse_args()
    if not args.phone or not args.password:
        sys.exit("Set SIM_PHONE and SIM_PASSWORD in this terminal first.")
    hold = parse_hold(args.hold)
    if not logging.getLogger().handlers:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    auth = AuthClient(args.base_url, args.phone, args.password)
    auth.token()
    rng = random.Random()
    sim_time = (datetime.now(timezone.utc) - timedelta(hours=args.replay_hours)) if args.replay_hours else None
    tick = 0
    log.info("Posting for every farm of this account every %s s. Press Ctrl+C to stop.", args.interval)
    try:
        while True:
            try:
                farms = sorted(api(args.base_url, "/farms", auth), key=lambda f: f.get("name", ""))
                if not farms:
                    log.warning("This account has no farms yet.")
                recorded_at = None
                if sim_time is not None and sim_time <= datetime.now(timezone.utc):
                    recorded_at = sim_time
                    sim_time = sim_time + timedelta(minutes=args.step_minutes)
                for i, farm in enumerate(farms):
                    scenario = hold[i % len(hold)] if hold else STRESS_CLASSES[(tick + i) % len(STRESS_CLASSES)]
                    reading = generate_reading(scenario, farm.get("soil_type") or "loam", rng)
                    if recorded_at is not None:
                        reading["recorded_at"] = recorded_at.isoformat()
                    api(args.base_url, f"/farms/{farm['id']}/readings", auth, reading)
                    log.info("%-14s %-18s T=%5.1f C  soil=%5.1f  hum=%5.1f%s", farm.get("name", "")[:14], scenario,
                             reading["temperature"], reading["soil_moisture"], reading["humidity"],
                             f"  (simulated {recorded_at:%d %b %H:%M})" if recorded_at is not None else "")
            except Exception:
                log.exception("This round failed; trying again next round")
            tick += 1
            if args.rounds and tick >= args.rounds:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        log.info("Stopped.")


if __name__ == "__main__":
    main()