# Systems Utilities & Telemetry (`sys/`) Plan

## 1. Overview
The `sys/` project houses high-performance systems engineering tools, telemetry daemons, and diagnostics written in Kale. It runs atop host operating systems (Windows NT and POSIX) using direct system calls and zero-dependency socket abstractions.

---

## 2. Directory Layout & Subsystems

```
sys/
├── sysmon/          # Real-time TUI process monitor, CPU core sparklines, memory breakdown
│   ├── main.kl      # Interactive CLI entry point and event loop
│   ├── telemetry.kl # CPU usage sampling, RAM statistics, thread count discovery
│   ├── tui.kl       # ANSI TrueColor virtual terminal dashboard renderer
│   ├── PLAN.md      # sysmon architecture roadmap
│   └── agents.md    # Agent instructions for sysmon
├── dig/             # Packet-crafted DNS query tool and diagnostic resolver
│   ├── main.kl      # DNS CLI client and human-readable answer formatter
│   ├── packet.kl    # Raw wire-format DNS header and question encoder/decoder
│   ├── resolver.kl  # UDP/TCP DNS socket client with timeout and retries
│   ├── PLAN.md      # dig architecture roadmap
│   └── agents.md    # Agent instructions for dig
└── PLAN.md          # Systems utilities roadmap
```

---

## 3. Mission & Capabilities
1. **Real-time Telemetry (`sys/sysmon`)**:
   - Zero-allocation 60 Hz polling loops using Windows NT Toolhelp32 snapshots and Win32 queries.
   - Per-core CPU load sparklines, memory gauge visualizers, and responsive ANSI terminal UI.
2. **DNS Diagnostics (`sys/dig`)**:
   - Native wire-level DNS query construction without third-party C resolver libraries.
   - Comprehensive record resolution (A, AAAA, MX, CNAME, TXT, NS, SOA) directly over raw sockets.

---

## 4. Bare-Metal OS Migration
The standalone bare-metal x86_64 operating system, bootloader, microkernel, and hardware drivers have been relocated to the dedicated top-level project `os/`.
