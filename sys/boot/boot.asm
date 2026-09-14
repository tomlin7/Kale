; ==============================================================================
; Kale OS Stage 1 MBR Bootloader (x86_64 Bootstrap)
; Loaded by BIOS at 0x7C00 in 16-bit Real Mode
; Transitions: 16-bit Real Mode -> 32-bit Protected Mode -> 64-bit Long Mode
; ==============================================================================

[BITS 16]
[ORG 0x7C00]

start:
    cli                         ; Disable maskable interrupts
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00              ; Setup stack below bootloader

    cld

    ; Fast A20 Gate Enable
    in al, 0x92
    or al, 2
    out 0x92, al

    ; Load GDT for 32-bit protected mode
    lgdt [gdt32_descriptor]

    ; Enable Protected Mode (Set PE bit in CR0)
    mov eax, cr0
    or eax, 1
    mov cr0, eax

    ; Far jump to enter 32-bit mode
    jmp CODE_SEG_32:init_pm32

; ==============================================================================
; 32-Bit Protected Mode
; ==============================================================================
[BITS 32]
init_pm32:
    mov ax, DATA_SEG_32
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov esp, 0x90000            ; Low memory stack

    ; Setup 64-bit Identity Paging at 0x1000
    call setup_paging_64

    ; Load 64-bit GDT
    lgdt [gdt64_descriptor]

    ; Enable PAE in CR4
    mov eax, cr4
    or eax, 1 << 5
    mov cr4, eax

    ; Set LME (Long Mode Enable) in EFER MSR (0xC0000080)
    mov ecx, 0xC0000080
    rdmsr
    or eax, 1 << 8
    wrmsr

    ; Enable Paging (PG bit in CR0)
    mov eax, cr0
    or eax, (1 << 31) | (1 << 0)
    mov cr0, eax

    ; Far jump into 64-Bit Long Mode
    jmp CODE_SEG_64:init_lm64

setup_paging_64:
    ; Zero out 16KB of paging structures at 0x1000
    mov edi, 0x1000
    mov cr3, edi
    xor eax, eax
    mov ecx, 4096
    rep stosd

    ; PML4[0] -> PDPT (0x2000) (Present + Writable: 0x3)
    mov dword [0x1000], 0x2003

    ; PDPT[0] -> PD (0x3000) (Present + Writable: 0x3)
    mov dword [0x2000], 0x3003

    ; PD[0] -> 2MB huge page (0x83: Present + Writable + Page Size)
    ; Maps first 2MB: 0x00000000 -> 0x00200000
    mov dword [0x3000], 0x00000083
    ret

; ==============================================================================
; 64-Bit Long Mode
; ==============================================================================
[BITS 64]
init_lm64:
    mov ax, DATA_SEG_64
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov rsp, 0x00200000         ; 2MB stack top

    ; Write banner to VGA text buffer at 0xB8000
    mov rdi, 0xB8000
    mov rsi, msg_kale_kernel
    mov ah, 0x4F                ; White on Red (Imperial Crimson)

.print_vga:
    lodsb
    test al, al
    jz .halt
    mov [rdi], ax
    add rdi, 2
    jmp .print_vga

.halt:
    hlt
    jmp .halt

; ==============================================================================
; Global Descriptor Tables
; ==============================================================================

; --- 32-bit GDT ---
gdt32_start:
    dq 0x0000000000000000
    dw 0xFFFF, 0x0000, 0x9A00, 0x00CF
    dw 0xFFFF, 0x0000, 0x9200, 0x00CF
gdt32_end:

gdt32_descriptor:
    dw gdt32_end - gdt32_start - 1
    dd gdt32_start

CODE_SEG_32 equ 0x08
DATA_SEG_32 equ 0x10

; --- 64-bit GDT ---
gdt64_start:
    dq 0x0000000000000000
    dw 0x0000, 0x0000, 0x9A00, 0x0020
    dw 0x0000, 0x0000, 0x9200, 0x0000
gdt64_end:

gdt64_descriptor:
    dw gdt64_end - gdt64_start - 1
    dd gdt64_start

CODE_SEG_64 equ 0x08
DATA_SEG_64 equ 0x10

msg_kale_kernel: db " [KALE OS] 64-BIT LONG MODE ACTIVE. MICROKERNEL V0.0.1 ", 0

; Pad up to 510 bytes, then append MBR boot signature 0xAA55
times 510 - ($ - $$) db 0
dw 0xAA55
