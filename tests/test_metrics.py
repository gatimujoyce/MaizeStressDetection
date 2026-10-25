"""
tests/test_metrics.py
~~~~~~~~~~~~~~~~~~~~~
Unit tests for evaluation.metrics — no TensorFlow required.
All inputs are small hand-crafted arrays where the correct answer is known.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

# Make evaluation/ importable regardless of cwd
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evaluation.metrics import compute_metrics, task_extras  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_probs(indices: list[int], confidence: float, n_classes: int) -> np.ndarray:
    """Build a fake probability matrix where each row has `confidence` on the
    predicted class and the remainder spread evenly across the others."""
    n = len(indices)
    probs = np.full((n, n_classes), (1 - confidence) / max(n_classes - 1, 1))
    for row, idx in enumerate(indices):
        probs[row, idx] = confidence
    return probs


# ---------------------------------------------------------------------------
# Test 1 — basic accuracy: 2 of 4 correct = 0.5
# ---------------------------------------------------------------------------

def test_accuracy_half():
    y_true = np.array([0, 1, 2, 0])
    y_pred = np.array([0, 1, 0, 1])   # indices 0 and 1 correct
    probs  = _make_probs(y_pred.tolist(), 0.8, 3)
    m = compute_metrics(y_true, y_pred, probs, ["A", "B", "C"])
    assert m["accuracy"] == pytest.approx(0.5)
    assert m["n"] == 4


# ---------------------------------------------------------------------------
# Test 2 — diseased_called_healthy_rate = 1/4 (hand-known CM)
# ---------------------------------------------------------------------------
#
# CM layout (rows=true, cols=pred), classes: ["healthy", "rust", "blight", "spot"]
#
#                  healthy  rust  blight  spot
#  true healthy  [   2       0      0      0  ]   →  total healthy = 2
#  true rust     [   1       1      0      0  ]   →  called healthy = 1
#  true blight   [   0       0      2      0  ]   →  called healthy = 0
#  true spot     [   0       0      0      2  ]   →  called healthy = 0
#
# diseased_called_healthy_rate = 1 / (2+2+2) = 1/6  ... too many diseased.
#
# Let's use a simpler CM where the answer is exactly 1/4:
#
#                  healthy  rust  blight  spot
#  true healthy  [   2       0      0      0  ]   total_healthy = 2
#  true rust     [   1       1      0      0  ]   called_healthy = 1
#  true blight   [   1       0      1      0  ]   called_healthy = 1 (total 2 so far)
#  true spot     [   2       0      0      2  ]   called_healthy = 2 (total diseased = 2+2+4=8)
#
# That gives 4/8 = 0.5 … let's just build the exact scenario desired.
#
# DESIRED: diseased_called_healthy_rate = 1/4
# => called_healthy=1, total_non_healthy=4
#
# CM (4 classes, healthy=index 0):
#   healthy row : [2, 0, 0, 0]
#   rust row    : [1, 1, 0, 0]   1 diseased called healthy
#   blight row  : [0, 0, 2, 0]
#   spot row    : [0, 0, 1, 1]
# total_non_healthy = 2+2+2 = 6  →  that gives 1/6, not 1/4.
#
# For 1/4 exactly: total non-healthy = 4, called healthy = 1
#   rust row   : [1, 1, 0, 0]   (2 samples)
#   blight row : [0, 0, 1, 0]   (1 sample)
#   spot row   : [0, 0, 0, 1]   (1 sample)
# => called_healthy = 1, total_non_healthy = 2+1+1 = 4  → 1/4 ✓
#
# healthy_called_diseased: healthy row = [2, 0, 0, 0] → 0/2 = 0.0

def test_disease_task_extras():
    class_names = ["healthy", "rust", "blight", "spot"]
    cm = [
        [2, 0, 0, 0],   # true healthy
        [1, 1, 0, 0],   # true rust     (1 called healthy)
        [0, 0, 1, 0],   # true blight
        [0, 0, 0, 1],   # true spot
    ]
    extras = task_extras("disease", cm, class_names)
    assert extras["diseased_called_healthy_rate"] == pytest.approx(1 / 4)
    assert extras["healthy_called_diseased_rate"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Test 3 — confidence_analysis: threshold coverage
# ---------------------------------------------------------------------------

def test_confidence_threshold_coverage():
    # 3 samples: first has confidence 0.95, rest 0.55
    y_true = np.array([0, 1, 1])
    y_pred = np.array([0, 1, 0])   # 2 of 3 correct
    probs  = np.array([
        [0.95, 0.05],   # high confidence, correct
        [0.45, 0.55],   # low confidence, correct
        [0.55, 0.45],   # low confidence, wrong
    ])
    m = compute_metrics(y_true, y_pred, probs, ["A", "B"])
    by_t = {entry["threshold"]: entry for entry in m["confidence_analysis"]}

    # At t=0.5: all 3 accepted (max_prob >= 0.5 for all rows)
    assert by_t[0.5]["coverage"] == pytest.approx(1.0)

    # At t=0.9: only sample 0 accepted (max_prob=0.95)
    entry_09 = by_t[0.9]
    assert entry_09["coverage"] == pytest.approx(1 / 3)
    assert entry_09["accuracy_on_accepted"] == pytest.approx(1.0)  # that one is correct
    assert entry_09["deferred_share"] == pytest.approx(2 / 3)


# ---------------------------------------------------------------------------
# Test 4 — accuracy_on_accepted is None when nothing exceeds threshold
# ---------------------------------------------------------------------------

def test_accuracy_on_accepted_none_when_no_samples():
    y_true = np.array([0, 1])
    y_pred = np.array([0, 1])
    probs  = np.array([[0.6, 0.4], [0.4, 0.6]])   # max is 0.6
    m = compute_metrics(y_true, y_pred, probs, ["A", "B"])
    by_t = {entry["threshold"]: entry for entry in m["confidence_analysis"]}
    # At t=0.9 no sample has max_prob >= 0.9
    assert by_t[0.9]["accuracy_on_accepted"] is None
    assert by_t[0.9]["deferred_share"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Test 5 — gate task_extras (Regression: rejection correctly counts anything != in_scope)
# ---------------------------------------------------------------------------
#
# classes: ["in_scope", "not_leaf", "out_of_scope"]
# CM:
#          in_s  not_leaf  oos
# in_s   [ 216     0        4  ]  → wrongly rejected = 4, total in_scope = 220
# not_leaf[  0   306        0  ]  → accurately rejected = 306
# oos    [  0     0       97  ]  → accurately rejected = 97
#
# accepted count (predicted in_scope for not_leaf/oos) = 0
# out_of_scope_rejected_rate (aggregate) = 403/403 = 1.0
# per_class: not_leaf = 1.0, oos = 1.0

def test_gate_task_extras():
    class_names = ["in_scope", "not_leaf", "out_of_scope"]
    cm = [
        [216, 0, 4],    # true in_scope
        [0, 306, 0],    # true not_leaf
        [0, 0, 97],     # true out_of_scope
    ]
    extras = task_extras(
        "gate", cm, class_names,
        out_of_scope_class_name="out_of_scope",
        in_scope_class_name="in_scope",
    )
    assert extras["in_scope_wrongly_rejected_rate"] == pytest.approx(4 / 220)
    assert extras["out_of_scope_rejected_rate"]     == pytest.approx(1.0)
    pc = extras["out_of_scope_rejected_rate_per_class"]
    assert pc["not_leaf"]     == pytest.approx(1.0)
    assert pc["out_of_scope"] == pytest.approx(1.0)
    
    assert extras["out_of_scope_accepted_count"] == 0
    pc_accepted = extras["out_of_scope_accepted_count_per_class"]
    assert pc_accepted["not_leaf"] == 0
    assert pc_accepted["out_of_scope"] == 0


def test_gate_task_extras_accepted_samples():
    class_names = ["in_scope", "not_leaf", "out_of_scope"]
    cm = [
        [216, 0, 4],    # true in_scope (4 wrongly rejected)
        [2, 304, 0],    # true not_leaf (2 wrongly accepted, predicted in_scope)
        [1, 0, 96],     # true out_of_scope (1 wrongly accepted, predicted in_scope)
    ]
    extras = task_extras(
        "gate", cm, class_names,
        out_of_scope_class_name="out_of_scope",
        in_scope_class_name="in_scope",
    )
    
    assert extras["in_scope_wrongly_rejected_rate"] == pytest.approx(4 / 220)
    
    # overall accepted = 3, overall true = 403, rejected = 400
    assert extras["out_of_scope_rejected_rate"] == pytest.approx(400 / 403)
    
    pc = extras["out_of_scope_rejected_rate_per_class"]
    assert pc["not_leaf"]     == pytest.approx(304 / 306)
    assert pc["out_of_scope"] == pytest.approx(96 / 97)
    
    assert extras["out_of_scope_accepted_count"] == 3
    pc_accepted = extras["out_of_scope_accepted_count_per_class"]
    assert pc_accepted["not_leaf"] == 2
    assert pc_accepted["out_of_scope"] == 1


# ---------------------------------------------------------------------------
# Test 6 — sensor task returns empty dict
# ---------------------------------------------------------------------------

def test_sensor_task_extras_empty():
    cm = [[3, 1], [0, 4]]
    result = task_extras("sensor", cm, ["normal", "drought"])
    assert result == {}


# ---------------------------------------------------------------------------
# Test 7 — missing required class raises ValueError
# ---------------------------------------------------------------------------

def test_missing_healthy_class_raises():
    cm = [[2, 0], [1, 1]]
    with pytest.raises(ValueError, match="healthy"):
        task_extras("disease", cm, ["rust", "blight"], healthy_class_name="healthy")


def test_missing_out_of_scope_class_raises():
    cm = [[2, 0], [1, 1]]
    with pytest.raises(ValueError, match="out_of_scope"):
        task_extras(
            "gate", cm, ["in_scope", "not_leaf"],
            out_of_scope_class_name="out_of_scope",
        )


# ---------------------------------------------------------------------------
# Test 8 — class ordering is honoured (not alphabetical)
# ---------------------------------------------------------------------------

def test_per_class_order_matches_class_names():
    # 2 classes: "z_class" (idx 0) and "a_class" (idx 1)
    # If ordering were alphabetical TF would put a_class first.
    class_names = ["z_class", "a_class"]
    y_true = np.array([0, 0, 1, 1])   # 2 z_class, 2 a_class
    y_pred = np.array([0, 1, 1, 1])   # z_class: 1 correct, 1 wrong; a_class: 2 correct
    probs  = _make_probs(y_pred.tolist(), 0.9, 2)
    m = compute_metrics(y_true, y_pred, probs, class_names)
    assert m["per_class"][0]["name"] == "z_class"
    assert m["per_class"][1]["name"] == "a_class"
    # z_class precision: predicted as z_class = 1 time, that 1 is TP → 1.0
    assert m["per_class"][0]["precision"] == pytest.approx(1.0)
    # a_class recall: 2 true, both predicted as a_class → 1.0
    assert m["per_class"][1]["recall"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Test 9 — no numpy types in compute_metrics output
# ---------------------------------------------------------------------------

def test_no_numpy_types_in_output():
    y_true = np.array([0, 1, 2, 0])
    y_pred = np.array([0, 1, 0, 2])
    probs  = _make_probs(y_pred.tolist(), 0.8, 3)
    m = compute_metrics(y_true, y_pred, probs, ["X", "Y", "Z"])

    def _check_no_numpy(obj, path="root"):
        if isinstance(obj, dict):
            for k, v in obj.items():
                _check_no_numpy(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _check_no_numpy(v, f"{path}[{i}]")
        else:
            assert not isinstance(obj, np.generic), (
                f"numpy type {type(obj)} found at {path}: {obj!r}"
            )

    _check_no_numpy(m)


# ---------------------------------------------------------------------------
# Test 10 — class with zero predictions does not crash (zero_division=0)
# ---------------------------------------------------------------------------

def test_zero_division_safe():
    # class 2 ("C") never predicted
    y_true = np.array([0, 1, 2, 0])
    y_pred = np.array([0, 1, 1, 0])   # class 2 never predicted
    probs  = np.array([
        [0.8, 0.1, 0.1],
        [0.1, 0.8, 0.1],
        [0.1, 0.8, 0.1],
        [0.8, 0.1, 0.1],
    ])
    m = compute_metrics(y_true, y_pred, probs, ["A", "B", "C"])
    # Should not raise; class C precision should be 0.0 (zero_division=0)
    c_metrics = next(p for p in m["per_class"] if p["name"] == "C")
    assert c_metrics["precision"] == pytest.approx(0.0)
    assert c_metrics["recall"]    == pytest.approx(0.0)
