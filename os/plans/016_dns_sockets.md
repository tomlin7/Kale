# Milestone 16: DNS Resolver & Transport Protocol Sockets

## Overview
Implement Domain Name System (DNS) resolution and the Transport Protocol Socket Layer for Kale OS. This milestone establishes RFC 1035 DNS packet generation and parsing over UDP, introduces the standard Berkeley socket API abstraction (`socket`, `bind`, `connect`, `send`, `recv`, `close`), and implements the TCP finite state machine.

## Architecture

```
                       +-----------------------------+
                       |      Network Manager        |
                       +--------------+--------------+
                                      |
            +-------------------------+-------------------------+
            |                                                   |
            v                                                   v
     [DNS Resolver]                                      [Socket Layer]
   (os/kernel/dns.kl)                                 (os/kernel/socket.kl)
  RFC 1035 QNAME Labels                              AF_INET / SOCK_STREAM / SOCK_DGRAM
  Type A IPv4 Resolution                             TCP State Machine (SYN/ACK/FIN)
```

## Phases

### Phase 1: RFC 1035 DNS Message Framing
- Header format (12 bytes):
  - `id`: 16-bit transaction identifier.
  - `flags`:
    - QR bit (0 = Query, 1 = Response).
    - Opcode (0 = Standard Query).
    - AA (Authoritative Answer), TC (Truncated), RD (Recursion Desired = 1).
    - RA (Recursion Available), RCODE (Response Code: 0 = No Error, 3 = Name Error).
  - `qdcount`: Number of questions (1).
  - `ancount`: Number of answer records.
  - `nscount`: Number of authority records.
  - `arcount`: Number of additional records.

### Phase 2: QNAME Label Serialization & Answer Parsing
- QNAME format: Sequence of length-prefixed labels ending with a zero byte:
  - `"kale-lang.org"` -> `[9] 'k' 'a' 'l' 'e' '-' 'l' 'a' 'n' 'g' [3] 'o' 'r' 'g' [0]`.
- Question trailer:
  - `QTYPE`: Type A = `0x0001` (IPv4).
  - `QCLASS`: Class IN = `0x0001` (Internet).
- Answer parser:
  - Pointer decompression (handles `0xC000` offset pointers).
  - Validates `TYPE == 1` and `RDLENGTH == 4`.
  - Extracts resolved 32-bit IPv4 address (e.g. `192.0.2.1`).

### Phase 3: Socket API & Types
- Socket Families: `AF_INET = 2`.
- Socket Types:
  - `SOCK_STREAM = 1` (TCP reliable stream).
  - `SOCK_DGRAM = 2` (UDP datagram).
- `Socket` structure:
  - `fd`, `family`, `type`, `state`.
  - `local_ip`, `local_port`.
  - `remote_ip`, `remote_port`.
  - Sequence and acknowledgment numbers (`seq_num`, `ack_num`).
  - Ring buffer storage.

### Phase 4: TCP Finite State Machine
- State transitions:
  - `CLOSED` -> `LISTEN` (via `bind()` + `listen()`).
  - `CLOSED` -> `SYN_SENT` (via `connect()`).
  - `SYN_SENT` -> `ESTABLISHED` (upon receiving SYN+ACK).
  - `LISTEN` -> `SYN_RECEIVED` (upon receiving SYN).
  - `SYN_RECEIVED` -> `ESTABLISHED` (upon receiving ACK).
  - `ESTABLISHED` -> `FIN_WAIT_1` / `CLOSE_WAIT` -> `LAST_ACK` / `TIME_WAIT` -> `CLOSED`.
