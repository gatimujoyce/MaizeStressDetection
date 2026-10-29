"""Control check: run the app's real pipeline on the PlantVillage maize TEST split the models were measured on.
If the pipeline gets close to your notebook accuracy here, the pipeline is fine and the Bangladesh failure is a domain gap.
If it does not, there is a bug between the notebook and the app (preprocessing, class order, gate).

  python eval/eval_control.py --data "<...>\\plantvillage_maize\\test" --ml-root <ML_ROOT> [--per-class 100]
It prints the folder-to-class mapping first; check that it is right."""
import argparse
import os
import random
import sys
from collections import Counter
from pathlib import Path

STRONG, WEAK = 0.80, 0.60
EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def expected_for(folder):
    n = folder.lower().replace(" ", "_")
    if "healthy" in n:
        return "healthy"
    if "rust" in n:
        return "common_rust"
    if "gray" in n or "grey" in n or "cercospora" in n:
        return "gray_leaf_spot"
    if "northern" in n or "blight" in n:
        return "northern_leaf_blight"
    return None


def band(c):
    return "strong" if c >= STRONG else "weak" if c >= WEAK else "none"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--ml-root", default=os.getenv("ML_ROOT"))
    ap.add_argument("--per-class", type=int, default=100)
    a = ap.parse_args()
    if not a.ml_root:
        sys.exit("Give --ml-root or set ML_ROOT.")
    sys.path.insert(0, a.ml_root)
    from mlruntime.loader import load_runtime
    runtime = load_runtime(a.ml_root)

    folders = sorted(p for p in Path(a.data).iterdir() if p.is_dir())
    plan = [(p, expected_for(p.name)) for p in folders]
    print("Folder -> expected class")
    for p, e in plan:
        print(f"  {p.name:45} -> {e}")
    rng = random.Random(0)
    for p, exp in plan:
        if exp is None:
            print(f"\nSkipping {p.name} (could not map it)")
            continue
        files = sorted(f for f in p.rglob("*") if f.suffix.lower() in EXTS)
        if len(files) > a.per_class:
            files = rng.sample(files, a.per_class)
        preds, bands, rejected = Counter(), Counter(), 0
        for f in files:
            r = runtime.run(f.read_bytes())
            if r["gate"] and not r["gate"]["ok"]:
                rejected += 1
                continue
            d = r["disease"]
            if not d:
                continue
            preds[d["label"]] += 1
            bands[(band(d["confidence"]), d["label"] == exp)] += 1
        n = sum(preds.values())
        right = preds[exp]
        print(f"\n{p.name} (expected '{exp}'): {right}/{n} right = {100 * right / n:.0f}%  [gate rejected {rejected} of {len(files)}]"
              if n else f"\n{p.name}: nothing assessed (gate rejected {rejected})")
        print("   predicted as:", dict(preds.most_common()))
        print(f"   right: strong {bands[('strong', True)]}, weak {bands[('weak', True)]}, none {bands[('none', True)]};"
              f"  wrong: strong {bands[('strong', False)]}, weak {bands[('weak', False)]}, none {bands[('none', False)]}")


if __name__ == "__main__":
    main()
