# Milestone 26: High Precision Event Timer (HPET) & Timekeeping Subsystem

## Overview
Implement the High Precision Event Timer (HPET) memory-mapped driver and nanosecond-resolution timekeeping architecture for Kale OS. HPET replaces legacy 8254 PIT polling with a 64-bit wide free-running counter operating at $\ge 10\text{ MHz}$, delivering jitter-free sub-microsecond timestamps and supporting POSIX monotonic clocks.

## Technical Architecture
1. **ACPI HPET Table Description**:
   - Signature: `"HPET"` (4 bytes).
   - Event Timer Block ID (`event_timer_block_id`): Bit 13 specifies 64-bit counter support; bits 12:8 specify comparator count.
   - Base Address: 64-bit physical MMIO base address (typically `0xFED00000`).
2. **HPET MMIO Register Map**:
   - `0x000` (`GCAP_ID`): General Capabilities & ID.
     - Bits 63:32: `COUNTER_CLK_PERIOD` (femtoseconds per tick, $10^{-15}\text{ s}$).
     - Bits 31:16: PCI Vendor ID.
     - Bit 13: 64-bit counter capable (`COUNT_SIZE_CAP`).
     - Bits 12:8: Number of comparators (`NUM_TIM_CAP` = $N - 1$).
   - `0x010` (`GEN_CONF`): General Configuration.
     - Bit 0: `ENABLE_CNF` (Overall counter enable).
     - Bit 1: `LEG_RT_CNF` (Legacy replacement routing for IRQ0 / IRQ8).
   - `0x020` (`GINTR_STA`): General Interrupt Status.
   - `0x0F0` (`MAIN_CNT`): 64-bit main up-counter.
   - `0x100 + 0x20 * N` (`Tn_CONF`): Timer $N$ Configuration (Interrupt Enable, Periodic capability, 64-bit mode, IRQ routing).
   - `0x108 + 0x20 * N` (`Tn_COMP`): Timer $N$ Comparator value.
3. **Nanosecond Timekeeping & Conversion**:
   - Clock tick period conversion:
     - $\text{ticks\_to\_nanoseconds}(\Delta\text{ticks}) = \frac{\Delta\text{ticks} \times \text{period\_fs}}{1,000,000}$.
     - $\text{ticks\_to\_microseconds}(\Delta\text{ticks}) = \frac{\Delta\text{ticks} \times \text{period\_fs}}{1,000,000,000}$.
   - Monotonic time tracking (`Timespec { sec, nsec }`).
   - One-shot and periodic comparator alarm programming.

## Deliverables
- `os/plans/026_hpet_timer.md`: Specification plan.
- `os/drivers/hpet.kl`: Pure Kale HPET driver with MMIO register layout, capability decoding, and nanosecond math.
- `tests/test_os_hpet_timer.py`: Test suite validating capabilities parsing, tick period decoding, frequency calculation, nanosecond conversion, and comparator programming.
