import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSPTYTermios(unittest.TestCase):
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

    def test_termios_defaults_and_init(self):
        code = r"""
        import "os/drivers/pty.kl" as pty;

        pty.PTY term;
        pty.pty_init(&term, 0);

        if (term.id != 0) return 1;
        if (!term.is_open) return 2;

        // Check input flags (ICRNL)
        if ((term.termios.c_iflag & pty.TERMIOS_ICRNL) == (0 as uint32)) return 3;

        // Check output flags (OPOST | ONLCR)
        if ((term.termios.c_oflag & pty.TERMIOS_ONLCR) == (0 as uint32)) return 4;

        // Check local flags (ISIG | ICANON | ECHO | ECHOE)
        if ((term.termios.c_lflag & pty.TERMIOS_ICANON) == (0 as uint32)) return 5;
        if ((term.termios.c_lflag & pty.TERMIOS_ECHO) == (0 as uint32)) return 6;
        if ((term.termios.c_lflag & pty.TERMIOS_ISIG) == (0 as uint32)) return 7;

        // Check control characters
        if (term.termios.c_cc[pty.CC_VINTR] != (0x03 as uint8)) return 8;
        if (term.termios.c_cc[pty.CC_VERASE] != (0x08 as uint8)) return 9;
        if (term.termios.c_cc[pty.CC_VKILL] != (0x15 as uint8)) return 10;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pty_canonical_line_editing(self):
        code = r"""
        import "os/drivers/pty.kl" as pty;

        pty.PTY term;
        pty.pty_init(&term, 1);

        // Type 'a' (97), 'b' (98), 'c' (99)
        pty.pty_input_char(&term, 97 as uint8);
        pty.pty_input_char(&term, 98 as uint8);
        pty.pty_input_char(&term, 99 as uint8);

        // In canonical mode, nothing sent to slave yet
        if (term.slave_count != 0) return 1;

        // Backspace (0x08)
        pty.pty_input_char(&term, 0x08 as uint8);
        if (term.line_len != 2) return 2; // Should now only have 2 characters

        // Type 'd' (100)
        pty.pty_input_char(&term, 100 as uint8);
        if (term.line_len != 3) return 3;

        // Submit line with NL (0x0A)
        pty.pty_input_char(&term, 0x0A as uint8);

        // Slave queue should now have 4 bytes: 97, 98, 100, 10
        if (term.slave_count != 4) return 4;

        uint8[8] read_buf;
        int n = pty.pty_slave_read(&term, &read_buf[0], 8);
        if (n != 4) return 5;
        if (read_buf[0] != (97 as uint8)) return 6;
        if (read_buf[1] != (98 as uint8)) return 7;
        if (read_buf[2] != (100 as uint8)) return 8;
        if (read_buf[3] != (0x0A as uint8)) return 9;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pty_line_kill(self):
        code = r"""
        import "os/drivers/pty.kl" as pty;

        pty.PTY term;
        pty.pty_init(&term, 1);

        // Type 4 characters
        pty.pty_input_char(&term, 116 as uint8); // 't'
        pty.pty_input_char(&term, 121 as uint8); // 'y'
        pty.pty_input_char(&term, 112 as uint8); // 'p'
        pty.pty_input_char(&term, 111 as uint8); // 'o'
        if (term.line_len != 4) return 1;

        // Kill line with VKILL (0x15)
        pty.pty_input_char(&term, 0x15 as uint8);
        if (term.line_len != 0) return 2;

        // Type "ok\n"
        pty.pty_input_char(&term, 111 as uint8); // 'o'
        pty.pty_input_char(&term, 107 as uint8); // 'k'
        pty.pty_input_char(&term, 0x0A as uint8); // NL

        uint8[8] read_buf;
        int n = pty.pty_slave_read(&term, &read_buf[0], 8);
        if (n != 3) return 3;
        if (read_buf[0] != (111 as uint8) || read_buf[1] != (107 as uint8)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pty_input_translation_icrnl(self):
        code = r"""
        import "os/drivers/pty.kl" as pty;

        pty.PTY term;
        pty.pty_init(&term, 1);

        // Type 'x' then carriage return CR (0x0D)
        pty.pty_input_char(&term, 120 as uint8); // 'x'
        pty.pty_input_char(&term, 0x0D as uint8); // CR should translate to NL and flush

        uint8[4] read_buf;
        int n = pty.pty_slave_read(&term, &read_buf[0], 4);
        if (n != 2) return 1;
        if (read_buf[0] != (120 as uint8)) return 2;
        if (read_buf[1] != (0x0A as uint8)) return 3; // Translated to NL

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pty_slave_write_onlcr_output(self):
        code = r"""
        import "os/drivers/pty.kl" as pty;

        pty.PTY term;
        pty.pty_init(&term, 1);

        // Slave writes "A\n" (2 bytes)
        uint8[4] write_buf;
        write_buf[0] = 65 as uint8; // 'A'
        write_buf[1] = 0x0A as uint8; // NL

        pty.pty_slave_write(&term, &write_buf[0], 2);

        // Master should receive "A\r\n" (3 bytes due to ONLCR)
        uint8[8] master_buf;
        int n = pty.pty_master_read(&term, &master_buf[0], 8);
        if (n != 3) return 1;
        if (master_buf[0] != (65 as uint8)) return 2;
        if (master_buf[1] != (0x0D as uint8)) return 3; // CR
        if (master_buf[2] != (0x0A as uint8)) return 4; // NL

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pty_signal_generation(self):
        code = r"""
        import "os/drivers/pty.kl" as pty;

        pty.PTY term;
        pty.pty_init(&term, 1);

        if (term.pending_signal != 0) return 1;

        // Send ^C (0x03) -> SIGINT (2)
        pty.pty_input_char(&term, 0x03 as uint8);
        if (term.pending_signal != 2) return 2;

        // Reset signal
        term.pending_signal = 0;

        // Send ^\ (0x1C) -> SIGQUIT (3)
        pty.pty_input_char(&term, 0x1C as uint8);
        if (term.pending_signal != 3) return 3;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pty_raw_mode(self):
        code = r"""
        import "os/drivers/pty.kl" as pty;

        pty.PTY term;
        pty.pty_init(&term, 1);

        // Clear ICANON flag for raw mode
        term.termios.c_lflag = term.termios.c_lflag & (~pty.TERMIOS_ICANON);

        // Input 'z' (122)
        pty.pty_input_char(&term, 122 as uint8);

        // In raw mode, immediately delivered to slave without newline
        if (term.slave_count != 1) return 1;

        uint8[4] read_buf;
        int n = pty.pty_slave_read(&term, &read_buf[0], 4);
        if (n != 1 || read_buf[0] != (122 as uint8)) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
