# Milestone 34: Desktop Audio Mixer & PCM Sound Server

## Overview
Implement a multi-channel software PCM audio mixing engine and sound server in pure Kale. The sound server coordinates audio streams from desktop applications, applies per-channel and master volume attenuation, performs saturating clipping, and interfaces with hardware audio drivers (SB16 and AC97).

## Key Components
1. **Audio Channels & Streams**:
   - Up to 4 simultaneous PCM audio channels (`AUDIO_CHAN_SYSTEM`, `AUDIO_CHAN_MEDIA`, `AUDIO_CHAN_SFX`, `AUDIO_CHAN_VOICE`).
   - Per-channel volume attenuation (0–100%) and mute flags.
   - Master volume attenuation (0–100%) and master mute flag.
2. **PCM Audio Mixing & Clamping**:
   - 16-bit signed linear PCM processing (`int16`).
   - Dynamic range saturation clamping to `[-32768, 32767]` preventing overflow distortion.
   - Audio mixing equation: `sample_out = clamp((sample_in * chan_vol * master_vol) / 10000)`.
3. **Ring Buffer & Buffer Descriptors**:
   - 64-sample chunk mixing blocks.
   - Stream playback state tracking (`STATE_STOPPED`, `STATE_PLAYING`, `STATE_PAUSED`).
   - Peak amplitude level meter calculation for GUI volume sliders and tray applets.
