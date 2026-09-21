import unittest
import os
from kale.diagnostics.source_text import SourceText
from kale.diagnostics.diagnostic_bag import DiagnosticBag
from kale.parser.parser import Parser
from kale.binding.binder import Binder
from kale.binding.module_loader import ModuleLoader
from kale.codegen.llvm_emitter import LLVMEmitter
from kale.codegen.llvm_jit import LLVMJIT

class TestOSAudioSubsystem(unittest.TestCase):
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

    def test_sb16_init_and_versioning(self):
        code = """
        import "os/drivers/audio.kl" as audio;

        audio.SB16Device dev;
        // Default SB16 config: Base 0x220, IRQ 5, 8-bit DMA 1, 16-bit DMA 5
        audio.sb16_init(&dev, 0x0220 as uint16, 5 as uint8, 1 as uint8, 5 as uint8);

        if (!dev.is_active || !dev.speaker_enabled) {
            return 1;
        }
        if (dev.base_port != (0x0220 as uint16) || dev.irq != (5 as uint8)) {
            return 2;
        }
        if (dev.dma8_channel != (1 as uint8) || dev.dma16_channel != (5 as uint8)) {
            return 3;
        }
        if (dev.major_version != (4 as uint8) || dev.minor_version != (5 as uint8)) {
            return 4;
        }

        // Test updating version
        audio.sb16_set_version(&dev, 4 as uint8, 12 as uint8);
        if (dev.minor_version != (12 as uint8)) {
            return 5;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_sb16_volume_packing(self):
        code = """
        import "os/drivers/audio.kl" as audio;

        audio.SB16Device dev;
        audio.sb16_init(&dev, 0x0220 as uint16, 5 as uint8, 1 as uint8, 5 as uint8);

        // Set volume to 12 (left) and 10 (right)
        // 12 = 0x0C, 10 = 0x0A -> (0x0C << 4) | 0x0A = 0xCA
        uint8 packed1 = audio.sb16_set_master_volume(&dev, 12 as uint8, 10 as uint8);
        if (packed1 != (0xCA as uint8)) {
            return 1;
        }
        if (dev.master_vol_left != (12 as uint8) || dev.master_vol_right != (10 as uint8)) {
            return 2;
        }

        // Test clamping to 15 (0x0F)
        uint8 packed2 = audio.sb16_set_master_volume(&dev, 20 as uint8, 30 as uint8);
        if (packed2 != (0xFF as uint8)) {
            return 3;
        }
        if (dev.master_vol_left != (15 as uint8) || dev.master_vol_right != (15 as uint8)) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_sb16_time_constant_calculation(self):
        code = """
        import "os/drivers/audio.kl" as audio;

        // 11025 Hz mono: div = 1000000 / 11025 = 90 -> tc = 256 - 90 = 166
        uint8 tc1 = audio.sb16_calc_time_constant(11025 as uint32, 1 as uint8);
        if (tc1 != (166 as uint8)) {
            return 1;
        }

        // 22050 Hz mono: div = 1000000 / 22050 = 45 -> tc = 256 - 45 = 211
        uint8 tc2 = audio.sb16_calc_time_constant(22050 as uint32, 1 as uint8);
        if (tc2 != (211 as uint8)) {
            return 2;
        }

        // 44100 Hz mono: div = 1000000 / 44100 = 22 -> tc = 256 - 22 = 234
        uint8 tc3 = audio.sb16_calc_time_constant(44100 as uint32, 1 as uint8);
        if (tc3 != (234 as uint8)) {
            return 3;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_ac97_bdl_entry_init(self):
        code = """
        import "os/drivers/audio.kl" as audio;

        audio.AC97Device dev;
        // NAMBAR = 0x1000, NABMBAR = 0x1100, IRQ 11
        audio.ac97_init(&dev, 0x1000 as uint16, 0x1100 as uint16, 11 as uint8);

        if (!dev.is_active || dev.mixer_base != (0x1000 as uint16) || dev.bus_master_base != (0x1100 as uint16)) {
            return 1;
        }

        // Initialize BDL Entry: Buffer 0x00200000, 1024 samples, with IOC
        audio.AC97BDLEntry entry;
        audio.ac97_bdl_entry_init(&entry, 0x00200000 as uint32, 1024 as uint16, true);

        if (entry.buffer_phys != (0x00200000 as uint32) || entry.sample_count != (1024 as uint16)) {
            return 2;
        }
        if (entry.flags != (0x8000 as uint16)) { // IOC bit 15
            return 3;
        }

        // Without IOC
        audio.ac97_bdl_entry_init(&entry, 0x00200000 as uint32, 512 as uint16, false);
        if (entry.flags != (0 as uint16)) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_audio_synth_square_wave(self):
        code = """
        import "os/drivers/audio.kl" as audio;

        audio.AudioSynth synth;
        audio.audio_synth_init(&synth, 8000 as uint32, 1 as uint8, 8 as uint8);

        if (synth.sample_rate != (8000 as uint32) || synth.channels != (1 as uint8)) {
            return 1;
        }

        // Generate 1000 Hz tone for 10 ms at 8000 Hz sample rate
        // Expected samples: 8000 * 10 / 1000 = 80 samples
        // Period: 8000 / 1000 = 8 samples (half period = 4 samples)
        uint8[100] buf;
        int count = audio.audio_synth_square_wave(&synth, 1000 as uint32, 10 as uint32, &buf[0], 100);
        if (count != 80) {
            return 2;
        }

        // First 4 samples should be high amplitude (200)
        int i = 0;
        while (i < 4) {
            if (buf[i] != (200 as uint8)) {
                return 3;
            }
            i = i + 1;
        }

        // Next 4 samples should be low amplitude (56)
        while (i < 8) {
            if (buf[i] != (56 as uint8)) {
                return 4;
            }
            i = i + 1;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)

    def test_audio_alert_frequencies(self):
        code = """
        import "os/drivers/audio.kl" as audio;

        uint32 freq = 0 as uint32;
        uint32 dur = 0 as uint32;

        // 1. Terminal Bell
        audio.audio_alert_params(audio.AUDIO_ALERT_BELL, &freq, &dur);
        if (freq != (800 as uint32) || dur != (100 as uint32)) {
            return 1;
        }

        // 2. Chime Note 1
        audio.audio_alert_params(audio.AUDIO_ALERT_CHIME1, &freq, &dur);
        if (freq != (523 as uint32) || dur != (120 as uint32)) {
            return 2;
        }

        // 3. Chime Note 2
        audio.audio_alert_params(audio.AUDIO_ALERT_CHIME2, &freq, &dur);
        if (freq != (659 as uint32) || dur != (180 as uint32)) {
            return 3;
        }

        // 4. Mouse Click
        audio.audio_alert_params(audio.AUDIO_ALERT_CLICK, &freq, &dur);
        if (freq != (1200 as uint32) || dur != (15 as uint32)) {
            return 4;
        }

        return 42;
        """
        res = self.run_kale_jit(code)
        self.assertEqual(res, 42)
