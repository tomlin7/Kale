# Milestone 29: CPUID Architecture Probing & Hardware Feature Discovery

## Overview
Implement the CPUID feature probing architecture for Kale OS. Detects processor vendor strings (Intel, AMD), family, model, stepping, and instruction set extensions (SSE, SSE2, AVX, FMA, RDRAND, APIC, TSC-Deadline, NX/XD execute-disable bit, long mode 64-bit support). Enables dynamic kernel feature dispatch and processor-specific hardware optimization.

## Technical Architecture
1. **CPUID Function Registers (`eax`, `ebx`, `ecx`, `edx`)**:
   - Leaf `0x00000000`: Maximum basic function and 12-byte Vendor String in `ebx`, `edx`, `ecx` (`"GenuineIntel"` or `"AuthenticAMD"`).
   - Leaf `0x00000001`: Processor Info and Feature Flags:
     - `eax`: Stepping ID (bits 3:0), Model (bits 7:4), Family ID (bits 11:8), Processor Type (bits 13:12), Extended Model (bits 19:16), Extended Family (bits 27:20).
     - `ebx`: Initial APIC ID (bits 31:24), Maximum Logical Processors (bits 23:16), CLFLUSH line size (bits 15:8).
     - `ecx`: Features (SSE3, PCLMULQDQ, SSSE3, FMA, SSE4.1, SSE4.2, x2APIC, MOVBE, POPCNT, AESNI, XSAVE, OSXSAVE, AVX, RDRAND).
     - `edx`: Features (FPU, VME, DE, PSE, TSC, MSR, PAE, MCE, CX8, APIC, SEP, MTRR, PGE, MCA, CMOV, PAT, PSE36, CLFSH, MMX, FXSR, SSE, SSE2).
   - Leaf `0x80000000`: Maximum extended function.
   - Leaf `0x80000001`: Extended Processor Info:
     - `edx`: Long Mode 64-bit capable (bit 29 `LM`), No-Execute / Execute Disable bit (bit 20 `NX`), 1GB Huge Pages (bit 26 `Page1GB`).
2. **Feature Flags Bitmasks**:
   - Standardized 64-bit kernel capability mask `cpu_caps`:
     - `CAP_FPU`, `CAP_TSC`, `CAP_APIC`, `CAP_MTRR`, `CAP_SSE`, `CAP_SSE2`, `CAP_SSE3`, `CAP_SSSE3`, `CAP_SSE4_1`, `CAP_SSE4_2`, `CAP_AVX`, `CAP_FMA`, `CAP_RDRAND`, `CAP_AESNI`, `CAP_NX`, `CAP_LONG_MODE`, `CAP_1GB_PAGES`, `CAP_X2APIC`.
3. **Hardware Query Functions**:
   - `cpuid_parse_vendor(uint32 ebx, uint32 edx, uint32 ecx, uint8* vendor_dst)`.
   - `cpuid_parse_family_model(uint32 eax, CPUInfo* info)`.
   - `cpuid_build_caps(uint32 ecx1, uint32 edx1, uint32 ext_edx1) -> uint64`.
   - `cpuid_has_feature(uint64 caps, uint64 feature_mask) -> bool`.

## Deliverables
- `os/plans/029_cpuid_features.md`: Specification plan.
- `os/kernel/cpuid.kl`: Pure Kale CPUID decoder, vendor string unpacker, family/model parser, and feature detector.
- `tests/test_os_cpuid_features.py`: Test suite validating vendor string extraction, family/model decoding, feature bitmask generation, and extended capability testing.
