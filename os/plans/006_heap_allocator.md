# Milestone 6: Heap Allocator

## Overview
Implement a robust heap allocator for both kernel and user space dynamic memory allocation. This includes a fast allocator algorithm, memory fragmentation management, and proper integration with the VMM.

## Current State
- PMM (Physical Memory Manager) for page-level allocation
- No heap allocator for dynamic memory
- User space programs have no malloc/free
- Kernel has no dynamic memory allocation

## Objectives
1. Implement kernel heap allocator
2. Implement user space heap allocator
3. Add memory fragmentation management
4. Implement memory debugging tools
5. Add performance monitoring
6. Integrate with VMM for large allocations

## Technical Implementation

### Phase 1: Kernel Heap Allocator (Week 1-2)

**File: `os/kernel/heap.kl` (new)**
```kale
// Memory Block Header
struct BlockHeader {
    size: uint64,
    is_free: bool,
    prev: *BlockHeader,
    next: *BlockHeader,
}

// Heap Structure
struct Heap {
    start: uint64,
    end: uint64,
    max_size: uint64,
    used: uint64,
    free_list: *BlockHeader,
}

let kernel_heap: Heap;

fn heap_init(start: uint64, size: uint64) -> Heap {
    let heap: Heap;
    heap.start = start;
    heap.end = start + size;
    heap.max_size = size;
    heap.used = 0;
    
    // Create initial free block
    let initial_block: *BlockHeader = start as *BlockHeader;
    initial_block.size = size - sizeof(BlockHeader);
    initial_block.is_free = true;
    initial_block.prev = null;
    initial_block.next = null;
    
    heap.free_list = initial_block;
    
    return heap;
}

fn heap_alloc(heap: *Heap, size: uint64) -> *uint8 {
    // Align size to 8 bytes
    let aligned_size: uint64 = (size + 7) & ~7;
    
    // Find suitable free block (first-fit)
    let block: *BlockHeader = heap.free_list;
    while block != null {
        if block.is_free && block.size >= aligned_size {
            break;
        }
        block = block.next;
    }
    
    if block == null {
        // No suitable block found
        return null;
    }
    
    // Check if block should be split
    let remaining_size: uint64 = block.size - aligned_size - sizeof(BlockHeader);
    if remaining_size >= 16 { // Minimum block size
        // Split block
        let new_block: *BlockHeader = (block as *uint8 + sizeof(BlockHeader) + aligned_size) as *BlockHeader;
        new_block.size = remaining_size;
        new_block.is_free = true;
        new_block.prev = block;
        new_block.next = block.next;
        
        if block.next != null {
            block.next.prev = new_block;
        }
        
        block.next = new_block;
        block.size = aligned_size;
    }
    
    // Mark block as used
    block.is_free = false;
    heap.used = heap.used + block.size + sizeof(BlockHeader);
    
    // Return pointer after header
    return (block as *uint8 + sizeof(BlockHeader)) as *uint8;
}

fn heap_free(heap: *Heap, ptr: *uint8) -> void {
    if ptr == null {
        return;
    }
    
    let block: *BlockHeader = (ptr - sizeof(BlockHeader)) as *BlockHeader;
    
    // Mark block as free
    block.is_free = true;
    heap.used = heap.used - block.size - sizeof(BlockHeader);
    
    // Try to merge with next block
    if block.next != null && block.next.is_free {
        block.size = block.size + block.next.size + sizeof(BlockHeader);
        block.next = block.next.next;
        if block.next != null {
            block.next.prev = block;
        }
    }
    
    // Try to merge with previous block
    if block.prev != null && block.prev.is_free {
        block.prev.size = block.prev.size + block.size + sizeof(BlockHeader);
        block.prev.next = block.next;
        if block.next != null {
            block.next.prev = block.prev;
        }
    }
}
```

**Tasks:**
- Implement basic first-fit allocator
- Add block splitting logic
- Add block coalescing logic
- Add alignment handling
- Initialize kernel heap in boot

### Phase 2: Advanced Allocator Features (Week 2-3)

**File: `os/kernel/heap.kl`**
```kale
// Enhanced allocator with multiple free lists for different sizes
struct SizeClass {
    size: uint64,
    free_list: *BlockHeader,
}

struct AdvancedHeap {
    base: Heap,
    size_classes: [SizeClass; 8], // For sizes: 16, 32, 64, 128, 256, 512, 1024, 2048
    large_free_list: *BlockHeader, // For allocations > 2048
}

fn advanced_heap_init(start: uint64, size: uint64) -> AdvancedHeap {
    let heap: AdvancedHeap;
    heap.base = heap_init(start, size);
    
    // Initialize size classes
    heap.size_classes[0].size = 16;
    heap.size_classes[1].size = 32;
    heap.size_classes[2].size = 64;
    heap.size_classes[3].size = 128;
    heap.size_classes[4].size = 256;
    heap.size_classes[5].size = 512;
    heap.size_classes[6].size = 1024;
    heap.size_classes[7].size = 2048;
    
    let i: int32 = 0;
    while i < 8 {
        heap.size_classes[i].free_list = null;
        i = i + 1;
    }
    
    heap.large_free_list = heap.base.free_list;
    
    return heap;
}

fn advanced_heap_alloc(heap: *AdvancedHeap, size: uint64) -> *uint8 {
    let aligned_size: uint64 = (size + 7) & ~7;
    
    // Check size classes first
    if aligned_size <= 2048 {
        let class_idx: int32 = 0;
        while class_idx < 8 {
            if heap.size_classes[class_idx].size >= aligned_size {
                break;
            }
            class_idx = class_idx + 1;
        }
        
        // Try to allocate from size class
        let block: *BlockHeader = heap.size_classes[class_idx].free_list;
        if block != null {
            // Remove from free list
            heap.size_classes[class_idx].free_list = block.next;
            block.is_free = false;
            return (block as *uint8 + sizeof(BlockHeader)) as *uint8;
        }
    }
    
    // Fall back to large allocator
    return heap_alloc(&heap.base, size);
}

fn advanced_heap_free(heap: *AdvancedHeap, ptr: *uint8) -> void {
    let block: *BlockHeader = (ptr - sizeof(BlockHeader)) as *BlockHeader;
    let block_size: uint64 = block.size;
    
    block.is_free = true;
    
    // Add to appropriate size class
    if block_size <= 2048 {
        let class_idx: int32 = 0;
        while class_idx < 8 {
            if heap.size_classes[class_idx].size >= block_size {
                break;
            }
            class_idx = class_idx + 1;
        }
        
        block.next = heap.size_classes[class_idx].free_list;
        heap.size_classes[class_idx].free_list = block;
    } else {
        // Add to large free list
        block.next = heap.large_free_list;
        heap.large_free_list = block;
    }
}
```

**Tasks:**
- Implement size-class allocator
- Add segregated free lists
- Implement fast allocation for small sizes
- Add allocation statistics
- Optimize for common allocation patterns

### Phase 3: User Space Heap (Week 3-4)

**File: `os/userspace/libc/heap.kl` (new)**
```kale
// User space heap implementation
struct UserHeap {
    heap_start: uint64,
    heap_end: uint64,
    current_break: uint64,
    max_break: uint64,
}

let user_heap: UserHeap;

fn user_heap_init() -> void {
    user_heap.heap_start = syscall(12, 0, 0, 0); // brk(0)
    user_heap.heap_end = user_heap.heap_start + 0x1000000; // 16MB initial
    user_heap.current_break = user_heap.heap_start;
    user_heap.max_break = 0x00007FFFFFFFFFFF; // User space limit
}

fn user_sbrk(increment: int64) -> uint64 {
    let old_break: uint64 = user_heap.current_break;
    let new_break: uint64 = old_break + (increment as uint64);
    
    if new_break > user_heap.max_break {
        return 0; // Failure
    }
    
    let result: uint64 = syscall(12, new_break, 0, 0); // brk(new_break)
    if result == new_break {
        user_heap.current_break = new_break;
        return old_break;
    } else {
        return 0; // Failure
    }
}

fn user_malloc(size: uint64) -> *uint8 {
    // Simple implementation using sbrk
    let aligned_size: uint64 = (size + 7) & ~7;
    let ptr: uint64 = user_sbrk((aligned_size + 16) as int64);
    
    if ptr == 0 {
        return null;
    }
    
    // Store size before block
    *(ptr as *uint64) = aligned_size;
    
    return (ptr + 16) as *uint8;
}

fn user_free(ptr: *uint8) -> void {
    // Simple implementation - doesn't actually free memory
    // TODO: Implement proper free with coalescing
}

fn user_realloc(ptr: *uint8, size: uint64) -> *uint8 {
    if ptr == null {
        return user_malloc(size);
    }
    
    let old_size: uint64 = *((ptr - 16) as *uint64);
    if size <= old_size {
        return ptr; // Shrink - just return same pointer
    }
    
    // Grow - allocate new and copy
    let new_ptr: *uint8 = user_malloc(size);
    if new_ptr == null {
        return null;
    }
    
    let i: uint64 = 0;
    while i < old_size {
        new_ptr[i] = ptr[i];
        i = i + 1;
    }
    
    user_free(ptr);
    return new_ptr;
}
```

**Tasks:**
- Implement user space heap using brk syscall
- Add malloc/free/realloc functions
- Implement simple allocation strategy
- Add memory alignment
- Handle allocation failures

### Phase 4: Memory Debugging (Week 4)

**File: `os/kernel/heap_debug.kl` (new)**
```kale
struct AllocationInfo {
    ptr: uint64,
    size: uint64,
    allocator: uint64, // IP address of allocator
    timestamp: uint64,
}

let allocation_log: [AllocationInfo; 1024];
let allocation_log_index: uint64 = 0;

fn heap_alloc_debug(heap: *Heap, size: uint64, allocator_ip: uint64) -> *uint8 {
    let ptr: *uint8 = heap_alloc(heap, size);
    
    if ptr != null && allocation_log_index < 1024 {
        allocation_log[allocation_log_index].ptr = ptr as uint64;
        allocation_log[allocation_log_index].size = size;
        allocation_log[allocation_log_index].allocator = allocator_ip;
        allocation_log[allocation_log_index].timestamp = get_system_ticks();
        allocation_log_index = allocation_log_index + 1;
    }
    
    return ptr;
}

fn heap_free_debug(heap: *Heap, ptr: *uint8, free_ip: uint64) -> void {
    // Log the free
    if allocation_log_index < 1024 {
        allocation_log[allocation_log_index].ptr = ptr as uint64;
        allocation_log[allocation_log_index].size = 0; // 0 indicates free
        allocation_log[allocation_log_index].allocator = free_ip;
        allocation_log[allocation_log_index].timestamp = get_system_ticks();
        allocation_log_index = allocation_log_index + 1;
    }
    
    heap_free(heap, ptr);
}

fn heap_check_leaks() -> void {
    serial_write_string("Allocation log:\n");
    
    let i: uint64 = 0;
    while i < allocation_log_index {
        if allocation_log[i].size != 0 {
            serial_write_string("Leak: ptr=0x");
            serial_write_hex(allocation_log[i].ptr);
            serial_write_string(", size=");
            serial_write_dec(allocation_log[i].size);
            serial_write_string(", allocated at 0x");
            serial_write_hex(allocation_log[i].allocator);
            serial_write_string("\n");
        }
        i = i + 1;
    }
}

fn heap_detect_corruption(heap: *Heap) -> bool {
    let block: *BlockHeader = heap.start as *BlockHeader;
    
    while block as uint64 < heap.end {
        // Check for invalid pointers
        if block.prev != null && (block.prev as uint64 < heap.start || block.prev as uint64 >= heap.end) {
            serial_write_string("Corruption: invalid prev pointer\n");
            return true;
        }
        
        if block.next != null && (block.next as uint64 < heap.start || block.next as uint64 >= heap.end) {
            serial_write_string("Corruption: invalid next pointer\n");
            return true;
        }
        
        // Check for double-free
        if block.is_free && block.next != null && block.next.is_free {
            serial_write_string("Corruption: adjacent free blocks\n");
            return true;
        }
        
        block = block.next;
    }
    
    return false;
}
```

**Tasks:**
- Add allocation tracking
- Implement leak detection
- Add corruption detection
- Add allocation statistics
- Add debugging interfaces

### Phase 5: Performance Monitoring (Week 4-5)

**File: `os/kernel/heap.kl`**
```kale
struct HeapStats {
    total_allocations: uint64,
    total_frees: uint64,
    current_allocations: uint64,
    total_allocated: uint64,
    total_freed: uint64,
    peak_usage: uint64,
    fragmentation_ratio: uint64,
}

let heap_stats: HeapStats;

fn heap_get_stats(heap: *Heap) -> HeapStats {
    let stats: HeapStats;
    stats.total_allocations = heap_stats.total_allocations;
    stats.total_frees = heap_stats.total_frees;
    stats.current_allocations = heap_stats.total_allocations - heap_stats.total_frees;
    stats.total_allocated = heap_stats.total_allocated;
    stats.total_freed = heap_stats.total_freed;
    stats.peak_usage = heap_stats.peak_usage;
    
    // Calculate fragmentation
    let free_blocks: uint64 = 0;
    let free_space: uint64 = 0;
    let block: *BlockHeader = heap.free_list;
    
    while block != null {
        free_blocks = free_blocks + 1;
        free_space = free_space + block.size;
        block = block.next;
    }
    
    if free_space > 0 {
        stats.fragmentation_ratio = (free_blocks * 100) / (free_space / 64);
    } else {
        stats.fragmentation_ratio = 0;
    }
    
    return stats;
}

fn heap_print_stats(heap: *Heap) -> void {
    let stats: HeapStats = heap_get_stats(heap);
    
    serial_write_string("Heap Statistics:\n");
    serial_write_string("  Total allocations: ");
    serial_write_dec(stats.total_allocations);
    serial_write_string("\n");
    serial_write_string("  Total frees: ");
    serial_write_dec(stats.total_frees);
    serial_write_string("\n");
    serial_write_string("  Current allocations: ");
    serial_write_dec(stats.current_allocations);
    serial_write_string("\n");
    serial_write_string("  Total allocated: ");
    serial_write_dec(stats.total_allocated);
    serial_write_string("\n");
    serial_write_string("  Total freed: ");
    serial_write_dec(stats.total_freed);
    serial_write_string("\n");
    serial_write_string("  Peak usage: ");
    serial_write_dec(stats.peak_usage);
    serial_write_string("\n");
    serial_write_string("  Fragmentation: ");
    serial_write_dec(stats.fragmentation_ratio);
    serial_write_string("%\n");
}
```

**Tasks:**
- Add allocation statistics
- Track peak usage
- Calculate fragmentation ratio
- Add statistics reporting
- Add performance counters

### Phase 6: VMM Integration (Week 5)

**File: `os/kernel/heap.kl`**
```kale
fn heap_alloc_large(heap: *Heap, size: uint64) -> *uint8 {
    // For large allocations (> 1MB), use VMM directly
    if size > 0x100000 {
        let pages: uint64 = (size + 4095) / 4096;
        let virt_addr: uint64 = find_free_virtual_region(pages);
        
        let i: uint64 = 0;
        while i < pages {
            let phys: uint64 = pmm_alloc_frame(&pmm);
            if phys == 0 {
                // Cleanup on failure
                heap_free_large(virt_addr, i * 4096);
                return null;
            }
            
            vmm_map_page(&vmm, virt_addr + (i * 4096), phys, 0x7);
            i = i + 1;
        }
        
        return virt_addr as *uint8;
    }
    
    // Use regular heap for smaller allocations
    return heap_alloc(heap, size);
}

fn heap_free_large(ptr: *uint8, size: uint64) -> void {
    if size > 0x100000 {
        let pages: uint64 = (size + 4095) / 4096;
        let virt_addr: uint64 = ptr as uint64;
        
        let i: uint64 = 0;
        while i < pages {
            let phys: uint64 = vmm_get_phys_addr(&vmm, virt_addr + (i * 4096));
            vmm_unmap_page(&vmm, virt_addr + (i * 4096));
            pmm_free_frame(&pmm, phys);
            i = i + 1;
        }
    } else {
        heap_free(&kernel_heap, ptr);
    }
}
```

**Tasks:**
- Add large allocation handling
- Integrate with VMM for big allocations
- Add memory pressure handling
- Add allocation limits
- Handle allocation failures gracefully

### Phase 7: Kernel Integration (Week 5-6)

**File: `os/kernel/main.kl` (extend)**
```kale
fn kmain(info: *KernelInfo) -> int32 {
    // Initialize serial
    let serial: SerialPort = serial_init(0x3F8);
    
    // Initialize PMM
    let pmm: PMM = pmm_init(&pmm_bitmap, total_memory);
    
    // Initialize VMM
    let vmm: VMM = vmm_init();
    
    // Initialize kernel heap (16MB initially)
    let heap_start: uint64 = 0xFFFFFFFF80000000;
    let heap_size: uint64 = 0x1000000;
    kernel_heap = heap_init(heap_start, heap_size);
    
    // Load GDT
    gdt_load(&gdt_table);
    
    // Load IDT
    idt_load(&idt_table.pointer);
    
    // Initialize PIT
    let pit: PITDriver = pit_init(1000);
    
    // Initialize scheduler
    let scheduler: Scheduler = scheduler_init();
    
    // Enable interrupts
    enable_interrupts();
    
    // Continue with kernel initialization
    return 0;
}
```

**Tasks:**
- Integrate heap initialization into boot
- Set up kernel heap in proper memory region
- Test heap operations
- Add heap to memory map
- Document heap layout

## Testing Strategy

### Unit Tests
1. Basic allocation/deallocation
2. Block splitting/coalescing
3. Size class allocation
4. Alignment handling
5. Large allocation handling

### Integration Tests
1. Kernel heap operations under load
2. User space heap operations
3. Memory pressure handling
4. Fragmentation management
5. VMM integration

### Manual Tests
1. Allocate many small blocks
2. Allocate few large blocks
3. Mixed allocation patterns
4. Free operations
5. Leak detection

## Dependencies
- VMM (Milestone 1) - for large allocations
- PMM (already implemented) - for physical memory
- System Call Interface (Milestone 4) - for user space heap

## Success Criteria
- ✅ Kernel heap works correctly
- ✅ User space heap works via syscalls
- ✅ Memory fragmentation is manageable
- ✅ Performance is acceptable
- ✅ Leak detection works
- ✅ Corruption detection works
- ✅ Large allocations use VMM
- ✅ No memory leaks in kernel

## Next Steps
After Heap Allocator completion:
1. Implement Filesystem (Milestone 7)
2. Implement Enhanced I/O (Milestone 8)
3. Implement Graphics System (Milestone 9)

## Notes
- Consider implementing multiple allocation strategies
- Add memory pool support for fixed-size allocations
- Consider adding garbage collection for specific use cases
- Profile allocator performance regularly
- Keep allocator algorithms simple initially
