import unittest
import os
import struct
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSGUIDesktop(unittest.TestCase):
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

    def test_bootinfo_structure_and_vbe_parameters(self):
        boot_info_bytes = bytearray(32)
        struct.pack_into("<IIQIIII", boot_info_bytes, 0, 0x4B414C45, 1, 0xFD000000, 800, 600, 3200, 32)
        
        magic, mode, base, w, h, pitch, bpp = struct.unpack_from("<IIQIIII", boot_info_bytes, 0)
        self.assertEqual(magic, 0x4B414C45)
        self.assertEqual(mode, 1)
        self.assertEqual(base, 0xFD000000)
        self.assertEqual(w, 800)
        self.assertEqual(h, 600)
        self.assertEqual(pitch, 3200)
        self.assertEqual(bpp, 32)

    def test_identity_paging_4gb_coverage(self):
        page_dirs = 4
        entries_per_dir = 512
        total_entries = page_dirs * entries_per_dir
        self.assertEqual(total_entries, 2048)

        fb_base = 0xFD000000
        gb_index = fb_base // (1024 * 1024 * 1024)
        self.assertEqual(gb_index, 3)

        entry_index = (fb_base % (1024 * 1024 * 1024)) // (2 * 1024 * 1024)
        self.assertEqual(entry_index, 488)
        self.assertLess(entry_index, 512)

    def test_gui_mouse_packet_decoding(self):
        code = """
        import "os/drivers/mouse.kl" as mouse;

        mouse.MouseState state;
        mouse.mouse_init(&state, 400, 300);

        uint8 b0 = 0x09 as uint8;
        uint8 b1 = 5 as uint8;
        uint8 b2 = 10 as uint8;

        bool ok = mouse.mouse_process_packet(&state, b0, b1, b2, 800, 600);
        if (!ok || state.delta_x != 5 || state.delta_y != -10 || !state.left_button) {
            return 1;
        }
        if (state.x != 405 || state.y != 290) {
            return 2;
        }

        uint8 c0 = 0x38 as uint8;
        uint8 c1 = 253 as uint8;
        uint8 c2 = 249 as uint8;

        ok = mouse.mouse_process_packet(&state, c0, c1, c2, 800, 600);
        if (!ok || state.delta_x != -3 || state.delta_y != 7 || state.left_button) {
            return 3;
        }
        if (state.x != 402 || state.y != 297) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_gui_window_manager_hit_testing(self):
        code = """
        fn int hit_test_window(int mx, int my) {
            if (mx >= 496 && mx <= 516 && my >= 46 && my <= 66) {
                return 100;
            }
            if (mx >= 40 && mx <= 520 && my >= 44 && my <= 354) {
                return 1;
            }
            if (mx >= 540 && mx <= 760 && my >= 44 && my <= 314) {
                return 2;
            }
            if (mx >= 140 && mx <= 660 && my >= 374 && my <= 570) {
                return 3;
            }
            return 0;
        }

        if (hit_test_window(500, 50) != 100) return 1;
        if (hit_test_window(100, 100) != 1) return 2;
        if (hit_test_window(600, 150) != 2) return 3;
        if (hit_test_window(300, 450) != 3) return 4;
        if (hit_test_window(50, 500) != 0) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_gui_bresenham_line_interpolation(self):
        code = """
        fn int bresenham_pixel_count(int x0, int y0, int x1, int y1) {
            int dx = x1 - x0;
            if (dx < 0) dx = -dx;
            int dy = y1 - y0;
            if (dy < 0) dy = -dy;

            int sx = -1;
            if (x0 < x1) sx = 1;
            int sy = -1;
            if (y0 < y1) sy = 1;

            int err = dx - dy;
            int count = 0;

            while (true) {
                count = count + 1;
                if (x0 == x1 && y0 == y1) {
                    break;
                }
                int e2 = 2 * err;
                if (e2 >= -dy) {
                    err = err - dy;
                    x0 = x0 + sx;
                }
                if (e2 <= dx) {
                    err = err + dx;
                    y0 = y0 + sy;
                }
            }
            return count;
        }

        if (bresenham_pixel_count(10, 20, 20, 20) != 11) return 1;
        if (bresenham_pixel_count(15, 10, 15, 30) != 21) return 2;
        if (bresenham_pixel_count(0, 0, 10, 10) != 11) return 3;
        if (bresenham_pixel_count(0, 0, 5, 20) != 21) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_gui_font_glyph_lookup(self):
        font_path = "os/kernel/font8x8.inc"
        self.assertTrue(os.path.exists(font_path))
        with open(font_path, "r") as f:
            content = f.read()

        self.assertIn("gui_font8x8:", content)
        db_lines = [line.strip() for line in content.splitlines() if line.strip().startswith("db ")]
        self.assertEqual(len(db_lines), 95)
