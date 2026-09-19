# Milestone 5: User Space Support

## Overview
Implement complete user space support including ELF loader, user space initialization, ring 3 transitions, user space standard library (Kale libc), and dynamic linking. This milestone enables the OS to run actual user programs in protected user mode.

## Current State
- Basic syscall interface implemented
- No ELF loader
- No user space processes
- No user space standard library
- No dynamic linking support
- Kernel runs in ring 0 only

## Objectives
1. Implement ELF binary loader
2. Implement user space process creation
3. Implement ring 3 transitions
4. Create basic user space standard library
5. Implement dynamic linking support
6. Add user space initialization
7. Test with simple user programs

## Technical Implementation

### Phase 1: ELF Structures and Parsing (Week 1)

**File: `os/kernel/elf.kl` (new)**
```kale
// ELF Identification
struct ElfIdent {
    magic: [uint8; 4],      // 0x7F 'E' 'L' 'F'
    class: uint8,           // 1 = 32-bit, 2 = 64-bit
    endianness: uint8,      // 1 = little endian, 2 = big endian
    version: uint8,         // 1 = original ELF
    os_abi: uint8,          // System V = 0
    abi_version: uint8,
    padding: [uint8; 7],
}

// ELF Header (64-bit)
struct ElfHeader {
    ident: ElfIdent,
    type: uint16,           // 1 = relocatable, 2 = executable, 3 = shared object
    machine: uint16,        // 0x3E = x86_64
    version: uint32,
    entry: uint64,          // Entry point address
    phoff: uint64,          // Program header offset
    shoff: uint64,          // Section header offset
    flags: uint32,
    ehsize: uint16,         // ELF header size
    phentsize: uint16,      // Program header entry size
    phnum: uint16,          // Number of program headers
    shentsize: uint16,      // Section header entry size
    shnum: uint16,          // Number of section headers
    shstrndx: uint16,       // Section header string table index
}

// Program Header (64-bit)
struct ElfProgramHeader {
    type: uint32,           // PT_LOAD = 1, PT_DYNAMIC = 2, PT_INTERP = 3
    flags: uint32,          // PF_X = 0x1, PF_W = 0x2, PF_R = 0x4
    offset: uint64,         // Offset in file
    vaddr: uint64,          // Virtual address
    paddr: uint64,          // Physical address (ignored)
    filesz: uint64,        // Size in file
    memsz: uint64,          // Size in memory
    align: uint64,          // Alignment
}

// Section Header (64-bit)
struct ElfSectionHeader {
    name: uint32,
    type: uint32,
    flags: uint64,
    addr: uint64,
    offset: uint64,
    size: uint64,
    link: uint32,
    info: uint32,
    addralign: uint64,
    entsize: uint64,
}

// ELF Constants
const ELF_MAGIC: [uint8; 4] = [0x7F, 'E', 'L', 'F'];
const ELF_CLASS_64: uint8 = 2;
const ELF_DATA_LITTLE: uint8 = 1;
const ELF_TYPE_EXEC: uint16 = 2;
const ELF_MACHINE_X86_64: uint16 = 0x3E;
const PT_NULL: uint32 = 0;
const PT_LOAD: uint32 = 1;
const PT_DYNAMIC: uint32 = 2;
const PT_INTERP: uint32 = 3;
const PT_NOTE: uint32 = 4;
const PT_PHDR: uint32 = 6;
const PF_X: uint32 = 0x1;
const PF_W: uint32 = 0x2;
const PF_R: uint32 = 0x4;
```

**Tasks:**
- Define ELF structure definitions
- Add ELF parsing functions
- Implement magic number validation
- Add architecture validation
- Document ELF format requirements

### Phase 2: ELF Loader (Week 1-2)

**File: `os/kernel/elf.kl`**
```kale
fn elf_validate_header(header: *ElfHeader) -> bool {
    // Check magic
    if header.ident.magic[0] != 0x7F { return false; }
    if header.ident.magic[1] != 'E' { return false; }
    if header.ident.magic[2] != 'L' { return false; }
    if header.ident.magic[3] != 'F' { return false; }
    
    // Check class (64-bit)
    if header.ident.class != ELF_CLASS_64 { return false; }
    
    // Check endianness (little)
    if header.ident.endianness != ELF_DATA_LITTLE { return false; }
    
    // Check type (executable)
    if header.type != ELF_TYPE_EXEC { return false; }
    
    // Check machine (x86_64)
    if header.machine != ELF_MACHINE_X86_64 { return false; }
    
    return true;
}

fn elf_load_binary(data: *uint8, size: uint64, process: *ProcessControlBlock) -> bool {
    let header: *ElfHeader = data as *ElfHeader;
    
    // Validate header
    if !elf_validate_header(header) {
        serial_write_string("Invalid ELF header\n");
        return false;
    }
    
    // Calculate memory requirements
    let min_vaddr: uint64 = 0xFFFFFFFFFFFFFFFF;
    let max_vaddr: uint64 = 0;
    
    let i: uint16 = 0;
    while i < header.phnum {
        let ph: *ElfProgramHeader = (data as *uint8 + header.phoff + (i as uint64 * header.phentsize as uint64)) as *ElfProgramHeader;
        
        if ph.type == PT_LOAD {
            if ph.vaddr < min_vaddr { min_vaddr = ph.vaddr; }
            if ph.vaddr + ph.memsz > max_vaddr { max_vaddr = ph.vaddr + ph.memsz; }
        }
        
        i = i + 1;
    }
    
    // Allocate address space
    let total_size: uint64 = max_vaddr - min_vaddr;
    let base_addr: uint64 = allocate_user_region(total_size);
    
    // Load program segments
    i = 0;
    while i < header.phnum {
        let ph: *ElfProgramHeader = (data as *uint8 + header.phoff + (i as uint64 * header.phentsize as uint64)) as *ElfProgramHeader;
        
        if ph.type == PT_LOAD {
            // Calculate protection flags
            let vmm_flags: uint64 = 0x1; // Present
            if (ph.flags & PF_W) != 0 { vmm_flags = vmm_flags | 0x2; } // Writable
            if (ph.flags & PF_X) != 0 { vmm_flags = vmm_flags | 0x0; } // Executable (default)
            vmm_flags = vmm_flags | 0x4; // User accessible
            
            // Map pages
            let segment_start: uint64 = ph.vaddr;
            let segment_end: uint64 = ph.vaddr + ph.memsz;
            let page_start: uint64 = segment_start & ~0xFFF;
            let page_end: uint64 = (segment_end + 0xFFF) & ~0xFFF;
            
            let addr: uint64 = page_start;
            while addr < page_end {
                let phys: uint64 = pmm_alloc_frame(&pmm);
                if phys == 0 {
                    serial_write_string("Failed to allocate frame for ELF segment\n");
                    return false;
                }
                
                vmm_map_page(&process.vmm, addr, phys, vmm_flags);
                
                // Copy file data
                let offset_in_segment: uint64 = addr - segment_start;
                if offset_in_segment < ph.filesz {
                    let copy_start: uint64 = offset_in_segment;
                    let copy_end: uint64 = offset_in_segment + 4096;
                    if copy_end > ph.filesz { copy_end = ph.filesz; }
                    
                    let phys_ptr: *uint8 = phys as *uint8;
                    let file_ptr: *uint8 = (data as *uint8 + ph.offset + offset_in_segment);
                    
                    let j: uint64 = 0;
                    while j < (copy_end - copy_start) {
                        phys_ptr[j] = file_ptr[j];
                        j = j + 1;
                    }
                }
                
                addr = addr + 4096;
            }
        }
        
        i = i + 1;
    }
    
    // Set entry point
    process.registers.rip = header.entry;
    
    return true;
}
```

**Tasks:**
- Implement ELF header validation
- Implement program segment loading
- Handle PT_LOAD segments
- Calculate memory requirements
- Set proper page protections
- Handle BSS (zero-initialized data)

### Phase 3: User Space Process Creation (Week 2-3)

**File: `os/kernel/process.kl` (new)**
```kale
fn create_user_process(elf_data: *uint8, elf_size: uint64, args: **char, env: **char) -> *ProcessControlBlock {
    let process: *ProcessControlBlock = alloc_pcb();
    
    process.id = scheduler.next_pid;
    scheduler.next_pid = scheduler.next_pid + 1;
    process.state = PROCESS_READY;
    process.priority = 0;
    process.time_slice = 10;
    process.time_used = 0;
    
    // Create new address space
    process.page_table = create_user_address_space();
    
    // Allocate kernel stack
    process.kernel_stack = alloc_kernel_stack();
    
    // Allocate user stack
    process.user_stack = alloc_user_stack();
    
    // Load ELF binary
    if !elf_load_binary(elf_data, elf_size, process) {
        free_pcb(process);
        return null;
    }
    
    // Setup user stack with arguments and environment
    setup_user_stack(process, args, env);
    
    // Initialize CPU context for user mode entry
    process.registers = init_user_context(header.entry, process.user_stack, process.kernel_stack);
    
    // Add to ready queue
    add_to_ready_queue(process);
    scheduler.process_count = scheduler.process_count + 1;
    
    return process;
}

fn setup_user_stack(process: *ProcessControlBlock, args: **char, env: **char) -> void {
    let stack_top: uint64 = process.user_stack + USER_STACK_SIZE;
    let stack_ptr: uint64 = stack_top;
    
    // Count arguments
    let argc: int32 = 0;
    if args != null {
        while args[argc] != null {
            argc = argc + 1;
        }
    }
    
    // Count environment variables
    let envc: int32 = 0;
    if env != null {
        while env[envc] != null {
            envc = envc + 1;
        }
    }
    
    // Calculate space needed
    let arg_ptrs_size: uint64 = (argc + 1) * 8;
    let env_ptrs_size: uint64 = (envc + 1) * 8;
    let auxv_size: uint64 = 2 * 16; // AT_NULL, AT_ENTRY
    
    // Copy strings
    let string_space: uint64 = 0;
    let i: int32 = 0;
    while i < argc {
        let len: uint64 = string_length(args[i]) + 1;
        string_space = string_space + len;
        i = i + 1;
    }
    
    i = 0;
    while i < envc {
        let len: uint64 = string_length(env[i]) + 1;
        string_space = string_space + len;
        i = i + 1;
    }
    
    // Allocate space on stack
    stack_ptr = stack_ptr - string_space;
    let string_base: uint64 = stack_ptr;
    
    // Copy argument strings
    let arg_strings: [*char; 256];
    i = 0;
    let current_string: uint64 = string_base;
    while i < argc {
        let len: uint64 = string_length(args[i]) + 1;
        copy_string(current_string as *char, args[i], len);
        arg_strings[i] = current_string as *char;
        current_string = current_string + len;
        i = i + 1;
    }
    arg_strings[argc] = null;
    
    // Copy environment strings
    let env_strings: [*char; 256];
    i = 0;
    while i < envc {
        let len: uint64 = string_length(env[i]) + 1;
        copy_string(current_string as *char, env[i], len);
        env_strings[i] = current_string as *char;
        current_string = current_string + len;
        i = i + 1;
    }
    env_strings[envc] = null;
    
    // Set up pointer arrays
    stack_ptr = stack_ptr - env_ptrs_size;
    let env_ptr: **char = stack_ptr as **char;
    i = 0;
    while i < envc {
        env_ptr[i] = env_strings[i];
        i = i + 1;
    }
    env_ptr[envc] = null;
    
    stack_ptr = stack_ptr - arg_ptrs_size;
    let arg_ptr: **char = stack_ptr as **char;
    i = 0;
    while i < argc {
        arg_ptr[i] = arg_strings[i];
        i = i + 1;
    }
    arg_ptr[argc] = null;
    
    // Set up aux vector
    stack_ptr = stack_ptr - auxv_size;
    let auxv: [uint64; 4] = [0, 0, 0, 0];
    auxv[0] = 9; // AT_ENTRY
    auxv[1] = process.registers.rip;
    auxv[2] = 0; // AT_NULL
    auxv[3] = 0;
    
    copy_memory(stack_ptr as *uint8, auxv as *uint8, auxv_size);
    
    // Set up final stack layout
    stack_ptr = stack_ptr - 8;
    *(stack_ptr as *uint64) = env_ptr as uint64;
    
    stack_ptr = stack_ptr - 8;
    *(stack_ptr as *uint64) = arg_ptr as uint64;
    
    stack_ptr = stack_ptr - 8;
    *(stack_ptr as *uint64) = argc as uint64;
    
    process.user_stack_pointer = stack_ptr;
}
```

**Tasks:**
- Implement user process creation
- Handle argument and environment setup
- Setup user stack correctly
- Initialize user mode context
- Handle ELF loading failures

### Phase 4: Ring 3 Transitions (Week 3)

**File: `os/kernel/context.asm` (extend)**
```assembly
; Initialize User Mode Context
global init_user_context
extern init_user_context_kl

init_user_context:
    ; RDI = entry point
    ; RSI = user stack
    ; RDX = kernel stack
    
    ; Save kernel stack pointer
    mov [kernel_stack_ptr], rdx
    
    ; Set up user stack
    mov rax, rsi
    sub rax, 8          ; Space for return address
    mov qword [rax], 0  ; Return address (null)
    
    ; Set up iretq frame
    sub rax, 8          ; RSP
    mov qword [rax], rsi
    
    sub rax, 8          ; SS (user data selector)
    mov qword [rax], 0x23
    
    sub rax, 8          ; RFLAGS
    pushfq
    pop rbx
    mov qword [rax], rbx
    
    sub rax, 8          ; CS (user code selector)
    mov qword [rax], 0x1B
    
    sub rax, 8          // RIP
    mov qword [rax], rdi
    
    ; Return with context structure
    mov rdi, rax
    call init_user_context_kl
    ret

; Switch to User Mode
global switch_to_user_mode
extern switch_to_user_mode_kl

switch_to_user_mode:
    ; RDI = context pointer
    
    ; Restore user stack
    mov rsp, rdi
    
    ; Switch to user data selector
    mov ax, 0x23
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    
    ; Execute iretq to switch to user mode
    iretq
```

**File: `os/kernel/context.kl`**
```kale
struct UserContext {
    user_rsp: uint64,
    user_ss: uint64,
    user_rflags: uint64,
    user_cs: uint64,
    user_rip: uint64,
}

fn init_user_context(entry: uint64, user_stack: uint64, kernel_stack: uint64) -> UserContext {
    let ctx: UserContext;
    
    ctx.user_rip = entry;
    ctx.user_cs = 0x1B;  // User code selector (ring 3)
    ctx.user_rflags = 0x202; // Interrupt enable
    ctx.user_rsp = user_stack;
    ctx.user_ss = 0x23;  // User data selector (ring 3)
    
    return ctx;
}

fn switch_to_user_mode(ctx: *UserContext) -> void {
    // This function doesn't return - switches to user mode
    asm {
        "mov rsp, %0"
        "mov ax, 0x23"
        "mov ds, ax"
        "mov es, ax"
        "mov fs, ax"
        "mov gs, ax"
        "iretq"
        : 
        : "r"(ctx)
        : "rax", "rsp"
    };
}
```

**Tasks:**
- Implement user mode context initialization
- Add GDT entries for user code/data segments
- Implement ring 3 transition
- Handle return from user space
- Test user mode transitions

### Phase 5: GDT User Mode Entries (Week 3-4)

**File: `os/kernel/gdt.kl` (extend)**
```kale
fn gdt_setup_user_entries(table: *GDTTable) -> void {
    // 0x18: User 64-bit Code Segment (Ring 3)
    // Access: 0xFA = 250 (Present, DPL=3, Code, Readable, Accessed)
    // Granularity: 0x20 = 32 (Long Mode)
    table.user_code = gdt_create_entry(0, 1048575, 250, 32);
    
    // 0x20: User 64-bit Data Segment (Ring 3)
    // Access: 0xF2 = 242 (Present, DPL=3, Data, Writable, Accessed)
    // Granularity: 0
    table.user_data = gdt_create_entry(0, 1048575, 242, 0);
    
    // Update GDT pointer
    table.pointer.limit = 39; // 5 * 8 - 1
    table.pointer.base = 0;
}

// Selector values
const USER_CODE_SELECTOR: uint16 = 0x18;
const USER_DATA_SELECTOR: uint16 = 0x20;
```

**Tasks:**
- Add user mode GDT entries
- Set proper DPL (Descriptor Privilege Level)
- Update GDT loading
- Test segment transitions
- Document selector values

### Phase 6: Basic User Space Standard Library (Week 4-5)

**File: `os/userspace/libc/stdio.kl` (new)**
```kale
// Minimal Standard Library for User Space

// System call numbers
const SYS_WRITE: uint64 = 1;
const SYS_READ: uint64 = 0;
const SYS_EXIT: uint64 = 60;
const SYS_GETPID: uint64 = 39;

// System call interface
fn syscall(num: uint64, arg1: uint64, arg2: uint64, arg3: uint64) -> uint64 {
    let result: uint64;
    asm {
        "mov rax, %0"
        "mov rdi, %1"
        "mov rsi, %2"
        "mov rdx, %3"
        "syscall"
        "mov %4, rax"
        : "=r"(result)
        : "r"(num), "r"(arg1), "r"(arg2), "r"(arg3), "r"(result)
        : "rax", "rdi", "rsi", "rdx"
    };
    return result;
}

// File descriptors
const STDIN_FILENO: int32 = 0;
const STDOUT_FILENO: int32 = 1;
const STDERR_FILENO: int32 = 2;

// Basic I/O functions
fn write(fd: int32, buf: *uint8, count: uint64) -> int64 {
    return syscall(SYS_WRITE, fd as uint64, buf as uint64, count) as int64;
}

fn read(fd: int32, buf: *uint8, count: uint64) -> int64 {
    return syscall(SYS_READ, fd as uint64, buf as uint64, count) as int64;
}

fn exit(status: int32) -> void {
    syscall(SYS_EXIT, status as uint64, 0, 0);
}

fn getpid() -> int32 {
    return syscall(SYS_GETPID, 0, 0, 0) as int32;
}

// String functions
fn strlen(s: *char) -> uint64 {
    let len: uint64 = 0;
    while s[len] != 0 {
        len = len + 1;
    }
    return len;
}

fn puts(s: *char) -> int32 {
    let len: uint64 = strlen(s);
    let newline: char = '\n';
    write(STDOUT_FILENO, s as *uint8, len);
    write(STDOUT_FILENO, &newline as *uint8, 1);
    return 0;
}

fn putchar(c: char) -> int32 {
    write(STDOUT_FILENO, &c as *uint8, 1);
    return c as int32;
}

// Memory functions
fn malloc(size: uint64) -> *uint8 {
    // Simple implementation using brk
    let result: uint64 = syscall(12, 0, 0, 0); // brk(0) to get current break
    let current_break: uint64 = result;
    let new_break: uint64 = current_break + size;
    result = syscall(12, new_break, 0, 0); // brk(new_break)
    
    if result == new_break {
        return current_break as *uint8;
    } else {
        return null;
    }
}

fn free(ptr: *uint8) -> void {
    // TODO: Implement proper free
    // For now, do nothing (simple allocator)
}

// Process functions
fn fork() -> int32 {
    // TODO: Implement fork
    return -1;
}

fn execve(path: *char, argv: **char, envp: **char) -> int32 {
    // TODO: Implement execve
    return -1;
}
```

**Tasks:**
- Create minimal libc
- Implement basic I/O functions
- Implement string functions
- Implement memory functions
- Add syscall wrappers
- Document library API

### Phase 7: Dynamic Linking Support (Week 5-6)

**File: `os/kernel/elf.kl` (extend)**
```kale
struct DynamicEntry {
    tag: uint64,
    val: uint64,
}

// Dynamic section tags
const DT_NULL: uint64 = 0;
const DT_NEEDED: uint64 = 1;
const DT_STRTAB: uint64 = 5;
const DT_SYMTAB: uint64 = 6;
const DT_STRSZ: uint64 = 10;
const DT_JMPREL: uint64 = 23;
const DT_PLTRELSZ: uint64 = 2;
const DT_PLTREL: uint64 = 20;

struct Symbol {
    name: uint32,
    info: uint8,
    other: uint8,
    shndx: uint16,
    value: uint64,
    size: uint64,
}

struct Relocation {
    offset: uint64,
    info: uint64,
    addend: int64,
}

fn elf_process_dynamic(process: *ProcessControlBlock, dynamic_addr: uint64) -> bool {
    let dynamic: *DynamicEntry = dynamic_addr as *DynamicEntry;
    
    let strtab: *char = null;
    let symtab: *Symbol = null;
    let strsz: uint64 = 0;
    
    // Parse dynamic entries
    let i: uint64 = 0;
    while dynamic[i].tag != DT_NULL {
        switch dynamic[i].tag {
            case DT_STRTAB:
                strtab = dynamic[i].val as *char;
            case DT_SYMTAB:
                symtab = dynamic[i].val as *Symbol;
            case DT_STRSZ:
                strsz = dynamic[i].val;
        }
        i = i + 1;
    }
    
    // TODO: Process relocations
    // TODO: Load shared libraries (DT_NEEDED)
    
    return true;
}

fn elf_resolve_symbol(name: *char) -> uint64 {
    // TODO: Implement symbol resolution
    return 0;
}
```

**Tasks:**
- Implement dynamic section parsing
- Add symbol table support
- Implement relocation processing
- Add shared library loading
- Implement symbol resolution
- Handle PLT/GOT

### Phase 8: User Space Initialization (Week 6)

**File: `os/kernel/process.kl` (extend)**
```kale
fn init_userspace() -> void {
    // Create init process (PID 1)
    let init_elf: *uint8 = load_init_binary();
    let init_size: uint64 = get_init_binary_size();
    
    let args: [*char; 2] = ["init", null];
    let env: [*char; 1] = [null];
    
    let init_process: *ProcessControlBlock = create_user_process(init_elf, init_size, args, env);
    
    if init_process == null {
        serial_write_string("Failed to create init process\n");
        kernel_panic();
    }
    
    serial_write_string("Init process created: PID ");
    serial_write_dec(init_process.id);
    serial_write_string("\n");
}

fn load_init_binary() -> *uint8 {
    // For now, return a simple init program embedded in kernel
    // In future, load from filesystem
    return embedded_init_binary;
}

fn get_init_binary_size() -> uint64 {
    return embedded_init_binary_size;
}
```

**File: `os/kernel/init_program.asm` (new)**
```assembly
; Simple init program for testing
[BITS 64]
[DEFAULT REL]
[ORG 0x400000]  ; Standard user space load address

global _start

extern puts
extern exit

section .text
_start:
    ; Call puts
    mov rdi, hello_msg
    call puts
    
    ; Exit
    mov rdi, 0
    call exit

section .data
hello_msg: db "Hello from user space!", 10, 0
```

**Tasks:**
- Implement init process creation
- Create simple test programs
- Add user space initialization
- Test user program execution
- Handle program termination

## Testing Strategy

### Unit Tests
1. ELF header parsing
2. Program segment loading
3. Symbol resolution
4. Relocation processing
5. Dynamic linking

### Integration Tests
1. Load and execute simple user programs
2. Test argument passing
3. Test environment variables
4. Test library loading
5. Test process isolation

### Manual Tests
1. Run "Hello World" program
2. Test syscalls from user space
3. Test memory allocation
4. Test file I/O
5. Test program termination

## Dependencies
- VMM (Milestone 1) - for user space memory management
- Task Scheduler (Milestone 2) - for process scheduling
- ISR Framework (Milestone 3) - for syscall handling
- System Call Interface (Milestone 4) - for user-kernel communication

## Success Criteria
- ✅ ELF binaries can be loaded
- ✅ User processes run in ring 3
- ✅ Syscalls work from user space
- ✅ Basic libc functions work
- ✅ Dynamic linking works
- ✅ Process isolation maintained
- ✅ Memory protection works
- ✅ Init process runs successfully

## Next Steps
After User Space Support completion:
1. Implement Heap Allocator (Milestone 6)
2. Implement Filesystem (Milestone 7)
3. Implement Enhanced I/O (Milestone 8)

## Notes
- Start with static linking before dynamic linking
- Create comprehensive test programs
- Document user space ABI thoroughly
- Consider adding a minimal shell
- Test with real C programs (compiled for Kale)
- Keep user space libc minimal initially
