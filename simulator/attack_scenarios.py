"""
Controlled IoT Cyberattack and Anomaly Scenario Generator.
Simulates realistic cyber threats and hardware anomalies for IoT devices:
1. DoS / Message Flooding (abnormal message rate & CPU spike)
2. Brute-Force Authentication (repeated simulated login failures)
3. Sensor Tampering & Voltage Surges (extreme sensor readings)
4. Network Degradation / MITM (abnormal network latency)

Provides both live MQTT attack injection and labeled ground-truth evaluation dataset generation.
"""

import json
import time
import sys
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import paho.mqtt.client as mqtt
from config.settings import mqtt_config, BASE_DIR
from simulator.device_simulator import IoTDevice


class AttackScenarioGenerator:
    """
    Generates controlled abnormal IoT telemetry scenarios with explicit ground-truth labels.
    """

    def __init__(self, random_state: int = 100):
        self.rng = np.random.default_rng(random_state)
        self.normal_device = IoTDevice("device_001", random_state=random_state)

    def generate_dos_flooding(self, device_id: str = "device_001") -> Dict[str, Any]:
        """
        Scenario 1: Denial of Service (DoS) / Message Flooding.
        Characterized by extreme message publishing frequency and high device CPU saturation.
        """
        base = self.normal_device.generate_normal_telemetry()
        base["device_id"] = device_id
        base["timestamp"] = datetime.now(timezone.utc).isoformat()
        base["message_rate"] = round(float(self.rng.uniform(18.0, 45.0)), 2)
        base["cpu_usage"] = round(float(self.rng.uniform(78.0, 98.0)), 2)
        base["network_latency"] = round(float(self.rng.uniform(40.0, 95.0)), 2)
        base["is_anomaly"] = 1
        base["attack_type"] = "dos_flooding"
        return base

    def generate_brute_force_auth(self, device_id: str = "device_002") -> Dict[str, Any]:
        """
        Scenario 2: Brute-Force Credential Stuffing / Unauthorized Access.
        Characterized by sudden repeated failed authentication attempts and slightly elevated CPU.
        """
        base = self.normal_device.generate_normal_telemetry()
        base["device_id"] = device_id
        base["timestamp"] = datetime.now(timezone.utc).isoformat()
        base["failed_auth_count"] = int(self.rng.integers(6, 25))
        base["cpu_usage"] = round(float(self.rng.uniform(35.0, 58.0)), 2)
        base["is_anomaly"] = 1
        base["attack_type"] = "brute_force_auth"
        return base

    def generate_sensor_tampering(self, device_id: str = "device_003") -> Dict[str, Any]:
        """
        Scenario 3: Sensor Tampering / Electrical Fault / Overheating.
        Characterized by dangerous electrical surges or abnormal physical thermal spikes.
        """
        base = self.normal_device.generate_normal_telemetry()
        base["device_id"] = device_id
        base["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Alternate between electrical surge and thermal overheating
        tamper_mode = self.rng.choice(["voltage_surge", "overheating", "voltage_drop"])
        if tamper_mode == "voltage_surge":
            base["voltage"] = round(float(self.rng.uniform(270.0, 315.0)), 2)
        elif tamper_mode == "overheating":
            base["temperature"] = round(float(self.rng.uniform(68.0, 92.0)), 2)
        else:
            base["voltage"] = round(float(self.rng.uniform(140.0, 185.0)), 2)

        base["is_anomaly"] = 1
        base["attack_type"] = "sensor_tampering"
        return base

    def generate_network_degradation(self, device_id: str = "device_001") -> Dict[str, Any]:
        """
        Scenario 4: Network Degradation / Man-in-the-Middle (MITM) Delay.
        Characterized by abnormal packet round-trip time (RTT latency) without physical device faults.
        """
        base = self.normal_device.generate_normal_telemetry()
        base["device_id"] = device_id
        base["timestamp"] = datetime.now(timezone.utc).isoformat()
        base["network_latency"] = round(float(self.rng.uniform(250.0, 750.0)), 2)
        base["is_anomaly"] = 1
        base["attack_type"] = "network_degradation"
        return base

    def generate_labeled_evaluation_dataset(
        self,
        normal_samples: int = 800,
        anomalies_per_type: int = 100
    ) -> pd.DataFrame:
        """
        Generates a strictly labeled ground-truth evaluation dataset.
        Contains a realistic blend of normal traffic alongside all 4 cyberattack scenarios.
        Zero data leakage: Independent random state separate from training data.
        """
        records: List[Dict[str, Any]] = []

        # 1. Normal traffic
        for _ in range(normal_samples):
            item = self.normal_device.generate_normal_telemetry()
            item["is_anomaly"] = 0
            item["attack_type"] = "normal"
            records.append(item)

        # 2. DoS Flooding
        for _ in range(anomalies_per_type):
            records.append(self.generate_dos_flooding())

        # 3. Brute Force Auth
        for _ in range(anomalies_per_type):
            records.append(self.generate_brute_force_auth())

        # 4. Sensor Tampering
        for _ in range(anomalies_per_type):
            records.append(self.generate_sensor_tampering())

        # 5. Network Degradation
        for _ in range(anomalies_per_type):
            records.append(self.generate_network_degradation())

        df = pd.DataFrame(records)
        # Shuffle dataset cleanly
        df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
        return df

    def save_labeled_evaluation_csv(self, output_path: Path) -> Path:
        """Exports labeled ground truth evaluation dataset to CSV."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = self.generate_labeled_evaluation_dataset()
        df.to_csv(output_path, index=False)
        print(f"[SUCCESS] Saved {len(df)} labeled evaluation samples to: {output_path}")
        print(f"         Class distribution:\n{df['attack_type'].value_counts().to_string()}\n")
        return output_path

    def inject_live_attack(
        self,
        attack_type: str,
        device_id: str = "device_001",
        cycles: int = 5,
        interval_sec: float = 1.0
    ):
        """
        Publishes real-time abnormal telemetry over MQTT to test live detection pipelines.
        """
        generators = {
            "dos_flooding": self.generate_dos_flooding,
            "brute_force_auth": self.generate_brute_force_auth,
            "sensor_tampering": self.generate_sensor_tampering,
            "network_degradation": self.generate_network_degradation
        }

        if attack_type not in generators:
            raise ValueError(f"Unknown attack type: {attack_type}. Valid: {list(generators.keys())}")

        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"attack_injector_{attack_type}"
        )

        try:
            print(f"[ATTACK INJECTOR] Connecting to {mqtt_config.broker_host}:{mqtt_config.broker_port}...")
            client.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=mqtt_config.keep_alive)
            client.loop_start()
            time.sleep(0.5)

            topic = f"iot/devices/{device_id}/telemetry"
            print(f"[ATTACK INJECTOR] Injecting '{attack_type}' on {topic} for {cycles} cycles...")

            gen_func = generators[attack_type]
            for i in range(1, cycles + 1):
                payload_data = gen_func(device_id)
                # Keep payload standard by dropping local evaluation labels before publishing
                publish_data = {k: v for k, v in payload_data.items() if k not in ("is_anomaly", "attack_type")}
                client.publish(topic, json.dumps(publish_data), qos=0)
                print(f"  [Cycle {i}/{cycles}] Published injected anomaly: {publish_data}")
                time.sleep(interval_sec)

            print("[ATTACK INJECTOR] Attack sequence completed.")

        finally:
            client.loop_stop()
            client.disconnect()


def main():
    parser = argparse.ArgumentParser(description="IoT Anomaly & Cyberattack Scenario Generator")
    parser.add_argument("--mode", choices=["generate", "inject"], default="generate",
                        help="'generate' saves labeled ground-truth evaluation CSV; 'inject' sends live MQTT attacks")
    parser.add_argument("--attack", choices=["dos_flooding", "brute_force_auth", "sensor_tampering", "network_degradation"],
                        default="dos_flooding", help="Type of attack scenario")
    parser.add_argument("--device", type=str, default="device_001", help="Target device ID")
    parser.add_argument("--cycles", type=int, default=5, help="Number of anomaly packets to inject")
    parser.add_argument("--interval", type=float, default=1.0, help="Interval between attack packets")
    args = parser.parse_args()

    generator = AttackScenarioGenerator(random_state=100)

    if args.mode == "generate":
        output_file = BASE_DIR / "data" / "attack_scenarios" / "labeled_evaluation_data.csv"
        generator.save_labeled_evaluation_csv(output_file)
    else:
        generator.inject_live_attack(
            attack_type=args.attack,
            device_id=args.device,
            cycles=args.cycles,
            interval_sec=args.interval
        )


if __name__ == "__main__":
    main()
