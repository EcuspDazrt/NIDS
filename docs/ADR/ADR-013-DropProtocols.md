# ADR-013: Drop Protocols (besides UDP/TCP)

**Date:** 2026-03-09
**Status:** Accepted

## Context
- In order to handle network traffic properly, the inference logic must align with the training features and logic.
- Since the CICIDS-2017 dataset (refer to [ADR-006](ADR-006-CICIDS2017.md)) only offers three protocols - UDP, TCP, and ICMP - the system is constrained to those three protocols unless the dataset changes

## Decision
Keep TCP and UDP only.

## Alternatives Considered
| Option                                  | Reason Rejected                                                                                                                                                                                                              |
|-----------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Use TCP, UDP, and ICMP                  | Although this may be a more broad way to account for more attacks, ICMP attacks show up at a way lesser scale than the other two. Although it may be implemented on a later date to upgrade the system.                      |
| Expand dataset and use more protocols   | This would require explicit handling of each individual protocol, and would likely require a great amount of overhead. However, when [ADR-010](ADR-010-RealData.md) is finished, this may become possible and more likely.   |

## Consequences
- The system may not be able to fully handle every explicit attack
- The pipeline will be finished, and overall overhead for each protocol will be low