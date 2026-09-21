# Milestone 19: Signals & Inter-Process Communication (IPC)

## Overview
Implement POSIX signals and anonymous pipes for Inter-Process Communication (IPC) in Kale OS. This milestone introduces process signal masks, asynchronous signal delivery prioritization, uncatchable signals (`SIGKILL`, `SIGSTOP`), circular-buffer anonymous pipes, EOF propagation, and `SIGPIPE` generation on broken pipes.

## Architecture

```
                       +-----------------------------+
                       |      Signal & IPC Core      |
                       +--------------+--------------+
                                      |
            +-------------------------+-------------------------+
            |                                                   |
            v                                                   v
    [POSIX Signal Engine]                              [Anonymous Pipes]
     (os/kernel/signal.kl)                              (os/kernel/pipe.kl)
   Pending / Blocked Masks                             Circular Buffer Ring
   SIG_DFL / SIG_IGN / Handler                         Read / Write Ends, EPIPE
```

## Phases

### Phase 1: POSIX Signals
- Standard signal definitions:
  - `SIGHUP (1)`: Hangup.
  - `SIGINT (2)`: Terminal interrupt (`^C`).
  - `SIGQUIT (3)`: Terminal quit (`^\`).
  - `SIGILL (4)`: Illegal instruction.
  - `SIGKILL (9)`: Kill (cannot be caught or ignored).
  - `SIGSEGV (11)`: Segmentation violation / page fault.
  - `SIGPIPE (13)`: Broken pipe write.
  - `SIGALRM (14)`: Timer alarm.
  - `SIGTERM (15)`: Software termination signal.
  - `SIGCHLD (17)`: Child status changed.
  - `SIGCONT (18)`: Continue execution.
  - `SIGSTOP (19)`: Stop execution (cannot be caught or ignored).
- Dispositions:
  - `SIG_DFL (0)`: Default action (terminate process, ignore for SIGCHLD/SIGCONT).
  - `SIG_IGN (1)`: Ignore signal.
  - User Handler address.

### Phase 2: Signal State & Delivery Resolution
- `SignalState`:
  - `pending_mask`: Bitmask of pending unhandled signals.
  - `blocked_mask`: Bitmask of blocked signals (`sigprocmask`).
  - `dispositions[32]`: Signal handlers.
- `sig_send(state, signum)`: Sets bit `1 << signum` in pending mask.
- `sig_next_deliverable(state)`: Finds highest-priority unblocked signal `pending & (~blocked)`.
  - Special handling: `SIGKILL` and `SIGSTOP` can NEVER be blocked or ignored.

### Phase 3: Anonymous Pipes
- `PipeBuffer`:
  - Fixed-size circular ring buffer (e.g. 256 bytes).
  - `head`: Write index.
  - `tail`: Read index.
  - `bytes_count`: Current occupied bytes.
  - `readers_count`: Number of open read file descriptors.
  - `writers_count`: Number of open write file descriptors.
- Pipe operations:
  - `pipe_write()`: Copies user bytes into ring buffer. If `readers_count == 0`, returns -1 and generates `SIGPIPE` / `EPIPE`.
  - `pipe_read()`: Reads bytes from ring buffer. If buffer is empty and `writers_count == 0`, returns 0 (EOF).
  - `pipe_close_read()` / `pipe_close_write()`: Updates descriptor reference counts.
