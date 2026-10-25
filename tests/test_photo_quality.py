import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from quality.photo_quality import check_photo, laplacian_variance, load_rules

CFG = load_rules()
BASE = np.random.default_rng(0).integers(60, 200, (512, 512, 3)).astype(np.float64)


def img(arr):
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def test_sharp_normal_photo_passes():
    r = check_photo(img(BASE), CFG)
    assert r["ok"] is True and r["issues"] == []


def test_blurred_photo_is_flagged():
    r = check_photo(img(BASE).filter(ImageFilter.GaussianBlur(10)), CFG)
    assert "blurry" in r["issues"] and "too_dark" not in r["issues"] and "too_bright" not in r["issues"]


def test_dark_photo_is_flagged():
    r = check_photo(img(BASE * 0.1), CFG)
    assert "too_dark" in r["issues"] and "too_bright" not in r["issues"]


def test_bright_photo_is_flagged():
    r = check_photo(img(BASE * 0.1 + 230), CFG)
    assert r["issues"] == ["too_bright"]


def test_small_photo_is_flagged():
    r = check_photo(img(BASE[:100, :100]), CFG)
    assert "too_small" in r["issues"]


def test_laplacian_variance_of_a_constant_image_is_zero():
    assert laplacian_variance(np.full((50, 50), 100)) == 0.0
    assert laplacian_variance(np.zeros((2, 2))) == 0.0


def test_dark_boundary():
    at = check_photo(Image.fromarray(np.full((512, 512, 3), 40, dtype=np.uint8)), CFG)
    below = check_photo(Image.fromarray(np.full((512, 512, 3), 39, dtype=np.uint8)), CFG)
    assert "too_dark" not in at["issues"] and "too_dark" in below["issues"]


def test_bright_boundary():
    at = check_photo(Image.fromarray(np.full((512, 512, 3), 225, dtype=np.uint8)), CFG)
    above = check_photo(Image.fromarray(np.full((512, 512, 3), 226, dtype=np.uint8)), CFG)
    assert "too_bright" not in at["issues"] and "too_bright" in above["issues"]


def test_non_rgb_input_is_handled():
    assert check_photo(img(BASE).convert("RGBA"), CFG)["ok"] is True


def test_config_has_every_key():
    for k in ("status", "min_side_px", "analysis_max_side", "dark_mean", "bright_mean", "blur_laplacian_var"):
        assert k in CFG["quality"]