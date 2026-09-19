; VMM Assembly Support Functions
; CR3 manipulation and TLB invalidation

[BITS 64]

global get_cr3
global set_cr3
global invlpg

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