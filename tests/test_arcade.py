import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestArcade(unittest.TestCase):
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

    def test_arcade_physics_and_gameplay(self):
        code = """
        import "games/arcade/game.kl" as game;
        import "libs/physics/body.kl" as body;

        game.ArcadeGame* g = game.arcade_new(400, 300);

        game.arcade_player_thrust(g, 2, -1);
        if (g->player_body->vel.x != 2) {
            return 1;
        }

        // Place bullet on target0 to simulate hit
        g->bullet->pos.x = g->target0->pos.x + 2;
        g->bullet->pos.y = g->target0->pos.y + 2;
        g->bullet_active = true;

        game.arcade_step(g, 1);
        if (g->score != 100) {
            return 2;
        }

        game.arcade_render(g);

        game.arcade_free(g);
        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
