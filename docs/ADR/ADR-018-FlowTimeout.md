# ADR-018: Flow Timeout

**Date:** 2026-03-12
**Status:** Accepted

## Context
- To ensure the system will properly scrape each flow and not leave it in queue, there must be a system to sweep the queue periodically to find any non-timed out flows that pass a certain activity threshold.


## Decisions
- Use a 10-second sweep period to detect if a flow has a 120-second activity time
- Keep the existing timeout logic in which an epoch ID is incremented each time a flow is timed out
- Keep the existing timeout logic in which the flow is timed out when a 'rst' or 'fin' flag is detected or when the proceeding packet has an IAT greater than 60 seconds.

## Alternatives Considered
| Option                                                            | Reason Rejected                                                                                                                                                                                                                                                                                                                                                                              |
|-------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Remove the previous timeout logic and use activity threshold only | Although the activity timeout threshold could potentially prove efficient to determine flow time-outs itself, it would be most beneficial to separate flows that send an 'rst' or 'fin' flag as well as those that have an IAT time greater than 60 seconds since they are also good indicators that a flow is completed, adding an additional layer of accuracy in timing out a given flow. |

## Consequences
- Flows will now be more accurately timed out when they should
- When flows send rapid packets and then don't send any more after a certain amount of time, they used to be stuck in the flow queue - but they will now be caught and ran through the system