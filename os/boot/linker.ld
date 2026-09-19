/* os/boot/linker.ld
 * Higher-half x86_64 kernel linker script for Kale OS
 */

ENTRY(kmain)

SECTIONS
{
    /* The kernel will be loaded at 1MB physical address (0x100000) */
    . = 1M;

    .text ALIGN(4K) :
    {
        *(.multiboot)
        *(.text*)
    }

    .rodata ALIGN(4K) :
    {
        *(.rodata*)
    }

    .data ALIGN(4K) :
    {
        *(.data*)
    }

    .bss ALIGN(4K) :
    {
        *(COMMON)
        *(.bss*)
    }

    kernel_end = .;
}
