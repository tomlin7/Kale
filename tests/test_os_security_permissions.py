import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSSecurityPermissions(unittest.TestCase):
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

    def test_root_superuser_bypass_and_capabilities(self):
        code = """
        import "os/kernel/security.kl" as sec;

        sec.Credentials root_creds;
        sec.creds_init_root(&root_creds);

        if (root_creds.uid != sec.UID_ROOT || root_creds.euid != sec.UID_ROOT) {
            return 1;
        }
        if (!sec.creds_has_capability(&root_creds, sec.CAP_SYS_ADMIN)) {
            return 2;
        }

        // File mode 0600 (User Read+Write only, owned by UID 1000)
        uint32 mode_rw = sec.S_IRUSR | sec.S_IWUSR;

        // Root can read and write even though not owner
        bool can_read = sec.security_check_access(&root_creds, 1000 as uint32, 100 as uint32, mode_rw, sec.ACCESS_R_OK);
        bool can_write = sec.security_check_access(&root_creds, 1000 as uint32, 100 as uint32, mode_rw, sec.ACCESS_W_OK);

        if (!can_read || !can_write) {
            return 3;
        }

        // Root cannot execute a file with NO execute bits set anywhere
        bool can_exec_no = sec.security_check_access(&root_creds, 1000 as uint32, 100 as uint32, mode_rw, sec.ACCESS_X_OK);
        if (can_exec_no) {
            return 4;
        }

        // Root can execute if at least one execute bit is set (e.g. S_IXUSR)
        uint32 mode_rx = sec.S_IRUSR | sec.S_IXUSR;
        bool can_exec_yes = sec.security_check_access(&root_creds, 1000 as uint32, 100 as uint32, mode_rx, sec.ACCESS_X_OK);
        if (!can_exec_yes) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_owner_permissions_read_write_execute(self):
        code = """
        import "os/kernel/security.kl" as sec;

        sec.Credentials user;
        sec.creds_init_user(&user, 1000 as uint32, 100 as uint32);

        // Mode 0700: Owner Read, Write, Execute
        uint32 mode_700 = sec.S_IRUSR | sec.S_IWUSR | sec.S_IXUSR;

        // Owner access (matches UID 1000)
        bool ok_r = sec.security_check_access(&user, 1000 as uint32, 100 as uint32, mode_700, sec.ACCESS_R_OK);
        bool ok_w = sec.security_check_access(&user, 1000 as uint32, 100 as uint32, mode_700, sec.ACCESS_W_OK);
        bool ok_x = sec.security_check_access(&user, 1000 as uint32, 100 as uint32, mode_700, sec.ACCESS_X_OK);

        if (!ok_r || !ok_w || !ok_x) {
            return 1;
        }

        // Non-owner access to same mode 0700 file (Owner is UID 2000, GID 200)
        bool denied_r = sec.security_check_access(&user, 2000 as uint32, 200 as uint32, mode_700, sec.ACCESS_R_OK);
        if (denied_r) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_group_and_other_permissions(self):
        code = """
        import "os/kernel/security.kl" as sec;

        sec.Credentials user;
        sec.creds_init_user(&user, 1000 as uint32, 100 as uint32);

        // Mode 0070: Group Read, Write, Execute (Owner 2000, Group 100)
        uint32 mode_070 = sec.S_IRGRP | sec.S_IWGRP | sec.S_IXGRP;

        // User GID matches file GID 100
        bool grp_read = sec.security_check_access(&user, 2000 as uint32, 100 as uint32, mode_070, sec.ACCESS_R_OK);
        bool grp_write = sec.security_check_access(&user, 2000 as uint32, 100 as uint32, mode_070, sec.ACCESS_W_OK);

        if (!grp_read || !grp_write) {
            return 1;
        }

        // Mode 0004: Other Read (Owner 2000, Group 200)
        uint32 mode_004 = sec.S_IROTH;
        bool oth_read = sec.security_check_access(&user, 2000 as uint32, 200 as uint32, mode_004, sec.ACCESS_R_OK);
        bool oth_write = sec.security_check_access(&user, 2000 as uint32, 200 as uint32, mode_004, sec.ACCESS_W_OK);

        if (!oth_read || oth_write) {
            return 2;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_privilege_dropping_and_seteuid(self):
        code = """
        import "os/kernel/security.kl" as sec;

        sec.Credentials creds;
        sec.creds_init_root(&creds);

        // Root drops privileges to UID 1000
        bool ok = sec.creds_set_euid(&creds, 1000 as uint32);
        if (!ok || creds.euid != (1000 as uint32)) {
            return 1;
        }

        // Now user is unprivileged (euid = 1000, uid = 0, suid = 0)
        // Can switch back to saved UID 0
        ok = sec.creds_set_euid(&creds, 0 as uint32);
        if (!ok || creds.euid != (0 as uint32)) {
            return 2;
        }

        // Completely unprivileged user (uid = 1000, euid = 1000, suid = 1000)
        sec.Credentials normal_user;
        sec.creds_init_user(&normal_user, 1000 as uint32, 100 as uint32);

        // Normal user attempts illegal switch to root (UID 0)
        bool illegal = sec.creds_set_euid(&normal_user, 0 as uint32);
        if (illegal || normal_user.euid != (1000 as uint32)) {
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_cap_dac_override(self):
        code = """
        import "os/kernel/security.kl" as sec;

        sec.Credentials creds;
        sec.creds_init_user(&creds, 1000 as uint32, 100 as uint32);

        // Grant CAP_DAC_OVERRIDE
        creds.capabilities = sec.CAP_DAC_OVERRIDE;

        // File with mode 0000 (no permissions for anyone)
        uint32 mode_000 = 0 as uint32;

        bool can_read = sec.security_check_access(&creds, 2000 as uint32, 200 as uint32, mode_000, sec.ACCESS_R_OK);
        bool can_write = sec.security_check_access(&creds, 2000 as uint32, 200 as uint32, mode_000, sec.ACCESS_W_OK);

        if (!can_read || !can_write) {
            return 1;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
