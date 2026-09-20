; ==============================================================================
; Kale OS Context Switching and Control Register Routines
; Architecture: x86_64 Long Mode (NASM)
; ==============================================================================

[BITS 64]

global cpu_context_switch
global cpu_load_cr3
global cpu_read_cr3
global cpu_enable_interrupts
global cpu_disable_interrupts
global cpu_halt
global cpu_load_tr
global switch_to_user_mode

; cpu_context_switch(CPUContext* old_ctx, CPUContext* new_ctx)
; Windows x64 ABI: RCX = old_ctx, RDX = new_ctx
cpu_context_switch:
    ; Check if old_ctx is null
    test rcx, rcx
    jz .restore_new
    
    ; Save general-purpose registers into old_ctx
    mov [rcx + 0],   rax
    mov [rcx + 8],   rbx
    mov [rcx + 16],  rcx
    mov [rcx + 24],  rdx
    mov [rcx + 32],  rsi
    mov [rcx + 40],  rdi
    mov [rcx + 48],  rbp
    mov [rcx + 56],  rsp
    mov [rcx + 64],  r8
    mov [rcx + 72],  r9
    mov [rcx + 80],  r10
    mov [rcx + 88],  r11
    mov [rcx + 96],  r12
    mov [rcx + 104], r13
    mov [rcx + 112], r14
    mov [rcx + 120], r15
    
    ; Save return address from stack as RIP
    mov rax, [rsp]
    mov [rcx + 128], rax
    
    ; Save RFLAGS
    pushfq
    pop rax
    mov [rcx + 136], rax

.restore_new:
    test rdx, rdx
    jz .done
    
    ; Restore registers from new_ctx (in RDX)
    mov rax, [rdx + 0]
    mov rbx, [rdx + 8]
    mov rcx, [rdx + 16]
    mov rsi, [rdx + 32]
    mov rdi, [rdx + 40]
    mov rbp, [rdx + 48]
    mov rsp, [rdx + 56]
    mov r8,  [rdx + 64]
    mov r9,  [rdx + 72]
    mov r10, [rdx + 80]
    mov r11, [rdx + 88]
    mov r12, [rdx + 96]
    mov r13, [rdx + 104]
    mov r14, [rdx + 112]
    mov r15, [rdx + 120]
    
    ; Set up target RIP on stack for return
    push qword [rdx + 128]
    
    ; Restore RFLAGS
    push qword [rdx + 136]
    popfq
    
    mov rdx, [rdx + 24]
    ret

.done:
    ret

; cpu_load_cr3(uint64 cr3_val)
cpu_load_cr3:
    mov cr3, rcx
    ret

; cpu_read_cr3() -> uint64
cpu_read_cr3:
    mov rax, cr3
    ret

; cpu_enable_interrupts()
cpu_enable_interrupts:
    sti
    ret

; cpu_disable_interrupts()
cpu_disable_interrupts:
    cli
    ret

; cpu_halt()
cpu_halt:
    hlt
    ret

; cpu_load_tr(uint16 selector)
; Windows x64: RCX = selector
cpu_load_tr:
    ltr cx
    ret

; switch_to_user_mode(uint64 entry_point, uint64 user_rsp)
; Windows x64 ABI: RCX = entry_point, RDX = user_rsp
switch_to_user_mode:
    ; Set user data segment registers (0x23 = 0x20 | 3)
    mov ax, 0x23
    mov ds, ax
    mov es, ax
    mov fs, ax
    mov gs, ax

    ; Construct iretq stack frame:
    ; [rsp + 32] = SS     (0x23)
    ; [rsp + 24] = RSP    (user_rsp in RDX)
    ; [rsp + 16] = RFLAGS (0x202: Interrupts enabled)
    ; [rsp + 8]  = CS     (0x1B)
    ; [rsp + 0]  = RIP    (entry_point in RCX)
    push qword 0x23
    push rdx
    push qword 0x202
    push qword 0x1B
    push rcx
    iretq
