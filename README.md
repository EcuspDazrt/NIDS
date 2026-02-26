# NIDS — Network Intrusion Detection System

A real-time network intrusion detection system (NIDS) that continuously monitors live network traffic, extracts behavioral features, and uses an ensemble of machine-learning models to identify malicious activity with low latency and high reliability. The goal is to approximate how modern security platforms detect attacks in production environments.

---

## Architecture Overview
See [System Design](docs/system_design.md) for the full architecture diagram.

At a high level, the system has four stages: **capture → feature extraction → inference → alerting.**

```
[Network Interface]
       ↓
[Packet Capture — LibPcap]
       ↓
[Flow Aggregator — extracts per-flow behavioral features]
       ↓
[Feature Store — Redis]
       ↓
[ML Inference Layer]
   ├── Random Forest (supervised classifier)
   └── Autoencoder (unsupervised anomaly detector)
       ↓
[Alert Engine → SQLite log + GUI]
```

---

## How It Works

**Packet Capture:** LibPcap sniffs raw packets from the network interface and groups them into flows (bidirectional streams identified by 6-tuple: (epoch-ID, source IP, destination IP, source port, destination port, protocol).

**Feature Extraction:** Each flow is tracked in a flow table. As packets arrive, the system computes behavioral features — things like packet size statistics, inter-arrival times, flow duration, and byte ratios — that characterize how the flow behaves rather than what it contains.

**Feature Storage:** Extracted feature vectors are pushed into Redis, enabling low-latency access across processes and future multi-process scaling.

**Inference:** Two models run on each completed flow. The Random Forest classifies the flow against known attack signatures it was trained on. The Autoencoder assigns a reconstruction-error anomaly score, catching patterns the classifier may not have seen before.

**Alerting:** Flagged flows are written to a SQLite log and surfaced in a customtkinter GUI dashboard in real time.

---

## Project Structure

```
NIDS/
├── alerts/                  # Alert engine and SQLite logging
├── capture/                 # Packet sniffing and flow tracking, in progress
├── datasets/                # Training datasets (not committed — see below)
├── docs/
│   ├── adr/                 # Architecture Decision Records
│   ├── experiment_plan.md
│   ├── feature_spec.md
│   ├── model_plan.md
│   └── system_design.md
├── evaluation/              # Evaluates the current model based on CICIDS2017 dataset
│   ├── ae_eval.py
│   └── rf_eval.py
├── features/                # Feature extraction logic
│   └── extract.py
├── gui/                     # customtkinter dashboard
│   ├── app.py
│   └── resources/           # contains all images the app depends on
├── inference/
│   └── inference.py
├── models/
│   ├── artifacts/           # model weights, biases, and dependencies (not committed - see below)
│   └── definitions/
│       ├── random_forest.py
│       └── autoencoder.py
├── scripts/
│   ├── build_dataset.py
│   └── build_dataframe.py
├── storage/                 # Redis interface and flow state management, in progress
├── tests/                   # in progress
├── training/
│   ├── ae_train.py
│   └── rf_train.py
├── .gitignore
└── README.md
```
---

## Setup & Installation

### Prerequisites

- Python 3.10+
- Redis (running locally or via Docker)
- Root/admin privileges for packet capture

### Install

```bash
git clone https://github.com/EcuspDazrt/NIDS.git
cd nids
pip install -r requirements.txt
```

### Start Redis

```bash
# With Docker:
docker run -d -p 6379:6379 redis

# Or locally (macOS):
brew services start redis
```

### Run

```bash
# Requires elevated privileges for raw packet capture
sudo python main.py --interface eth0
```

---

## Training Data

The models were trained on the **CIC-IDS-2017** dataset, a standard benchmark for network intrusion detection containing labeled benign and attack traffic across multiple attack categories (DDoS, PortScan, Brute Force, etc.).

Training data is not committed to this repo. To retrain:

```bash
# Download CIC-IDS-2017, then:
python train.py --data data/cicids2017/
```

---

## Current Status & Roadmap

| Feature                                     | Status      |
|---------------------------------------------|-------------|
| Packet capture + flow aggregation           | In Progress |
| Feature extraction                          | Working     |
| Random Forest classifier                    | Working     |
| Autoencoder anomaly detector                | Working     |
| Redis feature store                         | In progress |
| SQLite alert log                            | In progress |
| GUI dashboard                               | Working     |
| Multi-process scaling                       | Planned     |
| Evaluation vs. CIC-IDS-2017 benchmark       | Planned     |

---

## Documentation

- [Feature Specification](docs/feature_spec.md) — detailed definitions of all extracted flow features
- [System Design](docs/system_design.md) — architecture decisions and component breakdown
- [Architecture Decision Records](docs/adr/) — log of key technical decisions and their rationale
