# Feature Specifications

## 1. Feature tables
| Feature Name              | Computed From                                          | Type      |
| ------------------------- | ------------------------------------------------------ | --------- |
| Protocol encoding         | protocol                                               | Identity  |
| Port category             | sorting ports into well-known, ephermeral, and unusual | Identity  |
| Network type              | local vs external ip                                   | Identity  |
| Duration                  | last seen time - start time                            | Timing    |
| Byte rate                 | total bytes / duration                                 | Timing    |
| Packet rate               | total packets / duration                               | Timing    |
| Forward rate              | forward packets / duration                             | Timing    |
| Backward rate             | backward packets / duration                            | Timing    |
| Min interarrival time     | min interarrival                                       | Timing    |
| Max interarrival time     | max interarrival                                       | Timing    |
| Mean interarrival time    | mean interarrival                                      | Timing    |
| Min packet size           | min packet size                                        | Sizes     |
| Max packet size           | max packet size                                        | Sizes     |
| Mean packet size          | mean packet size                                       | Sizes     |
| Variance in packet size   | variance in size                                       | Sizes     |
| In/out ratio              | forward packets / backward packets                     | Counters  |
| Byte/Packet ratio         | total bytes / total packets                            | Counters  |
| Syn ratio                 | syn count / total packets                              | TCP Flags |
| Ack ratio                 | ack count / total packets                              | TCP Flags |
| Fin ratio                 | fin count / total packets                              | TCP Flags |
| Rst ratio                 | rst count / total packets                              | TCP Flags |
| Syn rate                  | syn count / duration                                   | TCP Flags |
| Ack rate                  | ack count / duration                                   | TCP Flags |
| Fin rate                  | fin count / duration                                   | TCP Flags |
| Rst rate                  | rst count / duration                                   | TCP Flags |
| Syn/Ack ratio             | syn count / ack count                                  | TCP Flags |
| Fin/Ack ratio             | fin count / ack count                                  | TCP Flags |
| Rst/Syn ratio             | rst count / syn count                                  | TCP Flags |
| Failed connection ratio   | num failed connections / total packets                 | Errors    |
| Reset ratio               | num resets / total packets                             | Errors    |



## 2. Raw flow data
### 2.1 Indentity
- Srp ip
- Dst ip
- Src port
- Dst port
- Protocol
### 2.2 Timing
- Start time
- Last seen time
- Min interarrival
- Max interarrival
- Mean interarrival
### 2.3 Counters
- Total packets
- Total bytes
- Forward packets
- Backward packets
### 2.4 TCP Flags
- Syn count
- Ack count
- Fin count
- Rst count
### 2.5 Sizes
- Min packet size
- Max packet size
- Mean packet size
- Variance in size
### 2.6 Errors
- Num failed connections
- Num resets