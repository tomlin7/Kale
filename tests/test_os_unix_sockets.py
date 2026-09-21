import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSUnixSockets(unittest.TestCase):
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

    def test_unix_socket_lifecycle(self):
        code = r"""
        import "os/kernel/unix_sock.kl" as unix;

        unix.UnixSocketTable tbl;
        unix.unix_sock_table_init(&tbl);

        int s0 = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);
        if (s0 != 0) return 1;
        if (tbl.sockets[s0].state != unix.UNIX_SOCK_STATE_UNBOUND) return 2;

        // Bind to path "/tmp/kale.sock\0"
        uint8[32] p;
        p[0] = 47 as uint8; // '/'
        p[1] = 116 as uint8;// 't'
        p[2] = 109 as uint8;// 'm'
        p[3] = 112 as uint8;// 'p'
        p[4] = 47 as uint8; // '/'
        p[5] = 97 as uint8; // 'a'
        p[6] = 0 as uint8;

        int rc = unix.unix_sock_bind(&tbl, s0, &p[0]);
        if (rc != unix.UNIX_ERR_OK) return 3;
        if (tbl.sockets[s0].state != unix.UNIX_SOCK_STATE_BOUND) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_unix_socket_bind_collision(self):
        code = r"""
        import "os/kernel/unix_sock.kl" as unix;

        unix.UnixSocketTable tbl;
        unix.unix_sock_table_init(&tbl);

        int s0 = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);
        int s1 = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);

        uint8[16] path;
        path[0] = 47 as uint8; // '/'
        path[1] = 120 as uint8;// 'x'
        path[2] = 0 as uint8;

        int rc0 = unix.unix_sock_bind(&tbl, s0, &path[0]);
        if (rc0 != unix.UNIX_ERR_OK) return 1;

        // Binding second socket to same path should fail with ADDRINUSE
        int rc1 = unix.unix_sock_bind(&tbl, s1, &path[0]);
        if (rc1 != unix.UNIX_ERR_ADDRINUSE) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_unix_socket_listen_and_connect(self):
        code = r"""
        import "os/kernel/unix_sock.kl" as unix;

        unix.UnixSocketTable tbl;
        unix.unix_sock_table_init(&tbl);

        int srv = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);
        uint8[16] srv_path;
        srv_path[0] = 47 as uint8; // '/'
        srv_path[1] = 115 as uint8;// 's'
        srv_path[2] = 0 as uint8;

        unix.unix_sock_bind(&tbl, srv, &srv_path[0]);
        int l_rc = unix.unix_sock_listen(&tbl, srv, 4);
        if (l_rc != unix.UNIX_ERR_OK) return 1;
        if (tbl.sockets[srv].state != unix.UNIX_SOCK_STATE_LISTENING) return 2;

        // Client connects
        int cli = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);
        int c_rc = unix.unix_sock_connect(&tbl, cli, &srv_path[0]);
        if (c_rc != unix.UNIX_ERR_OK) return 3;

        // Server backlog should now contain cli
        if (tbl.sockets[srv].backlog_count != 1) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_unix_socket_accept_and_link(self):
        code = r"""
        import "os/kernel/unix_sock.kl" as unix;

        unix.UnixSocketTable tbl;
        unix.unix_sock_table_init(&tbl);

        int srv = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);
        uint8[8] p;
        p[0] = 47 as uint8;
        p[1] = 97 as uint8;
        p[2] = 0 as uint8;

        unix.unix_sock_bind(&tbl, srv, &p[0]);
        unix.unix_sock_listen(&tbl, srv, 4);

        int cli = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);
        unix.unix_sock_connect(&tbl, cli, &p[0]);

        // Accept connection
        int acc = unix.unix_sock_accept(&tbl, srv);
        if (acc < 0) return 1;

        // Both client and accepted socket should now be connected to each other
        if (tbl.sockets[cli].state != unix.UNIX_SOCK_STATE_CONNECTED) return 2;
        if (tbl.sockets[acc].state != unix.UNIX_SOCK_STATE_CONNECTED) return 3;
        if (tbl.sockets[cli].peer_id != acc) return 4;
        if (tbl.sockets[acc].peer_id != cli) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_unix_socket_data_transfer(self):
        code = r"""
        import "os/kernel/unix_sock.kl" as unix;

        unix.UnixSocketTable tbl;
        unix.unix_sock_table_init(&tbl);

        int srv = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);
        uint8[8] p;
        p[0] = 47 as uint8;
        p[1] = 98 as uint8;
        p[2] = 0 as uint8;
        unix.unix_sock_bind(&tbl, srv, &p[0]);
        unix.unix_sock_listen(&tbl, srv, 4);

        int cli = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);
        unix.unix_sock_connect(&tbl, cli, &p[0]);
        int acc = unix.unix_sock_accept(&tbl, srv);

        // 1. Client sends "HELO"
        uint8[8] send_buf;
        send_buf[0] = 72 as uint8; // 'H'
        send_buf[1] = 69 as uint8; // 'E'
        send_buf[2] = 76 as uint8; // 'L'
        send_buf[3] = 79 as uint8; // 'O'

        int written = unix.unix_sock_send(&tbl, cli, &send_buf[0], 4);
        if (written != 4) return 1;

        // 2. Server receives "HELO"
        uint8[8] recv_buf;
        int n_read = unix.unix_sock_recv(&tbl, acc, &recv_buf[0], 8);
        if (n_read != 4) return 2;
        if (recv_buf[0] != (72 as uint8) || recv_buf[3] != (79 as uint8)) return 3;

        // 3. Server replies "OK"
        uint8[4] reply_buf;
        reply_buf[0] = 79 as uint8; // 'O'
        reply_buf[1] = 75 as uint8; // 'K'
        unix.unix_sock_send(&tbl, acc, &reply_buf[0], 2);

        // 4. Client receives "OK"
        uint8[4] cli_recv;
        int cli_n = unix.unix_sock_recv(&tbl, cli, &cli_recv[0], 4);
        if (cli_n != 2) return 4;
        if (cli_recv[0] != (79 as uint8) || cli_recv[1] != (75 as uint8)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_unix_socket_peer_close_and_eof(self):
        code = r"""
        import "os/kernel/unix_sock.kl" as unix;

        unix.UnixSocketTable tbl;
        unix.unix_sock_table_init(&tbl);

        int srv = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);
        uint8[8] p;
        p[0] = 47 as uint8;
        p[1] = 99 as uint8;
        p[2] = 0 as uint8;
        unix.unix_sock_bind(&tbl, srv, &p[0]);
        unix.unix_sock_listen(&tbl, srv, 4);

        int cli = unix.unix_sock_create(&tbl, unix.SOCK_STREAM);
        unix.unix_sock_connect(&tbl, cli, &p[0]);
        int acc = unix.unix_sock_accept(&tbl, srv);

        // Close client socket
        unix.unix_sock_close(&tbl, cli);

        // Server attempts to read empty buffer from closed peer -> returns 0 (EOF)
        uint8[4] buf;
        int n = unix.unix_sock_recv(&tbl, acc, &buf[0], 4);
        if (n != 0) return 1;

        // Writing to closed peer returns UNIX_ERR_PIPE (-32)
        uint8[4] wbuf;
        wbuf[0] = 1 as uint8;
        int err = unix.unix_sock_send(&tbl, acc, &wbuf[0], 1);
        if (err != unix.UNIX_ERR_PIPE) return 2;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
