import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSDNSSockets(unittest.TestCase):
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

    def test_dns_qname_label_encoding(self):
        code = """
        import "os/kernel/dns.kl" as dns;

        // "kale.org" -> [4]'k''a''l''e' [3]'o''r''g' [0]
        uint8[16] domain;
        domain[0] = 0x6B as uint8; // 'k'
        domain[1] = 0x61 as uint8; // 'a'
        domain[2] = 0x6C as uint8; // 'l'
        domain[3] = 0x65 as uint8; // 'e'
        domain[4] = 0x2E as uint8; // '.'
        domain[5] = 0x6F as uint8; // 'o'
        domain[6] = 0x72 as uint8; // 'r'
        domain[7] = 0x67 as uint8; // 'g'
        domain[8] = 0x00 as uint8; // null

        uint8[32] qname_buf;
        int len = dns.dns_encode_qname(&domain[0], &qname_buf[0], 32);

        // Expected length: 1 + 4 + 1 + 3 + 1 = 10 bytes
        if (len != 10) {
            return 1;
        }

        // Label 1: len 4, "kale"
        if (qname_buf[0] != (4 as uint8)) return 2;
        if (qname_buf[1] != (0x6B as uint8)) return 3;

        // Label 2: len 3, "org"
        if (qname_buf[5] != (3 as uint8)) return 4;
        if (qname_buf[6] != (0x6F as uint8)) return 5;

        // Terminal 0
        if (qname_buf[9] != (0 as uint8)) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_dns_query_packet_serialization(self):
        code = """
        import "os/kernel/dns.kl" as dns;

        uint8[16] domain;
        domain[0] = 0x61 as uint8; // 'a'
        domain[1] = 0x00 as uint8; // null

        dns.DNSQuery query;
        // Server IP 8.8.8.8 = 0x08080808, Transaction ID = 0x1234
        int total_len = dns.dns_build_query_packet(&query, 0x1234 as uint16, &domain[0], 0x08080808 as uint32);

        // Header (12) + QNAME ("a" -> [1]'a'[0] = 3) + QTYPE(2) + QCLASS(2) = 19 bytes
        if (total_len != 19) {
            return 1;
        }

        // Check Transaction ID in header (0x1234)
        if (query.raw_packet[0] != (0x12 as uint8) || query.raw_packet[1] != (0x34 as uint8)) {
            return 2;
        }

        // Check RD bit (Recursion Desired = 0x0100)
        if (query.raw_packet[2] != (0x01 as uint8) || query.raw_packet[3] != (0x00 as uint8)) {
            return 3;
        }

        // Check QDCOUNT = 1
        if (query.raw_packet[4] != (0x00 as uint8) || query.raw_packet[5] != (0x01 as uint8)) {
            return 4;
        }

        // Check QTYPE (1) and QCLASS (1) at end of packet
        if (query.raw_packet[15] != (0x00 as uint8) || query.raw_packet[16] != (0x01 as uint8)) {
            return 5;
        }
        if (query.raw_packet[17] != (0x00 as uint8) || query.raw_packet[18] != (0x01 as uint8)) {
            return 6;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_dns_answer_parsing(self):
        code = """
        import "os/kernel/dns.kl" as dns;

        // Mock DNS Response Packet
        uint8[48] packet;
        int i = 0;
        while (i < 48) { packet[i] = 0 as uint8; i = i + 1; }

        // Header: ID = 0x1234
        packet[0] = 0x12 as uint8; packet[1] = 0x34 as uint8;
        // Flags: QR=1 (Response), RD=1, RA=1, RCODE=0 -> 0x8180
        packet[2] = 0x81 as uint8; packet[3] = 0x80 as uint8;
        // QDCOUNT = 1, ANCOUNT = 1
        packet[4] = 0x00 as uint8; packet[5] = 0x01 as uint8;
        packet[6] = 0x00 as uint8; packet[7] = 0x01 as uint8;

        // Question: [1]'x'[0] (3 bytes) + QTYPE (2) + QCLASS (2) = 7 bytes
        packet[12] = 1 as uint8; packet[13] = 0x78 as uint8; packet[14] = 0 as uint8;
        packet[15] = 0 as uint8; packet[16] = 1 as uint8; // QTYPE A
        packet[17] = 0 as uint8; packet[18] = 1 as uint8; // QCLASS IN

        // Answer Section: Name pointer 0xC00C (points to offset 12)
        packet[19] = 0xC0 as uint8; packet[20] = 0x0C as uint8;
        // TYPE A (0x0001), CLASS IN (0x0001)
        packet[21] = 0 as uint8; packet[22] = 1 as uint8;
        packet[23] = 0 as uint8; packet[24] = 1 as uint8;
        // TTL = 300 (0x0000012C)
        packet[25] = 0 as uint8; packet[26] = 0 as uint8;
        packet[27] = 1 as uint8; packet[28] = 0x2C as uint8;
        // RDLENGTH = 4
        packet[29] = 0 as uint8; packet[30] = 4 as uint8;
        // IP Address: 192.168.1.50
        packet[31] = 192 as uint8;
        packet[32] = 168 as uint8;
        packet[33] = 1 as uint8;
        packet[34] = 50 as uint8;

        uint32 resolved_ip = 0 as uint32;
        bool ok = dns.dns_parse_answer(&packet[0], 35, &resolved_ip);

        if (!ok) {
            return 1;
        }

        // Expected packed IP: 192 | (168 << 8) | (1 << 16) | (50 << 24)
        uint32 expected = (192 as uint32) | ((168 as uint32) << 8) | ((1 as uint32) << 16) | ((50 as uint32) << 24);
        if (resolved_ip != expected) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_socket_table_create_and_bind(self):
        code = """
        import "os/kernel/socket.kl" as sock;

        sock.SocketTable tbl;
        sock.socket_table_init(&tbl);

        if (tbl.count != 0) return 1;

        int fd0 = sock.socket_create(&tbl, sock.AF_INET, sock.SOCK_STREAM);
        int fd1 = sock.socket_create(&tbl, sock.AF_INET, sock.SOCK_DGRAM);

        if (fd0 != 0 || fd1 != 1 || tbl.count != 2) return 2;

        sock.Socket* s0 = sock.socket_get(&tbl, fd0);
        if (s0 == null || s0->sock_type != sock.SOCK_STREAM) return 3;

        // Bind socket 0 to 127.0.0.1:8080
        bool ok = sock.socket_bind(&tbl, fd0, 0x7F000001 as uint32, 8080 as uint16);
        if (!ok || s0->local_port != (8080 as uint16)) return 4;

        // Close socket 0
        sock.socket_close(&tbl, fd0);
        if (tbl.count != 1) return 5;
        if (sock.socket_get(&tbl, fd0) != null) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_tcp_client_handshake_state_machine(self):
        code = """
        import "os/kernel/socket.kl" as sock;

        sock.SocketTable tbl;
        sock.socket_table_init(&tbl);

        int fd = sock.socket_create(&tbl, sock.AF_INET, sock.SOCK_STREAM);
        sock.Socket* s = sock.socket_get(&tbl, fd);

        if (s->state != sock.TCP_CLOSED) return 1;

        // Initiate connection -> transitions to SYN_SENT
        sock.socket_connect(&tbl, fd, 0x08080808 as uint32, 80 as uint16);
        if (s->state != sock.TCP_SYN_SENT) return 2;

        // Receive SYN+ACK from remote server
        bool ok = sock.socket_tcp_process_event(s, true, true, false, 5000 as uint32, 1001 as uint32);
        if (!ok || s->state != sock.TCP_ESTABLISHED) return 3;
        if (s->ack_num != (5001 as uint32)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_tcp_teardown_state_machine(self):
        code = """
        import "os/kernel/socket.kl" as sock;

        sock.SocketTable tbl;
        sock.socket_table_init(&tbl);

        int fd = sock.socket_create(&tbl, sock.AF_INET, sock.SOCK_STREAM);
        sock.Socket* s = sock.socket_get(&tbl, fd);
        s->state = sock.TCP_ESTABLISHED;

        // Passive close: Remote sends FIN -> transitions to CLOSE_WAIT
        bool ok = sock.socket_tcp_process_event(s, false, false, true, 8000 as uint32, 2000 as uint32);
        if (!ok || s->state != sock.TCP_CLOSE_WAIT) return 1;

        // Local process closes socket -> transitions to LAST_ACK
        ok = sock.socket_tcp_process_event(s, false, false, false, 0 as uint32, 0 as uint32);
        if (!ok || s->state != sock.TCP_LAST_ACK) return 2;

        // Remote responds with final ACK -> transitions to CLOSED
        ok = sock.socket_tcp_process_event(s, false, true, false, 0 as uint32, 0 as uint32);
        if (!ok || s->state != sock.TCP_CLOSED) return 3;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
