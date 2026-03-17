# ADR-002: Model Ensemble

**Date:** 2026-03-03
**Status:** Superseded by [ADR-017](ADR-017-SeparatedModelScores)

## Context
- To incorporate multiple machine learning models into a single system, there must be a way for the user to accurately interpret the scores

## Decision
Model ensemble.

## Alternatives Considered
| Option                                  | Reason Rejected                                                                                                                                                               |
|-----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Separating Models into separate signals | The separation signal may be difficult for the user to interpret unless heavily normalized. How does the user know what reconstruction error or classification confidence is? |

## Consequences
- The system will have a more interpretable signal to identify whether a network is being attacked, requiring little to no knowledge of how the system actually works.