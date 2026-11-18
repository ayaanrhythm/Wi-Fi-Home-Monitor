"""Predict activities from CSI windows using the model saved by train.py.

For now this runs on a few UT-HAR test windows. Later, feed it windows of
live CSI from the ESP32 (read over serial with pyserial), shaped (250, 90).

Run:
    .\\.venv\\Scripts\\python.exe predict.py
"""

from pathlib import Path

from train import extract_features, load_split

MODEL_PATH = Path(__file__).parent / "models" / "activity_model.joblib"


def load_model():
    import joblib  # installed with scikit-learn
    # joblib uses pickle: only load models you trained yourself with train.py
    bundle = joblib.load(MODEL_PATH)
    return bundle["model"], bundle["class_names"]


def predict(model, class_names, window):
    """Return (activity name, confidence) for one CSI window of shape (250, 90)."""
    probs = model.predict_proba(extract_features(window))[0]
    best = probs.argmax()
    return class_names[model.classes_[best]], float(probs[best])


def main():
    model, class_names = load_model()
    X_test, y_test = load_split("test")
    for i in range(0, len(X_test), 100):
        activity, conf = predict(model, class_names, X_test[i])
        print(f"Predicted activity: {activity}")
        print(f"Confidence: {conf:.0%}   (true: {class_names[y_test[i]]})\n")


if __name__ == "__main__":
    main()
