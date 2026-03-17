# ADR-005: Redis

**Date:** 2026-03-04  
**Status:** Superseded by [ADR-009](ADR-009-MultiProcessing.md)

## Context
- In order to have an efficient and low-latent system, there must be a mechanism to decouple the capture and inference modules

## Decision
Redis.

## Alternatives Considered
| Option                   | Reason Rejected                                                                                                                                         |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| Multi Processing Library | It will not scale across multiple machines as there will be no way to access the network queue that is attached to each device from a separate machine. |

## Consequences
- The system will be able to detect malicious behavior across multiple systems
- The inference and capture modules will be decoupled properly for low-latency