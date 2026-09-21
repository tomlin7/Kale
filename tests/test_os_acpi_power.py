import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSACPIPower(unittest.TestCase):
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

    def test_acpi_checksum_validation(self):
        code = """
        import "os/kernel/acpi.kl" as acpi;

        uint8[4] buffer;
        buffer[0] = 0x10 as uint8;
        buffer[1] = 0x20 as uint8;
        buffer[2] = 0x30 as uint8;
        // 0x10 + 0x20 + 0x30 = 0x60 -> checksum byte is 0x100 - 0x60 = 0xA0
        buffer[3] = 0xA0 as uint8;

        if (!acpi.acpi_validate_checksum(&buffer[0], 4)) {
            return 1;
        }

        // Corrupt one byte
        buffer[3] = 0xA1 as uint8;
        if (acpi.acpi_validate_checksum(&buffer[0], 4)) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_acpi_rsdp_parsing(self):
        code = """
        import "os/kernel/acpi.kl" as acpi;

        // Construct 20-byte RSDP structure
        // Signature: "RSD PTR "
        uint8[20] rsdp_bytes;
        rsdp_bytes[0] = 0x52 as uint8; // 'R'
        rsdp_bytes[1] = 0x53 as uint8; // 'S'
        rsdp_bytes[2] = 0x44 as uint8; // 'D'
        rsdp_bytes[3] = 0x20 as uint8; // ' '
        rsdp_bytes[4] = 0x50 as uint8; // 'P'
        rsdp_bytes[5] = 0x54 as uint8; // 'T'
        rsdp_bytes[6] = 0x52 as uint8; // 'R'
        rsdp_bytes[7] = 0x20 as uint8; // ' '

        // OEM ID: "BOCHS "
        rsdp_bytes[9]  = 0x42 as uint8; // 'B'
        rsdp_bytes[10] = 0x4F as uint8; // 'O'
        rsdp_bytes[11] = 0x43 as uint8; // 'C'
        rsdp_bytes[12] = 0x48 as uint8; // 'H'
        rsdp_bytes[13] = 0x53 as uint8; // 'S'
        rsdp_bytes[14] = 0x20 as uint8; // ' '

        // Revision 0 (ACPI 1.0)
        rsdp_bytes[15] = 0 as uint8;

        // RSDT Address: 0x07FE1000 (Little Endian)
        rsdp_bytes[16] = 0x00 as uint8;
        rsdp_bytes[17] = 0x10 as uint8;
        rsdp_bytes[18] = 0xFE as uint8;
        rsdp_bytes[19] = 0x07 as uint8;

        // Calculate checksum for byte 8
        int sum = 0;
        int i = 0;
        while (i < 20) {
            if (i != 8) {
                sum = sum + (rsdp_bytes[i] as int);
            }
            i = i + 1;
        }
        uint8 chk = ((256 - (sum & 0xFF)) & 0xFF) as uint8;
        rsdp_bytes[8] = chk;

        acpi.RSDPDescriptor rsdp;
        bool ok = acpi.acpi_rsdp_init(&rsdp, &rsdp_bytes[0]);
        if (!ok || !rsdp.is_valid) {
            return 1;
        }

        if (rsdp.rsdt_address != (0x07FE1000 as uint32)) {
            return 2;
        }
        if (rsdp.revision != (0 as uint8)) {
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_acpi_sleep_command_and_poweroff_plan(self):
        code = """
        import "os/kernel/acpi.kl" as acpi;

        // S5 sleep type = 5 -> (5 << 10) | 0x2000 = 0x1400 | 0x2000 = 0x3400
        uint16 cmd = acpi.acpi_make_sleep_command(5 as uint16);
        if (cmd != (0x3400 as uint16)) {
            return 1;
        }

        // FADT with PM1a block at port 0x0604
        acpi.FADTInfo fadt;
        acpi.acpi_fadt_init(&fadt, 0xB2 as uint32, 0xA0 as uint8, 0xA1 as uint8, 0x0604 as uint32, 0 as uint32);

        uint16 port = 0 as uint16;
        uint16 val = 0 as uint16;
        bool ok = acpi.acpi_poweroff_plan(&fadt, &port, &val);

        if (!ok || port != (0x0604 as uint16) || val != (0x3400 as uint16)) {
            return 2;
        }

        // Test fallback poweroff when FADT is null
        uint16 fallback_port = 0 as uint16;
        uint16 fallback_val = 0 as uint16;
        ok = acpi.acpi_poweroff_plan(null, &fallback_port, &fallback_val);
        if (!ok || fallback_port != (0x0604 as uint16) || fallback_val != (0x2000 as uint16)) {
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_acpi_reboot_plan(self):
        code = """
        import "os/kernel/acpi.kl" as acpi;

        uint16 port = 0 as uint16;
        uint8 val = 0 as uint8;
        acpi.acpi_reboot_plan(&port, &val);

        // Standard 8042 reset: port 0x64, val 0xFE
        if (port != (0x0064 as uint16) || val != (0xFE as uint8)) {
            return 1;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_acpi_madt_cpu_topology(self):
        code = """
        import "os/kernel/acpi.kl" as acpi;

        acpi.MADTInfo madt;
        acpi.acpi_madt_init(&madt, 0xFEE00000 as uint32);

        if (!madt.is_valid || madt.lapic_addr != (0xFEE00000 as uint32) || madt.cpu_count != (0 as uint32)) {
            return 1;
        }

        // Add 4 virtual CPU cores (BSP + 3 APs)
        bool ok1 = acpi.acpi_madt_add_cpu(&madt, 0 as uint8, true);
        bool ok2 = acpi.acpi_madt_add_cpu(&madt, 1 as uint8, true);
        bool ok3 = acpi.acpi_madt_add_cpu(&madt, 2 as uint8, true);
        bool ok4 = acpi.acpi_madt_add_cpu(&madt, 3 as uint8, true);

        if (!ok1 || !ok2 || !ok3 || !ok4 || madt.cpu_count != (4 as uint32)) {
            return 2;
        }

        if (madt.cpu_apic_ids[0] != (0 as uint8) || !madt.cpu_enabled[0]) {
            return 3;
        }
        if (madt.cpu_apic_ids[3] != (3 as uint8) || !madt.cpu_enabled[3]) {
            return 4;
        }

        // Configure I/O APIC at 0xFEC00000, ID 2
        acpi.acpi_madt_set_ioapic(&madt, 2 as uint8, 0xFEC00000 as uint32);
        if (madt.ioapic_id != (2 as uint8) || madt.ioapic_addr != (0xFEC00000 as uint32)) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
