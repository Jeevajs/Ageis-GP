from pathlib import Path
import joblib

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "data" / "gnn" / "gnn_rca_baseline.joblib"

class GNNRCAAgent:
    def __init__(self):
        self.available = MODEL_PATH.exists()
        self.model = joblib.load(MODEL_PATH) if self.available else None

    def predict(self, incident):
        text = f"{incident.get('alert','')} {incident.get('logs','')} {incident.get('metrics','')}".lower()

        if not self.available:
            return {
                "agent": "GNNRCAAgent",
                "available": False,
                "top3_root_causes": self._fallback(text)
            }

        # If your trained model expects engineered features, connect here.
        return {
            "agent": "GNNRCAAgent",
            "available": True,
            "top3_root_causes": self._fallback(text)
        }

    def _fallback(self, text):
        if "oom" in text or "memory" in text:
            return [
                {"root_cause": "Memory exhaustion", "confidence": 0.86},
                {"root_cause": "Pod resource limit issue", "confidence": 0.72},
                {"root_cause": "Node pressure", "confidence": 0.55}
            ]

        if "kafka" in text or "consumer lag" in text:
            return [
                {"root_cause": "Kafka consumer bottleneck", "confidence": 0.88},
                {"root_cause": "Message processing delay", "confidence": 0.70},
                {"root_cause": "Downstream dependency slowness", "confidence": 0.52}
            ]

        if "database" in text or "connection pool" in text:
            return [
                {"root_cause": "Database connection pool exhaustion", "confidence": 0.90},
                {"root_cause": "Slow query", "confidence": 0.61},
                {"root_cause": "Database saturation", "confidence": 0.58}
            ]

        return [
            {"root_cause": "Application degradation", "confidence": 0.70},
            {"root_cause": "Dependency failure", "confidence": 0.60},
            {"root_cause": "Infrastructure issue", "confidence": 0.50}
        ]