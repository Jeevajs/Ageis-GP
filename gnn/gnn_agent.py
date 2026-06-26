from pathlib import Path
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MODEL_FILE = ROOT / "data" / "gnn" / "gnn_rca_baseline.joblib"
KEYWORDS = ["timeout", "connection reset", "under replicated", "oomkilled", "crashloopbackoff",
            "connection pool", "consumer lag", "http 500", "machine check", "not responding",
            "database", "kafka"]

class GNNRCABaselineAgent:
    def analyze(self, incident):
        if not MODEL_FILE.exists():
            return {"agent": "GNNRCABaselineAgent", "available": False,
                    "summary": "GNN baseline model not trained. Run setup_phase6_7_8.py.",
                    "top3_root_causes": []}
        bundle = joblib.load(MODEL_FILE)
        model, encoder, features = bundle["model"], bundle["encoder"], bundle["features"]
        text = f"{incident.get('alert','')} {incident.get('logs','')} {incident.get('metrics','')}".lower()
        row = {"severity_num": {"P1": 3, "P2": 2, "P3": 1}.get(str(incident.get("severity")), 1),
               "text_length": len(text)}
        for kw in KEYWORDS:
            row[f"kw_{kw.replace(' ', '_')}"] = int(kw in text)
        X = pd.DataFrame([{f: row.get(f, 0) for f in features}])
        probs = model.predict_proba(X)[0]
        classes = list(encoder.classes_)
        ranked = probs.argsort()[::-1][:3]
        top3 = [{"root_cause": classes[i], "confidence": round(float(probs[i]), 3)} for i in ranked]
        return {"agent": "GNNRCABaselineAgent", "available": True, "top3_root_causes": top3,
                "summary": f"Top GNN-style RCA candidate: {top3[0]['root_cause']}"}
