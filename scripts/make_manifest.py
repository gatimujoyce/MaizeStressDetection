"""Writes the four model manifests plus the disease validation threshold table.
Inputs: committed evidence files and model_hashes.json (sha256 of the weights, printed in Colab).
Class names and metrics are read from committed files and never typed here. The only constants are the
RAP fusion bands, the pre-stated disease rule and the post-hoc nitrogen cap, each with its source named.
Run from anywhere; paths are relative to the repo root."""
import argparse
import csv
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

FUSION_BANDS = {"strong_min": 0.80, "weak_min": 0.60}  # RAP fusion rules: disease and nutrient share the bands
DISEASE_RULE = {"split": "validation", "grid": "0.50 to 0.95 in steps of 0.05",
                "min_accuracy_on_accepted": 0.97, "sick_accepted_as_healthy": 0}  # docs/limitations.md, disease section
DISEASE_DOCUMENTED = 0.55  # value recorded in docs/limitations.md; the script stops if it recomputes another one
DRIVE = {
    "gate": "MyDrive/maize-project/models/gate/checkpoints/gate_best.keras",
    "disease": "MyDrive/maize-project/models/core_classifier/checkpoints/disease_best.keras",
    "nutrient": "MyDrive/maize-project/models/nutrient_head/run1/nutrient_run1.keras",
    "sensor": "MyDrive/maize-project/models/sensor/v2/",
}


def read_json(rel):
    with open(REPO / rel, encoding="utf-8") as fh:
        return json.load(fh)


def write_json(rel, obj):
    path = REPO / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print("wrote", rel)


def disease_threshold(classes, healthy="healthy"):
    if healthy not in classes:
        sys.exit(f"the class '{healthy}' is not in {classes}")
    with open(REPO / "results/disease_best/disease_v1_val/predictions.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    n = len(rows)
    table, chosen = [], None
    for k in range(10, 20):
        t = round(k * 0.05, 2)
        acc = [r for r in rows if float(r["confidence"]) >= t]
        sick = sum(1 for r in acc if r["true_label"] != healthy and r["predicted_label"] == healthy)
        accuracy = round(sum(int(r["correct"]) for r in acc) / len(acc), 4) if acc else None
        row = {"threshold": t, "coverage": round(len(acc) / n, 4), "accuracy_on_accepted": accuracy,
               "sick_accepted_as_healthy": sick}
        for c in classes:
            cr = [r for r in rows if r["true_label"] == c]
            row["coverage_" + c] = round(sum(1 for r in cr if float(r["confidence"]) >= t) / len(cr), 3)
        table.append(row)
        if (chosen is None and accuracy is not None
                and accuracy >= DISEASE_RULE["min_accuracy_on_accepted"] and sick == 0):
            chosen = t
    with open(REPO / "results/disease_best/disease_v1_val/threshold_table.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(table[0].keys()))
        w.writeheader()
        w.writerows(table)
    print("wrote results/disease_best/disease_v1_val/threshold_table.csv")
    for row in table:
        print("  ", row)
    if chosen is None or abs(chosen - DISEASE_DOCUMENTED) > 1e-9:
        sys.exit(f"recomputed t_disease = {chosen}, but docs/limitations.md records {DISEASE_DOCUMENTED}. Stopping.")
    return chosen


def image_manifest(hashes, key, folder, file_name, run_info, classes_src, thresholds, evidence, version, extra=None):
    run = read_json(run_info)
    h = hashes[key]
    if h["file"] != file_name:
        sys.exit(f"{key}: the hashes file lists {h['file']}, expected {file_name}")
    if classes_src is None:
        classes = run["class_names"]
        write_json(f"{folder}/class_names.json", classes)
    else:
        classes = read_json(classes_src)
        if run["class_names"] != classes:
            sys.exit(f"{key}: class order in {run_info} differs from {classes_src}")
        dest = REPO / folder / "class_names.json"
        if (REPO / classes_src).resolve() != dest.resolve():
            shutil.copyfile(REPO / classes_src, dest)
            print("copied", classes_src, "->", f"{folder}/class_names.json")
    manifest = {
        "name": key, "task": key, "file": file_name, "sha256": h["sha256"], "bytes": h["bytes"],
        "weights_location": DRIVE[key], "tf_version": run.get("tf_version"), "enabled": True,
        "input": {"size": run["img_size"], "channels": 3, "preprocess": run["preprocess"]},
        "classes": classes, "thresholds": thresholds, "evidence": evidence, "version": version,
    }
    if extra:
        manifest.update(extra)
    write_json(f"{folder}/manifest.json", manifest)
    return manifest


def sensor_manifest(hashes):
    classes = read_json("models/mlp_sensor/class_names.json")
    if not (REPO / "models/mlp_sensor/sensor_preprocessing.json").exists():
        sys.exit("models/mlp_sensor/sensor_preprocessing.json is missing")
    full, nos = hashes["sensor_full"], hashes["sensor_no_stage"]
    run = read_json("results/sensor/full_network/run_info.json")
    manifest = {
        "name": "sensor", "task": "sensor",
        "file": full["file"], "sha256": full["sha256"], "bytes": full["bytes"],
        "no_stage_file": nos["file"], "no_stage_sha256": nos["sha256"], "no_stage_bytes": nos["bytes"],
        "weights_location": DRIVE["sensor"], "tf_version": run.get("tf_version"), "enabled": True,
        "input": {"type": "feature vector", "preprocessing_file": "sensor_preprocessing.json",
                  "use_no_stage_file_when": "growth stage is unknown"},
        "classes": classes, "thresholds": {"decision": "argmax", "report_confidence": True},
        "data": "simulated; not validated on real sensors",
        "evidence": ["results/sensor/comparison.md", "results/sensor/sensor_model_card.md"],
        "version": "sensor-v2",
    }
    write_json("models/mlp_sensor/manifest.json", manifest)
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--hashes", required=True, help="model_hashes.json downloaded from Colab")
    args = ap.parse_args()
    with open(args.hashes, encoding="utf-8") as fh:
        hashes = json.load(fh)
    for key in ("gate", "disease", "nutrient", "sensor_full", "sensor_no_stage"):
        if key not in hashes:
            sys.exit(f"{key} is missing from {args.hashes}")
    made = []

    made.append(image_manifest(
        hashes, "gate", "models/gate", "gate_best.keras",
        "results/gate_best/gate_v1_recheck/run_info.json", None,
        {"accept_p_in_scope": None, "status": "provisional",
         "interim_rule": "argmax is in_scope, the rule behind the committed test metrics",
         "to_be_set_by": "real-world gate test (P5) and scripts/threshold_sweep.py"},
        ["results/gate_best/gate_v1_recheck/metrics.json", "docs/limitations.md"], "gate-v1"))

    d_classes = read_json("models/core_classifier/class_names.json")
    t_disease = disease_threshold(d_classes)
    made.append(image_manifest(
        hashes, "disease", "models/core_classifier", "disease_best.keras",
        "results/disease_best/disease_v1_test/run_info.json", "models/core_classifier/class_names.json",
        {"t_disease": FUSION_BANDS["weak_min"], "t_disease_validation_selected": t_disease, "t_disease_rule": DISEASE_RULE,
         "t_disease_table": "results/disease_best/disease_v1_val/threshold_table.csv",
         "fusion_bands": FUSION_BANDS,
         "note": "fusion applies t_disease, the RAP bound below which a result is uncertain. t_disease_validation_selected is the operating point chosen on the validation split by the pre-stated rule, and fusion overrides it with the stricter value"},
        ["results/disease_best/disease_v1_test/metrics.json", "results/disease_best/disease_v1_val/predictions.csv"],
        "disease-v1"))

    n_classes = read_json("models/nutrient_head/run1/class_names.json")
    if "nitrogen" not in n_classes:
        sys.exit("the class 'nitrogen' is not in the nutrient class list")
    verdict = read_json("results/nutrient_run1/nutrient_run1_test/test_decision.json")["verdict"]
    made.append(image_manifest(
        hashes, "nutrient", "models/nutrient_head", "nutrient_run1.keras",
        "results/nutrient_run1/nutrient_run1_test/run_info.json", "models/nutrient_head/run1/class_names.json",
        {"fusion_bands": FUSION_BANDS, "class_caps": {"nitrogen": "weak"},
         "class_caps_status": "post-hoc decision after the test evaluation (docs/nutrient_posthoc_findings.md); kept through submission whatever the phone photos show, because a small smoke test can reveal failures but cannot prove nitrogen detection works",
         "temperature": 1.0, "calibration_applied": False},
        ["results/nutrient_run1/nutrient_run1_test/metrics.json",
         "results/nutrient_run1/nutrient_run1_test/test_decision.json", "docs/nutrient_ship_rule.md"],
        "nutrient-v1", extra={"ship_verdict": verdict, "run_dir": "models/nutrient_head/run1"}))

    made.append(sensor_manifest(hashes))

    print("\nsummary")
    for m in made:
        print(f"  {m['name']:<10} {m['file']:<26} sha256 {m['sha256'][:12]}...  classes {m['classes']}")


if __name__ == "__main__":
    main()