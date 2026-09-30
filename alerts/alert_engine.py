"""
Security Alert & Threat Attribution Engine.
Analyzes observations flagged as anomalous by the Isolation Forest model.
Attributes root cause to distinguish between genuine cyberattacks and benign hardware/environmental faults.
Emits structured alert payloads with threat category, severity, and actionable mitigations.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AlertEvent:
    """
    Standardized security alert payload emitted by the detection pipeline.
    """
    alert_id: str
    timestamp: str
    device_id: str
    is_anomaly: bool
    is_cyberattack: bool
    alert_category: str       # "CYBERATTACK", "HARDWARE_FAULT", "ENVIRONMENTAL", "STATISTICAL"
    threat_name: str          # e.g., "DoS Message Flooding", "Brute-Force Authentication"
    severity: str            # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    raw_anomaly_score: float
    calibrated_risk_score: float
    contributing_metrics: Dict[str, Any]
    recommended_action: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AlertEngine:
    """
    Rule-based Threat Attribution Engine acting as Tier-2 verification.
    """

    # Baseline operational thresholds for heuristic attribution
    THRESHOLDS = {
        "max_normal_msg_rate": 5.0,        # Normal is ~1.0 msg/s
        "dos_msg_rate": 15.0,              # Flooding threshold
        "dos_cpu_usage": 75.0,             # CPU saturation
        "max_normal_failed_auth": 2,       # Normal is 0-1
        "brute_force_auth_count": 5,       # Sustained failed login threshold
        "max_normal_voltage": 250.0,       # High voltage surge threshold
        "min_normal_voltage": 200.0,       # Low brownout threshold
        "overheat_temp": 60.0,             # Hardware overheat threshold
        "max_normal_latency": 150.0        # Latency anomaly threshold
    }

    @classmethod
    def evaluate(cls, telemetry_data: Dict[str, Any], ml_result: Dict[str, Any]) -> Optional[AlertEvent]:
        """
        Evaluates a telemetry observation and its ML prediction.
        If flagged as anomalous (or high risk), performs root-cause attribution.

        Returns:
            AlertEvent if an alert condition is met, else None.
        """
        is_anomaly = ml_result.get("is_anomaly", False)
        risk_score = ml_result.get("risk_score", 0.0)
        raw_score = ml_result.get("raw_score", 0.0)

        # Trigger alert only if Isolation Forest flags anomaly or risk score >= 0.50
        if not is_anomaly and risk_score < 0.50:
            return None

        device_id = telemetry_data.get("device_id", "UNKNOWN")
        timestamp = telemetry_data.get("timestamp", datetime.now(timezone.utc).isoformat())

        temp = float(telemetry_data.get("temperature", 25.0))
        volt = float(telemetry_data.get("voltage", 230.0))
        cpu = float(telemetry_data.get("cpu_usage", 15.0))
        msg_rate = float(telemetry_data.get("message_rate", 1.0))
        failed_auth = int(telemetry_data.get("failed_auth_count", 0))
        latency = float(telemetry_data.get("network_latency", 15.0))

        # -------------------------------------------------------------
        # Rule 1: Brute-Force Authentication Attempt
        # -------------------------------------------------------------
        if failed_auth >= cls.THRESHOLDS["brute_force_auth_count"]:
            return AlertEvent(
                alert_id=str(uuid.uuid4()),
                timestamp=timestamp,
                device_id=device_id,
                is_anomaly=True,
                is_cyberattack=True,
                alert_category="CYBERATTACK",
                threat_name="Brute-Force Authentication Attack",
                severity="HIGH" if failed_auth < 15 else "CRITICAL",
                raw_anomaly_score=raw_score,
                calibrated_risk_score=risk_score,
                contributing_metrics={"failed_auth_count": failed_auth, "cpu_usage": cpu},
                recommended_action="Enforce exponential backoff on auth endpoint; quarantine source client."
            )

        # -------------------------------------------------------------
        # Rule 2: DoS / MQTT Message Flooding
        # -------------------------------------------------------------
        if msg_rate >= cls.THRESHOLDS["dos_msg_rate"] and cpu >= cls.THRESHOLDS["dos_cpu_usage"]:
            return AlertEvent(
                alert_id=str(uuid.uuid4()),
                timestamp=timestamp,
                device_id=device_id,
                is_anomaly=True,
                is_cyberattack=True,
                alert_category="CYBERATTACK",
                threat_name="Denial-of-Service (DoS) / Message Flooding",
                severity="CRITICAL",
                raw_anomaly_score=raw_score,
                calibrated_risk_score=risk_score,
                contributing_metrics={"message_rate": msg_rate, "cpu_usage": cpu},
                recommended_action="Throttle device publish rate at Mosquitto ACL; terminate client session."
            )

        # -------------------------------------------------------------
        # Rule 3: Network Latency / Man-in-the-Middle (MITM) Degradation
        # -------------------------------------------------------------
        if latency >= cls.THRESHOLDS["max_normal_latency"] and cpu < cls.THRESHOLDS["dos_cpu_usage"]:
            return AlertEvent(
                alert_id=str(uuid.uuid4()),
                timestamp=timestamp,
                device_id=device_id,
                is_anomaly=True,
                is_cyberattack=True,
                alert_category="CYBERATTACK",
                threat_name="Network Degradation / Man-in-the-Middle (MITM)",
                severity="MEDIUM",
                raw_anomaly_score=raw_score,
                calibrated_risk_score=risk_score,
                contributing_metrics={"network_latency": latency},
                recommended_action="Inspect network gateway routing hops; verify broker TLS certificate integrity."
            )

        # -------------------------------------------------------------
        # Rule 4: Electrical Power Grid Surge or Brownout (Hardware Fault)
        # -------------------------------------------------------------
        if volt > cls.THRESHOLDS["max_normal_voltage"] or volt < cls.THRESHOLDS["min_normal_voltage"]:
            fault_type = "Power Surge" if volt > cls.THRESHOLDS["max_normal_voltage"] else "Brownout"
            return AlertEvent(
                alert_id=str(uuid.uuid4()),
                timestamp=timestamp,
                device_id=device_id,
                is_anomaly=True,
                is_cyberattack=False,  # NOT a cyberattack!
                alert_category="HARDWARE_FAULT",
                threat_name=f"Electrical Voltage Anomaly ({fault_type})",
                severity="HIGH",
                raw_anomaly_score=raw_score,
                calibrated_risk_score=risk_score,
                contributing_metrics={"voltage": volt},
                recommended_action="Inspect hardware power regulator and physical voltage supply line."
            )

        # -------------------------------------------------------------
        # Rule 5: Thermal Overheating (Environmental / Cooling Fault)
        # -------------------------------------------------------------
        if temp >= cls.THRESHOLDS["overheat_temp"]:
            return AlertEvent(
                alert_id=str(uuid.uuid4()),
                timestamp=timestamp,
                device_id=device_id,
                is_anomaly=True,
                is_cyberattack=False,  # Environmental!
                alert_category="ENVIRONMENTAL",
                threat_name="Thermal Overheating / Sensor Fault",
                severity="HIGH",
                raw_anomaly_score=raw_score,
                calibrated_risk_score=risk_score,
                contributing_metrics={"temperature": temp},
                recommended_action="Inspect physical device enclosure, heatsink, and environmental cooling."
            )

        # -------------------------------------------------------------
        # Rule 6: Unspecified Statistical Anomaly
        # -------------------------------------------------------------
        return AlertEvent(
            alert_id=str(uuid.uuid4()),
            timestamp=timestamp,
            device_id=device_id,
            is_anomaly=True,
            is_cyberattack=False,
            alert_category="STATISTICAL",
            threat_name="Unclassified Multidimensional Anomaly",
            severity="LOW",
            raw_anomaly_score=raw_score,
            calibrated_risk_score=risk_score,
            contributing_metrics={k: v for k, v in telemetry_data.items() if isinstance(v, (int, float))},
            recommended_action="Log observation and monitor for repeated multi-metric deviation."
        )
