# B.Tech Project Viva & Technical Interview Guide
## Project P_310: AI-Based IoT Cyberattack and Device Anomaly Detection

---

### Core Question 1: How do you prove an anomaly is an actual cyberattack and not just a sensor glitch or environmental noise?

**Examiner Question:**
> *"Your project uses Isolation Forest to detect anomalies. How do you distinguish whether an anomaly is a malicious cyberattack or just a benign hardware glitch or hot weather?"*

**The Technical Distinction (Key Concept):**
- **Anomaly:** A statistical outlier where observed telemetry values deviate significantly from the baseline distribution. Anomaly detection is purely mathematical and unsupervised.
- **Cyberattack:** An intentional, adversarial action with malicious intent (e.g., unauthorized access, resource exhaustion, data tampering).
- **Fundamental Rule:** Isolation Forest outputs only a score and a binary classification ($1$ for normal, $-1$ for anomaly). It **cannot** determine attack intent or classification on its own.

**Our Engineering Solution (2-Tier Hybrid Architecture):**
1. **Tier 1 (Unsupervised ML Layer - Isolation Forest):** Flags that the multidimensional feature vector is anomalous without needing prior knowledge of attack signatures.
2. **Tier 2 (Alert & Threat Attribution Engine):** Inspects the root-cause feature deviations using threat signatures:
   - **DoS / MQTT Flooding:** Flagged if Anomaly = True AND $\text{message\_rate} > 15\text{ msg/s}$ AND $\text{cpu\_usage} > 75\%$.
   - **Brute-Force Authentication:** Flagged if Anomaly = True AND $\text{failed\_auth\_count} > 5$.
   - **Network Degradation / MITM:** Flagged if Anomaly = True AND $\text{network\_latency} > 250\text{ms}$ while device CPU is normal.
   - **Hardware / Electrical Fault (Not a Cyberattack):** Flagged if Anomaly = True AND $\text{voltage} > 270\text{V}$ or $< 180\text{V}$ with zero failed authentications.
   - **Thermal / Environmental Anomaly (Not a Cyberattack):** Flagged if Anomaly = True AND $\text{temperature} > 65^\circ\text{C}$ with normal CPU load.

**Model Viva Answer (Speak this with confidence):**
> *"Isolation Forest is an unsupervised algorithm that detects statistical deviations from the baseline operational envelope, but it does not inherently understand adversarial intent.*
>
> *In our architecture, we solve this using a two-tier defense pipeline:*
> *1. First, the Isolation Forest flags that the device state is anomalous based on multidimensional feature distances.*
> *2. Next, our Alert Engine inspects the individual feature deviations. If the anomaly is driven by cyber indicators such as repeated failed authentication attempts, message rate flooding, or network latency spikes, it is classified as a cyberattack.*
> *If the anomaly is driven purely by physical sensor readings with zero security indicator deviations, it is flagged as a hardware or environmental fault.*
>
> *This hybrid approach prevents false cyber alarms caused by benign environmental fluctuations."*

---

### Core Question 2: How does Isolation Forest mathematically isolate anomalies, and why is it superior to distance-based algorithms (like K-Means or DBSCAN) for IoT?

**Examiner Question:**
> *"Explain the internal mechanism of an Isolation Tree. Why did you choose Isolation Forest over clustering or one-class SVM?"*

**Technical Explanation:**
1. **Core Principle:** Most anomaly detection methods profile normal data points and look for points that don't fit (density or distance calculations). Isolation Forest isolates anomalies directly using random recursive partitioning.
2. **Few and Different:** Because anomalous observations have extreme attribute values, they are easily separated from dense clusters in very few random splits. Thus, anomalies have **noticeably shorter path lengths $h(x)$** from root to leaf node.
3. **Anomaly Score Formula:**
   $$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
   Where $E(h(x))$ is the average path length across all isolation trees, and $c(n)$ is the average path length of unsuccessful searches in a Binary Search Tree (BST) of size $n$.
   - If $s(x, n) \to 1.0$: Observation is definitely an anomaly (short path length).
   - If $s(x, n) < 0.5$: Observation is normal (long path length deep in tree).
4. **Computational Complexity (Why it's ideal for IoT):**
   - Distance algorithms ($k$-NN, DBSCAN) have quadratic time complexity $O(n^2)$ and struggle in high dimensions ("curse of dimensionality").
   - Isolation Forest has linear time complexity $O(t \cdot \psi \log \psi)$ where $t$ is number of trees (100) and $\psi$ is subsampling size (256). It requires extremely low memory and runs fast on edge hardware.

---

### Core Question 3: What does the Contamination parameter mean, and what happens if you set it incorrectly?

**Examiner Question:**
> *"What is the contamination parameter in Scikit-Learn IsolationForest, and why did you set it to 0.05?"*

**Technical Explanation:**
- **Definition:** The `contamination` parameter defines the expected proportion of outliers in the dataset.
- **Decision Boundary Offset:** It tells the algorithm where to place the decision threshold. In Scikit-learn:
  $$\text{threshold} = \text{percentile}(\text{decision\_function\_scores}, 100 \times \text{contamination})$$
- **Why 0.05 (5%)?** Industrial IoT field baselines typically experience $\approx 2\% - 5\%$ natural noise/jitter. Setting contamination to 0.05 provides high detection sensitivity without flooding operators with false alarms.
- **Viva Warning:** Setting contamination too high ($>0.20$) creates excessive false positives (normal operations flagged as attacks). Setting it too low ($<0.001$) creates false negatives (subtle attacks slip through undetected).

---

### Core Question 4: Why do you publish detection alerts back to an MQTT topic (`iot/alerts`) instead of just logging them to a console or database?

**Examiner Question:**
> *"Why does your pipeline publish alerts back onto the MQTT broker under `iot/alerts`? What is the architectural benefit?"*

**Technical Explanation:**
1. **Decoupled Real-Time Mitigation:** In modern IoT security architectures, incident detection and incident response must be loosely coupled. By publishing alerts to `iot/alerts`, automated security actuators, network switches, or edge gateways can subscribe and take immediate mitigating actions (such as disconnecting the compromised client or updating firewall rules) in milliseconds, without polling a database.
2. **Push vs. Pull Latency:** Database queries operate on a polling schedule (pull architecture), which adds latency. MQTT is event-driven (push architecture), ensuring sub-second notification to Security Operations Center (SOC) dashboards and emergency notification webhooks.
3. **Multi-Consumer Fan-Out:** A single alert published to `iot/alerts` can be simultaneously received by:
   - The InfluxDB storage worker (for long-term historical forensics).
   - The Grafana visualization dashboard.
   - An incident notification service (e.g., Slack, SMS, or PagerDuty).

---

### Core Question 5: Why did you choose a Time-Series Database (InfluxDB) over a Relational Database (MySQL/PostgreSQL) or Document Store (MongoDB) for IoT?

**Examiner Question:**
> *"Why use InfluxDB? Couldn't you just create a table in MySQL or a collection in MongoDB to store the sensor readings?"*

**Technical Explanation:**
1. **Append-Only Write Throughput (TSM Engine):**
   - Relational databases (RDBMS) use B-Trees with transactional locking (ACID overhead), which creates write bottlenecks under high-frequency sensor streams (e.g., thousands of events per second).
   - InfluxDB uses a **Time-Structured Merge Tree (TSM)** engine optimized for continuous, append-only, sequential timestamp ingestion with zero row-locking overhead.
2. **Built-in Retention Policies & Automated Downsampling:**
   - In IoT, raw high-frequency telemetry is valuable for recent days, but keeping second-by-second readings for months wastes gigabytes of disk space.
   - InfluxDB provides automated **Retention Policies** (e.g., automatically expire raw readings after 30 days) and **Continuous Queries / Tasks** (downsample 1-second telemetry into 5-minute averages for long-term trend analysis). In MySQL, this would require complex cron jobs and disk fragmentation management.
3. **Optimized Time-Window Queries (Flux Engine):**
   - Queries like *"calculate the rolling 5-minute moving average of CPU usage grouped by device"* require complex table scans and SQL subqueries. In InfluxDB Flux, this is a single, hardware-accelerated pipeline function (`aggregateWindow(every: 5m, fn: mean)`).
4. **Native Plug-and-Play Grafana Integration:**
   - InfluxDB connects natively to Grafana with pre-built alerting, streaming dashboards, and microsecond visual rendering.

---

### Core Question 6: How does Grafana visualize real-time IoT security metrics, and what is Automated Provisioning?

**Examiner Question:**
> *"How did you connect Grafana to InfluxDB, and what is dashboard provisioning? Why is it better than setting up charts manually through the web browser?"*

**Technical Explanation:**
1. **Automated Provisioning (Infrastructure as Code - IaC):**
   - In production enterprise environments, manually clicking buttons in a browser GUI to add datasources and build dashboards is error-prone, untracked, and cannot be recreated in disaster recovery.
   - We implemented **Grafana Provisioning**:
     - `docker/grafana/provisioning/datasources/influxdb.yml`: Automatically injects the InfluxDB connection string, org, bucket, and security token.
     - `docker/grafana/provisioning/dashboards/dashboards.yml`: Automatically mounts and deploys the dashboard JSON specification from `grafana/iot_security_dashboard.json`.
   - Result: Whenever the container starts, the entire security dashboard is ready in seconds with zero manual configuration.
2. **Dashboard Visual Hierarchy:**
   - **Gauges:** Instant visual status of anomaly risk ($0.0 - 1.0$), with green/yellow/red color thresholds.
   - **Time-Series Charts:** Multi-signal temporal correlations (e.g., observing a message rate spike simultaneously causing a CPU spike during a DoS flood).
   - **Incident Log Table:** Structured audit trail of alerts, severity levels, and recommended mitigation actions for SOC analysts.

---
### Core Question 7: Why is Raw Accuracy a misleading metric in Cybersecurity & IoT Anomaly Detection? Why do Precision, Recall, and F1-Score matter?

**Examiner Question:**
> *"Your model achieves 88.6% accuracy on the TON_IoT dataset. Is accuracy alone a good measure of an intrusion detection system? Why did you report Precision, Recall, and F1-score?"*

**Technical Explanation:**
1. **The Accuracy Paradox in Imbalanced Cyber Data:**
   - In real-world IoT networks, attacks represent less than $1\%$ to $5\%$ of all network traffic.
   - If an evaluation set has $9,900$ normal packets and $100$ cyberattack packets, a trivial "dumb" classifier that predicts *every single packet as normal* will achieve **$99.0\%$ Accuracy** — while missing $100\%$ of all cyberattacks!
   - Therefore, in cybersecurity, **raw accuracy is a dangerous and misleading metric**.

2. **The True Cyber Performance Triad:**
   - **Recall (Sensitivity / Detection Rate):**
     $$\text{Recall} = \frac{TP}{TP + FN}$$
     *Answers:* Out of all actual attacks launched against our IoT devices, what percentage did we catch? High recall prevents catastrophic breaches.
   - **Precision (Alert Trustworthiness):**
     $$\text{Precision} = \frac{TP}{TP + FP}$$
     *Answers:* When an alert fires in the Security Operations Center (SOC), what is the probability that it is an actual attack rather than a false alarm? High precision prevents **alert fatigue** for human analysts.
   - **$F_1$-Score (Harmonic Mean):**
     $$F_1 = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$$
     Penalizes extreme imbalance between precision and recall, providing an honest, unified indicator of model health.

3. **Our Verified Results:**
   - **Synthetic Attack Scenarios:** Accuracy $= 87.0\%$, Precision $= 82.8\%$, Recall $= 77.0\%$, $F_1 = 0.7979$.
   - **UNSW TON_IoT Benchmark:** Accuracy $= 88.6\%$, Precision $= 100.0\%$, Recall $= 74.6\%$, $F_1 = 0.8545$.
   - **Significance:** $100\%$ precision on TON_IoT means zero false alarms occurred on normal thermostat operations, while catching $74.6\%$ of complex, real-world attack vectors.

---

### Core Question 8: Explain your quantitative results on the authentic UNSW Canberra TON_IoT dataset. Why did the model achieve 100% detection on Ransomware and Password attacks, but 0% on Injection attacks?

**Examiner Question:**
> *"In your TON_IoT benchmark, your model detected 100% of Backdoor, Password, and Ransomware attacks, but 0% of Injection attacks. Why did this happen, and does this mean your system is flawed?"*

**Model Viva Answer (Demonstrates deep engineering maturity):**
> *"This outcome is not a flaw in the system — it is a fundamental property of feature representation and telemetry granularity in cybersecurity.*
>
> *1. **Why Backdoor, Password, and Ransomware reached 100% Recall:**
>   - **Password attacks** generate repeated, high-frequency authentication attempts (`failed_auth_count = 9-20`), which violently violate the baseline feature bounds.
>   - **Ransomware & Backdoors** engage in file encryption, process injection, and reverse shells, driving CPU usage to $>90\%$ and RAM usage to $>90\%$. The Isolation Forest easily isolates these multidimensional resource spikes.
>
> *2. **Why Injection (SQLi/XSS) had low/zero telemetry recall:**
>   - Injection attacks operate entirely inside application-layer payload bodies (e.g., `SELECT * FROM users WHERE '1'='1'`).
>   - In a lightweight embedded thermostat, an HTTP GET/POST injection payload takes only a few hundred bytes and does **not** spike device CPU, voltage, or message rates.
>   - Because our feature vector inspects **device health and transport telemetry** (`temperature`, `voltage`, `cpu_usage`, `ram_usage`, `message_rate`, `failed_auth_count`, `network_latency`), it cannot see SQL syntax inside the payload body without Deep Packet Inspection (DPI).
>
> *This highlights the core industry principle of **Defense-in-Depth**: Transport-level anomaly detection handles volumetric, resource-exhaustion, and credential-stuffing attacks at high speeds with low overhead, while application-layer Web Application Firewalls (WAFs) inspect textual payload content."*

---

### Core Question 9: What is ROC-AUC, and how did your model achieve 0.9364 on synthetic data and 0.8805 on TON_IoT?

**Examiner Question:**
> *"What does the ROC-AUC score represent, and why is it preferred when comparing anomaly detection models across different operating environments?"*

**Technical Explanation:**
1. **Definition:**
   - The **Receiver Operating Characteristic (ROC)** curve plots the **True Positive Rate (Recall)** against the **False Positive Rate ($FPR = FP / (FP + TN)$)** across all possible decision threshold values.
   - The **Area Under the Curve (AUC)** summarizes this performance into a single scalar value between $0.0$ and $1.0$:
     - $\text{AUC} = 0.50$: Equivalent to flipping a coin (random guessing).
     - $\text{AUC} = 1.00$: Perfect separation between normal operations and cyber threats.
2. **Threshold Independence:**
   - Classification accuracy and precision depend on choosing a single arbitrary cutoff threshold ($0.0$).
   - ROC-AUC measures the model's fundamental statistical ranking capability: it tells us the probability that a randomly chosen cyberattack will be assigned a higher anomaly score than a randomly chosen normal telemetry packet.
3. **Our System Performance:**
   - **Synthetic Scenarios:** $\text{ROC-AUC} = \mathbf{0.9364}$ ($93.6\%$ separation).
   - **UNSW TON_IoT Dataset:** $\text{ROC-AUC} = \mathbf{0.8805}$ ($88.1\%$ separation).
   - This proves our Isolation Forest model possesses high discriminatory power across diverse threat topologies.

---

### Core Question 10: What are the real-world limitations of Unsupervised Isolation Forest in IoT, and how would you enhance this system for future work?

**Examiner Question:**
> *"Every machine learning system has limitations. What are the weaknesses of your current architecture, and how would you address them in future research?"*

**Technical Explanation (Critical Self-Reflection):**
1. **Concept Drift & Seasonal Environmental Variations:**
   - *Limitation:* IoT sensors placed in outdoor industrial settings experience natural seasonal drift (e.g., ambient temperature rising in summer, or higher network latency during business peak hours). A static Isolation Forest model trained in winter might misclassify normal summer telemetry as anomalous.
   - *Future Solution:* Implement **Online Incremental Tree Updates** (e.g., Half-Space Trees or Streaming Isolation Forest) with sliding-window retraining to adapt to non-adversarial concept drift.
2. **Low-and-Slow Adversarial Evasion (Stealth Attacks):**
   - *Limitation:* Sophisticated adversaries intentionally throttle attack rates (e.g., attempting 1 password login every 4 hours instead of 20 per minute) to remain within the normal operational distribution.
   - *Future Solution:* Introduce **Stateful Temporal Sequence Models** (e.g., LSTM-Autoencoders or Temporal Convolutional Networks) that analyze multi-hour time-lagged state sequences rather than stateless single-packet snapshots.
3. **Decentralized Privacy & Edge Computing:**
   - *Limitation:* Streaming all raw telemetry to a centralized collector requires continuous network bandwidth and raises data privacy concerns.
   - *Future Solution:* Deploy **Federated Learning (FL)** to train Isolation Forests locally on edge microcontrollers (e.g., Raspberry Pi or ESP32) using TensorFlow Lite Micro, sharing only mathematical tree split bounds with the central server.




