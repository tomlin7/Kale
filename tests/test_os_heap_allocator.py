import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSHeapAllocator(unittest.TestCase):
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

    def test_kernel_heap_initialization_and_metadata(self):
        code = """
        import "os/kernel/heap.kl" as heap;

        uint8[4096] raw_buf;
        uint64 base = &raw_buf[0] as uint64;

        heap.Heap h;
        bool ok = heap.heap_init(&h, base, 4096 as uint64);
        if (!ok) {
            return 1;
        }

        if (h.start != base || h.end != base + (4096 as uint64) || h.max_size != (4096 as uint64)) {
            return 2;
        }
        if (h.used != (0 as uint64)) {
            return 3;
        }

        // Initial free block
        heap.BlockHeader* init_b = h.free_list;
        if (init_b == null) {
            return 4;
        }
        if (!init_b.is_free || init_b.magic != heap.BLOCK_MAGIC) {
            return 5;
        }
        if (init_b.size != (4096 as uint64) - heap.BLOCK_HEADER_SIZE) {
            return 6;
        }
        if (init_b.prev != null || init_b.next != null) {
            return 7;
        }

        // Reject too small size (< BLOCK_HEADER_SIZE + MIN_ALLOC_SIZE)
        heap.Heap h_invalid;
        bool bad = heap.heap_init(&h_invalid, base, 32 as uint64);
        if (bad) {
            return 8;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_kernel_heap_allocation_and_alignment(self):
        code = """
        import "os/kernel/heap.kl" as heap;

        uint8[8192] raw_buf;
        uint64 base = &raw_buf[0] as uint64;

        heap.Heap h;
        heap.heap_init(&h, base, 8192 as uint64);

        // Request 13 bytes -> should be aligned to 16 bytes
        uint8* p1 = heap.heap_alloc(&h, 13 as uint64);
        if (p1 == null) {
            return 1;
        }
        if (((p1 as uint64) & (15 as uint64)) != (0 as uint64)) {
            return 2; // Not 16-byte aligned
        }

        heap.BlockHeader* b1 = ((p1 as uint64) - heap.BLOCK_HEADER_SIZE) as heap.BlockHeader*;
        if (b1.is_free || b1.size != (16 as uint64) || b1.magic != heap.BLOCK_MAGIC) {
            return 3;
        }

        // Request 35 bytes -> aligned to 48 bytes
        uint8* p2 = heap.heap_alloc(&h, 35 as uint64);
        if (p2 == null) {
            return 4;
        }
        if (((p2 as uint64) & (15 as uint64)) != (0 as uint64)) {
            return 5;
        }

        heap.BlockHeader* b2 = ((p2 as uint64) - heap.BLOCK_HEADER_SIZE) as heap.BlockHeader*;
        if (b2.is_free || b2.size != (48 as uint64)) {
            return 6;
        }

        // Check stats
        if (h.stats.total_allocations != (2 as uint64) || h.stats.current_allocations != (2 as uint64)) {
            return 7;
        }
        if (h.stats.total_allocated != (16 as uint64) + (48 as uint64)) {
            return 8;
        }
        if (h.used != (16 as uint64) + (48 as uint64) + (2 as uint64) * heap.BLOCK_HEADER_SIZE) {
            return 9;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_kernel_heap_block_splitting(self):
        code = """
        import "os/kernel/heap.kl" as heap;

        uint8[4096] raw_buf;
        uint64 base = &raw_buf[0] as uint64;

        heap.Heap h;
        heap.heap_init(&h, base, 4096 as uint64);

        // Allocate 128 bytes
        uint8* p = heap.heap_alloc(&h, 128 as uint64);
        if (p == null) {
            return 1;
        }

        heap.BlockHeader* b = ((p as uint64) - heap.BLOCK_HEADER_SIZE) as heap.BlockHeader*;
        if (b.size != (128 as uint64)) {
            return 2;
        }

        // Following block must be the remainder free block
        heap.BlockHeader* rem = b.next;
        if (rem == null) {
            return 3;
        }
        if (!rem.is_free || rem.magic != heap.BLOCK_MAGIC) {
            return 4;
        }
        if (rem.prev != b) {
            return 5;
        }

        uint64 expected_rem_size = (4096 as uint64) - (128 as uint64) - ((2 as uint64) * heap.BLOCK_HEADER_SIZE);
        if (rem.size != expected_rem_size) {
            return 6;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_kernel_heap_bi_directional_coalescing(self):
        code = """
        import "os/kernel/heap.kl" as heap;

        uint8[8192] raw_buf;
        uint64 base = &raw_buf[0] as uint64;

        heap.Heap h;
        heap.heap_init(&h, base, 8192 as uint64);

        // Allocate three contiguous blocks A, B, C
        uint8* pA = heap.heap_alloc(&h, 64 as uint64);
        uint8* pB = heap.heap_alloc(&h, 64 as uint64);
        uint8* pC = heap.heap_alloc(&h, 64 as uint64);

        if (pA == null || pB == null || pC == null) {
            return 1;
        }

        // 1. Free A: becomes a free block at base
        bool fA = heap.heap_free(&h, pA);
        if (!fA) {
            return 2;
        }

        // 2. Free C: merges with the trailing unallocated block (Right coalescing)
        bool fC = heap.heap_free(&h, pC);
        if (!fC) {
            return 3;
        }

        // At this point, middle block B is allocated, flanked by free block A and free block C
        if (h.stats.current_allocations != (1 as uint64)) {
            return 4;
        }

        // 3. Free B: merges with left neighbor A AND right neighbor C (Bi-directional coalescing!)
        bool fB = heap.heap_free(&h, pB);
        if (!fB) {
            return 5;
        }

        // The entire heap should now be a single monolithic free block!
        if (h.used != (0 as uint64)) {
            return 6;
        }
        if (h.stats.current_allocations != (0 as uint64)) {
            return 7;
        }

        heap.BlockHeader* head = h.free_list;
        if (head.next != null || !head.is_free) {
            return 8; // Still fragmented
        }
        if (head.size != (8192 as uint64) - heap.BLOCK_HEADER_SIZE) {
            return 9;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_kernel_heap_reallocation_lifecycle(self):
        code = """
        import "os/kernel/heap.kl" as heap;

        uint8[8192] raw_buf;
        uint64 base = &raw_buf[0] as uint64;

        heap.Heap h;
        heap.heap_init(&h, base, 8192 as uint64);

        // 1. Realloc with null pointer behaves like alloc
        uint8* p = heap.heap_realloc(&h, null, 64 as uint64);
        if (p == null) {
            return 1;
        }

        // Write test pattern
        p[0] = 77 as uint8;
        p[63] = 88 as uint8;

        // 2. In-place growth (free block immediately follows p)
        uint8* p_grown = heap.heap_realloc(&h, p, 128 as uint64);
        if (p_grown == null) {
            return 2;
        }
        if (p_grown != p) {
            return 3; // Should have expanded in-place!
        }
        if (p_grown[0] != (77 as uint8) || p_grown[63] != (88 as uint8)) {
            return 4; // Data integrity lost
        }

        // 3. Shrink block
        uint8* p_shrunk = heap.heap_realloc(&h, p_grown, 32 as uint64);
        if (p_shrunk != p_grown) {
            return 5;
        }
        if (p_shrunk[0] != (77 as uint8)) {
            return 6;
        }

        // 4. Realloc with 0 size frees block
        uint8* p_freed = heap.heap_realloc(&h, p_shrunk, 0 as uint64);
        if (p_freed != null) {
            return 7;
        }
        if (h.stats.current_allocations != (0 as uint64)) {
            return 8;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_kernel_heap_calloc_zero_initialization(self):
        code = """
        import "os/kernel/heap.kl" as heap;

        uint8[4096] raw_buf;
        uint64 base = &raw_buf[0] as uint64;

        // Pre-fill buffer with garbage bytes (0xFF)
        int k = 0;
        while (k < 4096) {
            raw_buf[k] = 255 as uint8;
            k = k + 1;
        }

        heap.Heap h;
        heap.heap_init(&h, base, 4096 as uint64);

        // Calloc 16 elements of 8 bytes = 128 bytes
        uint8* p = heap.heap_calloc(&h, 16 as uint64, 8 as uint64);
        if (p == null) {
            return 1;
        }

        // Verify all 128 bytes are strictly 0
        int i = 0;
        while (i < 128) {
            if (p[i] != (0 as uint8)) {
                return 2;
            }
            i = i + 1;
        }

        heap.heap_free(&h, p);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_advanced_heap_segregated_size_classes(self):
        code = """
        import "os/kernel/heap.kl" as heap;

        uint8[16384] raw_buf;
        uint64 base = &raw_buf[0] as uint64;

        heap.AdvancedHeap aheap;
        bool ok = heap.advanced_heap_init(&aheap, base, 16384 as uint64);
        if (!ok) {
            return 1;
        }

        // Small allocations: 16, 32, 64 bytes
        uint8* p16 = heap.advanced_heap_alloc(&aheap, 16 as uint64);
        uint8* p32 = heap.advanced_heap_alloc(&aheap, 32 as uint64);
        uint8* p64 = heap.advanced_heap_alloc(&aheap, 64 as uint64);

        if (p16 == null || p32 == null || p64 == null) {
            return 2;
        }

        // Free small block p32 into segregated class list
        bool f32 = heap.advanced_heap_free(&aheap, p32);
        if (!f32) {
            return 3;
        }
        if (aheap.size_classes[1].free_list == null) {
            return 4; // Should be cached in 32-byte class bucket
        }

        // Reallocate 32 bytes: should immediately reuse cached bucket!
        uint8* p32_reuse = heap.advanced_heap_alloc(&aheap, 30 as uint64);
        if (p32_reuse != p32) {
            return 5; // Must reuse identical block
        }

        // Clean up remaining allocations
        heap.advanced_heap_free(&aheap, p16);
        heap.advanced_heap_free(&aheap, p32_reuse);
        heap.advanced_heap_free(&aheap, p64);

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_kernel_heap_corruption_detection_and_integrity(self):
        code = """
        import "os/kernel/heap.kl" as heap;

        uint8[8192] raw_buf;
        uint64 base = &raw_buf[0] as uint64;

        heap.Heap h;
        heap.heap_init(&h, base, 8192 as uint64);

        uint8* p1 = heap.heap_alloc(&h, 64 as uint64);
        uint8* p2 = heap.heap_alloc(&h, 64 as uint64);

        // 1. Healthy heap: no corruption
        if (heap.heap_detect_corruption(&h)) {
            return 1;
        }

        // 2. Reject double-free
        bool f1 = heap.heap_free(&h, p1);
        if (!f1) {
            return 2;
        }
        bool double_free = heap.heap_free(&h, p1);
        if (double_free) {
            return 3; // Must reject double-free
        }

        // 3. Corrupt block header magic
        heap.BlockHeader* b2 = ((p2 as uint64) - heap.BLOCK_HEADER_SIZE) as heap.BlockHeader*;
        b2.magic = 0xDEADBEEF as uint32;
        if (!heap.heap_detect_corruption(&h)) {
            return 4; // Must detect corrupted magic
        }
        b2.magic = heap.BLOCK_MAGIC; // Restore

        // 4. Corrupt pointer linkage
        b2.next = (base + 999999 as uint64) as heap.BlockHeader*;
        if (!heap.heap_detect_corruption(&h)) {
            return 5; // Must detect out-of-bounds pointer
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_kernel_heap_leak_detection_and_metrics(self):
        code = """
        import "os/kernel/heap.kl" as heap;

        uint8[8192] raw_buf;
        uint64 base = &raw_buf[0] as uint64;

        heap.Heap h;
        heap.heap_init(&h, base, 8192 as uint64);

        // Allocate 4 blocks
        uint8* p1 = heap.heap_alloc(&h, 32 as uint64);
        uint8* p2 = heap.heap_alloc(&h, 64 as uint64);
        uint8* p3 = heap.heap_alloc(&h, 128 as uint64);
        uint8* p4 = heap.heap_alloc(&h, 256 as uint64);

        // Free 1 block
        heap.heap_free(&h, p2);

        // Check leaks: 3 active allocations remaining
        uint64 leaks = heap.heap_check_leaks(&h);
        if (leaks != (3 as uint64)) {
            return 1;
        }

        heap.HeapStats stats = heap.heap_get_stats(&h);
        if (stats.total_allocations != (4 as uint64)) {
            return 2;
        }
        if (stats.total_frees != (1 as uint64)) {
            return 3;
        }
        if (stats.current_allocations != (3 as uint64)) {
            return 4;
        }
        if (stats.peak_usage == (0 as uint64)) {
            return 5;
        }

        // Clean up remaining
        heap.heap_free(&h, p1);
        heap.heap_free(&h, p3);
        heap.heap_free(&h, p4);

        if (heap.heap_check_leaks(&h) != (0 as uint64)) {
            return 6;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_kernel_heap_vmm_large_allocation_mapping(self):
        code = """
        import "os/kernel/heap.kl" as heap;

        uint8[8192] raw_buf;
        uint64 base = &raw_buf[0] as uint64;

        heap.Heap h;
        heap.heap_init(&h, base, 8192 as uint64);

        heap.PageMapper mapper;
        heap.page_mapper_init(&mapper, 0x00400000 as uint64); // Frame pool starts at 4MB

        // Large allocation >= 64KB (128 KB = 32 pages)
        uint64 large_size = 131072 as uint64;
        uint64 virt_target = 0x0000000100000000 as uint64;
        uint8* large_ptr = heap.heap_alloc_large(&h, &mapper, large_size, virt_target);

        if (large_ptr == null) {
            return 1;
        }
        if ((large_ptr as uint64) != virt_target) {
            return 2;
        }
        if (mapper.mapped_count != (32 as uint64)) {
            return 3; // 128KB / 4KB = 32 pages mapped
        }

        // Free large allocation
        bool f_ok = heap.heap_free_large(&h, &mapper, large_ptr, large_size);
        if (!f_ok) {
            return 4;
        }
        if (mapper.mapped_count != (0 as uint64)) {
            return 5; // All 32 pages unmapped
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_user_space_heap_allocator_integration(self):
        code = """
        import "os/kernel/syscall.kl" as sys;
        import "os/userspace/libc/heap.kl" as libc_heap;
        import "os/userspace/libc/stdlib.kl" as stdlib;

        uint8[16384] user_mem;
        uint64 base = &user_mem[0] as uint64;

        sys.ProcessHeap pheap;
        sys.SyscallStatsTable stats;
        sys.syscall_stats_init(&stats);
        sys.process_heap_init(&pheap, base, base + (16384 as uint64));

        libc_heap.UserHeap uheap;
        libc_heap.user_heap_init(&uheap, base, base + (16384 as uint64));

        // 1. User malloc
        uint8* u1 = libc_heap.user_malloc(&uheap, 64 as uint64, &stats, &pheap, 100 as uint32);
        uint8* u2 = libc_heap.user_malloc(&uheap, 128 as uint64, &stats, &pheap, 100 as uint32);
        if (u1 == null || u2 == null) {
            return 1;
        }

        // Write test markers
        u1[0] = 111 as uint8;
        u2[0] = 222 as uint8;

        // 2. User free and coalescing
        bool f1 = libc_heap.user_free(&uheap, u1);
        bool f2 = libc_heap.user_free(&uheap, u2);
        if (!f1 || !f2) {
            return 2;
        }

        // 3. User calloc via stdlib
        uint8* c = stdlib.calloc(8 as uint64, 8 as uint64, &stats, &pheap, 100 as uint32);
        if (c == null) {
            return 3;
        }
        int k = 0;
        while (k < 64) {
            if (c[k] != (0 as uint8)) {
                return 4;
            }
            k = k + 1;
        }

        // 4. User realloc via stdlib
        c[0] = 99 as uint8;
        uint8* r = stdlib.realloc(c, 128 as uint64, 64 as uint64, &stats, &pheap, 100 as uint32);
        if (r == null || r[0] != (99 as uint8)) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
