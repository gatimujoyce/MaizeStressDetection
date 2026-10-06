#!/usr/bin/env python3
"""
evaluation/evaluate_images.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CLI for evaluating an image-classification model (gate, disease, nutrient).

Designed to run in Google Colab where TensorFlow is pre-installed.
TensorFlow is imported at module level intentionally — this script should
NEVER be imported by the local test suite (use metrics.py instead).

Usage example:
    python evaluation/evaluate_images.py \
        --model models/gate/gate_best.keras \
        --test-dir data/processed/triage_gate/test \
        --task gate \
        --run-name gate_v1 \
        --preprocess efficientnet
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report

# Local import works whether run from repo root or evaluation/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from evaluation.metrics import compute_metrics, task_extras  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_class_names(path: Path) -> list[str]:
    with open(path) as f:
        names = json.load(f)
    if not isinstance(names, list) or not all(isinstance(x, str) for x in names):
        raise ValueError(
            f"{path}: expected a JSON array of strings, got {type(names).__name__}."
        )
    return names


def _check_dir_vs_class_names(test_dir: Path, class_names: list[str]) -> None:
    """Abort with a clear error if directory names ≠ class names set."""
    dir_classes = sorted(
        d.name for d in test_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    )
    names_set = set(class_names)
    dirs_set  = set(dir_classes)
    if dirs_set != names_set:
        missing = dirs_set - names_set
        extra   = names_set - dirs_set
        lines   = ["ERROR: test directory class folders do not match class_names.json."]
        if missing:
            lines.append(f"  Folders present but NOT in class_names.json : {sorted(missing)}")
        if extra:
            lines.append(f"  Names in class_names.json but NOT as folders: {sorted(extra)}")
        lines.append(f"  class_names.json order: {class_names}")
        raise SystemExit("\n".join(lines))


def _build_dataset(
    test_dir: Path,
    class_names: list[str],
    img_size: int,
    batch_size: int = 32,
) -> tf.data.Dataset:
    """Build a non-shuffling dataset with class order fixed by class_names."""
    ds = tf.keras.utils.image_dataset_from_directory(
        str(test_dir),
        labels="inferred",
        label_mode="int",
        class_names=class_names,   # ← enforces our ordering, not TF's alphabetical
        image_size=(img_size, img_size),
        batch_size=batch_size,
        shuffle=False,
    )
    return ds


def _apply_preprocess(ds: tf.data.Dataset, mode: str) -> tf.data.Dataset:
    if mode == "efficientnet":
        preprocess_fn = tf.keras.applications.efficientnet.preprocess_input

        def apply(images, labels):
            return preprocess_fn(images), labels

        return ds.map(apply, num_parallel_calls=tf.data.AUTOTUNE)
    # "none" — pass through unchanged
    return ds


def _collect_predictions(model: tf.keras.Model, ds: tf.data.Dataset):
    """Run inference; return (y_true, y_pred, probs) as numpy arrays."""
    all_probs  = []
    all_labels = []
    for batch_images, batch_labels in ds:
        batch_probs = model.predict(batch_images, verbose=0)
        all_probs.append(batch_probs)
        all_labels.append(batch_labels.numpy())
    probs  = np.concatenate(all_probs,  axis=0)
    y_true = np.concatenate(all_labels, axis=0).astype(int)
    y_pred = probs.argmax(axis=1).astype(int)
    return y_true, y_pred, probs


def _collect_image_paths(test_dir: Path, class_names: list[str]) -> list[str]:
    """Return relative image paths in the same order as image_dataset_from_directory
    (sorted by class then filename, matching shuffle=False)."""
    paths = []
    for cls in class_names:
        cls_dir = test_dir / cls
        if not cls_dir.exists():
            continue
        img_files = sorted(
            p for p in cls_dir.rglob("*")
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
        )
        paths.extend(str(p.relative_to(test_dir)) for p in img_files)
    return paths


def _plot_confusion_matrix(
    cm: list[list[int]],
    class_names: list[str],
    out_path: Path,
) -> None:
    cm_arr  = np.array(cm)
    row_sum = cm_arr.sum(axis=1, keepdims=True).astype(float)
    cm_norm = np.divide(cm_arr, row_sum, where=(row_sum != 0))

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    n = len(class_names)

    for ax, data, title, fmt in [
        (axes[0], cm_arr.astype(float), "Counts",          "d"),
        (axes[1], cm_norm,               "Row-Normalised",  ".2f"),
    ]:
        im = ax.imshow(data, interpolation="nearest", cmap="Blues")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        ax.set(
            xticks=range(n),
            yticks=range(n),
            xticklabels=class_names,
            yticklabels=class_names,
            xlabel="Predicted label",
            ylabel="True label",
            title=title,
        )
        ax.xaxis.set_tick_params(rotation=45)
        thresh = data.max() / 2.0
        for i in range(n):
            for j in range(n):
                val = data[i, j]
                text = f"{int(val)}" if fmt == "d" else f"{val:.2f}"
                ax.text(j, i, text, ha="center", va="center",
                        color="white" if val > thresh else "black", fontsize=8)

    fig.suptitle("Confusion Matrix", fontsize=13, y=1.01)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def _write_predictions_csv(
    out_path: Path,
    image_paths: list[str],
    y_true: np.ndarray,
    y_pred: np.ndarray,
    probs: np.ndarray,
    class_names: list[str],
) -> None:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["image_path", "true_label", "predicted_label",
             "confidence", "second_best_label", "correct"]
        )
        for path, yt, yp, prob in zip(image_paths, y_true, y_pred, probs):
            sorted_idx  = prob.argsort()[::-1]
            top_idx     = sorted_idx[0]
            second_idx  = sorted_idx[1] if len(sorted_idx) > 1 else top_idx
            writer.writerow([
                path,
                class_names[yt],
                class_names[yp],
                f"{prob[top_idx]:.6f}",
                class_names[second_idx],
                int(yt == yp),
            ])


def _subfolder_breakdown(
    test_dir: Path,
    class_names: list[str],
    image_paths: list[str],
    y_true: np.ndarray,
    y_pred: np.ndarray,
    task: str,
    out_of_scope_idx: int | None,
) -> dict:
    """Per second-level subfolder accuracy and (gate) rejection rate."""
    # Build map: relative_image_path -> (yt, yp)
    path_to_pred = {p: (yt, yp) for p, yt, yp in zip(image_paths, y_true, y_pred)}

    subfolder_results = {}
    for cls_idx, cls in enumerate(class_names):
        cls_dir = test_dir / cls
        if not cls_dir.exists():
            continue
        for sub in sorted(d for d in cls_dir.iterdir() if d.is_dir()):
            imgs = sorted(
                p for p in sub.rglob("*")
                if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
            )
            if not imgs:
                continue
            rel_paths = [str(p.relative_to(test_dir)) for p in imgs]
            preds = [path_to_pred[rp] for rp in rel_paths if rp in path_to_pred]
            if not preds:
                continue
            yt_sub = np.array([p[0] for p in preds])
            yp_sub = np.array([p[1] for p in preds])
            n_sub = len(yt_sub)
            acc_sub = float((yt_sub == yp_sub).mean()) if n_sub else None
            entry: dict = {"class": cls, "n": n_sub, "accuracy": acc_sub}
            if task == "gate" and out_of_scope_idx is not None:
                rejected = int((yp_sub == out_of_scope_idx).sum())
                entry["rejection_rate"] = float(rejected / n_sub) if n_sub else None
            subfolder_results[f"{cls}/{sub.name}"] = entry

    return subfolder_results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Evaluate a Keras image-classification model and write "
                    "standardised evaluation artefacts."
    )
    p.add_argument("--model",       required=True, help="Path to .keras or .h5 model.")
    p.add_argument("--test-dir",    required=True, help="Root of class/image folder tree.")
    p.add_argument("--task",        required=True, choices=["disease", "gate", "nutrient"],
                   help="Model task type.")
    p.add_argument("--run-name",    required=True, help="Slug used for output folder.")
    p.add_argument("--class-names-file", default=None,
                   help="Path to class_names.json (default: class_names.json beside model).")
    p.add_argument("--preprocess", default="efficientnet",
                   choices=["efficientnet", "none"],
                   help="Preprocessing to apply before inference.")
    p.add_argument("--img-size",   type=int, default=224, help="Square image size in pixels.")
    p.add_argument("--out",        default="results", help="Root output directory.")
    p.add_argument("--breakdown-by-subfolder", action="store_true",
                   help="Also report per second-level-subfolder accuracy.")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    model_path   = Path(args.model).resolve()
    test_dir     = Path(args.test_dir).resolve()
    out_root     = Path(args.out)

    # --- Class names ---------------------------------------------------------
    if args.class_names_file:
        class_names_path = Path(args.class_names_file)
    else:
        class_names_path = model_path.parent / "class_names.json"

    if not class_names_path.exists():
        raise SystemExit(
            f"ERROR: class names file not found: {class_names_path}\n"
            f"Pass --class-names-file explicitly or place class_names.json "
            f"beside the model."
        )
    class_names = _load_class_names(class_names_path)
    print(f"Class names ({len(class_names)}): {class_names}")

    # --- Validate test dir ---------------------------------------------------
    if not test_dir.is_dir():
        raise SystemExit(f"ERROR: test directory not found: {test_dir}")
    _check_dir_vs_class_names(test_dir, class_names)

    # --- Load model ----------------------------------------------------------
    print(f"Loading model: {model_path}")
    model = tf.keras.models.load_model(str(model_path))

    # --- Build dataset -------------------------------------------------------
    ds = _build_dataset(test_dir, class_names, args.img_size)
    ds = _apply_preprocess(ds, args.preprocess)

    # --- Inference -----------------------------------------------------------
    print("Running inference …")
    y_true, y_pred, probs = _collect_predictions(model, ds)
    image_paths = _collect_image_paths(test_dir, class_names)

    n = len(y_true)
    print(f"Evaluated {n} images.")

    # --- Metrics -------------------------------------------------------------
    metrics = compute_metrics(y_true, y_pred, probs, class_names)
    cm      = metrics["confusion_matrix"]
    extras  = task_extras(args.task, cm, class_names)
    metrics["task_extras"] = extras

    # --- Output directory ----------------------------------------------------
    out_dir = out_root / model_path.stem / args.run_name
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Writing results to: {out_dir}")

    # --- metrics.json --------------------------------------------------------
    with open(out_dir / "metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    # --- classification_report.txt -------------------------------------------
    report = classification_report(
        y_true, y_pred,
        target_names=class_names,
        labels=list(range(len(class_names))),
        zero_division=0,
    )
    with open(out_dir / "classification_report.txt", "w") as f:
        f.write(report)
    print(report)

    # --- confusion_matrix.png ------------------------------------------------
    _plot_confusion_matrix(cm, class_names, out_dir / "confusion_matrix.png")

    # --- predictions.csv -----------------------------------------------------
    _write_predictions_csv(
        out_dir / "predictions.csv",
        image_paths, y_true, y_pred, probs, class_names,
    )

    # --- Subfolder breakdown -------------------------------------------------
    if args.breakdown_by_subfolder:
        oos_idx: int | None = None
        if args.task == "gate" and "out_of_scope" in class_names:
            oos_idx = class_names.index("out_of_scope")
        breakdown = _subfolder_breakdown(
            test_dir, class_names, image_paths, y_true, y_pred, args.task, oos_idx
        )
        metrics["subfolder_breakdown"] = breakdown
        # Re-write metrics.json with breakdown appended
        with open(out_dir / "metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

    # --- run_info.json -------------------------------------------------------
    run_info = {
        "model_file":   str(model_path),
        "date":         datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "test_dir":     str(test_dir),
        "n":            n,
        "tf_version":   tf.__version__,
        "class_names":  class_names,
        "task":         args.task,
        "preprocess":   args.preprocess,
        "img_size":     args.img_size,
        "run_name":     args.run_name,
    }
    with open(out_dir / "run_info.json", "w") as f:
        json.dump(run_info, f, indent=2)

    # --- Summary line --------------------------------------------------------
    print(
        f"\nDone.  accuracy={metrics['accuracy']:.4f}  "
        f"macro_f1={metrics['macro_f1']:.4f}  "
        f"n={n}"
    )
    print(f"Results: {out_dir}")


if __name__ == "__main__":
    main()
