# Feature Specifications
Data captured directly from the network scraper (with disabled LRO and GRO)
## 1. LibPcap Data
LibPcap directly captures:
- Timestamp
- On-wire packet length (pcap_pkthdr.len)
- Raw packet bytes
- Data link type

*Snap length will be set to 128 bytes to account for:
- Ethernet header (14 bytes)
- IP header (~30 bytes)
- TCP header (~50 bytes)
- Safety margin (34 bytes)

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
- Protocol\
#### For IPv6:
- Next Header (follow the header chain until it hits a protocol)
### 2.3 Transport layer (4)
- If protocol is not TCP or UDP -> skip transport layer
- If TCP - Flags counters (fwd/bwd SYN, fwd/bwd ACK, fwd/bwd FIN, fwd/bwd RST, PSH, URG)
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
Sorted into 6-tuple categories (flow-id, src ip, dsp ip, src port, dst port, protocol)  
**Store epoch ID for each, increment each time a flow is timed-out and separate into a different flow state**\
\
IAT - arrival time between two packets of the same direction
### 3.1 Identity
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
- Syn count
- Ack count
- Fin count
- Rst count
- Seen syn flag
- Seen syn-ack flag
- Seen final ack flag
- Handshake complete flag

## 4. Feature table
| Feature Name                 | Computed From                                                                                      | Restrictions |
|------------------------------|----------------------------------------------------------------------------------------------------|--------------|
| Protocol Encoding            | protocol                                                                                           | -            |
| Port Category                | sorting ports into well-known, ephemeral, and unusual                                              | -            |
| Network Type                 | local vs external ip                                                                               | -            |
| Duration                     | last seen time - start time                                                                        | -            |
| In/out Ratio                 | forward packets / backward packets                                                                 | -            |
| Total Packets                | forward packets + backward packets                                                                 | -            |
| Total Bytes                  | forward bytes + backward bytes                                                                     | -            |
| Total Packet Rate            | (forward packets + backward packets) / (last seen time - start time)                               | -            |
| Total Byte Rate              | (forward bytes + backward bytes) / (last seen time - start time)                                   | -            |
| Total Max Bytes              | max(max forward bytes, max backward bytes)                                                         | -            |
| Total Min Bytes              | min(min forward bytes, min backward bytes)                                                         | -            |
| Total Mean Bytes             | (forward bytes + backward bytes) / (forward packets + backward packets)                            | -            |
| ***Total Byte Variance***    | ((Total Max Bytes - Total Mean Bytes)^2 + (Total Mean Bytes - Total Min Bytes)^2)) / 2             | -            |
| Forward Packets              | forward packets                                                                                    | -            |
| Forward Bytes                | forward bytes                                                                                      | -            |
| Forward Packet Rate          | forward packets / (last seen time - start time)                                                    | -            |
| Forward Byte Rate            | forward bytes / forward packets                                                                    | -            |
| Forward Bytes Max            | max forward bytes                                                                                  | -            |
| Forward Bytes Min            | min forward bytes                                                                                  | -            |
| Forward Bytes Mean           | forward bytes / forward packets                                                                    | -            |
| ***Forward Byte Variance***  | ((Forward Max Bytes - Forward Mean Bytes)^2 + (Forward Mean Bytes - Forward Min Bytes)^2)) / 2     | -            |
| Backward Packets             | backward packets                                                                                   | -            |
| Backward Bytes               | backward bytes                                                                                     | -            |
| Backward Packet Rate         | backward packets / (last seen time - start time)                                                   | -            |
| Backward Byte rate           | backward bytes / backward packets                                                                  | -            |
| Backward Bytes Max           | max backward bytes                                                                                 | -            |
| Backward Bytes Min           | min backward bytes                                                                                 | -            |
| Backward Bytes Mean          | backward bytes / backward packets                                                                  | -            |
| ***Backward Byte Variance*** | ((Backward Max Bytes - Backward Mean Bytes)^2 + (Backward Mean Bytes - Backward Min Bytes)^2)) / 2 | -            |
| Total IAT                    | forward total IAT + backward total IAT                                                             | -            |
| Total IAT Max                | max(max forward IAT, max backward IAT)                                                             | -            |
| Total IAT Min                | min(min forward IAT, min backward IAT)                                                             | -            |
| Total IAT Mean               | (forward total IAT + backward total IAT) / (forward packets + backward packets)                    | -            |
| ***Total IAT Variance***     | ((Total IAT Max - Total IAT Mean)^2 + (Total IAT Mean - Total IAT Min)^2)) / 2                     | -            |
| Forward IAT                  | forward total IAT                                                                                  | -            |
| Forward IAT Max              | max forward IAT                                                                                    | -            |
| Forward IAT Min              | min forward IAT                                                                                    | -            |
| Forward IAT Mean             | forward IAT / forward packets                                                                      | -            |
| ***Forward IAT Variance***   | ((Forward IAT Max - Forward IAT Mean)^2 + (Forward IAT Mean - Forward IAT Min)^2)) / 2             | -            |
| Backward IAT                 | backward total IAT                                                                                 | -            |
| Backward IAT Max             | max backward IAT                                                                                   | -            |
| Backward IAT Min             | min backward IAT                                                                                   | -            |
| Backward IAT Mean            | backward IAT / backward packets                                                                    | -            |
| ***Backward IAT Variance***  | ((Backward IAT Max - Backward IAT Mean)^2 + (Backward IAT Mean - Backward IAT Min)^2)) / 2         | -            |
| Active Max                   | max active period                                                                                  | -            |
| Active Min                   | min active period                                                                                  | -            |
| Active Mean                  | active period total / active period count                                                          | -            |
| ***Active Variance***        | ((Active Max - Active Mean)^2 + (Active Mean - Active min)^2) / 2                                  | -            |
| Idle Max                     | max idle period                                                                                    | -            | 
| Idle Min                     | min idle period                                                                                    | -            |
| Idle Mean                    | idle period total / idle period count                                                              | -            | 
| ***Idle Variance***          | ((Idle Max - Idle Mean)^2 + (Idle Mean - Idle min)^2) / 2                                          | -            |
| Syn ratio                    | syn count / (forward packets + backward packets)                                                   | TCP Only     |
| Ack ratio                    | ack count / (forward packets + backward packets)                                                   | TCP Only     |
| Fin ratio                    | fin count / (forward packets + backward packets)                                                   | TCP Only     |
| Rst ratio                    | rst count / (forward packets + backward packets)                                                   | TCP Only     |
| Syn rate                     | syn count / (last seen time - start time)                                                          | TCP Only     |
| Ack rate                     | ack count / (last seen time - start time)                                                          | TCP Only     |
| Fin rate                     | fin count / (last seen time - start time)                                                          | TCP Only     |
| Rst rate                     | rst count / (last seen time - start time)                                                          | TCP Only     |
| Syn/Ack ratio                | syn count / ack count                                                                              | TCP Only     |
| Fin/Ack ratio                | fin count / ack count                                                                              | TCP Only     |
| Rst/Syn ratio                | rst count / syn count                                                                              | TCP Only     |


| Failed Connection            | seen_syn && !handshake complete && flow terminated                                                 | TCP Only     |
