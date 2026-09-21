# Milestone 20: Pseudo-Terminal (PTY) & Termios Line Discipline

## Overview
Implement the Pseudo-Terminal (PTY) device pairs and POSIX Termios line discipline engine for Kale OS. This milestone establishes master/slave terminal device endpoints (`/dev/ptmx`, `/dev/pts/N`), bidirectional packet bridging between graphical terminal emulators and user shells, canonical line buffering with backspace and kill editing, input carriage return translation, output newline expansion, and terminal control character signal dispatch (`^C` -> `SIGINT`, `^\` -> `SIGQUIT`).

## Architecture

```
        [GUI Terminal Window]  <--- Master PTY --->  [Line Discipline]  <--- Slave PTY --->  [Kale Shell]
        (Draws characters,                          (ECHO, ICANON,                            (Receives lines,
         Sends keystrokes)                           ONLCR, Signals)                           Executes cmds)
```

## Phases

### Phase 1: Master/Slave PTY Device Pair
- `PTYPair`:
  - `master_fd`, `slave_fd`.
  - `master_rx_buf` / `slave_rx_buf` circular ring buffers.
  - `is_open_master`, `is_open_slave`.
  - `termios` configuration struct.

### Phase 2: POSIX Termios Flags
- Input flags (`c_iflag`):
  - `IGNBRK (0x0001)`: Ignore break condition.
  - `BRKINT (0x0002)`: Map break to SIGINT.
  - `ICRNL  (0x0100)`: Map CR (`\r`) to NL (`\n`) on input.
  - `IXON   (0x0400)`: Enable XON/XOFF output flow control.
- Output flags (`c_oflag`):
  - `OPOST  (0x0001)`: Enable post-processing of output.
  - `ONLCR  (0x0004)`: Map NL (`\n`) to CR-NL (`\r\n`) on output.
- Local flags (`c_lflag`):
  - `ISIG   (0x0001)`: Enable signals (`^C` -> SIGINT, `^\` -> SIGQUIT).
  - `ICANON (0x0002)`: Enable canonical mode (line-by-line input with line editing).
  - `ECHO   (0x0008)`: Echo input characters back to terminal.
  - `ECHOE  (0x0010)`: Visual erase on backspace.
- Control characters (`c_cc`):
  - `VINTR  (0)`: `0x03` (`^C`)
  - `VQUIT  (1)`: `0x1C` (`^\`)
  - `VERASE (2)`: `0x08` (`\b` or `0x7F`)
  - `VKILL  (3)`: `0x15` (`^U`)
  - `VEOF   (4)`: `0x04` (`^D`)

### Phase 3: Canonical Line Discipline Engine
- Master Input Processing (`pty_master_write_keystroke`):
  - Signal check: If `ISIG` enabled and char is `VINTR`, trigger `SIGINT` (2); if `VQUIT`, trigger `SIGQUIT` (3).
  - Erase check: If `ICANON` and char is `VERASE` (`\b` or `127`), remove last character from line buffer.
  - Kill line check: If `ICANON` and char is `VKILL` (`^U`), clear line buffer.
  - Enter check: If char is `\r` and `ICRNL` set, convert to `\n`. In canonical mode, flush line buffer to slave queue.
  - Echo: If `ECHO` enabled, append typed character to echo output buffer for display rendering.

### Phase 4: Slave Output Processing (`pty_slave_write`)
- If `OPOST` and `ONLCR` enabled:
  - When encountering `\n`, write `\r` followed by `\n` to the master output buffer.
