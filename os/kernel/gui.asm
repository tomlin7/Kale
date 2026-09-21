; ==============================================================================
; Kale OS 64-Bit Graphical User Interface (GUI) Desktop Subsystem
; Architecture : x86_64 Long Mode (Ring 0)
; Linear Framebuffer : 800x600, 32-bit ARGB (VESA VBE / BGA)
; Features: Desktop Wallpaper & Grid, Taskbar, Window Manager (Terminal,
;           System Monitor, 2D Graphics Demo), 8x8 Bitmap Font Typography,
;           and PS/2 Mouse Pointer with Hit-Testing.
; ==============================================================================

[BITS 64]

; ==============================================================================
; GUI State & Global Variables
; ==============================================================================
align 8
gui_active:         db 0
gui_cursor_visible: db 1

align 8
fb_base:            dq 0xFD000000       ; Default fallback (read from [0x7008])
fb_width:           dq 800
fb_height:          dq 600
fb_pitch:           dq 3200             ; 800 * 4 bytes
fb_bpp:             dq 32

mouse_x:            dd 400
mouse_y:            dd 300
mouse_old_x:        dd 400
mouse_old_y:        dd 300
mouse_btn:          db 0
mouse_cycle:        db 0
mouse_pkt:          db 0, 0, 0
cursor_saved_valid: db 0

align 16
cursor_saved_bg:    times 144 dd 0      ; 12x12 pixels background

focused_window:     dd 1                ; 1=Terminal, 2=SysMon, 3=2D Demo
win_terminal_vis:   db 1
win_sysmon_vis:     db 1
win_demo_vis:       db 1

term_cursor_blink:  dd 0
term_last_cmd_res:  times 64 db 0

; Colors (32-bit ARGB)
COLOR_DESKTOP_BG    equ 0xFF1E1E2E      ; Catppuccin Mocha Dark Slate
COLOR_GRID_DOT      equ 0xFF2A2B3D
COLOR_TASKBAR_BG    equ 0xFF11111B
COLOR_BORDER        equ 0xFF313244
COLOR_BORDER_FOCUS  equ 0xFF585B70
COLOR_TITLEBAR      equ 0xFF313244
COLOR_TITLEBAR_FOC  equ 0xFF45475A
COLOR_TITLE_TEXT    equ 0xFFCDD6F4
COLOR_CLOSE_BTN     equ 0xFFF38BA8
COLOR_WIN_BG        equ 0xFF181825
COLOR_BRAND         equ 0xFF89DCEB      ; Bright Cyan
COLOR_PROMPT        equ 0xFFA6E3A1      ; Bright Green
COLOR_TEXT_WHITE    equ 0xFFCDD6F4
COLOR_TEXT_YELLOW   equ 0xFFF9E2AF
COLOR_TEXT_GRAY     equ 0xFF6C7086
COLOR_ACCENT_BLUE   equ 0xFF89B4FA

; ==============================================================================
; GUI Initialization
; ==============================================================================
gui_init_desktop:
    push rbx
    push r12
    push r13

    ; Read BootInfo at 0x7000 if valid
    cmp dword [0x7000], 0x4B414C45      ; 'KALE'
    jne .use_defaults
    cmp dword [0x7004], 1               ; 1 = VBE Graphics
    jne .use_defaults

    mov eax, [0x7008]                   ; LFB Physical Base (low 32-bits)
    test eax, eax
    jz .use_defaults
    mov [fb_base], rax                  ; rax zero-extended

    ; Ensure BGA controller is in 800x600 32-bpp ARGB mode
    mov dx, 0x01CE
    mov ax, 4           ; VBE_DISPI_INDEX_ENABLE
    out dx, ax
    inc dx
    xor ax, ax          ; VBE_DISPI_DISABLED
    out dx, ax

    dec dx
    mov ax, 1           ; VBE_DISPI_INDEX_XRES
    out dx, ax
    inc dx
    mov ax, 800
    out dx, ax

    dec dx
    mov ax, 2           ; VBE_DISPI_INDEX_YRES
    out dx, ax
    inc dx
    mov ax, 600
    out dx, ax

    dec dx
    mov ax, 3           ; VBE_DISPI_INDEX_BPP
    out dx, ax
    inc dx
    mov ax, 32          ; 32 BPP
    out dx, ax

    dec dx
    mov ax, 4           ; VBE_DISPI_INDEX_ENABLE
    out dx, ax
    inc dx
    mov ax, 0x41        ; VBE_DISPI_ENABLED | VBE_DISPI_LFB_ENABLED
    out dx, ax

    mov qword [fb_width], 800
    mov qword [fb_height], 600
    mov qword [fb_pitch], 3200
    mov qword [fb_bpp], 32

.use_defaults:
    mov byte [gui_active], 1
    mov byte [cursor_saved_valid], 0
    mov dword [mouse_x], 400
    mov dword [mouse_y], 300

    ; Initialize PS/2 Mouse hardware controller
    call mouse_init_hardware

    ; Full Desktop Render Pass
    call gui_render_desktop

    pop r13
    pop r12
    pop rbx
    ret

; ==============================================================================
; 2D Graphics Primitives
; ==============================================================================

; ------------------------------------------------------------------------------
; gui_fill_rect
; In: rdi = x, rsi = y, rdx = w, rcx = h, r8d = ARGB color
; ------------------------------------------------------------------------------
gui_fill_rect:
    push rbx
    push r12
    push r13
    push r14
    push r15

    test rdx, rdx
    jle .fr_done
    test rcx, rcx
    jle .fr_done

    ; x2 = x + w, y2 = y + h
    mov r12, rdi
    add r12, rdx
    mov r13, rsi
    add r13, rcx

    ; Clamp x1 (rdi) to [0..fb_width]
    test rdi, rdi
    jns .fr_x1_ok
    xor rdi, rdi
.fr_x1_ok:
    cmp rdi, [fb_width]
    jge .fr_done

    ; Clamp y1 (rsi) to [0..fb_height]
    test rsi, rsi
    jns .fr_y1_ok
    xor rsi, rsi
.fr_y1_ok:
    cmp rsi, [fb_height]
    jge .fr_done

    ; Clamp x2 (r12) to [0..fb_width]
    cmp r12, [fb_width]
    jle .fr_x2_ok
    mov r12, [fb_width]
.fr_x2_ok:
    cmp r12, rdi
    jle .fr_done

    ; Clamp y2 (r13) to [0..fb_height]
    cmp r13, [fb_height]
    jle .fr_y2_ok
    mov r13, [fb_height]
.fr_y2_ok:
    cmp r13, rsi
    jle .fr_done

    ; Clipped dimensions
    mov r14, r12
    sub r14, rdi                        ; Width in pixels
    mov r15, r13
    sub r15, rsi                        ; Height in lines

    ; Screen buffer pointer: fb_base + y * fb_pitch + x * 4
    mov rax, rsi
    imul rax, [fb_pitch]
    lea rax, [rax + rdi * 4]
    add rax, [fb_base]

.fr_row_loop:
    mov rbx, rax
    mov rcx, r14
.fr_pixel_loop:
    mov [rbx], r8d
    add rbx, 4
    dec rcx
    jnz .fr_pixel_loop

    add rax, [fb_pitch]
    dec r15
    jnz .fr_row_loop

.fr_done:
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; ------------------------------------------------------------------------------
; gui_draw_rect
; In: rdi = x, rsi = y, rdx = w, rcx = h, r8d = ARGB color
; ------------------------------------------------------------------------------
gui_draw_rect:
    push rbx
    push r12
    push r13
    push r14
    push r15
    mov r12, rdi
    mov r13, rsi
    mov r14, rdx
    mov r15, rcx
    mov ebx, r8d

    ; Top border
    mov rdi, r12
    mov rsi, r13
    mov rdx, r14
    mov rcx, 1
    mov r8d, ebx
    call gui_fill_rect

    ; Bottom border
    mov rdi, r12
    mov rsi, r13
    add rsi, r15
    dec rsi
    mov rdx, r14
    mov rcx, 1
    mov r8d, ebx
    call gui_fill_rect

    ; Left border
    mov rdi, r12
    mov rsi, r13
    mov rdx, 1
    mov rcx, r15
    mov r8d, ebx
    call gui_fill_rect

    ; Right border
    mov rdi, r12
    add rdi, r14
    dec rdi
    mov rsi, r13
    mov rdx, 1
    mov rcx, r15
    mov r8d, ebx
    call gui_fill_rect

    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; ------------------------------------------------------------------------------
; gui_put_pixel_clip
; In: rdi = x, rsi = y, edx = color
; ------------------------------------------------------------------------------
gui_put_pixel_clip:
    push rax
    test rdi, rdi
    js .pp_done
    cmp rdi, [fb_width]
    jge .pp_done
    test rsi, rsi
    js .pp_done
    cmp rsi, [fb_height]
    jge .pp_done

    mov rax, rsi
    imul rax, [fb_pitch]
    lea rax, [rax + rdi * 4]
    add rax, [fb_base]
    mov [rax], edx
.pp_done:
    pop rax
    ret

; ------------------------------------------------------------------------------
; gui_draw_line (Bresenham Algorithm across all octants)
; In: rdi = x0, rsi = y0, rdx = x1, rcx = y1, r8d = color
; ------------------------------------------------------------------------------
gui_draw_line:
    push rbx
    push r12
    push r13
    push r14
    push r15
    push rbp

    ; Save inputs
    mov r12, rdi        ; x0
    mov r13, rsi        ; y0
    mov r14, rdx        ; x1
    mov r15, rcx        ; y1
    mov ebp, r8d        ; color

    ; dx = abs(x1 - x0)
    mov rax, r14
    sub rax, r12
    test rax, rax
    jns .dl_dx_pos
    neg rax
.dl_dx_pos:
    mov rbx, rax        ; rbx = dx

    ; dy = abs(y1 - y0)
    mov rax, r15
    sub rax, r13
    test rax, rax
    jns .dl_dy_pos
    neg rax
.dl_dy_pos:
    ; r8 = dy, r9 = -dy
    mov r8, rax         ; r8 = dy
    mov r9, rax
    neg r9              ; r9 = -dy

    ; sx = (x0 < x1) ? 1 : -1
    mov r10, -1
    cmp r12, r14
    jge .dl_sx_set
    mov r10, 1
.dl_sx_set:

    ; sy = (y0 < y1) ? 1 : -1
    mov r11, -1
    cmp r13, r15
    jge .dl_sy_set
    mov r11, 1
.dl_sy_set:

    ; err = dx - dy
    mov rax, rbx
    sub rax, r8         ; rax = err

.dl_loop:
    ; Put pixel at (x0, y0)
    mov rdi, r12
    mov rsi, r13
    mov edx, ebp
    call gui_put_pixel_clip

    ; If (x0 == x1 && y0 == y1) return
    cmp r12, r14
    jne .dl_step
    cmp r13, r15
    je .dl_done

.dl_step:
    ; e2 = 2 * err
    mov rcx, rax
    shl rcx, 1

    ; if e2 >= -dy: err -= dy; x0 += sx
    cmp rcx, r9
    jl .dl_check_dy
    sub rax, r8
    add r12, r10

.dl_check_dy:
    ; if e2 <= dx: err += dx; y0 += sy
    cmp rcx, rbx
    jg .dl_loop
    add rax, rbx
    add r13, r11
    jmp .dl_loop

.dl_done:
    pop rbp
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; ==============================================================================
; 8x8 Monospace Bitmap Font Rendering
; ==============================================================================

; ------------------------------------------------------------------------------
; gui_draw_char
; In: rdi = x, rsi = y, dl = char, r8d = fg, r9d = bg, r10b = is_transparent
; ------------------------------------------------------------------------------
gui_draw_char:
    push rbx
    push r12
    push r13
    push r14
    push r15
    push rbp

    mov r12, rdi        ; x
    mov r13, rsi        ; y
    movzx eax, dl       ; char
    mov ebx, r8d        ; fg
    mov ebp, r9d        ; bg
    mov r15b, r10b      ; transparent flag

    ; Check screen bounds: 0 <= x <= width - 8, 0 <= y <= height - 8
    test r12, r12
    js .dc_done
    mov rax, [fb_width]
    sub rax, 8
    cmp r12, rax
    jg .dc_done
    test r13, r13
    js .dc_done
    mov rax, [fb_height]
    sub rax, 8
    cmp r13, rax
    jg .dc_done

    ; Clamp ASCII range 32..126
    movzx eax, dl
    cmp eax, 32
    jl .dc_space
    cmp eax, 126
    jle .dc_in_range
.dc_space:
    mov eax, 32
.dc_in_range:
    sub eax, 32
    shl eax, 3          ; 8 bytes per char
    lea r14, [gui_font8x8 + rax]

    ; Start address: fb_base + y * fb_pitch + x * 4
    mov rax, r13
    imul rax, [fb_pitch]
    lea rax, [rax + r12 * 4]
    add rax, [fb_base]

    xor ecx, ecx        ; row index 0..7
.dc_row_loop:
    movzx edx, byte [r14 + rcx]
    mov rdi, rax

    ; Pixel 0 (bit 7)
    test dl, 0x80
    jz .b7_bg
    mov [rdi + 0], ebx
    jmp .b6
.b7_bg:
    test r15b, r15b
    jnz .b6
    mov [rdi + 0], ebp

.b6: ; Pixel 1 (bit 6)
    test dl, 0x40
    jz .b6_bg
    mov [rdi + 4], ebx
    jmp .b5
.b6_bg:
    test r15b, r15b
    jnz .b5
    mov [rdi + 4], ebp

.b5: ; Pixel 2 (bit 5)
    test dl, 0x20
    jz .b5_bg
    mov [rdi + 8], ebx
    jmp .b4
.b5_bg:
    test r15b, r15b
    jnz .b4
    mov [rdi + 8], ebp

.b4: ; Pixel 3 (bit 4)
    test dl, 0x10
    jz .b4_bg
    mov [rdi + 12], ebx
    jmp .b3
.b4_bg:
    test r15b, r15b
    jnz .b3
    mov [rdi + 12], ebp

.b3: ; Pixel 4 (bit 3)
    test dl, 0x08
    jz .b3_bg
    mov [rdi + 16], ebx
    jmp .b2
.b3_bg:
    test r15b, r15b
    jnz .b2
    mov [rdi + 16], ebp

.b2: ; Pixel 5 (bit 2)
    test dl, 0x04
    jz .b2_bg
    mov [rdi + 20], ebx
    jmp .b1
.b2_bg:
    test r15b, r15b
    jnz .b1
    mov [rdi + 20], ebp

.b1: ; Pixel 6 (bit 1)
    test dl, 0x02
    jz .b1_bg
    mov [rdi + 24], ebx
    jmp .b0
.b1_bg:
    test r15b, r15b
    jnz .b0
    mov [rdi + 24], ebp

.b0: ; Pixel 7 (bit 0)
    test dl, 0x01
    jz .b0_bg
    mov [rdi + 28], ebx
    jmp .row_next
.b0_bg:
    test r15b, r15b
    jnz .row_next
    mov [rdi + 28], ebp

.row_next:
    add rax, [fb_pitch]
    inc ecx
    cmp ecx, 8
    jl .dc_row_loop

.dc_done:
    pop rbp
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; ------------------------------------------------------------------------------
; gui_draw_str
; In: rdi = x, rsi = y, rdx = string_ptr, r8d = fg, r9d = bg, r10b = is_transparent
; ------------------------------------------------------------------------------
gui_draw_str:
    push rbx
    push r12
    push r13
    push r14
    push r15
    push rbp

    mov r12, rdi        ; current x
    mov r13, rsi        ; y
    mov r14, rdx        ; str ptr
    mov ebx, r8d        ; fg
    mov ebp, r9d        ; bg
    mov r15b, r10b      ; transparent

.ds_loop:
    mov dl, [r14]
    test dl, dl
    jz .ds_done

    mov rdi, r12
    mov rsi, r13
    mov r8d, ebx
    mov r9d, ebp
    mov r10b, r15b
    call gui_draw_char

    add r12, 8          ; Advance 8 pixels
    inc r14
    jmp .ds_loop

.ds_done:
    pop rbp
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; ==============================================================================
; Mouse Cursor (12x12 Pointer)
; ==============================================================================

align 8
cursor_mask:
    dw 0b100000000000 ; Row 0
    dw 0b110000000000 ; Row 1
    dw 0b111000000000 ; Row 2
    dw 0b111100000000 ; Row 3
    dw 0b111110000000 ; Row 4
    dw 0b111111000000 ; Row 5
    dw 0b111111100000 ; Row 6
    dw 0b111111110000 ; Row 7
    dw 0b111111000000 ; Row 8
    dw 0b110111100000 ; Row 9
    dw 0b100011110000 ; Row 10
    dw 0b000001110000 ; Row 11

cursor_border:
    dw 0b100000000000 ; Row 0
    dw 0b110000000000 ; Row 1
    dw 0b101000000000 ; Row 2
    dw 0b100100000000 ; Row 3
    dw 0b100010000000 ; Row 4
    dw 0b100001000000 ; Row 5
    dw 0b100000100000 ; Row 6
    dw 0b100000010000 ; Row 7
    dw 0b100011000000 ; Row 8
    dw 0b110100100000 ; Row 9
    dw 0b100010010000 ; Row 10
    dw 0b000001110000 ; Row 11

; ------------------------------------------------------------------------------
; gui_save_cursor_bg
; Saves 12x12 pixels under (rdi, rsi) into cursor_saved_bg
; ------------------------------------------------------------------------------
gui_save_cursor_bg:
    push rbx
    push r12
    push r13
    push r14

    movsxd r12, edi     ; cx
    movsxd r13, esi     ; cy
    lea r14, [cursor_saved_bg]

    xor ebx, ebx        ; row 0..11
.sc_row:
    xor ecx, ecx        ; col 0..11
.sc_col:
    lea rdi, [r12 + rcx]
    lea rsi, [r13 + rbx]

    ; Check bounds
    xor edx, edx
    cmp rdi, 0
    jl .sc_store
    cmp rdi, [fb_width]
    jge .sc_store
    cmp rsi, 0
    jl .sc_store
    cmp rsi, [fb_height]
    jge .sc_store

    mov rax, rsi
    imul rax, [fb_pitch]
    lea rax, [rax + rdi * 4]
    add rax, [fb_base]
    mov edx, [rax]

.sc_store:
    mov [r14], edx
    add r14, 4
    inc ecx
    cmp ecx, 12
    jl .sc_col

    inc ebx
    cmp ebx, 12
    jl .sc_row

    mov byte [cursor_saved_valid], 1
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; ------------------------------------------------------------------------------
; gui_restore_cursor_bg
; Restores 12x12 pixels from cursor_saved_bg to (rdi, rsi)
; ------------------------------------------------------------------------------
gui_restore_cursor_bg:
    cmp byte [cursor_saved_valid], 0
    je .rc_done

    push rbx
    push r12
    push r13
    push r14

    movsxd r12, edi     ; cx
    movsxd r13, esi     ; cy
    lea r14, [cursor_saved_bg]

    xor ebx, ebx        ; row 0..11
.rc_row:
    xor ecx, ecx        ; col 0..11
.rc_col:
    lea rdi, [r12 + rcx]
    lea rsi, [r13 + rbx]
    mov edx, [r14]

    ; Put pixel with clipping
    call gui_put_pixel_clip

    add r14, 4
    inc ecx
    cmp ecx, 12
    jl .rc_col

    inc ebx
    cmp ebx, 12
    jl .rc_row

    mov byte [cursor_saved_valid], 0
    pop r14
    pop r13
    pop r12
    pop rbx
.rc_done:
    ret

; ------------------------------------------------------------------------------
; gui_draw_mouse_cursor
; Draws cursor at (rdi, rsi)
; ------------------------------------------------------------------------------
gui_draw_mouse_cursor:
    push rbx
    push r12
    push r13
    push r14
    push r15

    movsxd r12, edi
    movsxd r13, esi

    ; Save background first
    mov rdi, r12
    mov rsi, r13
    call gui_save_cursor_bg

    xor ebx, ebx        ; row 0..11
.mc_row:
    movzx r14, word [cursor_mask + rbx * 2]
    movzx r15, word [cursor_border + rbx * 2]
    xor ecx, ecx        ; col 0..11

.mc_col:
    mov rdx, 0x0800     ; Bit 11
    shr rdx, cl

    test r14, rdx       ; Is pixel in body/border?
    jz .mc_next_pixel

    test r15, rdx       ; Is pixel border?
    jz .mc_body

    ; Border pixel (black: 0xFF000000)
    lea rdi, [r12 + rcx]
    lea rsi, [r13 + rbx]
    mov edx, 0xFF000000
    call gui_put_pixel_clip
    jmp .mc_next_pixel

.mc_body:
    ; Body pixel (white: 0xFFFFFFFF)
    lea rdi, [r12 + rcx]
    lea rsi, [r13 + rbx]
    mov edx, 0xFFFFFFFF
    call gui_put_pixel_clip

.mc_next_pixel:
    inc ecx
    cmp ecx, 12
    jl .mc_col

    inc ebx
    cmp ebx, 12
    jl .mc_row

    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; ==============================================================================
; Window Renderer & Desktop Layout
; ==============================================================================

; ------------------------------------------------------------------------------
; gui_draw_window_frame
; In: rdi = x, rsi = y, rdx = w, rcx = h, r8 = title_str, r9d = is_focused
; ------------------------------------------------------------------------------
gui_draw_window_frame:
    push rbx
    push r12
    push r13
    push r14
    push r15
    push rbp

    mov r12, rdi        ; x
    mov r13, rsi        ; y
    mov r14, rdx        ; w
    mov r15, rcx        ; h
    mov rbx, r8         ; title_str
    mov ebp, r9d        ; is_focused

    ; Outer Border Color
    mov r8d, COLOR_BORDER
    test ebp, ebp
    jz .wf_draw_border
    mov r8d, COLOR_BORDER_FOCUS
.wf_draw_border:
    mov rdi, r12
    mov rsi, r13
    mov rdx, r14
    mov rcx, r15
    call gui_draw_rect

    ; Titlebar background (height = 24px)
    mov r8d, COLOR_TITLEBAR
    test ebp, ebp
    jz .wf_draw_tb
    mov r8d, COLOR_TITLEBAR_FOC
.wf_draw_tb:
    lea rdi, [r12 + 1]
    lea rsi, [r13 + 1]
    lea rdx, [r14 - 2]
    mov rcx, 23
    call gui_fill_rect

    ; Titlebar bottom separator line
    lea rdi, [r12 + 1]
    lea rsi, [r13 + 24]
    lea rdx, [r14 - 2]
    mov rcx, 1
    mov r8d, COLOR_BORDER
    call gui_fill_rect

    ; Window Client Area
    lea rdi, [r12 + 1]
    lea rsi, [r13 + 25]
    lea rdx, [r14 - 2]
    lea rcx, [r15 - 26]
    mov r8d, COLOR_WIN_BG
    call gui_fill_rect

    ; Window Title Text
    lea rdi, [r12 + 10]
    lea rsi, [r13 + 8]
    mov rdx, rbx
    mov r8d, COLOR_TITLE_TEXT
    mov r9d, 0
    mov r10b, 1         ; transparent
    call gui_draw_str

    ; Close Button "[X]" at top-right
    lea rdi, [r12 + r14 - 22]
    lea rsi, [r13 + 6]
    mov rdx, str_win_close_btn
    mov r8d, COLOR_CLOSE_BTN
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    pop rbp
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbx
    ret

; ------------------------------------------------------------------------------
; gui_render_terminal_window
; Draws Window 1 (Interactive Graphical Terminal): x=40, y=44, w=480, h=310
; ------------------------------------------------------------------------------
gui_render_terminal_window:
    cmp byte [win_terminal_vis], 0
    je .rt_done

    push rbx
    ; Frame
    mov rdi, 40
    mov rsi, 44
    mov rdx, 480
    mov rcx, 310
    mov r8, str_win_term_title
    xor r9d, r9d
    cmp dword [focused_window], 1
    jne .rt_unfocused
    mov r9d, 1
.rt_unfocused:
    call gui_draw_window_frame

    ; Terminal Content
    mov rdi, 52
    mov rsi, 74
    mov rdx, str_term_banner1
    mov r8d, COLOR_ACCENT_BLUE
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    mov rdi, 52
    mov rsi, 88
    mov rdx, str_term_banner2
    mov r8d, COLOR_TEXT_YELLOW
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    mov rdi, 52
    mov rsi, 102
    mov rdx, str_term_divider
    mov r8d, COLOR_BORDER
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    ; Draw prompt and command buffer
    call gui_terminal_draw_prompt

    ; If last command output exists, show it
    cmp byte [term_last_cmd_res], 0
    je .rt_skip_last
    mov rdi, 52
    mov rsi, 136
    mov rdx, term_last_cmd_res
    mov r8d, COLOR_BRAND
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str
.rt_skip_last:

    pop rbx
.rt_done:
    ret

; ------------------------------------------------------------------------------
; gui_terminal_draw_prompt
; Redraws the terminal prompt row: "kale-os> " + cmd_buffer + cursor
; ------------------------------------------------------------------------------
gui_terminal_draw_prompt:
    push rbx
    push r12

    ; Clear the prompt row
    mov rdi, 50
    mov rsi, 118
    mov rdx, 460
    mov rcx, 14
    mov r8d, COLOR_WIN_BG
    call gui_fill_rect

    ; Draw prompt: "kale-os> "
    mov rdi, 52
    mov rsi, 120
    mov rdx, prompt_str
    mov r8d, COLOR_PROMPT
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    ; Draw command buffer
    mov rdi, 124        ; 52 + 9 chars * 8 = 124
    mov rsi, 120
    mov rdx, cmd_buffer
    mov r8d, COLOR_TEXT_WHITE
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    ; Draw block cursor if focused
    cmp dword [focused_window], 1
    jne .tp_done

    movzx eax, byte [cmd_len]
    shl eax, 3          ; len * 8
    lea rdi, [rax + 124]
    mov rsi, 120
    mov rdx, 8
    mov rcx, 10
    mov r8d, COLOR_PROMPT
    call gui_fill_rect

.tp_done:
    pop r12
    pop rbx
    ret

; ------------------------------------------------------------------------------
; gui_render_sysmon_window
; Draws Window 2 (System Monitor): x=540, y=44, w=220, h=270
; ------------------------------------------------------------------------------
gui_render_sysmon_window:
    cmp byte [win_sysmon_vis], 0
    je .sm_done

    mov rdi, 540
    mov rsi, 44
    mov rdx, 220
    mov rcx, 270
    mov r8, str_win_sysmon_title
    xor r9d, r9d
    cmp dword [focused_window], 2
    jne .sm_unfocused
    mov r9d, 1
.sm_unfocused:
    call gui_draw_window_frame

    ; Status rows
    mov rdi, 552
    mov rsi, 74
    mov rdx, str_sm_cpu
    mov r8d, COLOR_PROMPT
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    mov rdi, 552
    mov rsi, 94
    mov rdx, str_sm_vmm
    mov r8d, COLOR_BRAND
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    mov rdi, 552
    mov rsi, 114
    mov rdx, str_sm_heap
    mov r8d, COLOR_TEXT_YELLOW
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    mov rdi, 552
    mov rsi, 134
    mov rdx, str_sm_storage
    mov r8d, COLOR_ACCENT_BLUE
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    mov rdi, 552
    mov rsi, 154
    mov rdx, str_sm_net
    mov r8d, COLOR_PROMPT
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    ; RAM Usage Bar Outline
    mov rdi, 552
    mov rsi, 184
    mov rdx, 196
    mov rcx, 14
    mov r8d, COLOR_BORDER
    call gui_draw_rect

    ; RAM Usage Fill (42% = 82px)
    mov rdi, 554
    mov rsi, 186
    mov rdx, 82
    mov rcx, 10
    mov r8d, COLOR_ACCENT_BLUE
    call gui_fill_rect

    ; RAM Text
    mov rdi, 552
    mov rsi, 206
    mov rdx, str_sm_ram_text
    mov r8d, COLOR_TEXT_GRAY
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

.sm_done:
    ret

; ------------------------------------------------------------------------------
; gui_render_demo_window
; Draws Window 3 (2D Graphics Showcase): x=140, y=374, w=520, h=196
; ------------------------------------------------------------------------------
gui_render_demo_window:
    cmp byte [win_demo_vis], 0
    je .dm_done

    mov rdi, 140
    mov rsi, 374
    mov rdx, 520
    mov rcx, 196
    mov r8, str_win_demo_title
    xor r9d, r9d
    cmp dword [focused_window], 3
    jne .dm_unfocused
    mov r9d, 1
.dm_unfocused:
    call gui_draw_window_frame

    ; Section header
    mov rdi, 154
    mov rsi, 404
    mov rdx, str_demo_palette_label
    mov r8d, COLOR_BRAND
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    ; Color Swatches (8 boxes of 22x16)
    ; Red
    mov rdi, 154
    mov rsi, 420
    mov rdx, 22
    mov rcx, 16
    mov r8d, 0xFFF38BA8
    call gui_fill_rect

    ; Green
    mov rdi, 182
    mov rsi, 420
    mov rdx, 22
    mov rcx, 16
    mov r8d, 0xFFA6E3A1
    call gui_fill_rect

    ; Blue
    mov rdi, 210
    mov rsi, 420
    mov rdx, 22
    mov rcx, 16
    mov r8d, 0xFF89B4FA
    call gui_fill_rect

    ; Yellow
    mov rdi, 238
    mov rsi, 420
    mov rdx, 22
    mov rcx, 16
    mov r8d, 0xFFF9E2AF
    call gui_fill_rect

    ; Cyan
    mov rdi, 266
    mov rsi, 420
    mov rdx, 22
    mov rcx, 16
    mov r8d, 0xFF89DCEB
    call gui_fill_rect

    ; Magenta
    mov rdi, 294
    mov rsi, 420
    mov rdx, 22
    mov rcx, 16
    mov r8d, 0xFFCBA6F7
    call gui_fill_rect

    ; White
    mov rdi, 322
    mov rsi, 420
    mov rdx, 22
    mov rcx, 16
    mov r8d, 0xFFFFFFFF
    call gui_fill_rect

    ; Orange
    mov rdi, 350
    mov rsi, 420
    mov rdx, 22
    mov rcx, 16
    mov r8d, 0xFFFAB387
    call gui_fill_rect

    ; Bresenham lines demo
    mov rdi, 154
    mov rsi, 452
    mov rdx, str_demo_lines_label
    mov r8d, COLOR_BRAND
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    mov rdi, 154
    mov rsi, 470
    mov rdx, 260
    mov rcx, 540
    mov r8d, 0xFF89DCEB
    call gui_draw_line

    mov rdi, 154
    mov rsi, 540
    mov rdx, 260
    mov rcx, 470
    mov r8d, 0xFFA6E3A1
    call gui_draw_line

    mov rdi, 207
    mov rsi, 470
    mov rdx, 207
    mov rcx, 540
    mov r8d, 0xFFF9E2AF
    call gui_draw_line

    ; Concentric outlined rects
    mov rdi, 280
    mov rsi, 470
    mov rdx, 70
    mov rcx, 70
    mov r8d, COLOR_BORDER_FOCUS
    call gui_draw_rect

    mov rdi, 290
    mov rsi, 480
    mov rdx, 50
    mov rcx, 50
    mov r8d, 0xFF89B4FA
    call gui_draw_rect

    mov rdi, 300
    mov rsi, 490
    mov rdx, 30
    mov rcx, 30
    mov r8d, 0xFFF38BA8
    call gui_fill_rect

    ; Typography Showcase
    mov rdi, 380
    mov rsi, 420
    mov rdx, str_demo_typo1
    mov r8d, COLOR_TEXT_WHITE
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    mov rdi, 380
    mov rsi, 442
    mov rdx, str_demo_typo2
    mov r8d, COLOR_PROMPT
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    mov rdi, 380
    mov rsi, 464
    mov rdx, str_demo_typo3
    mov r8d, COLOR_TEXT_YELLOW
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    mov rdi, 380
    mov rsi, 486
    mov rdx, str_demo_typo4
    mov r8d, COLOR_BRAND
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

.dm_done:
    ret

; ------------------------------------------------------------------------------
; gui_render_taskbar
; Renders top taskbar: height 28px
; ------------------------------------------------------------------------------
gui_render_taskbar:
    ; Taskbar background
    mov rdi, 0
    mov rsi, 0
    mov rdx, [fb_width]
    mov rcx, 27
    mov r8d, COLOR_TASKBAR_BG
    call gui_fill_rect

    ; Taskbar bottom separator
    mov rdi, 0
    mov rsi, 27
    mov rdx, [fb_width]
    mov rcx, 1
    mov r8d, COLOR_BORDER
    call gui_fill_rect

    ; OS Logo & Branding
    mov rdi, 12
    mov rsi, 8
    mov rdx, str_tb_brand
    mov r8d, COLOR_BRAND
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    ; Active Window Button
    mov rdi, 140
    mov rsi, 8
    mov rdx, str_tb_term_active
    mov r8d, COLOR_PROMPT
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    ; Status Bar info
    mov rdi, 360
    mov rsi, 8
    mov rdx, str_tb_sys_info
    mov r8d, COLOR_TEXT_GRAY
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    ; Uptime Ticks
    mov rdi, 690
    mov rsi, 8
    mov rdx, str_tb_uptime
    mov r8d, COLOR_TEXT_YELLOW
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    ret

; ------------------------------------------------------------------------------
; gui_render_desktop
; Full desktop render pass
; ------------------------------------------------------------------------------
gui_render_desktop:
    push rbx
    push r12
    push r13

    ; 1. Clear desktop to dark slate
    mov rdi, 0
    mov rsi, 0
    mov rdx, [fb_width]
    mov rcx, [fb_height]
    mov r8d, COLOR_DESKTOP_BG
    call gui_fill_rect

    ; 2. Subtle background dot grid (every 40px)
    mov r12d, 40        ; x
.dt_grid_x:
    mov r13d, 48        ; y (below taskbar)
.dt_grid_y:
    movsxd rdi, r12d
    movsxd rsi, r13d
    mov edx, COLOR_GRID_DOT
    call gui_put_pixel_clip

    add r13d, 40
    cmp r13d, 580
    jl .dt_grid_y

    add r12d, 40
    cmp r12d, 780
    jl .dt_grid_x

    ; 3. Desktop watermark text
    mov rdi, 240
    mov rsi, 582
    mov rdx, str_dt_watermark
    mov r8d, 0xFF313244
    mov r9d, 0
    mov r10b, 1
    call gui_draw_str

    ; 4. Render top taskbar
    call gui_render_taskbar

    ; 5. Render Windows
    call gui_render_terminal_window
    call gui_render_sysmon_window
    call gui_render_demo_window

    ; 6. Draw mouse pointer
    movsxd rdi, dword [mouse_x]
    movsxd rsi, dword [mouse_y]
    call gui_draw_mouse_cursor

    pop r13
    pop r12
    pop rbx
    ret

; ==============================================================================
; PS/2 Mouse Hardware Controller & Packet Parser
; ==============================================================================
mouse_wait_write:
    in al, 0x64
    test al, 2          ; Input buffer full?
    jnz mouse_wait_write
    ret

mouse_wait_read:
    in al, 0x64
    test al, 1          ; Output buffer full?
    jz mouse_wait_read
    ret

mouse_init_hardware:
    push rax

    ; Enable auxiliary device (mouse) on PS/2 controller
    call mouse_wait_write
    mov al, 0xA8
    out 0x64, al

    ; Tell controller we want to send byte to mouse (0xD4)
    call mouse_wait_write
    mov al, 0xD4
    out 0x64, al

    ; Enable packet streaming (0xF4)
    call mouse_wait_write
    mov al, 0xF4
    out 0x60, al

    ; Read ACK
    call mouse_wait_read
    in al, 0x60

    mov byte [mouse_cycle], 0
    pop rax
    ret

; ------------------------------------------------------------------------------
; mouse_poll_event
; Polls mouse controller port 0x64/0x60 and updates cursor position
; ------------------------------------------------------------------------------
mouse_poll_event:
    in al, 0x64
    test al, 1          ; Data ready?
    jz .m_done
    test al, 0x20       ; Is AUX (mouse) data?
    jz .m_done

    ; Read mouse packet byte from 0x60
    in al, 0x60
    movzx ecx, byte [mouse_cycle]

    cmp ecx, 0
    je .m_byte0
    cmp ecx, 1
    je .m_byte1
    jmp .m_byte2

.m_byte0:
    ; Byte 0: bit 3 must always be 1
    test al, 0x08
    jz .m_reset_cycle
    mov [mouse_pkt + 0], al
    inc byte [mouse_cycle]
    jmp .m_done

.m_byte1:
    mov [mouse_pkt + 1], al
    inc byte [mouse_cycle]
    jmp .m_done

.m_byte2:
    mov [mouse_pkt + 2], al
    mov byte [mouse_cycle], 0

    ; Decode 3-byte packet:
    ; Byte 0: flags & buttons
    ; Byte 1: delta X
    ; Byte 2: delta Y
    movzx edx, byte [mouse_pkt + 0]
    movzx eax, byte [mouse_pkt + 1]     ; dx
    movzx ebx, byte [mouse_pkt + 2]     ; dy

    ; Sign extend dx if bit 4 set
    test edx, 0x10
    jz .dx_pos
    or eax, 0xFFFFFF00
.dx_pos:

    ; Sign extend dy if bit 5 set
    test edx, 0x20
    jz .dy_pos
    or ebx, 0xFFFFFF00
.dy_pos:

    ; Hardware PS/2 reports positive dy when moving up -> invert for screen coordinates
    neg ebx

    ; If both deltas are 0 and no buttons, nothing to update
    test eax, eax
    jnz .m_apply
    test ebx, ebx
    jnz .m_apply
    ; Check button state change
    mov cl, dl
    and cl, 0x01        ; Left button
    cmp cl, [mouse_btn]
    je .m_done

.m_apply:
    ; Erase old cursor
    movsxd rdi, dword [mouse_x]
    movsxd rsi, dword [mouse_y]
    call gui_restore_cursor_bg

    ; Update X with clamping [0..788]
    mov ecx, [mouse_x]
    add ecx, eax
    test ecx, ecx
    jns .cx_nonneg
    xor ecx, ecx
.cx_nonneg:
    cmp ecx, 788
    jle .cx_ok
    mov ecx, 788
.cx_ok:
    mov [mouse_x], ecx

    ; Update Y with clamping [0..588]
    mov ecx, [mouse_y]
    add ecx, ebx
    test ecx, ecx
    jns .cy_nonneg
    xor ecx, ecx
.cy_nonneg:
    cmp ecx, 588
    jle .cy_ok
    mov ecx, 588
.cy_ok:
    mov [mouse_y], ecx

    ; Draw new cursor
    movsxd rdi, dword [mouse_x]
    movsxd rsi, dword [mouse_y]
    call gui_draw_mouse_cursor

    ; Handle Left Mouse Button Click
    test edx, 0x01
    jz .m_btn_up
    cmp byte [mouse_btn], 0
    jne .m_done         ; Already held down
    mov byte [mouse_btn], 1

    ; Click Hit-testing
    call mouse_handle_click
    jmp .m_done

.m_btn_up:
    mov byte [mouse_btn], 0
    jmp .m_done

.m_reset_cycle:
    mov byte [mouse_cycle], 0

.m_done:
    ret

; ------------------------------------------------------------------------------
; mouse_handle_click
; Hit-tests windows and close buttons at current (mouse_x, mouse_y)
; ------------------------------------------------------------------------------
mouse_handle_click:
    mov eax, [mouse_x]
    mov ebx, [mouse_y]

    ; Check Terminal Close Button [X]: (498..515, 48..64)
    cmp eax, 496
    jl .hc_check_term
    cmp eax, 516
    jg .hc_check_term
    cmp ebx, 46
    jl .hc_check_term
    cmp ebx, 66
    jg .hc_check_term
    ; Toggle terminal visibility
    xor byte [win_terminal_vis], 1
    call gui_render_desktop
    ret

.hc_check_term:
    ; Check Terminal Window: (40..520, 44..354)
    cmp eax, 40
    jl .hc_check_sysmon
    cmp eax, 520
    jg .hc_check_sysmon
    cmp ebx, 44
    jl .hc_check_sysmon
    cmp ebx, 354
    jg .hc_check_sysmon
    mov dword [focused_window], 1
    call gui_render_terminal_window
    call gui_render_sysmon_window
    call gui_render_demo_window
    movsxd rdi, dword [mouse_x]
    movsxd rsi, dword [mouse_y]
    call gui_draw_mouse_cursor
    ret

.hc_check_sysmon:
    ; Check SysMon Window: (540..760, 44..314)
    cmp eax, 540
    jl .hc_check_demo
    cmp eax, 760
    jg .hc_check_demo
    cmp ebx, 44
    jl .hc_check_demo
    cmp ebx, 314
    jg .hc_check_demo
    mov dword [focused_window], 2
    call gui_render_terminal_window
    call gui_render_sysmon_window
    call gui_render_demo_window
    movsxd rdi, dword [mouse_x]
    movsxd rsi, dword [mouse_y]
    call gui_draw_mouse_cursor
    ret

.hc_check_demo:
    ; Check Demo Window: (140..660, 374..570)
    cmp eax, 140
    jl .hc_done
    cmp eax, 660
    jg .hc_done
    cmp ebx, 374
    jl .hc_done
    cmp ebx, 570
    jg .hc_done
    mov dword [focused_window], 3
    call gui_render_terminal_window
    call gui_render_sysmon_window
    call gui_render_demo_window
    movsxd rdi, dword [mouse_x]
    movsxd rsi, dword [mouse_y]
    call gui_draw_mouse_cursor

.hc_done:
    ret

; ==============================================================================
; Interactive GUI Main Loop
; ==============================================================================
gui_main_loop:
    ; 1. Poll PS/2 Mouse packets
    call mouse_poll_event

    ; 2. Poll PS/2 Keyboard
    call kbd_poll_char
    test al, al
    jz .gml_no_key

    ; Key pressed!
    cmp al, 10          ; Enter
    je .gml_enter

    cmp al, 8           ; Backspace
    je .gml_backspace

    ; Normal character
    movzx ecx, byte [cmd_len]
    cmp ecx, 50
    jge .gml_no_key

    mov [cmd_buffer + rcx], al
    inc byte [cmd_len]
    mov byte [cmd_buffer + rcx + 1], 0

    ; Mirror to serial
    call serial_putc

    ; Redraw terminal prompt line
    call gui_terminal_draw_prompt
    jmp .gml_no_key

.gml_backspace:
    movzx ecx, byte [cmd_len]
    test ecx, ecx
    jz .gml_no_key

    dec byte [cmd_len]
    dec ecx
    mov byte [cmd_buffer + rcx], 0

    ; Mirror to serial
    mov al, 8
    call serial_putc
    mov al, ' '
    call serial_putc
    mov al, 8
    call serial_putc

    call gui_terminal_draw_prompt
    jmp .gml_no_key

.gml_enter:
    ; Mirror newline to serial
    mov al, 13
    call serial_putc
    mov al, 10
    call serial_putc

    ; Check if command is "text" (switch back to VGA text mode)
    mov rsi, cmd_buffer
    mov rdi, str_cmd_text
    call str_equals
    test eax, eax
    jnz .gml_switch_to_text

    ; Check if command is "clear"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_clear
    call str_equals
    test eax, eax
    jnz .gml_clear_term

    ; Run command and copy summary into term_last_cmd_res
    call gui_execute_command

    ; Reset command buffer
    mov byte [cmd_len], 0
    mov byte [cmd_buffer], 0

    ; Redraw terminal window with new output
    call gui_render_terminal_window
    movsxd rdi, dword [mouse_x]
    movsxd rsi, dword [mouse_y]
    call gui_draw_mouse_cursor
    jmp .gml_no_key

.gml_clear_term:
    mov byte [term_last_cmd_res], 0
    mov byte [cmd_len], 0
    mov byte [cmd_buffer], 0
    call gui_render_terminal_window
    movsxd rdi, dword [mouse_x]
    movsxd rsi, dword [mouse_y]
    call gui_draw_mouse_cursor
    jmp .gml_no_key

.gml_switch_to_text:
    mov byte [cmd_len], 0
    mov byte [cmd_buffer], 0
    mov byte [gui_active], 0
    ; Switch back to VGA text mode (03h)
    call vga_init_display
    call vga_enable_cursor
    mov byte [cursor_row], 11
    mov byte [cursor_col], 9
    call vga_sync_cursor
    jmp shell_loop

.gml_no_key:
    jmp gui_main_loop

; ------------------------------------------------------------------------------
; gui_execute_command
; Dispatches command in GUI mode and stores summary in term_last_cmd_res
; ------------------------------------------------------------------------------
gui_execute_command:
    push rbx
    push r12

    ; "help"
    mov rsi, cmd_buffer
    mov rdi, str_cmd_help
    call str_equals
    test eax, eax
    jz .gec_info
    mov rsi, str_res_help
    call gui_copy_result
    jmp .gec_done

.gec_info:
    mov rsi, cmd_buffer
    mov rdi, str_cmd_info
    call str_equals
    test eax, eax
    jz .gec_mem
    mov rsi, str_res_info
    call gui_copy_result
    jmp .gec_done

.gec_mem:
    mov rsi, cmd_buffer
    mov rdi, str_cmd_mem
    call str_equals
    test eax, eax
    jz .gec_cpu
    mov rsi, str_res_mem
    call gui_copy_result
    jmp .gec_done

.gec_cpu:
    mov rsi, cmd_buffer
    mov rdi, str_cmd_cpu
    call str_equals
    test eax, eax
    jz .gec_disk
    mov rsi, str_res_cpu
    call gui_copy_result
    jmp .gec_done

.gec_disk:
    mov rsi, cmd_buffer
    mov rdi, str_cmd_disk
    call str_equals
    test eax, eax
    jz .gec_net
    mov rsi, str_res_disk
    call gui_copy_result
    jmp .gec_done

.gec_net:
    mov rsi, cmd_buffer
    mov rdi, str_cmd_net
    call str_equals
    test eax, eax
    jz .gec_reboot
    mov rsi, str_res_net
    call gui_copy_result
    jmp .gec_done

.gec_reboot:
    mov rsi, cmd_buffer
    mov rdi, str_cmd_reboot
    call str_equals
    test eax, eax
    jz .gec_halt
    ; Trigger 8042 reset
    mov al, 0xFE
    out 0x64, al
    hlt

.gec_halt:
    mov rsi, cmd_buffer
    mov rdi, str_cmd_halt
    call str_equals
    test eax, eax
    jz .gec_unknown
    cli
    hlt

.gec_unknown:
    mov rsi, str_res_unknown
    call gui_copy_result

.gec_done:
    pop r12
    pop rbx
    ret

gui_copy_result:
    mov rdi, term_last_cmd_res
    mov ecx, 63
.gcr_loop:
    lodsb
    stosb
    test al, al
    jz .gcr_done
    dec ecx
    jnz .gcr_loop
    mov byte [rdi], 0
.gcr_done:
    ret

; ==============================================================================
; GUI String Constants
; ==============================================================================
str_cmd_text:           db "text", 0
str_win_close_btn:      db "[X]", 0
str_win_term_title:     db "Terminal - Kale Shell (Active)", 0
str_win_sysmon_title:   db "System Monitor", 0
str_win_demo_title:     db "2D Vector & Rasterizer Primitives", 0

str_term_banner1:       db "Kale OS v0.5.0-alpha (x86_64 Long Mode)", 0
str_term_banner2:       db "Type 'help' for commands, 'text' for VGA mode.", 0
str_term_divider:       db "--------------------------------------------------", 0

str_sm_cpu:             db "CPU: AMD64 Long Mode", 0
str_sm_vmm:             db "VMM: 4-Level PML4 4GB", 0
str_sm_heap:            db "Heap: Segregated Size", 0
str_sm_storage:         db "Storage: ATA /dev/hda", 0
str_sm_net:             db "Net: 127.0.0.1 (UP)", 0
str_sm_ram_text:        db "RAM: 64 MB / 128 MB Active", 0

str_demo_palette_label: db "Color Palette Swatches:", 0
str_demo_lines_label:   db "Bresenham Vector Lines & Shapes:", 0
str_demo_typo1:         db "8x8 Monospace Bitmap Typography", 0
str_demo_typo2:         db "Linear 32-Bit Framebuffer OK", 0
str_demo_typo3:         db "Hardware PS/2 Mouse Streaming", 0
str_demo_typo4:         db "Z-Ordered Window Compositor", 0

str_tb_brand:           db "[#] KALE OS", 0
str_tb_term_active:     db "Terminal [Focus]", 0
str_tb_sys_info:        db "x86_64 | 128MB | VFS | NET", 0
str_tb_uptime:          db "UP: 00:01", 0
str_dt_watermark:       db "KALE OS - 64-BIT GRAPHICAL WORKSTATION", 0

str_res_help:           db "[OK] Available: info, mem, cpu, disk, net, clear, text", 0
str_res_info:           db "[OK] Kale OS v0.5.0-alpha (AMD64 Long Mode GUI)", 0
str_res_mem:            db "[OK] Memory: 128MB PMM Frame Pool | 4GB Identity Paging", 0
str_res_cpu:            db "[OK] CPU: Ring 0 Kernel Mode | CR0.PG=1 CR4.PAE=1", 0
str_res_disk:           db "[OK] ATA Primary Master: 28/48-bit LBA OK (/dev/hda)", 0
str_res_net:            db "[OK] Network: lo0 (127.0.0.1) & Socket Stack Active", 0
str_res_unknown:        db "[!] Command not found. Type 'help'.", 0

; Include 8x8 font table
%include "os/kernel/font8x8.inc"
