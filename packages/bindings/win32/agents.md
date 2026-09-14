# Win32 Bindings

## Version
`0.1.0`

## Description
Foreign function interface bindings for Windows Win32 API (user32.dll, gdi32.dll, kernel32.dll). Provides native window creation, GDI graphics, and system calls.

## Status
Current status: 🟡 In Progress

## Dependencies
- PythonKale compiler
- Windows OS

## Build Instructions
Imported by Kale programs. Linked against system DLLs automatically.

## Coding Conventions
- Extern declarations match C ABI exactly
- Use int32 for UINT/DWORD/int C types, void* for HANDLE/HWND/HDC

## Short-term Milestones
- [ ] Add common dialog bindings (file open/save)
- [ ] Add clipboard API
- [ ] Add timer API

## Future Plans
May be superseded by GLFW for windowing, but remains for native Windows integration.
