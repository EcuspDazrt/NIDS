# ADR-016: Offline Retraining

**Date:** 2026-03-10
**Status:** Accepted

## Context
- In order to combat model drift, there should be some form of offline retraining, allowing the models to learn traffic patterns without becoming outdated.

## Decisions
- Don't retrain the random forest.
- Retrain the auto-encoder.

## Alternatives Considered
| Option                    | Reason Rejected                                                                                                                                                                                                                           |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Retrain the random forest | Since the random forest is a supervised model, it would need to be fed labeled malicious and benign data. Although benign data could be easily labeled as such, high-confidence malicious data would be difficult to come by continuously |

## Consequences
- The random forest will continue to identify explicit attacks.
- The auto-encoder will be able to adapt to a network's benign traffic and allow for more accurate predictions