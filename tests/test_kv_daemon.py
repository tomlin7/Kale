import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestKvDaemon(unittest.TestCase):
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

    def test_kv_store_and_daemon_commands(self):
        code = """
        import "apps/kv/store.kl" as store;
        import "apps/kv/daemon.kl" as daemon;

        extern int strcmp(string s1, string s2);

        store.KvStore* s = store.store_new(16);
        store.store_set(s, "arch", "x86_64");

        string res_ping = daemon.daemon_execute_command(s, "PING\\r\\n");
        if (strcmp(res_ping, "+PONG\\r\\n") != 0) {
            return 1;
        }

        string res_get = daemon.daemon_execute_command(s, "GET arch\\r\\n");
        if (strcmp(res_get, "$6\\r\\nx86_64\\r\\n") != 0) {
            return 2;
        }

        string res_set = daemon.daemon_execute_command(s, "SET mode daemon\\r\\n");
        if (strcmp(res_set, "+OK\\r\\n") != 0) {
            return 3;
        }

        string res_del = daemon.daemon_execute_command(s, "DEL arch\\r\\n");
        if (strcmp(res_del, ":1\\r\\n") != 0) {
            return 4;
        }

        string res_dbsize = daemon.daemon_execute_command(s, "DBSIZE\\r\\n");
        if (strcmp(res_dbsize, ":1\\r\\n") != 0) {
            return 5;
        }

        store.store_free(s);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_kv_resp_array_and_arity(self):
        code = """
        import "apps/kv/store.kl" as store;
        import "apps/kv/daemon.kl" as daemon;

        extern int strcmp(string s1, string s2);

        store.KvStore* s = store.store_new(16);

        // Test RESP array commands
        string r_ping = daemon.daemon_execute_command(s, "*1\\r\\n$4\\r\\nPING\\r\\n");
        if (strcmp(r_ping, "+PONG\\r\\n") != 0) {
            return 1;
        }

        string r_set = daemon.daemon_execute_command(s, "*3\\r\\n$3\\r\\nSET\\r\\n$3\\r\\nkey\\r\\n$5\\r\\nvalue\\r\\n");
        if (strcmp(r_set, "+OK\\r\\n") != 0) {
            return 2;
        }

        string r_get = daemon.daemon_execute_command(s, "*2\\r\\n$3\\r\\nGET\\r\\n$3\\r\\nkey\\r\\n");
        if (strcmp(r_get, "$5\\r\\nvalue\\r\\n") != 0) {
            return 3;
        }

        // Arity validation on SET with no value
        string r_err = daemon.daemon_execute_command(s, "SET only_key\\r\\n");
        if (strcmp(r_err, "-ERR wrong number of arguments for 'set' command\\r\\n") != 0) {
            return 4;
        }

        store.store_free(s);
        return 99;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 99)

if __name__ == "__main__":
    unittest.main()
