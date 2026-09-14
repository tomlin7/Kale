# Android Cross-Compilation Scaffolding (`apps/android-bootstrapper`)

## Version
`0.0.1`

## Description
CLI toolchain component for cross-compiling Kale applications to ARM64 Android (`aarch64-linux-android`) and assembling NativeActivity APKs.

## Status
Current status: 🔴 Not Started

## Dependencies
- PythonKale compiler (with ARM64 LLVM target support)
- Android NDK & SDK (AAPT2, apksigner, zipalign)

## Build Instructions
`kale build apps/android-bootstrapper/main.kl -o bin/kale_android.exe`

## Coding Conventions
- Standard Kale naming conventions (snake_case functions, PascalCase structs).
- Explicit target triple validation.

## Short-term Milestones
- [ ] Define LLVM target triple and data layout for `aarch64-linux-android`.
- [ ] Implement NativeActivity glue interface in Kale.
- [ ] Script automatic APK packaging and signing.

## Future Plans
Interactive emulator launcher, device USB deployment via ADB, and asset compression.
