# Milestone 1: Virtual Memory Manager (VMM)

## Overview
Implement a complete Virtual Memory Manager (VMM) with 4-level paging, page allocation, address translation, and proper kernel-user memory isolation. This is the foundation for all subsequent OS features including multitasking, user space, and process isolation.

## Current State
- Basic identity paging setup in bootloader (single 2MB page)
- Physical Memory Manager (PMM) with bitmap allocator implemented in Kale
- GDT structures defined in Kale but not loaded
- No virtual memory management beyond initial identity mapping

## Objectives
1. Complete 4-level paging implementation (PML4, PDPT, PD, PT)
2. Implement page table allocation and management
3. Implement virtual address mapping and unmapping
4. Implement page fault handling
5. Establish kernel/user memory separation
6. Implement copy-on-write mechanism

## Technical Implementation

### Phase 1: Page Table Structures (Week 1-2)

**File: `os/kernel/vmm.kl`**
```kale
// Page Table Entry (64-bit)
struct PageTableEntry {
    present: bool,
    writable: bool,
    user_accessible: bool,
    page_write_through: bool,
    page_cache_disable: bool,
    accessed: bool,
    dirty: bool,
    global: bool,
    available: uint8,
    frame: uint64,
    no_execute: bool,
}

// Page Table
struct PageTable {
    entries: [PageTableEntry; 512],
}

// Virtual Memory Manager
struct VMM {
    pml4: *PageTable,
    kernel_heap_start: uint64,
    kernel_heap_end: uint64,
    user_heap_start: uint64,
    user_heap_end: uint64,
}
```

**Tasks:**
- Define PageTableEntry structure with all x86_64 flags
- Implement page table entry manipulation functions
- Implement PML4, PDPT, PD, PT structure definitions
- Add bit-field accessors for page table entries

### Phase 2: Page Table Allocation (Week 2-3)

**Functions to implement:**
```kale
fn vmm_init() -> VMM
fn vmm_alloc_page_table() -> *PageTable
fn vmm_free_page_table(table: *PageTable) -> void
fn vmm_get_or_create_table(entry: *PageTableEntry) -> *PageTable
```

**Implementation details:**
- Use PMM to allocate physical frames for page tables
- Map page tables themselves into kernel address space
- Implement recursive mapping for easier page table access
- Handle page table allocation failures gracefully

### Phase 3: Virtual Address Mapping (Week 3-4)

**Functions to implement:**
```kale
fn vmm_map_page(vmm: *VMM, virt_addr: uint64, phys_addr: uint64, flags: uint64) -> bool
fn vmm_unmap_page(vmm: *VMM, virt_addr: uint64) -> void
fn vmm_get_phys_addr(vmm: *VMM, virt_addr: uint64) -> uint64
fn vmm_map_range(vmm: *VMM, virt_start: uint64, phys_start: uint64, pages: uint64, flags: uint64) -> bool
```

**Implementation details:**
- Walk 4-level page table hierarchy
- Create missing page tables on demand
- Handle large pages (2MB/1GB) for efficiency
- Implement proper cache control (PAT if available)
- Map kernel space to higher half (canonical addresses)

### Phase 4: Memory Layout (Week 4)

**Memory Map Definition:**
```kale
// Kernel Space (Higher Half, starting at 0xFFFF800000000000)
const KERNEL_PML4_INDEX: uint64 = 511;
const KERNEL_CODE_BASE: uint64 = 0xFFFFFFFF80000000;
const KERNEL_HEAP_BASE: uint64 = 0xFFFFFFFF80000000;
const KERNEL_HEAP_SIZE: uint64 = 0x10000000; // 256MB

// User Space (Lower Half, 0x0000000000000000 - 0x00007FFFFFFFFFFF)
const USER_STACK_BASE: uint64 = 0x00007FFFFFFFFFFF;
const USER_STACK_SIZE: uint64 = 0x100000; // 1MB
const USER_HEAP_BASE: uint64 = 0x0000000000400000;
const USER_HEAP_MAX: uint64 = 0x00007FFFFFFFFFFF;
```

**Tasks:**
- Define kernel and user space memory regions
- Map kernel code, data, and heap regions
- Set up proper permissions (kernel pages non-user-accessible)
- Implement address space switching functions

### Phase 5: Page Fault Handler (Week 5)

**File: `os/kernel/idt.kl` (extend)**
```kale
fn page_fault_handler(frame: *InterruptFrame) -> void {
    let fault_addr: uint64 = get_cr2();
    let error_code: uint64 = frame.error_code;
    
    // Check if fault was caused by:
    // - Page not present
    // - Access violation (write to read-only, user access to kernel page)
    // - Reserved bit set
    // - Instruction fetch from NX page
    
    // Handle copy-on-write pages
    // Handle demand paging
    // Kill process on access violation
}
```

**Tasks:**
- Implement page fault ISR in assembly stub
- Add page fault handler to IDT
- Implement CR2 register reading to get fault address
- Parse error code bits to determine fault cause
- Implement copy-on-write page handling
- Add basic demand paging support

### Phase 6: Copy-on-Write (Week 6)

**Functions to implement:**
```kale
fn vmm_fork_address_space(src_vmm: *VMM) -> VMM
fn vmm_handle_cow_fault(vmm: *VMM, fault_addr: uint64) -> void
fn vmm_mark_page_cow(entry: *PageTableEntry) -> void
```

**Implementation details:**
- Implement reference counting for shared pages
- On fork, mark pages as read-only and shared
- On write fault, allocate new page and copy content
- Update page table entries appropriately
- Handle atomic operations for reference counting

### Phase 7: Kernel Integration (Week 7)

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
    
    // Load IDT with page fault handler
    idt_load(&idt_table);
    
    // Enable interrupts
    enable_interrupts();
    
    // Continue with kernel initialization
    return 0;
}
```

**Tasks:**
- Integrate VMM initialization into kernel boot sequence
- Properly order initialization (PMM before VMM)
- Test virtual memory operations
- Verify kernel space protection
- Add debug output for memory operations

## Testing Strategy

### Unit Tests
1. Page table entry bit manipulation
2. Page table allocation/deallocation
3. Virtual address mapping/unmapping
4. Address translation accuracy
5. Page table walking logic

### Integration Tests
1. Boot with new VMM system
2. Map and access kernel memory regions
3. Test page fault handling with invalid accesses
4. Test copy-on-write mechanism
5. Memory stress testing

### Manual Tests
1. QEMU boot and basic operation
2. Test memory protection violations
3. Verify memory layout matches design
4. Test memory allocation under load

## Dependencies
- PMM (Physical Memory Manager) - already implemented
- GDT (Global Descriptor Table) - structures defined, needs loading
- IDT (Interrupt Descriptor Table) - needs page fault handler integration
- Assembly support for page fault ISR stub

## Success Criteria
- ✅ System boots with 4-level paging
- ✅ Kernel space properly mapped to higher half
- ✅ User space accessible but protected
- ✅ Page faults handled correctly
- ✅ Copy-on-write mechanism functional
- ✅ Memory isolation between kernel and user space
- ✅ All existing functionality still works

## Next Steps
After VMM completion:
1. Implement Task Scheduler (Milestone 2)
2. Implement Timer Driver (Milestone 3)
3. Implement System Call Interface (Milestone 4)

## Notes
- Use QEMU's `-trace` functionality for debugging paging issues
- Consider adding page table flushing functions for TLB management
- Document memory layout decisions for future reference
- Keep assembly stubs minimal and push logic to Kale
