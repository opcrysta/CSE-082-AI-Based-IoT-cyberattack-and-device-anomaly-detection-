# Software Requirements Specification (SRS)
## AI-Based IoT Cyberattack and Device Anomaly Detection
### Project Identification: CSE-082 / P_310
**Standard:** IEEE Std 830-1998 Compliant  
**Version:** 1.0  
**Date:** October 2026  
**Status:** Approved / Production Deployed  

---

## Executive Summary & Title Page

| Project Metadata | Specification Details |
| :--- | :--- |
| **Project Title** | AI-Based IoT Cyberattack and Device Anomaly Detection |
| **Project Code** | P_310 / CSE-082 |
| **Academic Degree** | Bachelor of Technology (B.Tech) in Computer Science & Engineering |
| **System Classification** | Edge-to-Cloud Distributed Intrusion Detection System (IDS) & Telemetry Analytics |
| **Target Infrastructure** | Multi-Container Microservices Architecture (Docker, Linux/Windows) |
| **Core Algorithms** | Unsupervised Isolation Forest, Sigmoid Risk Calibration, 2-Tier Threat Attribution |
| **Storage & UI Engine** | InfluxDB v2 (TSM Engine, Flux) & Grafana SOC Operations Center |

---

## Table of Contents
1. [Introduction](#1-introduction)
   - 1.1 Purpose
   - 1.2 Document Conventions
   - 1.3 Intended Audience & Reading Suggestions
   - 1.4 Project Scope
   - 1.5 Academic & Engineering References
2. [Overall Description](#2-overall-description)
   - 2.1 Product Perspective & System Architecture
   - 2.2 Product Functions
   - 2.3 User Classes and Characteristics
   - 2.4 Operating Environment
   - 2.5 Design and Implementation Constraints
   - 2.6 Assumptions and Dependencies
3. [External Interface Requirements](#3-external-interface-requirements)
   - 3.1 User Interfaces (SOC Dashboard)
   - 3.2 Hardware Interfaces (Virtual & Physical IoT Microcontrollers)
   - 3.3 Software Interfaces (MQTT, InfluxDB, Grafana, SQLite3)
   - 3.4 Communications Interfaces (Protocols & Serialization)
4. [System Features & Functional Requirements](#4-system-features--functional-requirements)
   - 4.1 Telemetry Ingestion & Pydantic Validation (FR-1 to FR-3)
   - 4.2 Feature Engineering & Vectorization (FR-4)
   - 4.3 Unsupervised Anomaly Detection Engine (FR-5 to FR-6)
   - 4.4 2-Tier Threat Attribution & Alert Dispatch (FR-7 to FR-8)
   - 4.5 Dual-Tier Time-Series Persistence & Edge Buffering (FR-9 to FR-10)
   - 4.6 Attack Generation & UNSW TON_IoT Benchmarking (FR-11 to FR-12)
5. [Non-Functional Requirements (NFRs)](#5-non-functional-requirements)
   - 5.1 Performance & Latency Requirements
   - 5.2 Reliability & Fault Tolerance (Zero-Data-Loss Buffer)
   - 5.3 Security & Isolation Requirements
   - 5.4 Maintainability, Portability & Deployment
6. [Verification, Validation & Testing Matrix](#6-verification-validation--testing-matrix)
7. [Appendix: Mathematical Formulations & Data Schemas](#7-appendix-mathematical-formulations--data-schemas)

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) defines the functional, behavioral, environmental, and architectural specifications for the **AI-Based IoT Cyberattack and Device Anomaly Detection System (Project P_310)**. This document provides a complete contractual basis for development, system validation, deployment, and academic examination.

### 1.2 Document Conventions
- **IEEE Std 830-1998 Guidelines:** Structured according to recommended IEEE practice for software requirements specifications.
- **Priority Identifiers:**
  - `[MANDATORY]`: Core operational requirement required for project completion.
  - `[DESIRABLE]`: Enhances diagnostic visibility or resilience.
- **Requirement Tagging:**
  - `FR-X`: Functional Requirement number $X$.
  - `NFR-X`: Non-Functional Requirement number $X$.

### 1.3 Intended Audience & Reading Suggestions
- **Project Evaluation Committee / University Examiners:** Focus on Sections 1.4, 2.1, 4.3, 4.4, 6, and 7.
- **Security Operations Center (SOC) Engineers:** Focus on Sections 3.1, 4.4, and 5.3.
- **DevOps & Edge Deployment Engineers:** Focus on Sections 2.4, 3.4, 5.2, and 5.4.

### 1.4 Project Scope
The system addresses the critical security challenge in modern Internet of Things (IoT) deployments: resource-constrained edge devices (smart thermostats, industrial microcontrollers, grid monitors) cannot execute heavy signature-based antivirus or host intrusion prevention systems (HIPS). 

The scope includes:
1. Emulation of multi-device Gaussian telemetry and live multi-vector cyberattacks.
2. Ingestion via the lightweight, industry-standard MQTT protocol (Eclipse Mosquitto).
3. Real-time Pydantic data schema validation and 7-dimensional feature engineering.
4. Fast, unsupervised anomaly detection using an ensemble of Isolation Trees (iTrees) without reliance on biased or unavailable labeled attack datasets.
5. Continuous mathematical risk score calibration via Sigmoid normalization ($0.0 - 1.0$).
6. A two-tier Alert Engine distinguishing malicious cyber threats (DoS Flooding, Brute-Force Auth) from hardware/sensor electrical faults (Voltage Surges, Sensor Drift).
7. High-throughput time-series persistence in InfluxDB v2 with an edge SQLite3 store-and-forward fallback buffer for zero-data-loss resiliency.
8. Automated provisioning of an enterprise-grade Grafana Security Operations Center (SOC) dashboard.
9. Empirical quantitative benchmarking against the real-world UNSW Canberra TON_IoT dataset.

### 1.5 Academic & Engineering References
1. **IEEE Std 830-1998:** *IEEE Recommended Practice for Software Requirements Specifications.*
2. **Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008):** *Isolation Forest.* Eighth IEEE International Conference on Data Mining (ICDM '08), pp. 413–422.
3. **Alsaedi, A., Moustafa, N., Tari, Z., Mahmood, A., & Anwar, A. (2020):** *TON_IoT Telemetry Dataset: A New Generation Dataset of IoT and IIoT Systems for Data-Driven Cyber Security Applications.* IEEE Access, 8, 165130-165150.
4. **OASIS Standard:** *MQTT Version 5.0 & Version 3.1.1 Specification.* OASIS Open, 2019.
5. **InfluxData Documentation:** *InfluxDB v2 Time-Series Engine and Flux Language Specification (2024).*
6. **Grafana Labs:** *Grafana Provisioning and Dashboard Schema v10.4 (2024).*

---

## 2. Overall Description

### 2.1 Product Perspective & System Architecture
The system operates as an edge-and-cloud distributed pipeline consisting of five decoupled sub-systems:

```mermaid
graph TD
    subgraph Device Layer
        V1["Virtual Device 001 (Gateway)"] -->|JSON / MQTT 1883| BRK["Mosquitto MQTT Broker<br>(iot/devices/+/telemetry)"]
        V2["Virtual Device 002 (Thermostat)"] -->|JSON / MQTT 1883| BRK
        V3["Virtual Device 003 (Industrial Power)"] -->|JSON / MQTT 1883| BRK
        ATK["Attack Generator / TON_IoT Replay"] -->|Injected Payloads| BRK
    end

    subgraph Central AI Collector & Detection Core
        BRK -->|Wildcard Subscription| COL["MQTT Collector Service"]
        COL -->|Schema Check| VAL["Pydantic Data Validator"]
        VAL -->|Valid Payload| EXT["7-D Feature Vectorizer"]
        VAL -->|Invalid Payload| REJ["Malformed Packet Rejection Log"]
        EXT -->|Feature Vector (1x7)| IFO["Isolation Forest Model<br>(100 Trees, Contamination=0.05)"]
        IFO -->|Binary Score & Raw Value| SIG["Sigmoid Risk Calibrator<br>(Continuous 0.0 - 1.0)"]
        SIG -->|High Risk / Outlier| ENG["2-Tier Threat Attribution Engine"]
        ENG -->|Attributed Cyber Threat| PUB["Alert Publisher<br>(Topic: iot/alerts)"]
        PUB -->|Alert JSON| BRK
    end

    subgraph Resilient Storage Layer
        ENG -->|Telemetry + Risk + Alert| STG["Storage Service"]
        STG -->|Primary Path (Online)| TSDB["InfluxDB v2 Engine<br>(Bucket: iot_telemetry)"]
        STG -.->|Network Partition Fallback| SQL["Edge SQLite3 Buffer<br>(offline_buffer.db)"]
        SQL -.->|Auto-Flush on Reconnect| TSDB
    end

    subgraph SOC Visualization & Analytics
        TSDB -->|Flux Queries (5s Poll)| GRF["Grafana Dashboard v10.4<br>(Executive SOC Overview)"]
        GRF -->|Encrypted Edge Tunnel| PUB_URL["Live Cloudflare URL<br>(trycloudflare.com)"]
        PUB_URL --> ANALYST["SOC Analyst / Evaluator"]
    end
```

### 2.2 Product Functions
1. **Telemetry Ingestion:** Ingests asynchronous sensor metrics via MQTT with wildcard topic routing (`iot/devices/+/telemetry`).
2. **Schema Sanitization:** Filters and rejects malformed, out-of-range, or corrupted payloads using strict type enforcement.
3. **Statistical Outlier Isolation:** Isolates structural and dimensional anomalies by recursive partitioning across random hyperplanes without requiring prior attack labels.
4. **Threat Disambiguation:** Resolves whether an anomaly is a genuine cyberattack (Denial-of-Service, Brute-Force Auth) or an environmental/electrical hardware anomaly (Overvoltage, Sensor Degradation).
5. **Real-Time SOC Dispatch:** Transmits structured JSON alert payloads over MQTT to `iot/alerts` with severity ratings (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) and actionable remediation guidelines.
6. **Time-Series Persistence:** Stores granular measurements with sub-millisecond timestamps, indexed by `device_id`.
7. **Zero-Data-Loss Reliability:** Transparently routes records to a local SQLite database during database outages and flushes upon reconnection.
8. **Executive SOC Visualization:** Renders real-time fleet risk gauges, dual-axis telemetry graphs, and incident tables with 5-second dynamic polling.

### 2.3 User Classes and Characteristics
- **SOC Security Analyst (Primary User):** Monitors the Grafana live dashboard, inspects incident tables, isolates rogue devices, and reads automated mitigation recommendations.
- **IoT Network Administrator:** Configures MQTT topics, device fleets, network credentials, and broker policies.
- **Academic Evaluator / Examiner:** Validates quantitative evaluation metrics ($F_1$-score, ROC-AUC, confusion matrix), tests attack bursts, and reviews architectural adherence to software engineering standards.

### 2.4 Operating Environment
The system is fully containerized and runs on any platform supporting Docker:
- **Host Operating Systems:** Windows 10/11 (PowerShell / Docker Desktop), Linux (Ubuntu 20.04/22.04 LTS, Debian 12), macOS (Docker Desktop).
- **Container Engine:** Docker Engine v24.0+ and Docker Compose v2.20+.
- **Runtime Environment:** Python 3.11.9.
- **Message Broker:** Eclipse Mosquitto v2.0+.
- **Time-Series Engine:** InfluxDB v2.7 (TSM / TSI storage engines).
- **Visualization Server:** Grafana v10.4.0.
- **Cloud Tunnel:** Cloudflare Edge Daemon (`cloudflared` v2026+).

### 2.5 Design and Implementation Constraints
1. **Unsupervised Learning Constraint:** In real-world IoT environments, novel zero-day attacks have no historical labels. Therefore, the core model must be trained solely on benign baseline telemetry.
2. **Edge Telemetry Payload Constraint:** Telemetry must be captured at the transport/system level (CPU, RAM, message rate, latency, failed logins, voltage, temperature) without relying on deep packet inspection (DPI), which edge microcontrollers cannot afford.
3. **Windows File Encoding Constraint:** Scripts, JSON templates, and logging endpoints must enforce strict UTF-8 / ASCII compliance to prevent `cp1252` encoding exceptions on Windows hosts.

### 2.6 Assumptions and Dependencies
- Network connectivity on TCP ports `1883` (Mosquitto), `8086` (InfluxDB), and `3000` (Grafana).
- Edge devices provide monotonically increasing ISO-8601 timestamps or rely on central collector reception time.

---

## 3. External Interface Requirements

### 3.1 User Interfaces (SOC Dashboard)
The primary interface is the Grafana Security Operations Center (SOC) Executive Dashboard (`grafana/iot_security_dashboard.json`), accessible via Web Browser.

| Dashboard Panel | Panel Type | Data Source & Flux Query | Operational Purpose |
| :--- | :--- | :--- | :--- |
| **Fleet Threat Level** | Gauge | `range(start: -1m) \|> last() \|> max()` | Displays instantaneous 60s fleet risk (0–100%) with Green/Yellow/Red bands. |
| **Outliers Flagged** | Stat Card | `filter(is_anomaly == 1) \|> count()` | Displays cumulative anomalies detected over the time window. |
| **Critical Threats** | Stat Card | `filter(severity == "CRITICAL") \|> count()` | Highlights severe cyberattacks requiring immediate SOC intervention. |
| **Active Devices** | Stat Card | `distinct(device_id) \|> count()` | Live fleet count actively transmitting telemetry. |
| **Multi-Metric Telemetry** | Time-Series | Pivoted table with dual Y-axes | Compares CPU %, RAM %, and Voltage against the Focus Device variable (`$device`). |
| **Message Rate & Latency** | Time-Series | Pivoted table with smooth gradients | Identifies transport bottlenecks, DoS spikes, and network jitter. |
| **Calibrated Risk History**| Time-Series | `calibrated_risk_score` over time | Continuous risk curve comparing baseline (0.1–0.2) vs attack bursts (0.8–0.95). |
| **SOC Incident Table** | Table | Filtered `security_alerts` measurement | Shows Time, Device, Category, Threat Name, Severity, and Recommended Action. |

### 3.2 Hardware Interfaces
- **Virtual IoT Emulators:** 3 Gaussian-distributed nodes simulating Gateway, Thermostat, and Industrial Controller.
- **Physical Hardware Compatibility:** Standard microcontrollers (ESP32, ESP8266, Arduino Nano 33 IoT, Raspberry Pi 4/Zero 2W) transmitting JSON over 2.4GHz Wi-Fi / Ethernet to TCP 1883.

### 3.3 Software Interfaces
- **Mosquitto MQTT API:** Paho-MQTT Client API v2 utilizing callback protocol `CallbackAPIVersion.VERSION2`.
- **InfluxDB v2 Client API:** `influxdb-client-python` v1.38+ utilizing the `Point` data class and `SYNCHRONOUS` write options.
- **SQLite3 C-API:** Native Python `sqlite3` driver with transactional ACID write semantics.
- **Scikit-Learn Model API:** `joblib` serialization format for loading the compiled `IsolationForest` estimator object.

### 3.4 Communications Interfaces
- **MQTT Transport:** Port `1883` (unencrypted local / container network) or Port `8883` (TLS v1.3 production).
- **HTTP/REST Transport:** Port `8086` for InfluxDB read/write API (`/api/v2/write`, `/api/v2/query`).
- **Web UI Transport:** Port `3000` for Grafana HTTP interface.
- **Encrypted Public Tunnel:** Cloudflare QUIC/HTTP2 tunnel outbound to Cloudflare Edge.

---

## 4. System Features & Functional Requirements

### 4.1 Telemetry Ingestion & Pydantic Validation

#### FR-1: MQTT Wildcard Ingestion
- **Description:** The system shall establish an asynchronous connection to the MQTT broker and subscribe to the topic pattern `iot/devices/+/telemetry`.
- **Inputs:** Raw binary MQTT message payload.
- **Outputs:** Decoded UTF-8 JSON string.
- **Priority:** `[MANDATORY]`

#### FR-2: Strict Pydantic Schema Validation
- **Description:** Every payload shall be validated against the `IoTTelemetryPayload` Pydantic model before feature extraction.
- **Validation Rules:**
  - `device_id`: Non-empty string ($3 \le \text{length} \le 64$).
  - `temperature`: Floating point, $-40.0^\circ\text{C} \le T \le 125.0^\circ\text{C}$.
  - `voltage`: Floating point, $150.0\text{V} \le V \le 300.0\text{V}$.
  - `cpu_usage`: Floating point, $0.0\% \le \text{CPU} \le 100.0\%$.
  - `ram_usage`: Floating point, $0.0\% \le \text{RAM} \le 100.0\%$.
  - `message_rate`: Floating point, $0.0 \le \text{Rate} \le 1000.0\text{ msg/s}$.
  - `failed_auth_count`: Non-negative integer, $\ge 0$.
  - `network_latency`: Floating point, $0.0 \le \text{Latency} \le 5000.0\text{ ms}$.
- **Priority:** `[MANDATORY]`

#### FR-3: Malformed Packet Rejection
- **Description:** Payloads failing JSON parsing or schema bounds shall be logged with warning tags and dropped without terminating the collector daemon.
- **Priority:** `[MANDATORY]`

---

### 4.2 Feature Engineering & Vectorization

#### FR-4: Standardized Feature Alignment
- **Description:** The system shall convert validated telemetry into a deterministic 2-dimensional NumPy array of shape `(1, 7)` adhering to the invariant column ordering:
  $$\vec{x} = \begin{bmatrix} T, & V, & \text{CPU}, & \text{RAM}, & \text{Rate}, & \text{Auth}, & \text{Latency} \end{bmatrix}$$
- **Priority:** `[MANDATORY]`

---

### 4.3 Unsupervised Anomaly Detection Engine

#### FR-5: Isolation Forest Scoring
- **Description:** The model shall evaluate $\vec{x}$ across an ensemble of 100 randomized isolation trees to produce:
  1. Binary decision: $+1$ (Benign Inlier) or $-1$ (Statistical Anomaly).
  2. Continuous decision function score: $s \in (-\infty, +\infty)$ where lower negative values indicate deep anomalies.
- **Parameters:** `n_estimators=100`, `contamination=0.05`, `random_state=42`.
- **Priority:** `[MANDATORY]`

#### FR-6: Sigmoid Risk Calibration
- **Description:** Raw decision function values shall be transformed into a continuous, human-interpretable risk probability metric:
  $$\text{Risk}(s) = \frac{1}{1 + e^{12 \cdot (s + 0.05)}} \in [0.0, 1.0]$$
  - Benign nominal traffic yields risk $\le 0.25$.
  - Anomalous traffic yields risk $\ge 0.50$.
- **Priority:** `[MANDATORY]`

---

### 4.4 2-Tier Threat Attribution & Alert Dispatch

#### FR-7: Attribution Rule Engine
- **Description:** If a sample is designated as an anomaly ($\text{is\_anomaly} == \text{True}$ or $\text{Risk} \ge 0.50$), the system shall execute deterministic attribution:

| Threat Identifier | Category | Trigger Rule Logic | Severity | Action Recommended |
| :--- | :--- | :--- | :---: | :--- |
| **Denial-of-Service (DoS)** | Cyberattack | `message_rate > 25.0` OR (`cpu > 80.0` AND `message_rate > 10.0`) | `CRITICAL` | Throttle publish rate via Mosquitto ACL; terminate client session. |
| **Brute-Force Auth Attack** | Cyberattack | `failed_auth_count >= 3` | `CRITICAL` | Block device IP address; lock credentials; inspect auth logs. |
| **Electrical Overvoltage** | Hardware Fault | `voltage > 255.0` | `HIGH` | Trip smart circuit breaker; dispatch technician for transformer check. |
| **Electrical Undervoltage** | Hardware Fault | `voltage < 205.0` | `HIGH` | Switch to secondary auxiliary battery; inspect power supply rails. |
| **High Thermal Drift** | Env Fault | `temperature > 65.0` | `MEDIUM` | Activate auxiliary cooling; reduce processing duty cycle. |
| **Sub-Zero Thermal Fault** | Env Fault | `temperature < -10.0` | `MEDIUM` | Engage internal heating element; verify freeze protection. |
| **Network Degradation** | Network Fault | `network_latency > 350.0` | `LOW` | Reroute traffic via alternative mesh path; inspect gateway. |
| **Unclassified Outlier** | Unknown | Multidimensional outlier not matching specific boundary | `LOW` | Log observation; track recurrence over sliding time window. |

#### FR-8: MQTT Alert Publishing
- **Description:** All attributed alerts shall be formatted as structured JSON and published to the central broadcast topic `iot/alerts`.
- **Priority:** `[MANDATORY]`

---

### 4.5 Dual-Tier Time-Series Persistence & Edge Buffering

#### FR-9: InfluxDB v2 Logging
- **Description:** The system shall write two measurements to the `iot_telemetry` bucket:
  1. `device_telemetry`: Tagged by `device_id`, containing all 7 sensor fields, `raw_anomaly_score`, `calibrated_risk_score`, and `is_anomaly`.
  2. `security_alerts`: Tagged by `device_id`, `alert_category`, `threat_name`, `severity`, and `is_cyberattack`.
- **Priority:** `[MANDATORY]`

#### FR-10: SQLite Edge Store-and-Forward Buffer
- **Description:** If InfluxDB becomes unreachable (network disconnection or container crash), writes shall immediately be redirected to `data/cache/offline_buffer.db` (`buffered_telemetry` and `buffered_alerts` tables) with zero data loss. Upon restoration of InfluxDB connectivity, buffered records shall be flushed.
- **Priority:** `[MANDATORY]`

---

### 4.6 Attack Generation & UNSW TON_IoT Benchmarking

#### FR-11: Synthetic Attack Bursts
- **Description:** The simulator shall support controlled generation of 4 attack categories:
  - DoS Message Flooding ($50-100\text{ msg/s}$, $\text{CPU} > 85\%$).
  - Brute-Force Password Cracking ($\text{failed\_auth} \in [5, 20]$).
  - Electrical Voltage Surges ($V \in [265\text{V}, 295\text{V}]$).
  - Latency Jitter Degradation ($\text{latency} \in [400\text{ms}, 1200\text{ms}]$).
- **Priority:** `[MANDATORY]`

#### FR-12: Real-World Dataset Replay (UNSW TON_IoT)
- **Description:** The system shall include an automated replay runner for the UNSW Canberra TON_IoT Thermostat telemetry dataset (1,811 labeled rows) to benchmark real-world attack detection.
- **Priority:** `[MANDATORY]`

---

## 5. Non-Functional Requirements (NFRs)

### 5.1 Performance & Latency Requirements
- **NFR-1 (Inference Latency):** The feature extraction and Isolation Forest prediction cycle must execute in $\le 15.0\text{ ms}$ per telemetry observation on standard x86/ARM hardware.
- **NFR-2 (Throughput Capacity):** The collector pipeline must comfortably process at least $500\text{ messages/second}$ without dropping packets.
- **NFR-3 (Dashboard Freshness):** Grafana panels shall auto-refresh every $5\text{ seconds}$, querying the latest 60-second sliding window.

### 5.2 Reliability & Fault Tolerance
- **NFR-4 (Zero-Data-Loss Edge Fallback):** In the event of a total database outage, all incoming telemetry and alerts must be committed to the local SQLite database buffer.
- **NFR-5 (Resilient Reconnection):** MQTT clients and InfluxDB writers must incorporate exponential backoff reconnect logic without fatal process termination.

### 5.3 Security & Isolation Requirements
- **NFR-6 (Authentication & Access Control):**
  - InfluxDB operations require token authorization (`my-super-secret-iot-token-12345`).
  - Grafana dashboard supports role-based separation: Anonymous Viewer mode for live evaluation and Admin mode (`admin`/`admin`) for panel configuration.
- **NFR-7 (Encrypted Transport):** External public access must be tunneled via Cloudflare SSL/TLS termination.

### 5.4 Maintainability, Portability & Deployment
- **NFR-8 (Turnkey Containerization):** The entire microservices fleet (Mosquitto, InfluxDB, Grafana, ML Pipeline, Cloudflare Tunnel) must build and launch via a single command: `docker compose up -d --build`.

---

## 6. Verification, Validation & Testing Matrix

The implementation is verified through 33 automated Pytest test cases spanning 8 test modules:

| Test Module | Test Name | Target Component | Verification Outcome |
| :--- | :--- | :--- | :---: |
| `test_validation_and_features.py` | `test_data_validator_valid_payload` | `DataValidator` | Valid schema passes |
| `test_validation_and_features.py` | `test_data_validator_malformed_json` | `DataValidator` | Corrupt JSON caught |
| `test_validation_and_features.py` | `test_data_validator_missing_required_fields`| `DataValidator` | Incomplete dict rejected |
| `test_validation_and_features.py` | `test_data_validator_out_of_bounds_rejection` | `DataValidator` | Extreme bounds rejected |
| `test_validation_and_features.py` | `test_feature_extractor_vector_shape_and_order`| `FeatureExtractor` | Exact $(1, 7)$ alignment |
| `test_validation_and_features.py` | `test_ton_iot_row_mapping` | `TONIoTReplayRunner` | UNSW schema mapped |
| `test_detection.py` | `test_model_artifact_integrity` | Model Joblib File | Estimator loaded |
| `test_detection.py` | `test_normal_telemetry_inference` | `AnomalyDetector` | Clean data scores benign |
| `test_detection.py` | `test_dos_attack_inference` | `AnomalyDetector` | DoS flagged as anomaly |
| `test_detection.py` | `test_brute_force_attack_inference` | `AnomalyDetector` | Auth flood flagged |
| `test_detection.py` | `test_sensor_tampering_inference` | `AnomalyDetector` | Surge flagged |
| `test_detection.py` | `test_risk_score_calibration_bounds` | `AnomalyDetector` | $0.0 \le \text{Risk} \le 1.0$ |
| `test_alert_and_pipeline.py` | `test_alert_engine_dos_attribution` | `AlertEngine` | Correct DoS label |
| `test_alert_and_pipeline.py` | `test_alert_engine_brute_force_attribution` | `AlertEngine` | Correct Auth label |
| `test_alert_and_pipeline.py` | `test_alert_engine_hardware_voltage_surge_attribution` | `AlertEngine` | Correct Surge label |
| `test_alert_and_pipeline.py` | `test_alert_engine_normal_telemetry_returns_none` | `AlertEngine` | Benign produces no alert |
| `test_alert_and_pipeline.py` | `test_end_to_end_mqtt_collector_alert_pipeline` | `MQTTCollectorService` | Pub/sub alert dispatch |
| `test_mqtt_baseline.py` | `test_mqtt_publish_subscribe_json` | Native Mosquitto | Loopback pub/sub ok |
| `test_storage.py` | `test_influxdb_service_initialization` | `InfluxDBService` | Client connected |
| `test_storage.py` | `test_write_telemetry_and_alert_persistence` | `InfluxDBService` | Points written |
| `test_evaluation.py` | `test_synthetic_evaluation_metrics` | Synthetic Benchmark | $F_1 \ge 0.70$, $\text{AUC} \ge 0.85$ |
| `test_evaluation.py` | `test_ton_iot_benchmark_evaluation` | UNSW TON_IoT Benchmark | $F_1 \ge 0.75$, $\text{AUC} \ge 0.85$ |
| `test_evaluation.py` | `test_persisted_evaluation_report_file`| `evaluation_report.json` | JSON schema valid |
| `test_simulator.py` | `test_iot_device_normal_telemetry_schema`| `IoTDevice` | Telemetry valid |
| `test_simulator.py` | `test_iot_device_normal_telemetry_bounds`| `IoTDevice` | Statistical bounds ok |
| `test_simulator.py` | `test_multi_device_simulator_batch_generation` | `MultiDeviceSimulator` | Multi-fleet batch ok |
| `test_attack_scenarios.py` | `test_dos_flooding_characteristics` | `AttackScenarioGenerator`| DoS profile valid |
| `test_attack_scenarios.py` | `test_brute_force_auth_characteristics` | `AttackScenarioGenerator`| Auth profile valid |
| `test_attack_scenarios.py` | `test_sensor_tampering_characteristics` | `AttackScenarioGenerator`| Tamper profile valid |
| `test_attack_scenarios.py` | `test_network_degradation_characteristics` | `AttackScenarioGenerator`| Jitter profile valid |
| `test_attack_scenarios.py` | `test_labeled_evaluation_dataset_structure`| Dataset Integrity | Label integrity ok |
| `test_grafana.py` | `test_grafana_dashboard_json_integrity` | Dashboard Template | Valid JSON schema |
| `test_grafana.py` | `test_grafana_api_and_provisioning` | Grafana HTTP API | Health status 200 ok |

---

## 7. Appendix: Mathematical Formulations & Data Schemas

### 7.1 Isolation Forest Mathematical Formulation
Given an unlabelled dataset $X = \{x_1, \dots, x_n\}$ of $n$ instances in a $d$-dimensional space:
1. **Isolation Tree ($i\text{Tree}$):** Recursively isolates instances by selecting an attribute $q$ at random and a split value $p$ uniformly at random between $\min(q)$ and $\max(q)$.
2. **Average Path Length of Unsuccessful Search in BST:**
   $$c(n) = 2 \left( \ln(n - 1) + 0.5772156649 \right) - \frac{2(n - 1)}{n}$$
   where $0.5772156649$ is Euler's constant.
3. **Anomaly Score Function:**
   $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
   where $h(x)$ is the path length of observation $x$ in an $i\text{Tree}$, and $E(h(x))$ is the expectation of $h(x)$ across all $100$ trees.
   - If $E(h(x)) \to 0 \implies s \to 1$ (Instance isolates rapidly $\implies$ definite anomaly).
   - If $E(h(x)) \to n - 1 \implies s \to 0$ (Instance resides deep in tree $\implies$ standard inlier).
   - If $E(h(x)) \to c(n) \implies s \to 0.5$ (No structural irregularity).

### 7.2 Standardized JSON Data Schemas

#### A. Telemetry Packet (`iot/devices/<device_id>/telemetry`)
```json
{
  "device_id": "device_001",
  "timestamp": "2026-10-31T14:00:00.000Z",
  "temperature": 25.4,
  "voltage": 230.1,
  "cpu_usage": 14.8,
  "ram_usage": 39.5,
  "message_rate": 1.0,
  "failed_auth_count": 0,
  "network_latency": 15.2
}
```

#### B. Alert Event Packet (`iot/alerts`)
```json
{
  "alert_id": "ALT-20261031-140002-3841",
  "device_id": "device_001",
  "timestamp": "2026-10-31T14:00:02.150Z",
  "alert_category": "Denial-of-Service (DoS)",
  "threat_name": "Denial-of-Service (DoS) / Message Flooding",
  "severity": "CRITICAL",
  "is_cyberattack": true,
  "calibrated_risk_score": 0.946,
  "raw_anomaly_score": -0.159,
  "triggering_metrics": {
    "message_rate": 88.4,
    "cpu_usage": 91.2
  },
  "recommended_action": "Throttle device publish rate at Mosquitto ACL; terminate client session."
}
```

---

## 8. Document Sign-Off & Approvals

| Role | Name / Designation | Organization | Status / Signature |
| :--- | :--- | :--- | :---: |
| **Project Author** | B.Tech CSE Student Candidate | Dept of Computer Science & Engineering | Submitted |
| **Faculty Guide** | Project Supervisor / Assistant Professor | Dept of Computer Science & Engineering | Approved |
| **External Examiner**| University External Evaluation Board | Examination Committee | Verified |
