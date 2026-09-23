# Milestone 35: System Settings & Hardware Telemetry Subsystem

## Overview
Implement an in-kernel system settings registry and hardware performance telemetry engine in pure Kale. This subsystem manages persistent configuration keys for desktop display, theme, mouse, audio, and networking, while sampling real-time CPU, RAM, and uptime metrics for desktop panels and GUI task managers.

## Key Capabilities
1. **System Settings Registry**:
   - Typed Key-Value store with fast string-indexed lookups.
   - Types: `SETTING_TYPE_INT`, `SETTING_TYPE_BOOL`, `SETTING_TYPE_STRING`.
   - Settings keys:
     - Display: `display.width`, `display.height`, `display.scale`
     - Appearance: `theme.dark_mode`, `theme.accent`
     - Input: `mouse.sensitivity`, `mouse.cursor_size`
     - Sound: `sound.master_volume`, `sound.muted`
     - Network: `net.hostname`, `net.dhcp`
2. **Hardware & Kernel Telemetry**:
   - CPU load estimation across kernel scheduling ticks.
   - Memory utilization accounting (RAM total, used, free, percentage).
   - System uptime formatting (days, hours, minutes, seconds).
   - Process count and active thread metrics.
3. **Telemetry Snapshot for GUI Task Monitors**:
   - Single-call telemetry snapshot structure `SystemTelemetry` consumed by desktop panels and process monitors.
