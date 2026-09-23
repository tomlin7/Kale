import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSWorkspaces(unittest.TestCase):
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

    def test_workspace_init_and_switching(self):
        code = r"""
        import "os/kernel/workspace.kl" as ws;

        ws.WorkspaceManager mgr;
        ws.ws_init(&mgr);

        if (ws.ws_get_active(&mgr) != (1 as uint32)) return 1;
        if (mgr.monitors[0].width != 1024 || mgr.monitors[0].height != 768) return 2;
        if (!mgr.monitors[0].is_active) return 3;
        if (mgr.monitors[1].is_active) return 4;

        // Switch workspace
        bool ok = ws.ws_set_active(&mgr, 3 as uint32);
        if (!ok || ws.ws_get_active(&mgr) != (3 as uint32)) return 5;

        // Out of bounds check
        if (ws.ws_set_active(&mgr, 5 as uint32)) return 6;
        if (ws.ws_set_active(&mgr, 0 as uint32)) return 7;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_workspace_cycle(self):
        code = r"""
        import "os/kernel/workspace.kl" as ws;

        ws.WorkspaceManager mgr;
        ws.ws_init(&mgr);

        // 1 -> 2 -> 3 -> 4 -> 1
        if (ws.ws_cycle_next(&mgr) != (2 as uint32)) return 1;
        if (ws.ws_cycle_next(&mgr) != (3 as uint32)) return 2;
        if (ws.ws_cycle_next(&mgr) != (4 as uint32)) return 3;
        if (ws.ws_cycle_next(&mgr) != (1 as uint32)) return 4;

        // Cycle prev: 1 -> 4 -> 3
        if (ws.ws_cycle_prev(&mgr) != (4 as uint32)) return 5;
        if (ws.ws_cycle_prev(&mgr) != (3 as uint32)) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_window_assignment_and_sticky(self):
        code = r"""
        import "os/kernel/workspace.kl" as ws;

        ws.WorkspaceManager mgr;
        ws.ws_init(&mgr);

        // Window 1 on Desk 1, Window 2 moved to Desk 2
        ws.ws_assign_window(&mgr, 2 as uint32, 2 as uint32);
        if (ws.ws_get_window_workspace(&mgr, 2 as uint32) != (2 as uint32)) return 1;

        // On Desk 1: Win 1 is visible, Win 2 is not
        if (!ws.ws_is_window_visible_on_active(&mgr, 1 as uint32)) return 2;
        if (ws.ws_is_window_visible_on_active(&mgr, 2 as uint32)) return 3;

        // Switch to Desk 2: Win 1 not visible, Win 2 is visible
        ws.ws_set_active(&mgr, 2 as uint32);
        if (ws.ws_is_window_visible_on_active(&mgr, 1 as uint32)) return 4;
        if (!ws.ws_is_window_visible_on_active(&mgr, 2 as uint32)) return 5;

        // Make Window 1 sticky: visible on Desk 2 as well!
        ws.ws_set_window_sticky(&mgr, 1 as uint32, true);
        if (!ws.ws_is_window_sticky(&mgr, 1 as uint32)) return 6;
        if (!ws.ws_is_window_visible_on_active(&mgr, 1 as uint32)) return 7;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_multi_monitor_and_window_migration(self):
        code = r"""
        import "os/kernel/workspace.kl" as ws;

        ws.WorkspaceManager mgr;
        ws.ws_init(&mgr);

        // Enable secondary monitor at (1024, 0) 800x600
        ws.ws_enable_secondary_monitor(&mgr, 1024, 0, 800, 600);
        if (mgr.monitor_count != (2 as uint32)) return 1;

        // Test coordinate hit testing
        if (ws.ws_get_monitor_for_coords(&mgr, 500, 300) != 0) return 2;
        if (ws.ws_get_monitor_for_coords(&mgr, 1200, 200) != 1) return 3;

        // Move window from Mon 0 (100, 150) to Mon 1
        int32 win_x = 100;
        int32 win_y = 150;
        bool ok = ws.ws_move_window_to_monitor(&mgr, &win_x, &win_y, 1);
        if (!ok) return 4;
        if (win_x != 1124 || win_y != 150) return 5; // 1024 + 100 = 1124
        if (ws.ws_get_monitor_for_coords(&mgr, win_x, win_y) != 1) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
