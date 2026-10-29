"""Cross-dataset check of the real pipeline on the Bangladesh maize leaf dataset (DOI 10.17632/sb4wwjs8bz.1, CC BY 4.0).

Pre-registered rules (written before the first run, do not change them after seeing results):
  * Test on RAW_Image only, every image, no sampling. Never use Augmented_Images or Converted raw Images.
  * Confidence bands are the app's: strong >= 0.80, weak 0.60-0.79, none < 0.60 (from fusion_rules.yaml).
  * Clean classes: Common_Rust, Gray_Leaf_Spot, Healthy_Leaf. Corn_Leaf_Blight is 'any blight' (any label with 'blight').
  * A disease class with recall under 70% goes into the limitations section.
  * 'Wrong at strong' (a disease photo called a different thing at 0.80 or more) is reported separately; above 10% means
    the thresholds must be reviewed and reported.
  * Bacterial_Leaf_Streak, Eyespot and Maize_Streak_Disease are unknown to the model: report how many are called a known
    disease at strong confidence (the dangerous case). No retraining before this test is reported.

Run from the repo root in the environment that has TensorFlow:
  python eval/eval_bangladesh.py --data "<...>\\RAW_Image" --ml-root <ML_ROOT>
"""
import argparse
import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

STRONG, WEAK = 0.80, 0.60
EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# folder name -> (what we expect, kind)
FOLDERS = {
    "Common_Rust": ("common_rust", "clean"),
    "Gray_Leaf_Spot": ("gray_leaf_spot", "clean"),
    "Healthy_Leaf": ("healthy", "clean"),
    "Corn_Leaf_Blight": ("blight", "family"),
    "Bacterial_Leaf_Streak": (None, "unknown"),
    "Eyespot": (None, "unknown"),
    "Maize_Streak_Disease": (None, "unknown"),
}


def band(conf):
    return "strong" if conf >= STRONG else "weak" if conf >= WEAK else "none"


def is_right(expected, label):
    if expected == "blight":
        return "blight" in label
    return label == expected


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, help="the RAW_Image folder")
    ap.add_argument("--ml-root", default=os.getenv("ML_ROOT"), help="folder holding the trained models")
    ap.add_argument("--out", default="eval/bangladesh_results.csv")
    ap.add_argument("--limit", type=int, default=0, help="only for a quick smoke test; leave 0 for the real run")
    a = ap.parse_args()
    if not a.ml_root:
        sys.exit("Give --ml-root or set ML_ROOT.")
    sys.path.insert(0, a.ml_root)
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from mlruntime.loader import load_runtime
    runtime = load_runtime(a.ml_root)

    data = Path(a.data)
    missing = [f for f in FOLDERS if not (data / f).is_dir()]
    if missing:
        sys.exit(f"Folders not found in {data}: {missing}")

    rows = []
    for folder, (expected, kind) in FOLDERS.items():
        files = sorted(p for p in (data / folder).rglob("*") if p.suffix.lower() in EXTS)
        if a.limit:
            files = files[: a.limit]
        print(f"{folder}: {len(files)} images", flush=True)
        for i, path in enumerate(files, 1):
            try:
                r = runtime.run(path.read_bytes())
            except Exception as exc:  # an unreadable file is reported, not hidden
                rows.append({"folder": folder, "file": path.name, "kind": kind, "outcome": "error", "label": "",
                             "conf": "", "band": "", "gate_ok": "", "nutrient": "", "nutrient_conf": "", "note": str(exc)[:80]})
                continue
            d, n, g = r["disease"], r["nutrient"], r["gate"]
            if not r["quality"]["ok"]:
                outcome = "quality_failed"
            elif g and not g["ok"]:
                outcome = "gate_rejected"
            else:
                outcome = "assessed"
            rows.append({"folder": folder, "file": path.name, "kind": kind, "outcome": outcome,
                         "label": d["label"] if d else "", "conf": f"{d['confidence']:.4f}" if d else "",
                         "band": band(d["confidence"]) if d else "", "gate_ok": g["ok"] if g else "",
                         "nutrient": n["label"] if n else "", "nutrient_conf": f"{n['confidence']:.4f}" if n else "",
                         "note": ",".join(r["quality"]["issues"])})
            if i % 50 == 0:
                print(f"  {i}/{len(files)}", flush=True)

    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    summarise(rows)
    print(f"\nPer-image results saved to {a.out}")


def pct(n, d):
    return f"{100 * n / d:.0f}%" if d else "n/a"


def summarise(rows):
    by = defaultdict(list)
    for r in rows:
        by[r["folder"]].append(r)
    print("\n=== Photos the app would not assess ===")
    for folder, rs in by.items():
        c = Counter(r["outcome"] for r in rs)
        print(f"{folder:24} total {len(rs):4}  assessed {c['assessed']:4}  quality_failed {c['quality_failed']:3}  "
              f"gate_rejected {c['gate_rejected']:3}  error {c['error']:3}")

    print("\n=== Known classes (assessed photos only) ===")
    wrong_strong = n_disease = 0
    for folder, (expected, kind) in FOLDERS.items():
        if kind == "unknown":
            continue
        rs = [r for r in by[folder] if r["outcome"] == "assessed"]
        if not rs:
            continue
        right = [r for r in rs if is_right(expected, r["label"])]
        bands = Counter((r["band"], is_right(expected, r["label"])) for r in rs)
        print(f"\n{folder} (expected '{expected}'): {len(right)}/{len(rs)} right = recall {pct(len(right), len(rs))}")
        print(f"   right:  strong {bands[('strong', True)]}, weak {bands[('weak', True)]}, none {bands[('none', True)]}")
        print(f"   wrong:  strong {bands[('strong', False)]}, weak {bands[('weak', False)]}, none {bands[('none', False)]}")
        print("   predicted as:", dict(Counter(r["label"] for r in rs).most_common()))
        if expected != "healthy":
            wrong_strong += bands[("strong", False)]
            n_disease += len(rs)
    print(f"\nDisease photos called something else at strong confidence: {wrong_strong}/{n_disease} = {pct(wrong_strong, n_disease)}"
          "  (rule: above 10% means the thresholds need review)")

    print("\n=== Diseases the model does not know ===")
    for folder, (_, kind) in FOLDERS.items():
        if kind != "unknown":
            continue
        rs = [r for r in by[folder] if r["outcome"] == "assessed"]
        if not rs:
            continue
        healthy = sum(1 for r in rs if r["label"] == "healthy")
        s = sum(1 for r in rs if r["label"] != "healthy" and r["band"] == "strong")
        w = sum(1 for r in rs if r["label"] != "healthy" and r["band"] == "weak")
        nn = sum(1 for r in rs if r["label"] != "healthy" and r["band"] == "none")
        print(f"{folder:24} {len(rs):4} assessed: called a known disease strong {s} ({pct(s, len(rs))}), "
              f"weak {w}, not sure {nn}; called healthy {healthy} ({pct(healthy, len(rs))})")


if __name__ == "__main__":
    main()