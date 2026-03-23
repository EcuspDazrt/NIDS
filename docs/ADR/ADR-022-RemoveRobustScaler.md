# ADR-022: Remove Robust Scaler

**Date:** 2026-03-16
**Status:** Accepted

## Context
In order for the random forest model to be most efficient, it needs to choose the correct scaling methods.

## Decision
Remove the Robust Scaler.

## Alternatives Considered
| Option                 | Reason Rejected                                                                                                                                                                                                                                                       |
|------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Keep the Robust Scaler | Although it could potentially pose benefits to the random forest's correctness during inference time, it proved counter-productive because it shifted the inference-time features in a way that made the random forest mis-label more traffic than it had without it. |

## Consequences
The random forest attains a higher level of recall and precision while maintaining its feature integrity.