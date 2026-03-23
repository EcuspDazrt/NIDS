# ADR-021: Logging

**Date:** 2026-03-15  
**Status:** Accepted

## Context
In order for the system to hold up its integrity and efficiency, there must also be a way for the system to be monitored as well as ported to external tools.

## Decision
- Log individual flows and alerts (alerts will be written in two different forms - .db and .log - to allow for easy-reading locally and portability to external tools such as syslog or SIEM)
- Separate retrain events and drift checks into a different logging section

## Alternatives Considered
| Option                                                                | Reason Rejected                                                                                                                                                                                              |
|-----------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Combine alerts, model drift, and retrain events into one logging file | Although this would technically allow for all the monitoring to come from a single place, it would overall make the logging less clean and it would be difficult to monitor any single alert type on its own |

## Consequences
The logs will be easily monitored and will allow for portability to external tools efficiently.