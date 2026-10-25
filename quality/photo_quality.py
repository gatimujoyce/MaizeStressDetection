"""Photo quality check, run before the gate model. Pure Python plus numpy and Pillow, no TensorFlow.
It judges how usable a photo is (size, brightness, sharpness), not what is in it. It cannot tell whether the
leaf fills the frame. The thresholds in models/quality/quality_rules.yaml are provisional.

check_photo(image, cfg): `image` is a PIL image already decoded and rotated by its EXIF orientation, as in the
backend path. Returns {"ok": bool, "issues": [codes], "metrics": {...}}. Issue codes, in this order:
too_small, too_dark, too_bright, blurry. A dark photo often also reads as blurry; show the first code."""
from pathlib import Path

import numpy as np
import yaml
from PIL import Image

DEFAULT_RULES = Path(__file__).resolve().parent.parent / "models" / "quality" / "quality_rules.yaml"


def load_rules(path=None):
    with open(path or DEFAULT_RULES, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def laplacian_variance(gray):
    """Variance of the 4-neighbour Laplacian of a 2-D grey array; 0.0 when the array is smaller than 3x3."""
    g = np.asarray(gray, dtype=np.float64)
    if min(g.shape) < 3:
        return 0.0
    lap = (-4.0 * g[1:-1, 1:-1] + g[:-2, 1:-1] + g[2:, 1:-1] + g[1:-1, :-2] + g[1:-1, 2:])
    return float(lap.var())


def check_photo(image, cfg):
    q = cfg["quality"]
    width, height = image.size
    gray_im = image.convert("L")
    gray_im.thumbnail((q["analysis_max_side"], q["analysis_max_side"]), Image.LANCZOS)
    gray = np.asarray(gray_im)
    mean = float(gray.mean())
    blur = laplacian_variance(gray)
    issues = []
    if min(width, height) < q["min_side_px"]:
        issues.append("too_small")
    if mean < q["dark_mean"]:
        issues.append("too_dark")
    if mean > q["bright_mean"]:
        issues.append("too_bright")
    if blur < q["blur_laplacian_var"]:
        issues.append("blurry")
    return {"ok": not issues, "issues": issues,
            "metrics": {"width": width, "height": height, "mean_gray": mean, "laplacian_var": blur}}