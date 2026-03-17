# ADR-008: SnapLen

**Date:** 2026-03-06  
**Status:** Accepted

## Context
- When examining flow-based statistics without looking at the payload, it is important to establish whether there should be a snap length, and if so, how much it should be.

## Decision
SnapLen of 256

## Alternatives Considered
| Option                    | Reason Rejected                                                                                                                                                                 |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Full capture              | Potentially a violation of privacy in a given network. Looking at packet payloads can be seen as malicious in of itself and is generally not a good practice for a NIDS system. |
| Snaplen of 128            | This snap length would be too low, and may not capture enough information to accurately reconstruct flows if the packet contains a long flow of IPv4 fragments.                 |
| Snaplen of 512 or above   | This snap length would be largely unnecessary, and would result in discarding a great amount of data. Refer to [Feature Specs](../../docs/feature_spec.md) for details.         |

## Consequences
- An adequate amount of data will be captured from each packet, optimizing for latency
- Avoids a potential violation of privacy
- Avoids the risk of capturing too little data to reconstruct flow-level data