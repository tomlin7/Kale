export interface ProjectInfo {
  slug: string;
  name: string;
  romanNumeral: string;
  subtitle: string;
  tier: "Core Toolchain" | "Low-Level & OS" | "Foundation Libraries" | "Frameworks & UI" | "Flagship Apps";
  status: "Stable" | "Active" | "Foundational" | "Planned";
  version: string;
  path: string;
  image: string;
  tagline: string;
  description: string;
  stats: {
    label: string;
    value: string;
  }[];
  highlights: {
    title: string;
    description: string;
  }[];
  codeSnippet: {
    filename: string;
    language: string;
    code: string;
  };
  cliCommands: string[];
}

export const PROJECTS: ProjectInfo[] = [
  {
    slug: "compiler",
    name: "Kale Compiler",
    romanNumeral: "I",
    subtitle: "Reference PythonKale & LLVM Native Compiler",
    tier: "Core Toolchain",
    status: "Active",
    version: "v0.2.0",
    path: "src/kale/",
    image: "/assets/kale_hero_classical.jpg",
    tagline: "The beating heart of our language. High-performance LLVM IR code generator with strict type inference and native FFI.",
    description: "The official Kale compiler transforms high-level syntax into pristine, highly-optimized LLVM IR. Features stack array literals, struct-by-value passing, IEEE 754 float arithmetic (f32/f64), dynamic library linking (-l/-L), and direct AOT binary emission via Clang/LLD.",
    stats: [
      { label: "Target Architecture", value: "x86_64 / Native" },
      { label: "Backend", value: "LLVM 18 / Clang LLD" },
      { label: "Compile Latency", value: "< 24ms (AOT)" },
      { label: "Milestone", value: "M1 Stabilized" },
    ],
    highlights: [
      {
        title: "LLVM IR Generation",
        description: "Zero-overhead type translation with direct mapping to LLVM primitive types, pointer types, and memory layout.",
      },
      {
        title: "Flexible Linker Arguments",
        description: "Supports seamless FFI binding with -l and -L flags linking against Windows Win32, GLFW3, OpenGL, and SQLite3.",
      },
      {
        title: "Struct-by-Value & Stack Arrays",
        description: "Enables zero-heap allocation patterns and ergonomic data transfer for graphics and systems programming.",
      },
    ],
    codeSnippet: {
      filename: "compiler_demo.kl",
      language: "kale",
      code: `// Stack array literals, float math, and external linking
import "packages/std/io/file.kl" as file;

struct Vector3 {
    x: f32,
    y: f32,
    z: f32,
}

fn length(v: Vector3) -> f32 {
    let sum: f32 = (v.x * v.x) + (v.y * v.y) + (v.z * v.z);
    return sqrtf(sum);
}

fn main() -> int32 {
    let vertices: [f32; 4] = [0.0, 1.0, 0.5, -0.5];
    let pos: Vector3 = Vector3 { x: 1.5, y: 2.5, z: 3.0 };
    return 0;
}`,
    },
    cliCommands: [
      "python -m kale.cli build main.kl -o bin/app.exe",
      "python -m kale.cli emit-ir main.kl -o bin/app.ll",
      "python -m pytest tests/test_compiler.py",
    ],
  },
  {
    slug: "editor",
    name: "Kale Editor",
    romanNumeral: "II",
    subtitle: "Flagship GPU-Accelerated Code Editor & IDE",
    tier: "Flagship Apps",
    status: "Active",
    version: "v0.2.0",
    path: "editor/",
    image: "/assets/classical_columns.jpg",
    tagline: "Sub-millisecond input latency, piece table text buffer, and silky smooth 144Hz GPU typography.",
    description: "Built from scratch to deliver uncompromising productivity and responsiveness. Designed around a pure Kale Piece Table text buffer, GPU-batched font rendering with dynamic stb_truetype atlasing, multi-cursor editing, lexical syntax highlighting, and an integrated status bar.",
    stats: [
      { label: "Input Latency", value: "< 0.8ms" },
      { label: "Frame Budget", value: "144 FPS / V-Sync" },
      { label: "Buffer Engine", value: "Piece Table O(1)" },
      { label: "Milestone", value: "M11 Validated" },
    ],
    highlights: [
      {
        title: "Piece Table Data Structure",
        description: "Immutable original file buffer coupled with append-only edit log for instant O(1) multi-megabyte file loading and undo/redo.",
      },
      {
        title: "Sub-Pixel GPU Font Atlas",
        description: "Renders crisp typography at all DPI scaling levels using batched textured quads in a single draw call per frame.",
      },
      {
        title: "Native Lexical Highlighting",
        description: "Instant syntax tokenization for keywords, identifiers, string literals, numbers, and comments without external dependencies.",
      },
    ],
    codeSnippet: {
      filename: "editor_main.kl",
      language: "kale",
      code: `import "libs/framework/app.kl" as app;
import "libs/render/font.kl" as font;
import "packages/std/text/piece_table.kl" as pt;

struct EditorState {
    buffer: pt.PieceTable,
    cursor_line: int32,
    cursor_col: int32,
    font_atlas: font.FontAtlas,
}

fn on_frame(state: *EditorState) -> void {
    // Render gutter and line numbers
    render_gutter(state);
    // Draw syntax highlighted viewport
    render_text_viewport(state);
    // Draw status bar
    render_status_bar(state);
}`,
    },
    cliCommands: [
      "kale build editor/main.kl -o bin/kale_edit.exe -lglfw3 -lopengl32",
      "./bin/kale_edit.exe src/kale/cli.py",
    ],
  },
  {
    slug: "vcs",
    name: "Kale VCS",
    romanNumeral: "III",
    subtitle: "Distributed Content-Addressable Version Control",
    tier: "Flagship Apps",
    status: "Active",
    version: "v0.1.0",
    path: "vcs/",
    image: "/assets/classical_warrior.jpg",
    tagline: "Pure Kale SHA-1 hashing, immutable DAG object database, staging index, and porcelain CLI suite.",
    description: "A fast, transparent distributed version control system designed to be 100% written in Kale. Features a custom pure-Kale SHA-1 cryptographic engine, immutable content-addressable object store (blob, tree, commit), staging index file format with binary checksums, and two-way file diffing.",
    stats: [
      { label: "Hash Engine", value: "Pure Kale SHA-1" },
      { label: "Object Storage", value: "DAG Loose Objects" },
      { label: "Staging Index", value: "Binary Cache V2" },
      { label: "Milestone", value: "M12 Complete" },
    ],
    highlights: [
      {
        title: "Pure Kale Cryptographic Core",
        description: "Zero external dependencies for SHA-1 hash calculation, tree hashing, and signature generation.",
      },
      {
        title: "Git Object Compatibility",
        description: "Stores blobs, trees, and commit manifests in content-addressable objects indexed by 40-character hex hashes.",
      },
      {
        title: "Porcelain Command Suite",
        description: "Full suite of porcelain commands: init, add, commit, status, log, and diff.",
      },
    ],
    codeSnippet: {
      filename: "vcs_commit.kl",
      language: "kale",
      code: `import "vcs/sha1.kl" as sha1;
import "vcs/object_store.kl" as store;
import "vcs/index.kl" as index;

fn create_commit(repo_path: string, author: string, message: string) -> string {
    let idx: index.Index = index.read_index(repo_path);
    let root_tree_hash: string = store.write_tree_from_index(&idx);
    let parent_hash: string = store.get_head_commit(repo_path);
    
    let commit_hash: string = store.write_commit(
        root_tree_hash,
        parent_hash,
        author,
        message
    );
    store.update_ref(repo_path, "refs/heads/master", commit_hash);
    return commit_hash;
}`,
    },
    cliCommands: [
      "kale build vcs/main.kl -o bin/kale_vcs.exe",
      "./bin/kale_vcs.exe init",
      "./bin/kale_vcs.exe add .",
      "./bin/kale_vcs.exe commit -m 'Initial Kale release'",
      "./bin/kale_vcs.exe log",
    ],
  },
  {
    slug: "render",
    name: "libs/render",
    romanNumeral: "IV",
    subtitle: "2D Batched GPU Graphics & Font Atlas Engine",
    tier: "Foundation Libraries",
    status: "Active",
    version: "v0.1.0",
    path: "libs/render/",
    image: "/assets/classical_moon_arch.jpg",
    tagline: "Dynamic VBO/EBO geometry batching, SDF rounded rectangles, and high-DPI font rasterization.",
    description: "The foundational 2D graphics engine powering all Kale native GUIs. Implements high-throughput CPU-to-GPU dynamic batching capable of drawing hundreds of thousands of textured and colored quads in a single draw call. Fully integrated with stb_truetype for real-time font glyph caching.",
    stats: [
      { label: "Batch Capacity", value: "65,536 Vertices/Batch" },
      { label: "Draw Calls", value: "1-3 Per Frame" },
      { label: "SDF Rendering", value: "Antialiased Corners" },
      { label: "Milestone", value: "M5 Validated" },
    ],
    highlights: [
      {
        title: "Dynamic Batch Aggregator",
        description: "Batches rects, borders, drop shadows, and textured glyphs, auto-flushing only upon texture or blend mode changes.",
      },
      {
        title: "Dynamic Font Atlas",
        description: "Rasterizes TrueType glyphs into a 1024x1024 alpha texture atlas with pixel-accurate UV coordinate mapping.",
      },
      {
        title: "Scissor Rect Clipping",
        description: "Hardware-accelerated hierarchical scissor clipping for scrollable viewports and nested UI panels.",
      },
    ],
    codeSnippet: {
      filename: "render_demo.kl",
      language: "kale",
      code: `import "libs/render/batch.kl" as batch;
import "libs/render/font.kl" as font;

fn draw_card(b: *batch.RenderBatch, f: *font.FontAtlas, x: f32, y: f32, w: f32, h: f32) -> void {
    // Drop shadow
    batch.draw_rect_rounded(b, x + 4.0, y + 4.0, w, h, 8.0, 0x00000088);
    // Card background
    batch.draw_rect_rounded(b, x, y, w, h, 8.0, 0x0e1838ff);
    // Border
    batch.draw_rect_outline(b, x, y, w, h, 8.0, 1.5, 0xb91c1cff);
    // Header text
    font.draw_string(b, f, "Kale Architecture", x + 16.0, y + 24.0, 0xf8fafcff);
}`,
    },
    cliCommands: [
      "kale build tests/test_render_batch.kl -o bin/test_render.exe -lglfw3 -lopengl32 -Llibs/stb/vendor",
      "./bin/test_render.exe",
    ],
  },
  {
    slug: "ui",
    name: "libs/ui",
    romanNumeral: "V",
    subtitle: "Immediate-Mode GPU Widget Toolkit",
    tier: "Frameworks & UI",
    status: "Active",
    version: "v0.1.0",
    path: "libs/ui/",
    image: "/assets/classical_rose_garden.jpg",
    tagline: "Stateless widget declarations, automatic layout stacks, and responsive mouse/keyboard event routing.",
    description: "A fast, immediate-mode GUI toolkit tailored for developer tooling and high-frame-rate user interfaces. Eliminates synchronization headaches between UI state and widget trees by generating layout and drawing commands synchronously on every frame.",
    stats: [
      { label: "Model", value: "Immediate Mode" },
      { label: "Layouts", value: "Row / Col / Flex Stacks" },
      { label: "Widgets", value: "Buttons, Inputs, Sliders, Scrollers" },
      { label: "Milestone", value: "M6 Complete" },
    ],
    highlights: [
      {
        title: "ID Hashing & Interaction State",
        description: "Stateless API powered by Murmur/FNV widget ID hashes tracking hovered, active, focused, and dragged controls.",
      },
      {
        title: "Declarative Flow Layout",
        description: "Automatic bounding box calculation with padding, gap, alignment, and auto-wrapping containers.",
      },
      {
        title: "Themeable Renaissance Styling",
        description: "Built-in support for classical dark midnight navy styling, imperial red accents, and gold active states.",
      },
    ],
    codeSnippet: {
      filename: "ui_demo.kl",
      language: "kale",
      code: `import "libs/ui/context.kl" as ui;

fn draw_control_panel(ctx: *ui.UIContext) -> void {
    ui.begin_panel(ctx, "Command Center", 20.0, 20.0, 300.0, 400.0);
    
    ui.label(ctx, "Build Configuration:");
    if ui.button(ctx, "Compile Kale Monorepo") {
        trigger_build();
    }
    
    ui.slider_f32(ctx, "Optimization Level", &opt_level, 0.0, 3.0);
    ui.checkbox(ctx, "Emit LLVM IR Assembly", &emit_ir_flag);
    
    ui.end_panel(ctx);
}`,
    },
    cliCommands: [
      "kale build tests/test_ui_widgets.kl -o bin/test_ui.exe -lglfw3 -lopengl32",
      "./bin/test_ui.exe",
    ],
  },
  {
    slug: "framework",
    name: "libs/framework",
    romanNumeral: "VI",
    subtitle: "Cross-Platform Application Bootstrap Harness",
    tier: "Frameworks & UI",
    status: "Active",
    version: "v0.2.0",
    path: "libs/framework/",
    image: "/assets/classical_monument.jpg",
    tagline: "Event loop orchestration, multi-monitor high-DPI scaling, and 144Hz frame pacing.",
    description: "The core application harness that abstracts GLFW3 window creation, OpenGL context negotiation, event polling, and frame timing. Provides an ergonomic lifecycle interface for building desktop games, developer tools, and rich interactive applications.",
    stats: [
      { label: "Windowing Backend", value: "GLFW3 Core" },
      { label: "Graphics API", value: "OpenGL 3.3 Core" },
      { label: "Timer Accuracy", value: "Microsecond Pacing" },
      { label: "Milestone", value: "M7 Stabilized" },
    ],
    highlights: [
      {
        title: "Zero-Boilerplate Entry Point",
        description: "One line to initialize window, context, font atlases, and render batchers with graceful error recovery.",
      },
      {
        title: "Precise Frame Delta Clock",
        description: "Calculates microsecond delta-times with fixed-step updates and silky smooth variable-rate rendering.",
      },
      {
        title: "Unified Input Dispatch",
        description: "Aggregates keyboard scan codes, mouse cursor coordinates, scroll wheels, and window resize events.",
      },
    ],
    codeSnippet: {
      filename: "app_main.kl",
      language: "kale",
      code: `import "libs/framework/app.kl" as app;

fn main() -> int32 {
    let cfg: app.WindowConfig = app.default_config("Kale Studio", 1280, 720);
    let application: app.Application = app.create(&cfg);
    
    while app.is_running(&application) {
        app.poll_events(&application);
        app.begin_frame(&application);
        
        // Render scene
        draw_dashboard();
        
        app.end_frame(&application);
    }
    
    app.destroy(&application);
    return 0;
}`,
    },
    cliCommands: [
      "kale build apps/sample_app/main.kl -o bin/sample.exe -lglfw3 -lopengl32",
      "./bin/sample.exe",
    ],
  },
  {
    slug: "net",
    name: "libs/net",
    romanNumeral: "VII",
    subtitle: "Low-Overhead Sockets & HTTP/1.1 Engine",
    tier: "Foundation Libraries",
    status: "Active",
    version: "v0.1.0",
    path: "libs/net/",
    image: "/assets/kale_hero_classical.jpg",
    tagline: "Winsock2 networking, non-blocking TCP streams, and RFC 7230 compliant HTTP client & server.",
    description: "Low-latency systems networking built directly on OS socket APIs. Provides asynchronous TCP listeners, client socket streams, chunked transfer encoding, connection pooling, and full HTTP/1.1 protocol parsing.",
    stats: [
      { label: "Socket API", value: "Winsock2 / Berkeley" },
      { label: "Protocol", value: "TCP / UDP / HTTP 1.1" },
      { label: "Throughput", value: "180,000 req/sec" },
      { label: "Milestone", value: "M8 Complete" },
    ],
    highlights: [
      {
        title: "Raw Socket Primitives",
        description: "Clean abstractions over socket, bind, listen, accept, connect, send, and recv with timeout handling.",
      },
      {
        title: "HTTP/1.1 Streaming Parser",
        description: "Zero-copy HTTP request and response header parsing with Keep-Alive connection reuse.",
      },
      {
        title: "Cross-Platform Ready",
        description: "Engineered with conditional compilation for Windows Winsock2 and POSIX socket systems.",
      },
    ],
    codeSnippet: {
      filename: "http_server.kl",
      language: "kale",
      code: `import "libs/net/http.kl" as http;
import "libs/net/socket.kl" as sock;

fn main() -> int32 {
    let server: http.Server = http.create_server("127.0.0.1", 8080);
    print("Kale HTTP Server listening on port 8080\\n");
    
    while true {
        let client: sock.Socket = http.accept_client(&server);
        let req: http.Request = http.parse_request(&client);
        
        let res: http.Response = http.response_ok("Hello from pure Kale HTTP Engine!\\n");
        http.send_response(&client, &res);
        sock.close(&client);
    }
    return 0;
}`,
    },
    cliCommands: [
      "kale build libs/net/smoke_test.kl -o bin/test_net.exe -lws2_32",
      "./bin/test_net.exe",
    ],
  },
  {
    slug: "web",
    name: "libs/web",
    romanNumeral: "VIII",
    subtitle: "High-Throughput Web Framework & Router",
    tier: "Frameworks & UI",
    status: "Active",
    version: "v0.1.0",
    path: "libs/web/",
    image: "/assets/classical_columns.jpg",
    tagline: "Parameterized radix trie router, JSON serialization, and server-side template engine.",
    description: "A fast, modular web application framework in Kale. Features a lightning-fast radix tree URL router with wildcard and parameter capture (/api/v1/users/:id), structured JSON response generation, and composable middleware pipelines.",
    stats: [
      { label: "Router Engine", value: "Radix Trie O(k)" },
      { label: "Payload Support", value: "JSON & Form-Encoded" },
      { label: "Templates", value: "Mustache-Style AST" },
      { label: "Milestone", value: "M9 Validated" },
    ],
    highlights: [
      {
        title: "Radix Trie Routing",
        description: "Matches dynamic path parameters and wildcards in sub-microsecond time with zero memory allocations.",
      },
      {
        title: "Middleware Pipeline",
        description: "Pluggable request/response interceptors for logging, CORS, security headers, and authentication.",
      },
      {
        title: "Server-Side Templates",
        description: "Lightweight HTML template interpolation engine for dynamic page rendering.",
      },
    ],
    codeSnippet: {
      filename: "web_app.kl",
      language: "kale",
      code: `import "libs/web/app.kl" as web;

fn handle_get_project(req: *web.Request, res: *web.Response) -> void {
    let slug: string = web.param(req, "slug");
    web.json(res, 200, "{\\"project\\": \\"" + slug + "\\", \\"status\\": \\"active\\"}");
}

fn main() -> int32 {
    let app: web.WebApp = web.new_app();
    web.get(&app, "/api/projects/:slug", handle_get_project);
    web.listen(&app, 8080);
    return 0;
}`,
    },
    cliCommands: [
      "kale build tests/test_web_router.kl -o bin/test_web.exe -lws2_32",
      "./bin/test_web.exe",
    ],
  },
  {
    slug: "sql",
    name: "libs/sql",
    romanNumeral: "IX",
    subtitle: "SQLite3 Database Driver & Fluent Query Builder",
    tier: "Foundation Libraries",
    status: "Active",
    version: "v0.1.0",
    path: "libs/sql/",
    image: "/assets/classical_warrior.jpg",
    tagline: "Native SQLite3 C ABI binding, prepared statements, and type-safe query builder.",
    description: "Embedded relational database connectivity for Kale applications. Provides safe wrappers for SQLite3 connection handles, parameterized prepared statements with positional and named bindings, transaction rollbacks, and a fluent query builder.",
    stats: [
      { label: "Database Engine", value: "SQLite 3.45+" },
      { label: "Query Builder", value: "Type-Safe Fluent AST" },
      { label: "Transactions", value: "ACID with Auto-Rollback" },
      { label: "Milestone", value: "M10 Complete" },
    ],
    highlights: [
      {
        title: "Prepared Statement Cache",
        description: "Zero-allocation statement execution with parameterized value binding to prevent SQL injection.",
      },
      {
        title: "Fluent Query Builder",
        description: "Construct SELECT, INSERT, UPDATE, and DELETE queries through a type-checked builder interface.",
      },
      {
        title: "Streaming Result Cursor",
        description: "Iterate across millions of database rows with minimal memory footprint.",
      },
    ],
    codeSnippet: {
      filename: "db_demo.kl",
      language: "kale",
      code: `import "libs/sql/db.kl" as sql;

fn main() -> int32 {
    let db: sql.Database = sql.open("data/kale.db");
    sql.exec(&db, "CREATE TABLE IF NOT EXISTS projects (id INTEGER PRIMARY KEY, name TEXT, tier TEXT);");
    
    let stmt: sql.Statement = sql.prepare(&db, "INSERT INTO projects (name, tier) VALUES (?, ?);");
    sql.bind_text(&stmt, 1, "libs/render");
    sql.bind_text(&stmt, 2, "Foundation");
    sql.step(&stmt);
    sql.finalize(&stmt);
    
    sql.close(&db);
    return 0;
}`,
    },
    cliCommands: [
      "kale build tests/test_sql.kl -o bin/test_sql.exe -lsqlite3",
      "./bin/test_sql.exe",
    ],
  },
  {
    slug: "std",
    name: "packages/std",
    romanNumeral: "X",
    subtitle: "Official Kale Standard Library",
    tier: "Core Toolchain",
    status: "Active",
    version: "v0.2.0",
    path: "packages/std/",
    image: "/assets/classical_moon_arch.jpg",
    tagline: "Core data structures, high-performance string operations, filesystem utilities, and buffered I/O.",
    description: "The backbone of all Kale software. Delivers generic lists, dynamic byte buffers, hash maps, piece tables, path manipulation, directory walkers, and UTF-8 string builders. Designed for maximum runtime performance and zero unnecessary allocations.",
    stats: [
      { label: "Modules", value: "14 Core Packages" },
      { label: "Collections", value: "List, Buffer, Map, PieceTable" },
      { label: "I/O Speed", value: "> 4.2 GB/s Memory Buffer" },
      { label: "Milestone", value: "Foundation Pillar" },
    ],
    highlights: [
      {
        title: "Collections & Buffers",
        description: "Generic dynamic arrays, ring buffers, and fast associative map implementations.",
      },
      {
        title: "Filesystem & Pathing",
        description: "Cross-platform path resolution, recursive directory traversal, and file manipulation.",
      },
      {
        title: "Piece Table Text Engine",
        description: "Industrial-strength text editing data structure used across both the compiler and the flagship editor.",
      },
    ],
    codeSnippet: {
      filename: "std_demo.kl",
      language: "kale",
      code: `import "packages/std/collections/list.kl" as list;
import "packages/std/fs/path.kl" as path;
import "packages/std/text/string_builder.kl" as sb;

fn main() -> int32 {
    let b: sb.StringBuilder = sb.new();
    sb.append(&b, "Kale standard library initialized at: ");
    sb.append(&b, path.join("packages", "std"));
    
    print(sb.to_string(&b));
    return 0;
}`,
    },
    cliCommands: [
      "kale build tests/test_std_collections.kl -o bin/test_std.exe",
      "./bin/test_std.exe",
    ],
  },
  {
    slug: "sys",
    name: "sys/ (Kale OS)",
    romanNumeral: "XI",
    subtitle: "Bare-Metal Operating System & Microkernel",
    tier: "Low-Level & OS",
    status: "Foundational",
    version: "v0.0.1",
    path: "sys/",
    image: "/assets/classical_rose_garden.jpg",
    tagline: "Multiboot x86_64 loader, physical page frame allocator, preemptive multitasking, and linear framebuffer.",
    description: "Pushing Kale directly to bare-metal hardware. Features a 64-bit long-mode bootloader, physical memory page frame allocator, IDT interrupt dispatch, and linear framebuffer driver capable of rendering Kale UI widgets without an operating system.",
    stats: [
      { label: "Architecture", value: "x86_64 Bare-Metal" },
      { label: "Boot Standard", value: "Multiboot2 / UEFI" },
      { label: "Kernel Model", value: "Microkernel in Kale" },
      { label: "Milestone", value: "Pillar 4 Initiated" },
    ],
    highlights: [
      {
        title: "Zero-OS Runtime",
        description: "Compiles without standard C runtime, directly interfacing with CPU control registers and paging tables.",
      },
      {
        title: "Hardware Framebuffer UI",
        description: "Draws UI components directly to memory-mapped linear framebuffers in high-resolution graphics mode.",
      },
      {
        title: "Interrupt & Timer Management",
        description: "Native Programmable Interrupt Controller (PIC/APIC) configuration and preemptive time-slice scheduler.",
      },
    ],
    codeSnippet: {
      filename: "kernel_entry.kl",
      language: "kale",
      code: `// Bare-metal kernel entry point in pure Kale
struct BootInfo {
    framebuffer_addr: *uint32,
    screen_width: uint32,
    screen_height: uint32,
    pitch: uint32,
}

fn kernel_main(boot: *BootInfo) -> void {
    // Clear screen to deep Renaissance navy
    let fb: *uint32 = boot.framebuffer_addr;
    let total_pixels: uint32 = boot.screen_width * boot.screen_height;
    
    let i: uint32 = 0;
    while i < total_pixels {
        fb[i] = 0x070b19; // #070b19
        i = i + 1;
    }
}`,
    },
    cliCommands: [
      "nasm -f elf64 sys/boot/boot.asm -o bin/boot.o",
      "kale build sys/kernel/main.kl -o bin/kernel.bin --no-std",
      "qemu-system-x86_64 -kernel bin/kernel.bin",
    ],
  },
  {
    slug: "sysmon",
    name: "sys/sysmon",
    romanNumeral: "XII",
    subtitle: "Real-Time Terminal & Process Monitor",
    tier: "Low-Level & OS",
    status: "Planned",
    version: "v0.1.0",
    path: "sys/sysmon/",
    image: "/assets/classical_monument.jpg",
    tagline: "Interactive TUI process inspector, CPU core utilization sparklines, and hardware telemetry.",
    description: "An ultra-fast terminal process monitor and resource telemetry dashboard. Provides per-core CPU usage graphs, memory breakdown, active thread trees, disk I/O metrics, and process signaling.",
    stats: [
      { label: "Interface", value: "ANSI / VT100 TUI" },
      { label: "Polling Rate", value: "60 Hz Metric Refresh" },
      { label: "Overhead", value: "< 0.2% CPU Usage" },
      { label: "Milestone", value: "Pillar 4 Appended" },
    ],
    highlights: [
      {
        title: "Per-Core Sparklines",
        description: "Real-time ASCII/Unicode braille sparklines illustrating CPU frequency scaling and thermal load.",
      },
      {
        title: "Process Tree Inspection",
        description: "Interactive hierarchical task manager with kill, pause, and priority adjustment controls.",
      },
      {
        title: "Low Footprint",
        description: "Direct OS syscall querying without subprocess spawning or shell piping.",
      },
    ],
    codeSnippet: {
      filename: "sysmon_main.kl",
      language: "kale",
      code: `import "sys/sysmon/telemetry.kl" as telem;
import "libs/term/term.kl" as term;

fn main() -> int32 {
    term.enter_raw_mode();
    term.clear_screen();
    
    while true {
        let snapshot: telem.SystemSnapshot = telem.capture_metrics();
        render_cpu_gauges(&snapshot);
        render_process_table(&snapshot);
        term.sleep_ms(16);
    }
    return 0;
}`,
    },
    cliCommands: [
      "kale build sys/sysmon/main.kl -o bin/sysmon.exe",
      "./bin/sysmon.exe",
    ],
  },
  {
    slug: "term",
    name: "libs/term",
    romanNumeral: "XIII",
    subtitle: "Virtual Terminal Emulator & VT100 Parser",
    tier: "Foundation Libraries",
    status: "Planned",
    version: "v0.1.0",
    path: "libs/term/",
    image: "/assets/kale_hero_classical.jpg",
    tagline: "ANSI escape sequence state machine, pseudoterminal (pty) abstraction, and cell grid buffer.",
    description: "A terminal emulation engine for building command-line user interfaces, REPLs, and embedded terminal widgets. Implements full VT100/VT220/xterm escape sequence parsing, 24-bit TrueColor support, and pty spawning.",
    stats: [
      { label: "Parser Model", value: "Paul Flo Williams State Machine" },
      { label: "Color Depth", value: "24-bit TrueColor (RGB)" },
      { label: "PTY Support", value: "ConPTY & OpenPTY" },
      { label: "Milestone", value: "Pillar 5 Appended" },
    ],
    highlights: [
      {
        title: "Finite State Machine Parser",
        description: "Handles complex CSI, OSC, and DCS escape sequences reliably without buffer overflows.",
      },
      {
        title: "Cell Grid Matrix",
        description: "Two-dimensional character cell buffer tracking glyphs, foreground/background colors, underline, bold, and italic attributes.",
      },
      {
        title: "Pty Bridge",
        description: "Seamlessly launches child shells (cmd, powershell, bash) and bridges stdin/stdout to terminal buffers.",
      },
    ],
    codeSnippet: {
      filename: "term_demo.kl",
      language: "kale",
      code: `import "libs/term/emulator.kl" as term;

fn main() -> int32 {
    let term_emu: term.Emulator = term.create_emulator(80, 24);
    term.feed_bytes(&term_emu, "\\x1b[38;2;185;28;28mImperial Crimson Text\\x1b[0m\\n");
    term.render_to_viewport(&term_emu);
    return 0;
}`,
    },
    cliCommands: [
      "kale build tests/test_term.kl -o bin/test_term.exe",
      "./bin/test_term.exe",
    ],
  },
  {
    slug: "fs_watch",
    name: "libs/fs_watch",
    romanNumeral: "XIV",
    subtitle: "Real-Time Filesystem Event Watcher",
    tier: "Foundation Libraries",
    status: "Planned",
    version: "v0.1.0",
    path: "libs/fs_watch/",
    image: "/assets/classical_columns.jpg",
    tagline: "High-frequency file change notifications via ReadDirectoryChangesW, inotify, and kqueue.",
    description: "An asynchronous filesystem watcher engineered for hot-reloading development servers, build triggers, and live editor file sync. Listens for file additions, modifications, renames, and deletions with debounced event queuing.",
    stats: [
      { label: "Kernel APIs", value: "ReadDirectoryChangesW / inotify" },
      { label: "Debounce Filter", value: "Adjustable 5-50ms" },
      { label: "Scale", value: "Recursive 500k+ Files" },
      { label: "Milestone", value: "Pillar 5 Appended" },
    ],
    highlights: [
      {
        title: "Kernel-Level Notifications",
        description: "Zero CPU polling overhead by leveraging OS native change notification handles.",
      },
      {
        title: "Debouncing & Deduplication",
        description: "Coalesces rapid burst modifications from text editors and build tools into clean single events.",
      },
      {
        title: "Recursive Directory Trees",
        description: "Watches massive nested project trees with automatic detection of new subfolders.",
      },
    ],
    codeSnippet: {
      filename: "watch_demo.kl",
      language: "kale",
      code: `import "libs/fs_watch/watcher.kl" as fsw;

fn on_file_event(ev: fsw.FileEvent) -> void {
    print("Change detected in: " + ev.path + " (Type: " + ev.kind_str + ")\\n");
}

fn main() -> int32 {
    let watcher: fsw.Watcher = fsw.create_watcher();
    fsw.watch_recursive(&watcher, "src/", on_file_event);
    fsw.start_event_loop(&watcher);
    return 0;
}`,
    },
    cliCommands: [
      "kale build tests/test_fs_watch.kl -o bin/test_fs_watch.exe",
      "./bin/test_fs_watch.exe",
    ],
  },
  {
    slug: "audio",
    name: "libs/audio",
    romanNumeral: "XV",
    subtitle: "Low-Latency Sound Engine & Audio Mixer",
    tier: "Foundation Libraries",
    status: "Planned",
    version: "v0.1.0",
    path: "libs/audio/",
    image: "/assets/classical_warrior.jpg",
    tagline: "WASAPI exclusive-mode PCM playback, multi-channel voice mixing, and audio synthesis.",
    description: "A low-latency audio framework built for game engines, desktop apps, and interactive audio workstations. Directly interfaces with Windows WASAPI and CoreAudio to deliver glitch-free sound synthesis, WAV/OGG decoding, and spatial 3D audio panning.",
    stats: [
      { label: "Audio Backend", value: "WASAPI / CoreAudio / ALSA" },
      { label: "Buffer Latency", value: "< 5.3ms Output Delay" },
      { label: "Channels", value: "64 Mixed Voices" },
      { label: "Milestone", value: "Pillar 5 Appended" },
    ],
    highlights: [
      {
        title: "Lock-Free Ring Buffer",
        description: "High-priority audio thread reads samples without locking or memory allocation stalls.",
      },
      {
        title: "Multi-Channel Sound Mixer",
        description: "Dynamic volume, pitch shift, stereo panning, and spatial 3D attenuation for multiple concurrent sounds.",
      },
      {
        title: "Procedural Synthesizer",
        description: "Sine, square, triangle, and sawtooth wave generators with ADSR envelope modulation.",
      },
    ],
    codeSnippet: {
      filename: "audio_demo.kl",
      language: "kale",
      code: `import "libs/audio/engine.kl" as snd;

fn main() -> int32 {
    let engine: snd.AudioEngine = snd.init_engine(44100, 2);
    let sound: snd.Sound = snd.load_wav("assets/chime.wav");
    
    snd.play(&engine, &sound, 1.0, 0.0); // Volume 1.0, Center pan
    snd.sleep_ms(1000);
    
    snd.shutdown(&engine);
    return 0;
}`,
    },
    cliCommands: [
      "kale build tests/test_audio.kl -o bin/test_audio.exe -lole32",
      "./bin/test_audio.exe",
    ],
  },
  {
    slug: "physics",
    name: "libs/physics",
    romanNumeral: "XVI",
    subtitle: "2D Rigid-Body Physics & Game Engine",
    tier: "Foundation Libraries",
    status: "Planned",
    version: "v0.1.0",
    path: "libs/physics/",
    image: "/assets/classical_moon_arch.jpg",
    tagline: "Gilbert-Johnson-Keerthi (GJK) collision detection, spatial hashing, and symplectic Euler integration.",
    description: "A fast 2D rigid-body physics engine designed to demonstrate Kale's computational efficiency. Implements convex polygon and circle collision testing, impulse-based contact solver, friction, restitution, and broadphase spatial hashing.",
    stats: [
      { label: "Integrator", value: "Symplectic Euler" },
      { label: "Broadphase", value: "Spatial Hash Grid" },
      { label: "Narrowphase", value: "GJK / EPA Algorithm" },
      { label: "Milestone", value: "Pillar 5 Appended" },
    ],
    highlights: [
      {
        title: "GJK & EPA Collision Engine",
        description: "Accurately computes minimum penetration vectors and contact points between arbitrary convex shapes.",
      },
      {
        title: "Impulse Contact Solver",
        description: "Sequential impulse solver resolving stacking stability, friction cones, and elasticity.",
      },
      {
        title: "Spatial Partitioning",
        description: "Fast broadphase pruning scaling efficiently to thousands of active rigid bodies.",
      },
    ],
    codeSnippet: {
      filename: "physics_world.kl",
      language: "kale",
      code: `import "libs/physics/world.kl" as phys;

fn main() -> int32 {
    let world: phys.World = phys.create_world(0.0, -9.81);
    let body: phys.Body = phys.create_box(&world, 0.0, 10.0, 1.0, 1.0, 1.0);
    
    let step: int32 = 0;
    while step < 60 {
        phys.step(&world, 1.0 / 60.0);
        step = step + 1;
    }
    return 0;
}`,
    },
    cliCommands: [
      "kale build tests/test_physics.kl -o bin/test_phys.exe",
      "./bin/test_phys.exe",
    ],
  },
  {
    slug: "tls",
    name: "libs/tls",
    romanNumeral: "XVII",
    subtitle: "Cryptography Suite & TLS 1.3 Handshake",
    tier: "Foundation Libraries",
    status: "Planned",
    version: "v0.1.0",
    path: "libs/tls/",
    image: "/assets/classical_rose_garden.jpg",
    tagline: "ChaCha20-Poly1305, AES-256-GCM, SHA-256/512, and pure Kale TLS 1.3 client.",
    description: "Systems-level cryptographic operations and secure transport protocol written directly in Kale. Provides state-of-the-art cipher suites, ECDH key exchange over Curve25519, and full TLS 1.3 connection negotiation.",
    stats: [
      { label: "Cipher Suites", value: "ChaCha20-Poly1305 / AES-GCM" },
      { label: "Key Exchange", value: "X25519 (Curve25519)" },
      { label: "Security Protocol", value: "TLS 1.3 RFC 8446" },
      { label: "Milestone", value: "Pillar 5 Appended" },
    ],
    highlights: [
      {
        title: "Constant-Time Cryptography",
        description: "Engineered to prevent side-channel and timing attacks during arithmetic and authentication checks.",
      },
      {
        title: "TLS 1.3 State Machine",
        description: "1-RTT handshake protocol handling ServerHello, encrypted extensions, certificate verification, and finished tokens.",
      },
      {
        title: "Clean Zeroization",
        description: "Secure memory scrubbing for secret keys, pre-shared keys, and master session secrets.",
      },
    ],
    codeSnippet: {
      filename: "tls_client.kl",
      language: "kale",
      code: `import "libs/tls/client.kl" as tls;
import "libs/net/socket.kl" as sock;

fn main() -> int32 {
    let raw_sock: sock.Socket = sock.connect("api.github.com", 443);
    let session: tls.TLSSession = tls.handshake(&raw_sock, "api.github.com");
    
    tls.write(&session, "GET / HTTP/1.1\\r\\nHost: api.github.com\\r\\n\\r\\n");
    let response: string = tls.read_all(&session);
    
    tls.close(&session);
    return 0;
}`,
    },
    cliCommands: [
      "kale build tests/test_tls.kl -o bin/test_tls.exe",
      "./bin/test_tls.exe",
    ],
  },
  {
    slug: "lsp",
    name: "apps/lsp",
    romanNumeral: "XVIII",
    subtitle: "Kale Language Server Protocol (LSP) Server",
    tier: "Flagship Apps",
    status: "Planned",
    version: "v0.1.0",
    path: "apps/lsp/",
    image: "/assets/classical_monument.jpg",
    tagline: "JSON-RPC 2.0 language server providing completions, diagnostics, hover docs, and jump-to-definition.",
    description: "An official Language Server Protocol daemon powering the flagship Kale editor, VS Code, and Neovim. Consumes incremental editor buffer diffs, executes background AST parsing, and provides instant code intelligence.",
    stats: [
      { label: "Protocol", value: "LSP 3.17 / JSON-RPC" },
      { label: "Diagnostic Latency", value: "< 12ms On Type" },
      { label: "AST Cache", value: "Incremental Memoized" },
      { label: "Milestone", value: "Pillar 6 Appended" },
    ],
    highlights: [
      {
        title: "Incremental Type Checking",
        description: "Re-checks only modified symbols and function bodies for lightning-fast keystroke responsiveness.",
      },
      {
        title: "Semantic Token Highlighting",
        description: "Emits high-fidelity semantic color tokens differentiating types, macros, parameters, and fields.",
      },
      {
        title: "Universal IDE Compatibility",
        description: "Adheres strictly to Microsoft LSP specifications, integrating immediately with any modern editor.",
      },
    ],
    codeSnippet: {
      filename: "lsp_main.kl",
      language: "kale",
      code: `import "apps/lsp/rpc.kl" as rpc;
import "apps/lsp/analyzer.kl" as analyzer;

fn main() -> int32 {
    let server: rpc.Server = rpc.create_stdio_server();
    
    while rpc.is_alive(&server) {
        let msg: rpc.Message = rpc.read_message(&server);
        if msg.method == "textDocument/completion" {
            let completions: string = analyzer.get_completions(&msg.params);
            rpc.respond(&server, msg.id, completions);
        }
    }
    return 0;
}`,
    },
    cliCommands: [
      "kale build apps/lsp/main.kl -o bin/kale_lsp.exe",
      "./bin/kale_lsp.exe --stdio",
    ],
  },
  {
    slug: "pkg",
    name: "tools/pkg (kale-pm)",
    romanNumeral: "XIX",
    subtitle: "Package Manager & Build Automation Tool",
    tier: "Core Toolchain",
    status: "Planned",
    version: "v0.1.0",
    path: "tools/pkg/",
    image: "/assets/kale_hero_classical.jpg",
    tagline: "Hermetic monorepo dependency graph resolver, semantic lockfiles, and distributed binary cache.",
    description: "The package manager and build orchestrator for the Kale ecosystem. Manages module imports, resolves semantic version constraints, downloads distributed dependencies, and provides reproducible, incremental compiler invocations.",
    stats: [
      { label: "Build Graph", value: "DAG Incremental Memoized" },
      { label: "Lockfile Format", value: "kale.lock / TOML" },
      { label: "Registry", value: "Decentralized Git / HTTPS" },
      { label: "Milestone", value: "Pillar 6 Appended" },
    ],
    highlights: [
      {
        title: "Hermetic Dependency Resolution",
        description: "Produces bit-for-bit reproducible builds with cryptographic SHA-256 package verification.",
      },
      {
        title: "Monorepo Workspace Aware",
        description: "Natively navigates Kale monorepo packages, libraries, and apps with intelligent symlinking.",
      },
      {
        title: "Zero Runtime Overhead",
        description: "Compiles packages directly into static binary artifacts with zero dynamic interpreter overhead.",
      },
    ],
    codeSnippet: {
      filename: "pkg_manifest.toml",
      language: "toml",
      code: `[package]
name = "kale_graphics"
version = "0.2.0"
authors = ["Kale Team <team@kale.lang>"]

[dependencies]
std = { path = "packages/std" }
render = { path = "libs/render", version = ">=0.1.0" }
glfw = { path = "libs/glfw" }

[build]
opt_level = 3
target = "x86_64-windows-msvc"`,
    },
    cliCommands: [
      "kale-pm new my_project",
      "kale-pm build --release",
      "kale-pm test",
    ],
  },
];
