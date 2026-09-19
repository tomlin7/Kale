# Systems Utilities & Telemetry (`sys/`)

## Version
`0.1.0`

## Description
High-performance systems engineering utilities, telemetry daemons, and diagnostics written in pure Kale (`sysmon`, `dig`).

## Status
Current status: 🟢 Active

## Sub-projects
- `sys/sysmon`: Terminal & process telemetry monitor (ANSI TrueColor, CPU sparklines).
- `sys/dig`: Low-level packet-crafted DNS query tool and diagnostic resolver.

## Dependencies
- `packages/std`: standard library, collections, filesystem
- `libs/term`: virtual terminal emulation and VT100 control sequences
- `libs/net`: networking socket layer

## Build Instructions
```bash
# Build sysmon
kale build sys/sysmon/main.kl -o bin/sysmon.exe

# Build dig
kale build sys/dig/main.kl -o bin/kale_dig.exe -lws2_32
```

## Conventions
- High-frequency loops must minimize heap allocations.
- System metrics sample OS counters directly via Win32 / host APIs.

