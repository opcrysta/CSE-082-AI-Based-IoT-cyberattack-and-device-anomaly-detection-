# Software Requirements Specification (SRS)
## AI-Based IoT Cyberattack and Device Anomaly Detection
### Project Identification: CSE-082 / P_310
**Standard:** IEEE Std 830-1998 Compliant  
**Version:** 1.0  
**Date:** October 2026  
**Status:** Approved / Production Deployed  

> [!NOTE]
> The full, detailed academic specification is available at [docs/SRS.md](docs/SRS.md). This file serves as the root-level entry point for university project upload portals.

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

## Complete Table of Contents
1. [Introduction (Purpose, Scope, IEEE Standards, Academic References)](docs/SRS.md#1-introduction)
2. [Overall Description (Architecture, Functions, User Classes, Operating Environment, Constraints)](docs/SRS.md#2-overall-description)
3. [External Interface Requirements (SOC Dashboard, Microcontroller Interfaces, MQTT/InfluxDB APIs)](docs/SRS.md#3-external-interface-requirements)
4. [System Features & Functional Requirements (FR-1 through FR-12)](docs/SRS.md#4-system-features--functional-requirements)
5. [Non-Functional Requirements (NFR-1 through NFR-8)](docs/SRS.md#5-non-functional-requirements)
6. [Verification, Validation & Testing Matrix (33 Pytest Suite Matrix)](docs/SRS.md#6-verification-validation--testing-matrix)
7. [Appendix: Mathematical Formulations & Data Schemas](docs/SRS.md#7-appendix-mathematical-formulations--data-schemas)

---

### Core Functional Highlights
- **FR-1 to FR-3 (Ingestion & Schema Validation):** Paho-MQTT wildcard subscriber (`iot/devices/+/telemetry`), strict Pydantic type & statistical bound enforcement.
- **FR-4 (Feature Alignment):** Invariant 7-dimensional vector extraction $\begin{bmatrix} T, & V, & \text{CPU}, & \text{RAM}, & \text{Rate}, & \text{Auth}, & \text{Latency} \end{bmatrix}$.
- **FR-5 to FR-6 (AI Anomaly Scoring):** Unsupervised Scikit-Learn Isolation Forest ensemble (100 trees, 5% contamination) with continuous Sigmoid risk mapping:
  $$\text{Risk}(s) = \frac{1}{1 + e^{12 \cdot (s + 0.05)}} \in [0.0, 1.0]$$
- **FR-7 to FR-8 (2-Tier Threat Attribution):** Disambiguates cyber threats (DoS Flooding, Brute-Force Auth) from hardware faults (Overvoltage, Sensor Degradation) and publishes actionable remediation alerts to `iot/alerts`.
- **FR-9 to FR-10 (Resilient Persistence):** InfluxDB v2 primary storage with zero-data-loss SQLite3 edge buffer fallback (`offline_buffer.db`).
- **FR-11 to FR-12 (Evaluation Benchmarks):** Synthetic attack burst generator and UNSW Canberra TON_IoT real-world thermostat dataset replay.

---

### Complete Document
For full IEEE standard text, tables, formulas, and test matrices, please refer to the complete document:
- **Direct File Link:** [docs/SRS.md](docs/SRS.md)
