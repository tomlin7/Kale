; Kale OS stage 2 payload. Loaded by the BIOS boot sector at 0x8000.
[BITS 64]
[ORG 0x8000]
default abs

start:
    call serial_init
    mov rsi, msg_serial
    call serial_print
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

serial_init:
    mov dx, 0x3F9
    xor al, al
    out dx, al
    mov dx, 0x3FB
    mov al, 0x80
    out dx, al
    mov dx, 0x3F8
    mov al, 3
    out dx, al
    mov dx, 0x3F9
    xor al, al
    out dx, al
    mov dx, 0x3FB
    mov al, 3
    out dx, al
    mov dx, 0x3FA
    mov al, 0xC7
    out dx, al
    mov dx, 0x3FC
    mov al, 0x0B
    out dx, al
    ret

serial_print:
    lodsb
    test al, al
    jz .done
    mov dx, 0x3FD
.wait:
    in al, dx
    test al, 0x20
    jz .wait
    mov dx, 0x3F8
    mov al, [rsi - 1]
    out dx, al
    jmp serial_print
.done:
    ret

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
    push rcx
    push rdx
    in al, 0x60
    mov dl, al
    movzx ecx, byte [kbd_head]
    mov eax, ecx
    inc eax
    and eax, 31
    cmp al, [kbd_tail]
    je .ack
    mov [kbd_queue + rcx], dl
    mov [kbd_head], al
.ack:
    mov al, 0x20
    out 0x20, al
    pop rdx
    pop rcx
    pop rax
    iretq

msg_stage2: db " [KALE OS] STAGE2 LOADED - LONG MODE KERNEL HANDOFF READY ", 0
msg_serial: db "KALE OS stage2: serial, IDT, PIC, keyboard queue online", 13, 10, 0
kbd_head: db 0
kbd_tail: db 0
kbd_queue: times 32 db 0
align 8
idt_pointer:
    dw (34 * 16) - 1
    dq idt_table
idt_table:
    times 34 * 16 db 0

times 2048 - ($ - $$) db 0
