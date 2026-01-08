# Feature Specifications

## 1. Feature table
Feature Name   | Description                        | Computed From |
------------   | ---------------------------------- | ------------- |
Byte rate      | total bytes / duration             | sizes         |
Syn ratio      | syn Count / total packets          | tcp flags     |
Packet rate    | number of packets / duration       | timestamps    |
In/out ratio   | forward packets / backward packets | packet types  |

## 2. Raw data
### 2.1 Indentity
- Srp ip
- Dst ip
- Src port
- Dst port
- Protocol
### 2.2 Timing
- Start time
- Last seen time
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
### 2.6 Timing
- Min interarrival
- Max interarrival
- Mean interarrival
### 2.7 Errors
- Num failed connections
- Num resets