# ADR-018: Flow Timeout

**Date:** 2026-10-26
**Status:** Accepted

## Context
- To ensure the system has the best accuracy on new data, the capture logic must mirror the logic used to capture that data that it was trained on.

## Decisions
- Swap out a 60-second idle flow timeout for a 5-second one.
- Swap out a 10-second sweep interval for a 2-second one.

## Alternatives Considered
| Option                                            | Reason Rejected                                                                                                                                                                                                                                                                                                                 |
|---------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Keep the timeout and interval thresholds the same | Although the original thresholds were viable as a stand-alone system, it sacrificed accuracy when it came to extrapolation due to the fact that it added a conflating factor in the differences between training and inference-time data. This was avoided because it would lead to a lower accuracy overall on a real network. |

## Consequences
- Sweeps will now happen much more often, causing more flows to drop.
- The system will now detect flows quicker, giving users a more responsive experience if actively monitoring the dashboard.
- The system may have more flows backed up in memory, leading to a potential overflow if unchecked.