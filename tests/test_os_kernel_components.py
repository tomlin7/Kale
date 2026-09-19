import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSKernelComponents(unittest.TestCase):
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

    def test_os_gdt_entry_encoding(self):
        code = """
        import "os/kernel/gdt.kl" as gdt;

        gdt.GDTTable table;
        gdt.gdt_init(&table);

        // Kernel Code descriptor (0x08)
        // Access: 154 (0x9A), Granularity: 0x2F = 47 (limit high nibble 0x0F | gran 0x20)
        if (table.kernel_code.access != 154) {
            return 1;
        }
        if (table.kernel_code.granularity != 47) {
            return 2;
        }

        // Kernel Data descriptor (0x10)
        // Access: 146 (0x92)
        if (table.kernel_data.access != 146) {
            return 3;
        }

        // User Code descriptor (0x18)
        if (table.user_code.access != 250) {
            return 4;
        }

        // GDT pointer limit: 5 * 8 - 1 = 39
        if (table.pointer.limit != 39) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_os_pic_configuration(self):
        code = """
        import "os/kernel/pic.kl" as pic;

        pic.PICDriver drv = pic.pic_init(32, 40);
        if (drv.master_offset != 32) {
            return 1;
        }
        if (drv.slave_offset != 40) {
            return 2;
        }
        // Master mask unmasks IRQ0 & IRQ1 (252)
        if (drv.master_mask != 252) {
            return 3;
        }
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_os_kbd_scancode_translation(self):
        code = """
        import "os/drivers/kbd.kl" as kbd;

        // Scancode 30 = 'A' / 'a'
        int a_lower = kbd.kbd_scancode_to_ascii(30, false);
        int a_upper = kbd.kbd_scancode_to_ascii(30, true);

        if (a_lower != 97) { // 'a' == 97
            return 1;
        }
        if (a_upper != 65) { // 'A' == 65
            return 2;
        }

        // Scancode 57 = Space (32)
        int space = kbd.kbd_scancode_to_ascii(57, false);
        if (space != 32) {
            return 3;
        }

        // Keyboard state buffer
        kbd.KeyboardState state = kbd.kbd_init();
        bool handled = kbd.kbd_handle_scancode(&state, 30);
        if (!handled || state.count != 1) {
            return 4;
        }

        kbd.KeyEvent ev;
        bool read_ok = kbd.kbd_read_event(&state, &ev);
        if (!read_ok || ev.ascii != 97) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
