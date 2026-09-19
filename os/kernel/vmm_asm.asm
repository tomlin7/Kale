; VMM Assembly Support Functions
; CR3 manipulation, TLB invalidation, and CR2 access

[BITS 64]

global get_cr3
global set_cr3
global invlpg
global get_cr2

; Get CR3 register value
get_cr3:
    mov rax, cr3
    ret

; Set CR3 register value
set_cr3:
    mov cr3, rdi
    ret

; Invalidate TLB entry for specific address
invlpg:
    invlpg [rdi]
    ret

; Get CR2 register value (page fault address)
get_cr2:
    mov rax, cr2
    ret