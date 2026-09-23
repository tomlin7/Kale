import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSAudioMixer(unittest.TestCase):
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

    def test_sound_server_init_and_controls(self):
        code = r"""
        import "os/kernel/sound_server.kl" as snd;

        snd.SoundServer srv;
        snd.sound_server_init(&srv);

        if (snd.sound_server_get_master_volume(&srv) != (80 as uint32)) return 1;
        if (snd.sound_server_is_master_muted(&srv)) return 2;
        if (snd.sound_server_get_channel_volume(&srv, 0 as uint32) != (100 as uint32)) return 3;

        // Change volume
        snd.sound_server_set_master_volume(&srv, 150 as uint32); // Clamped to 100
        if (snd.sound_server_get_master_volume(&srv) != (100 as uint32)) return 4;

        snd.sound_server_set_channel_volume(&srv, 1 as uint32, 50 as uint32);
        if (snd.sound_server_get_channel_volume(&srv, 1 as uint32) != (50 as uint32)) return 5;

        // Mute
        snd.sound_server_set_master_muted(&srv, true);
        if (!snd.sound_server_is_master_muted(&srv)) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_audio_mixing_and_attenuation(self):
        code = r"""
        import "os/kernel/sound_server.kl" as snd;

        snd.SoundServer srv;
        snd.sound_server_init(&srv);

        snd.sound_server_set_master_volume(&srv, 100 as uint32);
        snd.sound_server_set_channel_volume(&srv, 0 as uint32, 50 as uint32); // 50% attenuation

        int16[4] test_samples;
        test_samples[0] = 1000 as int16;
        test_samples[1] = 2000 as int16;
        test_samples[2] = -1000 as int16;
        test_samples[3] = 4000 as int16;

        uint32 fed = snd.sound_server_feed(&srv, 0 as uint32, &test_samples[0], 4 as uint32);
        if (fed != (4 as uint32)) return 1;

        // Mix 4 frames
        snd.sound_server_mix(&srv, 4 as uint32);

        // 1000 * 50% = 500
        if (srv.mix_output[0] != (500 as int16)) return 2;
        // 2000 * 50% = 1000
        if (srv.mix_output[1] != (1000 as int16)) return 3;
        // -1000 * 50% = -500
        if (srv.mix_output[2] != (-500 as int16)) return 4;
        // 4000 * 50% = 2000
        if (srv.mix_output[3] != (2000 as int16)) return 5;

        // Peak level: 2000
        if (srv.peak_level != (2000 as int16)) return 6;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_saturating_clipping_and_mute(self):
        code = r"""
        import "os/kernel/sound_server.kl" as snd;

        snd.SoundServer srv;
        snd.sound_server_init(&srv);

        snd.sound_server_set_master_volume(&srv, 100 as uint32);
        snd.sound_server_set_channel_volume(&srv, 0 as uint32, 100 as uint32);
        snd.sound_server_set_channel_volume(&srv, 1 as uint32, 100 as uint32);

        // Feed 25000 into channel 0 and channel 1 -> Sum = 50000 -> Should saturate to 32767
        int16[1] sample_a;
        sample_a[0] = 25000 as int16;
        int16[1] sample_b;
        sample_b[0] = 25000 as int16;

        snd.sound_server_feed(&srv, 0 as uint32, &sample_a[0], 1 as uint32);
        snd.sound_server_feed(&srv, 1 as uint32, &sample_b[0], 1 as uint32);

        snd.sound_server_mix(&srv, 1 as uint32);
        if (srv.mix_output[0] != (32767 as int16)) return 1;

        // Feed negative values: -25000 on both -> -50000 -> Should saturate to -32768
        sample_a[0] = -25000 as int16;
        sample_b[0] = -25000 as int16;
        snd.sound_server_feed(&srv, 0 as uint32, &sample_a[0], 1 as uint32);
        snd.sound_server_feed(&srv, 1 as uint32, &sample_b[0], 1 as uint32);

        snd.sound_server_mix(&srv, 1 as uint32);
        if (srv.mix_output[0] != (-32768 as int16)) return 2;

        // Test channel mute silence
        sample_a[0] = 10000 as int16;
        snd.sound_server_feed(&srv, 0 as uint32, &sample_a[0], 1 as uint32);
        snd.sound_server_set_channel_muted(&srv, 0 as uint32, true);
        snd.sound_server_mix(&srv, 1 as uint32);
        if (srv.mix_output[0] != (0 as int16)) return 3;

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

if __name__ == "__main__":
    unittest.main()
