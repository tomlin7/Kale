# sys/sysmon — Terminal & Process Monitor

## Version
`0.1.0`

## Description
Interactive TUI system monitor written in Kale. Provides per-core CPU utilization, memory allocation gauges, thread inspection, and process tree traversal without spawning child subprocesses.

## Status
🟡 In Progress

## Dependencies
- `packages/std`: core, collections, fs, sys
- `libs/term`: virtual terminal emulation and VT100 control sequences

## Build Instructions
```bash
kale build sys/sysmon/main.kl -o bin/sysmon.exe
./bin/sysmon.exe
```

## Conventions
- Zero allocations inside the 60Hz telemetry polling loop.
- Direct Windows Toolhelp32 / NT query system calls for instant metrics.
