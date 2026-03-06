# Feature Specifications
Data captured directly from the network scraper (with disabled LRO and GRO)
## 1. LibPcap Data
LibPcap directly captures:
- Timestamp
- On-wire packet length (pcap_pkthdr.len)
- Raw packet bytes
- Data link type

*Snap length will be set to 256 bytes to account for:
- Ethernet header (14 bytes)
- IP header (~60 bytes)
- TCP header (~60 bytes)
- Safety margin (122 bytes)

## 2. Parsed-byte data
### 2.1 Ethernet/Link layer (2)
- EtherType (determines network Protocol)
### 2.2 Network layer (3)
*partially handling fragmentation - keep first fragment and discard the rest
#### For all network protocols:
- Source IP
- Destination IP
#### For IPv4 fragmentation detection:</small>
- MF flag
- Fragment offset 
#### For IPv4:
- Header length (to find offset to next header)
- Protocol  
#### For IPv6:
- Next Header (follow the header chain until it hits a protocol)
### 2.3 Transport layer (4)
- If protocol is not TCP or UDP -> skip transport layer
- If TCP - Flags counters (fwd/bwd SYN, fwd/bwd ACK, fwd/bwd FIN, fwd/bwd RST)
- Source port
- Destination port
### 2.4 Direction Handling
For each flow, the direction will be established as the direction of the packet that starts the flow.
Then, this will stay consistent while the flow is active. Each flow will then track the direction counters to determine:
- Forward bytes
- Forward packet flag
- Backward bytes
- Backward packet flag

## 3. Flow state
Sorted into 6-tuple categories (epoch-flow-id, src ip, dsp ip, src port, dst port, protocol)  
**Store epoch ID for each, increment each time a flow is timed-out and separate into a different flow state**\
\
IAT - arrival time between two packets of the same direction
### 3.1 Identity
- Start timestamp
- Last seen timestamp
- Source IP
- Destination IP
- Source port
- Destination port
- Protocol
### 3.2 Running counters
<small>*Direction is observational, not absolute, and is established from the perspective of the packet that initiates the flow</small>
- Forward packets
- Backward packets
- Forward bytes
- Backward bytes
- Forward total IAT
- Backward total IAT
- Active period total
- Active period count
- Idle period total
- Idle period count
### 3.3 Minimum/Maximum trackers
- Min forward bytes
- Min backward bytes
- Min forward IAT
- Min backward IAT
- Min active period
- Min idle period
- Max forward bytes
- Max backward bytes
- Max forward IAT
- Max backward IAT
- Max active period
- Max idle period
### 3.4 TCP-Only
***Will be stored as zero for UDP protocol***
- Syn count
- Ack count
- Fin count
- Rst count
- Seen syn flag
- Seen syn-ack flag
- Seen final ack flag
- Handshake complete flag

## 4. Feature tables
### 4.1 Training
***Variance Formulas are approximation - Inference will be handled differently than training***

| Feature Name                 | Computed From                                                                                      | Restrictions | Model |
|------------------------------|----------------------------------------------------------------------------------------------------|--------------|-------|
| Protocol Encoding            | protocol                                                                                           | -            | RF    |
| Port Category                | sorting ports into well-known, ephemeral, and unusual                                              | -            | RF    |
| Network Type                 | local vs external ip                                                                               | -            | RF    |
| Duration                     | last seen time - start time                                                                        | -            | Both  |
| In/out Ratio                 | forward packets / backward packets                                                                 | -            | Both  |
| Absolute Difference          | abs(forward packets - backward packets) / (forward packets + backward packets)                     | -            | AE    |
| Byte Rate Asymmetry          | abs(forward packets / duration) - (backward packets / duration)                                    | -            | AE    |
| Total Packets                | forward packets + backward packets                                                                 | -            | RF    |
| Total Bytes                  | forward bytes + backward bytes                                                                     | -            | RF    |
| Total Packet Rate            | (forward packets + backward packets) / (last seen time - start time)                               | -            | RF    |
| Total Byte Rate              | (forward bytes + backward bytes) / (last seen time - start time)                                   | -            | RF    |
| Total Max Bytes              | max(max forward bytes, max backward bytes)                                                         | -            | RF    |
| Total Min Bytes              | min(min forward bytes, min backward bytes)                                                         | -            | RF    |
| Total Mean Bytes             | (forward bytes + backward bytes) / (forward packets + backward packets)                            | -            | RF    |
| ***Total Byte Variance***    | ((Total Max Bytes - Total Mean Bytes)^2 + (Total Mean Bytes - Total Min Bytes)^2)) / 2             | -            | RF    |
| Forward Packets              | forward packets                                                                                    | -            | RF    |
| Forward Bytes                | forward bytes                                                                                      | -            | RF    |
| Forward Packet Rate          | forward packets / (last seen time - start time)                                                    | -            | Both  |
| Forward Byte Rate            | forward bytes / (last seen time - start time)                                                      | -            | Both  |
| Forward Bytes Max            | max forward bytes                                                                                  | -            | RF    |
| Forward Bytes Min            | min forward bytes                                                                                  | -            | RF    |
| Forward Bytes Mean           | forward bytes / forward packets                                                                    | -            | Both  |
| ***Forward Byte Variance***  | ((Forward Max Bytes - Forward Mean Bytes)^2 + (Forward Mean Bytes - Forward Min Bytes)^2)) / 2     | -            | RF    |
| Forward Byte Std             | forward byte std                                                                                   | -            | Both  |
| Backward Packets             | backward packets                                                                                   | -            | RF    |
| Backward Bytes               | backward bytes                                                                                     | -            | RF    |
| Backward Packet Rate         | backward packets / (last seen time - start time)                                                   | -            | Both  |
| Backward Byte rate           | backward bytes / (last seen time - start time)                                                     | -            | Both  |
| Backward Bytes Max           | max backward bytes                                                                                 | -            | RF    |
| Backward Bytes Min           | min backward bytes                                                                                 | -            | RF    |
| Backward Bytes Mean          | backward bytes / backward packets                                                                  | -            | Both  |
| ***Backward Byte Variance*** | ((Backward Max Bytes - Backward Mean Bytes)^2 + (Backward Mean Bytes - Backward Min Bytes)^2)) / 2 | -            | RF    |
| Backward Byte Std            | backward byte std                                                                                  | -            | Both  |              
| Total IAT                    | forward total IAT + backward total IAT                                                             | -            | RF    |
| Total IAT Max                | max(max forward IAT, max backward IAT)                                                             | -            | RF    |
| Total IAT Min                | min(min forward IAT, min backward IAT)                                                             | -            | RF    |
| Total IAT Mean               | (forward total IAT + backward total IAT) / (forward packets + backward packets)                    | -            | RF    |
| ***Total IAT Variance***     | ((Total IAT Max - Total IAT Mean)^2 + (Total IAT Mean - Total IAT Min)^2)) / 2                     | -            | RF    |
| Forward IAT                  | forward total IAT                                                                                  | -            | RF    |
| Forward IAT Max              | max forward IAT                                                                                    | -            | RF    |
| Forward IAT Min              | min forward IAT                                                                                    | -            | RF    |
| Forward IAT Mean             | forward IAT / forward packets                                                                      | -            | Both  |
| ***Forward IAT Variance***   | ((Forward IAT Max - Forward IAT Mean)^2 + (Forward IAT Mean - Forward IAT Min)^2)) / 2             | -            | RF    |
| Forward IAT Std              | forward IAT Std                                                                                    | -            | Both  |
| Backward IAT                 | backward total IAT                                                                                 | -            | RF    |
| Backward IAT Max             | max backward IAT                                                                                   | -            | RF    |
| Backward IAT Min             | min backward IAT                                                                                   | -            | RF    |
| Backward IAT Mean            | backward IAT / backward packets                                                                    | -            | Both  |
| ***Backward IAT Variance***  | ((Backward IAT Max - Backward IAT Mean)^2 + (Backward IAT Mean - Backward IAT Min)^2)) / 2         | -            | RF    |
| Backward IAT Std             | backward IAT std                                                                                   | -            | Both  |     
| Active Max                   | max active period                                                                                  | -            | RF    |
| Active Min                   | min active period                                                                                  | -            | RF    |
| Active Mean                  | active period total / active period count                                                          | -            | Both  |
| ***Active Variance***        | ((Active Max - Active Mean)^2 + (Active Mean - Active min)^2) / 2                                  | -            | RF    |
| Active Std                   | active std                                                                                         | -            | Both  |
| Idle Max                     | max idle period                                                                                    | -            | RF    |
| Idle Min                     | min idle period                                                                                    | -            | RF    |
| Idle Mean                    | idle period total / idle period count                                                              | -            | Both  | 
| ***Idle Variance***          | ((Idle Max - Idle Mean)^2 + (Idle Mean - Idle min)^2) / 2                                          | -            | RF    |
| Idle Std                     | idle std                                                                                           | -            | Both  |
| Syn ratio                    | syn count / (forward packets + backward packets)                                                   | TCP Only     | RF    |
| Ack ratio                    | ack count / (forward packets + backward packets)                                                   | TCP Only     | RF    |
| Fin ratio                    | fin count / (forward packets + backward packets)                                                   | TCP Only     | RF    |
| Rst ratio                    | rst count / (forward packets + backward packets)                                                   | TCP Only     | RF    |
| Syn rate                     | syn count / (last seen time - start time)                                                          | TCP Only     | RF    |
| Ack rate                     | ack count / (last seen time - start time)                                                          | TCP Only     | RF    |
| Fin rate                     | fin count / (last seen time - start time)                                                          | TCP Only     | RF    |
| Rst rate                     | rst count / (last seen time - start time)                                                          | TCP Only     | RF    |
| Syn/Ack ratio                | syn count / ack count                                                                              | TCP Only     | RF    |
| Fin/Ack ratio                | fin count / ack count                                                                              | TCP Only     | RF    |
| Rst/Syn ratio                | rst count / syn count                                                                              | TCP Only     | RF    |

[//]: # (| Failed Connection            | seen_syn && !handshake complete && flow terminated                                                 | TCP Only     |)
