# ADR-007: Epoch Flow ID

**Date:** 2026-03-04  
**Status:** Accepted

## Context
- When considering network traffic, it is important to distinguish between timed-out flows and current flows, even if it's from a familiar connection.
- Timing statistics will explode if there is no way to time-out flows

## Decision
Epoch Flow ID

## Alternatives Considered
| Option                                         | Reason Rejected                                                                                                                                                                                                                                                                                                                 |
|------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Deleting flows from the queue without epoch ID | Although this would be a valid solution to the problem, it would be more efficient to use an epoch-ID to time-out flows in order to establish a greater level of semantics when logged flows are being sorted for offline training. If a given connection attempts to connect many times, it may be an important signal to use. |

## Consequences
- Flows will be established by the standard 5-tuple accompanied by an Epoch-ID that adds a new level of semantics to the system
- Establishes a greater level of integrity across flow time-outs