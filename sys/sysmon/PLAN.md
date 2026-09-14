# sys/sysmon Architecture Plan

## 1. Overview
A low-overhead, high-refresh terminal monitor delivering real-time insight into operating system resource utilization.

## 2. Core Modules
- `telemetry.kl`: CPU load sampling, memory status, thread counts.
- `proc.kl`: Process list snapshotting, parent-child PID resolution.
- `tui.kl`: ANSI/VT100 double-buffered terminal layout, gauge drawing, sparklines.
- `main.kl`: Main interactive loop, keyboard navigation (up/down/kill/filter).
