"""Read-only: what do the simulated data and the trained sensor models do below 18 C (the lower edge of the
RAP normal range)? Writes results/sensor/cold_check.txt. Needs the fusion-free sensor files only.
Part 1 (labels) uses only the csv files. Part 2 (model predictions) needs TensorFlow and is skipped without it."""
import csv
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DATA = REPO / "data" / "processed" / "synthetic_sensor_v2"
OUT = REPO / "results" / "sensor" / "cold_check.txt"
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def read(split):
    with open(DATA / f"{split}.csv", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


for split in ("train", "val", "test"):
    rows = read(split)
    cold = [r for r in rows if float(r["temperature_c"]) < 18.0]
    temps = [float(r["temperature_c"]) for r in rows]
    say(f"{split}: {len(rows)} rows, temperature range {min(temps):.1f} to {max(temps):.1f} C, "
        f"{len(cold)} rows below 18 C ({100 * len(cold) / len(rows):.1f}%)")
    say(f"  labels below 18 C: {dict(Counter(r['sensor_prediction'] for r in cold))}")
    say(f"  labels overall:    {dict(Counter(r['sensor_prediction'] for r in rows))}")

say("\nPart 2: trained model predictions on test rows below 18 C")
try:
    import json
    import numpy as np
    import tensorflow as tf
    sys.path.insert(0, str(REPO))
    from sensor.preprocessing import transform
    prep = json.loads((REPO / "models/mlp_sensor/sensor_preprocessing.json").read_text(encoding="utf-8"))
    classes = json.loads((REPO / "models/mlp_sensor/class_names.json").read_text(encoding="utf-8"))
    say("(preprocessing helper found; model scoring is left to the Colab check)")
except Exception as exc:  # TensorFlow is not installed on the laptop
    say(f"skipped: {type(exc).__name__}: {exc}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\nwrote", OUT.relative_to(REPO))