import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSCPUIDFeatures(unittest.TestCase):
    def run_kale_jit(self, code: str):
        st = SourceText(code)
        diag = DiagnosticBag()
        loader = ModuleLoader([os.path.abspath(".")], diag)
        parser = Parser(st, diag)
        unit = parser.parse_compilation_unit()
        self.assertFalse(diag.has_errors, f"Parser errors: {[d.message for d in diag]}")

        binder = Binder(diag, module_loader=loader)
        bound = binder.bind_program(unit)
        self.assertFalse(diag.has_errors, f"Binder errors: {[d.message for d in diag]}")

        emitter = LLVMEmitter()
        llvm_mod = emitter.emit_module(bound)
        jit = LLVMJIT()
        return jit.run_ir(str(llvm_mod))

    def test_cpuid_vendor_string_unpacking(self):
        code = r"""
        import "os/kernel/cpuid.kl" as cpuid;

        // 1. "GenuineIntel"
        // ebx = "Genu" (0x756e6547)
        // edx = "ineI" (0x49656e69)
        // ecx = "ntel" (0x6c65746e)
        uint32 intel_ebx = 0x756e6547 as uint32;
        uint32 intel_edx = 0x49656e69 as uint32;
        uint32 intel_ecx = 0x6c65746e as uint32;

        uint8[16] v_intel;
        cpuid.cpuid_parse_vendor(intel_ebx, intel_edx, intel_ecx, &v_intel[0]);

        if (v_intel[0] != (71 as uint8)) return 1;  // 'G'
        if (v_intel[7] != (73 as uint8)) return 2;  // 'I'
        if (v_intel[11] != (108 as uint8)) return 3;// 'l'
        if (v_intel[12] != (0 as uint8)) return 4;  // '\0'

        // 2. "AuthenticAMD"
        // ebx = "Auth" (0x68747541)
        // edx = "enti" (0x69746e65)
        // ecx = "cAMD" (0x444d4163)
        uint32 amd_ebx = 0x68747541 as uint32;
        uint32 amd_edx = 0x69746e65 as uint32;
        uint32 amd_ecx = 0x444d4163 as uint32;

        uint8[16] v_amd;
        cpuid.cpuid_parse_vendor(amd_ebx, amd_edx, amd_ecx, &v_amd[0]);
        if (v_amd[0] != (65 as uint8)) return 5;   // 'A'
        if (v_amd[9] != (65 as uint8)) return 6;   // 'A'
        if (v_amd[11] != (68 as uint8)) return 7;  // 'D'
        if (v_amd[12] != (0 as uint8)) return 8;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_cpuid_family_model_decoding(self):
        code = r"""
        import "os/kernel/cpuid.kl" as cpuid;

        cpuid.CPUInfo info;

        // Intel Sandy Bridge EAX: 0x000206A7
        // Stepping: 7
        // Model: (ext_model << 4) | base_model = (2 << 4) | 10 = 32 + 10 = 42 (0x2A)
        // Family: 6
        uint32 eax_intel = 0x000206A7 as uint32;
        cpuid.cpuid_parse_family_model(eax_intel, &info);

        if (info.stepping != (7 as uint32)) return 1;
        if (info.family != (6 as uint32)) return 2;
        if (info.model != (42 as uint32)) return 3;

        // AMD Zen EAX: 0x00800F11
        // Stepping: 1
        // Base Model: 1, Ext Model: 0 -> Model = 1
        // Base Family: 15, Ext Family: 8 -> Family = 15 + 8 = 23
        uint32 eax_amd = 0x00800F11 as uint32;
        cpuid.cpuid_parse_family_model(eax_amd, &info);

        if (info.stepping != (1 as uint32)) return 4;
        if (info.family != (23 as uint32)) return 5;
        if (info.model != (1 as uint32)) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_cpuid_features_bitmask_construction(self):
        code = r"""
        import "os/kernel/cpuid.kl" as cpuid;

        cpuid.CPUInfo info;

        // edx1: FPU (bit 0) | TSC (bit 4) | APIC (bit 9) | SSE (bit 25) | SSE2 (bit 26)
        uint32 edx1 = (1 as uint32) | ((1 as uint32) << 4) | ((1 as uint32) << 9) | ((1 as uint32) << 25) | ((1 as uint32) << 26);

        // ecx1: AVX (bit 28) | RDRAND (bit 30)
        uint32 ecx1 = ((1 as uint32) << 28) | ((1 as uint32) << 30);

        // ext_edx1: NX (bit 20) | LONG_MODE (bit 29)
        uint32 ext_edx1 = ((1 as uint32) << 20) | ((1 as uint32) << 29);

        info.features = cpuid.cpuid_build_features(ecx1, edx1, ext_edx1);

        // Should have FPU, TSC, APIC, SSE, SSE2, AVX, RDRAND, NX, LONG_MODE
        if (!cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_FPU)) return 1;
        if (!cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_TSC)) return 2;
        if (!cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_APIC)) return 3;
        if (!cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_SSE)) return 4;
        if (!cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_SSE2)) return 5;
        if (!cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_AVX)) return 6;
        if (!cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_RDRAND)) return 7;
        if (!cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_NX)) return 8;
        if (!cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_LONG_MODE)) return 9;

        // Should NOT have AESNI or 1GB_PAGES
        if (cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_AESNI)) return 10;
        if (cpuid.cpuid_has_feature(&info, cpuid.CPU_FEAT_1GB_PAGES)) return 11;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
