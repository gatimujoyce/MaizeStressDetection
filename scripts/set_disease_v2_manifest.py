"""Points the app's disease model at disease-v2 (decision of 22 Nov 2026, docs/disease_v2_rules.md).

Keeps the v1 manifest as models/core_classifier/manifest_v1.json, then rewrites models/core_classifier/manifest.json
for models/core_classifier/v2/disease_v2.keras with its real sha256 and size. Run from the repo root:
  python scripts/set_disease_v2_manifest.py
To go back to v1: copy manifest_v1.json over manifest.json and restart the backend.
"""
import hashlib
import json
import shutil
from pathlib import Path

DIR = Path("models/core_classifier")
V2 = DIR / "v2" / "disease_v2.keras"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if not V2.is_file():
        raise SystemExit(f"ERROR: {V2} not found")
    v1 = json.loads((DIR / "manifest.json").read_text(encoding="utf-8"))
    if v1.get("version") != "disease-v1":
        raise SystemExit(f"ERROR: manifest.json is {v1.get('version')!r}, expected disease-v1; nothing changed")
    names = json.loads((DIR / "v2" / "class_names.json").read_text(encoding="utf-8"))
    if names != v1["classes"]:
        raise SystemExit(f"ERROR: v2 class order {names} differs from v1 {v1['classes']}")
    run = json.loads((DIR / "v2" / "training_run.json").read_text(encoding="utf-8"))

    backup = DIR / "manifest_v1.json"
    if not backup.exists():
        shutil.copy2(DIR / "manifest.json", backup)

    v2 = dict(v1)
    v2.update({
        "file": "v2/disease_v2.keras",
        "sha256": sha256(V2),
        "bytes": V2.stat().st_size,
        "weights_location": "MyDrive/maize-project/models/core_classifier/v2/disease_v2.keras",
        "tf_version": run.get("tensorflow_version"),
        "version": "disease-v2",
        "training_data": "PlantVillage maize train/val + Bangladesh field photos (RAW_Image, 4 classes), grouped split; "
                         "data/processed/disease_v2/split_report.json",
        "evidence": [
            "results/disease_v2/disease_v2_test/metrics.json",
            "results/disease_v2/disease_v2_bdtest/metrics.json",
            "results/disease_best/disease_v1_bdtest/metrics.json",
            "results/disease_v2_decision.json",
            "docs/disease_v2_rules.md",
        ],
        "selection_note": "Pre-set rules 2 and 3 failed; v2 was adopted as a documented deviation because it beats v1 on "
                          "every overall measure on both test sets (see docs/disease_v2_rules.md, Decision).",
        "previous_version": "manifest_v1.json",
    })
    th = dict(v1["thresholds"])
    th["t_disease_validation_selected"] = None
    th["t_disease_table"] = None
    th["note"] = ("fusion applies t_disease = 0.60, the RAP bound below which a result is uncertain. For disease-v2 the "
                  "threshold was not re-selected on validation (fixed before training); 0.60 is kept.")
    v2["thresholds"] = th

    (DIR / "manifest.json").write_text(json.dumps(v2, indent=2) + "\n", encoding="utf-8")
    print(f"manifest.json now points to {v2['file']} (sha256 {v2['sha256'][:12]}..., {v2['bytes']} bytes)")
    print(f"v1 manifest kept as {backup}")


if __name__ == "__main__":
    main()
