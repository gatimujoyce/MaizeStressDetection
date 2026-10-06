import argparse
import csv
import json
import os
import numpy as np
import sys

def read_csv(path):
    with open(path, "r", newline="") as f:
        return list(csv.DictReader(f))

def main():
    parser = argparse.ArgumentParser(description="Train Sensor Classification Model")
    parser.add_argument("--data-dir", type=str, required=True, help="Directory with train.csv, val.csv, test.csv")
    parser.add_argument("--out-dir", type=str, required=True, help="Directory to save model artifacts")
    parser.add_argument("--seeds", type=int, default=5, help="Number of random seeds (starting from 42) to run")
    parser.add_argument("--no-growth-stage", action="store_true", help="Exclude growth stage feature from input")
    args = parser.parse_args()

    import tensorflow as tf
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import Dense, Input
    from tensorflow.keras.callbacks import EarlyStopping

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from sensor.preprocessing import fit_preprocessing, transform
    from evaluation.metrics import compute_metrics

    train_rows = read_csv(os.path.join(args.data_dir, "train.csv"))
    val_rows = read_csv(os.path.join(args.data_dir, "val.csv"))
    test_rows = read_csv(os.path.join(args.data_dir, "test.csv"))

    prep = fit_preprocessing(train_rows)
    
    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "sensor_preprocessing.json"), "w") as f:
        json.dump(prep, f, indent=2)

    all_labels = set(r["sensor_prediction"] for r in train_rows)
    class_names = sorted(list(all_labels))
    with open(os.path.join(args.out_dir, "class_names.json"), "w") as f:
        json.dump(class_names, f, indent=2)

    label_to_idx = {name: i for i, name in enumerate(class_names)}
    
    y_train = np.array([label_to_idx[r["sensor_prediction"]] for r in train_rows], dtype=np.int32)
    y_val = np.array([label_to_idx[r["sensor_prediction"]] for r in val_rows], dtype=np.int32)
    y_test = np.array([label_to_idx[r["sensor_prediction"]] for r in test_rows], dtype=np.int32)

    include_gs = not args.no_growth_stage
    X_train = transform(train_rows, prep, include_growth_stage=include_gs)
    X_val = transform(val_rows, prep, include_growth_stage=include_gs)
    X_test = transform(test_rows, prep, include_growth_stage=include_gs)

    best_val_loss = float("inf")
    best_seed = None
    seed_stats = []

    for idx in range(args.seeds):
        current_seed = 42 + idx
        tf.keras.utils.set_random_seed(current_seed)
        tf.config.experimental.enable_op_determinism()

        model = Sequential([
            Input(shape=(X_train.shape[1],)),
            Dense(32, activation='relu'),
            Dense(16, activation='relu'),
            Dense(len(class_names), activation='softmax')
        ])

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss='sparse_categorical_crossentropy',
            metrics=['accuracy']
        )

        es = EarlyStopping(
            monitor='val_loss',
            patience=10,
            restore_best_weights=True
        )

        history = model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val),
            batch_size=64,
            epochs=200,
            callbacks=[es],
            verbose=0
        )

        val_loss = min(history.history['val_loss'])

        test_probs = model.predict(X_test, verbose=0)
        test_preds = test_probs.argmax(axis=1)

        metrics = compute_metrics(y_test, test_preds, test_probs, class_names)
        
        seed_stats.append({
            "seed": current_seed,
            "val_loss": val_loss,
            "test_accuracy": metrics["accuracy"],
            "test_macro_f1": metrics["macro_f1"]
        })

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_seed = current_seed
            model_name = "sensor_v2_no_stage.keras" if args.no_growth_stage else "sensor_v2.keras"
            model.save(os.path.join(args.out_dir, model_name))

    accs = [s["test_accuracy"] for s in seed_stats]
    f1s = [s["test_macro_f1"] for s in seed_stats]
    
    summary = {
        "seeds": seed_stats,
        "mean_test_accuracy": float(np.mean(accs)),
        "std_test_accuracy": float(np.std(accs)),
        "mean_test_macro_f1": float(np.mean(f1s)),
        "std_test_macro_f1": float(np.std(f1s)),
        "release_seed": best_seed,
        "release_val_loss": float(best_val_loss)
    }
    
    summary_name = "seeds_summary_no_stage.json" if args.no_growth_stage else "seeds_summary.json"
    with open(os.path.join(args.out_dir, summary_name), "w") as f:
        json.dump(summary, f, indent=2)
        
if __name__ == "__main__":
    main()
