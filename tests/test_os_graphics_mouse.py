import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSGraphicsMouse(unittest.TestCase):
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

    def test_framebuffer_init_and_clipping(self):
        code = """
        import "os/drivers/fb.kl" as fb;

        uint32[100] dummy_buf;
        fb.Framebuffer frame;
        fb.fb_init(&frame, &dummy_buf[0], null, 10 as uint32, 10 as uint32, 40 as uint32);

        if (frame.width != (10 as uint32) || frame.height != (10 as uint32) || frame.pitch != (40 as uint32)) {
            return 1;
        }
        if (frame.clip.x1 != 0 || frame.clip.y1 != 0 || frame.clip.x2 != 9 || frame.clip.y2 != 9) {
            return 2;
        }

        // Tighten clip rect
        fb.fb_set_clip(&frame, 2, 2, 7, 7);
        if (frame.clip.x1 != 2 || frame.clip.y1 != 2 || frame.clip.x2 != 7 || frame.clip.y2 != 7) {
            return 3;
        }

        // Reset clip rect
        fb.fb_reset_clip(&frame);
        if (frame.clip.x1 != 0 || frame.clip.y1 != 0 || frame.clip.x2 != 9 || frame.clip.y2 != 9) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_framebuffer_pixel_put_and_scissor_clipping(self):
        code = """
        import "os/drivers/fb.kl" as fb;

        uint32[100] buffer;
        int i = 0;
        while (i < 100) {
            buffer[i] = 0 as uint32;
            i = i + 1;
        }

        fb.Framebuffer frame;
        fb.fb_init(&frame, &buffer[0], null, 10 as uint32, 10 as uint32, 40 as uint32);
        fb.fb_set_clip(&frame, 2, 2, 6, 6);

        // Put pixel outside clip rect (should be ignored)
        fb.fb_put_pixel_clip(&frame, 1, 1, 0xFFFFFFFF as uint32);
        if (fb.fb_get_pixel(&frame, 1, 1) != (0 as uint32)) {
            return 1;
        }

        // Put pixel way out of bounds (negative & beyond size)
        fb.fb_put_pixel_clip(&frame, -5, -5, 0xFFFFFFFF as uint32);
        fb.fb_put_pixel_clip(&frame, 50, 50, 0xFFFFFFFF as uint32);

        // Put pixel inside clip rect
        fb.fb_put_pixel_clip(&frame, 4, 4, 0x00FF00FF as uint32);
        if (fb.fb_get_pixel(&frame, 4, 4) != (0x00FF00FF as uint32)) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_framebuffer_double_buffering_swap(self):
        code = """
        import "os/drivers/fb.kl" as fb;

        uint32[64] front;
        uint32[64] back;
        int i = 0;
        while (i < 64) {
            front[i] = 0 as uint32;
            back[i] = 0 as uint32;
            i = i + 1;
        }

        fb.Framebuffer frame;
        fb.fb_init(&frame, &front[0], &back[0], 8 as uint32, 8 as uint32, 32 as uint32);

        if (!frame.double_buffered) {
            return 1;
        }

        // Draw to back buffer
        fb.fb_put_pixel_clip(&frame, 3, 3, 0x12345678 as uint32);

        // Front buffer must still be untouched
        if (front[3 * 8 + 3] != (0 as uint32)) {
            return 2;
        }
        if (back[3 * 8 + 3] != (0x12345678 as uint32)) {
            return 3;
        }

        // Swap buffers
        fb.fb_swap_buffers(&frame);

        // Front buffer must now contain the pixel
        if (front[3 * 8 + 3] != (0x12345678 as uint32)) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_bresenham_line_drawing(self):
        code = """
        import "os/drivers/fb.kl" as fb;

        uint32[100] buffer;
        int i = 0;
        while (i < 100) {
            buffer[i] = 0 as uint32;
            i = i + 1;
        }

        fb.Framebuffer frame;
        fb.fb_init(&frame, &buffer[0], null, 10 as uint32, 10 as uint32, 40 as uint32);

        // Draw diagonal line from (1, 1) to (5, 5)
        fb.fb_draw_line(&frame, 1, 1, 5, 5, 0x00FF0000 as uint32);

        int p = 1;
        while (p <= 5) {
            if (fb.fb_get_pixel(&frame, p, p) != (0x00FF0000 as uint32)) {
                return 1;
            }
            p = p + 1;
        }

        // Draw horizontal line from (2, 8) to (7, 8)
        fb.fb_draw_line(&frame, 2, 8, 7, 8, 0x0000FF00 as uint32);
        p = 2;
        while (p <= 7) {
            if (fb.fb_get_pixel(&frame, p, 8) != (0x0000FF00 as uint32)) {
                return 2;
            }
            p = p + 1;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_rectangle_rasterization(self):
        code = """
        import "os/drivers/fb.kl" as fb;

        uint32[100] buffer;
        int i = 0;
        while (i < 100) {
            buffer[i] = 0 as uint32;
            i = i + 1;
        }

        fb.Framebuffer frame;
        fb.fb_init(&frame, &buffer[0], null, 10 as uint32, 10 as uint32, 40 as uint32);

        // Fill rect at (2, 2) size 3x3
        fb.fb_fill_rect(&frame, 2, 2, 3, 3, 0x000000FF as uint32);

        int y = 2;
        while (y <= 4) {
            int x = 2;
            while (x <= 4) {
                if (fb.fb_get_pixel(&frame, x, y) != (0x000000FF as uint32)) {
                    return 1;
                }
                x = x + 1;
            }
            y = y + 1;
        }

        // Unfilled outside
        if (fb.fb_get_pixel(&frame, 1, 1) != (0 as uint32)) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_alpha_channel_compositing(self):
        code = """
        import "os/drivers/fb.kl" as fb;

        // 1. Alpha = 0 (100% background)
        uint32 fg = 0xFFFF0000 as uint32; // Red
        uint32 bg = 0xFF0000FF as uint32; // Blue
        uint32 b0 = fb.color_alpha_blend(fg, bg, 0 as uint32);
        if (b0 != bg) {
            return 1;
        }

        // 2. Alpha = 255 (100% foreground)
        uint32 b255 = fb.color_alpha_blend(fg, bg, 255 as uint32);
        if (b255 != fg) {
            return 2;
        }

        // 3. Alpha = 128 (~50% blend)
        uint32 b128 = fb.color_alpha_blend(fg, bg, 128 as uint32);
        uint32 r = (b128 >> 16) & (0xFF as uint32);
        uint32 b = b128 & (0xFF as uint32);

        // Half of 255 is ~128
        if (r < (125 as uint32) || r > (130 as uint32)) {
            return 3;
        }
        if (b < (125 as uint32) || b > (130 as uint32)) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_bitmap_font_rendering(self):
        code = """
        import "os/drivers/fb.kl" as fb;

        uint32[256] buffer;
        int i = 0;
        while (i < 256) {
            buffer[i] = 0 as uint32;
            i = i + 1;
        }

        fb.Framebuffer frame;
        fb.fb_init(&frame, &buffer[0], null, 16 as uint32, 16 as uint32, 64 as uint32);

        // Draw character 'K' at (0, 0)
        fb.fb_draw_char(&frame, 0, 0, 'K' as char, 0xFFFFFFFF as uint32, 0 as uint32, true);

        // Character 'K' row 0 has pattern 0x46 (bits: . X . . . X X .)
        // Column 1 should be set (0x40)
        uint32 p1 = fb.fb_get_pixel(&frame, 1, 0);
        if (p1 != (0xFFFFFFFF as uint32)) {
            return 1;
        }

        // Column 0 should be empty
        uint32 p0 = fb.fb_get_pixel(&frame, 0, 0);
        if (p0 != (0 as uint32)) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ps2_mouse_packet_decoding_positive_delta(self):
        code = """
        import "os/drivers/mouse.kl" as mouse;

        mouse.MouseState state;
        mouse.mouse_init(&state, 100, 100);

        // Byte 0: Always1 (0x08) | LeftBtn (0x01)
        uint8 b0 = 0x09 as uint8;
        // Delta X: +15
        uint8 b1 = 15 as uint8;
        // Delta Y: +10 (hardware up -> screen down is -10)
        uint8 b2 = 10 as uint8;

        bool ok = mouse.mouse_process_packet(&state, b0, b1, b2, 800, 600);
        if (!ok) {
            return 1;
        }

        if (!state.left_button || state.right_button || state.middle_button) {
            return 2;
        }
        if (state.delta_x != 15 || state.delta_y != -10) {
            return 3;
        }
        if (state.x != 115 || state.y != 90) {
            return 4;
        }
        if (state.total_packets != (1 as uint64)) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ps2_mouse_negative_delta_and_clamping(self):
        code = """
        import "os/drivers/mouse.kl" as mouse;

        mouse.MouseState state;
        mouse.mouse_init(&state, 5, 5);

        // Byte 0: Always1 (0x08) | RightBtn (0x02) | X_Sign (0x10) | Y_Sign (0x20)
        uint8 b0 = 0x3A as uint8;
        // Delta X: -20 (in 8-bit unsigned: 256 - 20 = 236)
        uint8 b1 = 236 as uint8;
        // Delta Y: -30 (in 8-bit unsigned: 256 - 30 = 226, hardware down -> screen up is +30)
        uint8 b2 = 226 as uint8;

        bool ok = mouse.mouse_process_packet(&state, b0, b1, b2, 800, 600);
        if (!ok) {
            return 1;
        }

        if (!state.right_button || state.left_button) {
            return 2;
        }
        if (state.delta_x != -20 || state.delta_y != 30) {
            return 3;
        }

        // Coordinate X: 5 - 20 = -15 -> clamped to 0!
        if (state.x != 0) {
            return 4;
        }
        // Coordinate Y: 5 + 30 = 35
        if (state.y != 35) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ps2_mouse_byte_streaming_pipeline(self):
        code = """
        import "os/drivers/mouse.kl" as mouse;

        mouse.MouseState state;
        mouse.mouse_init(&state, 50, 50);

        // Feed bytes one by one
        bool p1 = mouse.mouse_feed_byte(&state, 0x08 as uint8, 800, 600); // b0
        if (p1) { return 1; }
        bool p2 = mouse.mouse_feed_byte(&state, 10 as uint8, 800, 600);   // b1 (dx = +10)
        if (p2) { return 2; }
        bool p3 = mouse.mouse_feed_byte(&state, 5 as uint8, 800, 600);    // b2 (dy = +5 -> screen -5)
        if (!p3) { return 3; }

        if (state.x != 60 || state.y != 45) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_window_manager_lifecycle_and_z_order(self):
        code = """
        import "os/kernel/window.kl" as win;

        win.WindowManager wm;
        win.wm_init(&wm);

        win.Window* w1 = win.wm_create_window(&wm, "Terminal", 50, 50, 200, 150, 0x00000000 as uint32);
        if (w1 == null || wm.window_count != (1 as uint32)) {
            return 1;
        }

        win.Window* w2 = win.wm_create_window(&wm, "Editor", 100, 100, 300, 200, 0x00FFFFFF as uint32);
        if (w2 == null || wm.window_count != (2 as uint32)) {
            return 2;
        }

        // w2 should have higher z-order and be focused
        if (w2->z_order <= w1->z_order || !w2->is_focused || w1->is_focused) {
            return 3;
        }

        // Bring w1 to front
        win.wm_bring_to_front(&wm, w1->id);
        if (w1->z_order <= w2->z_order || !w1->is_focused || w2->is_focused) {
            return 4;
        }

        // Move w1
        win.wm_move_window(&wm, w1->id, 80, 80);
        if (w1->rect.x != 80 || w1->rect.y != 80) {
            return 5;
        }

        // Destroy w2
        bool destroyed = win.wm_destroy_window(&wm, w2->id);
        if (!destroyed || wm.window_count != (1 as uint32)) {
            return 6;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_window_manager_spatial_hit_testing(self):
        code = """
        import "os/kernel/window.kl" as win;

        win.WindowManager wm;
        win.wm_init(&wm);

        // Window 1: (0, 0) to (100, 100)
        win.Window* w1 = win.wm_create_window(&wm, "BackWin", 0, 0, 100, 100, 0 as uint32);

        // Window 2: (50, 50) to (150, 150)
        win.Window* w2 = win.wm_create_window(&wm, "FrontWin", 50, 50, 100, 100, 0 as uint32);

        // Point (25, 25) is exclusively inside w1
        win.Window* hit1 = win.wm_hit_test(&wm, 25, 25);
        if (hit1 != w1) {
            return 1;
        }

        // Point (125, 125) is exclusively inside w2
        win.Window* hit2 = win.wm_hit_test(&wm, 125, 125);
        if (hit2 != w2) {
            return 2;
        }

        // Overlap point (75, 75) is inside BOTH, but w2 is on top!
        win.Window* hit_overlap = win.wm_hit_test(&wm, 75, 75);
        if (hit_overlap != w2) {
            return 3;
        }

        // Point (200, 200) is outside all windows
        win.Window* hit_none = win.wm_hit_test(&wm, 200, 200);
        if (hit_none != null) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
