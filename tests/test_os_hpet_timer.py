import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSHPETTimer(unittest.TestCase):
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

    def test_hpet_init_capabilities(self):
        code = r"""
        import "os/drivers/hpet.kl" as hpet;

        hpet.HPETDevice dev;
        uint64 base = 0xFED00000 as uint64;

        // GCAP_ID:
        // Period: 100,000,000 fs (0x05F5E100) in upper 32 bits
        // Vendor: 0x8086 in bits 31:16
        // 64-bit counter: bit 13 (0x2000)
        // 3 timers: bits 12:8 = 2 (0x0200)
        uint64 hi = (0x05F5E100 as uint64) << (32 as uint64);
        uint64 lo = 0x80862200 as uint64;
        uint64 gcap = hi | lo;

        hpet.hpet_init(&dev, base, gcap);

        if (dev.base_addr != base) return 1;
        if (dev.clk_period_fs != (100000000 as uint32)) return 2;
        if (dev.vendor_id != (0x8086 as uint16)) return 3;
        if (!dev.is_64bit_counter) return 4;
        if (dev.timer_count != 3) return 5;
        // Frequency should be 10 MHz (10,000,000 Hz)
        if (dev.frequency_hz != (10000000 as uint64)) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_hpet_ticks_to_nanoseconds(self):
        code = r"""
        import "os/drivers/hpet.kl" as hpet;

        hpet.HPETDevice dev;
        dev.clk_period_fs = 100000000 as uint32; // 100 ns per tick

        // 1 tick = 100 ns
        uint64 ns1 = hpet.hpet_ticks_to_nanos(&dev, 1 as uint64);
        if (ns1 != (100 as uint64)) return 1;

        // 10 ticks = 1000 ns
        uint64 ns10 = hpet.hpet_ticks_to_nanos(&dev, 10 as uint64);
        if (ns10 != (1000 as uint64)) return 2;

        // 10,000,000 ticks = 1,000,000,000 ns (1 second)
        uint64 ns_1s = hpet.hpet_ticks_to_nanos(&dev, 10000000 as uint64);
        if (ns_1s != (1000000000 as uint64)) return 3;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_hpet_ticks_to_microseconds(self):
        code = r"""
        import "os/drivers/hpet.kl" as hpet;

        hpet.HPETDevice dev;
        dev.clk_period_fs = 100000000 as uint32; // 100 ns per tick

        // 10,000 ticks = 1,000 us (1 ms)
        uint64 us_1ms = hpet.hpet_ticks_to_micros(&dev, 10000 as uint64);
        if (us_1ms != (1000 as uint64)) return 1;

        // 10,000,000 ticks = 1,000,000 us
        uint64 us_1s = hpet.hpet_ticks_to_micros(&dev, 10000000 as uint64);
        if (us_1s != (1000000 as uint64)) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_hpet_nanos_to_ticks(self):
        code = r"""
        import "os/drivers/hpet.kl" as hpet;

        hpet.HPETDevice dev;
        dev.clk_period_fs = 100000000 as uint32; // 100 ns per tick

        // 500 ns = 5 ticks
        uint64 ticks5 = hpet.hpet_nanos_to_ticks(&dev, 500 as uint64);
        if (ticks5 != (5 as uint64)) return 1;

        // 1,000,000 ns (1 ms) = 10,000 ticks
        uint64 ticks_1ms = hpet.hpet_nanos_to_ticks(&dev, 1000000 as uint64);
        if (ticks_1ms != (10000 as uint64)) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_hpet_get_time_posix_timespec(self):
        code = r"""
        import "os/drivers/hpet.kl" as hpet;

        hpet.HPETDevice dev;
        dev.clk_period_fs = 100000000 as uint32; // 100 ns per tick

        // 25,500,000 ticks = 2,550,000,000 ns = 2 sec + 550,000,000 ns
        hpet.Timespec ts;
        hpet.hpet_get_time(&dev, 25500000 as uint64, &ts);

        if (ts.tv_sec != (2 as int64)) return 1;
        if (ts.tv_nsec != (550000000 as int64)) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_hpet_timer_comparator_setup(self):
        code = r"""
        import "os/drivers/hpet.kl" as hpet;

        hpet.HPETDevice dev;
        dev.timer_count = 3;

        // Setup Timer 0: periodic, comp = 1000, interrupt enabled
        hpet.hpet_setup_timer(&dev, 0, 1000 as uint64, true, true);
        if (dev.timers[0].comp != (1000 as uint64)) return 1;
        if (!dev.timers[0].is_periodic) return 2;
        if (!dev.timers[0].is_enabled) return 3;

        // Setup Timer 1: one-shot, comp = 5000, interrupt disabled
        hpet.hpet_setup_timer(&dev, 1, 5000 as uint64, false, false);
        if (dev.timers[1].comp != (5000 as uint64)) return 4;
        if (dev.timers[1].is_periodic) return 5;
        if (dev.timers[1].is_enabled) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
