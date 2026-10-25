"""Calibrates the photo quality thresholds from the disease validation images and reports once on the test images.
Rule (fixed before any number was seen): dark_mean = 1st percentile and bright_mean = 99th percentile of the mean
grey level over validation originals; blur_laplacian_var = the highest value with at most 1% of validation originals
below it, capped at the 5th percentile of the blur-degraded (Gaussian radius 2) validation copies.
Degradations are synthetic and stand in for real phone failures only roughly. Test images are used only for the report.
Writes results/quality/calibration.json and calibration.txt; with --write-config it also updates the thresholds in
models/quality/quality_rules.yaml (status stays 'provisional')."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from quality.photo_quality import check_photo, laplacian_variance, load_rules

DATA = REPO / "data" / "processed" / "plantvillage_maize"
EXTS = (".jpg", ".jpeg", ".png")
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def files(split):
    return sorted(p for p in (DATA / split).rglob("*") if p.suffix.lower() in EXTS)


def blur(im, r):
    return im.filter(ImageFilter.GaussianBlur(r))


def darken(im):
    return Image.fromarray((np.asarray(im, dtype=np.float64) * 0.2).clip(0, 255).astype(np.uint8))


def glare(im):
    return Image.fromarray((np.asarray(im, dtype=np.float64) + 150).clip(0, 255).astype(np.uint8))


DEGRADATIONS = {"blur radius 2": lambda im: blur(im, 2), "blur radius 4": lambda im: blur(im, 4),
                "darkened to 20%": darken, "glare +150": glare}


def measure(path, cfg):
    q = cfg["quality"]
    with Image.open(path) as im:
        im = im.convert("RGB")
        g = im.convert("L")
        g.thumbnail((q["analysis_max_side"], q["analysis_max_side"]), Image.LANCZOS)
        arr = np.asarray(g)
        return float(arr.mean()), laplacian_variance(arr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-config", action="store_true")
    args = ap.parse_args()
    cfg = load_rules()
    val, test = files("val"), files("test")
    say(f"validation originals: {len(val)}   test originals: {len(test)}")

    means, lap_orig, lap_blur2 = [], [], []
    for p in val:
        m, v = measure(p, cfg)
        means.append(m)
        lap_orig.append(v)
        with Image.open(p) as im:
            g = blur(im.convert("RGB"), 2).convert("L")
        g.thumbnail((cfg["quality"]["analysis_max_side"],) * 2, Image.LANCZOS)
        lap_blur2.append(laplacian_variance(np.asarray(g)))
    dark, bright = float(np.percentile(means, 1)), float(np.percentile(means, 99))
    cap = float(np.percentile(lap_blur2, 5))
    one_pct = float(np.percentile(lap_orig, 1))
    blur_thr = min(one_pct, cap)
    say(f"mean grey level on validation originals: 1st percentile {dark:.1f}, 99th percentile {bright:.1f}")
    say(f"laplacian variance: originals 1st percentile {one_pct:.1f}; blur-radius-2 copies 5th percentile {cap:.1f}")
    say(f"chosen: dark_mean {dark:.1f}, bright_mean {bright:.1f}, blur_laplacian_var {blur_thr:.1f}")
    q = cfg["quality"]
    thr = {"dark_mean": round(min(dark, q["dark_mean"]) if dark < q["dark_mean"] else dark, 1),
           "bright_mean": round(bright, 1), "blur_laplacian_var": round(blur_thr, 1)}
    new = {**cfg, "quality": {**q, **thr}}

    say("\nTEST report (thresholds as chosen above; test images not used for choosing)")
    rejected, issues = 0, {}
    for p in test:
        with Image.open(p) as im:
            r = check_photo(im.convert("RGB"), new)
        if not r["ok"]:
            rejected += 1
            for i in r["issues"]:
                issues[i] = issues.get(i, 0) + 1
    say(f"originals rejected: {rejected} of {len(test)} ({100 * rejected / len(test):.2f}%)   by issue: {issues}")
    caught = {}
    for name, fn in DEGRADATIONS.items():
        n = 0
        for p in test:
            with Image.open(p) as im:
                n += 0 if check_photo(fn(im.convert("RGB")), new)["ok"] else 1
        caught[name] = n
        say(f"  {name:<18} caught {n} of {len(test)} ({100 * n / len(test):.1f}%)")
    say("The degradations are synthetic and are not real phone failures. They show whether the thresholds react at all.")

    out = REPO / "results" / "quality"
    out.mkdir(parents=True, exist_ok=True)
    (out / "calibration.json").write_text(json.dumps({
        "rule": "see the docstring of scripts/calibrate_photo_quality.py", "thresholds": thr,
        "validation_images": len(val), "test_images": len(test), "test_originals_rejected": rejected,
        "test_rejected_by_issue": issues, "test_degradations_caught": caught}, indent=2) + "\n", encoding="utf-8")
    (out / "calibration.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nwrote results/quality/calibration.json and calibration.txt")
    if args.write_config:
        import yaml
        path = REPO / "models" / "quality" / "quality_rules.yaml"
        cfg_out = yaml.safe_load(path.read_text(encoding="utf-8"))
        cfg_out["quality"].update(thr)
        header = ("# Photo quality rules, run before the gate model. PROVISIONAL: set from disease validation images\n"
                  "# by the rule in scripts/calibrate_photo_quality.py (results/quality/calibration.txt). Not validated on\n"
                  "# phone photos. min_side_px and analysis_max_side are design values, not calibrated.\n")
        path.write_text(header + yaml.safe_dump(cfg_out, sort_keys=False), encoding="utf-8")
        print("updated models/quality/quality_rules.yaml")


if __name__ == "__main__":
    main()