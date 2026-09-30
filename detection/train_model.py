"""
Isolation Forest Training and Model Persistence Module.
Trains an unsupervised Isolation Forest on clean baseline normal telemetry.
Persists the trained model and metadata package into models/isolation_forest.joblib.
"""

import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.settings import model_config, BASE_DIR
from collector.feature_extractor import FeatureExtractor


class ModelTrainer:
    """
    Trains and packages the Isolation Forest model using clean baseline data.
    """

    def __init__(self, data_path: Path = None, model_output_path: Path = None):
        self.data_path = data_path or (BASE_DIR / "data" / "normal" / "baseline_telemetry.csv")
        self.model_output_path = model_output_path or model_config.model_path

    def load_training_data(self) -> pd.DataFrame:
        """Loads and verifies the clean normal training dataset."""
        if not self.data_path.exists():
            raise FileNotFoundError(
                f"Training dataset not found at: {self.data_path}. "
                "Run 'python simulator/device_simulator.py --mode generate' first."
            )

        print(f"[INFO] Loading baseline training data from: {self.data_path}...")
        df = pd.read_csv(self.data_path)
        print(f"[INFO] Loaded {len(df)} normal observations across columns: {list(df.columns)}")
        return df

    def train_and_persist(self, n_estimators: int = 100) -> Path:
        """
        Trains the Isolation Forest model and serializes it using Joblib.
        """
        df = self.load_training_data()
        X = FeatureExtractor.extract_dataframe(df)

        print(f"[INFO] Initializing IsolationForest (n_estimators={n_estimators}, "
              f"contamination={model_config.contamination}, random_state={model_config.random_state})...")
        
        model = IsolationForest(
            n_estimators=n_estimators,
            contamination=model_config.contamination,
            random_state=model_config.random_state,
            n_jobs=-1  # Use all available CPU cores for fast training
        )

        # Fit model strictly on normal baseline observations
        model.fit(X)

        # Compute baseline decision function scores for calibration
        scores = model.decision_function(X)
        mean_score = float(np.mean(scores))
        std_score = float(np.std(scores))
        min_score = float(np.min(scores))
        max_score = float(np.max(scores))

        print(f"[METRICS] Baseline Decision Function Distribution:")
        print(f"          Mean: {mean_score:.4f} | Std: {std_score:.4f} | Min: {min_score:.4f} | Max: {max_score:.4f}")

        # Package model with metadata to guarantee reproducibility
        artifact = {
            "model": model,
            "feature_names": FeatureExtractor.get_feature_names(),
            "contamination": model_config.contamination,
            "random_state": model_config.random_state,
            "n_estimators": n_estimators,
            "training_samples_count": len(df),
            "trained_at_utc": datetime.now(timezone.utc).isoformat(),
            "baseline_mean_score": mean_score,
            "baseline_std_score": std_score,
            "baseline_min_score": min_score,
            "baseline_max_score": max_score
        }

        self.model_output_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(artifact, self.model_output_path)
        print(f"[SUCCESS] Persisted trained ML model artifact to: {self.model_output_path}")

        return self.model_output_path


def main():
    parser = argparse.ArgumentParser(description="Train Isolation Forest for IoT Anomaly Detection")
    parser.add_argument("--trees", type=int, default=100, help="Number of isolation trees in ensemble")
    args = parser.parse_args()

    trainer = ModelTrainer()
    trainer.train_and_persist(n_estimators=args.trees)


if __name__ == "__main__":
    main()
