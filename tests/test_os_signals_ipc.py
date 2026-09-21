import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSSignalsIPC(unittest.TestCase):
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

    def test_signal_pending_and_delivery_ordering(self):
        code = """
        import "os/kernel/signal.kl" as sig;

        sig.SignalState st;
        sig.signal_state_init(&st);

        if (sig.signal_next_deliverable(&st) != 0) return 1;

        // Send SIGALRM (14) then SIGINT (2)
        sig.signal_send(&st, sig.SIGALRM);
        sig.signal_send(&st, sig.SIGINT);

        // SIGINT (2) should be delivered first (lower signal number)
        int s1 = sig.signal_next_deliverable(&st);
        if (s1 != sig.SIGINT) return 2;

        // Then SIGALRM (14)
        int s2 = sig.signal_next_deliverable(&st);
        if (s2 != sig.SIGALRM) return 3;

        // No more signals
        if (sig.signal_next_deliverable(&st) != 0) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_signal_blocking_and_unblocking(self):
        code = """
        import "os/kernel/signal.kl" as sig;

        sig.SignalState st;
        sig.signal_state_init(&st);

        // Block SIGINT (2)
        sig.signal_block(&st, sig.SIGINT);

        // Send SIGINT
        sig.signal_send(&st, sig.SIGINT);

        // Should NOT be deliverable while blocked
        if (sig.signal_next_deliverable(&st) != 0) return 1;

        // Unblock SIGINT
        sig.signal_unblock(&st, sig.SIGINT);

        // Now deliverable
        if (sig.signal_next_deliverable(&st) != sig.SIGINT) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_signal_uncatchable_sigkill_and_sigstop(self):
        code = """
        import "os/kernel/signal.kl" as sig;

        sig.SignalState st;
        sig.signal_state_init(&st);

        // Attempt to block SIGKILL (must be refused)
        bool b_kill = sig.signal_block(&st, sig.SIGKILL);
        if (b_kill) return 1;

        // Attempt to block SIGSTOP (must be refused)
        bool b_stop = sig.signal_block(&st, sig.SIGSTOP);
        if (b_stop) return 2;

        // Attempt to set custom handler on SIGKILL (must be refused)
        bool h_kill = sig.signal_set_handler(&st, sig.SIGKILL, 0x1234 as uint64);
        if (h_kill) return 3;

        // Send SIGINT and SIGKILL -> SIGKILL must take precedence
        sig.signal_send(&st, sig.SIGINT);
        sig.signal_send(&st, sig.SIGKILL);

        int next_sig = sig.signal_next_deliverable(&st);
        if (next_sig != sig.SIGKILL) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_signal_dispositions_and_actions(self):
        code = """
        import "os/kernel/signal.kl" as sig;

        sig.SignalState st;
        sig.signal_state_init(&st);

        // 1. Default action for SIGTERM is ACT_TERMINATE
        if (sig.signal_get_action(&st, sig.SIGTERM) != sig.ACT_TERMINATE) return 1;

        // 2. Default action for SIGCHLD is ACT_IGNORE
        if (sig.signal_get_action(&st, sig.SIGCHLD) != sig.ACT_IGNORE) return 2;

        // 3. Set SIG_IGN on SIGINT
        sig.signal_set_handler(&st, sig.SIGINT, sig.SIG_IGN);
        if (sig.signal_get_action(&st, sig.SIGINT) != sig.ACT_IGNORE) return 3;

        // 4. Custom handler
        sig.signal_set_handler(&st, sig.SIGINT, 0x00400000 as uint64);
        if (sig.signal_get_action(&st, sig.SIGINT) != sig.ACT_HANDLER) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pipe_read_write_ring_buffer(self):
        code = """
        import "os/kernel/pipe.kl" as pipe;

        pipe.PipeTable tbl;
        pipe.pipe_table_init(&tbl);

        int pid = pipe.pipe_create(&tbl);
        if (pid != 0 || tbl.active_pipes != 1) return 1;

        pipe.Pipe* p = &tbl.pipes[pid];

        // Write 4 bytes: "KALE"
        uint8[8] write_data;
        write_data[0] = 75 as uint8; // 'K'
        write_data[1] = 65 as uint8; // 'A'
        write_data[2] = 76 as uint8; // 'L'
        write_data[3] = 69 as uint8; // 'E'

        int written = pipe.pipe_write(p, &write_data[0], 4);
        if (written != 4 || p->count != 4) return 2;

        // Read 4 bytes back
        uint8[8] read_data;
        int read_count = pipe.pipe_read(p, &read_data[0], 8);
        if (read_count != 4 || p->count != 0) return 3;

        if (read_data[0] != (75 as uint8) || read_data[3] != (69 as uint8)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pipe_eof_and_broken_pipe_epipe(self):
        code = """
        import "os/kernel/pipe.kl" as pipe;

        pipe.PipeTable tbl;
        pipe.pipe_table_init(&tbl);

        int pid = pipe.pipe_create(&tbl);
        pipe.Pipe* p = &tbl.pipes[pid];

        // 1. Close write end -> reading empty pipe returns 0 (EOF)
        pipe.pipe_close_write(p);
        uint8[4] dst;
        int eof = pipe.pipe_read(p, &dst[0], 4);
        if (eof != 0) return 1;

        // 2. Broken Pipe: Close read end -> writing returns PIPE_ERR_BROKEN (-32)
        pipe.pipe_close_read(p);
        uint8[4] src;
        src[0] = 1 as uint8;
        int err = pipe.pipe_write(p, &src[0], 1);
        if (err != pipe.PIPE_ERR_BROKEN) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
