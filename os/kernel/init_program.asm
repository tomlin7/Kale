; ==============================================================================
; Kale OS Minimal User-Space Init Program
; Architecture: x86_64 ELF Executable (Ring 3)
; ==============================================================================

[BITS 64]
[ORG 0x00400000]

ehdr:
    ; e_ident (16 bytes)
    db 0x7F, "ELF"      ; Magic: 0x7F, 'E', 'L', 'F'
    db 2                ; ELFCLASS64 (64-bit)
    db 1                ; ELFDATA2LSB (Little Endian)
    db 1                ; EV_CURRENT
    db 0                ; System V ABI
    db 0                ; ABI Version
    times 7 db 0        ; Padding
    dd 2                ; e_type = ET_EXEC (2)
    dd 0x3E             ; e_machine = EM_X86_64 (62)
    dd 1                ; e_version = 1
    dd 0                ; Padding to align 64-bit e_entry to 8-byte boundary
    dq _start           ; e_entry
    dq phdr - $$        ; e_phoff (offset to program header table)
    dq 0                ; e_shoff (no section headers)
    dd 0                ; e_flags
    dd 128              ; e_ehsize (128 bytes)
    dd 56               ; e_phentsize (56 bytes)
    dd 1                ; e_phnum (1 loadable segment)
    dd 64               ; e_shentsize
    dd 0                ; e_shnum
    dd 0                ; e_shstrndx
    times 128 - ($ - ehdr) db 0  ; Align phdr to offset 128

phdr:
    dd 1                ; p_type = PT_LOAD (1)
    dd 7                ; p_flags = PF_R | PF_W | PF_X (1 | 2 | 4)
    dq 0                ; p_offset
    dq 0x00400000       ; p_vaddr
    dq 0x00400000       ; p_paddr
    dq file_end - $$    ; p_filesz
    dq file_end - $$    ; p_memsz
    dq 0x1000           ; p_align (4KB page alignment)

_start:
    ; Write greeting message to stdout via INT 0x80 syscall
    ; RAX = 1 (SYS_WRITE), RDI = 1 (stdout), RSI = msg, RDX = len
    mov eax, 1          ; SYS_WRITE
    mov edi, 1          ; STDOUT_FILENO
    lea rsi, [rel msg_hello]
    mov edx, msg_len
    int 0x80

    ; Exit process with status 0
    ; RAX = 60 (SYS_EXIT), RDI = 0 (status)
    mov eax, 60         ; SYS_EXIT
    xor edi, edi        ; status = 0
    int 0x80

    ; Fallback halt loop if syscall returns
.hang:
    hlt
    jmp .hang

msg_hello: db "Hello from user space!", 10, 0
msg_len equ $ - msg_hello - 1

align 8
file_end:
