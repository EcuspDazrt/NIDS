# ADR-011: Feature Selection

**Date:** 2026-03-09
**Status:** Accepted

## Context
- In order for each of the models to achieve the greatest precision and recall metrics possible, the features must be carefully selected with large significance in the model's decision.

## Decision
- For the random forest: raw statistics and counts, means, standard deviation, variance, rates, symmetry statistics, and TCP flags
- For the auto-encoder: means, standard deviation, variance, rates, and symmetry statistics

## Alternatives Considered
| Option                                                  | Reason Rejected                                                                                                                                                                             |
|---------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Using all the features for both models: around 60 total | The auto-encoder would learn too much noise in this case, and would not be able to accurately learn the behavioral patterns that malicious attacks tend to have.                            |
| Using only the aggregated features for each model       | The random forest model would not have as much information to accurately split the training data into groups, and would have a hard time deciphering between malicious and benign attacks   |       

## Consequences
- The auto-encoder will be able to learn a pattern of traffic that does not have much noise attributed to it, and has meaningful compression throughout.
- The random forest, being robust to noise, will be able to have enough information to split the data into benign and malicious groups accurately.