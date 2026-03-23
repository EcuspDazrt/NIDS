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

## 4. Feature table
***Variance Formulas for training are approximations - Inference will be handled differently than training***

| Feature Name                 | Computed From (training)                                                                           | Computed from (inference)                                                      | Restrictions | Model |
|------------------------------|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|--------------|-------|
| Protocol Encoding            | protocol                                                                                           | protocol                                                                       | -            | RF    |
| Port Category                | sorting ports into well-known, ephemeral, and unusual                                              | sorting ports into well-known, ephemeral, and unusual                          | -            | RF    |
| Network Type                 | local vs external ip                                                                               | local vs external ip                                                           | -            | RF    |
| Duration                     | duration                                                                                           | last seen time - start time                                                    | -            | Both  |
| In/out Ratio                 | forward packets / backward packets                                                                 | forward packets / backward packets                                             | -            | Both  |
| Absolute Difference          | abs(forward packets - backward packets) / (forward packets + backward packets)                     | abs(forward packets - backward packets) / (forward packets + backward packets) | -            | AE    |
| Byte Rate Asymmetry          | abs(forward bytes / duration) - (backward bytes / duration)                                        | abs(forward bytes / duration) - (backward bytes / duration)                    | -            | AE    |
| Total Packets                | forward packets + backward packets                                                                 | forward packets + backward packets                                             | -            | RF    |
| Total Bytes                  | forward bytes + backward bytes                                                                     | forward bytes + backward bytes                                                 | -            | RF    |
| Total Packet Rate            | (forward packets + backward packets) / duration                                                    | (forward packets + backward packets) / (last seen time - start time)           | -            | RF    |
| Total Byte Rate              | (forward bytes + backward bytes) / duration                                                        | (forward bytes + backward bytes) / duration                                    | -            | RF    |
| Total Max Bytes              | max(max forward bytes, max backward bytes)                                                         | total bytes stats . max (running max)                                          | -            | RF    |
| Total Min Bytes              | min(min forward bytes, min backward bytes)                                                         | total bytes stats . min (running min)                                          | -            | RF    |
| Total Mean Bytes             | (forward bytes + backward bytes) / (forward packets + backward packets)                            | (forward bytes + backward bytes) / (forward packets + backward packets)        | -            | RF    |
| ***Total Byte Variance***    | ((Total Max Bytes - Total Mean Bytes)^2 + (Total Mean Bytes - Total Min Bytes)^2)) / 2             | total bytes stats . variance (welford online algorithm)                        | -            | RF    |
| Total Bytes Std              | total byte std                                                                                     | total bytes stats . std (welford online algorithm)                             | -            | RF    |
| Forward Packets              | forward packets                                                                                    | forward packets                                                                | -            | RF    |
| Forward Bytes                | forward bytes                                                                                      | forward bytes                                                                  | -            | RF    |
| Forward Packet Rate          | forward packets / duration                                                                         | forward packets / (last seen time - start time)                                | -            | Both  |
| Forward Byte Rate            | forward bytes / duration                                                                           | forward bytes / (last seen time - start time)                                  | -            | Both  |
| Forward Bytes Max            | max forward bytes                                                                                  | forward bytes stats . max (running max)                                        | -            | RF    |
| Forward Bytes Min            | min forward bytes                                                                                  | forward bytes stats . min (running min)                                        | -            | RF    |
| Forward Bytes Mean           | forward bytes / forward packets                                                                    | forward bytes stats . mean (running mean)                                      | -            | Both  |
| ***Forward Byte Variance***  | ((Forward Max Bytes - Forward Mean Bytes)^2 + (Forward Mean Bytes - Forward Min Bytes)^2)) / 2     | forward bytes stats . variance (welford online algorithm)                      | -            | RF    |
| Forward Byte Std             | forward byte std                                                                                   | forward bytes stats . std (welford online algorithm)                           | -            | Both  |
| Backward Packets             | backward packets                                                                                   | backward packets                                                               | -            | RF    |
| Backward Bytes               | backward bytes                                                                                     | backward bytes                                                                 | -            | RF    |
| Backward Packet Rate         | backward packets / duration                                                                        | backward packets / (last seen time - start time)                               | -            | Both  |
| Backward Byte rate           | backward bytes / duration                                                                          | backward bytes / (last seen time - start time)                                 | -            | Both  |
| Backward Bytes Max           | max backward bytes                                                                                 | backward bytes stats . max (running max)                                       | -            | RF    |
| Backward Bytes Min           | min backward bytes                                                                                 | backward bytes stats . min (running min)                                       | -            | RF    |
| Backward Bytes Mean          | backward bytes / backward packets                                                                  | backward bytes stats . mean (running mean)                                     | -            | Both  |
| ***Backward Byte Variance*** | ((Backward Max Bytes - Backward Mean Bytes)^2 + (Backward Mean Bytes - Backward Min Bytes)^2)) / 2 | backward bytes stats . variance (welford online algorithm                      | -            | RF    |
| Backward Byte Std            | backward byte std                                                                                  | backward bytes stats . std (welford online algorithm)                          | -            | Both  |              
| Total IAT                    | forward total IAT + backward total IAT                                                             | forward total IAT + backward total IAT                                         | -            | RF    |
| Total IAT Max                | max(max forward IAT, max backward IAT)                                                             | total IAT stats . max (running max)                                            | -            | RF    |
| Total IAT Min                | min(min forward IAT, min backward IAT)                                                             | total IAT stats . min (running min)                                            | -            | RF    |
| Total IAT Mean               | (forward total IAT + backward total IAT) / (forward packets + backward packets)                    | total IAT stats. mean (running mean)                                           | -            | RF    |
| ***Total IAT Variance***     | ((Total IAT Max - Total IAT Mean)^2 + (Total IAT Mean - Total IAT Min)^2)) / 2                     | total IAT stats . variance (welford online algorithm)                          | -            | RF    |
| Total IAT Std                | total IAT std                                                                                      | total IAT stats . std (welford online algorith)                                | -            | RF    |                                                                                      
| Forward IAT                  | forward total IAT                                                                                  | forward total IAT                                                              | -            | RF    |
| Forward IAT Max              | max forward IAT                                                                                    | forward IAT stats . max (running max)                                          | -            | RF    |
| Forward IAT Min              | min forward IAT                                                                                    | forward IAT stats . min (running min)                                          | -            | RF    |
| Forward IAT Mean             | forward IAT / forward packets                                                                      | forward IAT stats. mean (running mean)                                         | -            | Both  |
| ***Forward IAT Variance***   | ((Forward IAT Max - Forward IAT Mean)^2 + (Forward IAT Mean - Forward IAT Min)^2)) / 2             | forward IAT stats . variance (welford online algorithm)                        | -            | RF    |
| Forward IAT Std              | forward IAT std                                                                                    | forward IAT stats . std (welford online algorith)                              | -            | Both  |
| Backward IAT                 | backward total IAT                                                                                 | backward total IAT                                                             | -            | RF    |
| Backward IAT Max             | max backward IAT                                                                                   | backward IAT stats . max (running max)                                         | -            | RF    |
| Backward IAT Min             | min backward IAT                                                                                   | backward IAT stats . min (running min)                                         | -            | RF    |
| Backward IAT Mean            | backward IAT / backward packets                                                                    | backward IAT stats. mean (running mean)                                        | -            | Both  |
| ***Backward IAT Variance***  | ((Backward IAT Max - Backward IAT Mean)^2 + (Backward IAT Mean - Backward IAT Min)^2)) / 2         | backward IAT stats . variance (welford online algorithm)                       | -            | RF    |
| Backward IAT Std             | backward IAT std                                                                                   | backward IAT stats . std (welford online algorith)                             | -            | Both  |     
| Active Max                   | max active period                                                                                  | active stats . max (running max)                                               | -            | RF    |
| Active Min                   | min active period                                                                                  | active stats . min (running min)                                               | -            | RF    |
| Active Mean                  | active period total / active period count                                                          | active stats . mean (running mean)                                             | -            | Both  |
| ***Active Variance***        | ((Active Max - Active Mean)^2 + (Active Mean - Active min)^2) / 2                                  | active stats. variance (welford online algorithm)                              | -            | RF    |
| Active Std                   | active std                                                                                         | active stats. std (welford online algorithm)                                   | -            | Both  |
| Idle Max                     | max idle period                                                                                    | idle stats . max (running max)                                                 | -            | RF    |
| Idle Min                     | min idle period                                                                                    | idle stats . min (running min)                                                 | -            | RF    |
| Idle Mean                    | idle period total / idle period count                                                              | idle stats . mean (running mean)                                               | -            | Both  | 
| ***Idle Variance***          | ((Idle Max - Idle Mean)^2 + (Idle Mean - Idle min)^2) / 2                                          | idle stats. variance (welford online algorithm)                                | -            | RF    |
| Idle Std                     | idle std                                                                                           | idle stats. std (welford online algorithm)                                     | -            | Both  |
| Syn ratio                    | syn count / (forward packets + backward packets)                                                   | syn count / (forward packets + backward packets)                               | TCP Only     | RF    |
| Ack ratio                    | ack count / (forward packets + backward packets)                                                   | ack count / (forward packets + backward packets)                               | TCP Only     | RF    |
| Fin ratio                    | fin count / (forward packets + backward packets)                                                   | fin count / (forward packets + backward packets)                               | TCP Only     | RF    |
| Rst ratio                    | rst count / (forward packets + backward packets)                                                   | rst count / (forward packets + backward packets)                               | TCP Only     | RF    |
| Syn rate                     | syn count / duration                                                                               | syn count / (last seen time - start time)                                      | TCP Only     | RF    |
| Ack rate                     | ack count / duration                                                                               | ack count / (last seen time - start time)                                      | TCP Only     | RF    |
| Fin rate                     | fin count / duration                                                                               | fin count / (last seen time - start time)                                      | TCP Only     | RF    |
| Rst rate                     | rst count / duration                                                                               | rst count / (last seen time - start time)                                      | TCP Only     | RF    |
| Syn/Ack ratio                | syn count / ack count                                                                              | syn count / ack count                                                          | TCP Only     | RF    |
| Fin/Ack ratio                | fin count / ack count                                                                              | fin count / ack count                                                          | TCP Only     | RF    |
| Rst/Syn ratio                | rst count / syn count                                                                              | rst count / syn count                                                          | TCP Only     | RF    |
