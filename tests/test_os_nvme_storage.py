import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSNVMeStorage(unittest.TestCase):
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

    def test_nvme_controller_init(self):
        code = r"""
        import "os/drivers/nvme.kl" as nvme;

        nvme.NVMEController ctrl;
        uint64 base = 0xFE000000 as uint64;
        uint32 cap_lo = 0x000003FF as uint32; // MQES = 1023 -> 1024 entries
        uint32 cap_hi = 0x00000000 as uint32; // DSTRD = 0
        uint32 vs = 0x00010400 as uint32;     // NVMe 1.4

        nvme.nvme_init_controller(&ctrl, base, cap_lo, cap_hi, vs);

        if (ctrl.base_addr != base) return 1;
        if (ctrl.max_queue_entries != 1024) return 2;
        if (ctrl.dstrd != 0) return 3;
        if (ctrl.vs != vs) return 4;
        if (!ctrl.is_ready) return 5;

        // Check CC flags
        if ((ctrl.cc & nvme.NVME_CC_EN) == (0 as uint32)) return 6;
        if ((ctrl.cc & nvme.NVME_CC_IOSQES_64) == (0 as uint32)) return 7;
        if ((ctrl.cc & nvme.NVME_CC_IOCQES_16) == (0 as uint32)) return 8;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_nvme_doorbell_address_calculation(self):
        code = r"""
        import "os/drivers/nvme.kl" as nvme;

        nvme.NVMEController ctrl;
        ctrl.base_addr = 0xFE000000 as uint64;
        ctrl.dstrd = 0; // Stride = 4 bytes

        // QID 0 (Admin Queue)
        uint64 sq0_dbl = nvme.nvme_calc_sq_doorbell(&ctrl, 0);
        uint64 cq0_dbl = nvme.nvme_calc_cq_doorbell(&ctrl, 0);
        // Base + 0x1000 + 0 = 0xFE001000
        if (sq0_dbl != (0xFE001000 as uint64)) return 1;
        // Base + 0x1000 + 4 = 0xFE001004
        if (cq0_dbl != (0xFE001004 as uint64)) return 2;

        // QID 1 (I/O Queue)
        uint64 sq1_dbl = nvme.nvme_calc_sq_doorbell(&ctrl, 1);
        uint64 cq1_dbl = nvme.nvme_calc_cq_doorbell(&ctrl, 1);
        // Base + 0x1000 + 8 = 0xFE001008
        if (sq1_dbl != (0xFE001008 as uint64)) return 3;
        // Base + 0x1000 + 12 = 0xFE00100C
        if (cq1_dbl != (0xFE00100C as uint64)) return 4;

        // Test with DSTRD = 1 (Stride = 8 bytes)
        ctrl.dstrd = 1;
        uint64 sq1_dbl_strd1 = nvme.nvme_calc_sq_doorbell(&ctrl, 1);
        // Base + 0x1000 + (2 * 1 * 8) = Base + 0x1010
        if (sq1_dbl_strd1 != (0xFE001010 as uint64)) return 5;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_nvme_build_io_read_command(self):
        code = r"""
        import "os/drivers/nvme.kl" as nvme;

        nvme.NVMESQE sqe;
        uint64 lba = 0x0000000180000000 as uint64; // 64-bit LBA
        uint16 count = 8 as uint16;                // 8 sectors
        uint64 prp1 = 0x0000000030000000 as uint64;

        nvme.nvme_build_io_cmd(&sqe, nvme.NVME_CMD_READ, 1 as uint16, 1 as uint32, lba, count, prp1);

        if (sqe.opcode != nvme.NVME_CMD_READ) return 1;
        if (sqe.cid != (1 as uint16)) return 2;
        if (sqe.nsid != (1 as uint32)) return 3;
        if (sqe.prp1 != prp1) return 4;

        // Check 64-bit LBA split
        if (sqe.cdw10 != (0x80000000 as uint32)) return 5;
        if (sqe.cdw11 != (0x00000001 as uint32)) return 6;

        // Check 0-based block count: 8 blocks -> num_blocks = 7
        if (sqe.num_blocks != (7 as uint16)) return 7;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_nvme_build_io_write_command(self):
        code = r"""
        import "os/drivers/nvme.kl" as nvme;

        nvme.NVMESQE sqe;
        uint64 lba = 100 as uint64;
        uint16 count = 1 as uint16; // 1 sector -> num_blocks = 0
        uint64 prp1 = 0x0000000040000000 as uint64;

        nvme.nvme_build_io_cmd(&sqe, nvme.NVME_CMD_WRITE, 2 as uint16, 1 as uint32, lba, count, prp1);

        if (sqe.opcode != nvme.NVME_CMD_WRITE) return 1;
        if (sqe.cdw10 != (100 as uint32)) return 2;
        if (sqe.cdw11 != (0 as uint32)) return 3;
        if (sqe.num_blocks != (0 as uint16)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_nvme_cqe_phase_and_status(self):
        code = r"""
        import "os/drivers/nvme.kl" as nvme;

        nvme.NVMECQE cqe;

        // Status 0x0001: Phase bit P = 1, Status Code SC = 0 (Success)
        cqe.status = 0x0001 as uint16;
        if (!nvme.nvme_cqe_is_complete(&cqe, true)) return 1;
        if (nvme.nvme_cqe_is_complete(&cqe, false)) return 2;
        if (nvme.nvme_cqe_status_code(&cqe) != (0 as uint16)) return 3;

        // Status 0x0005: Phase bit P = 1, Status Code = (5 >> 1) = 2
        cqe.status = 0x0005 as uint16;
        if (nvme.nvme_cqe_status_code(&cqe) != (2 as uint16)) return 4;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
