import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSSyscallInterface(unittest.TestCase):
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

    def test_process_control_syscalls(self):
        code = """
        import "os/kernel/syscall.kl" as sys;

        sys.SyscallStatsTable stats;
        sys.syscall_stats_init(&stats);

        sys.ProcessHeap heap;
        sys.process_heap_init(&heap, 0x0000000001000000 as uint64, 0x0000000010000000 as uint64);

        int32 exit_code = 0;
        bool terminated = false;
        bool yielded = false;

        // 1. Test SYS_GETPID (39)
        sys.SyscallContext ctx;
        ctx.number = 39 as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 42 as uint32, 1 as uint32, 5000 as uint64, 1024 as uint64, 512 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != 42 as uint64 || ctx.error != 0) {
            return 1;
        }

        // 2. Test SYS_GETPPID (110)
        ctx.number = 110 as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 42 as uint32, 1 as uint32, 5000 as uint64, 1024 as uint64, 512 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != 1 as uint64 || ctx.error != 0) {
            return 2;
        }

        // 3. Test SYS_SCHED_YIELD (24)
        ctx.number = 24 as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 42 as uint32, 1 as uint32, 5000 as uint64, 1024 as uint64, 512 as uint64, &exit_code, &terminated, &yielded);
        if (!yielded || ctx.return_value != 0 as uint64) {
            return 3;
        }

        // 4. Test SYS_EXIT (60)
        ctx.number = 60 as uint64;
        ctx.arg1 = 15 as uint64; // exit code 15
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 42 as uint32, 1 as uint32, 5000 as uint64, 1024 as uint64, 512 as uint64, &exit_code, &terminated, &yielded);
        if (!terminated || exit_code != 15) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_memory_management_syscalls(self):
        code = """
        import "os/kernel/syscall.kl" as sys;

        sys.SyscallStatsTable stats;
        sys.syscall_stats_init(&stats);

        sys.ProcessHeap heap;
        // Heap from 16MB to 272MB
        sys.process_heap_init(&heap, 0x0000000001000000 as uint64, 0x0000000010000000 as uint64);

        int32 exit_code = 0;
        bool terminated = false;
        bool yielded = false;

        // 1. Query brk with arg1 = 0
        sys.SyscallContext ctx;
        ctx.number = 12 as uint64;
        ctx.arg1 = 0 as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 10 as uint32, 1 as uint32, 0 as uint64, 0 as uint64, 0 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != 0x0000000001000000 as uint64) {
            return 1;
        }

        // 2. Expand brk to 32MB
        ctx.arg1 = 0x0000000002000000 as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 10 as uint32, 1 as uint32, 0 as uint64, 0 as uint64, 0 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != 0x0000000002000000 as uint64 || heap.heap_break != 0x0000000002000000 as uint64) {
            return 2;
        }

        // 3. Reject brk exceeding heap_max
        ctx.arg1 = 0x0000000020000000 as uint64; // Exceeds 272MB
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 10 as uint32, 1 as uint32, 0 as uint64, 0 as uint64, 0 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.error != sys.ENOMEM || ctx.return_value != 0x0000000002000000 as uint64) {
            return 3;
        }

        // 4. Test SYS_MMAP (9) with 64KB length
        ctx.number = 9 as uint64;
        ctx.arg2 = 65536 as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 10 as uint32, 1 as uint32, 0 as uint64, 0 as uint64, 0 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != 0x0000700000000000 as uint64 || ctx.error != 0) {
            return 4;
        }
        if (heap.mmap_current != 0x0000700000010000 as uint64) {
            return 5;
        }

        // 5. Test SYS_MUNMAP (11)
        ctx.number = 11 as uint64;
        ctx.arg1 = 0x0000700000000000 as uint64;
        ctx.arg2 = 65536 as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 10 as uint32, 1 as uint32, 0 as uint64, 0 as uint64, 0 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != 0 as uint64 || ctx.error != 0) {
            return 6;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_system_information_syscalls(self):
        code = """
        import "os/kernel/syscall.kl" as sys;

        sys.SyscallStatsTable stats;
        sys.syscall_stats_init(&stats);

        sys.ProcessHeap heap;
        sys.process_heap_init(&heap, 0x0000000001000000 as uint64, 0x0000000010000000 as uint64);

        int32 exit_code = 0;
        bool terminated = false;
        bool yielded = false;

        // 1. Test SYS_UNAME (63)
        sys.Utsname un;
        sys.SyscallContext ctx;
        ctx.number = 63 as uint64;
        ctx.arg1 = (&un) as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 125000 as uint64, 1048576 as uint64, 524288 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != 0 as uint64 || ctx.error != 0) {
            return 1;
        }
        if (un.sysname[0] != 'K' as uint8 || un.sysname[1] != 'a' as uint8 || un.sysname[4] != 'O' as uint8) {
            return 2;
        }
        if (un.machine[0] != 'x' as uint8 || un.machine[4] != '6' as uint8) {
            return 3;
        }

        // 2. Test SYS_SYSINFO (99)
        sys.Sysinfo sinfo;
        ctx.number = 99 as uint64;
        ctx.arg1 = (&sinfo) as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 125000 as uint64, 1048576 as uint64, 524288 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != 0 as uint64 || ctx.error != 0) {
            return 4;
        }
        // Uptime in seconds: 125000 ms / 1000 = 125 sec
        if (sinfo.uptime != 125 as uint64) {
            return 5;
        }
        if (sinfo.totalram != 1048576 as uint64 || sinfo.freeram != 524288 as uint64) {
            return 6;
        }

        // 3. Test SYS_GETTIMEOFDAY (96)
        sys.TimeVal tv;
        ctx.number = 96 as uint64;
        ctx.arg1 = (&tv) as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 125450 as uint64, 1048576 as uint64, 524288 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != 0 as uint64 || ctx.error != 0) {
            return 7;
        }
        if (tv.tv_sec != 125 as uint64 || tv.tv_usec != 450000 as uint64) {
            return 8;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_file_io_and_error_validation(self):
        code = """
        import "os/kernel/syscall.kl" as sys;

        sys.SyscallStatsTable stats;
        sys.syscall_stats_init(&stats);

        sys.ProcessHeap heap;
        sys.process_heap_init(&heap, 0x0000000001000000 as uint64, 0x0000000010000000 as uint64);

        int32 exit_code = 0;
        bool terminated = false;
        bool yielded = false;

        // 1. SYS_WRITE to stdout (FD 1) with valid user buffer
        sys.SyscallContext ctx;
        ctx.number = 1 as uint64;
        ctx.arg1 = 1 as uint64; // stdout
        ctx.arg2 = 0x0000000000401000 as uint64; // user buffer
        ctx.arg3 = 64 as uint64; // 64 bytes
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 0 as uint64, 0 as uint64, 0 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.return_value != 64 as uint64 || ctx.error != 0) {
            return 1;
        }

        // 2. SYS_WRITE with invalid FD (e.g. 5) -> EBADF
        ctx.arg1 = 5 as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 0 as uint64, 0 as uint64, 0 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.error != sys.EBADF) {
            return 2;
        }

        // 3. SYS_WRITE with kernel address -> EFAULT
        ctx.arg1 = 1 as uint64;
        ctx.arg2 = 0xFFFFFFFF80001000 as uint64; // kernel space address
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 0 as uint64, 0 as uint64, 0 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.error != sys.EFAULT) {
            return 3;
        }

        // 4. Unknown syscall number 999 -> ENOSYS
        ctx.number = 999 as uint64;
        sys.syscall_dispatch_context(&ctx, &stats, &heap, 1 as uint32, 0 as uint32, 0 as uint64, 0 as uint64, 0 as uint64, &exit_code, &terminated, &yielded);
        if (ctx.error != sys.ENOSYS) {
            return 4;
        }

        // Check stats counter
        if (stats.total_invocations != 4 as uint64 || stats.total_errors != 3 as uint64) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_syscall_profiling_and_stats(self):
        code = """
        import "os/kernel/syscall.kl" as sys;

        sys.SyscallStatsTable stats;
        sys.syscall_stats_init(&stats);

        // Record several calls to SYS_GETPID (39) with varying durations
        sys.syscall_stats_record(&stats, 39 as uint64, 15 as uint64, false);
        sys.syscall_stats_record(&stats, 39 as uint64, 25 as uint64, false);
        sys.syscall_stats_record(&stats, 39 as uint64, 10 as uint64, false);

        if (stats.stats[39].count != 3 as uint64) {
            return 1;
        }
        if (stats.stats[39].total_time_ticks != 50 as uint64) {
            return 2;
        }
        if (stats.stats[39].min_time_ticks != 10 as uint64) {
            return 3;
        }
        if (stats.stats[39].max_time_ticks != 25 as uint64) {
            return 4;
        }

        // Record error call
        sys.syscall_stats_record(&stats, 1 as uint64, 5 as uint64, true);
        if (stats.total_invocations != 4 as uint64 || stats.total_errors != 1 as uint64) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
