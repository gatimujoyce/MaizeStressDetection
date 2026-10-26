"""Smoke check of the real pipeline on committed disease test images. Needs a Python with TensorFlow.
Compares the disease probabilities from mlruntime with results/disease_best/disease_v1_test/predictions.csv (the same
images scored by evaluation/evaluate_images.py), then prints one full pipeline result per image and a few edge cases."""
import csv
import io
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from mlruntime.loader import load_runtime
from mlruntime.pipeline import InvalidImageError, decode_image

with open(REPO / "results/disease_best/disease_v1_test/predictions.csv", newline="", encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
pipe = load_runtime(REPO)
print("loaded; model versions:", pipe.versions, "\n")
test_dir = REPO / "data/processed/plantvillage_maize/test"
seen, picked = {}, []
for r in rows:
    if seen.get(r["true_label"], 0) < 3:
        seen[r["true_label"]] = seen.get(r["true_label"], 0) + 1
        picked.append(r)

worst, agree = 0.0, 0
for r in picked:
    content = (test_dir / r["image_path"]).read_bytes()
    probs = pipe.disease.predict(np.stack([pipe.preprocess(decode_image(content))]))[0]
    ref = np.array([float(r["prob_" + c]) for c in pipe.disease.classes])
    diff = float(np.abs(probs - ref).max())
    worst = max(worst, diff)
    label = pipe.disease.classes[int(probs.argmax())]
    agree += label == r["predicted_label"]
    out = pipe.run(content, [], "loam")
    f = out["fusion"]
    d = out["disease"]
    print(f"{r['image_path'][-44:]:<44} max diff {diff:.4f} | gate {out['gate'] and out['gate']['label']} | "
          f"disease {d and (d['label'], round(d['confidence'], 3))} | severity {f['severity']} retake {f['retake']}")
print(f"\nparity on {len(picked)} images: largest probability difference {worst:.4f}, same label as evaluation {agree}/{len(picked)}")

print("\nedge cases")
blank = io.BytesIO()
Image.new("RGB", (300, 300), (128, 128, 128)).save(blank, "JPEG")
noise = io.BytesIO()
Image.fromarray(np.random.default_rng(1).integers(0, 255, (300, 300, 3)).astype(np.uint8)).save(noise, "JPEG")
tiny = io.BytesIO()
Image.new("RGB", (80, 80), (30, 120, 30)).save(tiny, "JPEG")
for name, data in (("flat grey", blank.getvalue()), ("random noise", noise.getvalue()), ("80x80 green", tiny.getvalue())):
    o = pipe.run(data, [], "loam")
    print(f"{name:<14} quality {o['quality']['issues'] or 'ok'} | gate {o['gate'] and o['gate']['label']} | "
          f"severity {o['fusion']['severity']} retake {o['fusion']['retake']}")
try:
    pipe.run(b"junk", [], "loam")
except InvalidImageError as exc:
    print("junk bytes     ->", exc)