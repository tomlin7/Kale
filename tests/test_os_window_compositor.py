import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSWindowCompositor(unittest.TestCase):
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

    def test_compositor_alpha_blending(self):
        code = r"""
        import "os/kernel/compositor.kl" as comp;

        // 1. Completely opaque source (alpha = 255)
        uint32 c_black = 0xFF000000 as uint32;
        uint32 c_red   = 0xFFFF0000 as uint32;
        uint32 res1 = comp.compositor_blend_pixel(c_black, c_red);
        if (res1 != c_red) return 1;

        // 2. Completely transparent source (alpha = 0)
        uint32 c_trans = 0x00FF0000 as uint32;
        uint32 res2 = comp.compositor_blend_pixel(c_black, c_trans);
        if (res2 != c_black) return 2;

        // 3. 50% alpha white (0x80FFFFFF) over black (0xFF000000)
        // Red, Green, Blue should each be 128 (0x80)
        uint32 c_semi = 0x80FFFFFF as uint32;
        uint32 res3 = comp.compositor_blend_pixel(c_black, c_semi);
        uint32 r = (res3 >> 16) & (0xFF as uint32);
        uint32 g = (res3 >> 8) & (0xFF as uint32);
        uint32 b = res3 & (0xFF as uint32);

        if (r != (128 as uint32)) return 3;
        if (g != (128 as uint32)) return 4;
        if (b != (128 as uint32)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_compositor_window_lifecycle(self):
        code = r"""
        import "os/kernel/compositor.kl" as comp;

        comp.Compositor c;
        comp.compositor_init(&c, 1024, 768);

        uint8[16] title;
        title[0] = 69 as uint8; // 'E'
        title[1] = 100 as uint8;// 'd'
        title[2] = 0 as uint8;

        int w0 = comp.compositor_create_window(&c, 100, 150, 400, 300, &title[0]);
        if (w0 != 0) return 1;
        if (c.window_count != 1) return 2;
        if (c.focused_id != 0) return 3;

        comp.WindowSurface* s = &c.windows[w0];
        if (s->bounds.x != 100 || s->bounds.y != 150) return 4;
        if (s->bounds.w != 400 || s->bounds.h != 300) return 5;
        if (s->title[0] != (69 as uint8)) return 6;

        // Close window
        comp.compositor_close_window(&c, w0);
        if (c.window_count != 0) return 7;
        if (c.windows[w0].is_valid) return 8;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_compositor_move_and_resize(self):
        code = r"""
        import "os/kernel/compositor.kl" as comp;

        comp.Compositor c;
        comp.compositor_init(&c, 1024, 768);

        int w = comp.compositor_create_window(&c, 50, 50, 200, 100, null);

        // Move window by (+30, +20)
        comp.compositor_move_window(&c, w, 30, 20);
        if (c.windows[w].bounds.x != 80) return 1;
        if (c.windows[w].bounds.y != 70) return 2;

        // Resize window to (350, 250)
        comp.compositor_resize_window(&c, w, 350, 250);
        if (c.windows[w].bounds.w != 350) return 3;
        if (c.windows[w].bounds.h != 250) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_compositor_z_order_and_focus(self):
        code = r"""
        import "os/kernel/compositor.kl" as comp;

        comp.Compositor c;
        comp.compositor_init(&c, 1024, 768);

        int wA = comp.compositor_create_window(&c, 0, 0, 100, 100, null);
        int wB = comp.compositor_create_window(&c, 50, 50, 100, 100, null);

        // Initially wB has higher Z-order than wA
        if (c.windows[wB].z_order <= c.windows[wA].z_order) return 1;
        if (c.focused_id != wB) return 2;

        // Focus wA: wA should now have highest Z-order
        comp.compositor_focus_window(&c, wA);
        if (c.windows[wA].z_order <= c.windows[wB].z_order) return 3;
        if (c.focused_id != wA) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_compositor_hit_testing(self):
        code = r"""
        import "os/kernel/compositor.kl" as comp;

        comp.Compositor c;
        comp.compositor_init(&c, 1024, 768);

        // Window A: [0, 0, 100, 100]
        int wA = comp.compositor_create_window(&c, 0, 0, 100, 100, null);
        // Window B: [50, 50, 100, 100] (higher Z)
        int wB = comp.compositor_create_window(&c, 50, 50, 100, 100, null);

        // Point (20, 20) is only inside A
        if (comp.compositor_hit_test(&c, 20, 20) != wA) return 1;

        // Point (75, 75) is inside both A and B, but B is on top
        if (comp.compositor_hit_test(&c, 75, 75) != wB) return 2;

        // Point (200, 200) is outside all windows
        if (comp.compositor_hit_test(&c, 200, 200) != -1) return 3;

        // Minimize window B -> point (75, 75) should now hit A!
        comp.compositor_minimize_window(&c, wB);
        if (comp.compositor_hit_test(&c, 75, 75) != wA) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
