import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSNetworking(unittest.TestCase):
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

    def test_ethernet_framing_and_ethertypes(self):
        code = """
        import "os/kernel/net.kl" as net;

        if (net.ETH_TYPE_IPV4 != (0x0800 as uint16) || net.ETH_TYPE_ARP != (0x0806 as uint16)) {
            return 1;
        }

        uint8[14] raw_eth;
        // Dest MAC: 52:54:00:12:34:56
        raw_eth[0] = 0x52 as uint8; raw_eth[1] = 0x54 as uint8; raw_eth[2] = 0x00 as uint8;
        raw_eth[3] = 0x12 as uint8; raw_eth[4] = 0x34 as uint8; raw_eth[5] = 0x56 as uint8;
        // Src MAC: 00:11:22:33:44:55
        raw_eth[6] = 0x00 as uint8; raw_eth[7] = 0x11 as uint8; raw_eth[8] = 0x22 as uint8;
        raw_eth[9] = 0x33 as uint8; raw_eth[10] = 0x44 as uint8; raw_eth[11] = 0x55 as uint8;
        // EtherType: 0x0800
        raw_eth[12] = 0x08 as uint8; raw_eth[13] = 0x00 as uint8;

        uint16 et = ((raw_eth[12] as uint16) << 8) | (raw_eth[13] as uint16);
        if (et != net.ETH_TYPE_IPV4) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_arp_table_insert_and_lookup(self):
        code = """
        import "os/kernel/net.kl" as net;

        net.ARPTable arp;
        net.arp_init(&arp);

        if (arp.entry_count != (0 as uint32)) {
            return 1;
        }

        uint8[4] ip1;
        ip1[0] = 192 as uint8; ip1[1] = 168 as uint8; ip1[2] = 1 as uint8; ip1[3] = 50 as uint8;

        uint8[6] mac1;
        mac1[0] = 0xAA as uint8; mac1[1] = 0xBB as uint8; mac1[2] = 0xCC as uint8;
        mac1[3] = 0xDD as uint8; mac1[4] = 0xEE as uint8; mac1[5] = 0xFF as uint8;

        net.arp_insert(&arp, &ip1[0], &mac1[0]);
        if (arp.entry_count != (1 as uint32)) {
            return 2;
        }

        uint8[6] found_mac;
        bool found = net.arp_lookup(&arp, &ip1[0], &found_mac[0]);
        if (!found) {
            return 3;
        }
        if (found_mac[0] != (0xAA as uint8) || found_mac[5] != (0xFF as uint8)) {
            return 4;
        }

        // Unknown IP lookup
        uint8[4] unk_ip;
        unk_ip[0] = 10 as uint8; unk_ip[1] = 0 as uint8; unk_ip[2] = 0 as uint8; unk_ip[3] = 1 as uint8;
        bool not_found = net.arp_lookup(&arp, &unk_ip[0], &found_mac[0]);
        if (not_found) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_arp_packet_handling_and_reply_generation(self):
        code = """
        import "os/kernel/net.kl" as net;

        net.ARPTable arp;
        net.arp_init(&arp);

        uint8[4] my_ip;
        my_ip[0] = 10 as uint8; my_ip[1] = 0 as uint8; my_ip[2] = 2 as uint8; my_ip[3] = 15 as uint8;

        uint8[6] my_mac;
        my_mac[0] = 0x52 as uint8; my_mac[1] = 0x54 as uint8; my_mac[2] = 0x00 as uint8;
        my_mac[3] = 0x12 as uint8; my_mac[4] = 0x34 as uint8; my_mac[5] = 0x56 as uint8;

        // Build ARP Request targeting my_ip
        uint8[28] in_arp;
        in_arp[0] = 0 as uint8; in_arp[1] = 1 as uint8;     // HW: Ethernet
        in_arp[2] = 0x08 as uint8; in_arp[3] = 0x00 as uint8; // Proto: IPv4
        in_arp[4] = 6 as uint8; in_arp[5] = 4 as uint8;
        in_arp[6] = 0 as uint8; in_arp[7] = 1 as uint8;     // Opcode: 1 (Request)

        // Sender MAC: AA:BB:CC:DD:EE:FF, Sender IP: 10.0.2.2
        in_arp[8] = 0xAA as uint8; in_arp[9] = 0xBB as uint8; in_arp[10] = 0xCC as uint8;
        in_arp[11] = 0xDD as uint8; in_arp[12] = 0xEE as uint8; in_arp[13] = 0xFF as uint8;
        in_arp[14] = 10 as uint8; in_arp[15] = 0 as uint8; in_arp[16] = 2 as uint8; in_arp[17] = 2 as uint8;

        // Target IP: 10.0.2.15 (matching my_ip)
        in_arp[24] = 10 as uint8; in_arp[25] = 0 as uint8; in_arp[26] = 2 as uint8; in_arp[27] = 15 as uint8;

        uint8[28] out_reply;
        uint32 out_len = 0 as uint32;

        bool ok = net.arp_handle_packet(&arp, &my_ip[0], &my_mac[0], &in_arp[0], &out_reply[0], &out_len);
        if (!ok || out_len != (28 as uint32)) {
            return 1;
        }

        // Opcode should be 2 (Reply)
        if (out_reply[6] != (0 as uint8) || out_reply[7] != (2 as uint8)) {
            return 2;
        }

        // Sender in reply must be my MAC and IP
        if (out_reply[8] != (0x52 as uint8) || out_reply[13] != (0x56 as uint8)) {
            return 3;
        }
        if (out_reply[14] != (10 as uint8) || out_reply[17] != (15 as uint8)) {
            return 4;
        }

        // Requester must now be cached in ARP table
        uint8[4] requester_ip;
        requester_ip[0] = 10 as uint8; requester_ip[1] = 0 as uint8; requester_ip[2] = 2 as uint8; requester_ip[3] = 2 as uint8;
        uint8[6] cached_mac;
        bool found = net.arp_lookup(&arp, &requester_ip[0], &cached_mac[0]);
        if (!found || cached_mac[0] != (0xAA as uint8) || cached_mac[5] != (0xFF as uint8)) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ipv4_checksum_calculation(self):
        code = """
        import "os/kernel/net.kl" as net;

        // Standard RFC 791 IPv4 20-byte test header:
        // 45 00 00 73 00 00 40 00 40 11 [00 00] c0 a8 00 01 c0 a8 00 c7
        uint8[20] ip_hdr;
        ip_hdr[0] = 0x45 as uint8; ip_hdr[1] = 0x00 as uint8;
        ip_hdr[2] = 0x00 as uint8; ip_hdr[3] = 0x73 as uint8;
        ip_hdr[4] = 0x00 as uint8; ip_hdr[5] = 0x00 as uint8;
        ip_hdr[6] = 0x40 as uint8; ip_hdr[7] = 0x00 as uint8;
        ip_hdr[8] = 0x40 as uint8; ip_hdr[9] = 0x11 as uint8;
        ip_hdr[10] = 0x00 as uint8; ip_hdr[11] = 0x00 as uint8; // Checksum zeroed
        ip_hdr[12] = 0xC0 as uint8; ip_hdr[13] = 0xA8 as uint8; ip_hdr[14] = 0x00 as uint8; ip_hdr[15] = 0x01 as uint8; // 192.168.0.1
        ip_hdr[16] = 0xC0 as uint8; ip_hdr[17] = 0xA8 as uint8; ip_hdr[18] = 0x00 as uint8; ip_hdr[19] = 0xC7 as uint8; // 192.168.0.199

        uint16 cksum = net.net_checksum(&ip_hdr[0], 20);

        // Insert calculated checksum into header
        ip_hdr[10] = ((cksum >> 8) & (0xFF as uint16)) as uint8;
        ip_hdr[11] = (cksum & (0xFF as uint16)) as uint8;

        // Recomputing checksum over header with checksum inserted must equal 0!
        uint16 verify = net.net_checksum(&ip_hdr[0], 20);
        if (verify != (0 as uint16)) {
            return 1;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_icmp_echo_reply_generation(self):
        code = """
        import "os/kernel/net.kl" as net;

        // Build ICMP Echo Request: 8 bytes (Type 8, Code 0, ID 0x1234, Seq 1) + 4 bytes payload
        uint8[12] req;
        req[0] = net.ICMP_ECHO_REQUEST; // 8
        req[1] = 0 as uint8;
        req[2] = 0 as uint8; req[3] = 0 as uint8; // Checksum
        req[4] = 0x12 as uint8; req[5] = 0x34 as uint8; // ID
        req[6] = 0x00 as uint8; req[7] = 0x01 as uint8; // Seq 1
        req[8] = 'P' as uint8; req[9] = 'I' as uint8; req[10] = 'N' as uint8; req[11] = 'G' as uint8;

        uint16 req_cksum = net.net_checksum(&req[0], 12);
        req[2] = ((req_cksum >> 8) & (0xFF as uint16)) as uint8;
        req[3] = (req_cksum & (0xFF as uint16)) as uint8;

        uint8[12] reply;
        uint32 rep_len = 0 as uint32;

        bool ok = net.icmp_handle_echo_request(&req[0], 12 as uint32, &reply[0], &rep_len);
        if (!ok || rep_len != (12 as uint32)) {
            return 1;
        }

        // Reply Type must be Echo Reply (0) and Code 0
        if (reply[0] != net.ICMP_ECHO_REPLY || reply[1] != (0 as uint8)) {
            return 2;
        }

        // ID, Sequence, and payload preserved
        if (reply[4] != (0x12 as uint8) || reply[5] != (0x34 as uint8)) {
            return 3;
        }
        if (reply[6] != (0x00 as uint8) || reply[7] != (0x01 as uint8)) {
            return 4;
        }
        if (reply[8] != ('P' as uint8) || reply[11] != ('G' as uint8)) {
            return 5;
        }

        // Reply checksum must be valid (recomputing over entire reply yields 0)
        uint16 verify = net.net_checksum(&reply[0], 12);
        if (verify != (0 as uint16)) {
            return 6;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_loopback_device_init_and_queuing(self):
        code = """
        import "os/drivers/net_loopback.kl" as loop;

        loop.NetDevice dev;
        loop.loopback_init(&dev);

        if (dev.ip[0] != (127 as uint8) || dev.ip[3] != (1 as uint8)) {
            return 1;
        }
        if (!dev.is_up || dev.mtu != (1500 as uint32)) {
            return 2;
        }

        // Transmit packet through loopback
        uint8[4] pkt;
        pkt[0] = 1 as uint8; pkt[1] = 2 as uint8; pkt[2] = 3 as uint8; pkt[3] = 4 as uint8;

        bool tx_ok = loop.loopback_transmit(&dev, &pkt[0], 4 as uint32);
        if (!tx_ok || dev.tx_packets != (1 as uint64) || dev.rx_packets != (1 as uint64)) {
            return 3;
        }

        // Receive packet back
        uint8[1514] rx_pkt;
        uint32 rx_len = 0 as uint32;
        bool rx_ok = loop.loopback_receive(&dev, &rx_pkt[0], &rx_len);
        if (!rx_ok || rx_len != (4 as uint32)) {
            return 4;
        }

        if (rx_pkt[0] != (1 as uint8) || rx_pkt[3] != (4 as uint8)) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_udp_socket_lifecycle_and_loopback_transmission(self):
        code = """
        import "os/drivers/net_loopback.kl" as loop;
        import "os/kernel/net.kl" as net;

        loop.NetDevice dev;
        loop.loopback_init(&dev);

        net.SocketTable sock_tbl;
        net.socket_table_init(&sock_tbl);

        // 1. Create UDP socket
        int32 sock_id = net.socket_create(&sock_tbl, net.AF_INET, net.SOCK_DGRAM, 17 as uint32);
        if (sock_id <= 0) {
            return 1;
        }

        // 2. Bind to port 5000
        uint8[4] bind_ip;
        bind_ip[0] = 127 as uint8; bind_ip[1] = 0 as uint8; bind_ip[2] = 0 as uint8; bind_ip[3] = 1 as uint8;
        bool b_ok = net.socket_bind(&sock_tbl, sock_id, &bind_ip[0], 5000 as uint16);
        if (!b_ok) {
            return 2;
        }

        // 3. Attempt duplicate bind on port 5000 (must be rejected)
        int32 sock_dup = net.socket_create(&sock_tbl, net.AF_INET, net.SOCK_DGRAM, 17 as uint32);
        bool dup_ok = net.socket_bind(&sock_tbl, sock_dup, &bind_ip[0], 5000 as uint16);
        if (dup_ok) {
            return 3; // Should reject duplicate port
        }

        // 4. Send UDP packet to 127.0.0.1:5000
        uint8[5] msg;
        msg[0] = 'H' as uint8; msg[1] = 'E' as uint8; msg[2] = 'L' as uint8; msg[3] = 'L' as uint8; msg[4] = 'O' as uint8;

        int32 sent = net.socket_sendto(&sock_tbl, sock_id, &bind_ip[0], 5000 as uint16, &msg[0], 5 as uint32, &dev);
        if (sent != 5) {
            return 4;
        }

        // 5. Dequeue from loopback RX ring
        uint8[1514] loop_rx;
        uint32 loop_len = 0 as uint32;
        bool rx_ok = loop.loopback_receive(&dev, &loop_rx[0], &loop_len);
        if (!rx_ok || loop_len != (47 as uint32)) { // 14 (Eth) + 20 (IP) + 8 (UDP) + 5 = 47
            return 5;
        }

        // 6. Deliver to socket table
        bool deliv_ok = net.socket_deliver_udp(&sock_tbl, &loop_rx[0], loop_len);
        if (!deliv_ok) {
            return 6;
        }

        // 7. Receive from socket
        uint8[4] src_ip;
        uint16 src_port = 0 as uint16;
        uint8[16] payload_recv;
        int32 recv_len = net.socket_recvfrom(&sock_tbl, sock_id, &src_ip[0], &src_port, &payload_recv[0], 16 as uint32);
        if (recv_len != 5) {
            return 7;
        }

        if (payload_recv[0] != ('H' as uint8) || payload_recv[4] != ('O' as uint8)) {
            return 8;
        }
        if (src_port != (5000 as uint16)) {
            return 9;
        }

        // 8. Close socket
        net.socket_close(&sock_tbl, sock_id);
        net.socket_close(&sock_tbl, sock_dup);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_network_syscall_interface(self):
        code = """
        import "os/kernel/syscall.kl" as sys;

        sys.SyscallStatsTable stats;
        sys.syscall_stats_init(&stats);

        sys.ProcessHeap heap;
        sys.process_heap_init(&heap, 0x1000000 as uint64, 0x10000000 as uint64);

        int32 exit_code = 0;
        bool terminated = false;
        bool yielded = false;

        // 1. Test SYS_SOCKET (41)
        sys.SyscallContext ctx;
        ctx.number = 41 as uint64; // SYS_SOCKET
        ctx.arg1 = 2 as uint64;   // AF_INET
        ctx.arg2 = 2 as uint64;   // SOCK_DGRAM
        ctx.arg3 = 17 as uint64;  // IPPROTO_UDP

        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 1000 as uint64, 1024 as uint64, 512 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != (4 as uint64) || ctx.error != 0) {
            return 1;
        }

        // 2. Test SYS_BIND (49)
        ctx.number = 49 as uint64; // SYS_BIND
        ctx.arg1 = 4 as uint64;    // fd = 4
        ctx.arg2 = 0x2000000 as uint64; // valid pointer
        ctx.arg3 = 16 as uint64;   // sockaddr len

        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 1000 as uint64, 1024 as uint64, 512 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != (0 as uint64) || ctx.error != 0) {
            return 2;
        }

        // 3. Test SYS_SENDTO (44)
        ctx.number = 44 as uint64; // SYS_SENDTO
        ctx.arg1 = 4 as uint64;    // fd = 4
        ctx.arg2 = 0x2000000 as uint64; // buf
        ctx.arg3 = 128 as uint64;  // len = 128 bytes

        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 1000 as uint64, 1024 as uint64, 512 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != (128 as uint64) || ctx.error != 0) {
            return 3;
        }

        // 4. Test SYS_RECVFROM (45)
        ctx.number = 45 as uint64; // SYS_RECVFROM
        ctx.arg1 = 4 as uint64;    // fd = 4
        ctx.arg2 = 0x2000000 as uint64; // buf
        ctx.arg3 = 64 as uint64;   // len = 64 bytes

        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 1000 as uint64, 1024 as uint64, 512 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != (64 as uint64) || ctx.error != 0) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_hardware_drivers_stubs_rtl8139_and_e1000(self):
        code = """
        import "os/drivers/rtl8139.kl" as rtl;
        import "os/drivers/e1000.kl" as e1000;

        rtl.RTL8139Device r_dev;
        rtl.rtl8139_init(&r_dev, 0xC000 as uint16, 11 as uint8);
        if (r_dev.io_base != (0xC000 as uint16) || r_dev.irq != (11 as uint8)) {
            return 1;
        }

        rtl.rtl8139_enable(&r_dev, 0x100000 as uint32);
        if (!r_dev.is_active || r_dev.rx_buffer_phys != (0x100000 as uint32)) {
            return 2;
        }

        e1000.E1000Device e_dev;
        e1000.e1000_init(&e_dev, 0xFEB00000 as uint64, 10 as uint8);
        if (e_dev.mmio_base != (0xFEB00000 as uint64) || !e_dev.link_up) {
            return 3;
        }

        bool link = e1000.e1000_detect_link(&e_dev);
        if (!link) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
