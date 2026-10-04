"""
evaluation/summarize_results.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Scans results/**/metrics.json and writes results/SUMMARY.md —
one Markdown table row per evaluation run.

Usage (from repo root):
    python evaluation/summarize_results.py
    python evaluation/summarize_results.py --results-dir path/to/results
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _task_extras_summary(metrics: dict) -> str:
    """Produce a short human-readable string for the task_extras cell."""
    extras: dict = metrics.get("task_extras", {})
    if not extras:
        return ""
    parts = []
    # disease
    if "diseased_called_healthy_rate" in extras:
        v = extras["diseased_called_healthy_rate"]
        s = f"{v:.3f}" if v is not None else "n/a"
        parts.append(f"dis→hlth={s}")
    if "healthy_called_diseased_rate" in extras:
        v = extras["healthy_called_diseased_rate"]
        s = f"{v:.3f}" if v is not None else "n/a"
        parts.append(f"hlth→dis={s}")
    # gate
    if "out_of_scope_rejected_rate" in extras:
        v = extras["out_of_scope_rejected_rate"]
        s = f"{v:.3f}" if v is not None else "n/a"
        parts.append(f"oos_rej={s}")
    if "in_scope_wrongly_rejected_rate" in extras:
        v = extras["in_scope_wrongly_rejected_rate"]
        s = f"{v:.3f}" if v is not None else "n/a"
        parts.append(f"ins_rej={s}")
    # nutrient
    if "per_class_recall" in extras:
        recalls = extras["per_class_recall"]
        inner = ", ".join(
            f"{r['name']}={r['recall']:.2f}" if r["recall"] is not None
            else f"{r['name']}=n/a"
            for r in recalls
        )
        parts.append(f"recalls=[{inner}]")
    return " | ".join(parts)


def _fmt(v: float | None, decimals: int = 4) -> str:
    if v is None:
        return "n/a"
    return f"{v:.{decimals}f}"


def summarize(results_dir: Path) -> None:
    metrics_files = sorted(results_dir.rglob("metrics.json"))

    if not metrics_files:
        print(f"No metrics.json files found under {results_dir}.")
        return

    rows = []
    for mf in metrics_files:
        # Expected path: results/<model>/<run-name>/metrics.json
        parts = mf.relative_to(results_dir).parts
        model_name = parts[0] if len(parts) > 1 else "unknown"
        run_name   = parts[1] if len(parts) > 2 else "unknown"

        # Load run_info if present
        run_info_path = mf.parent / "run_info.json"
        run_info: dict = {}
        if run_info_path.exists():
            with open(run_info_path) as f:
                run_info = json.load(f)

        with open(mf) as f:
            metrics = json.load(f)

        test_dir = run_info.get("test_dir", "—")
        n        = metrics.get("n", run_info.get("n", "—"))
        accuracy = metrics.get("accuracy")
        macro_f1 = metrics.get("macro_f1")
        extras_s = _task_extras_summary(metrics)

        rows.append(
            {
                "model":    model_name,
                "run":      run_name,
                "test_dir": Path(test_dir).name if test_dir != "—" else "—",
                "n":        n,
                "accuracy": _fmt(accuracy),
                "macro_f1": _fmt(macro_f1),
                "extras":   extras_s,
            }
        )

    header = "| model | run | test_set | n | accuracy | macro_f1 | task_extras |"
    sep    = "|---|---|---|---|---|---|---|"
    table_rows = [
        f"| {r['model']} | {r['run']} | {r['test_dir']} | "
        f"{r['n']} | {r['accuracy']} | {r['macro_f1']} | {r['extras']} |"
        for r in rows
    ]

    summary_path = results_dir / "SUMMARY.md"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(f"# Evaluation Summary\n\n")
        f.write(f"_Generated from {len(rows)} run(s) found in `{results_dir}/`_\n\n")
        f.write(header + "\n")
        f.write(sep + "\n")
        f.write("\n".join(table_rows) + "\n")

    print(f"Wrote {summary_path} ({len(rows)} run(s))")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Scan results/**/metrics.json and write results/SUMMARY.md."
    )
    parser.add_argument(
        "--results-dir", default="results",
        help="Root results directory (default: results/)."
    )
    args = parser.parse_args()
    summarize(Path(args.results_dir))


if __name__ == "__main__":
    main()
