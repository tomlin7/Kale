import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSDesktopPanel(unittest.TestCase):
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

    def test_desktop_panel_init_and_layout(self):
        code = r"""
        import "os/kernel/desktop_panel.kl" as pnl;

        pnl.DesktopPanel p;
        pnl.panel_init(&p, 1024, 768, 32, true);

        if (p.x != 0) return 1;
        if (p.y != 736) return 2; // 768 - 32
        if (p.w != 1024 || p.h != 32) return 3;
        if (p.task_count != 0) return 4;
        if (p.clock_str[0] != (48 as uint8) || p.clock_str[2] != (58 as uint8)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_desktop_panel_task_tracking(self):
        code = r"""
        import "os/kernel/desktop_panel.kl" as pnl;

        pnl.DesktopPanel p;
        pnl.panel_init(&p, 1024, 768, 32, true);

        uint8[8] title1;
        title1[0] = 65 as uint8; // 'A'
        title1[1] = 0 as uint8;
        pnl.panel_add_task(&p, 1, &title1[0]);

        uint8[8] title2;
        title2[0] = 66 as uint8; // 'B'
        title2[1] = 0 as uint8;
        pnl.panel_add_task(&p, 2, &title2[0]);

        if (p.task_count != 2) return 1;

        // Focus task 2
        pnl.panel_set_focused_task(&p, 2);
        if (p.tasks[0].is_focused) return 2;
        if (!p.tasks[1].is_focused) return 3;

        // Remove task 1
        pnl.panel_remove_task(&p, 1);
        if (p.task_count != 1) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_desktop_panel_clock_applet(self):
        code = r"""
        import "os/kernel/desktop_panel.kl" as pnl;

        pnl.DesktopPanel p;
        pnl.panel_init(&p, 1024, 768, 32, true);

        // Update to 15:42
        pnl.panel_update_clock(&p, 15, 42);
        // '1', '5', ':', '4', '2', '\0'
        if (p.clock_str[0] != (49 as uint8)) return 1; // '1'
        if (p.clock_str[1] != (53 as uint8)) return 2; // '5'
        if (p.clock_str[2] != (58 as uint8)) return 3; // ':'
        if (p.clock_str[3] != (52 as uint8)) return 4; // '4'
        if (p.clock_str[4] != (50 as uint8)) return 5; // '2'
        if (p.clock_str[5] != (0 as uint8)) return 6;

        // Update to 09:05
        pnl.panel_update_clock(&p, 9, 5);
        if (p.clock_str[0] != (48 as uint8)) return 7; // '0'
        if (p.clock_str[1] != (57 as uint8)) return 8; // '9'
        if (p.clock_str[3] != (48 as uint8)) return 9; // '0'
        if (p.clock_str[4] != (53 as uint8)) return 10;// '5'

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_notification_posting_and_position(self):
        code = r"""
        import "os/kernel/desktop_panel.kl" as pnl;

        pnl.NotificationCenter nc;
        pnl.notification_center_init(&nc, 1024, 768);

        uint8[16] title;
        title[0] = 84 as uint8; // 'T'
        title[1] = 0 as uint8;

        uint8[16] body;
        body[0] = 66 as uint8;  // 'B'
        body[1] = 0 as uint8;

        int id = pnl.notification_post(&nc, &title[0], &body[0], 5000);
        if (id <= 0) return 1;
        if (nc.active_count != 1) return 2;

        // Toast 0: x = 1024 - 240 - 20 = 764, y = 20
        if (nc.toasts[0].x != 764) return 3;
        if (nc.toasts[0].y != 20) return 4;
        if (nc.toasts[0].duration_ms != 5000) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_notification_auto_dismiss_timer(self):
        code = r"""
        import "os/kernel/desktop_panel.kl" as pnl;

        pnl.NotificationCenter nc;
        pnl.notification_center_init(&nc, 1024, 768);

        int id = pnl.notification_post(&nc, null, null, 4000);

        // Advance 2000 ms: remaining should be 2000 ms
        pnl.notification_tick(&nc, 2000);
        if (nc.active_count != 1) return 1;
        if (nc.toasts[0].remaining_ms != 2000) return 2;

        // Advance another 2500 ms: toast should auto-dismiss
        pnl.notification_tick(&nc, 2500);
        if (nc.active_count != 0) return 3;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_notification_manual_dismiss(self):
        code = r"""
        import "os/kernel/desktop_panel.kl" as pnl;

        pnl.NotificationCenter nc;
        pnl.notification_center_init(&nc, 1024, 768);

        int id = pnl.notification_post(&nc, null, null, 10000);
        if (nc.active_count != 1) return 1;

        pnl.notification_dismiss(&nc, id);
        if (nc.active_count != 0) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
