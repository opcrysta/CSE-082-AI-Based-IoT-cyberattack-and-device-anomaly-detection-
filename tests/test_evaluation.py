"""
Unit and Integration Tests for Model Evaluation Engine.
Validates quantitative metric computations, confusion matrix math,
and evaluation persistence across Synthetic and UNSW TON_IoT benchmarks.
"""

import json
from pathlib import Path
import pytest
from detection.evaluate_model import ModelEvaluator
from config.settings import BASE_DIR


@pytest.fixture(scope="module")
def evaluator():
    return ModelEvaluator()


def test_synthetic_evaluation_metrics(evaluator):
    """Verifies evaluation execution and mathematical consistency on synthetic attack data."""
    synth_csv = BASE_DIR / "data" / "attack_scenarios" / "labeled_evaluation_data.csv"
    assert synth_csv.exists(), "Synthetic evaluation data must exist"

    results = evaluator.evaluate_dataset(synth_csv, "Synthetic Scenarios")

    assert results["total_records"] == 1200
    assert results["normal_records"] == 800
    assert results["anomaly_records"] == 400

    cm = results["confusion_matrix"]
    tp = cm["true_positives"]
    fp = cm["false_positives"]
    tn = cm["true_negatives"]
    fn = cm["false_negatives"]

    # Verify confusion matrix sums
    assert tp + fn == 400
    assert tn + fp == 800
    assert tp + fp + tn + fn == 1200

    # Verify metrics exist and are bounded
    metrics = results["metrics"]
    assert 0.0 <= metrics["accuracy"] <= 1.0
    assert 0.0 <= metrics["precision"] <= 1.0
    assert 0.0 <= metrics["recall"] <= 1.0
    assert 0.0 <= metrics["f1_score"] <= 1.0
    assert 0.0 <= metrics["roc_auc"] <= 1.0

    # Ensure baseline statistical performance exceeds random chance (0.50)
    assert metrics["accuracy"] > 0.80
    assert metrics["roc_auc"] > 0.85

    # Check attack breakdown
    breakdown = results["attack_breakdown"]
    assert "dos_flooding" in breakdown
    assert "brute_force_auth" in breakdown
    assert breakdown["dos_flooding"]["detection_rate_pct"] == 100.0
    assert breakdown["brute_force_auth"]["detection_rate_pct"] == 100.0


def test_ton_iot_benchmark_evaluation(evaluator):
    """Verifies evaluation on authentic UNSW Canberra TON_IoT dataset."""
    ton_csv = BASE_DIR / "data" / "attack_scenarios" / "ton_iot_benchmark.csv"
    assert ton_csv.exists(), "TON_IoT benchmark CSV must exist"

    results = evaluator.evaluate_dataset(ton_csv, "UNSW TON_IoT Benchmark")

    assert results["total_records"] == 1811
    assert results["normal_records"] == 1000
    assert results["anomaly_records"] == 811

    metrics = results["metrics"]
    # High precision ensures minimal false alarms on normal thermostat operation
    assert metrics["precision"] >= 0.95
    assert metrics["specificity"] >= 0.95
    assert metrics["f1_score"] > 0.80

    # Check high-impact attacks were isolated
    breakdown = results["attack_breakdown"]
    assert breakdown["password"]["detection_rate_pct"] == 100.0
    assert breakdown["ransomware"]["detection_rate_pct"] == 100.0
    assert breakdown["backdoor"]["detection_rate_pct"] == 100.0


def test_persisted_evaluation_report_file():
    """Verifies that the serialized JSON report matches saved schema."""
    report_file = BASE_DIR / "models" / "evaluation_report.json"
    assert report_file.exists(), "evaluation_report.json must be persisted"

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "model_path" in data
    assert "features_evaluated" in data
    assert len(data["features_evaluated"]) == 7
    assert "benchmarks" in data
    assert "synthetic_scenarios" in data["benchmarks"]
    assert "ton_iot_benchmark" in data["benchmarks"]
