"""Read-only: does each nutrient class look like it was captured differently?
Per class: filename styles, most common image sizes, median file size. Reads image headers only."""
import csv
import os
import re
import statistics
from collections import Counter, defaultdict

from PIL import Image

ROOT = "data/processed/nutrient_deficiency_v2"


def style(f):
    if re.match(r"IMG\d+", f, re.I):
        return "IMG camera name"
    if re.match(r"\d+_\d+_\d+\.", f):
        return "NNNN_a_b tile"
    if re.match(r"\d+_\d+\.", f):
        return "NNNN_a variant"
    return "other"


with open(f"{ROOT}/manifest.csv", newline="", encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))

stats = defaultdict(lambda: {"style": Counter(), "size": Counter(), "bytes": []})
for r in rows:
    path = os.path.join(ROOT, *r["path"].split("/"))
    s = stats[r["class"]]
    s["style"][style(os.path.basename(path))] += 1
    with Image.open(path) as im:
        s["size"][im.size] += 1
    s["bytes"].append(os.path.getsize(path))

for cls in sorted(stats):
    s = stats[cls]
    n = sum(s["style"].values())
    print(f"=== {cls}: {n} images ===")
    print("  filename styles:", dict(s["style"]))
    print("  top image sizes (width x height):", [f"{w}x{h} ({c})" for (w, h), c in s["size"].most_common(3)])
    print(f"  distinct sizes: {len(s['size'])}, median file size: {statistics.median(s['bytes']) / 1024:.1f} KB")