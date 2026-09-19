; ==============================================================================
; Kale OS 64-Bit Interrupt Service Routine (ISR) & IRQ Stubs
; Architecture : x86_64 Long Mode (Ring 0)
; ==============================================================================

[BITS 64]

; Export exception handlers (0-31)
global isr0, isr1, isr2, isr3, isr4, isr5, isr6, isr7
global isr8, isr9, isr10, isr11, isr12, isr13, isr14, isr15
global isr16, isr17, isr18, isr19, isr20, isr21, isr22, isr23
global isr24, isr25, isr26, isr27, isr28, isr29, isr30, isr31

; Export IRQ handlers (0-15)
global irq0, irq1, irq2, irq3, irq4, irq5, irq6, irq7
global irq8, irq9, irq10, irq11, irq12, irq13, irq14, irq15

; Export Syscall handler
global isr128

; Export common stubs & table & interrupt stats
global isr_common_stub
global irq_common_stub
global isr_stub_table
global isr_handler
global irq_handler
global timer_ticks
global interrupt_count
global kbd_buffer
global kbd_buf_head
global kbd_buf_tail
global kbd_buf_count

; ==============================================================================
; ISR / IRQ Entry Macros
; ==============================================================================

; Exception without CPU error code (pushes dummy error code 0)
%macro ISR_NOERRCODE 1
global isr%1
isr%1:
    push qword 0        ; Dummy error code
    push qword %1       ; Interrupt vector number
    jmp isr_common_stub
%endmacro

; Exception with CPU error code (CPU already pushed error code)
%macro ISR_ERRCODE 1
global isr%1
isr%1:
    push qword %1       ; Interrupt vector number
    jmp isr_common_stub
%endmacro

; Hardware IRQ entry (pushes dummy error code 0 and vector number 32 + irq_num)
%macro IRQ 2
global irq%1
irq%1:
    push qword 0        ; Dummy error code
    push qword %2       ; Interrupt vector number (32 + %1)
    jmp irq_common_stub
%endmacro

; ==============================================================================
; Common Exception Handler Stub
; ==============================================================================
isr_common_stub:
    ; Save all general-purpose registers (15 quadwords)
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

    ; Save data segment selector (zero-extended to 64-bit)
    mov ax, ds
    movzx rax, ax
    push rax

    ; Load kernel data segment selector (0x10)
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; Increment global interrupt counter
    inc qword [rel interrupt_count]

    ; Pass InterruptFrame pointer (rsp) in RDI (System V AMD64 ABI 1st parameter)
    mov rdi, rsp
    call isr_handler

    ; Restore data segment selector
    pop rax
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; Restore general-purpose registers
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

    ; Clean up error code and interrupt vector number (16 bytes)
    add rsp, 16

    iretq

; ==============================================================================
; Common IRQ Handler Stub
; ==============================================================================
irq_common_stub:
    ; Save all general-purpose registers (15 quadwords)
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

    ; Save data segment selector (zero-extended to 64-bit)
    mov ax, ds
    movzx rax, ax
    push rax

    ; Load kernel data segment selector (0x10)
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; Increment global interrupt counter
    inc qword [rel interrupt_count]

    ; Pass InterruptFrame pointer (rsp) in RDI
    mov rdi, rsp
    call irq_handler

    ; Restore data segment selector
    pop rax
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; Restore general-purpose registers
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

    ; Clean up error code and interrupt vector number (16 bytes)
    add rsp, 16

    iretq

; ==============================================================================
; Exception Handler Stubs (Vectors 0 - 31)
; ==============================================================================
ISR_NOERRCODE 0     ; 0: Divide-by-zero
ISR_NOERRCODE 1     ; 1: Debug
ISR_NOERRCODE 2     ; 2: Non-maskable Interrupt
ISR_NOERRCODE 3     ; 3: Breakpoint
ISR_NOERRCODE 4     ; 4: Overflow
ISR_NOERRCODE 5     ; 5: Bound Range Exceeded
ISR_NOERRCODE 6     ; 6: Invalid Opcode
ISR_NOERRCODE 7     ; 7: Device Not Available
ISR_ERRCODE   8     ; 8: Double Fault
ISR_NOERRCODE 9     ; 9: Coprocessor Segment Overrun
ISR_ERRCODE   10    ; 10: Invalid TSS
ISR_ERRCODE   11    ; 11: Segment Not Present
ISR_ERRCODE   12    ; 12: Stack-Segment Fault
ISR_ERRCODE   13    ; 13: General Protection Fault
ISR_ERRCODE   14    ; 14: Page Fault
ISR_NOERRCODE 15    ; 15: Reserved
ISR_NOERRCODE 16    ; 16: x87 Floating-Point Exception
ISR_ERRCODE   17    ; 17: Alignment Check
ISR_NOERRCODE 18    ; 18: Machine Check
ISR_NOERRCODE 19    ; 19: SIMD Floating-Point Exception
ISR_NOERRCODE 20    ; 20: Virtualization Exception
ISR_NOERRCODE 21    ; 21: Reserved
ISR_NOERRCODE 22    ; 22: Reserved
ISR_NOERRCODE 23    ; 23: Reserved
ISR_NOERRCODE 24    ; 24: Reserved
ISR_NOERRCODE 25    ; 25: Reserved
ISR_NOERRCODE 26    ; 26: Reserved
ISR_NOERRCODE 27    ; 27: Reserved
ISR_NOERRCODE 28    ; 28: Reserved
ISR_NOERRCODE 29    ; 29: Reserved
ISR_ERRCODE   30    ; 30: Security Exception
ISR_NOERRCODE 31    ; 31: Reserved

; ==============================================================================
; Hardware IRQ Stubs (IRQs 0-15 -> Vectors 32-47)
; ==============================================================================
IRQ 0, 32           ; IRQ 0: PIT Timer
IRQ 1, 33           ; IRQ 1: Keyboard
IRQ 2, 34           ; IRQ 2: Cascade
IRQ 3, 35           ; IRQ 3: COM2
IRQ 4, 36           ; IRQ 4: COM1
IRQ 5, 37           ; IRQ 5: LPT2
IRQ 6, 38           ; IRQ 6: Floppy
IRQ 7, 39           ; IRQ 7: LPT1
IRQ 8, 40           ; IRQ 8: RTC
IRQ 9, 41           ; IRQ 9: Peripherals
IRQ 10, 42          ; IRQ 10: Peripherals
IRQ 11, 43          ; IRQ 11: Peripherals
IRQ 12, 44          ; IRQ 12: Mouse
IRQ 13, 45          ; IRQ 13: FPU
IRQ 14, 46          ; IRQ 14: Primary ATA
IRQ 15, 47          ; IRQ 15: Secondary ATA

; ==============================================================================
; Reserved / Software Vectors (Vectors 48 - 127)
; ==============================================================================
%assign i 48
%rep 80
    ISR_NOERRCODE i
%assign i i+1
%endrep

; ==============================================================================
; System Call Stub (Vector 128 / 0x80)
; ==============================================================================
ISR_NOERRCODE 128

; ==============================================================================
; User / Extended Vectors (Vectors 129 - 255)
; ==============================================================================
%assign i 129
%rep 127
    ISR_NOERRCODE i
%assign i i+1
%endrep

; ==============================================================================
; Exception & IRQ High-Level Assembly Dispatch Handlers
; ==============================================================================
isr_handler:
    ; RDI points to InterruptFrame structure
    push rax
    push rbx
    push rsi

    mov rax, [rdi + 128]        ; Interrupt vector number (offset 128 = 0x80)

    ; Print Exception message to serial port
    mov rsi, msg_exc_prefix
    call serial_print

    ; Convert vector number to hex and print
    mov rbx, rax
    call serial_print_hex_byte

    mov rsi, msg_exc_error
    call serial_print
    mov rbx, [rdi + 136]        ; Error code (offset 136 = 0x88)
    call serial_print_hex_qword

    mov rsi, msg_exc_rip
    call serial_print
    mov rbx, [rdi + 144]        ; RIP (offset 144 = 0x90)
    call serial_print_hex_qword

    mov rsi, msg_newline
    call serial_print

    ; If syscall vector 128 (0x80)
    cmp rax, 128
    je .syscall_done

    ; If non-fatal breakpoint (vector 3) or debug (vector 1), return
    cmp rax, 3
    je .done
    cmp rax, 1
    je .done

    ; Fatal exception: halt system
    mov rsi, msg_exc_panic
    call serial_print
    cli
.panic_loop:
    hlt
    jmp .panic_loop

.syscall_done:
    nop
.done:
    pop rsi
    pop rbx
    pop rax
    ret

irq_handler:
    ; RDI points to InterruptFrame structure
    push rax
    push rbx
    push rcx

    mov rax, [rdi + 128]        ; Interrupt vector number

    cmp rax, 32                 ; IRQ 0 (Timer)
    je .handle_timer

    cmp rax, 33                 ; IRQ 1 (Keyboard)
    je .handle_keyboard

    jmp .send_eoi

.handle_timer:
    inc qword [rel timer_ticks]
    jmp .send_eoi

.handle_keyboard:
    in al, 0x60                 ; Read scancode from PS/2 controller
    test al, 0x80               ; Key release (break code)?
    jnz .send_eoi               ; Ignore release code for now
    movzx ecx, byte [rel kbd_buf_count]
    cmp ecx, 255
    jge .send_eoi               ; Buffer full
    movzx ebx, byte [rel kbd_buf_head]
    mov [kbd_buffer + rbx], al
    inc byte [rel kbd_buf_head]
    inc byte [rel kbd_buf_count]
    jmp .send_eoi

.send_eoi:
    ; Send EOI (0x20) to Master and/or Slave PIC
    cmp rax, 40                 ; IRQ 8..15 (vectors 40..47)
    jl .eoi_master
    mov al, 0x20
    out 0xA0, al                ; Slave PIC EOI
.eoi_master:
    mov al, 0x20
    out 0x20, al                ; Master PIC EOI

    pop rcx
    pop rbx
    pop rax
    ret

; Serial helper to print a byte in hex (BL = byte)
serial_print_hex_byte:
    push rax
    mov al, bl
    shr al, 4
    call .nibble
    mov al, bl
    and al, 0x0F
    call .nibble
    pop rax
    ret
.nibble:
    and al, 0x0F
    cmp al, 10
    jl .digit
    add al, 'A' - 10
    call serial_putc
    ret
.digit:
    add al, '0'
    call serial_putc
    ret

; Serial helper to print a quadword in hex (RBX = qword)
serial_print_hex_qword:
    push rcx
    push rbx
    mov rcx, 16
.loop:
    rol rbx, 4
    mov al, bl
    and al, 0x0F
    cmp al, 10
    jl .digit
    add al, 'A' - 10
    call serial_putc
    jmp .next
.digit:
    add al, '0'
    call serial_putc
.next:
    dec rcx
    jnz .loop
    pop rbx
    pop rcx
    ret

; ==============================================================================
; ISR Handler Pointer Table (256 Entries)
; ==============================================================================
align 16
isr_stub_table:
%assign i 0
%rep 256
    %if i >= 32 && i <= 47
        %assign irq_num (i - 32)
        dq irq%+irq_num
    %else
        dq isr%+i
    %endif
%assign i i+1
%endrep

; ==============================================================================
; Data Section for ISR Framework
; ==============================================================================
timer_ticks:        dq 0
interrupt_count:    dq 0

kbd_buf_head:       db 0
kbd_buf_tail:       db 0
kbd_buf_count:      db 0
kbd_buffer:         times 256 db 0

msg_exc_prefix:     db 13, 10, "[!] UNHANDLED EXCEPTION 0x", 0
msg_exc_error:      db " | Error Code: 0x", 0
msg_exc_rip:        db " | RIP: 0x", 0
msg_exc_panic:      db 13, 10, "[CRITICAL] System Halted due to Kernel Exception.", 13, 10, 0
msg_newline:        db 13, 10, 0
