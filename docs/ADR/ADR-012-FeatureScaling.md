# ADR-012: Feature Scaling

**Date:** 2026-03-09
**Status:** Accepted - Modified by [ADR-022](ADR-022-RemoveRobustScaler.md)

## Context
- Network traffic features can be skewed immensely, and require the correct scaling methods to maintain the model's precision and recall.
- The models must learn what general traffic looks like, and not simply identify large flows as malicious simply because they are outliers.

## Decision
- For the autoencoder: log1p on each feature, then apply StandardScaler.
- For the random forest: apply RobustScaler only. (See [ADR-022](ADR-022-RemoveRobustScaler.md) for the modification)


## Alternatives Considered
| Option                                   | Reason Rejected                                                                                                                                                                                                                                                                                                                   |
|------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Only apply Log1p on AutoEncoder          | Log1p handles the skewed data accurately, but won't normalize the mean and variance across features, which may make it so certain features will dominate reconstruction error rather than having an even split.                                                                                                                   |
| No normalization for the Random Forest   | Although for the training itself this would not matter, during inference time, the data will need to be scaled in a way such that the inference data will match the scale of the random forest data for increased integrity of the model. It adds an extra layer of correctness that the random forest may need in harsh cases.   |

## Consequences
- All the data will be normalized properly and be consistently passed through each model.
- The overall model's precision and recall will be much higher due to the fact that it will generalize at a greater scale than it would without.