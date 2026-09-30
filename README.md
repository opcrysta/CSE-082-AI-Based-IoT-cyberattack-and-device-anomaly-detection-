# AI-Based IoT Cyberattack and Device Anomaly Detection (Project P_310)

## Overview
This project develops an end-to-end prototype for monitoring Internet of Things (IoT) telemetry and detecting anomalous behaviour and cyberattack patterns using unsupervised Machine Learning (Isolation Forest).

### Tech Stack
- **IoT Telemetry & Simulator**: Python 3.11, Paho-MQTT v2.x
- **Message Broker**: Eclipse Mosquitto (MQTT over port 1883)
- **Data & Feature Engineering**: NumPy, Pandas, Pydantic
- **Machine Learning**: Scikit-Learn (Isolation Forest), Joblib
- **Time-Series Storage**: InfluxDB v2
- **Visualization**: Grafana
- **Testing**: Pytest

---

## Architecture Flow
```text
Python IoT Device Simulator
        │ (JSON over MQTT)
        ▼
Eclipse Mosquitto Broker (Port 1883)
        │ (Topic: iot/devices/+/telemetry)
        ▼
MQTT Collector & Validator (Pydantic schema check)
        │ (Standardized Feature Vector)
        ▼
Isolation Forest ML Engine (Unsupervised anomaly scoring)
        │ (Normal=1, Anomaly=-1 + Anomaly Score)
        ▼
Alert Engine & Enrichment Rules
        │
   ┌────┴──────────────────────────┐
   ▼                               ▼
InfluxDB (Time-series data)    MQTT Alert Topic (iot/alerts)
   │
   ▼
Grafana Dashboard (Real-time telemetry, anomaly scores & alerts)
```

---

## Project Structure
```text
CSE-082-AI-Based-IoT-cyberattack-and-device-anomaly-detection-/
├── config/
│   ├── __init__.py
│   └── settings.py          # Centralized configuration & environment loader
├── simulator/
│   └── __init__.py          # Multi-device telemetry & attack simulator
├── collector/
│   └── __init__.py          # MQTT subscriber & data validation
├── detection/
│   └── __init__.py          # Isolation Forest training & real-time inference
├── alerts/
│   └── __init__.py          # Rule enrichment and alerting
├── storage/
│   └── __init__.py          # InfluxDB client and persistence logic
├── tests/
│   └── __init__.py          # Pytest automated test suite
├── data/
│   ├── normal/              # Clean baseline telemetry for training
│   └── attack_scenarios/    # Labeled test datasets (DoS, brute-force, sensor tampering)
├── docker/
│   ├── docker-compose.yml   # Mosquitto, InfluxDB, and Grafana containers
│   └── mosquitto.conf       # MQTT broker configuration
├── models/                  # Persisted scikit-learn models (.joblib)
├── requirements.txt         # Core dependencies
├── .env.example             # Template environment variables
├── .gitignore               # Ignored files (venv, models, secrets, data)
└── README.md
```

---

## Milestone 1 Status: COMPLETED ✅
- Created isolated Python virtual environment (`venv`).
- Installed all core dependencies (`paho-mqtt`, `scikit-learn`, `pandas`, `numpy`, `joblib`, `pydantic`, `influxdb-client`, `pytest`).
- Established modular directory layout and centralized configuration ([config/settings.py](config/settings.py)).
- Verified package imports and runtime health.

---

## Milestone 2 Status: COMPLETED ✅
- Verified local Mosquitto MQTT broker on port 1883.
- Implemented test subscriber ([collector/test_subscriber.py](collector/test_subscriber.py)) with wildcard topic subscription `iot/devices/+/telemetry`.
- Implemented test publisher ([simulator/test_publisher.py](simulator/test_publisher.py)) sending structured JSON telemetry.
- Created automated integration test ([tests/test_mqtt_baseline.py](tests/test_mqtt_baseline.py)) passing with 100% success via `pytest`.

---

## Milestone 3 Status: COMPLETED ✅
- Implemented multi-device telemetry generator ([simulator/device_simulator.py](simulator/device_simulator.py)) using realistic Gaussian distributions and seed control for reproducibility.
- Supports both live multi-device MQTT publishing (`--mode stream`) and clean baseline dataset export (`--mode generate`).
- Generated 2,100 clean, normal baseline observations saved to `data/normal/baseline_telemetry.csv` for Isolation Forest training with 0 data leakage.
- Added comprehensive unit and bound tests ([tests/test_simulator.py](tests/test_simulator.py)) passing with 100% test suite success (4/4 tests).

---

## Milestone 4 Status: COMPLETED ✅
- Created controlled cyberattack and anomaly scenario generator ([simulator/attack_scenarios.py](simulator/attack_scenarios.py)).
- Implemented 4 specific IoT threat models:
  1. **DoS / Message Flooding:** Rate: 18-45 msg/s, CPU: 78-98%.
  2. **Brute-Force Authentication:** Repeated failed logins: 6-25 attempts/cycle.
  3. **Sensor Tampering / Overheating:** Voltage surges (270-315V), drops (140-185V), and thermal spikes (68-92°C).
  4. **Network Degradation:** Latency spikes: 250-750 ms.
- Exported ground-truth labeled evaluation dataset (1,200 samples: 800 normal, 100 per attack) to `data/attack_scenarios/labeled_evaluation_data.csv`.
- Added unit tests ([tests/test_attack_scenarios.py](tests/test_attack_scenarios.py)), bringing full test suite to 9/9 passing tests.

---

## Milestone 5 Status: COMPLETED ✅
- Implemented Pydantic-based schema validation ([collector/data_validator.py](collector/data_validator.py)) ensuring robust error handling and bad packet rejection.
- Implemented deterministic feature extractor ([collector/feature_extractor.py](collector/feature_extractor.py)) standardizing inputs to ordered 2D NumPy arrays `(1, 7)` for scikit-learn.
- Integrated the authentic UNSW Canberra **TON_IoT Telemetry Dataset** ([simulator/ton_iot_replay.py](simulator/ton_iot_replay.py)) supporting live MQTT replay and exporting curated benchmark test set (`data/attack_scenarios/ton_iot_benchmark.csv`).
- Expanded test suite to 15/15 passing tests ([tests/test_validation_and_features.py](tests/test_validation_and_features.py)).

---

## Milestone 6 Status: COMPLETED ✅
- Built Isolation Forest training module ([detection/train_model.py](detection/train_model.py)) and trained on 2,100 clean baseline records with 0 data leakage.
- Persisted full model artifact and metadata package to `models/isolation_forest.joblib` using Joblib.
- Built real-time inference engine ([detection/predict.py](detection/predict.py)) computing binary classifications (`1`/`-1`), decision function scores, and calibrated continuous risk probabilities (`0.0` - `1.0`).
- Validated detection sensitivity across DoS floods, brute-force logins, and hardware tampering with 21/21 passing automated tests ([tests/test_detection.py](tests/test_detection.py)).

---

## Milestone 7 Status: COMPLETED ✅
- Built Security Threat Attribution & Alert Engine ([alerts/alert_engine.py](alerts/alert_engine.py)) implementing 2-tier verification:
  - Differentiates genuine cyber threats (DoS floods, brute-force logins, MITM degradation) from benign hardware/environmental faults (electrical surges, overheating).
  - Emits structured alert events with severity (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`), threat category, and actionable mitigation guidance.
- Implemented production Central MQTT Collector Service ([collector/mqtt_collector.py](collector/mqtt_collector.py)):
  - Validates incoming device telemetry on `iot/devices/+/telemetry`.
  - Executes real-time Isolation Forest inference.
  - Automatically attributes and publishes live alert notifications to `iot/alerts`.
- Added end-to-end integration tests ([tests/test_alert_and_pipeline.py](tests/test_alert_and_pipeline.py)), expanding test suite to 26/26 passing tests.

---

## Milestone 8 Status: COMPLETED ✅
- Configured InfluxDB v2 container service running on port `8086` (`iot_security_org`, bucket `iot_telemetry`).
- Built time-series persistence service ([storage/database.py](storage/database.py)) storing multi-dimensional telemetry, Isolation Forest scores, and alert events.
- Implemented industrial Edge Store-and-Forward SQLite buffer (`data/cache/offline_buffer.db`) ensuring zero-data-loss when the database is unreachable or recovering.
- Wired automatic database persistence into [collector/mqtt_collector.py](collector/mqtt_collector.py).
- Added comprehensive unit and persistence tests ([tests/test_storage.py](tests/test_storage.py)), bringing full test suite to 28/28 passing tests.

---

## Milestone 9 Status: COMPLETED ✅
- Launched Grafana 10.4.0 container on port `3000` (`admin`/`admin`).
- Configured automatic datasource provisioning ([docker/grafana/provisioning/datasources/influxdb.yml](docker/grafana/provisioning/datasources/influxdb.yml)) pointing to InfluxDB v2 using Flux.
- Designed and provisioned complete operational dashboard ([grafana/iot_security_dashboard.json](grafana/iot_security_dashboard.json)):
  - **Gauge:** Real-time Anomaly Risk Score (Green $<0.35$, Yellow $0.35 - 0.70$, Red $>0.70$).
  - **Stats:** Total Observations, ML Flagged Anomalies, Actionable Cyber Incidents.
  - **Time Series:** Physical Telemetry (Temp/Volt) & Compute/Network Saturation (CPU%/Message Rate).
  - **Security Incident Feed:** Real-time table of recent alerts, threat names, severity, and mitigation advice.
- Added Grafana provisioning and dashboard schema tests ([tests/test_grafana.py](tests/test_grafana.py)), expanding test suite to 30/30 passing tests.

---

## Milestone 10 Status: COMPLETED ✅ (100% Project Completion)
- Developed offline quantitative evaluation engine ([detection/evaluate_model.py](detection/evaluate_model.py)).
- Evaluated Isolation Forest against both synthetic threat scenarios and the authentic UNSW Canberra **TON_IoT** dataset.
- Persisted verified benchmark results to [models/evaluation_report.json](models/evaluation_report.json).
- Created turnkey end-to-end live demonstration runner ([run_pipeline_demo.py](run_pipeline_demo.py)).
- Documented 10 in-depth B.Tech CSE project viva questions and technical explanations ([docs/viva_questions.md](docs/viva_questions.md)).
- Added automated evaluation tests ([tests/test_evaluation.py](tests/test_evaluation.py)), bringing the complete test suite to **33/33 passing tests (100% pass rate)**.

---

## Quantitative Evaluation & Benchmark Results

### 1. Overall Performance Metrics
| Metric | Synthetic Threat Scenarios (1,200 records) | UNSW TON_IoT Benchmark (1,811 records) | Industrial Significance |
| :--- | :---: | :---: | :--- |
| **Accuracy** | **87.00%** | **88.63%** | Overall correct classification rate |
| **Precision** | **82.80%** | **100.00%** | Zero false alarms on normal TON_IoT thermostat traffic |
| **Recall (Sensitivity)** | **77.00%** | **74.60%** | Proportion of actual attacks detected and isolated |
| **Specificity (TNR)** | **92.00%** | **100.00%** | Normal operational telemetry unflagged |
| **False Positive Rate** | **8.00%** | **0.00%** | Benign telemetry falsely alarmed |
| **$F_1$-Score** | **0.7979** | **0.8545** | Harmonic mean balancing precision and recall |
| **ROC-AUC Score** | **0.9364** | **0.8805** | High discriminatory power independent of decision threshold |

### 2. Detection Rate by Threat Category
| Threat Category | Dataset Origin | Total Samples | Detected | Recall Rate | Root Cause & Detection Mechanism |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **DoS / Flooding** | Synthetic | 100 | 100 | **100.00%** | Extreme message rate ($>30$ msg/s) & CPU saturation ($>85\%$) |
| **Brute-Force Auth** | Synthetic | 100 | 100 | **100.00%** | Repeated failed logins violations ($\text{failed\_auth} > 5$) |
| **Backdoor** | UNSW TON_IoT | 150 | 150 | **100.00%** | High CPU/RAM utilization from reverse shell processes |
| **Password Attack** | UNSW TON_IoT | 150 | 150 | **100.00%** | Multi-attempt authentication bursts |
| **Ransomware** | UNSW TON_IoT | 150 | 150 | **100.00%** | Resource exhaustion and memory spikes from encryption activity |
| **Port Scanning** | UNSW TON_IoT | 61 | 43 | **70.49%** | Network probe latency jitter and state transitions |
| **XSS / Web Attack** | UNSW TON_IoT | 150 | 112 | **74.67%** | Elevated transport and latency characteristics |
| **Sensor Tampering** | Synthetic | 100 | 62 | **62.00%** | Multidimensional electrical overvoltage & thermal anomalies |
| **Network Degradation**| Synthetic | 100 | 46 | **46.00%** | Network latency spikes without device load |
| **SQL/Command Injection**| UNSW TON_IoT | 150 | 0 | **0.00%** | *Insight:* Silent payload inside HTTP body; requires DPI/WAF |

---

## Quickstart & Viva Demonstration Guide

### 1. Run Complete Automated Test Suite (33 Tests)
```powershell
.\venv\Scripts\pytest.exe -v tests/
```

### 2. Run Offline Model Evaluation & Benchmark Report
```powershell
.\venv\Scripts\python.exe detection/evaluate_model.py
```

### 3. Run Turnkey Live Pipeline Demonstration (Recommended for Viva)
```powershell
.\venv\Scripts\python.exe run_pipeline_demo.py
```
This single turnkey script:
1. Validates Mosquitto (port 1883), InfluxDB (port 8086), and Grafana (port 3000).
2. Spawns the central MQTT Collector and Isolation Forest pipeline in the background.
3. Generates normal baseline telemetry across 3 virtual IoT devices.
4. Injects live DoS Flooding, Brute-Force Authentication, and Electrical Voltage Surges.
5. Displays real-time threat attribution and alerts.
6. Persists points to InfluxDB and confirms Grafana dashboard readiness.

### 4. Access Live Dashboards & Database
- **Grafana Security Overview:** [http://localhost:3000/d/iot-security-overview](http://localhost:3000/d/iot-security-overview) (Login: `admin` / `admin`)
- **InfluxDB Time-Series Explorer:** [http://localhost:8086](http://localhost:8086) (Org: `iot_security_org`, Bucket: `iot_telemetry`)
- **Viva Questions & Answers:** [docs/viva_questions.md](docs/viva_questions.md) (10 comprehensive engineering questions).