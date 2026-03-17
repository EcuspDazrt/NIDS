# ADR-017: Separate Model Scores

**Date:** 2026-03-11
**Status:** Accepted

## Context
- Model interpretability is a large part of the system, and the user must be able to understand what the signal means and where it is coming from.

## Decision
Separate the model scores into separate signals: anomalous and explicit.

## Alternatives Considered
| Option                                 | Reason Rejected                                                                                                                                                                                                                                                                                        |
|----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Combine the scores into a single score | Although this would be easily interpreted by a user, the combination of both models into a single score would eliminate the core purpose of each model since they are distinct from each other. The auto-encoder measures how weird a given flow it, and the random forest just detects known attacks. |

## Consequences
- As long as the scores are presented in a way that is easily interpreted by the user, it will show a more accurate representation of a network's malicious state
- There may be an increased chance of false positives given that there are two separate models that are generalizing to the network traffic.