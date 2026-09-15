; Kale OS stage 2 payload. Loaded by the BIOS boot sector at 0x8000.
[BITS 64]
[ORG 0x8000]
default abs

start:
    call idt_init
    call pic_init
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
    sti
    hlt
    jmp .halt

; Install the keyboard gate (vector 0x21) in a compact IDT covering vectors
; 0..33. All other vectors remain masked until the linked kernel replaces it.
idt_init:
    mov rdi, idt_table
    mov rcx, 68
    xor eax, eax
    rep stosq
    mov rax, kbd_isr
    mov word [idt_table + (0x21 * 16) + 0], ax
    shr rax, 16
    mov word [idt_table + (0x21 * 16) + 6], ax
    shr rax, 16
    mov dword [idt_table + (0x21 * 16) + 8], eax
    mov word [idt_table + (0x21 * 16) + 2], 0x08
    mov byte [idt_table + (0x21 * 16) + 5], 0x8E
    lidt [idt_pointer]
    ret

pic_init:
    mov al, 0x11
    out 0x20, al
    out 0xA0, al
    mov al, 0x20
    out 0x21, al
    mov al, 0x28
    out 0xA1, al
    mov al, 0x04
    out 0x21, al
    mov al, 0x02
    out 0xA1, al
    mov al, 0x01
    out 0x21, al
    out 0xA1, al
    mov al, 0xFD
    out 0x21, al
    mov al, 0xFF
    out 0xA1, al
    ret

kbd_isr:
    push rax
    in al, 0x60
    mov [last_scancode], al
    mov al, 0x20
    out 0x20, al
    pop rax
    iretq

msg_stage2: db " [KALE OS] STAGE2 LOADED - LONG MODE KERNEL HANDOFF READY ", 0
last_scancode: db 0
align 8
idt_pointer:
    dw (34 * 16) - 1
    dq idt_table
idt_table:
    times 34 * 16 db 0

times 2048 - ($ - $$) db 0
