import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSPCIBus(unittest.TestCase):
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

    def test_pci_make_address_calculation(self):
        code = """
        import "os/drivers/pci.kl" as pci;

        // Bus 0, Slot 3, Func 0, Offset 0x10 (BAR0)
        // Expected: 0x80000000 | (0 << 16) | (3 << 11) | (0 << 8) | 0x10
        // (3 << 11) = 0x1800
        // 0x80000000 | 0x1800 | 0x10 = 0x80001810
        uint32 addr1 = pci.pci_make_address(0 as uint8, 3 as uint8, 0 as uint8, 0x10 as uint8);
        if (addr1 != (0x80001810 as uint32)) {
            return 1;
        }

        // Bus 2, Slot 15, Func 1, Offset 0x05 (should align to 0x04)
        // (2 << 16) = 0x20000
        // (15 << 11) = 0x7800
        // (1 << 8) = 0x100
        // offset 0x05 & 0xFC = 0x04
        // Expected: 0x80027904
        uint32 addr2 = pci.pci_make_address(2 as uint8, 15 as uint8, 1 as uint8, 0x05 as uint8);
        if (addr2 != (0x80027904 as uint32)) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pci_bar_io_decoding_and_sizing(self):
        code = """
        import "os/drivers/pci.kl" as pci;

        pci.PCIBAR bar;
        // Raw value: 0xC001 (Port I/O base 0xC000, bit 0 = 1)
        // Mask value: 0xFFFFFF00 (Size = 256 bytes)
        pci.pci_decode_bar(&bar, 0xC001 as uint32, 0xFFFFFF00 as uint32);

        if (!bar.is_io) {
            return 1;
        }
        if (bar.base_address != (0xC000 as uint64)) {
            return 2;
        }
        if (bar.size != (256 as uint64)) {
            return 3;
        }
        if (bar.is_64bit) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pci_bar_mmio_decoding_and_sizing(self):
        code = """
        import "os/drivers/pci.kl" as pci;

        pci.PCIBAR bar;
        // Raw MMIO: 0xE0000008 (Base 0xE0000000, prefetchable bit 3 = 1, bit 0 = 0)
        // Mask: 0xFFF00000 (Size = 1 MB: 0x100000)
        pci.pci_decode_bar(&bar, 0xE0000008 as uint32, 0xFFF00000 as uint32);

        if (bar.is_io) {
            return 1;
        }
        if (!bar.is_prefetchable) {
            return 2;
        }
        if (bar.base_address != (0xE0000000 as uint64)) {
            return 3;
        }
        if (bar.size != (1048576 as uint64)) { // 1 MB
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pci_device_registration_and_lookup(self):
        code = """
        import "os/drivers/pci.kl" as pci;

        pci.PCIBusManager mgr;
        pci.pci_bus_init(&mgr);

        if (mgr.device_count != (0 as uint32)) {
            return 1;
        }

        // Create RTL8139 device
        pci.PCIDevice rtl;
        rtl.bus = 0 as uint8;
        rtl.slot = 3 as uint8;
        rtl.func = 0 as uint8;
        rtl.vendor_id = 0x10EC as uint16;
        rtl.device_id = 0x8139 as uint16;
        rtl.class_code = pci.PCI_CLASS_NETWORK;
        rtl.subclass = 0 as uint8;
        rtl.is_valid = true;

        // Create Intel E1000 device
        pci.PCIDevice e1000;
        e1000.bus = 0 as uint8;
        e1000.slot = 4 as uint8;
        e1000.func = 0 as uint8;
        e1000.vendor_id = 0x8086 as uint16;
        e1000.device_id = 0x100E as uint16;
        e1000.class_code = pci.PCI_CLASS_NETWORK;
        e1000.subclass = 0 as uint8;
        e1000.is_valid = true;

        pci.pci_bus_add_device(&mgr, &rtl);
        pci.pci_bus_add_device(&mgr, &e1000);

        if (mgr.device_count != (2 as uint32)) {
            return 2;
        }

        pci.PCIDevice* found1 = pci.pci_find_device(&mgr, 0x10EC as uint16, 0x8139 as uint16);
        if (found1 == null || found1->slot != (3 as uint8)) {
            return 3;
        }

        pci.PCIDevice* found2 = pci.pci_find_device(&mgr, 0x8086 as uint16, 0x100E as uint16);
        if (found2 == null || found2->slot != (4 as uint8)) {
            return 4;
        }

        pci.PCIDevice* not_found = pci.pci_find_device(&mgr, 0x1234 as uint16, 0x5678 as uint16);
        if (not_found != null) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_pci_driver_matching(self):
        code = """
        import "os/drivers/pci.kl" as pci;

        pci.PCIDevice dev;
        dev.is_valid = true;

        // 1. RTL8139
        dev.vendor_id = 0x10EC as uint16;
        dev.device_id = 0x8139 as uint16;
        dev.class_code = pci.PCI_CLASS_NETWORK;
        if (pci.pci_match_driver(&dev) != pci.DRIVER_RTL8139) {
            return 1;
        }

        // 2. Intel E1000
        dev.vendor_id = 0x8086 as uint16;
        dev.device_id = 0x100E as uint16;
        dev.class_code = pci.PCI_CLASS_NETWORK;
        if (pci.pci_match_driver(&dev) != pci.DRIVER_E1000) {
            return 2;
        }

        // 3. PIIX3 IDE
        dev.vendor_id = 0x8086 as uint16;
        dev.device_id = 0x7010 as uint16;
        dev.class_code = pci.PCI_CLASS_MASS_STORAGE;
        if (pci.pci_match_driver(&dev) != pci.DRIVER_ATA_IDE) {
            return 3;
        }

        // 4. Bochs VGA
        dev.vendor_id = 0x1234 as uint16;
        dev.device_id = 0x1111 as uint16;
        dev.class_code = pci.PCI_CLASS_DISPLAY;
        if (pci.pci_match_driver(&dev) != pci.DRIVER_VGA_BGA) {
            return 4;
        }

        // 5. AC97 Audio
        dev.vendor_id = 0x8086 as uint16;
        dev.device_id = 0x2415 as uint16;
        dev.class_code = pci.PCI_CLASS_MULTIMEDIA;
        if (pci.pci_match_driver(&dev) != pci.DRIVER_AC97) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
