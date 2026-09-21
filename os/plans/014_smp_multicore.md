# Milestone 14: SMP (Symmetric Multiprocessing) & Multi-Core Architecture

## Overview
Implement Symmetric Multiprocessing (SMP) and multi-core CPU architecture for Kale OS. This milestone establishes the Local APIC (LAPIC) register interface, constructs Inter-Processor Interrupt (IPI) commands, implements the dual Startup IPI (SIPI) protocol to awaken Application Processors (APs), maintains per-CPU state structures, and provides fair ticket spinlocks for multi-core synchronization.

## Architecture

```
                      +--------------------------+
                      |       SMP Manager        |
                      |   (os/kernel/smp.kl)     |
                      +-------------+------------+
                                    |
          +-------------------------+-------------------------+
          |                         |                         |
          v                         v                         v
   [Local APIC (LAPIC)]      [IPI Protocol]           [Ticket Spinlocks]
    MMIO 0xFEE00000           INIT -> SIPI -> SIPI    Fair FIFO Locking
    ICR / SVR / Timer         AP Trampoline Handoff   Per-CPU Runqueues
```

## Phases

### Phase 1: Local APIC (LAPIC) Interface
- MMIO Base Address: `0xFEE00000`.
- Registers:
  - `LAPIC_REG_ID` (`0x0020`): Local APIC ID.
  - `LAPIC_REG_VERSION` (`0x0030`): Version register.
  - `LAPIC_REG_TPR` (`0x0080`): Task Priority Register.
  - `LAPIC_REG_EOI` (`0x00B0`): End Of Interrupt.
  - `LAPIC_REG_SVR` (`0x00F0`): Spurious Interrupt Vector (bit 8: APIC Software Enable, bits 7..0: vector `0xFF`).
  - `LAPIC_REG_ICR_LOW` (`0x0300`): Interrupt Command Register (low 32 bits).
  - `LAPIC_REG_ICR_HIGH` (`0x0310`): Interrupt Command Register (high 32 bits, target APIC ID).
  - `LAPIC_REG_LVT_TIMER` (`0x0320`): Timer Local Vector Table.
  - `LAPIC_REG_TICR` (`0x0380`): Timer Initial Count Register.

### Phase 2: Inter-Processor Interrupts (IPI) & SIPI Sequence
- ICR command construction:
  - Delivery Modes:
    - Fixed = `0x0`
    - Lowest Priority = `0x1`
    - SMI = `0x2`
    - NMI = `0x4`
    - INIT = `0x5`
    - Startup (SIPI) = `0x6`
  - Destination Shorthand: None = `0x0`, Self = `0x1`, All Including Self = `0x2`, All Excluding Self = `0x3`.
  - Trigger Mode: Edge = `0x0`, Level = `0x1`.
  - Level: De-assert = `0x0`, Assert = `0x1`.
- Dual SIPI Sequence for waking APs:
  1. Send INIT IPI to target APIC ID: `delivery_mode = INIT (5), level = ASSERT (1), trigger = LEVEL (1)`.
  2. Delay 10 milliseconds.
  3. Send SIPI with trampoline page vector (e.g. vector `0x08` for page `0x8000`).
  4. Delay 200 microseconds.
  5. Send second SIPI if target core has not yet set online flag.

### Phase 3: Per-CPU Topology & Core States
- `CPUCoreState`:
  - `CORE_STATE_OFFLINE = 0`
  - `CORE_STATE_BOOTING = 1`
  - `CORE_STATE_ONLINE  = 2`
  - `CORE_STATE_HALTED  = 3`
- `CPUCore`: `cpu_id`, `lapic_id`, `state`, `stack_base`, `stack_top`, `current_task_id`, `ticks`.
- `SMPManager`: Up to 16 cores, active core count, bootstrap processor (BSP) ID.

### Phase 4: Ticket Spinlock Synchronization
- Avoid starvation and cache thrashing with ticket-based FIFO spinlocks:
  - `Spinlock`: `next_ticket` (serving sequence), `now_serving` (current lock holder).
  - `spinlock_acquire()`: atomically increment `next_ticket`, spin while `now_serving != my_ticket`.
  - `spinlock_release()`: increment `now_serving`.
