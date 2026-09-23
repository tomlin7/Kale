import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSSettings(unittest.TestCase):
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

    def test_settings_registry_defaults_and_int(self):
        code = r"""
        import "os/kernel/settings.kl" as set;

        set.SettingsRegistry reg;
        set.settings_init(&reg);

        // Check defaults
        if (set.settings_get_int(&reg, "display.width", 0) != 1024) return 1;
        if (set.settings_get_int(&reg, "display.height", 0) != 768) return 2;
        if (set.settings_get_int(&reg, "sound.master_volume", 0) != 80) return 3;

        // Overwrite setting
        set.settings_set_int(&reg, "display.width", 1920);
        if (set.settings_get_int(&reg, "display.width", 0) != 1920) return 4;

        // Missing key fallback
        if (set.settings_get_int(&reg, "non.existent", 999) != 999) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_settings_bool_and_string(self):
        code = r"""
        import "os/kernel/settings.kl" as set;

        set.SettingsRegistry reg;
        set.settings_init(&reg);

        if (!set.settings_get_bool(&reg, "theme.dark_mode", false)) return 1;
        if (set.settings_get_bool(&reg, "sound.muted", true)) return 2;

        set.settings_set_bool(&reg, "theme.dark_mode", false);
        if (set.settings_get_bool(&reg, "theme.dark_mode", true)) return 3;

        // String setting
        char[32] host;
        bool ok = set.settings_get_str(&reg, "net.hostname", &host[0], 32);
        if (!ok || host[0] != (107 as char) || host[1] != (97 as char)) return 4; // 'k', 'a'

        set.settings_set_str(&reg, "net.hostname", "my-workstation");
        set.settings_get_str(&reg, "net.hostname", &host[0], 32);
        if (host[0] != (109 as char) || host[1] != (121 as char)) return 5; // 'm', 'y'

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_telemetry_sampling(self):
        code = r"""
        import "os/kernel/settings.kl" as set;

        set.SystemTelemetry telem;
        
        // 250 active ticks out of 1000 total -> 25% CPU
        // 65536 KB RAM total, 16384 KB used -> 25% RAM used, 49152 KB free
        // 5000 PIT ticks at 1000Hz -> 5 seconds uptime
        // 8 processes, 3 windows
        set.telemetry_sample(
            &telem,
            250 as uint32,
            1000 as uint32,
            65536 as uint64,
            16384 as uint64,
            5000 as uint64,
            8 as uint32,
            3 as uint32
        );

        if (telem.cpu_load_percent != (25 as uint32)) return 1;
        if (telem.ram_total_kb != (65536 as uint64)) return 2;
        if (telem.ram_used_kb != (16384 as uint64)) return 3;
        if (telem.ram_free_kb != (49152 as uint64)) return 4;
        if (telem.ram_usage_percent != (25 as uint32)) return 5;
        if (telem.uptime_seconds != (5 as uint64)) return 6;
        if (telem.active_processes != (8 as uint32)) return 7;
        if (telem.active_windows != (3 as uint32)) return 8;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
