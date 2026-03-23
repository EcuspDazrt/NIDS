# ADR-019: CICIDS2017 As Base Training

**Date:** 2026-03-13
**Status:** Accepted

## Context
In order to have the most efficient model possible, it must be trained on data that is both diverse and realistic.

## Decision
- Use CICIDS2017 as the base training set that each of the models use
- After the initial training, the auto-encoder will be calibrated slightly to better match the local network's patterns
- Evaluate models and test system against real attacks - known and novel


## Alternatives Considered
| Option                     | Reason Rejected                                                                                                                                                                                                                         |
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Use real data for training | Although using real data for training the model would produce realistic traffic in a given network, it will not be diverse enough to produce valuable patterns for the models to learn that could be generalized to other deployments.  |

## Consequences
- The models will now generalize more efficiently
- The auto-encoder leaves room to improve per-deployment by slightly tuning it based on local traffic (with measures to avoid model poisoning)