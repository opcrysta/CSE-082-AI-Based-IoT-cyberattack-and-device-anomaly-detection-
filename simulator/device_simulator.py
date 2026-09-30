"""
Multi-Device IoT Telemetry Simulator
Generates realistic, reproducible normal telemetry for multiple edge devices.
Supports both live MQTT streaming and offline dataset generation for ML training.
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
from config.settings import mqtt_config, sim_config, model_config, BASE_DIR


class IoTDevice:
    """
    Simulates an individual IoT edge device with realistic telemetry dynamics.
    """

    def __init__(self, device_id: str, random_state: int = 42):
        self.device_id = device_id
        # Seed generator uniquely per device for reproducible yet independent streams
        device_seed = random_state + int(device_id.split("_")[-1]) if "_" in device_id else random_state
        self.rng = np.random.default_rng(device_seed)

        # Baseline parameters with small device-specific variations
        self.base_temp = 25.0 + self.rng.uniform(-2.0, 2.0)
        self.base_voltage = 230.0 + self.rng.uniform(-2.0, 2.0)
        self.base_cpu = 15.0 + self.rng.uniform(-3.0, 3.0)
        self.base_ram = 40.0 + self.rng.uniform(-4.0, 4.0)
        self.base_latency = 15.0 + self.rng.uniform(-2.0, 2.0)

    def generate_normal_telemetry(self) -> Dict[str, Any]:
        """
        Generates a single normal telemetry reading following Gaussian noise distributions.
        Normal operations exhibit low CPU, 0 failed auths, nominal voltage and temperatures.
        """
        temp = float(np.clip(self.rng.normal(self.base_temp, 1.2), 15.0, 40.0))
        voltage = float(np.clip(self.rng.normal(self.base_voltage, 2.5), 215.0, 245.0))
        cpu = float(np.clip(self.rng.normal(self.base_cpu, 3.0), 2.0, 35.0))
        ram = float(np.clip(self.rng.normal(self.base_ram, 2.0), 20.0, 60.0))
        msg_rate = float(np.clip(self.rng.normal(1.0, 0.08), 0.7, 1.3))
        # Normal operational state has 0 failed logins, with rare (2%) transient re-auth retries
        failed_auth = int(self.rng.choice([0, 1], p=[0.98, 0.02]))
        latency = float(np.clip(self.rng.normal(self.base_latency, 2.5), 5.0, 35.0))

        return {
            "device_id": self.device_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "temperature": round(temp, 2),
            "voltage": round(voltage, 2),
            "cpu_usage": round(cpu, 2),
            "ram_usage": round(ram, 2),
            "message_rate": round(msg_rate, 2),
            "failed_auth_count": int(failed_auth),
            "network_latency": round(latency, 2)
        }


class MultiDeviceSimulator:
    """
    Manages a fleet of simulated IoT devices.
    """

    def __init__(self, num_devices: int = 3, random_state: int = 42):
        self.devices = [
            IoTDevice(f"device_{i+1:03d}", random_state=random_state)
            for i in range(num_devices)
        ]

    def generate_batch_dataset(self, samples_per_device: int = 700) -> pd.DataFrame:
        """
        Generates a clean baseline dataset across all devices for ML training.
        Guarantees reproducible normal operational data with zero data leakage.
        """
        records: List[Dict[str, Any]] = []
        for device in self.devices:
            for _ in range(samples_per_device):
                reading = device.generate_normal_telemetry()
                records.append(reading)

        df = pd.DataFrame(records)
        return df

    def save_baseline_csv(self, output_path: Path, samples_per_device: int = 700) -> Path:
        """Saves generated baseline normal telemetry to CSV."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df = self.generate_batch_dataset(samples_per_device=samples_per_device)
        df.to_csv(output_path, index=False)
        print(f"[SUCCESS] Saved {len(df)} normal training samples to: {output_path}")
        return output_path

    def start_live_streaming(self, interval_sec: float = 2.0, max_iterations: int = None):
        """
        Continuously streams telemetry for all devices to Mosquitto MQTT broker.
        """
        client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id="fleet_telemetry_simulator"
        )

        try:
            print(f"[INFO] Connecting simulator to broker at {mqtt_config.broker_host}:{mqtt_config.broker_port}...")
            client.connect(mqtt_config.broker_host, mqtt_config.broker_port, keepalive=mqtt_config.keep_alive)
            client.loop_start()
            time.sleep(0.5)

            print(f"[INFO] Starting live telemetry stream for {len(self.devices)} devices (Interval: {interval_sec}s)...")
            print("[INFO] Press Ctrl+C to stop streaming.\n")

            iteration = 0
            while max_iterations is None or iteration < max_iterations:
                iteration += 1
                for device in self.devices:
                    telemetry = device.generate_normal_telemetry()
                    topic = f"iot/devices/{device.device_id}/telemetry"
                    payload = json.dumps(telemetry)

                    client.publish(topic, payload, qos=0)
                    print(
                        f"[{telemetry['timestamp']}] Published {device.device_id} -> "
                        f"Temp: {telemetry['temperature']} C, Volt: {telemetry['voltage']}V, "
                        f"CPU: {telemetry['cpu_usage']}%, Rate: {telemetry['message_rate']} msg/s"
                    )

                time.sleep(interval_sec)

        except KeyboardInterrupt:
            print("\n[INFO] Stopped live simulation.")
        except ConnectionRefusedError:
            print(f"[ERROR] Could not connect to Mosquitto at {mqtt_config.broker_host}:{mqtt_config.broker_port}.")
        finally:
            client.loop_stop()
            client.disconnect()
            print("[INFO] Simulator disconnected.")


def main():
    parser = argparse.ArgumentParser(description="IoT Telemetry Fleet Simulator")
    parser.add_argument("--mode", choices=["stream", "generate"], default="stream",
                        help="'stream' to publish live via MQTT; 'generate' to export normal training CSV")
    parser.add_argument("--devices", type=int, default=sim_config.num_devices,
                        help="Number of IoT devices to simulate")
    parser.add_argument("--samples", type=int, default=700,
                        help="Samples per device when generating dataset")
    parser.add_argument("--interval", type=float, default=sim_config.interval_sec,
                        help="Interval in seconds between telemetry cycles")
    args = parser.parse_args()

    simulator = MultiDeviceSimulator(num_devices=args.devices, random_state=42)

    if args.mode == "generate":
        output_file = BASE_DIR / "data" / "normal" / "baseline_telemetry.csv"
        simulator.save_baseline_csv(output_file, samples_per_device=args.samples)
    else:
        simulator.start_live_streaming(interval_sec=args.interval)


if __name__ == "__main__":
    main()
