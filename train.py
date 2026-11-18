"""Train a baseline activity recognition model on UT-HAR (SenseFi version).

Data layout (from the SenseFi benchmark, extracted into data/):
    data/UT_HAR/data/X_{train,val,test}.csv   NumPy .npy files despite the name,
                                              shape (N, 250, 90): 250 time steps
                                              x 90 CSI amplitude channels
                                              (30 subcarriers x 3 antennas)
    data/UT_HAR/label/y_{train,val,test}.csv  int labels 0..6

Baseline: summary statistics per channel -> RandomForest.
The model is fit on train, checked on val, and scored once on test.

Run:
    .\\.venv\\Scripts\\python.exe train.py
"""

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data" / "UT_HAR"
MODEL_PATH = ROOT / "models" / "activity_model.joblib"

# Class names in the order the SenseFi paper lists UT-HAR activities.
# The index-to-name mapping is not documented in the data files, so verify it
# (e.g. against the original ermongroup labels) before trusting the names.
CLASS_NAMES = ["Lie down", "Fall", "Walk", "Pick up", "Run", "Sit down", "Stand up"]


def load_split(split):
    """Return (X, y) for 'train', 'val' or 'test'. X has shape (N, 250, 90)."""
    X = np.load(DATA_DIR / "data" / f"X_{split}.csv", allow_pickle=False)
    y = np.load(DATA_DIR / "label" / f"y_{split}.csv", allow_pickle=False)
    return X.reshape(len(X), 250, 90), y


def extract_features(X):
    """Turn CSI windows (N, T, C) into a feature matrix (N, 6*C).

    Per channel: mean, std, min, max, range, and mean absolute first
    difference (how much the signal moves, a rough motion-energy measure).
    """
    X = np.asarray(X, dtype=np.float32)
    if X.ndim == 2:  # a single window (T, C)
        X = X[None]
    diff = np.abs(np.diff(X, axis=1)).mean(axis=1)
    mn, mx = X.min(axis=1), X.max(axis=1)
    return np.concatenate(
        [X.mean(axis=1), X.std(axis=1), mn, mx, mx - mn, diff], axis=1
    )


def main():
    X_train, y_train = load_split("train")
    X_val, y_val = load_split("val")
    X_test, y_test = load_split("test")
    print(f"train {len(y_train)}  val {len(y_val)}  test {len(y_test)} windows")

    F_train, F_val, F_test = map(extract_features, (X_train, X_val, X_test))

    model = RandomForestClassifier(
        n_estimators=300, class_weight="balanced", n_jobs=-1, random_state=0
    )
    model.fit(F_train, y_train)

    print(f"val accuracy:  {model.score(F_val, y_val):.3f}")
    test_pred = model.predict(F_test)
    print(f"test accuracy: {(test_pred == y_test).mean():.3f}\n")
    print(classification_report(y_test, test_pred, target_names=CLASS_NAMES, digits=3))
    print("Confusion matrix (rows = true, cols = predicted):")
    print(confusion_matrix(y_test, test_pred))

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump({"model": model, "class_names": CLASS_NAMES}, MODEL_PATH)
    print(f"\nSaved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()
