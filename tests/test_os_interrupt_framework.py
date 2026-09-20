import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSInterruptFramework(unittest.TestCase):
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

    def test_idt_table_initialization_and_gate_encoding(self):
        code = """
        import "os/kernel/idt.kl" as idt;

        idt.IDTTable table;
        idt.idt_init(&table);

        // IDT pointer limit: 256 * 16 - 1 = 4095
        if (table.pointer.limit != 4095 as uint16) {
            return 1;
        }

        // Test gate encoding with a 64-bit kernel handler address
        uint64 isr32_addr = 0xFFFFFFFF80005678 as uint64;
        idt.idt_set_gate(&table, 32, isr32_addr, 0x08 as uint16, idt.IDT_GATE_INTERRUPT);

        if (!idt.idt_is_entry_present(&table, 32)) {
            return 2;
        }

        idt.IDTEntry entry = idt.idt_get_gate(&table, 32);
        if (entry.selector != 0x08 as uint16) {
            return 3;
        }
        if (entry.type_attr != idt.IDT_GATE_INTERRUPT) {
            return 4;
        }

        uint64 reconstructed_addr = idt.idt_get_handler_address(&table, 32);
        if (reconstructed_addr != isr32_addr) {
            return 5;
        }

        // Test user-space syscall gate (0x80)
        uint64 syscall_addr = 0xFFFFFFFF80009999 as uint64;
        idt.idt_set_gate(&table, 128, syscall_addr, 0x08 as uint16, idt.IDT_GATE_USER);
        if (table.entries[128].type_attr != 0xEE as uint8) {
            return 6;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_interrupt_state_and_nesting_tracker(self):
        code = """
        import "os/kernel/isr.kl" as isr;

        isr.InterruptState state;
        isr.isr_state_init(&state);

        if (state.depth != 0 || state.total_interrupts != 0 as uint64) {
            return 1;
        }

        // Enter timer IRQ (vector 32)
        isr.interrupt_enter(&state, 32 as uint8);
        if (state.depth != 1 || state.current_vector != 32 as uint8) {
            return 2;
        }
        if (isr.interrupt_is_nested(&state)) {
            return 3; // Depth 1 is not nested
        }

        // Nested interrupt: Page fault (vector 14) during timer IRQ
        isr.interrupt_enter(&state, 14 as uint8);
        if (state.depth != 2 || state.current_vector != 14 as uint8) {
            return 4;
        }
        if (!isr.interrupt_is_nested(&state)) {
            return 5; // Depth 2 is nested
        }

        // Exit page fault
        isr.interrupt_exit(&state);
        if (state.depth != 1) {
            return 6;
        }

        // Exit timer IRQ
        isr.interrupt_exit(&state);
        if (state.depth != 0 || state.current_vector != 0 as uint8) {
            return 7;
        }

        // Check statistics: 1 exception (14), 1 irq (32), 0 syscalls, 2 total
        if (state.total_exceptions != 1 as uint64 || state.total_irqs != 1 as uint64 || state.total_interrupts != 2 as uint64) {
            return 8;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_syscall_dispatch_interface(self):
        code = """
        import "os/kernel/idt.kl" as idt;
        import "os/kernel/isr.kl" as isr;

        isr.InterruptState state;
        isr.isr_state_init(&state);

        idt.InterruptFrame frame;
        frame.rax = 39 as uint64; // SYS_GETPID
        frame.interrupt_number = 128 as uint64;

        isr.isr_dispatch_interrupt(&frame, &state, 1042 as uint32);

        // Result returned in frame.rax
        if (frame.rax != 1042 as uint64) {
            return 1;
        }
        if (state.total_syscalls != 1 as uint64) {
            return 2;
        }

        // SYS_WRITE
        frame.rax = 1 as uint64;
        frame.rdi = 1 as uint64; // stdout
        frame.rsi = 0x400000 as uint64; // buf
        frame.rdx = 25 as uint64; // count
        isr.isr_dispatch_interrupt(&frame, &state, 1042 as uint32);
        if (frame.rax != 25 as uint64) {
            return 3;
        }

        // SYS_EXIT
        frame.rax = 60 as uint64;
        frame.rdi = 0 as uint64; // status
        isr.isr_dispatch_interrupt(&frame, &state, 1042 as uint32);
        if (frame.rax != 0 as uint64) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_keyboard_interrupt_buffer(self):
        code = """
        import "os/kernel/keyboard.kl" as kbd;

        kbd.KeyboardBuffer kb;
        kbd.keyboard_buffer_init(&kb);

        if (kb.count != 0) {
            return 1;
        }

        // Scancode 30 = 'a'
        bool ok = kbd.keyboard_handle_irq(&kb, 30 as uint8);
        if (!ok || kb.count != 1) {
            return 2;
        }

        // Key release 30 | 0x80 (break code) should be ignored
        bool ignored = kbd.keyboard_handle_irq(&kb, 158 as uint8);
        if (ignored || kb.count != 1) {
            return 3;
        }

        // Left Shift press (scancode 42)
        kbd.keyboard_handle_irq(&kb, 42 as uint8);
        if (!kb.shift_pressed) {
            return 4;
        }

        // Scancode 48 with shift = 'B'
        kbd.keyboard_handle_irq(&kb, 48 as uint8);
        if (kb.count != 2) {
            return 5;
        }

        // Left Shift release (scancode 42 | 0x80 = 170)
        kbd.keyboard_handle_irq(&kb, 170 as uint8);
        if (kb.shift_pressed) {
            return 6;
        }

        // Pop characters
        uint8 ch1 = 0 as uint8;
        uint8 ch2 = 0 as uint8;
        if (!kbd.keyboard_buffer_pop(&kb, &ch1) || ch1 != 97 as uint8) { // 'a' == 97
            return 7;
        }
        if (!kbd.keyboard_buffer_pop(&kb, &ch2) || ch2 != 66 as uint8) { // 'B' == 66
            return 8;
        }
        if (kb.count != 0) {
            return 9;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_timer_irq_and_quantum_preemption(self):
        code = """
        import "os/kernel/timer.kl" as timer;

        timer.TimerState t;
        timer.timer_state_init(&t, 1000 as uint64, 10 as uint32); // 1000Hz, quantum = 10 ticks (10ms)

        if (t.ticks != 0 as uint64 || t.milliseconds != 0 as uint64) {
            return 1;
        }

        // Run 9 ticks: no preemption yet
        int i = 0;
        while (i < 9) {
            bool preempt = timer.timer_handle_irq(&t);
            if (preempt) return 2;
            i = i + 1;
        }

        if (t.ticks != 9 as uint64 || t.milliseconds != 9 as uint64) {
            return 3;
        }

        // 10th tick: quantum expires -> preemption triggered
        bool preempt = timer.timer_handle_irq(&t);
        if (!preempt || t.ticks != 10 as uint64 || t.milliseconds != 10 as uint64) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
