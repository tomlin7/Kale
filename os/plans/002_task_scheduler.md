# Milestone 2: Task Scheduler

## Overview
Implement a preemptive task scheduler with round-robin scheduling, process control blocks (PCBs), context switching, and basic process management. This enables multitasking and is essential for user space processes.

## Current State
- No multitasking system
- Single execution flow in kernel
- Basic interrupt handling structure (IDT defined)
- No process management concepts
- No timer driver for preemption

## Objectives
1. Implement Process Control Block (PCB) structure
2. Implement context saving and restoration
3. Implement timer driver (8254 PIT) for preemptive scheduling
4. Implement round-robin scheduler
5. Implement basic process creation and termination
6. Implement idle process and scheduling loop

## Technical Implementation

### Phase 1: Process Control Block (Week 1-2)

**File: `os/kernel/sched.kl`**
```kale
// Process State
enum ProcessState {
    PROCESS_RUNNING,
    PROCESS_READY,
    PROCESS_BLOCKED,
    PROCESS_TERMINATED,
}

// Process Control Block
struct ProcessControlBlock {
    id: uint32,
    state: ProcessState,
    priority: uint8,
    
    // CPU Context
    registers: *CPUContext,
    kernel_stack: uint64,
    user_stack: uint64,
    
    // Memory
    page_table: uint64,  // Physical address of PML4
    
    // Scheduling
    time_slice: uint32,
    time_used: uint32,
    next: *ProcessControlBlock,
    prev: *ProcessControlBlock,
}

// CPU Context (saved on interrupt/switch)
struct CPUContext {
    rax: uint64,
    rbx: uint64,
    rcx: uint64,
    rdx: uint64,
    rsi: uint64,
    rdi: uint64,
    rbp: uint64,
    rsp: uint64,
    r8: uint64,
    r9: uint64,
    r10: uint64,
    r11: uint64,
    r12: uint64,
    r13: uint64,
    r14: uint64,
    r15: uint64,
    rip: uint64,
    rflags: uint64,
    cs: uint64,
    ss: uint64,
}
```

**Tasks:**
- Define ProcessControlBlock structure
- Define CPUContext structure for register saving
- Implement process state management functions
- Create process ID generation system
- Implement PCB initialization functions

### Phase 2: Context Switching (Week 2-3)

**File: `os/kernel/context.asm` (new)**
```assembly
; Context Switch Assembly Stub
global context_switch
extern switch_to_process

context_switch:
    ; Save current context
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
    
    ; Save stack pointer
    mov [current_rsp], rsp
    
    ; Call scheduler to pick next process
    call switch_to_process
    
    ; Restore new context
    mov rsp, [new_rsp]
    
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
    
    iretq
```

**File: `os/kernel/sched.kl`**
```kale
fn switch_to_process(prev: *ProcessControlBlock, next: *ProcessControlBlock) -> void {
    // Save current process state
    prev.registers = get_current_context();
    prev.state = PROCESS_READY;
    
    // Switch to next process
    current_process = next;
    next.state = PROCESS_RUNNING;
    
    // Switch page tables
    load_cr3(next.page_table);
    
    // Restore context
    restore_context(next.registers);
}
```

**Tasks:**
- Implement assembly context save/restore stub
- Implement context switching logic in Kale
- Test context switching between processes
- Handle stack switching correctly
- Implement CR3 (page table) switching

### Phase 3: Timer Driver (Week 3-4)

**File: `os/kernel/pit.kl` (new)**
```kale
// 8254 Programmable Interval Timer
struct PITDriver {
    frequency: uint32,
    channel: uint8,
}

fn pit_init(frequency: uint32) -> PITDriver {
    let divisor: uint32 = 1193182 / frequency; // Base frequency
    
    // Set command byte
    outb(0x43, 0x36); // Channel 0, lobyte/hibyte, mode 3, binary
    
    // Set divisor
    outb(0x40, divisor & 0xFF);
    outb(0x40, (divisor >> 8) & 0xFF);
    
    return PITDriver { frequency: frequency, channel: 0 };
}

fn pit_set_frequency(pit: *PITDriver, frequency: uint32) -> void {
    let divisor: uint32 = 1193182 / frequency;
    outb(0x43, 0x36);
    outb(0x40, divisor & 0xFF);
    outb(0x40, (divisor >> 8) & 0xFF);
    pit.frequency = frequency;
}
```

**File: `os/kernel/idt.kl` (extend)**
```kale
// Timer ISR
fn timer_isr(frame: *InterruptFrame) -> void {
    // Acknowledge PIC
    pic_send_eoi(0);
    
    // Call scheduler
    schedule();
}
```

**Tasks:**
- Implement PIT driver initialization
- Implement frequency setting (1000Hz for 1ms time slices)
- Add timer ISR to IDT (IRQ0 = vector 0x20)
- Implement timer interrupt handler
- Test timer interrupts

### Phase 4: Round-Robin Scheduler (Week 4-5)

**File: `os/kernel/sched.kl`**
```kale
struct Scheduler {
    ready_queue: *ProcessControlBlock,
    current_process: *ProcessControlBlock,
    idle_process: *ProcessControlBlock,
    process_count: uint32,
    next_pid: uint32,
}

fn scheduler_init() -> Scheduler {
    let sched: Scheduler = Scheduler {
        ready_queue: null,
        current_process: null,
        idle_process: null,
        process_count: 0,
        next_pid: 1,
    };
    
    // Create idle process
    sched.idle_process = create_idle_process();
    sched.current_process = sched.idle_process;
    
    return sched;
}

fn schedule() -> void {
    let current: *ProcessControlBlock = scheduler.current_process;
    let next: *ProcessControlBlock;
    
    // Update time used
    current.time_used = current.time_used + 1;
    
    // Check if time slice expired
    if current.time_used >= current.time_slice {
        current.time_used = 0;
        
        // Move to next process in ready queue
        if current.next != null {
            next = current.next;
        } else {
            next = scheduler.ready_queue;
        }
        
        // If no other processes, continue with current
        if next == null {
            next = current;
        }
        
        // Switch context
        if next != current {
            switch_to_process(current, next);
        }
    }
}
```

**Tasks:**
- Implement round-robin scheduling algorithm
- Implement ready queue management
- Implement time slice management
- Handle empty ready queue (idle process)
- Test scheduling with multiple processes

### Phase 5: Process Creation (Week 5-6)

**File: `os/kernel/sched.kl`**
```kale
fn create_process(entry_point: uint64, is_user: bool) -> *ProcessControlBlock {
    let pcb: *ProcessControlBlock = alloc_pcb();
    
    pcb.id = scheduler.next_pid;
    scheduler.next_pid = scheduler.next_pid + 1;
    pcb.state = PROCESS_READY;
    pcb.priority = 0;
    pcb.time_slice = 10; // 10ms default
    pcb.time_used = 0;
    
    // Allocate kernel stack
    pcb.kernel_stack = alloc_kernel_stack();
    
    if is_user {
        // Allocate user stack
        pcb.user_stack = alloc_user_stack();
        
        // Create new address space
        pcb.page_table = create_user_address_space();
    } else {
        // Share kernel address space
        pcb.page_table = get_kernel_pml4();
    }
    
    // Initialize CPU context
    pcb.registers = init_cpu_context(entry_point, pcb.kernel_stack, is_user);
    
    // Add to ready queue
    add_to_ready_queue(pcb);
    scheduler.process_count = scheduler.process_count + 1;
    
    return pcb;
}

fn create_idle_process() -> *ProcessControlBlock {
    let pcb: *ProcessControlBlock = alloc_pcb();
    pcb.id = 0;
    pcb.state = PROCESS_RUNNING;
    pcb.priority = 0;
    pcb.time_slice = 1; // Short time slice for idle
    pcb.kernel_stack = alloc_kernel_stack();
    pcb.page_table = get_kernel_pml4();
    pcb.registers = init_cpu_context(idle_loop, pcb.kernel_stack, false);
    return pcb;
}

fn idle_loop() -> void {
    while true {
        halt(); // Wait for interrupt
    }
}
```

**Tasks:**
- Implement process creation function
- Implement kernel/user stack allocation
- Implement address space creation (using VMM)
- Initialize CPU context for new process
- Implement idle process
- Add process to ready queue

### Phase 6: Process Termination (Week 6-7)

**File: `os/kernel/sched.kl`**
```kale
fn terminate_process(pcb: *ProcessControlBlock, exit_code: int32) -> void {
    pcb.state = PROCESS_TERMINATED;
    pcb.exit_code = exit_code;
    
    // Free resources
    free_kernel_stack(pcb.kernel_stack);
    
    if pcb.page_table != get_kernel_pml4() {
        // Free user address space
        free_address_space(pcb.page_table);
    }
    
    // Remove from ready queue
    remove_from_ready_queue(pcb);
    
    scheduler.process_count = scheduler.process_count - 1;
    
    // Schedule next process
    schedule();
}

fn exit(exit_code: int32) -> void {
    terminate_process(scheduler.current_process, exit_code);
}
```

**Tasks:**
- Implement process termination
- Implement resource cleanup
- Implement ready queue removal
- Handle zombie processes (waitpid in future)
- Test process creation and termination

### Phase 7: Kernel Integration (Week 7-8)

**File: `os/kernel/main.kl` (extend)**
```kale
fn kmain(info: *KernelInfo) -> int32 {
    // Initialize serial
    let serial: SerialPort = serial_init(0x3F8);
    
    // Initialize PMM
    let pmm: PMM = pmm_init(&pmm_bitmap, total_memory);
    
    // Initialize VMM
    let vmm: VMM = vmm_init();
    
    // Load GDT
    gdt_load(&gdt_table);
    
    // Load IDT with timer and page fault handlers
    idt_load(&idt_table);
    
    // Initialize PIT (1000Hz)
    let pit: PITDriver = pit_init(1000);
    
    // Initialize scheduler
    let scheduler: Scheduler = scheduler_init();
    
    // Create kernel processes
    let shell_process: *ProcessControlBlock = create_process(shell_main, false);
    
    // Enable interrupts
    enable_interrupts();
    
    // Enter scheduler loop
    scheduler_loop();
    
    return 0;
}
```

**Tasks:**
- Integrate scheduler into kernel boot sequence
- Initialize timer before enabling interrupts
- Create initial kernel processes
- Test preemptive scheduling
- Verify context switching works correctly

## Testing Strategy

### Unit Tests
1. PCB allocation and initialization
2. Context save/restore accuracy
3. Timer frequency accuracy
4. Round-robin scheduling fairness
5. Process creation/destruction

### Integration Tests
1. Create multiple kernel processes
2. Test preemptive switching between processes
3. Test time slice expiration
4. Test process termination
5. Test idle process behavior

### Manual Tests
1. Boot with scheduler enabled
2. Run multiple processes simultaneously
3. Verify CPU time distribution
4. Test process creation limits
5. Monitor memory usage

## Dependencies
- VMM (Virtual Memory Manager) - needed for address space management
- GDT (Global Descriptor Table) - needs TSS for ring switching
- IDT (Interrupt Descriptor Table) - needs timer ISR
- PMM (Physical Memory Manager) - for stack allocation

## Success Criteria
- ✅ System boots with scheduler enabled
- ✅ Timer interrupts fire at correct frequency
- ✅ Context switching works correctly
- ✅ Multiple processes can run concurrently
- ✅ Round-robin scheduling is fair
- ✅ Process creation and termination work
- ✅ No crashes during context switches
- ✅ Idle process handles empty ready queue

## Next Steps
After Task Scheduler completion:
1. Implement Complete ISR Framework (Milestone 3)
2. Implement System Call Interface (Milestone 4)
3. Implement User Space Support (Milestone 5)

## Notes
- Use QEMU's `-d int` flag to debug interrupt issues
- Consider adding scheduler statistics (CPU time per process)
- Document scheduling policy for future enhancement
- Keep context switch assembly minimal for performance
- Test with different time slice values
