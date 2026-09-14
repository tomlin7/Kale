# Android Cross-Compilation & Scaffolding Tool (`apps/android-bootstrapper`) Plan

## 1. Overview
`apps/android-bootstrapper` is a dedicated CLI toolchain component for compiling Kale source code into native Android shared libraries (`.so`) targeting `aarch64-linux-android` and packaging them into runnable APKs with NativeActivity.

---

## 2. Architecture & Pipeline

```
[ Kale Source (.kl) ]
         │
         ▼
[ PythonKale Compiler ] ──(target: aarch64-linux-android)──► [ libmain.so ]
                                                                   │
                                                                   ▼
[ Android SDK / AAPT2 ] ──(compile AndroidManifest.xml)──────► [ app.apk ]
                                                                   │
                                                                   ▼
[ apksigner / zipalign ] ────────────────────────────────────► [ Signed APK ]
```

---

## 3. Planned Capabilities
1. **Target Triple Configuration**: Directing LLVM to emit ELF binaries for ARM64 Android (`aarch64-linux-android`).
2. **Android NativeActivity Glue**: Interfacing with the Android NDK `android_native_app_glue` to receive touch events, lifecycle events, and render surfaces without Java/Kotlin boilerplate.
3. **Automated Packaging**: Bundling assets, shaders, compiled native libraries, and manifest into a distributable APK.
