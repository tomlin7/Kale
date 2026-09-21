# Milestone 30: Kernel Crash Recovery, Panic & Core Dump Subsystem

## Overview
Implement the Kernel Panic, Stack Unwinding, and Crash Core Dump architecture for Kale OS. Captures CPU register state (general purpose, RIP, RFLAGS, and CR0/CR2/CR3/CR4), walks stack frame pointer chains (`RBP`) to generate backtraces, serializes structured core dump headers, and renders emergency diagnostic crash displays.

## Technical Architecture
1. **Crash Register Context (`PanicContext`)**:
   - General-purpose 64-bit registers: `rax`, `rbx`, `rcx`, `rdx`, `rsi`, `rdi`, `rbp`, `rsp`, `r8`..`r15`.
   - Instruction pointer (`rip`), segment selectors (`cs`, `ss`), CPU flags (`rflags`).
   - Paging & control registers: `cr0`, `cr2` (page fault linear address), `cr3` (PML4 base), `cr4`.
   - Error code and interrupt vector number (e.g. 14 for Page Fault, 13 for General Protection Fault).
2. **Stack Frame Pointer Unwinding**:
   - Standard x86_64 System V ABI frame layout:
     - `*(rbp) = previous_rbp`
     - `*(rbp + 8) = return_rip`
   - Iterates up to 16 call frames, verifying kernel stack bounds (`0xFFFF800000000000` or heap ranges).
   - Records array of return addresses `backtrace[16]`.
3. **Core Dump Serialization Header (`CoreDumpHeader`)**:
   - Magic: `0x4B414C4550414E43` (`"KALEPANC"`).
   - Architecture: `0x8664` (x86_64).
   - Timestamp epoch, panic message string, and frame count.
4. **Emergency Crash Display Protocol**:
   - Disables local interrupts (`cli`) and broadcasts halt IPI to secondary SMP CPU cores.
   - Clears linear framebuffer with emergency red/navy banner and displays formatted register dump.

## Deliverables
- `os/plans/030_kernel_panic_dump.md`: Architectural specification.
- `os/kernel/panic.kl`: Pure Kale panic state capture, stack frame unwinder, and core dump header serializer.
- `tests/test_os_kernel_panic.py`: Test suite validating context initialization, frame pointer backtrace extraction, stack bound safety, and core dump serialization.
