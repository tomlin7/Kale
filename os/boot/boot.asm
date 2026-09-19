; ==============================================================================
; Kale OS Stage 1 MBR Bootloader (x86_64 Bootstrap)
; Loaded by BIOS at 0x7C00 in 16-bit Real Mode
; Reads Kernel Payload (Sectors 2..33) to 0x8000
; Transitions: 16-bit Real Mode -> 32-bit Protected Mode -> 64-bit Long Mode
; Jumps to 64-bit Kernel at 0x8000
; ==============================================================================

[BITS 16]
[ORG 0x7C00]

start:
    cli                         ; Disable interrupts
    xor ax, ax
    mov ds, ax
    mov es, ax
    mov ss, ax
    mov sp, 0x7C00              ; Stack below bootloader
    cld

    ; Set standard VGA 80x25 color text mode (Mode 03h)
    mov ax, 0x0003
    int 0x10

    ; Save BIOS boot drive number passed in DL
    mov [boot_drive], dl


    ; Reset disk system (Drive = DL)
    xor ax, ax
    mov dl, [boot_drive]
    int 0x13

    ; Read sectors 2..33 (32 sectors = 16KB) from boot disk to 0x0000:0x8000
    mov di, 3                   ; Retry counter
.disk_read_loop:
    mov ax, 0x0220              ; AH=0x02 (read), AL=32 sectors (0x20)
    mov cx, 0x0002              ; CH=0 (Cylinder 0), CL=2 (Sector 2)
    mov dh, 0                   ; Head 0
    mov dl, [boot_drive]
    mov bx, 0x8000              ; Destination buffer ES:BX = 0x0000:0x8000
    int 0x13
    jnc .disk_read_success      ; If Carry Flag is clear, read succeeded

    ; Read failed, reset disk and retry
    xor ax, ax
    mov dl, [boot_drive]
    int 0x13
    dec di
    jnz .disk_read_loop

    ; Disk read failed after 3 attempts
    mov si, msg_disk_fail
    call bios_print
    cli
    hlt

.disk_read_success:
    ; Fast A20 Gate Enable
    in al, 0x92
    or al, 2
    out 0x92, al

    ; Load 32-bit GDT
    lgdt [gdt32_descriptor]

    ; Enable Protected Mode (CR0.PE = 1)
    mov eax, cr0
    or eax, 1
    mov cr0, eax

    ; Far jump to 32-bit protected mode
    jmp CODE_SEG_32:init_pm32

bios_print:
    lodsb
    test al, al
    jz .done
    mov ah, 0x0E
    mov bh, 0
    mov bl, 0x07
    int 0x10
    jmp bios_print
.done:
    ret

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

    ; Enable Paging (CR0.PG = 1)
    mov eax, cr0
    or eax, (1 << 31) | (1 << 0)
    mov cr0, eax

    ; Far jump into 64-Bit Long Mode Kernel at 0x8000!
    jmp CODE_SEG_64:0x8000

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

boot_drive:     db 0
msg_disk_fail:  db "Disk read error!", 0

; Pad up to 510 bytes, then append MBR boot signature 0xAA55
times 510 - ($ - $$) db 0
dw 0xAA55
