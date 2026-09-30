"""
Real-Time Anomaly Inference Engine.
Loads the persisted Isolation Forest model artifact and scores incoming telemetry vectors.
Produces binary classifications, decision function scores, and calibrated risk probabilities.
"""

import sys
from pathlib import Path
from typing import Union, Dict, Any
import numpy as np
import pandas as pd
import joblib

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.settings import model_config
from collector.data_validator import TelemetryPayload
from collector.feature_extractor import FeatureExtractor


class AnomalyDetector:
    """
    Inference service for scoring telemetry observations with Isolation Forest.
    """

    def __init__(self, model_path: Path = None):
        self.model_path = model_path or model_config.model_path
        self.artifact = self._load_model_artifact()
        self.model = self.artifact["model"]
        self.feature_names = self.artifact["feature_names"]
        self.baseline_mean = self.artifact.get("baseline_mean_score", 0.15)
        self.baseline_std = max(self.artifact.get("baseline_std_score", 0.05), 1e-6)

    def _load_model_artifact(self) -> Dict[str, Any]:
        """Loads and verifies the serialized joblib artifact."""
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Trained model not found at: {self.model_path}. "
                "Run 'python detection/train_model.py' to train and persist the model first."
            )
        return joblib.load(self.model_path)

    def calculate_risk_score(self, raw_score: float) -> float:
        """
        Calibrates raw decision function score into an intuitive 0.0 to 1.0 risk score.
        In Scikit-learn:
            - Positive score (>0.0) indicates normal operational inlier (low risk).
            - Negative score (<0.0) indicates an isolated outlier (high risk).
        Sigmoid calibration maps this smoothly:
            raw_score = +0.20 -> risk ~ 0.05 (Safe)
            raw_score =  0.00 -> risk ~ 0.50 (Decision boundary)
            raw_score = -0.20 -> risk ~ 0.95 (Severe anomaly)
        """
        # Sigmoid scaling factor k = 15.0 provides sensitive, well-calibrated risk spread
        k = 18.0
        risk = 1.0 / (1.0 + np.exp(k * raw_score))
        return round(float(np.clip(risk, 0.0, 1.0)), 4)

    def predict_vector(self, feature_vector: np.ndarray) -> Dict[str, Any]:
        """
        Infers anomaly status from a pre-extracted 2D feature vector (shape: 1, 7).
        """
        if feature_vector.ndim != 2 or feature_vector.shape[1] != len(self.feature_names):
            raise ValueError(
                f"Expected feature vector of shape (1, {len(self.feature_names)}), "
                f"got shape {feature_vector.shape}"
            )

        # Convert to DataFrame with feature names to match training schema and suppress warnings
        df_input = pd.DataFrame(feature_vector, columns=self.feature_names)

        # Scikit-learn predict returns 1 for normal, -1 for anomaly
        prediction = int(self.model.predict(df_input)[0])
        raw_score = float(self.model.decision_function(df_input)[0])
        is_anomaly = bool(prediction == -1)
        risk_score = self.calculate_risk_score(raw_score)

        return {
            "prediction": prediction,      # 1 = Normal, -1 = Anomaly
            "is_anomaly": is_anomaly,      # True = Anomaly, False = Normal
            "raw_score": round(raw_score, 4),
            "risk_score": risk_score,      # 0.0 (Safe) to 1.0 (Critical)
            "decision_threshold": 0.0
        }

    def predict_telemetry(self, telemetry: Union[TelemetryPayload, Dict[str, Any]]) -> Dict[str, Any]:
        """
        End-to-end inference directly from a validated telemetry object or dictionary.
        """
        vector = FeatureExtractor.extract_vector(telemetry)
        result = self.predict_vector(vector)

        # Attach device context if available
        if isinstance(telemetry, TelemetryPayload):
            result["device_id"] = telemetry.device_id
            result["timestamp"] = telemetry.timestamp
        elif isinstance(telemetry, dict):
            result["device_id"] = telemetry.get("device_id", "UNKNOWN")
            result["timestamp"] = telemetry.get("timestamp")

        return result


def main():
    detector = AnomalyDetector()
    print(f"[INFO] Loaded Isolation Forest (Trained at: {detector.artifact['trained_at_utc']})")

    # 1. Test clean normal observation
    normal_sample = {
        "device_id": "device_001",
        "temperature": 25.2,
        "voltage": 230.1,
        "cpu_usage": 14.5,
        "ram_usage": 41.0,
        "message_rate": 1.0,
        "failed_auth_count": 0,
        "network_latency": 15.0
    }
    norm_res = detector.predict_telemetry(normal_sample)
    print(f"\n[TEST 1 - NORMAL TELEMETRY]:")
    print(f"  Prediction: {norm_res['prediction']} (Anomaly: {norm_res['is_anomaly']})")
    print(f"  Raw Score: {norm_res['raw_score']} | Risk Score: {norm_res['risk_score']}")

    # 2. Test DoS flood attack observation
    attack_sample = {
        "device_id": "device_001",
        "temperature": 26.0,
        "voltage": 230.0,
        "cpu_usage": 92.5,
        "ram_usage": 42.0,
        "message_rate": 35.0,  # Extreme spike
        "failed_auth_count": 0,
        "network_latency": 45.0
    }
    att_res = detector.predict_telemetry(attack_sample)
    print(f"\n[TEST 2 - DoS ATTACK TELEMETRY]:")
    print(f"  Prediction: {att_res['prediction']} (Anomaly: {att_res['is_anomaly']})")
    print(f"  Raw Score: {att_res['raw_score']} | Risk Score: {att_res['risk_score']}")


if __name__ == "__main__":
    main()
