import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestSchedulerAndPIT(unittest.TestCase):
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

    def test_pit_driver_configuration_and_ticks(self):
        code = """
        import "os/kernel/pit.kl" as pit;

        pit.PITDriver p = pit.pit_init(100 as uint32);
        if (p.frequency != 100 || p.divisor != 11931 || p.ticks != 0) {
            return 1;
        }

        // 1000 Hz check
        pit.pit_set_frequency(&p, 1000 as uint32);
        if (p.frequency != 1000 || p.divisor != 1193) {
            return 2;
        }

        // Tick advancement
        pit.pit_on_tick(&p);
        pit.pit_on_tick(&p);
        pit.pit_on_tick(&p);
        if (p.ticks != 3) {
            return 3;
        }

        // Ticks to ms (at 1000 Hz, 50 ticks = 50 ms)
        uint64 ms = pit.pit_ticks_to_ms(&p, 50 as uint64);
        if (ms != 50) {
            return 4;
        }

        // ms to ticks
        uint64 t = pit.pit_ms_to_ticks(&p, 100 as uint64);
        if (t != 100) {
            return 5;
        }

        // Quantum expiration check
        p.ticks = 150 as uint64;
        bool exp1 = pit.pit_is_quantum_expired(&p, 100 as uint64, 40 as uint32); // 50ms elapsed >= 40ms
        bool exp2 = pit.pit_is_quantum_expired(&p, 100 as uint64, 60 as uint32); // 50ms elapsed < 60ms
        if (!exp1 || exp2) {
            return 6;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_scheduler_round_robin_execution(self):
        code = """
        import "os/kernel/sched.kl" as sched;

        sched.sched_reset_pid_counter(1);
        sched.Scheduler s;
        sched.scheduler_init(&s, 20 as uint32);

        sched.ProcessControlBlock p1;
        sched.ProcessControlBlock p2;
        sched.ProcessControlBlock p3;
        sched.CPUContext c1;
        sched.CPUContext c2;
        sched.CPUContext c3;

        sched.sched_create_process(&s, &p1, &c1, 0x1000 as uint64, 0x100000 as uint64, 0 as uint64, 0x200000 as uint64, false, 5 as uint8, 20 as uint32);
        sched.sched_create_process(&s, &p2, &c2, 0x2000 as uint64, 0x110000 as uint64, 0 as uint64, 0x200000 as uint64, false, 5 as uint8, 20 as uint32);
        sched.sched_create_process(&s, &p3, &c3, 0x3000 as uint64, 0x120000 as uint64, 0 as uint64, 0x200000 as uint64, false, 5 as uint8, 20 as uint32);

        if (s.ready_count != 3 || s.total_processes != 3) {
            return 1;
        }

        // Initial schedule should pick P1
        sched.ProcessControlBlock* cur = sched.sched_schedule(&s);
        if (cur == null || cur->id != 1 || !sched.pcb_is_running(cur)) {
            return 2;
        }

        // Partial time slice: 10ms -> not expired
        bool expired = sched.sched_tick(&s, 10 as uint32);
        if (expired || cur->time_used != 10) {
            return 3;
        }

        // Finish time slice: +10ms -> expired
        expired = sched.sched_tick(&s, 10 as uint32);
        if (!expired || cur->time_used != 20) {
            return 4;
        }

        // Schedule should rotate P1 to back and pick P2
        cur = sched.sched_schedule(&s);
        if (cur == null || cur->id != 2 || !sched.pcb_is_running(cur)) {
            return 5;
        }
        if (!sched.pcb_is_ready(&p1)) {
            return 6;
        }

        // P2 finishes time slice -> switch to P3
        sched.sched_tick(&s, 20 as uint32);
        cur = sched.sched_schedule(&s);
        if (cur == null || cur->id != 3) {
            return 7;
        }

        // P3 finishes time slice -> rotate back to P1
        sched.sched_tick(&s, 20 as uint32);
        cur = sched.sched_schedule(&s);
        if (cur == null || cur->id != 1) {
            return 8;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_scheduler_yield_and_termination(self):
        code = """
        import "os/kernel/sched.kl" as sched;

        sched.sched_reset_pid_counter(10);
        sched.Scheduler s;
        sched.scheduler_init(&s, 15 as uint32);

        sched.ProcessControlBlock p1;
        sched.ProcessControlBlock p2;
        sched.ProcessControlBlock idle;
        sched.CPUContext c1;
        sched.CPUContext c2;
        sched.CPUContext c_idle;

        sched.sched_create_process(&s, &p1, &c1, 0x1000 as uint64, 0x100000 as uint64, 0 as uint64, 0x200000 as uint64, false, 1 as uint8, 15 as uint32);
        sched.sched_create_process(&s, &p2, &c2, 0x2000 as uint64, 0x110000 as uint64, 0 as uint64, 0x200000 as uint64, false, 1 as uint8, 15 as uint32);
        sched.sched_create_idle_process(&s, &idle, &c_idle, 0xFFFFFFFF80000000 as uint64, 0x120000 as uint64, 0x200000 as uint64);

        sched.ProcessControlBlock* cur = sched.sched_schedule(&s);
        if (cur == null || cur->id != 10) {
            return 1;
        }

        // P1 yields voluntarily
        cur = sched.sched_yield(&s);
        if (cur == null || cur->id != 11) {
            return 2;
        }

        // Terminate P2 with exit code 0
        sched.sched_terminate_process(&s, &p2, 0);
        if (!sched.pcb_is_terminated(&p2) || p2.exit_code != 0) {
            return 3;
        }
        if (s.ready_count != 1 || s.total_processes != 1) {
            return 4;
        }

        // Now current process should be P1 again
        cur = sched.sched_schedule(&s);
        if (cur == null || cur->id != 10) {
            return 5;
        }

        // Terminate P1 as well
        sched.sched_terminate_process(&s, &p1, 123);
        if (s.ready_count != 0 || s.total_processes != 0) {
            return 6;
        }

        // When ready queue is empty, scheduler falls back to idle process
        cur = sched.sched_schedule(&s);
        if (cur == null || cur->id != 0) {
            return 7;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
