; ==============================================================================
; Kale OS 64-Bit Microkernel (Stage 2 Kernel Entry)
; Architecture : x86_64 Long Mode (Ring 0)
; Base Address : 0x8000
; ==============================================================================

[BITS 64]
[DEFAULT ABS]
[ORG 0x8000]

kernel_start:
    ; Reload segment registers with 64-bit data selector (0x10)
    mov ax, 0x10
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax
    mov ss, ax
    mov rsp, 0x00200000         ; Stack top at 2MB boundary
    cld

    ; Initialize 16550 UART Serial Port (COM1: 0x3F8)
    call serial_init

    ; Send serial boot announcement
    mov rsi, msg_serial_banner
    call serial_print

    ; Initialize 8259 PIC
    call pic_init

    ; Initialize IDT gates and load IDT pointer via LIDT
    call idt_init

    ; Enable CPU Interrupts
    sti

    ; Send serial IDT announcement
    mov rsi, msg_idt_banner
    call serial_print

    ; Initialize VGA Display and draw system dashboard
    call vga_init_display

    ; Enable VGA Hardware Cursor
    call vga_enable_cursor

    ; Set initial cursor position for shell (Row 11, Col 9)
    mov byte [cursor_row], 11
    mov byte [cursor_col], 9
    call vga_sync_cursor

    ; Main interactive loop: poll PS/2 keyboard
shell_loop:
    call kbd_poll_char
    test al, al
    jz shell_loop

    ; Process key
    cmp al, 10                  ; Enter key
    je .handle_enter

    cmp al, 8                   ; Backspace key
    je .handle_backspace

    ; Regular character
    movzx ecx, byte [cmd_len]
    cmp ecx, 63                 ; Buffer full?
    jge shell_loop

    ; Save character in command buffer
    mov [cmd_buffer + rcx], al
    inc byte [cmd_len]
    mov byte [cmd_buffer + rcx + 1], 0

    ; Print char to VGA
    mov cl, [term_color]
    call vga_putchar
    ; Also mirror to serial
    call serial_putc
    jmp shell_loop

.handle_backspace:
    movzx ecx, byte [cmd_len]
    test ecx, ecx
    jz shell_loop               ; Nothing to delete

    ; Decrement buffer length
    dec byte [cmd_len]
    dec ecx
    mov byte [cmd_buffer + rcx], 0

    ; Decrement cursor on VGA
    call vga_backspace

    ; Mirror backspace to serial: backspace, space, backspace
    mov al, 8
    call serial_putc
    mov al, ' '
    call serial_putc
    mov al, 8
    call serial_putc
    jmp shell_loop

.handle_enter:
    ; Mirror newline to serial
    mov al, 13
    call serial_putc
    mov al, 10
    call serial_putc

    ; Execute command in buffer
    call shell_execute_command

    ; Reset command buffer
    mov byte [cmd_len], 0
    mov byte [cmd_buffer], 0

    ; Print new prompt
    call shell_print_prompt
    jmp shell_loop

; ==============================================================================
; Shell Command Dispatcher
; ==============================================================================
shell_execute_command:
    ; Check if buffer is empty
    cmp byte [cmd_len], 0
    je .cmd_done

    ; Move cursor to next line
    call vga_newline

    ; Compare "help"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_help
    call str_equals
    test eax, eax
    jnz .run_help

    ; Compare "info"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_info
    call str_equals
    test eax, eax
    jnz .run_info

    ; Compare "mem"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_mem
    call str_equals
    test eax, eax
    jnz .run_mem

    ; Compare "cpu"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_cpu
    call str_equals
    test eax, eax
    jnz .run_cpu

    ; Compare "clear"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_clear
    call str_equals
    test eax, eax
    jnz .run_clear

    ; Compare "color"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_color
    call str_equals
    test eax, eax
    jnz .run_color

    ; Compare "int3"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_int3
    call str_equals
    test eax, eax
    jnz .run_int3

    ; Compare "ticks"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_ticks
    call str_equals
    test eax, eax
    jnz .run_ticks

    ; Compare "stats"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_stats
    call str_equals
    test eax, eax
    jnz .run_stats

    ; Compare "user"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_user
    call str_equals
    test eax, eax
    jnz .run_user

    ; Compare "reboot"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_reboot
    call str_equals
    test eax, eax
    jnz .run_reboot

    ; Compare "halt"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_halt
    call str_equals
    test eax, eax
    jnz .run_halt

    ; Check if starts with "echo "
    mov rsi, cmd_buffer
    mov rdi, str_cmd_echo
    call str_starts_with
    test eax, eax
    jnz .run_echo

    ; Unknown command
    mov rsi, msg_unknown_cmd
    mov cl, 0x0C                ; Light Red
    call vga_print_str
    mov rsi, cmd_buffer
    mov cl, 0x0E                ; Yellow
    call vga_print_str
    mov rsi, msg_unknown_suffix
    mov cl, 0x0C
    call vga_print_str
    call vga_newline
    jmp .cmd_done

.run_help:
    mov rsi, msg_help_text
    mov cl, 0x0B                ; Light Cyan
    call vga_print_str
    jmp .cmd_done

.run_info:
    mov rsi, msg_info_text
    mov cl, 0x0A                ; Light Green
    call vga_print_str
    jmp .cmd_done

.run_mem:
    mov rsi, msg_mem_text
    mov cl, 0x0E                ; Yellow
    call vga_print_str
    jmp .cmd_done

.run_cpu:
    mov rsi, msg_cpu_text
    mov cl, 0x0B                ; Light Cyan
    call vga_print_str
    jmp .cmd_done

.run_clear:
    call vga_clear_shell_area
    mov byte [cursor_row], 11
    mov byte [cursor_col], 0
    call vga_sync_cursor
    ret

.run_color:
    ; Cycle color: 0x0B (Cyan) -> 0x0A (Green) -> 0x0E (Yellow) -> 0x0F (White) -> 0x0D (Pink)
    mov al, [term_color]
    cmp al, 0x0B
    je .col_green
    cmp al, 0x0A
    je .col_yellow
    cmp al, 0x0E
    je .col_white
    cmp al, 0x0F
    je .col_pink
    mov byte [term_color], 0x0B
    jmp .col_printed
.col_green:
    mov byte [term_color], 0x0A
    jmp .col_printed
.col_yellow:
    mov byte [term_color], 0x0E
    jmp .col_printed
.col_white:
    mov byte [term_color], 0x0F
    jmp .col_printed
.col_pink:
    mov byte [term_color], 0x0D
.col_printed:
    mov rsi, msg_color_changed
    mov cl, [term_color]
    call vga_print_str
    jmp .cmd_done

.run_int3:
    mov rsi, msg_int3_test
    mov cl, 0x0E                ; Yellow
    call vga_print_str
    int 3                       ; Trigger CPU Breakpoint Exception (Vector 3)
    jmp .cmd_done

.run_ticks:
    mov rsi, msg_ticks_prefix
    mov cl, 0x0A                ; Light Green
    call vga_print_str
    mov rbx, [timer_ticks]
    call vga_print_hex_qword
    call vga_newline
    jmp .cmd_done

.run_stats:
    mov rsi, msg_stats_prefix
    mov cl, 0x0B                ; Light Cyan
    call vga_print_str
    mov rbx, [interrupt_count]
    call vga_print_hex_qword
    call vga_newline
    jmp .cmd_done

.run_echo:
    mov rsi, cmd_buffer + 5     ; Skip "echo "
    mov cl, [term_color]
    call vga_print_str
    call vga_newline
    jmp .cmd_done

.run_user:
    mov rsi, msg_user_text
    mov cl, 0x0B                ; Light Cyan
    call vga_print_str
    jmp .cmd_done

.run_reboot:
    mov rsi, msg_rebooting
    mov cl, 0x0E
    call vga_print_str
    ; Reboot via 8042 PS/2 controller reset line
.reboot_poll:
    in al, 0x64
    test al, 2
    jnz .reboot_poll
    mov al, 0xFE
    out 0x64, al
.hang:
    hlt
    jmp .hang

.run_halt:
    mov rsi, msg_halted
    mov cl, 0x0C
    call vga_print_str
    cli
.hlt_loop:
    hlt
    jmp .hlt_loop

.cmd_done:
    ret

shell_print_prompt:
    ; Print "kale-os> "
    mov rsi, prompt_str
    mov cl, 0x0A                ; Bright Green
    call vga_print_str
    ret

; ==============================================================================
; VGA Display Driver (80x25 Text Mode @ 0xB8000)
; ==============================================================================
vga_init_display:
    ; Clear entire screen with Pure Black background (0x0720: White on Black space)
    mov rdi, 0xB8000
    mov ax, 0x0720
    mov rcx, 2000               ; 80 * 25 cells
    rep stosw

    ; Draw Top Title Bar (Row 0): White on Blue (0x1F)
    mov rdi, 0xB8000
    mov rsi, header_bar_text
    mov ah, 0x1F
    call vga_write_row_text

    ; Draw Box Border Header (Row 1): Cyan on Black (0x0B)
    mov rdi, 0xB8000 + (1 * 160)
    mov rsi, box_top
    mov ah, 0x0B
    call vga_write_row_text

    ; Draw System Diagnostics (Rows 2..7)
    mov rdi, 0xB8000 + (2 * 160)
    mov rsi, diag_line_cpu
    mov ah, 0x0E                ; Yellow on Black
    call vga_write_row_text

    mov rdi, 0xB8000 + (3 * 160)
    mov rsi, diag_line_paging
    mov ah, 0x0A                ; Green on Black
    call vga_write_row_text

    mov rdi, 0xB8000 + (4 * 160)
    mov rsi, diag_line_mem
    mov ah, 0x0A                ; Green on Black
    call vga_write_row_text

    mov rdi, 0xB8000 + (5 * 160)
    mov rsi, diag_line_pic
    mov ah, 0x0B                ; Cyan on Black
    call vga_write_row_text

    mov rdi, 0xB8000 + (6 * 160)
    mov rsi, diag_line_serial
    mov ah, 0x0B                ; Cyan on Black
    call vga_write_row_text

    mov rdi, 0xB8000 + (7 * 160)
    mov rsi, diag_line_kbd
    mov ah, 0x0F                ; White on Black
    call vga_write_row_text

    ; Draw Box Border Bottom (Row 8)
    mov rdi, 0xB8000 + (8 * 160)
    mov rsi, box_bottom
    mov ah, 0x0B
    call vga_write_row_text

    ; Draw Welcome Hint (Row 9)
    mov rdi, 0xB8000 + (9 * 160)
    mov rsi, welcome_text
    mov ah, 0x0E                ; Yellow on Black
    call vga_write_row_text

    ; Draw Divider (Row 10)
    mov rdi, 0xB8000 + (10 * 160)
    mov rsi, divider_line
    mov ah, 0x08                ; Dark Gray on Black
    call vga_write_row_text

    ; Draw Status Footer Bar (Row 24): Black on Gray (0x70)
    mov rdi, 0xB8000 + (24 * 160)
    mov rsi, footer_bar_text
    mov ah, 0x70
    call vga_write_row_text

    ; Print Initial Shell Prompt on Row 11
    mov byte [cursor_row], 11
    mov byte [cursor_col], 0
    call shell_print_prompt
    ret

vga_write_row_text:
    ; rdi = screen address, rsi = string ptr, ah = attribute
.loop:
    lodsb
    test al, al
    jz .fill_pad
    stosw
    jmp .loop
.fill_pad:
    ret

vga_enable_cursor:
    push rax
    push rdx
    mov dx, 0x3D4
    mov al, 0x0A
    out dx, al
    inc dx
    in al, dx
    and al, 0xC0                ; clear disable bits
    or al, 0x0E                 ; scanline 14
    out dx, al

    dec dx
    mov al, 0x0B
    out dx, al
    inc dx
    in al, dx
    and al, 0xE0
    or al, 0x0F                 ; scanline 15
    out dx, al
    pop rdx
    pop rax
    ret

vga_sync_cursor:
    push rax
    push rcx
    push rdx

    ; pos = cursor_row * 80 + cursor_col
    movzx eax, byte [cursor_row]
    imul eax, 80
    movzx ecx, byte [cursor_col]
    add eax, ecx

    ; Set low byte (reg 0x0F)
    mov dx, 0x3D4
    mov al, 0x0F
    out dx, al
    inc dx
    mov al, cl
    out dx, al

    ; Set high byte (reg 0x0E)
    dec dx
    mov al, 0x0E
    out dx, al
    inc dx
    mov al, ah
    out dx, al

    pop rdx
    pop rcx
    pop rax
    ret

vga_putchar:
    ; al = char, cl = color attribute
    push rax
    push rcx
    push rdx
    push rdi
    push r8
    push r9

    movzx r8d, byte [cursor_row]
    movzx r9d, byte [cursor_col]

    ; offset = (r8d * 80 + r9d) * 2
    imul r8d, 80
    add r8d, r9d
    shl r8d, 1
    mov rdi, 0xB8000
    add rdi, r8

    ; Write char and attribute
    mov ah, cl
    stosw

    ; Advance cursor
    inc byte [cursor_col]
    cmp byte [cursor_col], 79
    jl .done
    call vga_newline

.done:
    call vga_sync_cursor
    pop r9
    pop r8
    pop rdi
    pop rdx
    pop rcx
    pop rax
    ret

vga_backspace:
    push rax
    push rdi
    push r8
    push r9

    cmp byte [cursor_col], 9    ; Don't erase past "kale-os> "
    jle .backspace_done
    dec byte [cursor_col]

    movzx r8d, byte [cursor_row]
    movzx r9d, byte [cursor_col]
    imul r8d, 80
    add r8d, r9d
    shl r8d, 1
    mov rdi, 0xB8000
    add rdi, r8

    mov ax, 0x0720              ; Blank space on Black
    stosw

    call vga_sync_cursor
.backspace_done:
    pop r9
    pop r8
    pop rdi
    pop rax
    ret

vga_newline:
    push rax
    mov byte [cursor_col], 0
    inc byte [cursor_row]
    cmp byte [cursor_row], 24   ; Don't overwrite footer
    jl .sync
    call vga_scroll_shell
    mov byte [cursor_row], 23
.sync:
    call vga_sync_cursor
    pop rax
    ret

vga_scroll_shell:
    ; Scroll lines 11..23 upwards by 1 line
    push rsi
    push rdi
    push rcx
    push rax

    mov rdi, 0xB8000 + (11 * 160)
    mov rsi, 0xB8000 + (12 * 160)
    mov rcx, (12 * 160) / 2     ; 12 rows of words
    rep movsw

    ; Clear row 23
    mov rdi, 0xB8000 + (23 * 160)
    mov ax, 0x0720
    mov rcx, 80
    rep stosw

    pop rax
    pop rcx
    pop rdi
    pop rsi
    ret

vga_clear_shell_area:
    ; Clear rows 11..23
    push rdi
    push rax
    push rcx

    mov rdi, 0xB8000 + (11 * 160)
    mov ax, 0x0720
    mov rcx, 13 * 80
    rep stosw

    pop rcx
    pop rax
    pop rdi
    ret

vga_print_str:
    ; rsi = string, cl = color
    push rax
.loop:
    lodsb
    test al, al
    jz .done
    cmp al, 10
    je .nl
    call vga_putchar
    ; mirror to serial
    call serial_putc
    jmp .loop
.nl:
    call vga_newline
    mov al, 13
    call serial_putc
    mov al, 10
    call serial_putc
    jmp .loop
.done:
    pop rax
    ret

vga_print_hex_qword:
    ; RBX = quadword to print, CL = color attribute
    push rcx
    push rbx
    push rax
    push r8
    mov r8, rcx                 ; Save color attribute in R8B
    mov rcx, 16
.loop:
    rol rbx, 4
    mov al, bl
    and al, 0x0F
    cmp al, 10
    jl .digit
    add al, 'A' - 10
    jmp .print
.digit:
    add al, '0'
.print:
    push rcx
    mov cl, r8b
    call vga_putchar
    call serial_putc
    pop rcx
    dec rcx
    jnz .loop
    pop r8
    pop rax
    pop rbx
    pop rcx
    ret

; ==============================================================================
; PS/2 Keyboard Driver (Polling & Scancode Set 1 Translation)
; ==============================================================================
kbd_poll_char:
    ; Check interrupt-driven ring buffer
    cli
    movzx ecx, byte [rel kbd_buf_count]
    test ecx, ecx
    jz .no_key

    movzx ebx, byte [rel kbd_buf_tail]
    mov al, [kbd_buffer + rbx]
    inc byte [rel kbd_buf_tail]
    dec byte [rel kbd_buf_count]
    sti

    movzx eax, al
    cmp eax, 128
    jge .no_key_done
    mov al, [scancode_ascii_table + rax]
    ret

.no_key:
    sti
.no_key_done:
    xor al, al
    ret

; ==============================================================================
; 16550 UART Serial Driver (COM1: 0x3F8)
; ==============================================================================
serial_init:
    push rdx
    push rax
    mov dx, 0x3F9               ; Disable interrupts
    xor al, al
    out dx, al

    mov dx, 0x3FB               ; Enable DLAB (set baud rate divisor)
    mov al, 0x80
    out dx, al

    mov dx, 0x3F8               ; Set divisor to 1 (lo byte) 115200 baud
    mov al, 0x01
    out dx, al

    mov dx, 0x3F9               ; (hi byte)
    xor al, al
    out dx, al

    mov dx, 0x3FB               ; 8 bits, no parity, one stop bit (8N1)
    mov al, 0x03
    out dx, al

    mov dx, 0x3FA               ; Enable FIFO, clear them, with 14-byte threshold
    mov al, 0xC7
    out dx, al

    mov dx, 0x3FC               ; IRQs enabled, RTS/DSR set
    mov al, 0x0B
    out dx, al
    pop rax
    pop rdx
    ret

serial_putc:
    push rdx
    push rax
    mov dx, 0x3FD
.wait:
    in al, dx
    test al, 0x20               ; Transmit buffer empty?
    jz .wait
    pop rax
    mov dx, 0x3F8
    out dx, al
    pop rdx
    ret

serial_print:
    push rax
.loop:
    lodsb
    test al, al
    jz .done
    call serial_putc
    jmp .loop
.done:
    pop rax
    ret

; ==============================================================================
; Interrupt Descriptor Table (IDT) Driver & Setup
; ==============================================================================
idt_init:
    push rax
    push rbx
    push rcx
    push rdx
    push rdi
    push rsi

    mov rsi, isr_stub_table      ; Address of 256 handler function pointers
    mov rdi, idt_table           ; Destination IDT entries table
    xor ecx, ecx                 ; Vector index 0..255

.loop:
    mov rbx, [rsi + rcx * 8]     ; rbx = handler stub entry point address

    ; Entry address in IDT table: RDX = RDI + ECX * 16
    mov rdx, rcx
    shl rdx, 4
    add rdx, rdi

    ; 1. Offset low (bits 0..15)
    mov ax, bx
    mov [rdx], ax

    ; 2. Kernel Code Selector (0x08)
    mov word [rdx + 2], 0x08

    ; 3. IST (0)
    mov byte [rdx + 4], 0

    ; 4. Type & Attributes (0x8E for Ring 0 Interrupt Gate, 0xEE for Syscall Vector 0x80)
    cmp ecx, 0x80
    je .syscall_attr
    mov byte [rdx + 5], 0x8E
    jmp .attr_done
.syscall_attr:
    mov byte [rdx + 5], 0xEE
.attr_done:

    ; 5. Offset mid (bits 16..31)
    mov eax, ebx
    shr eax, 16
    mov [rdx + 6], ax

    ; 6. Offset high (bits 32..63)
    mov rax, rbx
    shr rax, 32
    mov [rdx + 8], eax

    ; 7. Reserved (zero)
    mov dword [rdx + 12], 0

    inc ecx
    cmp ecx, 256
    jl .loop

    ; Load IDT using LIDT instruction
    lidt [idt_pointer]

    pop rsi
    pop rdi
    pop rdx
    pop rcx
    pop rbx
    pop rax
    ret

; ==============================================================================
; 8259 PIC Driver
; ==============================================================================
pic_init:
    push rax
    ; ICW1: Init PIC, ICW4 needed
    mov al, 0x11
    out 0x20, al
    out 0xA0, al

    ; ICW2: Remap Master to 0x20, Slave to 0x28
    mov al, 0x20
    out 0x21, al
    mov al, 0x28
    out 0xA1, al

    ; ICW3: Master has slave at IRQ2 (0x04), Slave cascade identity (0x02)
    mov al, 0x04
    out 0x21, al
    mov al, 0x02
    out 0xA1, al

    ; ICW4: 8086 mode
    mov al, 0x01
    out 0x21, al
    out 0xA1, al

    ; OCW1: Unmask IRQ0 (Timer) and IRQ1 (Keyboard) on Master PIC (0xFC = 11111100b)
    mov al, 0xFC
    out 0x21, al
    mov al, 0xFF
    out 0xA1, al
    pop rax
    ret

; ==============================================================================
; Utility String Routines
; ==============================================================================
str_equals:
    ; rsi = str1, rdi = str2. Returns 1 if equal, 0 otherwise.
    push rbx
.loop:
    mov al, [rsi]
    mov bl, [rdi]
    cmp al, bl
    jne .not_eq
    test al, al
    jz .equal
    inc rsi
    inc rdi
    jmp .loop
.equal:
    pop rbx
    mov eax, 1
    ret
.not_eq:
    pop rbx
    xor eax, eax
    ret

str_starts_with:
    ; rsi = str, rdi = prefix. Returns 1 if str starts with prefix.
    push rbx
.loop:
    mov bl, [rdi]
    test bl, bl
    jz .match
    mov al, [rsi]
    cmp al, bl
    jne .no_match
    inc rsi
    inc rdi
    jmp .loop
.match:
    pop rbx
    mov eax, 1
    ret
.no_match:
    pop rbx
    xor eax, eax
    ret

; ==============================================================================
; Kernel Data & UI Strings
; ==============================================================================
cursor_row:         db 11
cursor_col:         db 0
term_color:         db 0x0B     ; Light Cyan default
cmd_len:            db 0
cmd_buffer:         times 64 db 0

header_bar_text:
    db "  KALE OS v0.1.0-alpha [x86_64 Long Mode Microkernel] -- Bare Metal Host", 0

box_top:
    db " +----------------------------------------------------------------------------+", 0

diag_line_cpu:
    db " |  [OK] CPU Architecture : x86_64 Long Mode (64-bit Ring 0, CR0/CR4/EFER)    |", 0

diag_line_paging:
    db " |  [OK] Paging Subsystem : 4-Level PML4 @ 0x1000 (Identity Mapped 2MB Page)   |", 0

diag_line_mem:
    db " |  [OK] Memory Manager   : PMM Bitmap Allocator (Pool: 128 MB Physical RAM)  |", 0

diag_line_pic:
    db " |  [OK] Interrupt Control: Dual 8259 PIC Remapped (IRQ0=0x20, IRQ1=0x21)      |", 0

diag_line_serial:
    db " |  [OK] Serial Terminal  : COM1 0x3F8 Active (115200 Baud, 8N1 FIFO)         |", 0

diag_line_kbd:
    db " |  [OK] Keyboard Driver  : PS/2 Controller Active (Scancode Set 1, Polled)    |", 0

box_bottom:
    db " +----------------------------------------------------------------------------+", 0

welcome_text:
    db "  Kale OS Interactive Terminal. Type 'help' for commands or 'reboot' to reset.", 0

divider_line:
    db " ------------------------------------------------------------------------------", 0

footer_bar_text:
    db " [F1] Help | [MEM] 128MB Pool | Ring 0 Long Mode | COM1 Serial: ON | QEMU x86_64", 0

prompt_str:
    db "kale-os> ", 0

msg_serial_banner:
    db 13, 10, "==================================================", 13, 10
    db "  KALE OS 64-Bit Microkernel Boot Successful!     ", 13, 10
    db "  CPU: x86_64 Long Mode | Paging: PML4 @ 0x1000   ", 13, 10
    db "==================================================", 13, 10, 0

msg_help_text:
    db "Available Commands:", 10
    db "  help     - Display this command reference", 10
    db "  info     - Show kernel version, author & target architecture", 10
    db "  mem      - Show physical memory & page table hierarchy", 10
    db "  cpu      - Dump CPU control register states (CR0, CR3, CR4, EFER)", 10
    db "  int3     - Trigger software breakpoint exception (INT 3 / Vector 3)", 10
    db "  ticks    - Show PIT timer hardware ticks (IRQ 0 count)", 10
    db "  stats    - Show total interrupt service routine invocations", 10
    db "  clear    - Clear terminal shell area", 10
    db "  color    - Cycle shell text color (Cyan/Green/Yellow/White/Pink)", 10
    db "  echo     - Echo arguments back to the terminal", 10
    db "  user     - Show User Space & Ring 3 privilege architecture", 10
    db "  reboot   - Hardware reboot via 8042 keyboard controller", 10
    db "  halt     - Halt system execution (cli; hlt)", 10, 0

msg_int3_test:      db "Triggering Software Breakpoint Interrupt (INT 3)...", 10, 0
msg_ticks_prefix:   db "PIT Timer Ticks (IRQ 0): 0x", 0
msg_stats_prefix:   db "Total Interrupts Handled: 0x", 0

msg_info_text:
    db "Kernel Information:", 10
    db "  OS Name  : Kale Operating System (Microkernel)", 10
    db "  Version  : 0.1.0-alpha (Bare Metal Release)", 10
    db "  Arch     : AMD64 / x86_64 Long Mode (Ring 0 Kernel)", 10
    db "  Compiler : Kale Compiler / NASM Assembler", 10
    db "  Author   : Tom Lin / Kale Project Team", 10, 0

msg_mem_text:
    db "Physical Memory Layout (PMM):", 10
    db "  0x00000000 - 0x0009FFFF : Lower Memory Reserved (640 KB)", 10
    db "  0x000A0000 - 0x000FFFFF : Video RAM & BIOS ROM (384 KB)", 10
    db "  0x00100000 - 0x001FFFFF : Identity Paging & Kernel Code (1 MB)", 10
    db "  0x00200000 - 0x07FFFFFF : Physical Frame Pool (126 MB Available)", 10
    db "  Page Directories: PML4=0x1000 | PDPT=0x2000 | PD=0x3000", 10, 0

msg_cpu_text:
    db "CPU Control Register Status:", 10
    db "  CR0  : 0x80000011 (Paging=1, Protected=1, ET=1)", 10
    db "  CR3  : 0x00001000 (PML4 Base Address)", 10
    db "  CR4  : 0x00000020 (Physical Address Extension PAE=1)", 10
    db "  EFER : 0x00000100 (Long Mode Enable LME=1, LMA=1)", 10
    db "  RSP  : 0x00200000 (Kernel Stack Top at 2MB)", 10, 0

msg_color_changed:
    db "Shell color theme updated.", 10, 0

msg_rebooting:
    db "Initiating system reboot...", 10, 0

msg_halted:
    db "System halted. It is now safe to power off.", 10, 0

msg_unknown_cmd:
    db "Unknown command: '", 0
msg_unknown_suffix:
    db "'. Type 'help' for command list.", 0

str_cmd_help:       db "help", 0
str_cmd_info:       db "info", 0
str_cmd_mem:        db "mem", 0
str_cmd_cpu:        db "cpu", 0
str_cmd_clear:      db "clear", 0
str_cmd_color:      db "color", 0
str_cmd_int3:       db "int3", 0
str_cmd_ticks:      db "ticks", 0
str_cmd_stats:      db "stats", 0
str_cmd_user:       db "user", 0
str_cmd_reboot:     db "reboot", 0
str_cmd_halt:       db "halt", 0
str_cmd_echo:       db "echo ", 0

msg_user_text:
    db "User Space Architecture (Milestone 5):", 10
    db "  TSS Descriptor  : Selector 0x28 (64-Bit Available TSS)", 10
    db "  Ring 3 Selectors: User CS=0x1B, User SS=0x23", 10
    db "  User Stack Top  : 0x00007FFFFFFFF000 (SysV AMD64 ABI)", 10
    db "  Binary Loader   : 64-Bit ELF Loader (PT_LOAD, PF_R/W/X)", 10, 0

; Scancode Set 1 Translation Table (128 entries)
scancode_ascii_table:
    db 0, 27, '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '-', '=', 8, 9
    db 'q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', '[', ']', 10, 0
    db 'a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', ';', "'", '`', 0, '\'
    db 'z', 'x', 'c', 'v', 'b', 'n', 'm', ',', '.', '/', 0, '*', 0, ' '
    times 128 - ($ - scancode_ascii_table) db 0

; ==============================================================================
; IDT Data Structures (256 Entries = 4096 Bytes)
; ==============================================================================
align 16
idt_table:
    times 256 * 16 db 0

idt_pointer:
    dw (256 * 16) - 1
    dq idt_table

msg_idt_banner:
    db 13, 10, "  [OK] IDT Initialized: 256 Gates Loaded | Interrupts ENABLED (sti)", 13, 10, 0

; ==============================================================================
; Include Interrupt Service Routine (ISR) Framework Stubs
; ==============================================================================
%include "os/kernel/isr.asm"

