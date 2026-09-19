# Milestone 4: System Call Interface

## Overview
Implement a complete system call interface that provides a well-defined boundary between user space and kernel space. This includes the syscall instruction handling, parameter passing, return values, and a comprehensive set of basic system calls.

## Current State
- Basic syscall ISR stub implemented in Milestone 3
- No comprehensive syscall interface
- No parameter validation
- No user space ABI definition
- Limited syscall implementations

## Objectives
1. Define user space ABI and calling convention
2. Implement comprehensive syscall dispatcher
3. Implement basic syscall implementations
4. Add parameter validation and error handling
5. Implement syscall tracing/debugging
6. Add performance monitoring

## Technical Implementation

### Phase 1: User Space ABI Definition (Week 1)

**File: `os/kernel/syscall.h` (new header)**
```c
// System Call Calling Convention (x86_64 System V ABI)
// RAX = syscall number
// RDI, RSI, RDX, R10, R8, R9 = parameters (in order)
// RAX = return value
// RCX, R11, R12, R13, R14, R15 = clobbered by kernel

// System Call Numbers
#define SYS_EXIT          60
#define SYS_READ           0
#define SYS_WRITE          1
#define SYS_OPEN           2
#define SYS_CLOSE          3
#define SYS_STAT           4
#define SYS_FSTAT          5
#define SYS_LSTAT          6
#define SYS_POLL           7
#define SYS_LSEEK          8
#define SYS_MMAP           9
#define SYS_MPROT         10
#define SYS_MUNMAP        11
#define SYS_BRK           12
#define SYS_RT_SIGACTION  13
#define SYS_RT_SIGPROCMASK 14
#define SYS_RT_SIGRETURN  15
#define SYS_IOCTL         16
#define SYS_PREAD64       17
#define SYS_PWRITE64      18
#define SYS_READV         19
#define SYS_WRITEV        20
#define SYS_ACCESS        21
#define SYS_PIPE          22
#define SYS_SELECT        23
#define SYS_SCHED_YIELD   24
#define SYS_MREMAP        25
#define SYS_MSYNC         26
#define SYS_MINCORE       27
#define SYS_MADVISE       28
#define SYS_SHMGET        29
#define SYS_SHMAT         30
#define SYS_SHMCTL        31
#define SYS_DUP           32
#define SYS_DUP2          33
#define SYS_PAUSE         34
#define SYS_NANOSLEEP     35
#define SYS_GETITIMER     36
#define SYS_ALARM         37
#define SYS_SETITIMER     38
#define SYS_GETPID        39
#define SYS_SENDFILE      40
#define SYS_SOCKET        41
#define SYS_CONNECT       42
#define SYS_ACCEPT        43
#define SYS_SENDTO        44
#define SYS_RECVFROM      45
#define SYS_SENDMSG       46
#define SYS_RECVMSG       47
#define SYS_SHUTDOWN      48
#define SYS_BIND          49
#define SYS_LISTEN        50
#define SYS_GETSOCKNAME   51
#define SYS_GETPEERNAME   52
#define SYS_SOCKETPAIR    53
#define SYS_SETSOCKOPT    54
#define SYS_GETSOCKOPT    55
#define SYS_CLONE         56
#define SYS_FORK          57
#define SYS_VFORK         58
#define SYS_EXECVE        59
#define SYS_KILL          62
#define SYS_UNAME         63
#define SYS_SEMGET        64
#define SYS_SEMOP         65
#define SYS_SEMCTL        66
#define SYS_SHMDT         67
#define SYS_MSGGET        68
#define SYS_MSGSND        69
#define SYS_MSGRCV        70
#define SYS_MSGCTL        71
#define SYS_FCNTL         72
#define SYS_FLOCK         73
#define SYS_FSYNC         74
#define SYS_FDATASYNC     75
#define SYS_TRUNCATE      76
#define SYS_FTRUNCATE     77
#define SYS_GETDENTS      78
#define SYS_GETCWD        79
#define SYS_CHDIR         80
#define SYS_FCHDIR        81
#define SYS_RENAME        82
#define SYS_MKDIR         83
#define SYS_RMDIR         84
#define SYS_CREAT         85
#define SYS_LINK          86
#define SYS_UNLINK        87
#define SYS_SYMLINK       88
#define SYS_READLINK      89
#define SYS_CHMOD         90
#define SYS_FCHMOD        91
#define SYS_CHOWN         92
#define SYS_FCHOWN        93
#define SYS_LCHOWN        94
#define SYS_UMASK         95
#define SYS_GETTIMEOFDAY  96
#define SYS_GETRLIMIT     97
#define SYS_GETRUSAGE     98
#define SYS_SYSINFO       99
#define SYS_TIMES        100
#define SYS_GETUID       102
#define SYS_GETGID       103
#define SYS_SETUID       104
#define SYS_SETGID       105
#define SYS_GETEUID      106
#define SYS_GETEGID      107
#define SYS_SETEUID      108
#define SYS_SETEGID      109
#define SYS_GETPPID      110
#define SYS_GETPGRP      111
#define SYS_SETSID       112
#define SYS_SETPGID      113
#define SYS_GETPGID      114
#define SYS_GETSID       115
```

**File: `os/kernel/syscall.kl`**
```kale
// System Call ABI Structure
struct SyscallContext {
    number: uint64,
    arg1: uint64,
    arg2: uint64,
    arg3: uint64,
    arg4: uint64,
    arg5: uint64,
    arg6: uint64,
    return_value: uint64,
    error: int32,
}

// User Space ABI Definition
const SYSCALL_REG_RAX: uint8 = 0;   // Syscall number / return
const SYSCALL_REG_RDI: uint8 = 1;   // First argument
const SYSCALL_REG_RSI: uint8 = 2;   // Second argument
const SYSCALL_REG_RDX: uint8 = 3;   // Third argument
const SYSCALL_REG_R10: uint8 = 4;   // Fourth argument
const SYSCALL_REG_R8:  uint8 = 5;   // Fifth argument
const SYSCALL_REG_R9:  uint8 = 6;   // Sixth argument
```

**Tasks:**
- Define syscall calling convention
- Document register usage
- Define syscall number constants
- Create syscall context structure
- Document ABI for user space programs

### Phase 2: Syscall Dispatcher (Week 1-2)

**File: `os/kernel/syscall.kl`**
```kale
// Syscall Handler Function Type
type SyscallHandler = fn(ctx: *SyscallContext) -> void;

// Syscall Handler Table
struct SyscallTable {
    handlers: [SyscallHandler; 256],
    names: [*char; 256],
}

let syscall_table: SyscallTable;

fn syscall_init() -> void {
    let i: int32 = 0;
    while i < 256 {
        syscall_table.handlers[i] = syscall_not_implemented;
        syscall_table.names[i] = "unknown";
        i = i + 1;
    }
    
    // Register handlers
    syscall_register(SYS_EXIT, sys_exit, "exit");
    syscall_register(SYS_READ, sys_read, "read");
    syscall_register(SYS_WRITE, sys_write, "write");
    syscall_register(SYS_OPEN, sys_open, "open");
    syscall_register(SYS_CLOSE, sys_close, "close");
    syscall_register(SYS_GETPID, sys_getpid, "getpid");
    syscall_register(SYS_KILL, sys_kill, "kill");
    syscall_register(SYS_SCHED_YIELD, sys_sched_yield, "sched_yield");
}

fn syscall_register(num: uint64, handler: SyscallHandler, name: *char) -> void {
    if num < 256 {
        syscall_table.handlers[num] = handler;
        syscall_table.names[num] = name;
    }
}

fn syscall_not_implemented(ctx: *SyscallContext) -> void {
    ctx.return_value = -1 as uint64;
    ctx.error = 38; // ENOSYS
    serial_write_string("Syscall not implemented: ");
    serial_write_string(syscall_table.names[ctx.number]);
    serial_write_string("\n");
}

fn syscall_dispatch(ctx: *SyscallContext) -> void {
    if ctx.number >= 256 {
        syscall_not_implemented(ctx);
        return;
    }
    
    // Validate user space pointers
    if !validate_user_pointer(ctx.arg1) {
        ctx.return_value = -1 as uint64;
        ctx.error = 14; // EFAULT
        return;
    }
    
    // Call handler
    syscall_table.handlers[ctx.number](ctx);
}
```

**Tasks:**
- Implement syscall dispatcher
- Create syscall handler table
- Implement handler registration
- Add parameter validation
- Implement default "not implemented" handler

### Phase 3: Basic Syscall Implementations (Week 2-3)

**File: `os/kernel/syscall.kl`**
```kale
// Process Control Syscalls
fn sys_exit(ctx: *SyscallContext) -> void {
    let exit_code: int32 = ctx.arg1 as int32;
    terminate_process(scheduler.current_process, exit_code);
    // Does not return
}

fn sys_getpid(ctx: *SyscallContext) -> void {
    ctx.return_value = scheduler.current_process.id as uint64;
    ctx.error = 0;
}

fn sys_kill(ctx: *SyscallContext) -> void {
    let pid: uint32 = ctx.arg1 as uint32;
    let signal: uint32 = ctx.arg2 as uint32;
    
    let target: *ProcessControlBlock = find_process_by_pid(pid);
    if target == null {
        ctx.return_value = -1 as uint64;
        ctx.error = 3; // ESRCH
        return;
    }
    
    // TODO: Implement signal handling
    ctx.return_value = 0;
    ctx.error = 0;
}

fn sys_sched_yield(ctx: *SyscallContext) -> void {
    schedule();
    ctx.return_value = 0;
    ctx.error = 0;
}

// File I/O Syscalls (placeholder for filesystem milestone)
fn sys_read(ctx: *SyscallContext) -> void {
    let fd: int32 = ctx.arg1 as int32;
    let buf: *uint8 = ctx.arg2 as *uint8;
    let count: uint64 = ctx.arg3;
    
    // TODO: Implement proper file I/O
    ctx.return_value = 0;
    ctx.error = 38; // ENOSYS
}

fn sys_write(ctx: *SyscallContext) -> void {
    let fd: int32 = ctx.arg1 as int32;
    let buf: *uint8 = ctx.arg2 as *uint8;
    let count: uint64 = ctx.arg3;
    
    // For now, implement stdout/stderr to serial
    if fd == 1 || fd == 2 {
        let i: uint64 = 0;
        while i < count {
            serial_write_byte(buf[i]);
            i = i + 1;
        }
        ctx.return_value = count;
        ctx.error = 0;
    } else {
        ctx.return_value = -1 as uint64;
        ctx.error = 9; // EBADF
    }
}

fn sys_open(ctx: *SyscallContext) -> void {
    // TODO: Implement proper file opening
    ctx.return_value = -1 as uint64;
    ctx.error = 38; // ENOSYS
}

fn sys_close(ctx: *SyscallContext) -> void {
    let fd: int32 = ctx.arg1 as int32;
    
    // TODO: Implement proper file closing
    ctx.return_value = 0;
    ctx.error = 0;
}
```

**Tasks:**
- Implement process control syscalls
- Implement basic file I/O syscalls
- Implement memory management syscalls
- Implement information syscalls
- Add error code definitions

### Phase 4: Memory Management Syscalls (Week 3)

**File: `os/kernel/syscall.kl`**
```kale
fn sys_brk(ctx: *SyscallContext) -> void {
    let new_brk: uint64 = ctx.arg1;
    let current: *ProcessControlBlock = scheduler.current_process;
    
    if new_brk == 0 {
        // Return current break
        ctx.return_value = current.heap_break;
        ctx.error = 0;
        return;
    }
    
    // Validate new break address
    if new_brk < current.heap_start || new_brk > current.heap_max {
        ctx.return_value = current.heap_break;
        ctx.error = 12; // ENOMEM
        return;
    }
    
    // Allocate or free pages as needed
    let old_pages: uint64 = (current.heap_break - current.heap_start) / 4096;
    let new_pages: uint64 = (new_brk - current.heap_start) / 4096;
    
    if new_pages > old_pages {
        // Allocate pages
        let i: uint64 = old_pages;
        while i < new_pages {
            let phys: uint64 = pmm_alloc_frame(&pmm);
            if phys == 0 {
                ctx.return_value = current.heap_break;
                ctx.error = 12; // ENOMEM
                return;
            }
            let virt: uint64 = current.heap_start + (i * 4096);
            vmm_map_page(&vmm, virt, phys, 0x7); // User + Writable + Present
            i = i + 1;
        }
    } else if new_pages < old_pages {
        // Free pages
        let i: uint64 = new_pages;
        while i < old_pages {
            let virt: uint64 = current.heap_start + (i * 4096);
            let phys: uint64 = vmm_get_phys_addr(&vmm, virt);
            vmm_unmap_page(&vmm, virt);
            pmm_free_frame(&pmm, phys);
            i = i + 1;
        }
    }
    
    current.heap_break = new_brk;
    ctx.return_value = new_brk;
    ctx.error = 0;
}

fn sys_mmap(ctx: *SyscallContext) -> void {
    let addr: uint64 = ctx.arg1;
    let length: uint64 = ctx.arg2;
    let prot: uint32 = ctx.arg3 as uint32;
    let flags: uint32 = ctx.arg4 as uint32;
    let fd: int32 = ctx.arg5 as int32;
    let offset: uint64 = ctx.arg6;
    
    // Simple implementation: allocate at requested address or find free
    let current: *ProcessControlBlock = scheduler.current_process;
    let map_addr: uint64;
    
    if addr != 0 && (flags & 0x20) == 0 { // MAP_FIXED not set
        map_addr = addr;
    } else {
        // Find free address in user space
        map_addr = find_free_user_region(length);
    }
    
    // Map pages
    let pages: uint64 = (length + 4095) / 4096;
    let i: uint64 = 0;
    while i < pages {
        let phys: uint64 = pmm_alloc_frame(&pmm);
        if phys == 0 {
            // Cleanup on failure
            mmap_cleanup(map_addr, i * 4096);
            ctx.return_value = -1 as uint64;
            ctx.error = 12; // ENOMEM
            return;
        }
        
        let vmm_flags: uint64 = 0x1; // Present
        if (prot & 0x2) != 0 { vmm_flags = vmm_flags | 0x2; } // Writable
        if (prot & 0x4) != 0 { vmm_flags = vmm_flags | 0x4; } // User
        
        vmm_map_page(&vmm, map_addr + (i * 4096), phys, vmm_flags);
        i = i + 1;
    }
    
    ctx.return_value = map_addr;
    ctx.error = 0;
}

fn sys_munmap(ctx: *SyscallContext) -> void {
    let addr: uint64 = ctx.arg1;
    let length: uint64 = ctx.arg2;
    
    let pages: uint64 = (length + 4095) / 4096;
    let i: uint64 = 0;
    while i < pages {
        let virt: uint64 = addr + (i * 4096);
        let phys: uint64 = vmm_get_phys_addr(&vmm, virt);
        if phys != 0 {
            vmm_unmap_page(&vmm, virt);
            pmm_free_frame(&pmm, phys);
        }
        i = i + 1;
    }
    
    ctx.return_value = 0;
    ctx.error = 0;
}
```

**Tasks:**
- Implement brk syscall for heap management
- Implement mmap syscall for memory mapping
- Implement munmap syscall for unmapping
- Implement mprotect syscall for page protection
- Add address space layout management

### Phase 5: Information Syscalls (Week 4)

**File: `os/kernel/syscall.kl`**
```kale
struct Utsname {
    sysname: [char; 65],
    nodename: [char; 65],
    release: [char; 65],
    version: [char; 65],
    machine: [char; 65],
    domainname: [char; 65],
}

fn sys_uname(ctx: *SyscallContext) -> void {
    let buf: *Utsname = ctx.arg1 as *Utsname;
    
    if !validate_user_pointer(ctx.arg1) {
        ctx.return_value = -1 as uint64;
        ctx.error = 14; // EFAULT
        return;
    }
    
    // Copy strings
    copy_string(buf.sysname, "KaleOS", 65);
    copy_string(buf.nodename, "kaleos", 65);
    copy_string(buf.release, "0.1.0", 65);
    copy_string(buf.version, "Kale OS v0.1.0-alpha", 65);
    copy_string(buf.machine, "x86_64", 65);
    copy_string(buf.domainname, "(none)", 65);
    
    ctx.return_value = 0;
    ctx.error = 0;
}

struct Sysinfo {
    uptime: uint64,
    loads: [uint64; 3],
    totalram: uint64,
    freeram: uint64,
    sharedram: uint64,
    bufferram: uint64,
    totalswap: uint64,
    freeswap: uint64,
    procs: uint16,
    totalhigh: uint64,
    freehigh: uint64,
    mem_unit: uint32,
}

fn sys_sysinfo(ctx: *SyscallContext) -> void {
    let info: *Sysinfo = ctx.arg1 as *Sysinfo;
    
    if !validate_user_pointer(ctx.arg1) {
        ctx.return_value = -1 as uint64;
        ctx.error = 14; // EFAULT
        return;
    }
    
    info.uptime = system_ticks / 1000; // Assume 1000Hz
    info.loads[0] = 0;
    info.loads[1] = 0;
    info.loads[2] = 0;
    info.totalram = pmm.total_frames * 4096;
    info.freeram = (pmm.total_frames - pmm.used_frames) * 4096;
    info.sharedram = 0;
    info.bufferram = 0;
    info.totalswap = 0;
    info.freeswap = 0;
    info.procs = scheduler.process_count as uint16;
    info.totalhigh = 0;
    info.freehigh = 0;
    info.mem_unit = 1;
    
    ctx.return_value = 0;
    ctx.error = 0;
}
```

**Tasks:**
- Implement uname syscall
- Implement sysinfo syscall
- Implement gettimeofday syscall
- Implement getrlimit/setrlimit syscalls
- Add system information structures

### Phase 6: Enhanced ISR Integration (Week 4-5)

**File: `os/kernel/isr.asm` (extend)**
```assembly
; Enhanced syscall entry
global syscall_entry
extern syscall_handler

syscall_entry:
    ; Save user stack pointer
    mov [user_rsp], rsp
    
    ; Save user segment registers
    mov ax, ds
    push ax
    mov ax, es
    push ax
    
    ; Load kernel segments
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    
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
    
    ; Call handler
    mov rdi, rsp
    call syscall_handler
    
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
    
    ; Restore user segments
    pop ax
    mov es, ax
    pop ax
    mov ds, ax
    
    ; Restore user stack
    mov rsp, [user_rsp]
    
    ; Return to user space
    sysret
```

**File: `os/kernel/syscall.kl`**
```kale
fn syscall_handler(frame: *InterruptFrame) -> void {
    let ctx: SyscallContext;
    
    ctx.number = frame.rax;
    ctx.arg1 = frame.rdi;
    ctx.arg2 = frame.rsi;
    ctx.arg3 = frame.rdx;
    ctx.arg4 = frame.r10;
    ctx.arg5 = frame.r8;
    ctx.arg6 = frame.r9;
    ctx.return_value = 0;
    ctx.error = 0;
    
    // Dispatch syscall
    syscall_dispatch(&ctx);
    
    // Set return value and error
    frame.rax = ctx.return_value;
    
    // Set error flag in user-visible way
    if ctx.error != 0 {
        // Set error in a way user space can detect
        // (e.g., set carry flag or use a separate error register)
    }
}
```

**Tasks:**
- Enhance syscall assembly entry point
- Add proper segment switching
- Implement user space stack handling
- Add syscall performance monitoring
- Add syscall tracing support

### Phase 7: Error Handling and Validation (Week 5)

**File: `os/kernel/syscall.kl`**
```kale
// Error Codes (errno)
const EPERM: int32 = 1;
const ENOENT: int32 = 2;
const ESRCH: int32 = 3;
const EINTR: int32 = 4;
const EIO: int32 = 5;
const ENXIO: int32 = 6;
const E2BIG: int32 = 7;
const ENOEXEC: int32 = 8;
const EBADF: int32 = 9;
const ECHILD: int32 = 10;
const EAGAIN: int32 = 11;
const ENOMEM: int32 = 12;
const EACCES: int32 = 13;
const EFAULT: int32 = 14;
const ENOTBLK: int32 = 15;
const EBUSY: int32 = 16;
const EEXIST: int32 = 17;
const EXDEV: int32 = 18;
const ENODEV: int32 = 19;
const ENOTDIR: int32 = 20;
const EISDIR: int32 = 21;
const EINVAL: int32 = 22;
const ENFILE: int32 = 23;
const EMFILE: int32 = 24;
const ENOTTY: int32 = 25;
const ETXTBSY: int32 = 26;
const EFBIG: int32 = 27;
const ENOSPC: int32 = 28;
const ESPIPE: int32 = 29;
const EROFS: int32 = 30;
const EMLINK: int32 = 31;
const EPIPE: int32 = 32;
const EDOM: int32 = 33;
const ERANGE: int32 = 34;
const EDEADLK: int32 = 35;
const ENAMETOOLONG: int32 = 36;
const ENOLCK: int32 = 37;
const ENOSYS: int32 = 38;
const ENOTEMPTY: int32 = 39;
const ELOOP: int32 = 40;
const ENOMSG: int32 = 42;
const EIDRM: int32 = 43;
const ECHRNG: int32 = 44;
const EL2NSYNC: int32 = 45;
const EL3HLT: int32 = 46;
const EL3RST: int32 = 47;
const ELNRNG: int32 = 48;
const EUNATCH: int32 = 49;
const ENOCSI: int32 = 50;
const EL2HLT: int32 = 51;
const EBADE: int32 = 52;
const EBADR: int32 = 53;
const EXFULL: int32 = 54;
const ENOANO: int32 = 55;
const EBADRQC: int32 = 56;
const EBADSLT: int32 = 57;
const EDEADLOCK: int32 = 58;
const EBFONT: int32 = 59;
const ENOSTR: int32 = 60;
const ENODATA: int32 = 61;
const ETIME: int32 = 62;
const ENOSR: int32 = 63;
const ENONET: int32 = 64;
const ENOPKG: int32 = 65;
const EREMOTE: int32 = 66;
const ENOLINK: int32 = 67;
const EADV: int32 = 68;
const ESRMNT: int32 = 69;
const ECOMM: int32 = 70;
const EPROTO: int32 = 71;
const EMULTIHOP: int32 = 72;
const EDOTDOT: int32 = 73;
const EBADMSG: int32 = 74;
const EOVERFLOW: int32 = 75;
const ENOTUNIQ: int32 = 76;
const EBADFD: int32 = 77;
const EREMCHG: int32 = 78;
const ELIBACC: int32 = 79;
const ELIBBAD: int32 = 80;
const ELIBSCN: int32 = 81;
const ELIBMAX: int32 = 82;
const ELIBEXEC: int32 = 83;
const EILSEQ: int32 = 84;
const ERESTART: int32 = 85;
const ESTRPIPE: int32 = 86;
const EUSERS: int32 = 87;
const ENOTSOCK: int32 = 88;
const EDESTADDRREQ: int32 = 89;
const EMSGSIZE: int32 = 90;
const EPROTOTYPE: int32 = 91;
const ENOPROTOOPT: int32 = 92;
const EPROTONOSUPPORT: int32 = 93;
const ESOCKTNOSUPPORT: int32 = 94;
const EOPNOTSUPP: int32 = 95;
const EPFNOSUPPORT: int32 = 96;
const EAFNOSUPPORT: int32 = 97;
const EADDRINUSE: int32 = 98;
const EADDRNOTAVAIL: int32 = 99;
const ENETDOWN: int32 = 100;
const ENETUNREACH: int32 = 101;
const ENETRESET: int32 = 102;
const ECONNABORTED: int32 = 103;
const ECONNRESET: int32 = 104;
const ENOBUFS: int32 = 105;
const EISCONN: int32 = 106;
const ENOTCONN: int32 = 107;
const ESHUTDOWN: int32 = 108;
const ETOOMANYREFS: int32 = 109;
const ETIMEDOUT: int32 = 110;
const ECONNREFUSED: int32 = 111;
const EHOSTDOWN: int32 = 112;
const EHOSTUNREACH: int32 = 113;
const EALREADY: int32 = 114;
const EINPROGRESS: int32 = 115;
const ESTALE: int32 = 116;
const EUCLEAN: int32 = 117;
const ENOTNAM: int32 = 118;
const ENAVAIL: int32 = 119;
const EISNAM: int32 = 120;
const EREMOTEIO: int32 = 121;
const EDQUOT: int32 = 122;
const ENOMEDIUM: int32 = 123;
const EMEDIUMTYPE: int32 = 124;
const ECANCELED: int32 = 125;
const ENOKEY: int32 = 126;
const EKEYEXPIRED: int32 = 127;
const EKEYREVOKED: int32 = 128;
const EKEYREJECTED: int32 = 129;
const EOWNERDEAD: int32 = 130;
const ENOTRECOVERABLE: int32 = 131;
const ERFKILL: int32 = 132;
const EHWPOISON: int32 = 133;

fn validate_user_pointer(ptr: uint64) -> bool {
    // Check if pointer is in user space range
    return ptr < 0x0000800000000000;
}

fn validate_user_string(ptr: uint64, max_len: uint64) -> bool {
    if !validate_user_pointer(ptr) {
        return false;
    }
    
    // Check for null terminator within max_len
    let i: uint64 = 0;
    while i < max_len {
        if (ptr as *uint8)[i] == 0 {
            return true;
        }
        i = i + 1;
    }
    
    return false;
}
```

**Tasks:**
- Define all error codes
- Implement user pointer validation
- Implement user string validation
- Add parameter validation to all syscalls
- Add permission checking

### Phase 8: Performance Monitoring (Week 5-6)

**File: `os/kernel/syscall.kl`**
```kale
struct SyscallStats {
    count: uint64,
    total_time: uint64,
    min_time: uint64,
    max_time: uint64,
}

let syscall_stats: [SyscallStats; 256];

fn syscall_enter(num: uint64) -> void {
    syscall_stats[num].count = syscall_stats[num].count + 1;
}

fn syscall_exit(num: uint64, elapsed: uint64) -> void {
    syscall_stats[num].total_time = syscall_stats[num].total_time + elapsed;
    
    if elapsed < syscall_stats[num].min_time || syscall_stats[num].min_time == 0 {
        syscall_stats[num].min_time = elapsed;
    }
    
    if elapsed > syscall_stats[num].max_time {
        syscall_stats[num].max_time = elapsed;
    }
}

fn syscall_print_stats() -> void {
    let i: uint64 = 0;
    while i < 256 {
        if syscall_stats[i].count > 0 {
            serial_write_string("Syscall ");
            serial_write_dec(i);
            serial_write_string(": count=");
            serial_write_dec(syscall_stats[i].count);
            serial_write_string(", avg_time=");
            serial_write_dec(syscall_stats[i].total_time / syscall_stats[i].count);
            serial_write_string("\n");
        }
        i = i + 1;
    }
}
```

**Tasks:**
- Add syscall statistics tracking
- Add timing information
- Implement stats reporting
- Add performance profiling hooks
- Add syscall tracing support

## Testing Strategy

### Unit Tests
1. Syscall parameter validation
2. Error code generation
3. Pointer validation
4. Memory management syscalls
5. Information syscalls

### Integration Tests
1. All syscalls dispatch correctly
2. Return values are correct
3. Error handling works
4. Performance monitoring works
5. User space can call syscalls

### Manual Tests
1. Test each syscall individually
2. Test error conditions
3. Test invalid parameters
4. Test performance under load
5. Test syscall tracing

## Dependencies
- ISR Framework (Milestone 3) - for syscall interrupt handling
- VMM (Milestone 1) - for memory management syscalls
- Task Scheduler (Milestone 2) - for process control syscalls
- User Space Support (Milestone 5) - for proper testing

## Success Criteria
- ✅ All basic syscalls implemented
- ✅ Parameter validation works
- ✅ Error handling is correct
- ✅ Performance monitoring works
- ✅ User space can call syscalls
- ✅ ABI is well-documented
- ✅ No crashes during syscalls
- ✅ Performance is acceptable

## Next Steps
After System Call Interface completion:
1. Implement User Space Support (Milestone 5)
2. Implement Heap Allocator (Milestone 6)
3. Implement Filesystem (Milestone 7)

## Notes
- Document syscall ABI thoroughly for user space developers
- Consider adding a syscall compatibility layer for Linux binaries
- Add syscall performance benchmarks
- Keep syscall handlers as simple and fast as possible
- Consider adding seccomp-like syscall filtering
