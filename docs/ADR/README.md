# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) documenting key design decisions made throughout the development of the NIDS project.

ADRs were formalized on 2026-03-02 to capture decisions that had been made and revised during development. The dates on individual ADRs reflect when each decision was finalized, not necessarily when it was first made. The supersession chains between ADRs (e.g. ADR-005 → ADR-009, ADR-006 → ADR-010) show where design pivots occurred as the project evolved and constraints changed.

## Index

| ADR                                         | Title                      | Status                         |
|---------------------------------------------|----------------------------|--------------------------------|
| [ADR-001](ADR-001-Pcap.md)                  | Packet Capture Library     | Accepted                       |
| [ADR-002](ADR-002-Ensemble.md)              | Model Ensemble             | Superseded by ADR-017          |
| [ADR-003](ADR-003-RandomForest.md)          | Random Forest Model        | Accepted                       |
| [ADR-004](ADR-004-AutoEncoder.md)           | Auto-Encoder               | Accepted                       |
| [ADR-005](ADR-005-Redis.md)                 | Redis                      | Superseded by ADR-009          |
| [ADR-006](ADR-006-CICIDS2017.md)            | CICIDS-2017                | Superseded by ADR-010          |
| [ADR-007](ADR-007-FlowID.md)                | Epoch Flow ID              | Accepted                       |
| [ADR-008](ADR-008-SnapLen.md)               | Snap Length                | Accepted                       |
| [ADR-009](ADR-009-MultiProcessing.md)       | Multi Processing Library   | Accepted                       |
| [ADR-010](ADR-010-RealData.md)              | Real Data Collection       | Superseded by ADR-019          |
| [ADR-011](ADR-011-FeatureSelection.md)      | Feature Selection          | Accepted                       |
| [ADR-012](ADR-012-FeatureScaling.md)        | Feature Scaling            | Accepted - Modified by ADR-022 |
| [ADR-013](ADR-013-DropProtocols.md)         | Drop Non-TCP/UDP Protocols | Accepted                       |
| [ADR-014](ADR-014-RandomForestStructure.md) | Random Forest Structure    | Accepted                       |
| [ADR-015](ADR-015-AutoEncoderStructure.md)  | Auto-Encoder Structure     | Accepted                       |
| [ADR-016](ADR-016-OfflineRetraining.md)     | Offline Retraining         | Accepted                       |
| [ADR-017](ADR-017-SeparatedModelScores.md)  | Separate Model Scores      | Accepted                       |
| [ADR-018](ADR-018-FlowTimeout.md)           | Flow Timeout Logic         | Accepted                       | 
| [ADR-019](ADR-019-CICIDS2017AsBase.md)      | CICIDS2017                 | Accepted                       |
| [ADR-020](ADR-020-AlertEngine.md)           | Alert Engine               | Accepted                       | 
| [ADR-021](ADR-021-Logging.md)               | Logging                    | Accepted                       |
| [ADR-022](ADR-022-RemoveRobustScaler.md)    | Remove Robust Scaler       | Accepted                       |