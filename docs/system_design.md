# System Design Document
## 1. Overview
This document describes the system architecture for a real-time Network Intrusion Detection System (NIDS). 
It is intended for developers contributing to the project and technical reviewers evaluating the design. 
The document covers the core pipeline components — packet capture, flow aggregation, feature extraction, ML inference, alerting, and storage — 
as well as offline retraining and performance considerations. It does not cover model training methodology or feature definitions in depth; 
those are addressed in [Experiment Plan](experiment_plan.md) and [Feature Spec](feature_spec.md) respectively. 
Architecture Decision Records for key design choices can be found in [ADR](ADR).
```mermaid
graph TD
	A(Network Sniffer)
	B(Sort packet data into flows)
	C(Store current flow state in multiprocessing queue)
	D(Extract features from flow state)
	E(Pass through Models)
	F(Random Forest)
	G(Auto-encoder)
	H(Score Interpretation)
	I(Store logs in SQLite)
	J(Pass to Dashboard)
	K(Send alert if danger passes threshold)
	L(Offline ae training)
    A --> B --> C --> D --> E --> F
	E --> G
	G --> H
	F --> H --> I --> J --> K
	I --> L
```
## 2. Architecture
### 2.1 Packet Capture
Purpose: Capture raw network packets from the interface.  
Input: Network interface packets.  
Output: Raw packets to be processed into flows.  
Dependencies/Tools: LibPcap.  
Constraints: Packet throughput is very high - it must handle it with low latency and without dropping data
### 2.2 Flow Table
**Flows will be organized by 6-tuple: (epoch ID, src/dst IP, src/dst port, protocol)**  
**Epoch ID is incremented per-flow each time the given flow is timed-out**  
Purpose: Organize packets into flows. 
Input: Packets from Packet Capture.  
Output: Flow objects stored in memory through python's multiprocessing library  
Constraints: Flows may expire after inactivity.
### 2.3 Feature Extraction
Purpose: Convert flows into numerical features for ML models.  
Input: Flow objects.  
Output: Feature vectors (e.g., packet counts, byte counts, inter-arrival times).  
Considerations: Normalization/scaling may be needed.  
  
The Feature Extraction subsystem converts flow objects into a fixed-length feature vector defined  
in the Feature Specification document [Feature Spec](feature_spec.md). This vector is used by both the  
Random Forest and Auto-encoder models and is stored in the inference module's memory for live inference and SQLite for offline training.
### 2.4 Model Inference
Purpose: Pass features through trained ML models to detect anomalies.  
Input: Feature vectors  
Output: Risk score random forest and reconstruction error from auto-encoder in range [0, infinity)  
Models: Random Forest, Auto-encoder  
Considerations: Batch vs. live inference; latency requirements.  
### 2.5 Score Interpretation
Purpose: Translate scores into a risk category and percentage chance of anomaly.  
Input: Model outputs.  
Output: Auto-encoder anomaly percentage and risk category; Random forest risk category.
### 2.6 Dashboard
Purpose: Display risk alerts and flow statistics to the user.  
Input: Risk scores, logs from SQLite.  
Output: Visual alerts, dashboards.  
Considerations: Refresh rates, user interactivity, filtering options.
## 3. Storage
SQLite: Stores long-term logs coming for offline analysis and retraining  
SQLite table: flow_logs(timestamp, source ip, destination ip, source port, destination port, protocol, auto-encoder score, auto-encoder category, random forest score, random forest category, auto-encoder percentage representation, auto-encoder features, random forest features, ja3 hash/fingerprint, if the ja3 hash is malicious)  

Purpose: Periodically retrain the Autoencoder using historical flow data accumulated in SQLite, 
allowing the model to adapt to shifts in baseline network behavior over time; Allow for manual review of alerts, flow patterns, retraining events, and model drift detections.
SIEM capability: Alerts are written as newline-delimited JSON to nids_alerts.log. This format is directly ingestible by Splunk Universal Forwarder and Elastic Filebeat with no additional transformation. Syslog forwarding over UDP is also supported via Python's SysLogHandler for environments with an existing syslog infrastructure.

## 4. Offline 
Input: Flow logs from the flow_logs SQLite table, filtered to benign-labeled records for unsupervised retraining.
Output: Updated Autoencoder weights saved to models/artifacts/.
Rationale: The Autoencoder is an unsupervised anomaly detector: 
it learns a compressed representation of normal traffic and flags flows that deviate significantly from that representation. 
Because network traffic patterns shift over time (new services, changing usage patterns, infrastructure updates), 
a static model will gradually accumulate false positives as legitimate traffic drifts outside its learned distribution. 
Periodic retraining on recent benign traffic keeps the reconstruction baseline current. 
The Random Forest is not retrained in this loop because it is a supervised classifier trained on a fixed labeled dataset (CIC-IDS-2017); 
retraining it would require newly labeled attack data, which is not passively available at runtime.

Schedule: Retraining can be triggered manually or on a configurable schedule. 
The retraining script reads from SQLite, preprocesses features using the same normalization pipeline used during live inference, and overwrites the model artifact on completion.
Constraints: Retraining should only use data from a recent time window to avoid stale traffic patterns dominating the learned distribution. Care should be taken to exclude any flows flagged as malicious from the retraining set, as including attack traffic would corrupt the model's baseline.
## 5. Security & Performance Considerations
Security:
Raw packet payloads are never logged or stored, only behavioral flow features are retained. 
This is both a privacy consideration and a practical one, as payload inspection would introduce significant latency and storage overhead. 
If flow logs are stored on shared infrastructure, encryption of the SQLite database should be considered. 
Model artifacts should be treated as sensitive, since a compromised model could be used to understand the system's detection blind spots.

Performance:
The system is designed for low-latency inference on completed flows. 
Python's multiprocessing library is used as an intermediate feature store to decouple the capture and inference processes, 
enabling future multiprocess scaling where capture and inference run in parallel. 
The two models have meaningfully different latency profiles: the Random Forest produces near-instantaneous predictions, 
while the Autoencoder involves a forward pass through a neural network and is slightly more expensive. 
Both are expected to operate well within acceptable latency bounds for flow-level (rather than packet-level) inference. 
Bottlenecks are most likely to occur at the packet capture and flow aggregation stage under high-throughput conditions; 
this is the primary constraint motivating the planned multiprocess architecture.

## 6. Limitations
### 6.1 Retraining the auto-encoder
  - There is a big problem with using live traffic data to retrain an unsupervised model - model poisoning
  - However, the following will be used to mitigate it:
    - Temporal isolation - Only retrain on traffic more than 24 hours ago to offset direct attacks (however vulnerable if the attacker is patient)
    - Consensus filtering across detectors - The system will use an isolation forest model and a random forest model to filter out perceived malicious flows
    - Anomaly score drift monitoring - Constantly monitor the distribution of the auto-encoder under normal traffic; if it starts seeing flows that are unusually categorized by the auto-encoder, it will roll back to a previous version.
### 6.2 JA3 Hashing
  - It will only cover a partial encryption traffic signal (will not parse payload for it)
  - Only provides a slight extra layer of security (needs payload for better inspection)
### 6.3 The system will be payload-blind
  - SQL Injection
  - XSS
  - Shellcode
### 6.4 The system will be encryption-blind
  - TLS/HTTPS attacks at normal flow rates
### 6.5 The system will be Non-TCP/UDP blind
  - ICMP tunneling
  - DNS tunneling
### 6.6 The system will be fragment blind
  - Fragmented attacks (non-first IPv4 fragments are discarded)
### 6.7 The system will be layer 2 blind
  - ARP spoofing
  - MAC flooding
### 6.8 The system will be Low-and-slow blind
  - Attacks that mimic benign flow statistics (similar to payload blind)