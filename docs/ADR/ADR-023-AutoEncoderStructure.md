# ADR-023: Auto-Encoder Structure

**Date:** 2026-03-24
**Status:** Accepted

## Context
- The auto-encoder structure must have an aggressive enough bottleneck to meaningfully compress the feature set
- The auto-encoder structure must have enough room to be able to learn a significant representation of the feature set

## Decision
- The bottleneck will be 20 -> 32 -> 16 -> 8 -> 16 -> 32 -> 20; ballooning the original features by 160%, compressing the ballooned representation by 25%, and allowing the model to learn general patterns efficiently.
- Batch normalization and dropout will be applied at after each layer of the encoder.
- Dropout: 0.1
- Activation type: ReLU


## Alternatives Considered
| Option                                               | Reason Rejected                                                                                                                                                                                                                                    |
|------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Bottleneck of 20 -> 16 -> 8 -> 4 -> 8 -> 16 -> 20    | Although this bottleneck would potentially force the model to compress the data into a meaningful signal, from testing it ended up losing too much signal drop, and not performing as well as other structures.                                    |
| Bottleneck of 20 -> 16 -> 10 -> 6 -> 10 -> 16 -> 20  | Although this bottleneck would have a slightly more lenient bottleneck to fix the compression signal loss issue, it did not end up being enough to fix the issue; there was no room for the model to make a meaningful representation of the data  |

## Consequences
- The model will be forced to learn only the essential structure of traffic, reducing noise and creating more accurate predictions along the line while allowing room for the model to initially expand its representation of the data.

### Continuation from previous structure:  
- Network traffic features, even after the normalization that goes in the model beforehand, will develop slight shifts as they pass through the linear transformations. Batch renormalization re-centers and rescales the activation after each layer.
- The dropout will prevent individual neurons from becoming dependent on specific input features, and will allow the model to learn representations rather than individual features.