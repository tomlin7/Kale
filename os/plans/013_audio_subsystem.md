# Milestone 13: Audio Subsystem & Sound Blaster 16 / AC97 Driver

## Overview
Implement the bare-metal Audio Subsystem for Kale OS. This subsystem provides digital sound synthesis and audio hardware abstraction for the industry-standard Sound Blaster 16 (SB16) DSP architecture and the Intel AC97 PCI audio controller. It includes DSP reset handshaking, DMA buffer configuration, master volume mixing, software PCM waveform generation, and system alert sound synthesis (terminal bell, startup chime, button click).

## Architecture

```
                       +-------------------------+
                       |     Audio Subsystem     |
                       |   (os/drivers/audio.kl) |
                       +------------+------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
     [SB16 DSP Driver]        [AC97 Controller]       [PCM Waveform Synth]
     Ports 0x220..0x22F       PCI NAMBAR / NABMBAR     Square / Sine Waves
     DMA Channel 1 / 5        Buffer Descriptors (BDL) Chime, Bell, Click
```

## Phases

### Phase 1: Sound Blaster 16 DSP Interface
- Base port: `0x220` (default standard across PC architecture and QEMU).
- Ports:
  - `0x224`: Mixer Register Address.
  - `0x225`: Mixer Data Register.
  - `0x226`: DSP Reset.
  - `0x22A`: DSP Read Data.
  - `0x22C`: DSP Write Data / Command (and Write Buffer Status, bit 7: busy).
  - `0x22E`: DSP Data Available (Read Buffer Status, bit 7: ready).
  - `0x22F`: DSP 16-bit Interrupt Acknowledge.
- Reset protocol:
  - Write `1` to `0x226`, wait 3 microseconds, write `0` to `0x226`.
  - Poll `0x22E` (bit 7 == 1) for data ready.
  - Read `0x22A`: must return `0xAA` (success).

### Phase 2: SB16 DSP Commands & Mixer Control
- `DSP_CMD_SET_TIME_CONSTANT (0x40)`: Sets sample rate $TC = 65536 - (256000000 / (channels \times sample\_rate))$.
- `DSP_CMD_SET_OUTPUT_RATE (0x41)`: SB16 high-speed rate setting.
- `DSP_CMD_VERSION (0xE1)`: Returns major and minor versions (e.g., 4 and 5 for SB16).
- SB16 Mixer:
  - Register `0x22` (Master Volume: Left 4 bits, Right 4 bits).
  - Register `0x04` (Voice / DAC Volume).
  - Register `0x28` (CD Audio Volume).
  - Register `0x2E` (Line In Volume).

### Phase 3: DMA Buffer Configuration
- 8-bit Audio: DMA Channel 1 (Page register `0x83`, Address `0x02`, Count `0x03`).
- 16-bit Audio: DMA Channel 5 (Page register `0x8B`, Address `0xC4`, Count `0xC6`).
- Buffer descriptor calculation: Address, length in bytes / words, and auto-initialize mode.

### Phase 4: Intel AC97 Audio Controller
- Native Audio Mixer Base Address (NAMBAR) from PCI BAR0.
- Native Audio Bus Master Base Address (NABMBAR) from PCI BAR1.
- Buffer Descriptor List (BDL) structure for ring-buffered audio streaming.

### Phase 5: Software Sound Synthesis & Alerts
- Waveform generation engine:
  - Square wave generation: period $T = \frac{sample\_rate}{freq}$.
  - Sine wave approximation.
- Desktop sound alerts:
  - `audio_play_beep(freq, duration_ms)`: Generates square wave tone.
  - `audio_play_chime()`: Two-tone ascending chime (523 Hz -> 659 Hz).
  - `audio_play_click()`: Short 10ms impulse click for mouse interaction.
