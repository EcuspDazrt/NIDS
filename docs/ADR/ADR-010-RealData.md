# ADR-010: Real Data Collection

**Date:** 2026-03-09
**Status:** Superseded by [ADR-019](ADR-019-CICIDS2017AsBase.md)

## Context
- In order for each of the models to achieve desired metrics and results, they should use training data that comes from real traffic rather than synthetic or simulated traffic.

## Decision
Collecting data on a local network.

## Alternatives Considered
| Option      | Reason Rejected                                                                                             |
|-------------|-------------------------------------------------------------------------------------------------------------|
| CICIDS-2017 | This dataset's traffic was too synthetic and is outdated, but will be used a benchmark for experimentation. |

## Consequences
- The models will be able to achieve a higher level of precision and recall, and will learn current normal traffic
- It opens the opportunity to train it against many different attack types using a virtual machine, attacking it, and logging the data.