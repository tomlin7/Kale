import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestMatrixMath(unittest.TestCase):
    def run_kale_jit(self, code: str) -> int:
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

    def test_math_scalars_and_trig(self):
        code = """
        import "packages/std/math/math.kl" as m;

        float pi = m.PI();
        float rad = m.deg_to_rad(180.0f);
        if (!m.approx_eq(pi, rad, 0.001f)) {
            return 1;
        }

        float s = m.sinf(0.0f);
        float c = m.cosf(0.0f);
        if (s != 0.0f || c != 1.0f) {
            return 2;
        }

        float clamped = m.clamp_f(15.0f, 0.0f, 10.0f);
        if (clamped != 10.0f) {
            return 3;
        }

        float lerped = m.lerp_f(10.0f, 20.0f, 0.5f);
        if (lerped != 15.0f) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_vec2_and_vec3_primitives(self):
        code = """
        import "packages/std/math/vec2.kl" as v2;
        import "packages/std/math/vec3.kl" as v3;

        v2.Vec2 a = v2.vec2(3.0f, 4.0f);
        float len = v2.vec2_len(a); // 5.0f
        if (len != 5.0f) {
            return 1;
        }

        v2.Vec2 norm = v2.vec2_normalize(a);
        if (norm.x != 0.6f || norm.y != 0.8f) {
            return 2;
        }

        v3.Vec3 vx = v3.vec3(1.0f, 0.0f, 0.0f);
        v3.Vec3 vy = v3.vec3(0.0f, 1.0f, 0.0f);
        v3.Vec3 vz = v3.vec3_cross(vx, vy); // should be (0, 0, 1)

        if (vz.x != 0.0f || vz.y != 0.0f || vz.z != 1.0f) {
            return 3;
        }

        float dot = v3.vec3_dot(vx, vy);
        if (dot != 0.0f) {
            return 4;
        }

        return 55;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 55)

    def test_mat2_and_mat3_affine_transformations(self):
        code = """
        import "packages/std/math/vec2.kl" as v2;
        import "packages/std/math/mat2.kl" as m2;
        import "packages/std/math/mat3.kl" as m3;

        m2.Mat2 rot90 = m2.mat2_rotation(1.5707963f); // ~90 deg
        v2.Vec2 pt = v2.vec2(1.0f, 0.0f);
        v2.Vec2 rot_pt = m2.mat2_transform(rot90, pt);

        // (1, 0) rotated 90 deg -> (0, 1)
        if (rot_pt.x > 0.001f || rot_pt.x < -0.001f || rot_pt.y < 0.99f || rot_pt.y > 1.01f) {
            return 1;
        }

        // Test 3x3 translation
        m3.Mat3 trans = m3.mat3_translation(10.0f, 20.0f);
        v2.Vec2 moved = m3.mat3_transform_point(trans, pt);
        if (moved.x != 11.0f || moved.y != 20.0f) {
            return 2;
        }

        // Inverse test
        m3.Mat3 inv = m3.mat3_inverse(trans);
        v2.Vec2 back = m3.mat3_transform_point(inv, moved);
        if (back.x != 1.0f || back.y != 0.0f) {
            return 3;
        }

        return 77;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 77)

    def test_mat4_and_libs_matrix_pipeline(self):
        code = """
        import "packages/std/math/vec2.kl" as v2;
        import "packages/std/math/vec3.kl" as v3;
        import "packages/std/math/mat4.kl" as m4;
        import "libs/matrix/matrix.kl" as lm;

        // Test Mat4 translation & multiply
        m4.Mat4 m = m4.mat4_translation(5.0f, 10.0f, 15.0f);
        v3.Vec3 p = v3.vec3(1.0f, 2.0f, 3.0f);
        v3.Vec3 transformed = m4.mat4_transform_point(m, p);

        if (transformed.x != 6.0f || transformed.y != 12.0f || transformed.z != 18.0f) {
            return 1;
        }

        // Test Rigid Body 2D local-to-world and world-to-local
        lm.RigidTransform2D body = lm.rigid2d_new(100.0f, 200.0f, 0.0f);
        v2.Vec2 local_pt = v2.vec2(10.0f, 5.0f);
        v2.Vec2 world_pt = lm.rigid2d_local_to_world(body, local_pt);

        if (world_pt.x != 110.0f || world_pt.y != 205.0f) {
            return 2;
        }

        v2.Vec2 restored_pt = lm.rigid2d_world_to_local(body, world_pt);
        if (restored_pt.x != 10.0f || restored_pt.y != 5.0f) {
            return 3;
        }

        return 99;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 99)

if __name__ == "__main__":
    unittest.main()
