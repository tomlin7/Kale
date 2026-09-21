import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSSMPMultiCore(unittest.TestCase):
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

    def test_lapic_register_constants_and_svr(self):
        code = """
        import "os/kernel/smp.kl" as smp;

        if (smp.LAPIC_REG_ID != (0x0020 as uint32)) return 1;
        if (smp.LAPIC_REG_EOI != (0x00B0 as uint32)) return 2;
        if (smp.LAPIC_REG_ICR_LOW != (0x0300 as uint32)) return 3;
        if (smp.LAPIC_REG_ICR_HIGH != (0x0310 as uint32)) return 4;

        // SVR with software enable (bit 8) and vector 0xFF
        uint32 svr_val = smp.LAPIC_SVR_ENABLE | smp.LAPIC_SPURIOUS_VEC;
        if (svr_val != (0x000001FF as uint32)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ipi_icr_command_generation(self):
        code = """
        import "os/kernel/smp.kl" as smp;

        // 1. INIT IPI
        // Delivery=5 (0x500), Assert=1 (0x4000), Trigger=Level (0x8000)
        // Expected: 0x0000C500
        uint32 init_cmd = smp.smp_make_init_ipi();
        if (init_cmd != (0x0000C500 as uint32)) {
            return 1;
        }

        // 2. Startup IPI (SIPI) for trampoline at 0x8000 (page vector 0x08)
        // Delivery=6 (0x600), Assert=1 (0x4000), Trigger=Edge (0), Vector=0x08
        // Expected: 0x00004608
        uint32 sipi_cmd = smp.smp_make_sipi(0x08 as uint8);
        if (sipi_cmd != (0x00004608 as uint32)) {
            return 2;
        }

        // 3. ICR High for target APIC ID = 3
        // Shifted by 24 -> 3 << 24 = 0x03000000
        uint32 icr_high = smp.smp_make_icr_high(3 as uint8);
        if (icr_high != (0x03000000 as uint32)) {
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_smp_manager_core_registration(self):
        code = """
        import "os/kernel/smp.kl" as smp;

        smp.SMPManager mgr;
        // Init with LAPIC base 0xFEE00000, BSP LAPIC ID 0
        smp.smp_init(&mgr, 0xFEE00000 as uint64, 0 as uint8);

        if (mgr.total_cores != (1 as uint32) || mgr.online_cores != (1 as uint32)) {
            return 1;
        }
        if (mgr.cores[0].lapic_id != (0 as uint8) || !mgr.cores[0].is_bsp) {
            return 2;
        }
        if (mgr.cores[0].state != smp.CORE_STATE_ONLINE) {
            return 3;
        }

        // Register Application Processor 1 (LAPIC ID 1)
        int id1 = smp.smp_register_core(&mgr, 1 as uint8, 0x00300000 as uint64);
        if (id1 != 1 || mgr.total_cores != (2 as uint32) || mgr.online_cores != (1 as uint32)) {
            return 4;
        }

        // Register Application Processor 2 (LAPIC ID 2)
        int id2 = smp.smp_register_core(&mgr, 2 as uint8, 0x00400000 as uint64);
        if (id2 != 2 || mgr.total_cores != (3 as uint32)) {
            return 5;
        }

        smp.CPUCore* core1 = smp.smp_get_core(&mgr, 1 as uint8);
        if (core1 == null || core1->lapic_id != (1 as uint8) || core1->stack_top != (0x00300000 as uint64)) {
            return 6;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_smp_core_state_transitions(self):
        code = """
        import "os/kernel/smp.kl" as smp;

        smp.SMPManager mgr;
        smp.smp_init(&mgr, 0xFEE00000 as uint64, 0 as uint8);

        int ap1 = smp.smp_register_core(&mgr, 1 as uint8, 0x00300000 as uint64);
        // Initially in BOOTING state
        if (mgr.online_cores != (1 as uint32)) {
            return 1;
        }

        // Core 1 successfully wakes up and sets ONLINE
        smp.smp_set_core_state(&mgr, 1 as uint8, smp.CORE_STATE_ONLINE);
        if (mgr.online_cores != (2 as uint32)) {
            return 2;
        }

        // Core 1 halted
        smp.smp_set_core_state(&mgr, 1 as uint8, smp.CORE_STATE_HALTED);
        if (mgr.online_cores != (1 as uint32)) {
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ticket_spinlock_fifo_ordering(self):
        code = """
        import "os/kernel/smp.kl" as smp;

        smp.Spinlock lock;
        smp.spinlock_init(&lock);

        if (smp.spinlock_is_locked(&lock)) {
            return 1;
        }

        uint32 ticket1 = 0 as uint32;
        smp.spinlock_acquire(&lock, &ticket1);

        if (ticket1 != (0 as uint32)) return 2;
        if (!smp.spinlock_is_locked(&lock)) return 3;

        // Core 2 acquires ticket
        uint32 ticket2 = 0 as uint32;
        smp.spinlock_acquire(&lock, &ticket2);
        if (ticket2 != (1 as uint32)) return 4;

        // Core 1 releases lock
        smp.spinlock_release(&lock);
        // Still locked because Core 2 holds ticket 1
        if (!smp.spinlock_is_locked(&lock)) return 5;
        if (lock.now_serving != (1 as uint32)) return 6;

        // Core 2 releases lock
        smp.spinlock_release(&lock);
        if (smp.spinlock_is_locked(&lock)) return 7;
        if (lock.now_serving != (2 as uint32)) return 8;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
