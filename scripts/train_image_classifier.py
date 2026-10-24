import argparse
import json
import csv
import os
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import tensorflow as tf


def parse_args():
    parser = argparse.ArgumentParser(description="Train EfficientNetB0 image classifier")
    parser.add_argument("--data-dir", type=str, required=True,
                        help="Folder containing 'train/' and 'val/' subfolders")
    parser.add_argument("--out-dir", type=str, required=True,
                        help="Directory where artifacts will be saved")
    parser.add_argument("--model-name", type=str, default="disease_best",
                        help="Base name for the saved model file")
    parser.add_argument("--epochs-head", type=int, default=8,
                        help="Number of epochs for phase‑1 (head only)")
    parser.add_argument("--epochs-finetune", type=int, default=12,
                        help="Number of epochs for phase‑2 (fine‑tune)")
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Batch size for training and validation")
    parser.add_argument("--img-size", type=int, default=224,
                        help="Image height and width (square)")
    parser.add_argument("--lr-head", type=float, default=1e-3,
                        help="Learning rate for phase‑1")
    parser.add_argument("--lr-finetune", type=float, default=1e-5,
                        help="Learning rate for phase‑2")
    parser.add_argument("--unfreeze-layers", type=int, default=40,
                        help="Number of base model layers to unfreeze in phase‑2")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    return parser.parse_args()


def main():
    args = parse_args()
    tf.keras.utils.set_random_seed(args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # Load datasets
    # ---------------------------------------------------------------------
    train_path = os.path.join(args.data_dir, "train")
    val_path = os.path.join(args.data_dir, "val")

    train_ds = tf.keras.utils.image_dataset_from_directory(
        train_path,
        labels="inferred",
        label_mode="int",
        image_size=(args.img_size, args.img_size),
        batch_size=args.batch_size,
        shuffle=True,
    )
    val_ds = tf.keras.utils.image_dataset_from_directory(
        val_path,
        labels="inferred",
        label_mode="int",
        image_size=(args.img_size, args.img_size),
        batch_size=args.batch_size,
        shuffle=False,
    )

    if train_ds.class_names != val_ds.class_names:
        raise ValueError(
            "Class names differ between train and validation sets: "
            f"{train_ds.class_names} vs {val_ds.class_names}"
        )
    class_names = train_ds.class_names
    num_classes = len(class_names)

    # Save class names
    class_names_path = out_dir / "class_names.json"
    with open(class_names_path, "w", encoding="utf-8") as f:
        json.dump(class_names, f, ensure_ascii=False, indent=2)

    # ---------------------------------------------------------------------
    # Preprocessing and augmentation
    # ---------------------------------------------------------------------
    preprocess = tf.keras.applications.efficientnet.preprocess_input

    def preprocess_fn(image, label):
        return preprocess(image), label

    train_ds = train_ds.map(preprocess_fn, num_parallel_calls=tf.data.AUTOTUNE)
    val_ds = val_ds.map(preprocess_fn, num_parallel_calls=tf.data.AUTOTUNE)

    # Augmentation (train only)
    augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.1),
        tf.keras.layers.RandomZoom(0.1),
        tf.keras.layers.RandomContrast(0.1),
    ])

    def augment(image, label):
        return augmentation(image, training=True), label

    train_ds = train_ds.map(augment, num_parallel_calls=tf.data.AUTOTUNE)

    # Prefetch for performance
    train_ds = train_ds.prefetch(tf.data.AUTOTUNE)
    val_ds = val_ds.prefetch(tf.data.AUTOTUNE)

    # ---------------------------------------------------------------------
    # Compute balanced class weights
    # ---------------------------------------------------------------------
    # Gather all labels from the training dataset
    all_labels = []
    for _, labels in train_ds.unbatch():
        all_labels.append(labels.numpy())
    all_labels = np.array(all_labels)
    counts = np.bincount(all_labels, minlength=num_classes)
    total = all_labels.shape[0]
    class_weights = {i: float(total) / (num_classes * count) for i, count in enumerate(counts) if count > 0}

    # ---------------------------------------------------------------------
    # Build model
    # ---------------------------------------------------------------------
    base = tf.keras.applications.EfficientNetB0(
        include_top=False,
        weights="imagenet",
        input_shape=(args.img_size, args.img_size, 3),
    )
    base.trainable = False

    inputs = tf.keras.Input(shape=(args.img_size, args.img_size, 3))
    x = base(inputs, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)

    # ---------------------------------------------------------------------
    # Phase 1 – train head only
    # ---------------------------------------------------------------------
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=args.lr_head),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    checkpoint_path = str(out_dir / f"{args.model_name}.keras")
    callbacks_phase1 = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
        ),
        tf.keras.callbacks.EarlyStopping(monitor="val_accuracy", mode="max", patience=4, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(patience=2),
    ]
    history1 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs_head,
        class_weight=class_weights,
        callbacks=callbacks_phase1,
        verbose=2,
    )
    best_val_acc_phase1 = max(history1.history.get("val_accuracy", [0]))

    # ---------------------------------------------------------------------
    # Phase 2 – fine‑tune last N layers (excluding BatchNormalization)
    # ---------------------------------------------------------------------
    # Make the base trainable at model level, freeze everything, then unfreeze the last N layers
    base.trainable = True
    for layer in base.layers:
        layer.trainable = False
    layers_to_unfreeze = base.layers[-args.unfreeze_layers:] if args.unfreeze_layers > 0 else []
    for layer in layers_to_unfreeze:
        if not isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = True
    n_trainable_weights = len(model.trainable_weights)
    print(f"Phase 2: trainable weight tensors in model: {n_trainable_weights}")

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=args.lr_finetune),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    callbacks_phase2 = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=checkpoint_path,
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
            initial_value_threshold=best_val_acc_phase1,
        ),
        tf.keras.callbacks.EarlyStopping(monitor="val_accuracy", mode="max", patience=4, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(patience=2),
    ]
    history2 = model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=args.epochs_finetune,
        class_weight=class_weights,
        callbacks=callbacks_phase2,
        verbose=2,
    )

    # ---------------------------------------------------------------------
    # Combine histories and write CSV
    # ---------------------------------------------------------------------
    combined = []
    # Phase 1
    for epoch_idx, (loss, acc, val_loss, val_acc) in enumerate(
        zip(
            history1.history.get("loss", []),
            history1.history.get("accuracy", []),
            history1.history.get("val_loss", []),
            history1.history.get("val_accuracy", []),
        ),
        start=1,
    ):
        combined.append([epoch_idx, 1, loss, acc, val_loss, val_acc])
    # Phase 2 (epoch numbers continue)
    start_epoch = len(combined) + 1
    for i, (loss, acc, val_loss, val_acc) in enumerate(
        zip(
            history2.history.get("loss", []),
            history2.history.get("accuracy", []),
            history2.history.get("val_loss", []),
            history2.history.get("val_accuracy", []),
        ),
        start=start_epoch,
    ):
        combined.append([i, 2, loss, acc, val_loss, val_acc])

    csv_path = out_dir / "history.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "phase", "loss", "accuracy", "val_loss", "val_accuracy"])
        writer.writerows(combined)

    # ---------------------------------------------------------------------
    # Write training run metadata
    # ---------------------------------------------------------------------
    # Count images per class for train and val
    def count_images(split_path):
        counts = {}
        for class_name in class_names:
            class_dir = os.path.join(split_path, class_name)
            if os.path.isdir(class_dir):
                counts[class_name] = len([f for f in os.listdir(class_dir) if os.path.isfile(os.path.join(class_dir, f))])
            else:
                counts[class_name] = 0
        return counts

    train_counts = count_images(train_path)
    val_counts = count_images(val_path)

    run_info = {
        "model_name": args.model_name,
        "data_dir": args.data_dir,
        "out_dir": str(out_dir),
        "class_names": class_names,
        "train_counts": train_counts,
        "val_counts": val_counts,
        "hyperparameters": {
            "epochs_head": args.epochs_head,
            "epochs_finetune": args.epochs_finetune,
            "batch_size": args.batch_size,
            "img_size": args.img_size,
            "lr_head": args.lr_head,
            "lr_finetune": args.lr_finetune,
            "unfreeze_layers": args.unfreeze_layers,
            "seed": args.seed,
        },
        "tensorflow_version": tf.__version__,
        "best_val_accuracy": max(best_val_acc_phase1, max(history2.history.get("val_accuracy", [0]))),
            "epochs_run": {
                "phase1": len(history1.history.get("loss", [])),
                "phase2": len(history2.history.get("loss", [])),
        },
        "phase2_trainable_weight_tensors": n_trainable_weights,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    json_path = out_dir / "training_run.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(run_info, f, ensure_ascii=False, indent=2)

    print(f"Training completed. Best val_accuracy: {run_info['best_val_accuracy']:.4f}")
    print(f"Artifacts saved in: {out_dir}")


if __name__ == "__main__":
    main()
