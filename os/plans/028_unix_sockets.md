# Milestone 28: Unix Domain Sockets (`AF_UNIX`) Subsystem

## Overview
Implement the Unix Domain Sockets (`AF_UNIX` / `AF_LOCAL`) subsystem for Kale OS. Provides zero-copy, kernel-buffered local inter-process communication using VFS filesystem paths, supporting connection-oriented byte streams (`SOCK_STREAM`), connectionless datagrams (`SOCK_DGRAM`), connection backlogs, and peer credential verification.

## Technical Architecture
1. **Address Structure (`sockaddr_un`)**:
   - `sun_family`: Address family (`AF_UNIX = 1`).
   - `sun_path`: 108-byte null-terminated file path (e.g. `"/var/run/display.sock"`).
2. **Socket States & Lifecycle**:
   - `UNIX_SOCK_CLOSED` (0)
   - `UNIX_SOCK_UNBOUND` (1)
   - `UNIX_SOCK_BOUND` (2)
   - `UNIX_SOCK_LISTENING` (3)
   - `UNIX_SOCK_CONNECTED` (4)
3. **Queue & Buffer Architecture**:
   - Bidirectional circular ring buffers (512 bytes each) between paired sockets.
   - Pending connections backlog (up to 8 queued connections per listening socket).
   - Peer linkage: When server executes `accept()`, a new accepted socket endpoint is created and interconnected with the connecting client.
4. **I/O Operations**:
   - `unix_socket_create`: Allocates a new socket table descriptor.
   - `unix_socket_bind`: Associates socket with a filesystem path and checks for collisions.
   - `unix_socket_listen`: Transitions to listening state and configures connection backlog.
   - `unix_socket_connect`: Finds listening server by path, creates handshake, and queues client.
   - `unix_socket_accept`: Dequeues pending client connection and establishes peer relationship.
   - `unix_socket_send` / `unix_socket_recv`: Writes/reads data to/from peer ring buffer with EOF detection upon peer close.

## Deliverables
- `os/plans/028_unix_sockets.md`: Architectural specification.
- `os/kernel/unix_sock.kl`: Pure Kale Unix domain socket manager, state machine, and ring buffer IPC.
- `tests/test_os_unix_sockets.py`: Test suite validating socket creation, binding, listening, client-server handshake, bidirectional data exchange, backlog queueing, and peer disconnection.
