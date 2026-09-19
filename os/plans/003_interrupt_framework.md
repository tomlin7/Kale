# Milestone 3: Complete Interrupt Framework

## Overview
Implement a complete Interrupt Service Routine (ISR) framework including timer, keyboard, page fault, syscall, and other critical interrupt handlers. This provides the foundation for preemptive multitasking, user space communication, and hardware interaction.

## Current State
- Basic IDT structure defined in Kale
- Basic GDT structure defined in Kale
- PIC remapping implemented in Kale
- Serial port driver implemented
- VGA display driver implemented
- No ISRs beyond basic stubs
- No interrupt handling framework

## Objectives
1. Implement complete ISR framework with assembly stubs
2. Implement timer interrupt handler (IRQ0)
3. Implement keyboard interrupt handler (IRQ1)
4. Implement page fault handler (exception 14)
5. Implement system call handler (software interrupt)
6. Implement other critical exception handlers
7. Implement interrupt nesting and priority handling

## Technical Implementation

### Phase 1: ISR Framework Assembly Stubs (Week 1)

**File: `os/kernel/isr.asm` (new)**
```assembly
; ISR Entry/Exit Macros
%macro ISR_NOERRCODE 1
global isr%1
isr%1:
    push 0          ; Dummy error code
    push %1         ; Interrupt number
    jmp isr_common_stub
%endmacro

%macro ISR_ERRCODE 1
global isr%1
isr%1:
    push %1         ; Interrupt number
    jmp isr_common_stub
%endmacro

%macro IRQ 2
global irq%1
irq%1:
    push %1         ; Interrupt number
    jmp irq_common_stub
%endmacro

; Common ISR Handler
isr_common_stub:
    ; Save all registers
    push rax
    push rbx
    push rcx
    push rdx
    push rsi
    push rdi
    push rbp
    push r8
    push r9
    push r10
    push r11
    push r12
    push r13
    push r14
    push r15
    
    ; Save data segment
    mov ax, ds
    push ax
    
    ; Load kernel data segment
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    
    ; Call C handler
    mov rdi, rsp    ; Pass interrupt frame pointer
    call isr_handler
    
    ; Restore data segment
    pop ax
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    
    ; Restore registers
    pop r15
    pop r14
    pop r13
    pop r12
    pop r11
    pop r10
    pop r9
    pop r8
    pop rbp
    pop rdi
    pop rsi
    pop rdx
    pop rcx
    pop rbx
    pop rax
    
    ; Clean up error code and interrupt number
    add rsp, 16
    
    iretq

; Common IRQ Handler
irq_common_stub:
    ; Save all registers (same as ISR)
    push rax
    push rbx
    push rcx
    push rdx
    push rsi
    push rdi
    push rbp
    push r8
    push r9
    push r10
    push r11
    push r12
    push r13
    push r14
    push r15
    
    mov ax, ds
    push ax
    
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    
    ; Call IRQ handler
    mov rdi, rsp
    call irq_handler
    
    pop ax
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    
    pop r15
    pop r14
    pop r13
    pop r12
    pop r11
    pop r10
    pop r9
    pop r8
    pop rbp
    pop rdi
    pop rsi
    pop rdx
    pop rcx
    pop rbx
    pop rax
    
    add rsp, 16
    
    iretq

; Generate all ISRs
ISR_NOERRCODE 0    ; Division by zero
ISR_NOERRCODE 1    ; Debug
ISR_NOERRCODE 2    ; Non-maskable interrupt
ISR_NOERRCODE 3    ; Breakpoint
ISR_NOERRCODE 4    ; Overflow
ISR_NOERRCODE 5    ; Bound range exceeded
ISR_NOERRCODE 6    ; Invalid opcode
ISR_NOERRCODE 7    ; Device not available
ISR_ERRCODE   8    ; Double fault
ISR_NOERRCODE 9    ; Coprocessor segment overrun
ISR_ERRCODE   10   ; Invalid TSS
ISR_ERRCODE   11   ; Segment not present
ISR_ERRCODE   12   ; Stack-segment fault
ISR_ERRCODE   13   ; General protection fault
ISR_ERRCODE   14   ; Page fault
ISR_NOERRCODE 15   ; Reserved
ISR_NOERRCODE 16   ; x87 FPU error
ISR_ERRCODE   17   ; Alignment check
ISR_NOERRCODE 18   ; Machine check
ISR_NOERRCODE 19   ; SIMD floating-point
ISR_NOERRCODE 20   ; Virtualization
ISR_NOERRCODE 21   ; Reserved
ISR_NOERRCODE 22   ; Reserved
ISR_NOERRCODE 23   ; Reserved
ISR_NOERRCODE 24   ; Reserved
ISR_NOERRCODE 25   ; Reserved
ISR_NOERRCODE 26   ; Reserved
ISR_NOERRCODE 27   ; Reserved
ISR_NOERRCODE 28   ; Reserved
ISR_NOERRCODE 29   ; Reserved
ISR_NOERRCODE 30   ; Reserved
ISR_NOERRCODE 31   ; Reserved

; Generate all IRQs
IRQ 0, 32   ; Timer
IRQ 1, 33   ; Keyboard
IRQ 2, 34   ; Cascade (never called)
IRQ 3, 35   ; COM2
IRQ 4, 36   ; COM1
IRQ 5, 37   ; LPT2
IRQ 6, 38   ; Floppy
IRQ 7, 39   ; LPT1
IRQ 8, 40   ; CMOS RTC
IRQ 9, 41   ; Free for peripherals
IRQ 10, 42  ; Free for peripherals
IRQ 11, 43  ; Free for peripherals
IRQ 12, 44  ; PS/2 Mouse
IRQ 13, 45  ; FPU
IRQ 14, 46  ; Primary ATA
IRQ 15, 47  ; Secondary ATA
```

**Tasks:**
- Create ISR assembly file with stubs
- Implement common ISR entry/exit handling
- Generate all 32 exception handlers
- Generate all 16 IRQ handlers
- Implement proper register saving/restoration
- Add interrupt frame structure

### Phase 2: Interrupt Frame Structure (Week 1-2)

**File: `os/kernel/idt.kl` (extend)**
```kale
// Interrupt Frame (pushed by CPU + ISR stub)
struct InterruptFrame {
    rax: uint64,
    rbx: uint64,
    rcx: uint64,
    rdx: uint64,
    rsi: uint64,
    rdi: uint64,
    rbp: uint64,
    r8: uint64,
    r9: uint64,
    r10: uint64,
    r11: uint64,
    r12: uint64,
    r13: uint64,
    r14: uint64,
    r15: uint64,
    ds: uint64,
    interrupt_number: uint64,
    error_code: uint64,
    rip: uint64,
    cs: uint64,
    rflags: uint64,
    rsp: uint64,
    ss: uint64,
}
```

**Tasks:**
- Define interrupt frame structure
- Match assembly stack layout
- Add frame access functions
- Document each field's purpose

### Phase 3: ISR Handler Dispatch (Week 2)

**File: `os/kernel/isr.kl` (new)**
```kale
// ISR Handler Function Pointer
type ISRHandler = fn(frame: *InterruptFrame) -> void;

// ISR Table
struct ISRTable {
    handlers: [ISRHandler; 256],
}

fn isr_init(table: *ISRTable) -> void {
    let i: int32 = 0;
    while i < 256 {
        table.handlers[i] = default_isr_handler;
        i = i + 1;
    }
}

fn isr_register_handler(table: *ISRTable, vector: uint8, handler: ISRHandler) -> void {
    table.handlers[vector] = handler;
}

fn default_isr_handler(frame: *InterruptFrame) -> void {
    let vector: uint8 = frame.interrupt_number as uint8;
    
    // Print error message
    serial_write_string("Unhandled interrupt: ");
    serial_write_hex(vector);
    serial_write_string("\n");
    
    // Halt on unhandled exception
    if vector < 32 {
        cli();
        hlt();
    }
}

extern fn isr_handler(frame: *InterruptFrame) -> void {
    let vector: uint8 = frame.interrupt_number as uint8;
    isr_table.handlers[vector](frame);
}
```

**Tasks:**
- Implement ISR handler dispatch in Kale
- Create ISR handler table
- Implement handler registration
- Implement default handler for unhandled interrupts
- Add assembly-to-Kale interface

### Phase 4: Timer Interrupt Handler (Week 2-3)

**File: `os/kernel/timer.kl` (new)**
```kale
fn timer_isr(frame: *InterruptFrame) -> void {
    // Acknowledge PIC
    pic_send_eoi(0);
    
    // Update system time
    system_ticks = system_ticks + 1;
    
    // Call scheduler (if enabled)
    if scheduler_enabled {
        schedule();
    }
}

fn timer_init(vector: uint8) -> void {
    // Register handler
    isr_register_handler(&isr_table, vector, timer_isr);
    
    // Initialize PIT
    pit_init(1000); // 1000Hz
}
```

**Tasks:**
- Implement timer interrupt handler
- Acknowledge PIC properly
- Update system tick counter
- Integrate with scheduler
- Add system time functions

### Phase 5: Keyboard Interrupt Handler (Week 3)

**File: `os/kernel/keyboard.kl` (extend from existing)**
```kale
struct KeyboardBuffer {
    buffer: [uint8; 256],
    head: uint32,
    tail: uint32,
    count: uint32,
}

let kbd_buffer: KeyboardBuffer;

fn keyboard_isr(frame: *InterruptFrame) -> void {
    // Read scancode
    let scancode: uint8 = inb(0x60);
    
    // Process scancode
    let ascii: uint8 = kbd_scancode_to_ascii(scancode & 0x7F, shift_pressed);
    
    // If key press (not release)
    if (scancode & 0x80) == 0 {
        // Add to buffer if not full
        if kbd_buffer.count < 256 {
            kbd_buffer.buffer[kbd_buffer.head] = ascii;
            kbd_buffer.head = (kbd_buffer.head + 1) % 256;
            kbd_buffer.count = kbd_buffer.count + 1;
        }
    }
    
    // Acknowledge PIC
    pic_send_eoi(1);
}

fn keyboard_read_char() -> uint8 {
    while kbd_buffer.count == 0 {
        halt(); // Wait for interrupt
    }
    
    let c: uint8 = kbd_buffer.buffer[kbd_buffer.tail];
    kbd_buffer.tail = (kbd_buffer.tail + 1) % 256;
    kbd_buffer.count = kbd_buffer.count - 1;
    
    return c;
}

fn keyboard_init(vector: uint8) -> void {
    // Clear buffer
    kbd_buffer.head = 0;
    kbd_buffer.tail = 0;
    kbd_buffer.count = 0;
    
    // Register handler
    isr_register_handler(&isr_table, vector, keyboard_isr);
}
```

**Tasks:**
- Implement keyboard interrupt handler
- Add keyboard buffer for interrupt-driven input
- Implement buffer read function
- Replace polling with interrupt-driven approach
- Test keyboard input under interrupts

### Phase 6: Page Fault Handler (Week 3-4)

**File: `os/kernel/vmm.kl` (extend)**
```kale
fn page_fault_isr(frame: *InterruptFrame) -> void {
    let fault_addr: uint64 = get_cr2();
    let error_code: uint32 = frame.error_code as uint32;
    
    serial_write_string("Page fault at 0x");
    serial_write_hex(fault_addr);
    serial_write_string(", error: ");
    serial_write_hex(error_code);
    serial_write_string("\n");
    
    // Parse error code
    let present: bool = (error_code & 0x1) == 0;
    let write: bool = (error_code & 0x2) != 0;
    let user: bool = (error_code & 0x4) != 0;
    let reserved: bool = (error_code & 0x8) != 0;
    let instruction_fetch: bool = (error_code & 0x10) != 0;
    
    // Handle copy-on-write
    if present && write {
        if vmm_handle_cow_fault(fault_addr) {
            return; // Handled successfully
        }
    }
    
    // Handle demand paging
    if !present {
        if vmm_handle_demand_paging(fault_addr) {
            return; // Handled successfully
        }
    }
    
    // Unhandled page fault - kill process or panic
    if user {
        // User page fault - kill current process
        serial_write_string("User page fault - killing process\n");
        terminate_process(scheduler.current_process, -1);
    } else {
        // Kernel page fault - panic
        serial_write_string("Kernel page fault - system panic\n");
        kernel_panic();
    }
}

fn page_fault_init(vector: uint8) -> void {
    isr_register_handler(&isr_table, vector, page_fault_isr);
}
```

**Tasks:**
- Implement page fault interrupt handler
- Parse page fault error code
- Handle copy-on-write faults
- Handle demand paging
- Kill process on user page faults
- Panic on kernel page faults

### Phase 7: System Call Handler (Week 4)

**File: `os/kernel/syscall.kl` (new)**
```kale
// System Call Numbers
enum SyscallNumber {
    SYS_READ = 0,
    SYS_WRITE = 1,
    SYS_OPEN = 2,
    SYS_CLOSE = 3,
    SYS_EXIT = 60,
    SYS_GETPID = 39,
}

fn syscall_isr(frame: *InterruptFrame) -> void {
    let syscall_num: uint64 = frame.rax;
    let result: uint64 = 0;
    
    switch syscall_num {
        case SYS_READ:
            result = sys_read(frame.rdi, frame.rsi, frame.rdx);
        case SYS_WRITE:
            result = sys_write(frame.rdi, frame.rsi, frame.rdx);
        case SYS_OPEN:
            result = sys_open(frame.rdi, frame.rsi, frame.rdx);
        case SYS_CLOSE:
            result = sys_close(frame.rdi);
        case SYS_EXIT:
            sys_exit(frame.rdi);
            return; // Does not return
        case SYS_GETPID:
            result = scheduler.current_process.id as uint64;
        default:
            serial_write_string("Unknown syscall: ");
            serial_write_hex(syscall_num);
            result = -1 as uint64;
    }
    
    // Return result in RAX
    frame.rax = result;
}

fn syscall_init(vector: uint8) -> void {
    isr_register_handler(&isr_table, vector, syscall_isr);
}

// Make syscall from user space
fn syscall(num: uint64, arg1: uint64, arg2: uint64, arg3: uint64) -> uint64 {
    let result: uint64;
    asm {
        "mov rax, %0"
        "mov rdi, %1"
        "mov rsi, %2"
        "mov rdx, %3"
        "int %4"
        "mov %5, rax"
        : "=r"(result)
        : "r"(num), "r"(arg1), "r"(arg2), "r"(arg3), "r"(vector)
        : "rax", "rdi", "rsi", "rdx"
    };
    return result;
}
```

**Tasks:**
- Implement system call interrupt handler
- Define system call numbers
- Implement basic syscalls (read, write, exit, getpid)
- Add syscall instruction interface
- Test system calls from kernel space

### Phase 8: Other Exception Handlers (Week 4-5)

**File: `os/kernel/exceptions.kl` (new)**
```kale
fn divide_error_isr(frame: *InterruptFrame) -> void {
    serial_write_string("Division by zero\n");
    kernel_panic();
}

fn debug_isr(frame: *InterruptFrame) -> void {
    serial_write_string("Debug exception\n");
    // Continue execution
}

fn breakpoint_isr(frame: *InterruptFrame) -> void {
    serial_write_string("Breakpoint hit\n");
    // Continue execution
}

fn general_protection_fault_isr(frame: *InterruptFrame) -> void {
    serial_write_string("General protection fault, error: ");
    serial_write_hex(frame.error_code);
    serial_write_string("\n");
    kernel_panic();
}

fn double_fault_isr(frame: *InterruptFrame) -> void {
    serial_write_string("Double fault - critical error\n");
    kernel_panic();
}
```

**Tasks:**
- Implement divide error handler
- Implement debug exception handler
- Implement breakpoint handler
- Implement general protection fault handler
- Implement double fault handler
- Add handlers for other exceptions

### Phase 9: IDT Setup (Week 5)

**File: `os/kernel/idt.kl` (extend)**
```kale
fn idt_setup_interrupts() -> void {
    // Initialize ISR table
    isr_init(&isr_table);
    
    // Set exception handlers (vectors 0-31)
    isr_register_handler(&isr_table, 0, divide_error_isr);
    isr_register_handler(&isr_table, 1, debug_isr);
    isr_register_handler(&isr_table, 3, breakpoint_isr);
    isr_register_handler(&isr_table, 8, double_fault_isr);
    isr_register_handler(&isr_table, 13, general_protection_fault_isr);
    isr_register_handler(&isr_table, 14, page_fault_isr);
    
    // Set IRQ handlers (vectors 32-47)
    isr_register_handler(&isr_table, 32, timer_isr);
    isr_register_handler(&isr_table, 33, keyboard_isr);
    
    // Set syscall handler (vector 0x80)
    isr_register_handler(&isr_table, 0x80, syscall_isr);
    
    // Update IDT entries with assembly stub addresses
    idt_set_gate(&idt_table, 0, isr0, 0x08, 0x8E);
    idt_set_gate(&idt_table, 1, isr1, 0x08, 0x8E);
    // ... set all gates
    
    // Load IDT
    idt_load(&idt_table.pointer);
}
```

**Tasks:**
- Set up all exception handlers
- Set up all IRQ handlers
- Set up system call handler
- Update IDT entries with correct addresses
- Load IDT and test interrupts

### Phase 10: Interrupt Priority and Nesting (Week 5-6)

**File: `os/kernel/isr.kl` (extend)**
```kale
struct InterruptState {
    depth: uint32,
    current_vector: uint8,
}

let interrupt_state: InterruptState;

fn interrupt_enter(vector: uint8) -> void {
    interrupt_state.depth = interrupt_state.depth + 1;
    interrupt_state.current_vector = vector;
    
    // Enable higher priority interrupts if needed
    if interrupt_state.depth == 1 {
        // First level - enable all
        enable_interrupts();
    }
}

fn interrupt_exit() -> void {
    interrupt_state.depth = interrupt_state.depth - 1;
    
    if interrupt_state.depth == 0 {
        interrupt_state.current_vector = 0;
    }
}
```

**Tasks:**
- Implement interrupt nesting support
- Handle interrupt priority
- Prevent stack overflow from nested interrupts
- Add interrupt statistics

## Testing Strategy

### Unit Tests
1. ISR stub register saving/restoration
2. Interrupt frame structure integrity
3. Handler dispatch correctness
4. Timer frequency accuracy
5. Keyboard buffer behavior

### Integration Tests
1. All exceptions trigger correct handlers
2. Timer interrupts cause scheduling
3. Keyboard interrupts fill buffer correctly
4. Page faults are handled appropriately
5. System calls execute correctly

### Manual Tests
1. Cause each exception intentionally
2. Test timer-driven multitasking
3. Test keyboard input under load
4. Test page fault handling
5. Test system call interface

## Dependencies
- Task Scheduler (Milestone 2) - for timer-driven scheduling
- VMM (Milestone 1) - for page fault handling
- GDT/IDT structures - already defined
- PIC driver - already implemented

## Success Criteria
- ✅ All 32 exceptions have handlers
- ✅ All 16 IRQs have handlers
- ✅ Timer interrupts drive scheduling
- ✅ Keyboard input is interrupt-driven
- ✅ Page faults are handled correctly
- ✅ System calls work correctly
- ✅ No crashes during interrupt handling
- ✅ Interrupt nesting works properly

## Next Steps
After ISR Framework completion:
1. Implement System Call Interface (Milestone 4)
2. Implement User Space Support (Milestone 5)
3. Implement Heap Allocator (Milestone 6)

## Notes
- Use QEMU's `-d int,cpu_reset` for debugging interrupts
- Document interrupt vector assignments
- Consider adding interrupt masking for critical sections
- Test with interrupt flood conditions
- Keep interrupt handlers minimal and fast
