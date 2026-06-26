from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder

ROOT = Path(__file__).resolve().parents[1]
FEATURE_FILE = ROOT / "data" / "gnn" / "gnn_features.csv"
MODEL_FILE = ROOT / "data" / "gnn" / "gnn_rca_baseline.joblib"
OUT = ROOT / "phase_outputs" / "gnn_baseline_results.csv"

def train_gnn_baseline():
    df = pd.read_csv(FEATURE_FILE)
    feature_cols = [c for c in df.columns if c.startswith("kw_") or c in ["severity_num", "text_length"]]
    X = df[feature_cols]
    encoder = LabelEncoder()
    y = encoder.fit_transform(df["root_cause"])
    stratify = y if min(pd.Series(y).value_counts()) > 1 else None
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, df.index, test_size=0.3, random_state=42, stratify=stratify
    )
    model = RandomForestClassifier(n_estimators=200, random_state=42, class_weight="balanced")
    model.fit(X_train, y_train)
    probs = model.predict_proba(X_test)
    preds = model.predict(X_test)
    classes = list(encoder.classes_)
    results = []
    for i, idx in enumerate(idx_test):
        ranked_idx = probs[i].argsort()[::-1][:3]
        top3 = [classes[j] for j in ranked_idx]
        results.append({"incident_id": df.loc[idx, "incident_id"], "actual_root_cause": df.loc[idx, "root_cause"],
                        "predicted_root_cause": classes[preds[i]], "top3_root_causes": " | ".join(top3),
                        "confidence": round(float(max(probs[i])), 3), "top3_hit": int(df.loc[idx, "root_cause"] in top3)})
    out = pd.DataFrame(results)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "encoder": encoder, "features": feature_cols}, MODEL_FILE)
    print("GNN-style RCA baseline trained.")
    print(f"Accuracy: {accuracy_score(y_test, preds):.2f}")
    print(f"Top-3 Hit Rate: {out['top3_hit'].mean():.2f}")
    print(f"Saved model: {MODEL_FILE}")

if __name__ == "__main__":
    train_gnn_baseline()
