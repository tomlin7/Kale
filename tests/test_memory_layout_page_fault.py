import unittest
import os
import subprocess
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestMemoryLayoutAndPageFault(unittest.TestCase):
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

    def test_canonical_address_validation(self):
        code = """
        import "os/kernel/memory_layout.kl" as mem;

        // User canonical lower start/end
        if (!mem.is_user_address(0x0000000000000000)) return 1;
        if (!mem.is_user_address(0x00007FFFFFFFFFFF)) return 2;
        if (!mem.is_user_address(0x0000000000400000)) return 3;
        if (mem.is_kernel_address(0x0000000000400000)) return 4;
        if (!mem.is_canonical_address(0x0000000000400000)) return 5;

        // Kernel canonical upper start/end
        if (!mem.is_kernel_address(0xFFFF800000000000)) return 6;
        if (!mem.is_kernel_address(0xFFFFFFFFFFFFFFFF)) return 7;
        if (!mem.is_kernel_address(0xFFFFFFFF80000000)) return 8;
        if (mem.is_user_address(0xFFFFFFFF80000000)) return 9;
        if (!mem.is_canonical_address(0xFFFFFFFF80000000)) return 10;

        // Non-canonical gap addresses
        if (mem.is_canonical_address(0x0000800000000000)) return 11;
        if (mem.is_canonical_address(0xFFFF7FFFFFFFFFFF)) return 12;
        if (mem.is_user_address(0x0000800000000000)) return 13;
        if (mem.is_kernel_address(0x0000800000000000)) return 14;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_memory_region_management(self):
        code = """
        import "os/kernel/memory_layout.kl" as mem;

        mem.init_memory_layout();
        if (mem.region_count != 8) return 1;

        // Check region bounds
        mem.MemoryRegion* r0 = &mem.memory_regions[0];
        if (r0.start != mem.KERNEL_CODE_BASE) return 2;
        if (r0.end != mem.KERNEL_CODE_END) return 3;
        if (r0.size != 0x00200000) return 4;
        if (!r0.is_kernel || r0.is_writable || !r0.is_executable) return 5;

        // Check address lookup
        mem.MemoryRegion* lookup_kheap = mem.get_region_for_address(0xFFFFFFFF80301000);
        if (lookup_kheap == null || lookup_kheap.start != mem.KERNEL_HEAP_BASE) return 6;

        mem.MemoryRegion* lookup_null = mem.get_region_for_address(0x0000000000001000);
        if (lookup_null != null) return 7;

        // Validation
        if (!mem.validate_memory_layout()) return 8;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_page_fault_error_parsing(self):
        code = """
        import "os/kernel/page_fault.kl" as pf;

        // Error code 0: Not present, read, kernel
        pf.PageFaultInfo info0 = pf.parse_page_fault_error(0);
        if (info0.error_code != 0) return 1;
        if (!info0.is_present) return 2;
        if (info0.is_write) return 3;
        if (info0.is_user) return 4;
        if (info0.is_reserved) return 5;
        if (info0.is_instruction) return 6;

        // Error code 0x1: Present protection violation, read, kernel
        pf.PageFaultInfo info1 = pf.parse_page_fault_error(1);
        if (info1.is_present) return 7;

        // Error code 0x2: Not present, write, kernel
        pf.PageFaultInfo info2 = pf.parse_page_fault_error(2);
        if (!info2.is_present || !info2.is_write || info2.is_user) return 8;

        // Error code 0x7: Present protection violation, write, user
        pf.PageFaultInfo info7 = pf.parse_page_fault_error(7);
        if (info7.is_present || !info7.is_write || !info7.is_user) return 9;

        // Error code 0x8: Reserved bit set
        pf.PageFaultInfo info8 = pf.parse_page_fault_error(8);
        if (!info8.is_reserved) return 10;

        // Error code 0x10: Instruction fetch
        pf.PageFaultInfo info10 = pf.parse_page_fault_error(16);
        if (!info10.is_instruction) return 11;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_demand_paging_logic(self):
        code = """
        import "os/kernel/memory_layout.kl" as mem;
        import "os/kernel/page_fault.kl" as pf;

        uint64 mock_phys = 0x80000;
        bool mock_alloc_called = false;
        bool mock_map_called = false;
        uint64 mock_map_flags = 0;

        fn pmm_alloc_frame(void* pmm) -> uint64 {
            mock_alloc_called = true;
            return mock_phys;
        }

        fn pmm_free_frame(void* pmm, uint64 frame) -> void {}

        fn vmm_map_page(void* vmm, void* pmm, uint64 virt, uint64 phys, uint64 flags) -> bool {
            mock_map_called = true;
            mock_map_flags = flags;
            return true;
        }

        uint8 page_buf[4096];
        uint64 virt_addr = &page_buf as uint64;

        // User write demand paging -> flags should be Present(1) | Writable(2) | User(4) = 7
        bool ok = pf.handle_demand_paging(null, null, virt_addr, true);
        if (!ok) return 1;
        if (!mock_alloc_called) return 2;
        if (!mock_map_called) return 3;
        if (mock_map_flags != 7) return 4;

        // Rejection of non-canonical address
        bool bad_ok = pf.handle_demand_paging(null, null, 0x0000800000000000, true);
        if (bad_ok) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_full_kl_test_file_execution(self):
        code = """
        import "tests/test_memory_layout_page_fault.kl" as test_suite;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 0)

if __name__ == "__main__":
    unittest.main()
