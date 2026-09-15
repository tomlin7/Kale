; Kale OS stage 2 payload. Loaded by the BIOS boot sector at 0x8000.
[BITS 64]
[ORG 0x8000]

start:
    mov rdi, 0xB8000
    mov rsi, msg_stage2
    mov ah, 0x4F

.print:
    lodsb
    test al, al
    jz .halt
    mov [rdi], ax
    add rdi, 2
    jmp .print

.halt:
    cli
    hlt
    jmp .halt

msg_stage2: db " [KALE OS] STAGE2 LOADED - LONG MODE KERNEL HANDOFF READY ", 0

times 2048 - ($ - $$) db 0
