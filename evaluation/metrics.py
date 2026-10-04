"""
evaluation.metrics
~~~~~~~~~~~~~~~~~~
Pure-Python metric functions.  Dependencies: numpy, scikit-learn only.
No TensorFlow anywhere in this module.

All returned values are plain Python scalars / lists / dicts — never
numpy generics — so the output can be inserted directly into a database
JSONB column or written with json.dump() without a custom encoder.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_python(obj: Any) -> Any:
    """Recursively convert numpy scalars / arrays to plain Python types."""
    if isinstance(obj, dict):
        return {k: _to_python(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_python(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def _safe_div(numerator: float, denominator: float) -> float | None:
    """Return numerator / denominator, or None when denominator is 0."""
    if denominator == 0:
        return None
    return float(numerator / denominator)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_metrics(
    y_true: list | np.ndarray,
    y_pred: list | np.ndarray,
    probs: list | np.ndarray,
    class_names: list[str],
) -> dict:
    """Compute the full evaluation metric bundle for a classification run.

    Args:
        y_true:      1-D array of integer true class indices.
        y_pred:      1-D array of integer predicted class indices.
        probs:       2-D array, shape (n, num_classes), softmax probabilities.
        class_names: Ordered list of class name strings; index i ↔ class i.

    Returns:
        Plain-Python dict (no numpy types) with keys:
            n, accuracy,
            macro_precision, macro_recall, macro_f1,
            weighted_precision, weighted_recall, weighted_f1,
            per_class  (list of dicts: name, precision, recall, f1, support),
            confusion_matrix  (2-D list, rows=true, cols=predicted),
            confidence_analysis  (list of per-threshold dicts),
            mean_confidence_correct,
            mean_confidence_incorrect.
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    probs  = np.asarray(probs,  dtype=float)

    n = len(y_true)
    labels = list(range(len(class_names)))

    # --- Aggregate scores ---------------------------------------------------
    acc = float(accuracy_score(y_true, y_pred))

    macro_p, macro_r, macro_f, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", labels=labels, zero_division=0
    )
    wt_p, wt_r, wt_f, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", labels=labels, zero_division=0
    )

    # --- Per-class scores ---------------------------------------------------
    per_p, per_r, per_f, per_s = precision_recall_fscore_support(
        y_true, y_pred, average=None, labels=labels, zero_division=0
    )
    per_class = [
        {
            "name":      name,
            "precision": float(per_p[i]),
            "recall":    float(per_r[i]),
            "f1":        float(per_f[i]),
            "support":   int(per_s[i]),
        }
        for i, name in enumerate(class_names)
    ]

    # --- Confusion matrix ---------------------------------------------------
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    # --- Confidence analysis ------------------------------------------------
    max_prob = probs.max(axis=1)          # shape (n,)
    correct  = (y_true == y_pred)        # bool array

    confidence_thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    conf_analysis = []
    for t in confidence_thresholds:
        accepted_mask = max_prob >= t
        accepted_n   = int(accepted_mask.sum())
        deferred_n   = n - accepted_n
        if accepted_n > 0:
            acc_accepted: float | None = float(correct[accepted_mask].mean())
        else:
            acc_accepted = None
        conf_analysis.append(
            {
                "threshold":           t,
                "coverage":            float(accepted_n / n) if n else None,
                "accuracy_on_accepted": acc_accepted,
                "deferred_share":      float(deferred_n / n) if n else None,
            }
        )

    # --- Mean confidence correct / incorrect --------------------------------
    if correct.any():
        mean_conf_correct: float | None = float(max_prob[correct].mean())
    else:
        mean_conf_correct = None

    if (~correct).any():
        mean_conf_incorrect: float | None = float(max_prob[~correct].mean())
    else:
        mean_conf_incorrect = None

    result = {
        "n":                        n,
        "accuracy":                 acc,
        "macro_precision":          float(macro_p),
        "macro_recall":             float(macro_r),
        "macro_f1":                 float(macro_f),
        "weighted_precision":       float(wt_p),
        "weighted_recall":          float(wt_r),
        "weighted_f1":              float(wt_f),
        "per_class":                per_class,
        "confusion_matrix":         cm.tolist(),
        "confidence_analysis":      conf_analysis,
        "mean_confidence_correct":  mean_conf_correct,
        "mean_confidence_incorrect": mean_conf_incorrect,
    }
    # Guarantee no numpy types escape
    return _to_python(result)


def task_extras(
    task: str,
    cm: list[list[int]],
    class_names: list[str],
    *,
    healthy_class_name: str = "healthy",
    out_of_scope_class_name: str = "out_of_scope",
    in_scope_class_name: str = "in_scope",
) -> dict:
    """Compute task-specific extra metrics from the confusion matrix.

    Args:
        task:       One of "disease", "gate", "nutrient", "sensor".
        cm:         2-D list (rows=true, cols=predicted), as returned by
                    compute_metrics["confusion_matrix"].
        class_names: Ordered list of class names; index i ↔ row/col i.
        healthy_class_name:       Name of the healthy class (disease task).
        out_of_scope_class_name:  Name of the out-of-scope / reject class
                                  (gate task).
        in_scope_class_name:      Name of the in-scope / accept class
                                  (gate task).

    Returns:
        Plain-Python dict.  Empty dict for "sensor".

    Raises:
        ValueError: task is unknown, or a required class name is not in
                    class_names.
        ValueError: task is "sensor" with no extras — callers should just
                    expect {}.
    """
    cm_arr = np.array(cm, dtype=int)
    valid_tasks = {"disease", "gate", "nutrient", "sensor"}
    if task not in valid_tasks:
        raise ValueError(
            f"Unknown task {task!r}.  Choose from {sorted(valid_tasks)}."
        )

    def _index(name: str) -> int:
        try:
            return class_names.index(name)
        except ValueError:
            raise ValueError(
                f"Required class {name!r} not found in class_names {class_names}. "
                f"Pass the correct name via the appropriate keyword argument."
            )

    # -----------------------------------------------------------------------
    if task == "sensor":
        return {}

    # -----------------------------------------------------------------------
    if task == "disease":
        h_idx = _index(healthy_class_name)
        non_healthy_true = np.delete(cm_arr, h_idx, axis=0)   # rows not healthy

        # true non-healthy predicted as healthy
        total_non_healthy = int(non_healthy_true.sum())
        called_healthy    = int(non_healthy_true[:, h_idx].sum())
        diseased_called_healthy_rate = _safe_div(called_healthy, total_non_healthy)

        # true healthy predicted as anything else
        healthy_row     = cm_arr[h_idx]
        total_healthy   = int(healthy_row.sum())
        called_diseased = int(total_healthy - healthy_row[h_idx])
        healthy_called_diseased_rate = _safe_div(called_diseased, total_healthy)

        return _to_python(
            {
                "diseased_called_healthy_rate": diseased_called_healthy_rate,
                "healthy_called_diseased_rate": healthy_called_diseased_rate,
            }
        )

    # -----------------------------------------------------------------------
    if task == "gate":
        oos_idx = _index(out_of_scope_class_name)
        ins_idx = _index(in_scope_class_name)

        # Per non-in-scope class: share predicted as out_of_scope
        per_class_rejection = {}
        oos_true_total  = 0
        oos_rejected    = 0
        for i, name in enumerate(class_names):
            if i == ins_idx:
                continue
            row_sum = int(cm_arr[i].sum())
            rejected_count = int(cm_arr[i, oos_idx])
            per_class_rejection[name] = _safe_div(rejected_count, row_sum)
            oos_true_total  += row_sum
            oos_rejected    += rejected_count

        aggregate_oos_rejected_rate = _safe_div(oos_rejected, oos_true_total)

        # in-scope wrongly rejected
        ins_row         = cm_arr[ins_idx]
        total_in_scope  = int(ins_row.sum())
        wrongly_rejected = int(ins_row[oos_idx])
        in_scope_wrongly_rejected_rate = _safe_div(wrongly_rejected, total_in_scope)

        return _to_python(
            {
                "out_of_scope_rejected_rate":        aggregate_oos_rejected_rate,
                "out_of_scope_rejected_rate_per_class": per_class_rejection,
                "in_scope_wrongly_rejected_rate":    in_scope_wrongly_rejected_rate,
            }
        )

    # -----------------------------------------------------------------------
    if task == "nutrient":
        _, per_r, _, _ = precision_recall_fscore_support(
            # reconstruct y_true / y_pred implied by cm for this summary
            # We work directly from cm rows: recall[i] = cm[i,i] / sum(cm[i])
            np.zeros(1), np.zeros(1),   # dummy — we compute manually from cm
            average=None, zero_division=0
        )
        # Compute recall directly from the CM to avoid needing raw arrays
        recalls = []
        for i in range(len(class_names)):
            row_sum = int(cm_arr[i].sum())
            recalls.append(_safe_div(int(cm_arr[i, i]), row_sum))

        return _to_python(
            {
                "per_class_recall": [
                    {"name": name, "recall": r}
                    for name, r in zip(class_names, recalls)
                ]
            }
        )

    return {}  # unreachable
