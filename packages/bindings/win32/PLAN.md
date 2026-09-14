# Win32 Platform FFI Bindings (`packages/bindings/win32`) Plan

## 1. Overview
Provides direct C ABI declarations for the Windows Win32 API (`user32.dll`, `gdi32.dll`, `kernel32.dll`, `comdlg32.dll`).

---

## 2. Planned Module Additions

### 2.1 File Dialogs (`dialog.kl`)
- Bind `GetOpenFileNameA` and `GetSaveFileNameA` from `comdlg32.dll`.
- Provide high-level Kale wrappers: `open_file_dialog() -> string`, `save_file_dialog() -> string`.

### 2.2 System Clipboard (`clipboard.kl`)
- Bind `OpenClipboard`, `CloseClipboard`, `GetClipboardData`, `SetClipboardData`, `EmptyClipboard`.
- Provide `clipboard_get_text() -> string` and `clipboard_set_text(text: string)`.

### 2.3 High-Resolution Timers (`timer.kl`)
- Bind `QueryPerformanceCounter` and `QueryPerformanceFrequency` for sub-microsecond frame profiling.

---

## 3. ABI Consistency Rules
- All `UINT`, `int`, `DWORD`, and `BOOL` types must map to `int32`.
- All handles (`HWND`, `HDC`, `HBRUSH`, `HFONT`) map to `void*`.
- Structs (`WNDCLASS`, `MSG`, `RECT`, `PAINTSTRUCT`) must have precise field order and alignment.
