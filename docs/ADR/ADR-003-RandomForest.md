# ADR-003: Random Forest Model

**Date:** 2026-03-04  
**Status:** Accepted

## Context
- For intrusion detection overall, model selection is very crucial
- It should be able to learn patterns from flow-level data rather than payload (refer to [ADR-008](ADR-008-SnapLen.md))

## Decision
Random Forest.

## Alternatives Considered
| Option                 | Reason Rejected                                                                                                                                    |
|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| Gradient Boosted Trees | It overfits aggressively on noisy traffic data, requires more hyperparameter tuning than necessary.                                                |
| Neural Networks        | An auto-encoder model is already in use for the anomalous detection. Including a neural network would make the two models correlated and redundant |

## Consequences
- The explicit-risk model is more robust to noisy traffic
- The tree is built in parallel, rather than layered on top of itself
- It has no concept of unfamiliarity: if it hasn't seen certain types of traffic it will fail
  - This is what the anomalous detection model is for