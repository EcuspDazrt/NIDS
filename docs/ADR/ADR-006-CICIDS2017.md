# ADR-006: CICIDS-2017

**Date:** 2026-03-04 
**Status:** Superseded by [ADR-010](ADR-010-RealData.md)

## Context
- In order for the machine learning models to function properly, they must have data to train off of.
- It must be labeled (for the supervised model), separated by benign and malicious groups.

## Decision
CICIDS-2017

## Alternatives Considered
| Option    | Reason Rejected                                                                                                                                                                                                             |
|-----------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Real Data | It may be difficult to curate a large and diverse enough dataset from real traffic. Malicious traffic is not able to be simulated easily without installing a virtual machine, which currently requires too much  overhead. |

## Consequences
- The Dataset has a few faulty labels and some missing data, so it may not persist perfectly across the models
- It's outdated, so it may miss certain patterns that are used currently and have not been used previously.
- The models will have a training dataset to classify malicious traffic and understand what it looks like.