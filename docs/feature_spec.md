# Feature Specifications
## 1. LibPcap Data
Data captured directly from the network scraper (with disabled LRO and GRO)
- Timestamp
- On-wire packet length
- Raw packet bytes
- Data link type\
<small>*Set snaplen as to not capture full packet unnecessarily</small>

## 2. Parsed-byte data
### 2.1 Ethernet/Link layer (2)
- EtherType (determines network Protocol) -> from data link type 
### 2.2 Network layer (3)
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
- If TCP - Flags counters (SYN, ACK, FIN, RST, PSH, URG)
- Source port
- Destination port
- Length
### 2.4 Direction Handling
For each flow, the direction will be established as the direction of the packet that starts the flow.
Then, this will stay consistent while the flow is active. Each flow will then track the direction counters to determine:
- Forward bytes
- Forward packet count
- Backward bytes
- Backward packet count


## 3. Flow state
Sorted into 5-tuple categories (flow-id, src ip, dsp ip, src port, dst port)  
**Store epoch ID for each, increment each time a flow is timed-out and separate into a different flow state**
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
| Feature Name         | Computed From                                                                   | Restrictions |
|----------------------|---------------------------------------------------------------------------------|--------------|
| Protocol encoding    | protocol                                                                        | -            |
| Port category        | sorting ports into well-known, ephemeral, and unusual                           | -            |
| Network type         | local vs external ip                                                            | -            |
| Duration             | last seen time - start time                                                     | -            |
| Total Byte rate      | (forward bytes + backward bytes) / (last seen time - start time)                | -            |
| Total packet rate    | (forward packets + backward packets) / (last seen time - start time)            | -            |
| Min total bytes      | min(min forward bytes, min backward bytes)                                      | -            |
| Max total bytes      | max(max forward bytes, max backward bytes)                                      | -            |
| Mean total bytes     | (forward bytes + backward bytes) / (forward packets + backward packets)         | -            |
| Min IAT              | min(min forward IAT, min backward IAT)                                          | -            |
| Max IAT              | max(max forward IAT, max backward IAT)                                          | -            |
| Mean IAT             | (forward total IAT + backward total IAT) / (forward packets + backward packets) | -            |
| Forward packet rate  | forward packets / (last seen time - start time)                                 | -            |
| Forward Packets      | forward packets                                                                 | -            |
| Forward Bytes        | forward bytes                                                                   | -            |
| Forward Bytes Max    | max forward bytes                                                               | -            |
| Forward Bytes Min    | min forward bytes                                                               | -            |
| Forward Bytes Mean   | forward bytes / forward packets                                                 | -            |
| Forward IAT Total    | forward total IAT                                                               | -            |
| Forward IAT Max      | max forward IAT                                                                 | -            |
| Forward IAT Min      | min forward IAT                                                                 | -            |
| Forward IAT Mean     | forward IAT / forward packets                                                   | -            |
| Backward Packet Rate | backward packets / (last seen time - start time)                                | -            |
| Backward Packets     | backward packets                                                                | -            |
| Backward Bytes       | backward bytes                                                                  | -            |
| Backward Bytes Max   | max backward bytes                                                              | -            |
| Backward Bytes Min   | min backward bytes                                                              | -            |
| Backward Bytes Mean  | backward bytes / backward packets                                               | -            |
| Backward IAT Total   | backward total IAT                                                              | -            |
| Backward IAT Max     | max backward IAT                                                                | -            |
| Backward IAT Min     | min backward IAT                                                                | -            |
| Backward IAT Mean    | backward IAT / backward packets                                                 | -            |
| In/out ratio         | forward packets / backward packets                                              | -            |
| Active Mean          | active period total / active period count                                       | -            |
| Active Max           | max active period                                                               | -            |
| Active Min           | min active period                                                               | -            |
| Idle Mean            | idle period total / idle period count                                           | -            | 
| Idle Max             | max idle period                                                                 | -            | 
| Idle Min             | min idle period                                                                 | -            |
| Syn ratio            | syn count / (forward packets + backward packets)                                | TCP Only     |
| Ack ratio            | ack count / (forward packets + backward packets)                                | TCP Only     |
| Fin ratio            | fin count / (forward packets + backward packets)                                | TCP Only     |
| Rst ratio            | rst count / (forward packets + backward packets)                                | TCP Only     |
| Syn rate             | syn count / (last seen time - start time)                                       | TCP Only     |
| Ack rate             | ack count / (last seen time - start time)                                       | TCP Only     |
| Fin rate             | fin count / (last seen time - start time)                                       | TCP Only     |
| Rst rate             | rst count / (last seen time - start time)                                       | TCP Only     |
| Syn/Ack ratio        | syn count / ack count                                                           | TCP Only     |
| Fin/Ack ratio        | fin count / ack count                                                           | TCP Only     |
| Rst/Syn ratio        | rst count / syn count                                                           | TCP Only     |
| Failed Connection    | seen_syn && !handshake complete && flow terminated                              | TCP Only     |
