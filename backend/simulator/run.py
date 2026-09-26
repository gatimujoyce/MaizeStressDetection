"""
simulator/run.py — Live Sensor Simulator
========================================
Posts realistic maize-farm sensor readings to the backend API in a loop.

Usage (from the `backend/` directory):
    python -m simulator.run --farm-id <UUID> [options]

Environment variables (override with CLI flags):
    API_BASE_URL   API root, default http://localhost:8000
    SIM_PHONE      Farmer account phone number
    SIM_PASSWORD   Farmer account password

Round-robin scenario cycling:
    Each tick advances one step through:
        normal → drought_stress → heat_stress → waterlogging_risk → normal …

Staleness guard:
    If no reading has been successfully posted for > 24 h a WARNING is logged.
    In normal demo usage this will not fire, but the check is always active so
    it is visible in production logs.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


# Make `app.services.sensor` importable when running as:
#   python -m simulator.run          (from backend/)
#   python backend/simulator/run.py  (from project root)
# ---------------------------------------------------------------------------
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.services.sensor import (  # noqa: E402
    SOIL_TYPES,
    STRESS_CLASSES,
    generate_reading,
)


# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("simulator")

STALENESS_THRESHOLD = timedelta(hours=24)



# HTTP helpers (stdlib-only — no extra dependencies)
# ---------------------------------------------------------------------------

def _http_post(url: str, payload: dict, headers: dict | None = None,
               form_encoded: bool = False) -> tuple[int, dict]:
    """POST *payload* to *url*. Returns ``(status_code, response_body_dict)``."""
    if form_encoded:
        data = urllib.parse.urlencode(payload).encode()
        content_type = "application/x-www-form-urlencoded"
    else:
        data = json.dumps(payload).encode()
        content_type = "application/json"

    req_headers = {"Content-Type": content_type, **(headers or {})}
    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")

    try:
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except urllib.error.HTTPError as exc:
        body = {}
        try:
            body = json.loads(exc.read().decode())
        except Exception:
            pass
        return exc.code, body



# Auth
# ---------------------------------------------------------------------------

class AuthClient:
    """Manages Bearer-token auth with automatic re-login on 401."""

    def __init__(self, base_url: str, phone: str, password: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._phone    = phone
        self._password = password
        self._token: str | None = None

    def token(self) -> str:
        if self._token is None:
            self._login()
        return self._token  # type: ignore[return-value]

    def invalidate(self) -> None:
        """Call when the server returns 401 so the next request refreshes."""
        self._token = None

    def _login(self) -> None:
        url = f"{self._base_url}/auth/login"
        log.info("Authenticating as %s …", self._phone)
        status, body = _http_post(
            url,
            {"username": self._phone, "password": self._password},
            form_encoded=True,
        )
        if status != 200:
            raise RuntimeError(
                f"Login failed (HTTP {status}): {body.get('detail', body)}"
            )
        self._token = body["access_token"]
        log.info("Authenticated — Bearer token obtained.")

    def auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self.token()}"}



# Posting a reading
# ---------------------------------------------------------------------------

def post_reading(
    base_url: str,
    farm_id: str,
    reading: dict,
    auth: AuthClient,
    scenario: str = "?",
) -> bool:
    """POST one reading (must contain only API-schema keys). Retries once on
    401. Returns True on success.

    ``scenario`` is used only for log formatting — it is never sent to the API.
    """
    url = f"{base_url.rstrip('/')}/farms/{farm_id}/readings"

    for attempt in range(2):
        status, body = _http_post(url, reading, headers=auth.auth_header())

        if status in (200, 201):
            log.info(
                "✓ Reading posted  |  scenario=%-17s  soil_moisture=%-5s  "
                "temperature=%-5s  humidity=%-5s  leaf_wetness=%s",
                scenario,
                reading["soil_moisture"],
                reading["temperature"],
                reading["humidity"],
                reading["leaf_wetness"],
            )
            return True

        if status == 401 and attempt == 0:
            log.warning("401 Unauthorized — refreshing token …")
            auth.invalidate()
            continue  # retry with fresh token

        log.error("✗ POST failed (HTTP %s): %s", status, body.get("detail", body))
        return False

    return False


# ---------------------------------------------------------------------------
# Staleness check
# ---------------------------------------------------------------------------

def check_staleness(last_ok: datetime | None) -> None:
    """Warn if the last successful post is older than STALENESS_THRESHOLD."""
    if last_ok is None:
        return
    age = datetime.now(tz=timezone.utc) - last_ok
    if age > STALENESS_THRESHOLD:
        log.warning(
            "STALE — no successful reading posted for %s (threshold: %s). "
            "Check connectivity and farm-id.",
            age,
            STALENESS_THRESHOLD,
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Live sensor simulator — posts readings to the Maize Stress Detection API.",
    )
    p.add_argument(
        "--farm-id", required=True, metavar="UUID",
        help="UUID of the target farm.",
    )
    p.add_argument(
        "--soil-type", default="loam",
        choices=SOIL_TYPES,
        help="Soil type for this farm (default: loam).",
    )
    p.add_argument(
        "--interval", type=float, default=60.0, metavar="SECONDS",
        help="Seconds between readings (default: 60).",
    )
    p.add_argument(
        "--base-url",
        default=os.environ.get("API_BASE_URL", "http://localhost:8000"),
        metavar="URL",
        help="API base URL (env: API_BASE_URL, default: http://localhost:8000).",
    )
    p.add_argument(
        "--phone",
        default=os.environ.get("SIM_PHONE", ""),
        help="Farmer phone number for login (env: SIM_PHONE).",
    )
    p.add_argument(
        "--password",
        default=os.environ.get("SIM_PASSWORD", ""),
        help="Farmer password for login (env: SIM_PASSWORD).",
    )
    p.add_argument(
        "--verbose", action="store_true",
        help="Enable DEBUG logging.",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if not args.phone or not args.password:
        log.error(
            "Credentials required. Pass --phone / --password or set "
            "SIM_PHONE / SIM_PASSWORD environment variables."
        )
        sys.exit(1)

    auth = AuthClient(args.base_url, args.phone, args.password)
    rng  = random.Random()

    # Round-robin scenario state
    scenario_index     = 0
    num_scenarios      = len(STRESS_CLASSES)
    last_successful_at: datetime | None = None

    log.info(
        "Simulator starting  |  farm=%s  soil=%s  interval=%ss  api=%s",
        args.farm_id, args.soil_type, args.interval, args.base_url,
    )
    log.info("Scenario cycle: %s", " → ".join(STRESS_CLASSES) + " → …")

    # Authenticate eagerly so any credential errors surface immediately.
    try:
        auth.token()
    except RuntimeError as exc:
        log.error("Cannot start simulator: %s", exc)
        sys.exit(1)

    try:
        while True:
            scenario = STRESS_CLASSES[scenario_index % num_scenarios]
            log.info("── Tick ──  scenario=%s", scenario)

            # Staleness guard — fires if >24 h since last success.
            check_staleness(last_successful_at)

            # Generate reading via the shared service.
            # Only the four schema fields are in this dict — nothing extra.
            reading = generate_reading(scenario, args.soil_type, rng)

            success = post_reading(args.base_url, args.farm_id, reading, auth,
                                   scenario=scenario)
            if success:
                last_successful_at = datetime.now(tz=timezone.utc)

            # Advance round-robin.
            scenario_index += 1

            log.debug("Sleeping %s s …", args.interval)
            time.sleep(args.interval)

    except KeyboardInterrupt:
        log.info("Simulator stopped by user.")


if __name__ == "__main__":
    main()
