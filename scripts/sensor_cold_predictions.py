"""Read-only: how do the committed sensor model predictions behave on test rows below 18 C?
results/sensor/<network>/predictions.csv has only true_label and predicted_label, so rows are matched to
data/processed/synthetic_sensor_v2/test.csv by position. The script stops if the true labels do not line up
row by row. Writes results/sensor/cold_predictions.txt."""
import csv
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "sensor" / "cold_predictions.txt"
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


test = read(REPO / "data" / "processed" / "synthetic_sensor_v2" / "test.csv")
for name in ("full_network", "no_stage_network"):
    preds = read(REPO / "results" / "sensor" / name / "predictions.csv")
    if len(preds) != len(test):
        raise SystemExit(f"{name}: {len(preds)} predictions but {len(test)} test rows. Stopping.")
    off = sum(1 for t, p in zip(test, preds) if t["sensor_prediction"] != p["true_label"])
    if off:
        raise SystemExit(f"{name}: {off} rows where the true label differs from test.csv. Rows do not line up. Stopping.")
    say(f"=== {name}: rows line up with test.csv (all {len(test)} true labels match) ===")
    for title, keep in (("below 18 C", lambda t: t < 18.0), ("18 C and above", lambda t: t >= 18.0)):
        rows = [(t, p) for t, p in zip(test, preds) if keep(float(t["temperature_c"]))]
        correct = sum(1 for t, p in rows if p["predicted_label"] == p["true_label"])
        say(f"  {title}: {len(rows)} rows, accuracy {correct / len(rows):.4f} ({correct} correct)")
        if title == "below 18 C":
            say("  true label -> predicted label counts:")
            for (tl, pl), n in sorted(Counter((p["true_label"], p["predicted_label"]) for t, p in rows).items()):
                say(f"    {tl:<18} -> {pl:<18} {n}")
    say()
say("Note: only the cold rows of the test file are counted here; there are very few of them "
    "(see results/sensor/cold_check.txt), so none of this supports a conclusion about unseen cold readings.")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\nwrote", OUT.relative_to(REPO))