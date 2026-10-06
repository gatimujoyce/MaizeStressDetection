import argparse
import csv
import json
import os
import numpy as np
import sys
import matplotlib.pyplot as plt

def read_csv(path):
    with open(path, "r", newline="") as f:
        return list(csv.DictReader(f))

def plot_confusion_matrix(cm, class_names, out_path):
    cm = np.array(cm, dtype=int)
    row_sums = cm.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1
    cm_norm = cm.astype(float) / row_sums
    
    fig, ax = plt.subplots(figsize=(8,6))
    im = ax.imshow(cm_norm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    
    ax.set(xticks=np.arange(cm.shape[1]),
           yticks=np.arange(cm.shape[0]),
           xticklabels=class_names, yticklabels=class_names,
           ylabel='True label',
           xlabel='Predicted label')
           
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, f"{cm[i, j]}\n({cm_norm[i, j]:.2f})",
                    ha="center", va="center",
                    color="white" if cm_norm[i, j] > 0.5 else "black")
    
    fig.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()

def write_run_folder(name, metrics, preds, test_rows, class_names):
    d = os.path.join("results", "sensor", name)
    os.makedirs(d, exist_ok=True)
    
    with open(os.path.join(d, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
        
    with open(os.path.join(d, "classification_report.txt"), "w") as f:
        f.write("Classwise metrics:\n")
        recs = metrics.get("per_class", [])
        for r in recs:
            f.write(f"{r['name']}: Pre={r['precision']:.4f} Rec={r['recall']:.4f} F1={r['f1']:.4f} Sup={r['support']}\n")
    
    plot_confusion_matrix(metrics["confusion_matrix"], class_names, os.path.join(d, "confusion_matrix.png"))
    
    with open(os.path.join(d, "predictions.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["true_label", "predicted_label"])
        for r, p in zip(test_rows, preds):
            w.writerow([r["sensor_prediction"], class_names[p]])
            
    with open(os.path.join(d, "run_info.json"), "w") as f:
        json.dump({"run_name": name, "n": len(test_rows)}, f, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-csv", type=str, required=True)
    parser.add_argument("--model-keras", type=str, required=True)
    parser.add_argument("--no-stage-model", type=str)
    parser.add_argument("--prep-json", type=str, required=True)
    parser.add_argument("--classes-json", type=str, required=True)
    parser.add_argument("--out-dir", type=str, required=True)
    parser.add_argument("--seeds-summary", type=str)
    parser.add_argument("--seeds-summary-no-stage", type=str)
    parser.add_argument("--generation-config", type=str)
    args = parser.parse_args()

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from sensor.preprocessing import transform
    from evaluation.metrics import compute_metrics
    from scripts.rule_baseline import predict_sensor_stress
    from scripts.sensor_constants import GROWTH_STAGE_WEIGHTS, SOIL_PROPERTIES, DROUGHT_THRESHOLD_PCT_FC, WATERLOG_THRESHOLD_PCT_FC, HEAT_THRESHOLD_C

    # Load TF inside main so python evaluate_sensor.py --help works quickly
    import tensorflow as tf

    test_rows = read_csv(args.test_csv)
    
    with open(args.prep_json, "r") as f:
        prep = json.load(f)
    with open(args.classes_json, "r") as f:
        class_names = json.load(f)
        
    label_to_idx = {name: i for i, name in enumerate(class_names)}
    y_test = np.array([label_to_idx[r["sensor_prediction"]] for r in test_rows], dtype=np.int32)
    soil_types = np.array([r["soil_type"] for r in test_rows])
    
    X_test_full = transform(test_rows, prep, include_growth_stage=True)
    
    model_full = tf.keras.models.load_model(args.model_keras)
    probs_full = model_full.predict(X_test_full, verbose=0)
    preds_full = probs_full.argmax(axis=1)
    
    metrics_full = compute_metrics(y_test, preds_full, probs_full, class_names)
    
    model_no_stage = None
    if args.no_stage_model and os.path.exists(args.no_stage_model):
        X_test_no_stage = transform(test_rows, prep, include_growth_stage=False)
        model_no_stage = tf.keras.models.load_model(args.no_stage_model)
        probs_ns = model_no_stage.predict(X_test_no_stage, verbose=0)
        preds_ns = probs_ns.argmax(axis=1)
        metrics_ns = compute_metrics(y_test, preds_ns, probs_ns, class_names)
    
    preds_baseline_idx = []
    probs_baseline = []
    
    for row in test_rows:
        pred_str = predict_sensor_stress(float(row["soil_moisture"]), float(row["temperature_c"]), row["soil_type"])
        p_idx = label_to_idx[pred_str]
        
        preds_baseline_idx.append(p_idx)
        pr = [0.0]*len(class_names)
        pr[p_idx] = 1.0
        probs_baseline.append(pr)
        
    preds_baseline_idx = np.array(preds_baseline_idx, dtype=np.int32)
    probs_baseline = np.array(probs_baseline, dtype=np.float32)
    metrics_baseline = compute_metrics(y_test, preds_baseline_idx, probs_baseline, class_names)

    def evaluate_per_soil(metrics, preds):
        soil_acc = {}
        for st in prep["soil_types"]:
            mask = (soil_types == st)
            if mask.sum() > 0:
                acc = np.mean(y_test[mask] == preds[mask])
                soil_acc[st] = float(acc)
        metrics["per_soil_accuracy"] = soil_acc

    evaluate_per_soil(metrics_full, preds_full)
    evaluate_per_soil(metrics_baseline, preds_baseline_idx)
    if model_no_stage:
        evaluate_per_soil(metrics_ns, preds_ns)
        
    os.makedirs(args.out_dir, exist_ok=True)
    
    write_run_folder("full_network", metrics_full, preds_full, test_rows, class_names)
    write_run_folder("baseline", metrics_baseline, preds_baseline_idx, test_rows, class_names)
    if model_no_stage:
        write_run_folder("no_stage_network", metrics_ns, preds_ns, test_rows, class_names)

    def load_j(p):
        if p and os.path.exists(p):
            with open(p, "r") as fh:
                return json.load(fh)
        return {}

    sum_full = load_j(args.seeds_summary)
    sum_ns = load_j(args.seeds_summary_no_stage)
    gen = load_j(args.generation_config)
    
    f_acc_str = f"{sum_full.get('mean_test_accuracy', 0):.4f} +/- {sum_full.get('std_test_accuracy', 0):.4f}" if sum_full else f"{metrics_full['accuracy']:.4f}"
    ns_acc_str = f"{sum_ns.get('mean_test_accuracy', 0):.4f} +/- {sum_ns.get('std_test_accuracy', 0):.4f}" if sum_ns else (f"{metrics_ns['accuracy']:.4f}" if model_no_stage else "N/A")
    
    f_del_b = metrics_full['accuracy'] - metrics_baseline['accuracy']
    n_del_f = (metrics_ns['accuracy'] - metrics_full['accuracy']) if model_no_stage else 0.0

    comp_content = f"""# Model Comparison

| Metric | Baseline | Full Network | No Stage Network |
|---|---|---|---|
| Accuracy | {metrics_baseline['accuracy']:.4f} | {f_acc_str} | {ns_acc_str} |
| Full - Baseline Delta | | {f_del_b:.4f} | |
| No-Stage - Full Delta | | | {n_del_f:.4f} |
"""
    with open(os.path.join(args.out_dir, "comparison.md"), "w") as f:
        f.write(comp_content)

    f_std = sum_full.get("std_test_accuracy", 0.0) if sum_full else 0.0
    val_bl = gen.get("Validation_Baseline_Accuracy", "N/A")
    test_bl = gen.get("Test_Baseline_Accuracy", "N/A")
    ovr = gen.get("OVERLAP_SCALE", "N/A")

    d_bl_str = "Network difference to baseline is larger than seed-to-seed standard deviation." if abs(f_del_b) > f_std else "Network difference to baseline is within seed-to-seed variation."
    d_ns_str = "No-stage network difference to full network is larger than seed-to-seed standard deviation." if model_no_stage and abs(n_del_f) > f_std else ("No-stage network difference to full network is within seed-to-seed variation." if model_no_stage else "")

    card_content = f"""# Sensor Classifier Model Card

## Data Description
Simulated synthetic data. Classes: {", ".join(class_names)}.
Includes soil types ({", ".join(prep["soil_types"])}) and growth stages ({", ".join(prep["growth_stages"])}).

Growth Stage Biases:
{json.dumps(GROWTH_STAGE_WEIGHTS, indent=2)}

## Rule-Based Precedence Constraints
1. Waterlogging: > {WATERLOG_THRESHOLD_PCT_FC}% Field Capacity
2. Drought: < {DROUGHT_THRESHOLD_PCT_FC}% Field Capacity
3. Heat: >= {HEAT_THRESHOLD_C} C
4. Normal otherwise.

## Performance Validation
OVERLAP_SCALE: {ovr}
Validation Baseline Accuracy: {val_bl}
Test Baseline Accuracy: {test_bl}

### Results
Full Network Accuracy: {metrics_full['accuracy']:.4f}
Baseline Accuracy: {metrics_baseline['accuracy']:.4f}
{d_bl_str}
{d_ns_str}

## Limitations
- All data is strictly simulated. The network is not validated on real sensor fields mappings.
- For loam, silt loam and clay, the waterlogging band (110% of field capacity up to saturation, about 112-116%) is narrow, so many waterlogging samples sit clamped at saturation value.
- Many drought samples sit at the wilting-point value.
"""
    with open(os.path.join(args.out_dir, "sensor_model_card.md"), "w") as f:
        f.write(card_content)
        
    print("Evaluation Complete. Results saved to:", args.out_dir)

if __name__ == "__main__":
    main()
