# Systems Diagnostics & Telemetry (`sys/`) Plan

The `sys/` tree contains host operating-system diagnostics and networking utilities. Bare-metal boot and kernel work lives in the top-level `os/` project.

## Directory Layout

```
sys/
├── sysmon/          # CPU, memory, process, and disk telemetry
└── dig/             # Packet-level DNS diagnostics
```

## Roadmap

- [ ] Add cross-platform process sampling backends.
- [ ] Add structured telemetry export for dashboards.
- [ ] Expand `dig` with DNSSEC and TCP fallback.
