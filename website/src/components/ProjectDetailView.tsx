"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { ProjectInfo, PROJECTS } from "@/data/projects";
import {
  TerminalWindow,
  Stack,
  CheckCircle,
  ShieldCheck,
  ArrowSquareOut,
  CaretLeft,
  CaretRight,
  Code,
} from "@phosphor-icons/react";

function HatchingOverlay() {
  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-[0.08]" fill="none">
      <defs>
        <pattern id="detail-hatch" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke="#ffffff" strokeWidth="1" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#detail-hatch)" />
    </svg>
  );
}

export function ProjectDetailView({ project }: { project: ProjectInfo }) {
  const currentIndex = PROJECTS.findIndex((p) => p.slug === project.slug);
  const prevProject = currentIndex > 0 ? PROJECTS[currentIndex - 1] : PROJECTS[PROJECTS.length - 1];
  const nextProject = currentIndex < PROJECTS.length - 1 ? PROJECTS[currentIndex + 1] : PROJECTS[0];

  const secondaryImg = project.secondaryImage || "/assets/kaleimages/HR-35WubIAAt3Wd.jpg";

  return (
    <div className="w-full min-h-screen pb-32 bg-[#162b6b] text-white">
      {/* Top Breadcrumb Header (No filler text) */}
      <section className="w-full border-b border-[#243b82] bg-[#0d173d] py-5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-xs font-mono text-white/70">
            <Link href="/" className="hover:text-white transition-colors">
              Monorepo
            </Link>
            <span>/</span>
            <span>{project.tier}</span>
            <span>/</span>
            <span className="text-white font-medium">{project.name}</span>
          </div>

          <div className="flex items-center gap-3">
            <span className="px-2.5 py-1 rounded-[6px] bg-[#162b6b] border border-white/20 text-xs font-mono text-white">
              {project.version} • {project.status}
            </span>
            <a
              href={`https://github.com/tomlin7/kale/tree/master/${project.path}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-[6px] bg-white text-[#162b6b] text-xs font-medium hover:bg-white/90 transition-colors"
            >
              <span>Source Code</span>
              <ArrowSquareOut size={14} weight="bold" />
            </a>
          </div>
        </div>
      </section>

      {/* Main Content Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-8 space-y-8">
        {/* 1. MASTER UNIFIED HERO CARD (Image fills top, bottom, and right ends fully with ZERO margins) */}
        <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden grid grid-cols-1 lg:grid-cols-12 items-stretch relative">
          <HatchingOverlay />

          {/* Left 7 Columns: Technical Specifications */}
          <div className="lg:col-span-7 p-8 sm:p-10 flex flex-col justify-between space-y-6 z-10">
            <div className="space-y-4">
              <div className="text-xs font-mono text-white/60 uppercase tracking-wider">
                {project.path}
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-renaissance font-normal tracking-tight text-white leading-tight">
                {project.name}
              </h1>

              <p className="text-base text-white/90 font-normal">
                {project.subtitle}
              </p>

              <p className="text-sm text-white/80 leading-relaxed max-w-2xl font-normal">
                {project.description}
              </p>
            </div>

            {/* Quick Metrics Tiles */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-6 border-t border-[#243b82]">
              {project.stats.map((stat, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-[6px] bg-[#162b6b] border border-white/10 flex flex-col"
                >
                  <span className="text-[10px] uppercase font-mono tracking-wider text-white/60">
                    {stat.label}
                  </span>
                  <span className="text-sm font-medium text-white mt-1">
                    {stat.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Right 5 Columns: Image fills top, bottom, and right ends with ZERO margins */}
          <div className="lg:col-span-5 relative min-h-[440px] lg:min-h-full border-t lg:border-t-0 lg:border-l border-[#243b82]">
            <Image
              src={project.image}
              alt={project.name}
              fill
              className="object-cover object-center"
              priority
            />
          </div>
        </div>

        {/* 2. DOMAIN-SPECIFIC TECHNICAL LAYOUT (Varying architecture per category) */}
        {project.tier === "Core Toolchain" && (
          <div className="space-y-8">
            {/* Translation Pipeline Bento */}
            <div className="p-6 sm:p-8 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-4 relative overflow-hidden">
              <HatchingOverlay />
              <div className="flex items-center justify-between">
                <div className="text-sm font-renaissance font-normal text-white">
                  Compiler Internal Stages
                </div>
                <div className="text-xs font-mono text-white/60">AOT Emission Latency &lt; 24ms</div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-3 pt-2">
                <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1">
                  <div className="text-[10px] font-mono text-white/50">STAGE 1</div>
                  <div className="text-xs font-medium text-white">Lexer & Token Stream</div>
                  <div className="text-[11px] text-white/70">Single-pass UTF-8 scanner with zero allocations</div>
                </div>
                <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1">
                  <div className="text-[10px] font-mono text-white/50">STAGE 2</div>
                  <div className="text-xs font-medium text-white">Parser & AST Tree</div>
                  <div className="text-[11px] text-white/70">Recursive descent parser emitting strict typed AST nodes</div>
                </div>
                <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1">
                  <div className="text-[10px] font-mono text-white/50">STAGE 3</div>
                  <div className="text-xs font-medium text-white">Type Binder & Inference</div>
                  <div className="text-[11px] text-white/70">Symbol resolution, struct layout, and type deduction</div>
                </div>
                <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1">
                  <div className="text-[10px] font-mono text-white/50">STAGE 4</div>
                  <div className="text-xs font-medium text-white">LLVM IR Emitter</div>
                  <div className="text-[11px] text-white/70">LLVM 18 IR generation linked directly via Clang/LLD</div>
                </div>
              </div>
            </div>

            {/* Split Card with Secondary Image Filling Right Half */}
            <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden grid grid-cols-1 lg:grid-cols-12 items-stretch">
              <div className="lg:col-span-7 p-8 space-y-4">
                <div className="text-xs font-mono text-white/60 uppercase">Native C ABI Linker</div>
                <h3 className="text-2xl font-renaissance font-normal text-white">
                  Zero-Overhead Foreign Function Interface
                </h3>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                  Kale links directly against native C dynamic libraries with no runtime marshaling wrapper. Functions declared with extern symbols resolve directly through the platform loader (kernel32, user32, opengl32, glfw3, sqlite3).
                </p>
                <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-xs text-white/90">
                  <div className="text-white/50 text-[10px]">{"// Linker Flags"}</div>
                  <div>python -m kale.cli build main.kl -o bin/app.exe -lglfw3 -lopengl32 -lsqlite3</div>
                </div>
              </div>
              <div className="lg:col-span-5 relative min-h-[300px] border-t lg:border-t-0 lg:border-l border-[#243b82]">
                <Image
                  src={secondaryImg}
                  alt="Compiler Hardware Architecture"
                  fill
                  className="object-cover object-center"
                />
              </div>
            </div>
          </div>
        )}

        {(project.tier === "Flagship Apps" || project.tier === "Frameworks & UI") && (
          <div className="space-y-8">
            {/* 144Hz Latency & Frame Pacing Schematic Bento */}
            <div className="p-6 sm:p-8 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-4 relative overflow-hidden">
              <HatchingOverlay />
              <div className="flex items-center justify-between">
                <div className="text-sm font-renaissance font-normal text-white">
                  Frame Budget & Event Loop
                </div>
                <div className="text-xs font-mono text-white/60">Target: 144 FPS (6.94ms per frame)</div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-2">
                  <div className="text-xs font-medium text-white">1. Input Polling (0.2ms)</div>
                  <div className="w-full h-1.5 bg-[#162b6b] rounded-[2px] overflow-hidden">
                    <div className="h-full bg-white w-[15%]"></div>
                  </div>
                  <div className="text-[11px] text-white/70">Raw keyboard & mouse events polled via GLFW3 callbacks</div>
                </div>
                <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-2">
                  <div className="text-xs font-medium text-white">2. Piece Table Mutation (0.4ms)</div>
                  <div className="w-full h-1.5 bg-[#162b6b] rounded-[2px] overflow-hidden">
                    <div className="h-full bg-white w-[30%]"></div>
                  </div>
                  <div className="text-[11px] text-white/70">Append-only buffer edit with instant O(1) undo/redo stack</div>
                </div>
                <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-2">
                  <div className="text-xs font-medium text-white">3. GPU Batched Quad Draw (0.8ms)</div>
                  <div className="w-full h-1.5 bg-[#162b6b] rounded-[2px] overflow-hidden">
                    <div className="h-full bg-white w-[50%]"></div>
                  </div>
                  <div className="text-[11px] text-white/70">Dynamic font atlas textures rendered in single GPU draw call</div>
                </div>
              </div>
            </div>

            {/* Split Card with Secondary Image Filling Left Half */}
            <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden grid grid-cols-1 lg:grid-cols-12 items-stretch">
              <div className="lg:col-span-5 relative min-h-[300px] border-b lg:border-b-0 lg:border-r border-[#243b82]">
                <Image
                  src={secondaryImg}
                  alt="Graphics Engine Architecture"
                  fill
                  className="object-cover object-center"
                />
              </div>
              <div className="lg:col-span-7 p-8 space-y-4">
                <div className="text-xs font-mono text-white/60 uppercase">Piece Table Buffer Engine</div>
                <h3 className="text-2xl font-renaissance font-normal text-white">
                  Sub-Millisecond Multi-Cursor Editing
                </h3>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                  Unlike line-array or gap-buffer architectures, the Kale Piece Table holds an immutable original file buffer coupled with an append-only edit buffer. Loading a 100MB file takes under 1ms because no memory copying occurs.
                </p>
                <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-xs text-white/90">
                  <div>Buffer Type: Immutable File Span + Append-Only Log</div>
                  <div className="text-white/60 text-[11px] mt-1">Undo/Redo: Zero heap copy • O(1) pointer adjustment</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {project.tier === "Low-Level & OS" && (
          <div className="space-y-8">
            {/* Physical Memory Architecture Bento */}
            <div className="p-6 sm:p-8 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-4 relative overflow-hidden">
              <HatchingOverlay />
              <div className="flex items-center justify-between">
                <div className="text-sm font-renaissance font-normal text-white">
                  Physical Memory Page Frame Architecture
                </div>
                <div className="text-xs font-mono text-white/60">x86_64 4-Level Paging (PML4)</div>
              </div>

              <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-xs text-white/90 space-y-2">
                <div className="flex justify-between border-b border-white/10 pb-2 text-[11px] text-white/60">
                  <span>VIRTUAL ADDRESS RANGE</span>
                  <span>MAPPING & PRIVILEGE</span>
                  <span>PURPOSE</span>
                </div>
                <div className="flex justify-between">
                  <span>0x00000000 - 0x000FFFFF</span>
                  <span className="text-white">Kernel Ring 0</span>
                  <span>1MB Real Mode & BIOS Area</span>
                </div>
                <div className="flex justify-between">
                  <span>0x00100000 - 0x00FFFFFF</span>
                  <span className="text-white">Kernel Ring 0</span>
                  <span>Kernel Binary & Frame Allocator</span>
                </div>
                <div className="flex justify-between">
                  <span>0xFD000000 - 0xFE000000</span>
                  <span className="text-white">Hardware MMIO</span>
                  <span>Linear Framebuffer (1920x1080)</span>
                </div>
              </div>
            </div>

            {/* Split Card with Secondary Image */}
            <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden grid grid-cols-1 lg:grid-cols-12 items-stretch">
              <div className="lg:col-span-7 p-8 space-y-4">
                <div className="text-xs font-mono text-white/60 uppercase">Bare-Metal Runtime</div>
                <h3 className="text-2xl font-renaissance font-normal text-white">
                  Hardware Linear Framebuffer
                </h3>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                  The microkernel boots via standard Multiboot header, transitions the CPU to 64-bit long mode, programs the Interrupt Descriptor Table (IDT), and renders Kale UI widgets directly onto the physical display controller.
                </p>
                <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-xs text-white/90">
                  <div>Boot Protocol: Multiboot 1 / 2 • Target: x86_64 ELF64</div>
                  <div className="text-white/60 text-[11px] mt-1">Direct Hardware Framebuffer • No OS dependencies</div>
                </div>
              </div>
              <div className="lg:col-span-5 relative min-h-[300px] border-t lg:border-t-0 lg:border-l border-[#243b82]">
                <Image
                  src={secondaryImg}
                  alt="Microkernel Architecture"
                  fill
                  className="object-cover object-center"
                />
              </div>
            </div>
          </div>
        )}

        {project.tier === "Foundation Libraries" && (
          <div className="space-y-8">
            {/* Protocol & Data Structure Schematic Bento */}
            <div className="p-6 sm:p-8 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-4 relative overflow-hidden">
              <HatchingOverlay />
              <div className="flex items-center justify-between">
                <div className="text-sm font-renaissance font-normal text-white">
                  Protocol & Wire Format Architecture
                </div>
                <div className="text-xs font-mono text-white/60">Zero-Heap Allocation Primitives</div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
                <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1">
                  <div className="text-xs font-medium text-white">Deterministic Memory</div>
                  <div className="text-[11px] text-white/70">Buffer allocations are bound to caller lifecycle with zero heap fragmentation</div>
                </div>
                <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1">
                  <div className="text-xs font-medium text-white">RFC Wire Conformance</div>
                  <div className="text-[11px] text-white/70">Strict binary packet layout and protocol compliance written in pure Kale</div>
                </div>
                <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1">
                  <div className="text-xs font-medium text-white">Monorepo Integration</div>
                  <div className="text-[11px] text-white/70">Instantly consumable by Compiler, Editor, and Bare-Metal targets</div>
                </div>
              </div>
            </div>

            {/* Split Card with Secondary Image */}
            <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden grid grid-cols-1 lg:grid-cols-12 items-stretch">
              <div className="lg:col-span-7 p-8 space-y-4">
                <div className="text-xs font-mono text-white/60 uppercase">Architecture Contract</div>
                <h3 className="text-2xl font-renaissance font-normal text-white">
                  High-Throughput Systems Foundation
                </h3>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                  Engineered to maximize CPU instruction pipelining and data cache locality. Every algorithm avoids heap pointer indirection wherever contiguous stack or arena buffers can be employed.
                </p>
                <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-xs text-white/90">
                  <div>Verification: 138/138 Regression Suite Pass</div>
                  <div className="text-white/60 text-[11px] mt-1">Signed commit governance • Strict type safety</div>
                </div>
              </div>
              <div className="lg:col-span-5 relative min-h-[300px] border-t lg:border-t-0 lg:border-l border-[#243b82]">
                <Image
                  src={secondaryImg}
                  alt="Systems Foundation"
                  fill
                  className="object-cover object-center"
                />
              </div>
            </div>
          </div>
        )}

        {/* 3. CANONICAL IMPLEMENTATION CODEBLOCK & CLI DIRECTIVES */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
          {/* Left 7 Columns: Codeblock in #0a1333 */}
          <div className="lg:col-span-7 rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden flex flex-col">
            <div className="px-5 py-3 bg-[#0a1333] border-b border-[#243b82] flex items-center justify-between text-xs font-mono text-white">
              <div className="flex items-center gap-2">
                <Code size={16} weight="regular" className="text-white" />
                <span className="font-medium">{project.codeSnippet.filename}</span>
              </div>
              <span className="uppercase text-[10px] text-white/60 tracking-wider">
                {project.codeSnippet.language}
              </span>
            </div>
            <pre className="p-5 text-xs sm:text-sm font-mono text-white bg-[#0a1333] overflow-x-auto leading-relaxed flex-1">
              <code>{project.codeSnippet.code}</code>
            </pre>
          </div>

          {/* Right 5 Columns: CLI Compilation Directives */}
          <div className="lg:col-span-5 p-6 sm:p-8 rounded-[6px] bg-[#0d173d] border border-[#243b82] flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-sm font-renaissance font-normal text-white">
                <TerminalWindow size={18} weight="regular" className="text-white" />
                <span>Compilation & Linker Directives</span>
              </div>
              <p className="text-xs text-white/70 leading-relaxed font-normal">
                Deterministic command-line invocations to build, link native dynamic dependencies, and run automated regression tests:
              </p>
              <div className="space-y-2 pt-1">
                {project.cliCommands.map((cmd, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-xs text-white overflow-x-auto flex items-center gap-2"
                  >
                    <span className="text-white/40 select-none">$</span>
                    <code>{cmd}</code>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-[#243b82] space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-white">
                <ShieldCheck size={16} weight="regular" className="text-white" />
                <span>Monorepo Governance</span>
              </div>
              <p className="text-xs text-white/70">
                GPG Key <span className="font-mono text-white">1B917D4779A6102E</span> • Continuous integration with automated symbol verification.
              </p>
            </div>
          </div>
        </div>

        {/* 4. ARCHITECTURAL CAPABILITIES GRID */}
        <div className="p-6 sm:p-8 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-4 relative overflow-hidden">
          <HatchingOverlay />
          <div className="flex items-center gap-2 text-sm font-renaissance font-normal text-white">
            <Stack size={18} weight="regular" className="text-white" />
            <span>Architectural Capabilities</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            {project.highlights.map((h, i) => (
              <div
                key={i}
                className="p-5 rounded-[6px] bg-[#162b6b] border border-white/10 flex flex-col justify-between"
              >
                <div className="flex items-center gap-2 text-sm font-medium text-white">
                  <CheckCircle size={16} weight="regular" className="text-white flex-shrink-0" />
                  <span>{h.title}</span>
                </div>
                <p className="text-xs text-white/80 mt-2.5 leading-relaxed font-normal">
                  {h.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* 5. FOOTER NAVIGATION (Prev / Next Modules) */}
        <div className="grid grid-cols-2 gap-4 pt-4">
          <Link
            href={`/projects/${prevProject.slug}`}
            className="p-5 rounded-[6px] bg-[#0d173d] border border-[#243b82] hover:border-white/50 text-left transition-colors flex items-center justify-between"
          >
            <div>
              <span className="text-[10px] uppercase font-mono text-white/60 block">
                ← Previous Module
              </span>
              <span className="text-sm font-normal text-white block mt-1">
                {prevProject.name}
              </span>
            </div>
            <CaretLeft size={18} weight="bold" className="text-white" />
          </Link>

          <Link
            href={`/projects/${nextProject.slug}`}
            className="p-5 rounded-[6px] bg-[#0d173d] border border-[#243b82] hover:border-white/50 text-right transition-colors flex items-center justify-between"
          >
            <CaretRight size={18} weight="bold" className="text-white" />
            <div>
              <span className="text-[10px] uppercase font-mono text-white/60 block">
                Next Module →
              </span>
              <span className="text-sm font-normal text-white block mt-1">
                {nextProject.name}
              </span>
            </div>
          </Link>
        </div>
      </main>
    </div>
  );
}
