"""95% bootstrap intervals from committed prediction files.
Writes results/intervals/bootstrap_intervals.json and bootstrap_intervals.txt.
Nutrient: resamples independent photo groups (group_id in results/nutrient/split_v2_manifest.csv) within each class,
          2000 resamples, seed 42, the same procedure as the single test evaluation in the notebook.
Disease:  there is no photo-group file for the disease split, so images are resampled as if independent. This
          understates the real uncertainty if the test set contains near-twin images (not checked within the test set).
Point estimates are checked against the committed metrics files, and the script stops if they differ."""
import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
N_RESAMPLES = 2000
SEED = 42
OUT_DIR = REPO / "results" / "intervals"
lines = []


def say(s=""):
    print(s)
    lines.append(s)


def read_csv(rel):
    with open(REPO / rel, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def read_json(rel):
    with open(REPO / rel, encoding="utf-8") as fh:
        return json.load(fh)


def entry(point, boot):
    point = float(point)
    return {"point": None if point != point else point,
            "lo": float(np.nanpercentile(boot, 2.5)), "hi": float(np.nanpercentile(boot, 97.5))}


def show(label, e):
    p = "n/a" if e["point"] is None else f"{e['point']:.4f}"
    say(f"  {label:<34}{p:>8}   [{e['lo']:.3f}, {e['hi']:.3f}]")


def nutrient():
    d = read_json("results/nutrient_run1/nutrient_run1_test/test_decision.json")
    classes = read_json("models/nutrient_head/run1/class_names.json")
    nd = "no_deficiency"
    prob_cols = ["prob_" + c for c in classes]
    preds = read_csv("results/nutrient_run1/nutrient_run1_test/predictions.csv")
    man = {r["path"]: r for r in read_csv("results/nutrient/split_v2_manifest.csv") if r["split"] == "test"}
    groups = {}
    for r in preds:
        key = "test/" + r["image_path"].replace("\\", "/")
        if key not in man:
            sys.exit(f"nutrient: {key} is not in the manifest test split")
        m = man[key]
        true, pred = r["true_label"], r["predicted_label"]
        if m["class"] != true:
            sys.exit(f"nutrient: {key} has class {m['class']} in the manifest but {true} in the predictions")
        conf = max(float(r[c]) for c in prob_cols)
        g = groups.setdefault(m["group_id"], {"cls": true, "n": 0, "k": 0, "n80": 0, "k80": 0, "fa": 0})
        if g["cls"] != true:
            sys.exit(f"nutrient: group {m['group_id']} holds two classes")
        ok = int(pred == true)
        g["n"] += 1
        g["k"] += ok
        if conf >= 0.80:
            g["n80"] += 1
            g["k80"] += ok
        if true == nd and pred != nd and conf >= 0.60:
            g["fa"] += 1
    if len(preds) != d["test_images"] or len(groups) != d["test_photos"]:
        sys.exit(f"nutrient: {len(preds)} images and {len(groups)} photo groups, "
                 f"but test_decision.json says {d['test_images']} and {d['test_photos']}")
    A = {}
    for c in classes:
        ids = sorted(g for g in groups if groups[g]["cls"] == c)
        A[c] = {k: np.array([groups[g][k] for g in ids]) for k in ("n", "k", "n80", "k80", "fa")}

    def compute(idx):
        rec = np.array([A[c]["k"][idx[c]].sum() / A[c]["n"][idx[c]].sum() for c in classes])
        n80 = sum(A[c]["n80"][idx[c]].sum() for c in classes)
        k80 = sum(A[c]["k80"][idx[c]].sum() for c in classes)
        fa = A[nd]["fa"][idx[nd]].sum() / A[nd]["n"][idx[nd]].sum()
        return rec, (k80 / n80 if n80 else float("nan")), fa

    rec, p80, fa = compute({c: np.arange(len(A[c]["n"])) for c in classes})
    n80_img = int(sum(A[c]["n80"].sum() for c in classes))
    bad = [c for i, c in enumerate(classes) if abs(rec[i] - d["class_recall"][c]) > 1e-9]
    if (bad or abs(rec.mean() - d["macro_recall"]) > 1e-9 or abs(p80 - d["precision_conf80"]) > 1e-9
            or abs(fa - d["false_alarm_conf60"]) > 1e-9 or n80_img != d["images_conf80"]):
        sys.exit(f"nutrient: point estimates differ from test_decision.json (classes: {bad}). Stopping.")
    say("nutrient: point estimates match results/nutrient_run1/nutrient_run1_test/test_decision.json")
    rng = np.random.default_rng(SEED)
    reps = [compute({c: rng.integers(0, len(A[c]["n"]), len(A[c]["n"])) for c in classes})
            for _ in range(N_RESAMPLES)]
    recs = np.array([r[0] for r in reps])
    out = {"n_images": int(len(preds)), "n_photos": int(len(groups)), "n_resamples": N_RESAMPLES, "seed": SEED,
           "unit": "independent photo groups, resampled within each class",
           "photos_per_class": {c: int(len(A[c]["n"])) for c in classes},
           "recall": {c: entry(rec[i], recs[:, i]) for i, c in enumerate(classes)},
           "macro_recall": entry(rec.mean(), recs.mean(axis=1)),
           "rule4_precision": entry(p80, np.array([r[1] for r in reps])),
           "false_alarm_conf60": entry(fa, np.array([r[2] for r in reps]))}
    say(f"\nNUTRIENT test: {out['n_images']} images, {out['n_photos']} photo groups, {N_RESAMPLES} resamples, seed {SEED}")
    for c in classes:
        show(f"recall {c} ({out['photos_per_class'][c]} photos)", out["recall"][c])
    show("macro recall", out["macro_recall"])
    show("precision at confidence >= 0.80", out["rule4_precision"])
    show("false alarm (no_deficiency, >= 0.60)", out["false_alarm_conf60"])
    return out


def disease():
    classes = read_json("models/core_classifier/class_names.json")
    metrics = read_json("results/disease_best/disease_v1_test/metrics.json")
    rows = read_csv("results/disease_best/disease_v1_test/predictions.csv")
    A = {}
    for c in classes:
        rs = [r for r in rows if r["true_label"] == c]
        A[c] = {"ok": np.array([r["predicted_label"] == c for r in rs]),
                "conf": np.array([float(r["confidence"]) for r in rs])}
    n_total = sum(len(A[c]["ok"]) for c in classes)
    if n_total != metrics["n"]:
        sys.exit(f"disease: {n_total} images, but metrics.json says {metrics['n']}")

    def compute(idx):
        rec = np.array([A[c]["ok"][idx[c]].mean() for c in classes])
        correct = sum(A[c]["ok"][idx[c]].sum() for c in classes)
        acc_n = sum((A[c]["conf"][idx[c]] >= 0.60).sum() for c in classes)
        acc_ok = sum((A[c]["ok"][idx[c]] & (A[c]["conf"][idx[c]] >= 0.60)).sum() for c in classes)
        return rec, correct / n_total, acc_n / n_total, (acc_ok / acc_n if acc_n else float("nan"))

    rec, acc, cov, acc_acc = compute({c: np.arange(len(A[c]["ok"])) for c in classes})
    by_name = {p["name"]: p["recall"] for p in metrics["per_class"]}
    if abs(acc - metrics["accuracy"]) > 1e-9 or any(abs(rec[i] - by_name[c]) > 1e-9 for i, c in enumerate(classes)):
        sys.exit("disease: accuracy or per-class recall differ from metrics.json. Stopping.")
    say("\ndisease: accuracy and per-class recall match results/disease_best/disease_v1_test/metrics.json")
    row = next(r for r in metrics["confidence_analysis"] if abs(r["threshold"] - 0.60) < 1e-9)
    same = abs(cov - row["coverage"]) < 1e-9 and abs(acc_acc - row["accuracy_on_accepted"]) < 1e-9
    say(f"disease: at confidence 0.60, coverage {cov:.4f} and accuracy on accepted {acc_acc:.4f}; metrics.json says "
        f"{row['coverage']:.4f} and {row['accuracy_on_accepted']:.4f} -> {'match' if same else 'differ (the csv holds probabilities rounded to 6 decimals)'}")
    rng = np.random.default_rng(SEED)
    reps = [compute({c: rng.integers(0, len(A[c]["ok"]), len(A[c]["ok"])) for c in classes})
            for _ in range(N_RESAMPLES)]
    recs = np.array([r[0] for r in reps])
    out = {"n_images": int(n_total), "n_resamples": N_RESAMPLES, "seed": SEED,
           "unit": "images resampled as independent, within each class (no photo-group file exists for this split)",
           "note": "These intervals treat images as independent and therefore understate the uncertainty if the test set contains near-twin images.",
           "recall": {c: entry(rec[i], recs[:, i]) for i, c in enumerate(classes)},
           "macro_recall": entry(rec.mean(), recs.mean(axis=1)),
           "accuracy": entry(acc, np.array([r[1] for r in reps])),
           "coverage_at_0_60": entry(cov, np.array([r[2] for r in reps])),
           "accuracy_on_accepted_at_0_60": entry(acc_acc, np.array([r[3] for r in reps]))}
    say(f"\nDISEASE test: {out['n_images']} images, {N_RESAMPLES} resamples, seed {SEED} (images treated as independent)")
    for c in classes:
        show(f"recall {c}", out["recall"][c])
    show("macro recall", out["macro_recall"])
    show("accuracy", out["accuracy"])
    show("coverage at confidence >= 0.60", out["coverage_at_0_60"])
    show("accuracy on accepted at 0.60", out["accuracy_on_accepted_at_0_60"])
    return out


def main():
    result = {"nutrient": nutrient(), "disease": disease()}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "bootstrap_intervals.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "bootstrap_intervals.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nwrote results/intervals/bootstrap_intervals.json and bootstrap_intervals.txt")


if __name__ == "__main__":
    main()