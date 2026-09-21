import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSRTCCMOS(unittest.TestCase):
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

    def test_rtc_bcd_to_binary(self):
        code = """
        import "os/drivers/rtc.kl" as rtc;

        if (rtc.rtc_bcd_to_binary(0x00 as uint8) != (0 as uint8)) return 1;
        if (rtc.rtc_bcd_to_binary(0x09 as uint8) != (9 as uint8)) return 2;
        if (rtc.rtc_bcd_to_binary(0x10 as uint8) != (10 as uint8)) return 3;
        if (rtc.rtc_bcd_to_binary(0x59 as uint8) != (59 as uint8)) return 4;
        if (rtc.rtc_bcd_to_binary(0x99 as uint8) != (99 as uint8)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_rtc_leap_year_and_days_in_month(self):
        code = """
        import "os/drivers/rtc.kl" as rtc;

        // 2000 is divisible by 400 -> leap year
        if (!rtc.rtc_is_leap_year(2000 as uint16)) return 1;
        // 1900 is divisible by 100 but not 400 -> not leap
        if (rtc.rtc_is_leap_year(1900 as uint16)) return 2;
        // 2024 is divisible by 4 -> leap year
        if (!rtc.rtc_is_leap_year(2024 as uint16)) return 3;
        // 2026 -> not leap
        if (rtc.rtc_is_leap_year(2026 as uint16)) return 4;

        // Days in Feb: 2024 has 29, 2026 has 28
        if (rtc.rtc_days_in_month(2024 as uint16, 2 as uint8) != 29) return 5;
        if (rtc.rtc_days_in_month(2026 as uint16, 2 as uint8) != 28) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_rtc_register_decoding_bcd_24h(self):
        code = """
        import "os/drivers/rtc.kl" as rtc;

        // Mock BCD CMOS values for: 2026-09-21 14:30:45
        // Status B: 24h mode (0x02), BCD mode (bit 2 is 0)
        uint8 status_b = rtc.RTC_STATUS_B_24H;
        uint8 sec = 0x45 as uint8;
        uint8 min = 0x30 as uint8;
        uint8 hr  = 0x14 as uint8;
        uint8 day = 0x21 as uint8;
        uint8 mon = 0x09 as uint8;
        uint8 yr  = 0x26 as uint8;
        uint8 cen = 0x20 as uint8; // Century 20

        rtc.RTCDateTime dt;
        bool ok = rtc.rtc_decode_registers(&dt, sec, min, hr, day, mon, yr, cen, status_b);

        if (!ok || !dt.is_valid) return 1;
        if (dt.year != (2026 as uint16)) return 2;
        if (dt.month != (9 as uint8) || dt.day != (21 as uint8)) return 3;
        if (dt.hour != (14 as uint8) || dt.minute != (30 as uint8) || dt.second != (45 as uint8)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_rtc_register_decoding_12h_pm(self):
        code = """
        import "os/drivers/rtc.kl" as rtc;

        // Status B: 12h mode (bit 1 is 0), Binary mode (bit 2 is 1: 0x04)
        uint8 status_b = rtc.RTC_STATUS_B_BINARY;
        // Hour: 2 PM (0x80 | 2 = 130) -> should decode to 14:00
        uint8 hr = 0x82 as uint8;

        rtc.RTCDateTime dt;
        bool ok = rtc.rtc_decode_registers(
            &dt,
            0 as uint8, 0 as uint8, hr,
            1 as uint8, 1 as uint8, 26 as uint8, 20 as uint8,
            status_b
        );

        if (!ok || !dt.is_valid) return 1;
        if (dt.hour != (14 as uint8)) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_rtc_unix_epoch_timestamp(self):
        code = """
        import "os/drivers/rtc.kl" as rtc;

        // 1. Exact Unix Epoch: 1970-01-01 00:00:00 -> 0
        rtc.RTCDateTime ep0;
        ep0.year = 1970 as uint16; ep0.month = 1 as uint8; ep0.day = 1 as uint8;
        ep0.hour = 0 as uint8; ep0.minute = 0 as uint8; ep0.second = 0 as uint8;
        ep0.is_valid = true;

        uint64 ts0 = rtc.rtc_to_unix_epoch(&ep0);
        if (ts0 != (0 as uint64)) return 1;

        // 2. Y2K: 2000-01-01 00:00:00 -> 946684800
        rtc.RTCDateTime y2k;
        y2k.year = 2000 as uint16; y2k.month = 1 as uint8; y2k.day = 1 as uint8;
        y2k.hour = 0 as uint8; y2k.minute = 0 as uint8; y2k.second = 0 as uint8;
        y2k.is_valid = true;

        uint64 ts_y2k = rtc.rtc_to_unix_epoch(&y2k);
        if (ts_y2k != (946684800 as uint64)) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_rtc_periodic_interrupt_rates(self):
        code = """
        import "os/drivers/rtc.kl" as rtc;

        if (rtc.rtc_calc_periodic_rate(3 as uint8) != (8192 as uint32)) return 1;
        if (rtc.rtc_calc_periodic_rate(6 as uint8) != (1024 as uint32)) return 2;
        if (rtc.rtc_calc_periodic_rate(10 as uint8) != (64 as uint32)) return 3;
        if (rtc.rtc_calc_periodic_rate(15 as uint8) != (2 as uint32)) return 4;
        if (rtc.rtc_calc_periodic_rate(2 as uint8) != (0 as uint32)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
