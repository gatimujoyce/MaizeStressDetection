"""Applies the disease-v2 rules (docs/disease_v2_rules.md) to the predictions of v1 and v2.

Inputs are the predictions.csv files written by evaluation/evaluate_images.py:
  --v1-pv / --v2-pv : PlantVillage test set
  --v1-bd / --v2-bd : Bangladesh held-out test set (data/processed/disease_v2/test_bangladesh)
Prints per-class counts and recall for both models, each rule as PASS/FAIL, and the decision. Writes
results/disease_v2_decision.json. Reads only predictions; needs no TensorFlow.
"""
import argparse
import csv
import json
import os

CLASSES = ["common_rust", "gray_leaf_spot", "healthy", "northern_leaf_blight"]
STRONG = 0.80


def load(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["confidence"] = float(r["confidence"])
    return rows


def summary(rows):
    out = {"n": len(rows), "accuracy": sum(r["true_label"] == r["predicted_label"] for r in rows) / len(rows),
           "per_class": {}}
    for c in CLASSES:
        sub = [r for r in rows if r["true_label"] == c]
        hit = sum(r["predicted_label"] == c for r in sub)
        out["per_class"][c] = {"n": len(sub), "correct": hit, "recall": hit / len(sub) if sub else None}
    rec = [v["recall"] for v in out["per_class"].values() if v["recall"] is not None]
    out["macro_recall"] = sum(rec) / len(rec)
    sick = [r for r in rows if r["true_label"] != "healthy"]
    bad = [r for r in sick if r["predicted_label"] == "healthy" and r["confidence"] >= STRONG]
    out["sick_called_healthy_strong"] = {"n_sick": len(sick), "count": len(bad),
                                         "rate": len(bad) / len(sick) if sick else 0.0}
    return out


def pct(x):
    return "  n/a" if x is None else f"{100 * x:5.1f}%"


def show(name, a, b):
    print(f"\n{name}")
    print(f"  {'class':<22}{'v1':>18}{'v2':>18}")
    for c in CLASSES:
        pa, pb = a["per_class"][c], b["per_class"][c]
        print(f"  {c:<22}{pa['correct']:>4}/{pa['n']:<4}{pct(pa['recall']):>9}{pb['correct']:>5}/{pb['n']:<4}{pct(pb['recall']):>9}")
    print(f"  {'accuracy':<22}{pct(a['accuracy']):>18}{pct(b['accuracy']):>18}")
    print(f"  {'macro recall':<22}{pct(a['macro_recall']):>18}{pct(b['macro_recall']):>18}")
    sa, sb = a["sick_called_healthy_strong"], b["sick_called_healthy_strong"]
    print(f"  {'sick->healthy >=0.80':<22}{sa['count']:>8}/{sa['n_sick']:<9}{sb['count']:>8}/{sb['n_sick']:<9}")


def main():
    ap = argparse.ArgumentParser()
    for k in ("v1-pv", "v2-pv", "v1-bd", "v2-bd"):
        ap.add_argument(f"--{k}", required=True)
    ap.add_argument("--out", default="results/disease_v2_decision.json")
    args = ap.parse_args()

    s = {k: summary(load(getattr(args, k.replace("-", "_")))) for k in ("v1-pv", "v2-pv", "v1-bd", "v2-bd")}
    show("PlantVillage test", s["v1-pv"], s["v2-pv"])
    show("Bangladesh held-out test (distinct photos)", s["v1-bd"], s["v2-bd"])

    v2pv, v1bd, v2bd = s["v2-pv"], s["v1-bd"], s["v2-bd"]
    bd_rec = {c: v2bd["per_class"][c]["recall"] for c in CLASSES if v2bd["per_class"][c]["recall"] is not None}
    rules = {
        "1 PlantVillage accuracy >= 87.2% and healthy recall >= 95%":
            v2pv["accuracy"] >= 0.872 and v2pv["per_class"]["healthy"]["recall"] >= 0.95,
        "2 Bangladesh macro recall >= 70% and no class below 50%":
            v2bd["macro_recall"] >= 0.70 and min(bd_rec.values()) >= 0.50,
        "3 Bangladesh: v2 not lower than v1 in any class, and higher macro recall":
            all(v2bd["per_class"][c]["recall"] >= v1bd["per_class"][c]["recall"] for c in bd_rec)
            and v2bd["macro_recall"] > v1bd["macro_recall"],
        "4 Sick Bangladesh photos called healthy at >= 0.80: at most 5%":
            v2bd["sick_called_healthy_strong"]["rate"] <= 0.05,
    }
    print("\nRules")
    for k, v in rules.items():
        print(f"  {'PASS' if v else 'FAIL'}  {k}")
    decision = "v2 replaces v1" if all(rules.values()) else "v1 stays; v2 reported as an attempted improvement"
    print(f"\nDecision: {decision}")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"inputs": vars(args), "summaries": s, "rules": rules, "decision": decision}, fh, indent=2)
    print(f"Written: {args.out}")


if __name__ == "__main__":
    main()
