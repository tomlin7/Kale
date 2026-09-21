# Kale API Documentation

## Module: `apps\api_client\main.kl`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `printf`

```kale
extern int printf(string fmt, ...);
```

#### `poll_typing_api`

```kale
fn void poll_typing_api(void* window, rp.RequestPanel* panel, bool shift)
```

Poll keys for typing into the focused field of the request panel

#### `run_api_client`

```kale
fn void run_api_client()
```

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\api_client\request_panel.kl`

### Structs

#### `RequestPanel`

```kale
struct RequestPanel
```

**Methods:**

- `fn void RequestPanel.init()`
- `fn void RequestPanel.destroy()`
- `fn string RequestPanel.url()`
- `fn string RequestPanel.body()`
- `fn string RequestPanel.ct()`
- `fn string RequestPanel.method_name()`
- `fn void RequestPanel.append_char_to_focused(string ch)`
- `fn void RequestPanel.backspace()`
- `fn void RequestPanel.cycle_method()`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

---

## Module: `apps\api_client\response_viewer.kl`

### Structs

#### `ResponseLine`

```kale
struct ResponseLine
```

#### `ResponseViewer`

```kale
struct ResponseViewer
```

**Methods:**

- `fn void ResponseViewer.init()`
- `fn void ResponseViewer.destroy()`
- `fn void ResponseViewer.clear()`
- `fn void ResponseViewer.push_line(string text, int kind)`
- `fn void ResponseViewer.push_body(string body)`
  
  Split body text into individual lines and push them
- `fn void ResponseViewer.load_response(http.HttpResponse resp)`
- `fn void ResponseViewer.set_error(string msg)`
- `fn void ResponseViewer.scroll(float dy)`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

---

## Module: `apps\asset_studio\canvas_view.kl`

### Structs

#### `PixelColor`

```kale
struct PixelColor
```

RGBA color packed as int (0xRRGGBBAA)

#### `CanvasView`

```kale
struct CanvasView
```

**Methods:**

- `fn void CanvasView.init()`
- `fn void CanvasView.destroy()`
- `fn void CanvasView.set_pixel(int cx, int cy, PixelColor col)`
- `fn PixelColor CanvasView.get_pixel(int cx, int cy)`
- `fn void CanvasView.screen_to_canvas(float sx, float sy, float panel_x, float panel_y, int* out_cx, int* out_cy)`
  
  Convert screen coords to canvas pixel coords
- `fn void CanvasView.paint_at_screen(float sx, float sy, float panel_x, float panel_y)`

### Functions

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `pc_rgba`

```kale
fn PixelColor pc_rgba(int r, int g, int b, int a)
```

---

## Module: `apps\asset_studio\main.kl`

### Functions

#### `printf`

```kale
extern int printf(string fmt, ...);
```

#### `run_asset_studio`

```kale
fn void run_asset_studio()
```

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\db_studio\main.kl`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `printf`

```kale
extern int printf(string fmt, ...);
```

#### `poll_typing_into_qe`

```kale
fn void poll_typing_into_qe(void* window, qe.QueryEditor* editor, bool shift)
```

Poll A-Z keys for typing into query editor or path bar

#### `run_db_studio`

```kale
fn void run_db_studio()
```

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\db_studio\query_editor.kl`

### Structs

#### `QueryEditor`

```kale
struct QueryEditor
```

**Methods:**

- `fn void QueryEditor.init()`
- `fn void QueryEditor.destroy()`
- `fn string QueryEditor.text()`
- `fn void QueryEditor.set_text(string sql)`
- `fn void QueryEditor.append_char(string ch)`
- `fn void QueryEditor.backspace()`
- `fn void QueryEditor.clear()`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

---

## Module: `apps\db_studio\result_grid.kl`

### Structs

#### `GridCell`

```kale
struct GridCell
```

#### `ResultGrid`

```kale
struct ResultGrid
```

**Methods:**

- `fn void ResultGrid.init()`
- `fn void ResultGrid.destroy()`
- `fn void ResultGrid.clear()`
- `fn void ResultGrid.set_cell(int row, int col, string text)`
- `fn string ResultGrid.get_cell(int row, int col)`
- `fn void ResultGrid.run_query(conn.Database* db, string sql_query)`
  
  Execute a SQL query and populate this grid
- `fn void ResultGrid.scroll(float dx, float dy)`
- `fn void ResultGrid.select_at_y(float mouse_y, float panel_y)`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

---

## Module: `apps\db_studio\table_browser.kl`

### Structs

#### `TableBrowser`

```kale
struct TableBrowser
```

**Methods:**

- `fn void TableBrowser.init()`
- `fn void TableBrowser.destroy()`
- `fn void TableBrowser.load(conn.Database* db)`
- `fn void TableBrowser.select_at_y(float mouse_y, float panel_y)`
- `fn string TableBrowser.selected_name()`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `strcmp`

```kale
extern int strcmp(string a, string b);
```

---

## Module: `apps\editor\buffer_manager.kl`

### Structs

#### `EditorBuffer`

```kale
struct EditorBuffer
```

#### `BufferManager`

```kale
struct BufferManager
```

### Functions

#### `buffer_new`

```kale
fn EditorBuffer* buffer_new(int id, string path, string name, string initial_text)
```

#### `buffer_free`

```kale
fn void buffer_free(EditorBuffer* b)
```

#### `bufman_new`

```kale
fn BufferManager* bufman_new()
```

#### `bufman_get`

```kale
fn EditorBuffer* bufman_get(BufferManager* bm, int idx)
```

#### `bufman_set_slot`

```kale
fn void bufman_set_slot(BufferManager* bm, int idx, EditorBuffer* b)
```

#### `bufman_free`

```kale
fn void bufman_free(BufferManager* bm)
```

#### `bufman_open`

```kale
fn int bufman_open(BufferManager* bm, string path, string name, string content)
```

#### `bufman_get_active`

```kale
fn EditorBuffer* bufman_get_active(BufferManager* bm)
```

#### `bufman_switch`

```kale
fn void bufman_switch(BufferManager* bm, int idx)
```

#### `bufman_next`

```kale
fn void bufman_next(BufferManager* bm)
```

#### `bufman_prev`

```kale
fn void bufman_prev(BufferManager* bm)
```

#### `bufman_close`

```kale
fn bool bufman_close(BufferManager* bm, int idx)
```

#### `bufman_close_active`

```kale
fn void bufman_close_active(BufferManager* bm)
```

---

## Module: `apps\editor\layout.kl`

### Structs

#### `RectLayout`

```kale
struct RectLayout
```

#### `IdeLayout`

```kale
struct IdeLayout
```

### Functions

#### `make_rect`

```kale
fn RectLayout make_rect(int x, int y, int w, int h)
```

#### `calculate_layout`

```kale
fn IdeLayout calculate_layout(int total_w, int total_h, ts.TerminalSplit* term_split)
```

---

## Module: `apps\editor\main.kl`

### Functions

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\editor\terminal_split.kl`

### Structs

#### `TerminalSplit`

```kale
struct TerminalSplit
```

### Functions

#### `SPLIT_HORIZONTAL_BOTTOM`

```kale
fn int SPLIT_HORIZONTAL_BOTTOM()
```

#### `SPLIT_VERTICAL_RIGHT`

```kale
fn int SPLIT_VERTICAL_RIGHT()
```

#### `split_new`

```kale
fn TerminalSplit* split_new(int cols, int rows, string title)
```

#### `split_free`

```kale
fn void split_free(TerminalSplit* ts)
```

#### `split_toggle`

```kale
fn void split_toggle(TerminalSplit* ts)
```

#### `split_toggle_focus`

```kale
fn void split_toggle_focus(TerminalSplit* ts)
```

#### `split_set_direction`

```kale
fn void split_set_direction(TerminalSplit* ts, int dir)
```

#### `split_write`

```kale
fn void split_write(TerminalSplit* ts, string output)
```

#### `split_set_percent`

```kale
fn void split_set_percent(TerminalSplit* ts, int percent)
```

#### `split_resize`

```kale
fn void split_resize(TerminalSplit* ts, int cols, int rows)
```

#### `split_run_command`

```kale
fn int split_run_command(TerminalSplit* ts, string cmd)
```

#### `split_send_input`

```kale
fn void split_send_input(TerminalSplit* ts, string in_str)
```

#### `split_last_exit_code`

```kale
fn int split_last_exit_code(TerminalSplit* ts)
```

#### `split_commands_count`

```kale
fn int split_commands_count(TerminalSplit* ts)
```

#### `split_clear`

```kale
fn void split_clear(TerminalSplit* ts)
```

---

## Module: `apps\files\file_panel.kl`

### Structs

#### `FileEntry`

```kale
struct FileEntry
```

#### `FilePanel`

```kale
struct FilePanel
```

**Methods:**

- `fn void FilePanel.init(string start_dir)`
- `fn void FilePanel.destroy()`
- `fn void FilePanel.add_entry(string name, bool is_dir, int size, string ext)`
- `fn void FilePanel.refresh()`
  
  Populates entries for the current directory
- `fn void FilePanel.enter_selected()`
- `fn void FilePanel.scroll(float dy)`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `strcmp`

```kale
extern int strcmp(string a, string b);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

---

## Module: `apps\files\main.kl`

### Functions

#### `printf`

```kale
extern int printf(string fmt, ...);
```

#### `run_kale_files`

```kale
fn void run_kale_files()
```

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\git_lens\branch_view.kl`

### Structs

#### `BranchEntry`

```kale
struct BranchEntry
```

#### `BranchView`

```kale
struct BranchView
```

**Methods:**

- `fn void BranchView.init(string repo_root)`
- `fn void BranchView.destroy()`
- `fn void BranchView.load()`
  
  Load branch refs from .kale/refs/heads/
- `fn void BranchView.select_at_y(float mouse_y, float panel_y)`
- `fn string BranchView.selected_branch()`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `strcmp`

```kale
extern int strcmp(string a, string b);
```

---

## Module: `apps\git_lens\commit_graph.kl`

### Structs

#### `CommitEntry`

```kale
struct CommitEntry
```

#### `CommitGraph`

```kale
struct CommitGraph
```

**Methods:**

- `fn void CommitGraph.init(string repo_root)`
- `fn void CommitGraph.destroy()`
- `fn void CommitGraph.load()`
  
  Walk the commit DAG from HEAD and load up to MAX_COMMITS entries
- `fn void CommitGraph.scroll(float delta)`
  
  Scroll the view
- `fn void CommitGraph.select_at_y(float mouse_y, float panel_y)`
  
  Select commit at mouse y
- `fn string CommitGraph.selected_hash()`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `sprintf`

```kale
extern int sprintf(string buf, string fmt, ...);
```

#### `slice_str`

```kale
fn string slice_str(string s, int n)
```

Slices first `n` chars of `s` into a fresh malloc buffer

---

## Module: `apps\git_lens\diff_viewer.kl`

### Structs

#### `DiffLine`

```kale
struct DiffLine
```

Line kinds: 0 = context, 1 = added, 2 = removed, 3 = header

#### `DiffViewer`

```kale
struct DiffViewer
```

**Methods:**

- `fn void DiffViewer.init(string repo_root)`
- `fn void DiffViewer.destroy()`
- `fn void DiffViewer.clear()`
- `fn void DiffViewer.push_line(string text, int kind)`
- `fn void DiffViewer.load_diff_text(string diff_text)`
  
  Split a unified diff string into individual lines and load into DiffViewer
- `fn void DiffViewer.load_commit(string commit_hash)`
  
  Load diff between a commit and its parent by reading the staged blob vs current HEAD tree
- `fn void DiffViewer.scroll(float delta)`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `classify_diff_line`

```kale
fn int classify_diff_line(string s)
```

Classify a unified-diff output line by its first character

---

## Module: `apps\git_lens\main.kl`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `strcmp`

```kale
extern int strcmp(string a, string b);
```

#### `printf`

```kale
extern int printf(string fmt, ...);
```

#### `run_git_lens`

```kale
fn void run_git_lens(string repo_root)
```

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\hex\hex_view.kl`

### Structs

#### `HexView`

```kale
struct HexView
```

**Methods:**

- `fn void HexView.init()`
- `fn void HexView.load_data(char* data, int size, bool owns)`
- `fn void HexView.destroy()`
- `fn void HexView.scroll(float dy)`
- `fn void HexView.select_at(float mouse_x, float mouse_y, float panel_x, float panel_y)`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `nibble_to_char`

```kale
fn char nibble_to_char(int n)
```

---

## Module: `apps\hex\main.kl`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `printf`

```kale
extern int printf(string fmt, ...);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `int_to_str`

```kale
fn string int_to_str(int n)
```

Convert int to 10-char decimal string (right-aligned)

#### `append_path_char`

```kale
fn void append_path_char(int ch)
```

#### `poll_path_typing`

```kale
fn void poll_path_typing(void* window, bool shift)
```

#### `run_hex_editor`

```kale
fn void run_hex_editor()
```

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\kv\daemon.kl`

### Structs

#### `KaledisDaemon`

```kale
struct KaledisDaemon
```

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `strcmp`

```kale
extern int strcmp(string s1, string s2);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `to_upper_char`

```kale
fn char to_upper_char(char c)
```

Uppercase a character if lowercase ASCII

#### `str_eq_ci`

```kale
fn bool str_eq_ci(string a, string b)
```

Check if two strings match case-insensitively

#### `daemon_execute_command`

```kale
fn string daemon_execute_command(store.KvStore* s, string raw_cmd)
```

Parses raw command string into RESP-formatted response
Parses raw command string into RESP-formatted response

#### `daemon_new`

```kale
fn KaledisDaemon* daemon_new(string host, int port, int max_entries)
```

#### `daemon_free`

```kale
fn void daemon_free(KaledisDaemon* d)
```

#### `daemon_start`

```kale
fn bool daemon_start(KaledisDaemon* d, int backlog)
```

#### `daemon_stop`

```kale
fn void daemon_stop(KaledisDaemon* d)
```

#### `daemon_handle_client`

```kale
fn bool daemon_handle_client(KaledisDaemon* d, tcp.TcpStream* client)
```

Handles a single client connection exchange

---

## Module: `apps\kv\main.kl`

### Functions

#### `strcmp`

```kale
extern int strcmp(string s1, string s2);
```

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\kv\store.kl`

### Structs

#### `KvEntry`

```kale
struct KvEntry
```

#### `KvStore`

```kale
struct KvStore
```

### Functions

#### `strcmp`

```kale
extern int strcmp(string s1, string s2);
```

apps/kv/store.kl
Core In-Memory Key-Value Storage Engine (kaledis)

#### `store_new`

```kale
fn KvStore* store_new(int max_entries)
```

#### `store_free`

```kale
fn void store_free(KvStore* s)
```

#### `store_set`

```kale
fn void store_set(KvStore* s, string k, string v)
```

#### `store_get`

```kale
fn string store_get(KvStore* s, string k)
```

#### `store_exists`

```kale
fn bool store_exists(KvStore* s, string k)
```

#### `store_del`

```kale
fn bool store_del(KvStore* s, string k)
```

#### `store_active_count`

```kale
fn int store_active_count(KvStore* s)
```

#### `store_clear`

```kale
fn void store_clear(KvStore* s)
```

#### `store_get_key_at`

```kale
fn string store_get_key_at(KvStore* s, int active_index)
```

---

## Module: `apps\lsp\analysis.kl`

### Structs

#### `AnalysisResult`

```kale
struct AnalysisResult
```

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `analysis_analyze`

```kale
fn AnalysisResult analysis_analyze(string code)
```

---

## Module: `apps\lsp\document.kl`

### Structs

#### `LspDocument`

```kale
struct LspDocument
```

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

apps/lsp/document.kl
Document Store and Tracking for Kale LSP Server

#### `strcmp`

```kale
extern int strcmp(string a, string b);
```

#### `document_new`

```kale
fn LspDocument* document_new(string uri, int version, string content)
```

#### `document_free`

```kale
fn void document_free(LspDocument* doc)
```

#### `document_update`

```kale
fn void document_update(LspDocument* doc, int new_version, string new_content)
```

---

## Module: `apps\lsp\main.kl`

### Functions

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\lsp\protocol.kl`

### Structs

#### `LspPosition`

```kale
struct LspPosition
```

#### `LspRange`

```kale
struct LspRange
```

#### `LspDiagnostic`

```kale
struct LspDiagnostic
```

### Functions

#### `diagnostic_new`

```kale
fn LspDiagnostic diagnostic_new(int line, int col, string msg)
```

---

## Module: `apps\lsp\rpc.kl`

### Structs

#### `JsonRpcMessage`

```kale
struct JsonRpcMessage
```

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

apps/lsp/rpc.kl
JSON-RPC 2.0 Framing and Protocol Parser for Kale LSP

#### `strcmp`

```kale
extern int strcmp(string a, string b);
```

#### `rpc_make_request`

```kale
fn JsonRpcMessage rpc_make_request(int id, string method, string params)
```

#### `rpc_make_notification`

```kale
fn JsonRpcMessage rpc_make_notification(string method, string params)
```

#### `rpc_method_equals`

```kale
fn bool rpc_method_equals(string actual, string target)
```

Minimal match helper for JSON-RPC methods

---

## Module: `apps\lsp\server.kl`

### Structs

#### `LspServer`

```kale
struct LspServer
```

### Functions

#### `server_new`

```kale
fn LspServer* server_new()
```

#### `server_free`

```kale
fn void server_free(LspServer* s)
```

---

## Module: `apps\perf\main.kl`

### Structs

#### `PerfMonitor`

```kale
struct PerfMonitor
```

**Methods:**

- `fn void PerfMonitor.init()`
- `fn void PerfMonitor.destroy()`
- `fn void PerfMonitor.push_frame(float dt_ms)`

### Functions

#### `printf`

```kale
extern int printf(string fmt, ...);
```

#### `sprintf`

```kale
extern int sprintf(string buf, string f, ...);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `render_frame_graph`

```kale
fn void render_frame_graph(fw.App* app, PerfMonitor* pm, float x, float y, float w, float h)
```

Render the rolling frame-time bar chart

#### `run_perf`

```kale
fn void run_perf()
```

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\shader_lab\live_shader.kl`

### Structs

#### `LiveShader`

```kale
struct LiveShader
```

**Methods:**

- `fn void LiveShader.init(glloader.GLContext* gl_ctx)`
- `fn void LiveShader.destroy(glloader.GLContext* gl_ctx)`
- `fn bool LiveShader.compile(glloader.GLContext* gl_ctx, string frag_src)`
  
  Compile a new fragment shader source and link it with the fullscreen vert shader
Returns true on success; false on error (check last_error)
- `fn void LiveShader.render(glloader.GLContext* gl_ctx, float time, float w, float h, float mx, float my)`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `printf`

```kale
extern int printf(string fmt, ...);
```

---

## Module: `apps\shader_lab\main.kl`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `printf`

```kale
extern int printf(string fmt, ...);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `run_shader_lab`

```kale
fn void run_shader_lab()
```

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\term\main.kl`

### Structs

#### `TermSession`

```kale
struct TermSession
```

**Methods:**

- `fn void TermSession.init(int cols, int rows)`
- `fn void TermSession.destroy()`
- `fn void TermSession.append_char(int ch)`
- `fn void TermSession.backspace()`
- `fn void TermSession.submit()`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `printf`

```kale
extern int printf(string fmt, ...);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `poll_term_typing`

```kale
fn void poll_term_typing(void* window, TermSession* session, bool shift)
```

Poll keyboard and feed printable chars into the active session

#### `run_kale_term`

```kale
fn void run_kale_term()
```

#### `main_entry`

```kale
fn int main_entry()
```

---

## Module: `apps\term\tab_bar.kl`

### Structs

#### `TabBar`

```kale
struct TabBar
```

**Methods:**

- `fn void TabBar.init()`
- `fn void TabBar.destroy()`
- `fn void TabBar.add_tab(string title)`
- `fn void TabBar.close_active()`
- `fn void TabBar.select_at_x(float mouse_x, float panel_x)`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

---

## Module: `apps\term\terminal_view.kl`

### Structs

#### `TerminalView`

```kale
struct TerminalView
```

**Methods:**

- `fn void TerminalView.init(int cols, int rows, string title)`
- `fn void TerminalView.destroy()`
- `fn void TerminalView.write(string s)`
- `fn void TerminalView.scroll(float dy)`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `tci`

```kale
fn float tci(int v)
```

Convert TermColor int (0-255) to float

---

## Module: `apps\tracker\main.kl`

### Structs

#### `Card`

```kale
struct Card
```

#### `KanbanBoard`

```kale
struct KanbanBoard
```

**Methods:**

- `fn void KanbanBoard.init()`
- `fn void KanbanBoard.destroy()`
- `fn void KanbanBoard.add_card(string title)`
- `fn void KanbanBoard.move_selected(int dir)`
- `fn void KanbanBoard.delete_selected()`
- `fn int KanbanBoard.count_in_col(int col)`
- `fn void KanbanBoard.render(fw.App* app, float x, float y, float w, float h)`

### Functions

#### `strlen`

```kale
extern int strlen(string s);
```

#### `printf`

```kale
extern int printf(string fmt, ...);
```

#### `malloc`

```kale
extern void* malloc(int size);
```

#### `run_tracker`

```kale
fn void run_tracker()
```

#### `main_entry`

```kale
fn int main_entry()
```

---
