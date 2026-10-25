"""Sensitivity of the sensor-window thresholds (analysis only; writes results/fusion/sensor_sensitivity.csv).
Parts A and B: synthetic 24-hour windows at one sampling interval. Every weak and strong hour threshold is scaled
by 0.5 to 1.5 and the sensor status and the fused severity are compared with the unscaled configuration.
Part C: how the minimum-run rule behaves at different sampling intervals.
The windows are synthetic: the sensor data in this project is simulated and has no time structure."""
import argparse
import copy
import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from fusion.fuse import fuse, load_rules
from fusion.sensor_window import aggregate_sensor

NOW = datetime(2026, 10, 25, 12, 0, 0)
FACTORS = [0.5, 0.75, 1.0, 1.25, 1.5]
DURATIONS = [h / 2 for h in range(0, 41)]   # 0 to 20 hours in half-hour steps
FAMILIES = [  # (name, kind, class)
    ("heat_confirmed", "confirmed", "heat_stress"),
    ("heat_borderline", "borderline", "heat_stress"),
    ("drought_confirmed", "confirmed", "drought_stress"),
    ("waterlogging_confirmed", "confirmed", "waterlogging_risk"),
    ("waterlogging_borderline", "borderline", "waterlogging_risk"),
]
PLACEMENTS = ["ongoing", "cleared"]    # cleared: the run ended 2 hours before now
LEVEL = {"not_flagging": 0, "unavailable": 0, "weak": 1, "strong": 2}
CONTEXTS = {
    "images_quiet": ({"label": "healthy", "confidence": 0.95}, {"label": "no_deficiency", "confidence": 0.95}),
    "disease_weak": ({"label": "common_rust", "confidence": 0.70}, {"label": "no_deficiency", "confidence": 0.95}),
    "disease_strong": ({"label": "common_rust", "confidence": 0.90}, {"label": "no_deficiency", "confidence": 0.95}),
}


def make_readings(interval_min, flagged):
    """flagged(ago_minutes) -> dict of overrides (label / temperature_c / soil_pct_fc) or None."""
    out = []
    for k in range(1440 // interval_min):
        ago = 1440 - k * interval_min
        r = {"timestamp": NOW - timedelta(minutes=ago), "label": "normal", "temperature_c": 24.0, "soil_pct_fc": 80.0}
        extra = flagged(ago)
        if extra:
            r.update(extra)
        out.append(r)
    return out


def window(kind, cls, placement, hours, interval_min):
    lo = 0 if placement == "ongoing" else 120
    hi = lo + int(round(hours * 60))
    if kind == "confirmed":
        mark = {"label": cls}
    elif cls == "heat_stress":
        mark = {"temperature_c": 30.5}
    else:
        mark = {"soil_pct_fc": 105.0}
    return make_readings(interval_min, lambda ago: mark if lo < ago <= hi else None)


def scaled(cfg, factor):
    c = copy.deepcopy(cfg)
    for cls in c["sensor"]["hours"]:
        for k in ("weak", "strong"):
            c["sensor"]["hours"][cls][k] = cfg["sensor"]["hours"][cls][k] * factor
    return c


def severity(sensor, ctx, cfg):
    disease, nutrient = CONTEXTS[ctx]
    return fuse(True, disease, nutrient, sensor, cfg)["severity"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval-min", type=int, default=15, help="sampling interval for parts A and B")
    args = ap.parse_args()
    cfg = load_rules()
    rows, results = [], {}

    for fac in FACTORS:
        c = scaled(cfg, fac)
        for name, kind, cls in FAMILIES:
            for pl in PLACEMENTS:
                for h in DURATIONS:
                    sensor = aggregate_sensor(window(kind, cls, pl, h, args.interval_min), NOW, c)
                    sev = {ctx: severity(sensor, ctx, c) for ctx in CONTEXTS}
                    results[(fac, name, pl, h)] = (sensor["status"], sev)
                    rows.append({"interval_min": args.interval_min, "factor": fac, "family": name, "placement": pl,
                                 "hours": h, "sensor_status": sensor["status"],
                                 **{"sev_" + k: v for k, v in sev.items()}})
    base = {k[1:]: v for k, v in results.items() if k[0] == 1.0}
    total = len(base)

    print(f"A) hours of ongoing stress at which the sensor first turns weak / strong (interval {args.interval_min} min)")
    print(f"{'family':<26}" + "".join(f"{'x' + str(fac):>14}" for fac in FACTORS))
    for name, kind, cls in FAMILIES:
        cells = []
        for fac in FACTORS:
            w = next((h for h in DURATIONS if LEVEL[results[(fac, name, 'ongoing', h)][0]] >= 1), None)
            s = next((h for h in DURATIONS if LEVEL[results[(fac, name, 'ongoing', h)][0]] >= 2), None)
            cells.append(f"{w if w is not None else '-'} / {s if s is not None else '-'}")
        print(f"{name:<26}" + "".join(f"{x:>14}" for x in cells))

    print(f"\nB) windows (of {total}) whose result differs from the unscaled configuration")
    print(f"{'factor':>8}{'sensor status':>16}" + "".join(f"{('severity ' + c):>26}" for c in CONTEXTS))
    for fac in FACTORS:
        if fac == 1.0:
            continue
        ds = sum(1 for k, v in base.items() if results[(fac,) + k][0] != v[0])
        dv = {ctx: sum(1 for k, v in base.items() if results[(fac,) + k][1][ctx] != v[1][ctx]) for ctx in CONTEXTS}
        print(f"{'x' + str(fac):>8}{ds:>16}" + "".join(f"{dv[c]:>26}" for c in CONTEXTS))
    print("\n   by family, images_quiet: windows whose severity changes at x0.5 and x1.5")
    for name, kind, cls in FAMILIES:
        parts = []
        for fac in (0.5, 1.5):
            n = sum(1 for pl in PLACEMENTS for h in DURATIONS
                    if results[(fac, name, pl, h)][1]["images_quiet"] != base[(name, pl, h)][1]["images_quiet"])
            parts.append(f"x{fac}: {n}")
        print(f"   {name:<26}" + "   ".join(parts))

    print("\nC) the minimum-run rule at different sampling intervals (heat_stress label, config as written)")
    print(f"{'interval':>10}{'1 isolated reading':>22}{'8 isolated readings':>22}{'status':>10}{'2 consecutive':>16}")
    spaced = (180, 360, 540, 720, 900, 1080, 1260, 1380)
    for iv in (5, 15, 30, 60):
        def run(fn):
            a = aggregate_sensor(make_readings(iv, fn), NOW, cfg)
            return a["hours"]["heat_stress"]["confirmed"], a["status"]
        one, _ = run(lambda ago: {"label": "heat_stress"} if ago == 720 else None)
        eight, st = run(lambda ago: {"label": "heat_stress"} if ago in spaced else None)
        two, _ = run(lambda ago: {"label": "heat_stress"} if ago in (720, 720 - iv) else None)
        print(f"{str(iv) + ' min':>10}{one:>20.2f} h{eight:>20.2f} h{st:>10}{two:>14.2f} h")

    out = REPO / "results" / "fusion" / "sensor_sensitivity.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("\nwrote", out.relative_to(REPO), f"({len(rows)} rows)")


if __name__ == "__main__":
    main()