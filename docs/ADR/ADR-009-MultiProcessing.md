# ADR-009: Multi Processing Library

**Date:** 2026-03-07 
**Status:** Accepted

## Context
- For the system to be most efficient, the capture and inference modules must be decoupled (which will also spot potential bottlenecks)

## Decision
Python's Multi Processing Library

## Alternatives Considered
| Option | Reason Rejected                                                                                                       |
|--------|-----------------------------------------------------------------------------------------------------------------------|
| Redis  | Although previously mentioned as the solution to this issue, it would require too much overhead for a single machine. |

## Consequences
- The capture and inference modules will still be decoupled, but with less overhead