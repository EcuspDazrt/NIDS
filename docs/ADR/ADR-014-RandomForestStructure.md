# ADR-014: Random Forest Structure

**Date:** 2026-03-10
**Status:** Accepted

## Context
- In order for the random forest to be most efficient in recall and precision, the hyperparameters must be tuned

## Decisions
- Number of trees: 300
- Max depth of tree: None
- Minimum number of samples per leaf: 20
- Class weight: balanced subsample
- Random State (seed): 42

## Alternatives Considered
| Option                                  | Reason Rejected                                                                                                                                                                                                                                             |
|-----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Number of trees: 100                    | This would be sufficient for small datasets, but with over 3M training samples and 13 attack categories, 100 trees would not be enough to distinguish between benign flows and malicious flows                                                              |
| Max depth of tree: Integer              | Although this would be beneficial to prevent overfitting on a random forest with a small number of trees, the pure number of trees will make it so each tree will be able to generalize well and distinguish between flow categories when it's not limited. |
| Minimum number of samples per leaf: 1   | This would allow for memorization of rare attack samples since they would be able to be grouped into their own category with no drawbacks. Setting this higher would counteract this tendency and make the model generalize more efficiently.               |

## Consequences
- The overall number of trees will allow the model to generalize efficiently and cover many types of attacks without running out of tabular space, and is optimized to not increase the inference time unnecessarily.
- Allowing trees to grow to full depth lets each tree perfectly partition the training data, and with the total number of trees, will produce increasingly accurate results, allowing each tree to average the others out and prevent overfitting.
- The random forest will not memorize rare attack types and will generalize to a greater degree.