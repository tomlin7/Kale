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

    ; Query VBE Mode Info for Mode 0x0115 (800x600)
    mov ax, 0x4F01
    mov cx, 0x0115
    mov di, 0x7100              ; Temporary VBE Mode Info buffer (256 bytes)
    int 0x10
    cmp ax, 0x004F
    jne .vbe_fail

    ; Set VBE Mode with Linear Frame Buffer (bit 14: 0x4000)
    mov ax, 0x4F02
    mov bx, 0x4115              ; Mode 0x115 + LFB (0x4000)
    int 0x10
    cmp ax, 0x004F
    jne .vbe_fail

    ; Write BootInfo at 0x7000 from VBE info at 0x7100
    mov dword [0x7004], 1       ; 1 = VBE LFB Graphics
    mov eax, [di + 0x28]        ; PhysBasePtr
    mov [0x7008], eax
    movzx eax, word [di + 0x12] ; Width (800)
    mov [0x7010], eax
    movzx eax, word [di + 0x14] ; Height (600)
    mov [0x7014], eax
    movzx eax, word [di + 0x10] ; Pitch (3200)
    mov [0x7018], eax
    movzx eax, byte [di + 0x19] ; BPP (32)
    mov [0x701C], eax
    jmp .video_done

.vbe_fail:
    ; Fallback to VGA Text Mode 03h
    mov ax, 0x0003
    int 0x10
    mov dword [0x7004], 0       ; 0 = VGA text fallback
    mov dword [0x7008], 0xB8000
    mov dword [0x7010], 80
    mov dword [0x7014], 25
    mov dword [0x7018], 160
    mov dword [0x701C], 16

.video_done:
    mov dword [0x7000], 0x4B414C45  ; Magic: 'KALE'

    ; Save BIOS boot drive number passed in DL
    mov [boot_drive], dl


    ; Reset disk system (Drive = DL)
    xor ax, ax
    mov dl, [boot_drive]
    int 0x13

    ; Read sectors 2..49 (48 sectors = 24KB) from boot disk to 0x0000:0x8000
    mov di, 3                   ; Retry counter
.disk_read_loop:
    mov ax, 0x023C              ; AH=0x02 (read), AL=60 sectors (0x3C = 30KB)
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
    ; Zero out 24KB of paging structures at 0x1000..0x6FFF
    mov edi, 0x1000
    mov cr3, edi
    xor eax, eax
    mov ecx, 6144
    rep stosd

    ; PML4[0] -> PDPT (0x2000) (Present + Writable: 0x3)
    mov dword [0x1000], 0x2003

    ; PDPT[0..3] -> PDs at 0x3000, 0x4000, 0x5000, 0x6000 (0..4GB)
    mov dword [0x2000], 0x3003   ; 0..1 GB
    mov dword [0x2008], 0x4003   ; 1..2 GB
    mov dword [0x2010], 0x5003   ; 2..3 GB
    mov dword [0x2018], 0x6003   ; 3..4 GB

    ; Populate 2048 entries of 2MB huge pages across 0x3000..0x6FFF
    mov edi, 0x3000
    mov eax, 0x00000083         ; Present + Writable + Page Size (bit 7: 2MB huge page)
    mov ecx, 2048
.map_loop:
    mov [edi], eax
    add eax, 0x00200000          ; Next 2MB
    add edi, 8
    loop .map_loop
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

; --- 64-bit GDT (Minimal for kernel handoff) ---
gdt64_start:
    dq 0x0000000000000000               ; 0x00: Null descriptor
    dw 0x0000, 0x0000, 0x9A00, 0x0020   ; 0x08: Kernel Code (Ring 0, Long Mode)
    dw 0x0000, 0x0000, 0x9200, 0x0000   ; 0x10: Kernel Data (Ring 0)
gdt64_end:

gdt64_descriptor:
    dw gdt64_end - gdt64_start - 1
    dd gdt64_start

CODE_SEG_64 equ 0x08
DATA_SEG_64 equ 0x10

boot_drive:     db 0
msg_disk_fail:  db "Disk fail!", 0

; Pad up to 510 bytes, then append MBR boot signature 0xAA55
times 510 - ($ - $$) db 0
dw 0xAA55
