# ADR-015: Auto-Encoder Structure

**Date:** 2026-03-10
**Status:** Superseded by [ADR-023](ADR-023-AutoEncoderStructure.md)

## Context
- The auto-encoder structure must be optimized to counteract against direct memorization of features so it will learn general patterns across the features.

## Decisions
- The bottleneck will be 20 -> 16 -> 8 -> 4 -> 8 -> 16 -> 20; compressing the original features by 80% and allowing the model to learn general patterns rather than memorize each feature.
- Batch normalization and dropout will be applied at after each layer of the encoder.
- Dropout: 0.1
- Activation type: ReLU

## Alternatives Considered
| Option                                              | Reason Rejected                                                                                                                                                                                                    |
|-----------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Bottleneck of 20 -> 32 -> 16 -> 8 -> 16 -> 32 -> 20 | Although this would still allow for the model to learn general patterns, it initially makes the data balloon into inflated representations, making the model again learn individual features rather than patterns. |

## Consequences
- The model will be forced to learn only the essential structure of traffic, reducing noise and creating more accurate predictions along the line.
- Network traffic features, even after the normalization that goes in the model beforehand, will develop slight shifts as they pass through the linear transformations. Batch renormalization re-centers and rescales the activation after each layer.
- The dropout will prevent individual neurons from becoming dependent on specific input features, and will allow the model to learn representations rather than individual features.