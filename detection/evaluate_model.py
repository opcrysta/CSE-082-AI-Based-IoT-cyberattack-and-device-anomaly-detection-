"""
Offline Model Evaluation and Quantitative Benchmarking Engine.
Evaluates the trained Isolation Forest anomaly detection model against:
1. Synthetic Controlled Attack Scenarios (DoS, Brute-Force, Tampering, Degradation).
2. Authentic UNSW Canberra TON_IoT Telemetry Dataset (Password, Ransomware, XSS, Scanning, Backdoor).

Computes Confusion Matrix (TP, FP, TN, FN), Precision, Recall, F1-Score,
False Positive Rate (FPR), ROC-AUC, and Per-Attack Breakdown.
Persists the final evaluation metrics to 'models/evaluation_report.json'.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
    roc_auc_score,
)

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from config.settings import BASE_DIR, model_config
from detection.predict import AnomalyDetector


class ModelEvaluator:
    """
    Evaluates Isolation Forest on labeled validation sets and generates
    reproducible quantitative benchmarks.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.detector = AnomalyDetector(model_path=model_path)
        self.feature_names = self.detector.feature_names
        self.output_report_path = BASE_DIR / "models" / "evaluation_report.json"

    def evaluate_dataset(self, csv_path: Path, dataset_name: str) -> Dict[str, Any]:
        """
        Executes quantitative benchmarking on a given labeled CSV dataset.
        """
        if not csv_path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found at: {csv_path}")

        df = pd.read_csv(csv_path)

        # Validate required columns
        for col in self.feature_names:
            if col not in df.columns:
                raise ValueError(f"Missing required feature column '{col}' in {csv_path}")

        if "is_anomaly" not in df.columns:
            raise ValueError(f"Missing target column 'is_anomaly' in {csv_path}")

        X = df[list(self.feature_names)]
        y_true = df["is_anomaly"].astype(int).values

        # Isolation Forest: 1 = normal (inlier), -1 = anomaly (outlier)
        raw_preds = self.detector.model.predict(X)
        y_pred = (raw_preds == -1).astype(int)

        # Decision function: higher negative = more anomalous -> invert for positive anomaly ranking
        raw_scores = self.detector.model.decision_function(X)
        anomaly_scores = -raw_scores

        # Compute Confusion Matrix (where 1 = Anomaly / Positive Class, 0 = Normal / Negative Class)
        cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()

        accuracy = float(accuracy_score(y_true, y_pred))
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
        specificity = float(tn / (tn + fp)) if (tn + fp) > 0 else 0.0
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

        try:
            roc_auc = float(roc_auc_score(y_true, anomaly_scores))
        except Exception:
            roc_auc = 0.0

        # Per-attack category breakdown
        attack_breakdown: Dict[str, Dict[str, Any]] = {}
        if "attack_type" in df.columns:
            df_temp = df.copy()
            df_temp["pred_anomaly"] = y_pred
            for attack_type, group in df_temp.groupby("attack_type"):
                total_samples = len(group)
                detected = int(group["pred_anomaly"].sum())
                detection_rate = float(detected / total_samples) if total_samples > 0 else 0.0
                attack_breakdown[str(attack_type)] = {
                    "total_samples": total_samples,
                    "detected_samples": detected,
                    "detection_rate_pct": round(detection_rate * 100, 2),
                }

        results = {
            "dataset_name": dataset_name,
            "total_records": len(df),
            "normal_records": int((y_true == 0).sum()),
            "anomaly_records": int((y_true == 1).sum()),
            "confusion_matrix": {
                "true_positives": int(tp),
                "false_positives": int(fp),
                "true_negatives": int(tn),
                "false_negatives": int(fn),
            },
            "metrics": {
                "accuracy": round(accuracy, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "specificity": round(specificity, 4),
                "false_positive_rate": round(fpr, 4),
                "f1_score": round(f1, 4),
                "roc_auc": round(roc_auc, 4),
            },
            "attack_breakdown": attack_breakdown,
        }

        return results

    def run_full_evaluation(
        self,
        synthetic_path: Optional[Path] = None,
        ton_iot_path: Optional[Path] = None,
        save_report: bool = True,
    ) -> Dict[str, Any]:
        """
        Runs full benchmark across both synthetic and real-world TON_IoT datasets,
        persisting metrics to models/evaluation_report.json.
        """
        synth_csv = synthetic_path or (BASE_DIR / "data" / "attack_scenarios" / "labeled_evaluation_data.csv")
        ton_csv = ton_iot_path or (BASE_DIR / "data" / "attack_scenarios" / "ton_iot_benchmark.csv")

        report: Dict[str, Any] = {
            "model_path": str(self.detector.model_path),
            "features_evaluated": list(self.feature_names),
            "contamination_rate": model_config.contamination,
            "benchmarks": {},
        }

        print("=" * 78)
        print("          OFFLINE MODEL BENCHMARKING & QUANTITATIVE EVALUATION          ")
        print("=" * 78)

        # 1. Synthetic Evaluation
        if synth_csv.exists():
            print(f"\n[*] Evaluating Synthetic Attack Scenarios: {synth_csv.name}")
            synth_res = self.evaluate_dataset(synth_csv, "Synthetic Scenarios")
            report["benchmarks"]["synthetic_scenarios"] = synth_res
            self._print_benchmark_summary(synth_res)
        else:
            print(f"[!] Warning: Synthetic dataset not found at {synth_csv}")

        # 2. TON_IoT Real-World Benchmark
        if ton_csv.exists():
            print(f"\n[*] Evaluating Authentic UNSW TON_IoT Dataset: {ton_csv.name}")
            ton_res = self.evaluate_dataset(ton_csv, "UNSW TON_IoT Benchmark")
            report["benchmarks"]["ton_iot_benchmark"] = ton_res
            self._print_benchmark_summary(ton_res)
        else:
            print(f"[!] Warning: TON_IoT benchmark not found at {ton_csv}")

        if save_report:
            self.output_report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.output_report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2)
            print(f"\n[+] Full evaluation report persisted to: {self.output_report_path}")

        print("=" * 78)
        return report

    def _print_benchmark_summary(self, res: Dict[str, Any]) -> None:
        """Formats and prints an ASCII summary table for terminal review."""
        cm = res["confusion_matrix"]
        m = res["metrics"]

        print("-" * 78)
        print(f" Dataset: {res['dataset_name']} ({res['total_records']} total records)")
        print(f" Class Balance: Normal={res['normal_records']} | Anomaly={res['anomaly_records']}")
        print("-" * 78)
        print(" Confusion Matrix:")
        print(f"   [True Positives (TP)  = {cm['true_positives']:4d} ]  [False Negatives (FN) = {cm['false_negatives']:4d} ]")
        print(f"   [False Positives (FP) = {cm['false_positives']:4d} ]  [True Negatives (TN)  = {cm['true_negatives']:4d} ]")
        print()
        print(" Key Quantitative Metrics:")
        print(f"   Accuracy            : {m['accuracy'] * 100:.2f}%")
        print(f"   Precision           : {m['precision'] * 100:.2f}%  (Confidence that an alert is an actual attack)")
        print(f"   Recall (Sensitivity): {m['recall'] * 100:.2f}%  (Proportion of actual attacks isolated)")
        print(f"   Specificity (TNR)   : {m['specificity'] * 100:.2f}%  (Proportion of normal telemetry unflagged)")
        print(f"   False Positive Rate : {m['false_positive_rate'] * 100:.2f}%  (Benign samples falsely flagged)")
        print(f"   F1-Score            : {m['f1_score']:.4f}   (Harmonic mean of Precision and Recall)")
        print(f"   ROC-AUC Score       : {m['roc_auc']:.4f}   (Area Under the Receiver Operating Characteristic)")
        print()
        print(" Attack Detection Breakdown:")
        print(f"   {'Attack Type':<25} | {'Total':<6} | {'Detected':<8} | {'Recall Rate':<10}")
        print("   " + "-" * 57)
        for attack, details in res["attack_breakdown"].items():
            print(f"   {attack:<25} | {details['total_samples']:<6} | {details['detected_samples']:<8} | {details['detection_rate_pct']:>8.2f}%")
        print("-" * 78)


def main():
    evaluator = ModelEvaluator()
    evaluator.run_full_evaluation()


if __name__ == "__main__":
    main()
