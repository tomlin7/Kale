import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSFilesystem(unittest.TestCase):
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

    def test_vfs_node_initialization_and_types(self):
        code = """
        import "os/kernel/vfs.kl" as vfs;

        vfs.VFSNode file_node;
        vfs.vfs_node_init(&file_node, "test.txt", vfs.VFS_FILE, 101 as uint64);

        if (file_node.node_type != vfs.VFS_FILE || file_node.inode_number != (101 as uint64)) {
            return 1;
        }
        if (file_node.size != (0 as uint64) || file_node.child_count != (0 as uint32)) {
            return 2;
        }
        if (file_node.permissions != (420 as uint32)) { // 0644 default
            return 3;
        }

        vfs.VFSNode dir_node;
        vfs.vfs_node_init(&dir_node, "bin", vfs.VFS_DIRECTORY, 102 as uint64);
        if (dir_node.node_type != vfs.VFS_DIRECTORY) {
            return 4;
        }
        if (dir_node.permissions != (493 as uint32)) { // 0755 default
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vfs_hierarchical_directory_tree_and_child_addition(self):
        code = """
        import "os/kernel/vfs.kl" as vfs;

        vfs.VFSNode root;
        vfs.vfs_node_init(&root, "/", vfs.VFS_DIRECTORY, 1 as uint64);

        vfs.VFSNode bin_dir;
        vfs.vfs_create_dir(&root, &bin_dir, "bin", 2 as uint64);

        vfs.VFSNode dev_dir;
        vfs.vfs_create_dir(&root, &dev_dir, "dev", 3 as uint64);

        if (root.child_count != (2 as uint32)) {
            return 1;
        }
        if (bin_dir.parent != &root || dev_dir.parent != &root) {
            return 2;
        }

        vfs.VFSNode* found_bin = vfs.vfs_finddir(&root, "bin");
        if (found_bin != &bin_dir) {
            return 3;
        }

        vfs.VFSNode* found_dev = vfs.vfs_finddir(&root, "dev");
        if (found_dev != &dev_dir) {
            return 4;
        }

        vfs.VFSNode* not_found = vfs.vfs_finddir(&root, "var");
        if (not_found != null) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vfs_path_resolution(self):
        code = """
        import "os/kernel/vfs.kl" as vfs;

        vfs.VFSNode root;
        vfs.vfs_node_init(&root, "/", vfs.VFS_DIRECTORY, 1 as uint64);

        vfs.VFSNode etc_dir;
        vfs.vfs_create_dir(&root, &etc_dir, "etc", 10 as uint64);

        vfs.VFSNode os_release;
        uint8[64] file_buf;
        vfs.vfs_create_file(&etc_dir, &os_release, "os-release", &file_buf[0], 0 as uint64, 64 as uint64, 11 as uint64);

        // 1. Resolve root "/"
        vfs.VFSNode* r = vfs.vfs_resolve_path(&root, "/");
        if (r != &root) {
            return 1;
        }

        // 2. Resolve directory "/etc"
        vfs.VFSNode* e = vfs.vfs_resolve_path(&root, "/etc");
        if (e != &etc_dir) {
            return 2;
        }

        // 3. Resolve file "/etc/os-release"
        vfs.VFSNode* f = vfs.vfs_resolve_path(&root, "/etc/os-release");
        if (f != &os_release) {
            return 3;
        }

        // 4. Resolve non-existent path
        vfs.VFSNode* missing = vfs.vfs_resolve_path(&root, "/etc/passwd");
        if (missing != null) {
            return 4;
        }

        // 5. Reject relative path
        vfs.VFSNode* rel = vfs.vfs_resolve_path(&root, "etc/os-release");
        if (rel != null) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vfs_file_io_read_write_and_truncation(self):
        code = """
        import "os/kernel/vfs.kl" as vfs;

        uint8[256] storage;
        vfs.VFSNode file;
        vfs.vfs_node_init(&file, "data.bin", vfs.VFS_FILE, 42 as uint64);
        file.data = &storage[0];
        file.data_capacity = 256 as uint64;

        // Write 4 bytes: [10, 20, 30, 40]
        uint8[4] payload;
        payload[0] = 10 as uint8;
        payload[1] = 20 as uint8;
        payload[2] = 30 as uint8;
        payload[3] = 40 as uint8;

        uint64 written = vfs.vfs_write(&file, 0 as uint64, 4 as uint64, &payload[0]);
        if (written != (4 as uint64) || file.size != (4 as uint64)) {
            return 1;
        }

        // Read back 4 bytes
        uint8[8] read_buf;
        uint64 n_read = vfs.vfs_read(&file, 0 as uint64, 4 as uint64, &read_buf[0]);
        if (n_read != (4 as uint64)) {
            return 2;
        }
        if (read_buf[0] != (10 as uint8) || read_buf[1] != (20 as uint8) ||
            read_buf[2] != (30 as uint8) || read_buf[3] != (40 as uint8)) {
            return 3;
        }

        // Read beyond EOF returns 0
        uint64 beyond = vfs.vfs_read(&file, 10 as uint64, 4 as uint64, &read_buf[0]);
        if (beyond != (0 as uint64)) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vfs_device_nodes_null_and_zero(self):
        code = """
        import "os/kernel/vfs.kl" as vfs;

        vfs.VFSNode dev_null;
        vfs.vfs_node_init(&dev_null, "null", vfs.VFS_CHARDEVICE, 50 as uint64);

        vfs.VFSNode dev_zero;
        vfs.vfs_node_init(&dev_zero, "zero", vfs.VFS_CHARDEVICE, 51 as uint64);

        // 1. /dev/null read -> immediate EOF (0 bytes)
        uint8[16] buf;
        uint64 r_null = vfs.vfs_read(&dev_null, 0 as uint64, 16 as uint64, &buf[0]);
        if (r_null != (0 as uint64)) {
            return 1;
        }

        // 2. /dev/null write -> absorbs bytes without error
        uint64 w_null = vfs.vfs_write(&dev_null, 0 as uint64, 32 as uint64, &buf[0]);
        if (w_null != (32 as uint64)) {
            return 2;
        }

        // 3. /dev/zero read -> returns all zeros
        buf[0] = 99 as uint8;
        buf[7] = 88 as uint8;
        uint64 r_zero = vfs.vfs_read(&dev_zero, 0 as uint64, 8 as uint64, &buf[0]);
        if (r_zero != (8 as uint64)) {
            return 3;
        }
        if (buf[0] != (0 as uint8) || buf[7] != (0 as uint8)) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vfs_file_descriptor_table_lifecycle(self):
        code = """
        import "os/kernel/vfs.kl" as vfs;

        uint8[128] storage;
        vfs.VFSNode file;
        vfs.vfs_node_init(&file, "test.log", vfs.VFS_FILE, 70 as uint64);
        file.data = &storage[0];
        file.data_capacity = 128 as uint64;

        vfs.FileTable ft;
        vfs.vfs_file_table_init(&ft);

        // 1. Open for writing (FD 0)
        int32 fd0 = vfs.vfs_open(&ft, &file, vfs.O_WRONLY);
        if (fd0 != 0) {
            return 1;
        }

        // 2. Open for reading (FD 1)
        int32 fd1 = vfs.vfs_open(&ft, &file, vfs.O_RDONLY);
        if (fd1 != 1) {
            return 2;
        }

        // 3. Write via FD 0
        uint8[3] data;
        data[0] = 65 as uint8; // 'A'
        data[1] = 66 as uint8; // 'B'
        data[2] = 67 as uint8; // 'C'
        int64 nw = vfs.vfs_fd_write(&ft, fd0, &data[0], 3 as uint64);
        if (nw != (3 as int64) || file.size != (3 as uint64)) {
            return 3;
        }

        // 4. Attempt write on FD 1 (O_RDONLY) should fail
        int64 bad_w = vfs.vfs_fd_write(&ft, fd1, &data[0], 1 as uint64);
        if (bad_w != (-1 as int64)) {
            return 4;
        }

        // 5. Read via FD 1
        uint8[3] out_buf;
        int64 nr = vfs.vfs_fd_read(&ft, fd1, &out_buf[0], 3 as uint64);
        if (nr != (3 as int64)) {
            return 5;
        }
        if (out_buf[0] != (65 as uint8) || out_buf[1] != (66 as uint8) || out_buf[2] != (67 as uint8)) {
            return 6;
        }

        // 6. Close FD 0 and verify slot is recycled
        bool c0 = vfs.vfs_close(&ft, fd0);
        if (!c0) {
            return 7;
        }
        int32 fd0_recycled = vfs.vfs_open(&ft, &file, vfs.O_RDWR);
        if (fd0_recycled != 0) {
            return 8; // Must recycle lowest free FD 0
        }

        vfs.vfs_close(&ft, fd0_recycled);
        vfs.vfs_close(&ft, fd1);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vfs_file_seek_modes(self):
        code = """
        import "os/kernel/vfs.kl" as vfs;

        uint8[128] storage;
        vfs.VFSNode file;
        vfs.vfs_node_init(&file, "numbers.bin", vfs.VFS_FILE, 80 as uint64);
        file.data = &storage[0];
        file.data_capacity = 128 as uint64;
        file.size = 100 as uint64;

        vfs.FileTable ft;
        vfs.vfs_file_table_init(&ft);

        int32 fd = vfs.vfs_open(&ft, &file, vfs.O_RDWR);
        if (fd < 0) {
            return 1;
        }

        // 1. SEEK_SET to 20
        int64 p1 = vfs.vfs_fd_lseek(&ft, fd, 20 as int64, vfs.SEEK_SET);
        if (p1 != (20 as int64)) {
            return 2;
        }

        // 2. SEEK_CUR +15 -> offset 35
        int64 p2 = vfs.vfs_fd_lseek(&ft, fd, 15 as int64, vfs.SEEK_CUR);
        if (p2 != (35 as int64)) {
            return 3;
        }

        // 3. SEEK_END -10 -> offset 90 (file.size 100 - 10)
        int64 p3 = vfs.vfs_fd_lseek(&ft, fd, -10 as int64, vfs.SEEK_END);
        if (p3 != (90 as int64)) {
            return 4;
        }

        // 4. Reject negative seek position
        int64 bad_p = vfs.vfs_fd_lseek(&ft, fd, -200 as int64, vfs.SEEK_SET);
        if (bad_p != (-1 as int64)) {
            return 5;
        }

        vfs.vfs_close(&ft, fd);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vfs_stat_node(self):
        code = """
        import "os/kernel/vfs.kl" as vfs;

        vfs.VFSNode file;
        vfs.vfs_node_init(&file, "kernel.sys", vfs.VFS_FILE, 999 as uint64);
        file.size = 16384 as uint64;

        vfs.VFSStat st;
        bool ok = vfs.vfs_stat_node(&file, &st);
        if (!ok) {
            return 1;
        }

        if (st.ino != (999 as uint64) || st.size != (16384 as uint64)) {
            return 2;
        }
        if (st.blksize != (4096 as uint64) || st.blocks != (32 as uint64)) { // 16384 / 512 = 32
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vfs_dup_and_dup2(self):
        code = """
        import "os/kernel/vfs.kl" as vfs;

        vfs.VFSNode file;
        vfs.vfs_node_init(&file, "stdout.log", vfs.VFS_FILE, 10 as uint64);

        vfs.FileTable ft;
        vfs.vfs_file_table_init(&ft);

        int32 fd0 = vfs.vfs_open(&ft, &file, vfs.O_RDWR);
        if (fd0 != 0) {
            return 1;
        }

        // 1. dup(0) should allocate lowest free descriptor (FD 1)
        int32 fd1 = vfs.vfs_dup(&ft, fd0);
        if (fd1 != 1) {
            return 2;
        }
        if (ft.descriptors[fd1].node != &file) {
            return 3;
        }

        // 2. dup2(0, 5) duplicates to specific target FD 5
        int32 fd5 = vfs.vfs_dup2(&ft, fd0, 5);
        if (fd5 != 5) {
            return 4;
        }
        if (ft.descriptors[5].node != &file || !ft.descriptors[5].is_open) {
            return 5;
        }

        // Clean up
        vfs.vfs_close(&ft, fd0);
        vfs.vfs_close(&ft, fd1);
        vfs.vfs_close(&ft, fd5);

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_user_space_stdio_syscall_integration(self):
        code = """
        import "os/kernel/syscall.kl" as sys;
        import "os/userspace/libc/stdio.kl" as stdio;

        sys.ProcessHeap pheap;
        sys.SyscallStatsTable stats;
        sys.syscall_stats_init(&stats);
        sys.process_heap_init(&pheap, 0x00400000 as uint64, 0x00800000 as uint64);

        // 1. putchar and puts via standard descriptors
        int32 ch = stdio.putchar('K', &stats, &pheap, 100 as uint32);
        if (ch != 75) { // 'K' == 75
            return 1;
        }

        int32 res_puts = stdio.puts("Hello KaleOS VFS", &stats, &pheap, 100 as uint32);
        if (res_puts != 0) {
            return 2;
        }

        // 2. open and close system call wrappers
        int32 fd = stdio.open("/dev/null", 2 as uint32, &stats, &pheap, 100 as uint32);
        if (fd < 0) {
            return 3;
        }

        int32 cl = stdio.close(fd, &stats, &pheap, 100 as uint32);
        if (cl < 0) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
