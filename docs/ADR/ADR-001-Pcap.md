# ADR-001: Packet Capture Library

**Date:** 2026-03-02  
**Status:** Accepted

## Context
- Latency is a constraint with packet capture
- Something lower level, with higher control would be needed

## Decision
LibPcap.

## Alternatives Considered
| Option  | Reason Rejected                                                      |
|---------|----------------------------------------------------------------------|
| Scapy   | Creates objects for every packet capture - includes unnecessary data |
| PyShark | Same thing as Scapy, and does not allow for truncation               |

## Consequences
This decision makes packet capture faster and makes it so less memory is used.
