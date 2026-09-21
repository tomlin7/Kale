# Milestone 23: Dynamic Linker & ELF64 Relocation Engine

## Overview
Implement an in-kernel and user-space Dynamic Linker (`ld.so`) subsystem for Kale OS. Enables dynamic loading of shared ELF64 objects (`.so`), symbol resolution across dependent libraries, and runtime relocation applying Global Offset Table (GOT) and Procedure Linkage Table (PLT) fixups.

## Technical Architecture
1. **ELF64 Dynamic Section (`PT_DYNAMIC`)**:
   - `Elf64_Dyn` entries containing `d_tag` and `d_val`/`d_ptr`.
   - Core tags: `DT_NULL` (0), `DT_NEEDED` (1), `DT_PLTGOT` (3), `DT_HASH` (4), `DT_STRTAB` (5), `DT_SYMTAB` (6), `DT_RELA` (7), `DT_RELASZ` (8), `DT_RELAENT` (9), `DT_JMPREL` (23).
2. **Relocation Structure (`Elf64_Rela`)**:
   - `r_offset`: Virtual address to patch.
   - `r_info`: Encodes `(sym_index << 32) | rel_type`.
   - `r_addend`: Signed addend.
   - Supported x86_64 relocation types:
     - `R_X86_64_64` (1): `*patch_addr = S + A`
     - `R_X86_64_PC32` (2): `*patch_addr = (S + A - P)`
     - `R_X86_64_GLOB_DAT` (6): `*patch_addr = S` (sets GOT entry for global variable)
     - `R_X86_64_JUMP_SLOT` (7): `*patch_addr = S` (resolves PLT indirect jump target in GOT)
     - `R_X86_64_RELATIVE` (8): `*patch_addr = B + A` (relocates position-independent code relative to load base)
3. **Symbol Table & System V ELF Hashing**:
   - Standard ELF hash function for O(1) symbol lookup.
   - String table (`DT_STRTAB`) offset indexing.
   - Symbol binding: Local, Global, Weak.
4. **Linker Module Registry**:
   - Tracks loaded shared objects (`LoadedLib`).
   - Resolves undefined symbols by searching dependency graph.
   - Performs relocation phase over loaded text and data segments.

## Deliverables
- `os/plans/023_dynamic_linking.md`: Technical design.
- `os/kernel/dynlink.kl`: Pure Kale dynamic linker, ELF hash algorithm, and relocation engine.
- `tests/test_os_dynamic_linking.py`: Test suite validating dynamic section parsing, ELF symbol hashing, and all 5 primary x86_64 relocation calculations.
