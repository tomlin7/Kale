import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSVT100Console(unittest.TestCase):
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

    def test_vt100_init_and_clear(self):
        code = r"""
        import "os/kernel/vt100.kl" as vt;

        vt.VT100Console term;
        vt.vt100_init(&term);

        if (term.cur_x != 0 || term.cur_y != 0) return 1;
        if (term.cur_fg != vt.VT_COLOR_DEFAULT_FG) return 2;
        if (term.cur_bg != vt.VT_COLOR_DEFAULT_BG) return 3;

        // Check first and last cells
        if (term.cells[0].ch != (0x20 as uint8)) return 4;
        if (term.cells[1999].ch != (0x20 as uint8)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vt100_basic_output_and_wrap(self):
        code = r"""
        import "os/kernel/vt100.kl" as vt;

        vt.VT100Console term;
        vt.vt100_init(&term);

        // Print 'H', 'i'
        vt.vt100_putc(&term, 72 as uint8); // 'H'
        vt.vt100_putc(&term, 105 as uint8); // 'i'
        if (term.cur_x != 2 || term.cur_y != 0) return 1;
        if (term.cells[0].ch != (72 as uint8) || term.cells[1].ch != (105 as uint8)) return 2;

        // Print '\r'
        vt.vt100_putc(&term, 0x0D as uint8);
        if (term.cur_x != 0 || term.cur_y != 0) return 3;

        // Print '\n'
        vt.vt100_putc(&term, 0x0A as uint8);
        if (term.cur_x != 0 || term.cur_y != 1) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vt100_cursor_positioning_csi(self):
        code = r"""
        import "os/kernel/vt100.kl" as vt;

        vt.VT100Console term;
        vt.vt100_init(&term);

        // Sequence: \x1b[10;20H (moves to row 10, col 20 -> 0-indexed y=9, x=19)
        vt.vt100_putc(&term, 0x1B as uint8);
        vt.vt100_putc(&term, 91 as uint8);  // '['
        vt.vt100_putc(&term, 49 as uint8);  // '1'
        vt.vt100_putc(&term, 48 as uint8);  // '0'
        vt.vt100_putc(&term, 59 as uint8);  // ';'
        vt.vt100_putc(&term, 50 as uint8);  // '2'
        vt.vt100_putc(&term, 48 as uint8);  // '0'
        vt.vt100_putc(&term, 72 as uint8);  // 'H'

        if (term.cur_y != 9 || term.cur_x != 19) return 1;

        // Sequence: \x1b[3A (cursor up 3 rows -> y = 6)
        vt.vt100_putc(&term, 0x1B as uint8);
        vt.vt100_putc(&term, 91 as uint8);  // '['
        vt.vt100_putc(&term, 51 as uint8);  // '3'
        vt.vt100_putc(&term, 65 as uint8);  // 'A'

        if (term.cur_y != 6) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vt100_sgr_colors_and_attributes(self):
        code = r"""
        import "os/kernel/vt100.kl" as vt;

        vt.VT100Console term;
        vt.vt100_init(&term);

        // Sequence: \x1b[1;31m (Bold + Red foreground)
        vt.vt100_putc(&term, 0x1B as uint8);
        vt.vt100_putc(&term, 91 as uint8);  // '['
        vt.vt100_putc(&term, 49 as uint8);  // '1'
        vt.vt100_putc(&term, 59 as uint8);  // ';'
        vt.vt100_putc(&term, 51 as uint8);  // '3'
        vt.vt100_putc(&term, 49 as uint8);  // '1'
        vt.vt100_putc(&term, 109 as uint8); // 'm'

        if ((term.cur_flags & vt.VT_FLAG_BOLD) == (0 as uint8)) return 1;
        if (term.cur_fg != vt.VT_COLOR_RED) return 2;

        // Print 'A' with this style
        vt.vt100_putc(&term, 65 as uint8); // 'A'
        if (term.cells[0].ch != (65 as uint8)) return 3;
        if (term.cells[0].fg != vt.VT_COLOR_RED) return 4;
        if ((term.cells[0].flags & vt.VT_FLAG_BOLD) == (0 as uint8)) return 5;

        // Reset: \x1b[0m
        vt.vt100_putc(&term, 0x1B as uint8);
        vt.vt100_putc(&term, 91 as uint8);  // '['
        vt.vt100_putc(&term, 48 as uint8);  // '0'
        vt.vt100_putc(&term, 109 as uint8); // 'm'

        if (term.cur_fg != vt.VT_COLOR_DEFAULT_FG) return 6;
        if (term.cur_flags != vt.VT_FLAG_NONE) return 7;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vt100_line_and_screen_clear(self):
        code = r"""
        import "os/kernel/vt100.kl" as vt;

        vt.VT100Console term;
        vt.vt100_init(&term);

        // Put 'X' at (0, 0)
        vt.vt100_putc(&term, 88 as uint8);
        if (term.cells[0].ch != (88 as uint8)) return 1;

        // Clear screen: \x1b[2J
        vt.vt100_putc(&term, 0x1B as uint8);
        vt.vt100_putc(&term, 91 as uint8); // '['
        vt.vt100_putc(&term, 50 as uint8); // '2'
        vt.vt100_putc(&term, 74 as uint8); // 'J'

        // (0, 0) should now be space (0x20) and cursor at (0, 0)
        if (term.cells[0].ch != (0x20 as uint8)) return 2;
        if (term.cur_x != 0 || term.cur_y != 0) return 3;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vt100_scrolling(self):
        code = r"""
        import "os/kernel/vt100.kl" as vt;

        vt.VT100Console term;
        vt.vt100_init(&term);

        // Write '1' at row 0, col 0
        term.cells[0].ch = 49 as uint8; // '1'
        // Write '2' at row 1, col 0
        term.cells[80].ch = 50 as uint8; // '2'

        // Place cursor at row 24 (bottom) and send newline
        term.cur_y = 24;
        vt.vt100_putc(&term, 0x0A as uint8); // '\n'

        // Row 0 should now have '2' (scrolled up)
        if (term.cells[0].ch != (50 as uint8)) return 1;
        // Bottom row should be space
        if (term.cells[24 * 80].ch != (0x20 as uint8)) return 2;
        // Cursor stays at row 24
        if (term.cur_y != 24) return 3;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vt100_save_and_restore_cursor(self):
        code = r"""
        import "os/kernel/vt100.kl" as vt;

        vt.VT100Console term;
        vt.vt100_init(&term);

        term.cur_x = 15;
        term.cur_y = 7;

        // Save cursor: \x1b7
        vt.vt100_putc(&term, 0x1B as uint8);
        vt.vt100_putc(&term, 55 as uint8); // '7'

        // Move cursor
        term.cur_x = 0;
        term.cur_y = 0;

        // Restore cursor: \x1b8
        vt.vt100_putc(&term, 0x1B as uint8);
        vt.vt100_putc(&term, 56 as uint8); // '8'

        if (term.cur_x != 15 || term.cur_y != 7) return 1;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
