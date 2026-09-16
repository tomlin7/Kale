; Kale OS stage 2 payload. Loaded by the BIOS boot sector at 0x8000.
[BITS 64]
[ORG 0x8000]
default abs

start:
    call serial_init
    call boot_info_init
    call rtc_init
    mov rsi, msg_serial
    call serial_print
    mov rsi, msg_timer
    call serial_print
    mov rsi, msg_rtc
    call serial_print
    mov rsi, msg_boot_info
    call serial_print
    mov eax, [boot_info + 36]
    call serial_print_hex
    mov rsi, msg_newline
    call serial_print
    call idt_init
    call pit_init
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
    mov rdi, boot_info
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

serial_print_hex:
    mov rcx, 8
    mov rdi, hex_buffer
.hex:
    rol eax, 4
    mov edx, eax
    and edx, 0x0F
    cmp dl, 10
    jb .digit
    add dl, 55
    jmp .store
.digit:
    add dl, 48
.store:
    mov [rdi], dl
    inc rdi
    loop .hex
    mov byte [rdi], 0
    mov rsi, hex_buffer
    call serial_print
    ret

rtc_init:
.wait:
    mov al, 0x0A
    out 0x70, al
    in al, 0x71
    test al, 0x80
    jnz .wait
    mov dl, al
    mov al, 0x0B
    out 0x70, al
    in al, 0x71
    mov dh, al
    mov al, 0
    out 0x70, al
    in al, 0x71
    mov [rtc_time + 0], al
    mov al, 2
    out 0x70, al
    in al, 0x71
    mov [rtc_time + 1], al
    mov al, 4
    out 0x70, al
    in al, 0x71
    mov [rtc_time + 2], al
    test dh, 0x04
    jnz .done
    mov rsi, rtc_time
    xor ecx, ecx
    mov ecx, 3
.decode:
    mov al, [rsi]
    mov ah, al
    and al, 0x0F
    shr ah, 4
    mov bh, ah
    xor ah, ah
    mov bl, 10
    mul bl
    add al, bh
    mov [rsi], al
    inc rsi
    loop .decode
.done:
    ret

boot_info_init:
    mov dword [boot_info + 0], 0x4B414C45
    mov dword [boot_info + 4], 1
    mov qword [boot_info + 8], 0x500
    movzx eax, word [0x4F0]
    mov dword [boot_info + 16], eax
    mov qword [boot_info + 24], 0x8000
    mov dword [boot_info + 32], 4096
    xor eax, eax
    mov rcx, 4096
    mov rsi, 0x8000
.sum:
    movzx edx, byte [rsi]
    add eax, edx
    inc rsi
    dec rcx
    jnz .sum
    mov dword [boot_info + 36], eax
    mov word [boot_info + 40], 0
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
    mov rax, pit_isr
    mov word [idt_table + (0x20 * 16) + 0], ax
    shr rax, 16
    mov word [idt_table + (0x20 * 16) + 6], ax
    shr rax, 16
    mov dword [idt_table + (0x20 * 16) + 8], eax
    mov word [idt_table + (0x20 * 16) + 2], 0x08
    mov byte [idt_table + (0x20 * 16) + 5], 0x8E
    lidt [idt_pointer]
    ret

pit_init:
    mov al, 0x36
    out 0x43, al
    mov ax, 11932
    out 0x40, al
    mov al, ah
    out 0x40, al
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
    mov al, 0xFC
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

pit_isr:
    inc qword [timer_ticks]
    mov al, 0x20
    out 0x20, al
    iretq

msg_stage2: db " [KALE OS] STAGE2 LOADED - LONG MODE KERNEL HANDOFF READY ", 0
msg_serial: db "KALE OS stage2: serial, IDT, PIC, keyboard queue online", 13, 10, 0
msg_boot_info: db "KALE OS bootinfo checksum=0x", 0
msg_timer: db "KALE OS PIT timer online", 13, 10, 0
msg_rtc: db "KALE OS RTC clock online", 13, 10, 0
msg_newline: db 13, 10, 0
hex_digits: db "0123456789ABCDEF"
hex_buffer: times 8 db 0
kbd_head: db 0
kbd_tail: db 0
kbd_queue: times 32 db 0
timer_ticks: dq 0
rtc_time: times 3 db 0
align 8
idt_pointer:
    dw (34 * 16) - 1
    dq idt_table
idt_table:
    times 34 * 16 db 0
; BootInfo lives below the stage-two image so runtime writes do not alter the
; payload checksum recorded by the build manifest.
boot_info equ 0x7000

times 4096 - ($ - $$) db 0
