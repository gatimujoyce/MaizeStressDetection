"""Second calibration pass for the photo quality check, run as pre-registered in docs/photo_quality_check.md.
Applies the thresholds in models/quality/quality_rules.yaml exactly as they are (no tuning) to the disease validation
and test images, with and without synthetic degradations (blur radius 2 and 4, darkened to 20%, glare +150).
The blur decision is made on the VALIDATION split only: the limit stays only if it rejects at most 2% of originals
for blur and catches at least 80% of the blur-radius-4 copies. Test is reported next to it and is not used to decide.
Writes results/quality/pass2.json and pass2.txt. Does not modify any config; it only reports what the config would need."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from quality.photo_quality import check_photo, load_rules

DATA = REPO / "data" / "processed" / "plantvillage_maize"
EXTS = (".jpg", ".jpeg", ".png")
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def files(split):
    return sorted(p for p in (DATA / split).rglob("*") if p.suffix.lower() in EXTS)


def darken(im):
    return Image.fromarray((np.asarray(im, dtype=np.float64) * 0.2).clip(0, 255).astype(np.uint8))


def glare(im):
    return Image.fromarray((np.asarray(im, dtype=np.float64) + 150).clip(0, 255).astype(np.uint8))


DEGRADATIONS = {
    "blur radius 2": lambda im: im.filter(ImageFilter.GaussianBlur(2)),
    "blur radius 4": lambda im: im.filter(ImageFilter.GaussianBlur(4)),
    "darkened to 20%": darken,
    "glare +150": glare,
}
EXPECT = {"blur radius 2": "blurry", "blur radius 4": "blurry", "darkened to 20%": "too_dark", "glare +150": "too_bright"}


def run(split, cfg):
    paths = files(split)
    n = len(paths)
    rej, by_issue, caught, caught_by_expected = 0, {}, {k: 0 for k in DEGRADATIONS}, {k: 0 for k in DEGRADATIONS}
    for p in paths:
        with Image.open(p) as im:
            im = im.convert("RGB")
            r = check_photo(im, cfg)
            if not r["ok"]:
                rej += 1
            for i in r["issues"]:
                by_issue[i] = by_issue.get(i, 0) + 1
            for name, fn in DEGRADATIONS.items():
                rd = check_photo(fn(im), cfg)
                caught[name] += 0 if rd["ok"] else 1
                caught_by_expected[name] += 1 if EXPECT[name] in rd["issues"] else 0
    return {"n": n, "originals_rejected": rej, "by_issue": by_issue, "caught": caught,
            "caught_for_expected_reason": caught_by_expected}


def report(title, res):
    n = res["n"]
    say(f"\n{title} ({n} images)")
    say(f"  originals rejected: {res['originals_rejected']} ({100 * res['originals_rejected'] / n:.2f}%)   by issue: {res['by_issue']}")
    for name in DEGRADATIONS:
        say(f"  {name:<18} caught {res['caught'][name]:>4} ({100 * res['caught'][name] / n:5.1f}%)   "
            f"flagged as {EXPECT[name]}: {res['caught_for_expected_reason'][name]:>4} ({100 * res['caught_for_expected_reason'][name] / n:5.1f}%)")


def main():
    cfg = load_rules()
    q = cfg["quality"]
    say("thresholds as in models/quality/quality_rules.yaml (not changed): "
        f"min_side_px {q['min_side_px']}, dark_mean {q['dark_mean']}, bright_mean {q['bright_mean']}, "
        f"blur_laplacian_var {q['blur_laplacian_var']}")
    val, test = run("val", cfg), run("test", cfg)
    report("VALIDATION (decides the blur question)", val)
    report("TEST (reported, not used to decide)", test)

    blur_orig = val["by_issue"].get("blurry", 0) / val["n"]
    blur_r4 = val["caught_for_expected_reason"]["blur radius 4"] / val["n"]
    ok_orig, ok_r4 = blur_orig <= 0.02, blur_r4 >= 0.80
    say("\nBLUR DECISION (validation only; criteria from docs/photo_quality_check.md)")
    say(f"  originals rejected for blur: {100 * blur_orig:.2f}%   (must be at most 2%)   -> {'ok' if ok_orig else 'FAILS'}")
    say(f"  radius-4 copies flagged as blurry: {100 * blur_r4:.1f}%   (must be at least 80%)   -> {'ok' if ok_r4 else 'FAILS'}")
    keep = ok_orig and ok_r4
    say("  DECISION: " + ("the blur limit stays in the config." if keep else
        "the blur check is to be switched off in the config (blur_laplacian_var: 0) and sharpness reported as not reliably measurable on this data."))
    say("Degradations are synthetic. Laplacian variance depends on resolution and content, so none of this transfers to phone photos.")

    out = REPO / "results" / "quality"
    out.mkdir(parents=True, exist_ok=True)
    (out / "pass2.json").write_text(json.dumps({"thresholds": q, "validation": val, "test": test,
        "blur_decision": {"originals_rejected_for_blur": blur_orig, "radius4_flagged_blurry": blur_r4,
                          "criteria_met": bool(keep)}}, indent=2) + "\n", encoding="utf-8")
    (out / "pass2.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nwrote results/quality/pass2.json and pass2.txt")


if __name__ == "__main__":
    main()