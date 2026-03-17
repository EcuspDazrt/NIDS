# ADR-004: Auto-Encoder

**Date:** 2026-03-04  
**Status:** Accepted

## Context
- In addition to an explicit risk-based model, there must be a model that signifies whether traffic is anomalous: 'is this weird?' rather than 'is this dangerous?'
- To bolster system precision and recall, there also must be a mechanism to counteract model drift
- So, an unsupervised model should be used for each of these constraints

## Decision
Standard Auto-encoder.

## Alternatives Considered
| Option                   | Reason Rejected                                                                                                                                                                                                      |
|--------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Isolation Forests        | Isolation forests will simply learn its surface statistics rather than true patterns throughout the traffic. It will miss malicious flows that have standard statistics but awkward combinations.                    |
| Clustering               | This requires a defined number of clusters, which is largely not possible to do for network traffic. It won't generalize well to the distribution of real traffic and cannot be used to make tier-based predictions. |
| Variational Auto-encoder | Although the VAE would be more efficient in representing a traffic anomaly score, it is much more complex in its reconstruction error signal, and would be difficult to interpret across the system                  |

## Consequences
- The standard auto-encoder will be efficient in detecting anomalies across unfamiliar and familiar network traffic
- It has the capability of being retrained to account for model drift over time
- It has a clean signal that is easily interpreted by the system inference module