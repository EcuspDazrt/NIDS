# ADR-020: Alert Engine

**Date:** 2026-03-15
**Status:** Accepted

## Context
In order for the system to provide meaningful results to a user in a deployment, the way in which it alerts the user needs to be easy to monitor.

## Decision
- Make the alert engine log the alert
- Send a system notification to the device running the system
- Send the dashboard to a background process and make the tray icon flash when an alert signals

## Alternatives Considered
| Option                                                                                 | Reason Rejected                                                                                                                                                                                                                                  |
|----------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Keep the dashboard as a main process, require the user to monitor the dashboard itself | Although this would allow for less overhead in development, it would make network monitoring more resource-intensive for the device running the system and would require the user to manually look at activity, creating more overhead for them. |

## Consequences
The entire system is easy to monitor and will allow the user to know when there is a perceived attack on the network.