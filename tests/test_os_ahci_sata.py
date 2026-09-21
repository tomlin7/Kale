import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSAHCISATA(unittest.TestCase):
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

    def test_ahci_port_signature_and_detection(self):
        code = r"""
        import "os/drivers/ahci.kl" as ahci;

        // Valid SATA status: DET=3 (present), IPM=1 (active) -> ssts = 0x113
        uint32 ssts_active = 0x00000113 as uint32;

        // 1. SATA Drive
        int dev_sata = ahci.ahci_check_port_type(ssts_active, ahci.SATA_SIG_ATA);
        if (dev_sata != ahci.AHCI_DEV_SATA) return 1;

        // 2. ATAPI CD/DVD Drive
        int dev_atapi = ahci.ahci_check_port_type(ssts_active, ahci.SATA_SIG_ATAPI);
        if (dev_atapi != ahci.AHCI_DEV_SATAPI) return 2;

        // 3. Enclosure SEMB
        int dev_semb = ahci.ahci_check_port_type(ssts_active, ahci.SATA_SIG_SEMB);
        if (dev_semb != ahci.AHCI_DEV_SEMB) return 3;

        // 4. Port Multiplier
        int dev_pm = ahci.ahci_check_port_type(ssts_active, ahci.SATA_SIG_PM);
        if (dev_pm != ahci.AHCI_DEV_PM) return 4;

        // 5. Inactive / No device
        uint32 ssts_empty = 0x00000000 as uint32;
        int dev_none = ahci.ahci_check_port_type(ssts_empty, ahci.SATA_SIG_ATA);
        if (dev_none != ahci.AHCI_DEV_NULL) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ahci_port_start_and_stop(self):
        code = r"""
        import "os/drivers/ahci.kl" as ahci;

        ahci.HBAPort port;
        port.cmd = 0 as uint32;

        // Start port
        ahci.ahci_port_start(&port);
        // Both FRE (0x10) and ST (0x01) should be set
        if ((port.cmd & ahci.HBA_CMD_FRE) == (0 as uint32)) return 1;
        if ((port.cmd & ahci.HBA_CMD_ST) == (0 as uint32)) return 2;

        // Stop port
        ahci.ahci_port_stop(&port);
        // Both FRE and ST should be cleared
        if ((port.cmd & ahci.HBA_CMD_FRE) != (0 as uint32)) return 3;
        if ((port.cmd & ahci.HBA_CMD_ST) != (0 as uint32)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ahci_command_slot_allocation(self):
        code = r"""
        import "os/drivers/ahci.kl" as ahci;

        ahci.HBAPort port;
        port.ci = 0 as uint32;
        port.sact = 0 as uint32;

        // Slot 0 should be free initially
        int slot0 = ahci.ahci_find_cmdslot(&port);
        if (slot0 != 0) return 1;

        // Mark slots 0, 1, 2 as busy in CI bitmask (0b0111 = 0x7)
        port.ci = 0x00000007 as uint32;
        int slot3 = ahci.ahci_find_cmdslot(&port);
        if (slot3 != 3) return 2;

        // Mark slot 3 as busy in SACT bitmask (1 << 3 = 8)
        port.sact = 0x00000008 as uint32;
        int slot4 = ahci.ahci_find_cmdslot(&port);
        if (slot4 != 4) return 3;

        // All 32 slots busy
        port.ci = 0xFFFFFFFF as uint32;
        int full = ahci.ahci_find_cmdslot(&port);
        if (full != -1) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ahci_h2d_fis_construction(self):
        code = r"""
        import "os/drivers/ahci.kl" as ahci;

        ahci.FISRegH2D fis;
        uint64 lba = 0x123456789ABC as uint64;
        uint16 count = 64 as uint16;

        ahci.ahci_build_h2d_fis(&fis, ahci.ATA_CMD_READ_DMA_EXT, lba, count);

        if (fis.fis_type != ahci.FIS_TYPE_REG_H2D) return 1;
        if (fis.pmport_c != (0x80 as uint8)) return 2; // Bit 7: Command flag
        if (fis.command != ahci.ATA_CMD_READ_DMA_EXT) return 3;
        if (fis.device != (0x40 as uint8)) return 4; // LBA mode bit

        // Validate 48-bit LBA split
        if (fis.lba0 != (0xBC as uint8)) return 5;
        if (fis.lba1 != (0x9A as uint8)) return 6;
        if (fis.lba2 != (0x78 as uint8)) return 7;
        if (fis.lba3 != (0x56 as uint8)) return 8;
        if (fis.lba4 != (0x34 as uint8)) return 9;
        if (fis.lba5 != (0x12 as uint8)) return 10;

        if (fis.count != (64 as uint16)) return 11;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ahci_prdt_and_cmd_header_setup(self):
        code = r"""
        import "os/drivers/ahci.kl" as ahci;

        // 1. Setup PRDT entry for 4096 bytes with Interrupt-on-Completion (IOC)
        ahci.HBAPRDTEntry prdt;
        uint64 dba = 0x0000000020000000 as uint64;
        ahci.ahci_setup_prdt(&prdt, dba, 4096 as uint32, true);

        if (prdt.dba != dba) return 1;
        // 4096 bytes encoded as (4096 - 1) = 4095 (0xFFF)
        // With IOC bit (0x80000000)
        uint32 expected_dbc = 0x80000FFF as uint32;
        if (prdt.dbc != expected_dbc) return 2;

        // 2. Setup Command Header for Write operation
        ahci.HBACmdHeader hdr;
        uint64 ctba = 0x0000000030000000 as uint64;
        ahci.ahci_setup_cmd_header(&hdr, 1 as uint16, true, ctba);

        if (hdr.prdtl != (1 as uint16)) return 3;
        if (hdr.ctba != ctba) return 4;
        // CFL = 5, Write bit = 0x40 -> flags = 0x0045
        if (hdr.flags != (0x0045 as uint16)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ahci_controller_init(self):
        code = r"""
        import "os/drivers/ahci.kl" as ahci;

        ahci.HBAController ctrl;
        uint64 mmio = 0xFEB00000 as uint64;
        // Ports implemented bitmask: Port 0 and Port 3 implemented (0b1001 = 0x09)
        uint32 pi = 0x00000009 as uint32;
        uint32 cap = 0xC734FF00 as uint32;

        ahci.ahci_init_controller(&ctrl, mmio, pi, cap);

        if (ctrl.base_addr != mmio) return 1;
        if (ctrl.pi != pi) return 2;
        if (ctrl.port_count != 2) return 3;
        if (ctrl.vs != (0x00010300 as uint32)) return 4; // AHCI 1.3
        if ((ctrl.ghc & (0x80000000 as uint32)) == (0 as uint32)) return 5; // GHC.AE

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
