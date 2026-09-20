import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSUserSpaceSupport(unittest.TestCase):
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

    def test_elf_header_validation_and_rejection(self):
        code = """
        import "os/kernel/elf.kl" as elf;

        // 1. Valid ELF 64-bit Header
        elf.ElfHeader hdr;
        elf.elf_header_init(&hdr, 0x0000000000401000 as uint64, 2 as uint16);

        if (!elf.elf_validate_header(&hdr)) {
            return 1;
        }
        if (hdr.ident.magic[0] != 127 as uint8 || hdr.ident.magic[1] != 69 as uint8 ||
            hdr.ident.magic[2] != 76 as uint8 || hdr.ident.magic[3] != 70 as uint8) {
            return 2;
        }
        if (hdr.ident.class_type != elf.ELF_CLASS_64 || hdr.ident.endianness != elf.ELF_DATA_LITTLE) {
            return 3;
        }
        if (hdr.machine != elf.ELF_MACHINE_X86_64 || hdr.entry != 0x0000000000401000 as uint64) {
            return 4;
        }

        // 2. Reject Corrupted Magic
        hdr.ident.magic[0] = 0 as uint8;
        if (elf.elf_validate_header(&hdr)) {
            return 5;
        }
        hdr.ident.magic[0] = 127 as uint8; // restore

        // 3. Reject 32-bit ELF class
        hdr.ident.class_type = elf.ELF_CLASS_32;
        if (elf.elf_validate_header(&hdr)) {
            return 6;
        }
        hdr.ident.class_type = elf.ELF_CLASS_64; // restore

        // 4. Reject Big-Endian ELF
        hdr.ident.endianness = elf.ELF_DATA_BIG;
        if (elf.elf_validate_header(&hdr)) {
            return 7;
        }
        hdr.ident.endianness = elf.ELF_DATA_LITTLE; // restore

        // 5. Reject Incompatible Architecture (e.g. i386)
        hdr.machine = elf.ELF_MACHINE_386;
        if (elf.elf_validate_header(&hdr)) {
            return 8;
        }
        hdr.machine = elf.ELF_MACHINE_X86_64; // restore

        // 6. Reject Relocatable object (ET_REL instead of ET_EXEC/ET_DYN)
        hdr.type = elf.ELF_TYPE_REL;
        if (elf.elf_validate_header(&hdr)) {
            return 9;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_elf_program_header_parsing_and_memory_bounds(self):
        code = """
        import "os/kernel/elf.kl" as elf;

        // Construct mock binary image with 64-byte ElfHeader + two 56-byte ProgramHeaders
        uint8[256] elf_buf;
        int k = 0;
        while (k < 256) {
            elf_buf[k] = 0 as uint8;
            k = k + 1;
        }

        elf.ElfHeader* hdr = (&elf_buf[0]) as elf.ElfHeader*;
        elf.elf_header_init(hdr, 0x00401000 as uint64, 2 as uint16);

        // Segment 0: Code Segment (0x00400000 - 0x00405000)
        // Offset: 128, Filesz: 4096, Memsz: 4096, Flags: PF_R | PF_X
        elf.ElfProgramHeader* ph0 = elf.elf_get_program_header(&elf_buf[0], hdr, 0 as uint16);
        elf.elf_program_header_init(ph0, elf.PT_LOAD, elf.PF_R | elf.PF_X, 128 as uint64, 0x00400000 as uint64, 4096 as uint64, 4096 as uint64, 4096 as uint64);

        // Segment 1: Data + BSS Segment (0x00600000 - 0x00608000)
        // Offset: 4224, Filesz: 4096, Memsz: 32768, Flags: PF_R | PF_W
        elf.ElfProgramHeader* ph1 = elf.elf_get_program_header(&elf_buf[0], hdr, 1 as uint16);
        elf.elf_program_header_init(ph1, elf.PT_LOAD, elf.PF_R | elf.PF_W, 4224 as uint64, 0x00600000 as uint64, 4096 as uint64, 32768 as uint64, 4096 as uint64);

        // Verify segment attribute inspectors
        if (!elf.elf_is_loadable(ph0) || !elf.elf_is_executable(ph0) || elf.elf_is_writable(ph0)) {
            return 1;
        }
        if (!elf.elf_is_loadable(ph1) || elf.elf_is_executable(ph1) || !elf.elf_is_writable(ph1)) {
            return 2;
        }

        // Check VMM protection flags translation
        // ph0: Present (1) | User (4) = 5
        // ph1: Present (1) | User (4) | Writable (2) = 7
        if (elf.elf_segment_vmm_flags(ph0) != 5 as uint64) {
            return 3;
        }
        if (elf.elf_segment_vmm_flags(ph1) != 7 as uint64) {
            return 4;
        }

        // Calculate overall virtual memory footprint
        uint64 min_v = 0 as uint64;
        uint64 max_v = 0 as uint64;
        uint64 total_sz = 0 as uint64;
        bool ok = elf.elf_calculate_memory_bounds(&elf_buf[0], hdr, &min_v, &max_v, &total_sz);
        if (!ok) {
            return 5;
        }
        if (min_v != 0x00400000 as uint64) {
            return 6;
        }
        if (max_v != 0x00608000 as uint64) {
            return 7;
        }
        if (total_sz != (0x00608000 - 0x00400000) as uint64) {
            return 8;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_elf_segment_loader_and_bss_zeroing(self):
        code = """
        import "os/kernel/elf.kl" as elf;

        // Buffer for ELF file
        uint8[512] elf_file;
        int i = 0;
        while (i < 512) {
            elf_file[i] = 0 as uint8;
            i = i + 1;
        }

        // Buffer for loaded process memory
        uint8[512] dest_mem;
        i = 0;
        while (i < 512) {
            dest_mem[i] = 255 as uint8; // Poison with 0xFF
            i = i + 1;
        }

        elf.ElfHeader* hdr = (&elf_file[0]) as elf.ElfHeader*;
        elf.elf_header_init(hdr, 0x400000 as uint64, 1 as uint16);

        // Put test payload bytes at file offset 256 (after header and program headers)
        elf_file[256] = 0xAA as uint8;
        elf_file[257] = 0xBB as uint8;
        elf_file[258] = 0xCC as uint8;
        elf_file[259] = 0xDD as uint8;

        // Segment has filesz = 4 bytes, memsz = 16 bytes (12 bytes of BSS)
        elf.ElfProgramHeader* ph = elf.elf_get_program_header(&elf_file[0], hdr, 0 as uint16);
        elf.elf_program_header_init(ph, elf.PT_LOAD, elf.PF_R | elf.PF_W, 256 as uint64, 0x400000 as uint64, 4 as uint64, 16 as uint64, 4096 as uint64);

        bool load_ok = elf.elf_load_segment(&elf_file[0], ph, &dest_mem[0], 0x400000 as uint64);
        if (!load_ok) {
            return 1;
        }

        // Verify loaded payload data
        if (dest_mem[0] != 0xAA as uint8 || dest_mem[1] != 0xBB as uint8 ||
            dest_mem[2] != 0xCC as uint8 || dest_mem[3] != 0xDD as uint8) {
            return 2;
        }

        // Verify remaining 12 bytes of BSS zero-initialized
        int b = 4;
        while (b < 16) {
            if (dest_mem[b] != 0 as uint8) {
                return 3;
            }
            b = b + 1;
        }

        // Verify unmapped memory beyond segment remains untouched (0xFF)
        if (dest_mem[16] != 255 as uint8) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_gdt_tss_descriptor_and_ring3_privilege_selectors(self):
        code = """
        import "os/kernel/gdt.kl" as gdt;

        gdt.GDTTable table;
        gdt.gdt_init(&table);

        // Before TSS setup, limit is 39 (5 * 8 - 1)
        if (table.pointer.limit != 39) {
            return 1;
        }

        // Verify privilege selectors
        // User CS RPL 3 = 0x18 | 3 = 0x1B (27)
        // User SS RPL 3 = 0x20 | 3 = 0x23 (35)
        if (gdt.USER_CS_RPL3 != 27 as uint16 || gdt.USER_SS_RPL3 != 35 as uint16) {
            return 2;
        }
        if (gdt.TSS_SELECTOR != 40 as uint16) { // 0x28
            return 3;
        }

        // Initialize 64-bit TSS structure
        gdt.TSS64 tss;
        gdt.tss_init(&tss, 0x00200000 as uint64); // Ring 0 kernel stack at 2MB

        if (tss.rsp0 != 0x00200000 as uint64 || tss.iopb_offset != 104 as uint16) {
            return 4;
        }

        // Setup TSS in GDT (Base: 0x0000000000015000, Limit: 103 bytes)
        uint64 tss_addr = 0x0000000000015000 as uint64;
        gdt.gdt_setup_tss(&table, tss_addr, 103 as uint32);

        // With TSS (16 bytes = 2 entries), GDT has 7 descriptors -> limit = 55
        if (table.pointer.limit != 55) {
            return 5;
        }

        // TSS Low descriptor access byte must be 137 (0x89: Present, DPL=0, 64-bit TSS available)
        if (table.tss_low.access != 137) {
            return 6;
        }
        if (table.tss_low.limit_low != 103) {
            return 7;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_user_stack_frame_layout_and_alignment(self):
        code = """
        import "os/kernel/process.kl" as proc;

        // Allocate scratch buffer for stack construction (128 words)
        uint64[128] stack_buf;
        int i = 0;
        while (i < 128) {
            stack_buf[i] = 0 as uint64;
            i = i + 1;
        }

        uint64[2] argv_ptrs;
        argv_ptrs[0] = 0x00007FFFFFFFFF10 as uint64; // "init"
        argv_ptrs[1] = 0x00007FFFFFFFFF20 as uint64; // "--verbose"

        uint64[1] envp_ptrs;
        envp_ptrs[0] = 0x00007FFFFFFFFF50 as uint64; // "PATH=/bin"

        proc.UserStackInfo info;
        uint64 user_stack_top = proc.USER_STACK_TOP; // 0x00007FFFFFFFF000

        uint64 initial_rsp = proc.setup_user_stack(
            &stack_buf[0],
            128 as uint64,
            user_stack_top,
            2,
            &argv_ptrs[0],
            1,
            &envp_ptrs[0],
            0x0000000000401000 as uint64, // entry point
            0x0000000000400040 as uint64, // phdr address
            2 as uint16,
            56 as uint16,
            &info
        );

        if (initial_rsp == 0 as uint64) {
            return 1;
        }

        // Verify 16-byte alignment of the initial stack pointer
        if ((initial_rsp % 16 as uint64) != 0 as uint64) {
            return 2;
        }

        // Verify stack top is properly relative to USER_STACK_TOP
        if (initial_rsp >= user_stack_top) {
            return 3;
        }

        // Inspect written stack contents:
        // [rsp + 0] = argc (2)
        if (stack_buf[0] != 2 as uint64) {
            return 4;
        }
        // [rsp + 8] = argv[0]
        if (stack_buf[1] != 0x00007FFFFFFFFF10 as uint64) {
            return 5;
        }
        // [rsp + 16] = argv[1]
        if (stack_buf[2] != 0x00007FFFFFFFFF20 as uint64) {
            return 6;
        }
        // [rsp + 24] = NULL terminator for argv
        if (stack_buf[3] != 0 as uint64) {
            return 7;
        }
        // [rsp + 32] = envp[0]
        if (stack_buf[4] != 0x00007FFFFFFFFF50 as uint64) {
            return 8;
        }
        // [rsp + 40] = NULL terminator for envp
        if (stack_buf[5] != 0 as uint64) {
            return 9;
        }

        // Inspect auxv entries: AT_ENTRY tag & value
        if (stack_buf[6] != proc.AT_ENTRY || stack_buf[7] != 0x0000000000401000 as uint64) {
            return 10;
        }

        // Inspect AT_PAGESZ tag & value (4096)
        if (stack_buf[14] != proc.AT_PAGESZ || stack_buf[15] != 4096 as uint64) {
            return 11;
        }

        // Inspect AT_NULL terminator tag
        if (stack_buf[16] != proc.AT_NULL) {
            return 12;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_user_process_creation_lifecycle(self):
        code = """
        import "os/kernel/sched.kl" as sched;
        import "os/kernel/elf.kl" as elf;
        import "os/kernel/process.kl" as proc;

        sched.Scheduler scheduler;
        sched.scheduler_init(&scheduler, 10 as uint32);

        // Build valid mock ELF image
        uint8[256] elf_image;
        int i = 0;
        while (i < 256) {
            elf_image[i] = 0 as uint8;
            i = i + 1;
        }

        elf.ElfHeader* hdr = (&elf_image[0]) as elf.ElfHeader*;
        elf.elf_header_init(hdr, 0x00401000 as uint64, 1 as uint16);

        elf.ElfProgramHeader* ph = elf.elf_get_program_header(&elf_image[0], hdr, 0 as uint16);
        elf.elf_program_header_init(ph, elf.PT_LOAD, elf.PF_R | elf.PF_X, 128 as uint64, 0x00400000 as uint64, 4096 as uint64, 4096 as uint64, 4096 as uint64);

        // Stack scratch buffer
        uint64[64] stack_buf;

        proc.UserProcess user_proc;
        bool ok = proc.create_user_process(
            &scheduler,
            &user_proc,
            &elf_image[0],
            256 as uint64,
            0x00200000 as uint64, // Kernel stack
            0x00001000 as uint64, // PML4
            0,
            null,
            0,
            null,
            &stack_buf[0],
            64 as uint64
        );

        if (!ok) {
            return 1;
        }
        if (!user_proc.is_alive || user_proc.pcb.id == 0 as uint32) {
            return 2;
        }

        // Verify scheduler state
        if (scheduler.ready_count != 1 as uint32 || scheduler.total_processes != 1 as uint32) {
            return 3;
        }

        // Verify CPU Context initialized for Ring 3
        if (user_proc.context.rip != 0x00401000 as uint64) {
            return 4;
        }
        if (user_proc.context.cs != 27 as uint64) { // 0x1B (User CS with RPL 3)
            return 5;
        }
        if (user_proc.context.ss != 35 as uint64) { // 0x23 (User SS with RPL 3)
            return 6;
        }
        if (user_proc.context.rflags != 514 as uint64) { // 0x202 (IF enabled)
            return 7;
        }
        if (user_proc.context.rsp != user_proc.user_stack_rsp) {
            return 8;
        }

        // Verify process heap setup above ELF segment
        if (user_proc.heap.heap_start != 0x00401000 as uint64) {
            return 9;
        }

        // Terminate process
        proc.terminate_user_process(&scheduler, &user_proc, 0);
        if (user_proc.is_alive || user_proc.pcb.state != sched.ProcessState.PROCESS_TERMINATED) {
            return 10;
        }
        if (scheduler.ready_count != 0 as uint32) {
            return 11;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_user_space_libc_wrappers_and_allocator(self):
        code = """
        import "os/kernel/syscall.kl" as sys;
        import "os/userspace/libc/syscall.kl" as l_sys;
        import "os/userspace/libc/string.kl" as l_str;
        import "os/userspace/libc/stdio.kl" as l_io;
        import "os/userspace/libc/stdlib.kl" as l_std;

        sys.SyscallStatsTable stats;
        sys.syscall_stats_init(&stats);

        sys.ProcessHeap heap;
        sys.process_heap_init(&heap, 0x01000000 as uint64, 0x10000000 as uint64);

        // 1. Test string operations
        char* msg = "Hello User Space!";
        if (l_str.strlen(msg) != 17 as uint64) {
            return 1;
        }
        if (l_str.strcmp("test", "test") != 0 || l_str.strcmp("abc", "abd") >= 0) {
            return 2;
        }

        // 2. Test stdio write & puts
        int64 w = l_io.write(l_io.STDOUT_FILENO, msg as uint8*, 17 as uint64, &stats, &heap, 100 as uint32);
        if (w != 17) {
            return 3;
        }
        int32 p = l_io.puts("Kale OS Libc Active", &stats, &heap, 100 as uint32);
        if (p != 0) {
            return 4;
        }

        // 3. Test stdlib getpid & getppid
        int32 pid = l_std.getpid(&stats, &heap, 100 as uint32);
        if (pid != 100) {
            return 5;
        }
        int32 ppid = l_std.getppid(&stats, &heap, 100 as uint32, 1 as uint32);
        if (ppid != 1) {
            return 6;
        }

        // 4. Test stdlib sched_yield
        bool yielded = false;
        int32 yr = l_std.sched_yield(&stats, &heap, 100 as uint32, &yielded);
        if (yr != 0 || !yielded) {
            return 7;
        }

        // 5. Test stdlib malloc and heap expansion
        uint8* ptr1 = l_std.malloc(1024 as uint64, &stats, &heap, 100 as uint32);
        if (ptr1 == null || (ptr1 as uint64) != 0x01000000 as uint64) {
            return 8;
        }

        uint8* ptr2 = l_std.malloc(2048 as uint64, &stats, &heap, 100 as uint32);
        if (ptr2 == null || (ptr2 as uint64) != 0x01000400 as uint64) {
            return 9;
        }

        // 6. Test stdlib exit
        int32 exit_code = 0;
        bool terminated = false;
        l_std.exit(7, &stats, &heap, 100 as uint32, &exit_code, &terminated);
        if (!terminated || exit_code != 7) {
            return 10;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
