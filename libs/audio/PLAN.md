# libs/audio Architecture Plan

## 1. Overview
Real-time audio engine with sub-6ms playback latency.

## 2. Modules
- `wasapi.kl`: Windows Audio Session API COM interface wrappers.
- `mixer.kl`: Multi-channel floating point PCM mixer with volume & panning.
- `synth.kl`: Sine, square, sawtooth, and noise wave generators with ADSR envelopes.
- `sound.kl`: WAV and raw sample format decoders.
