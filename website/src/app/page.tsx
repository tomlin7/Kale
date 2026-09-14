"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { PROJECTS } from "@/data/projects";
import {
  ArrowRight,
  ArrowUpRight,
  Code,
  Terminal,
  GitBranch,
  Browsers,
  SquareHalf,
  AppWindow,
  Broadcast,
  Globe,
  Database,
  Package,
  Cpu,
  Pulse,
  TerminalWindow,
  Eye,
  SpeakerHigh,
  Atom,
  ShieldCheck,
  FileCode,
  Archive,
  Columns,
  IconProps,
} from "@phosphor-icons/react";

const PROJECT_ICONS: Record<string, React.ComponentType<IconProps>> = {
  compiler: Code,
  editor: Terminal,
  vcs: GitBranch,
  gui: Browsers,
  render: SquareHalf,
  framework: AppWindow,
  net: Broadcast,
  web: Globe,
  sql: Database,
  std: Package,
  sys: Cpu,
  sysmon: Pulse,
  term: TerminalWindow,
  fs_watch: Eye,
  audio: SpeakerHigh,
  physics: Atom,
  tls: ShieldCheck,
  lsp: FileCode,
  pkg: Archive,
};

export default function HomePage() {
  return (
    <div className="w-full min-h-screen bg-[#162b6b] text-white pb-24">
      {/* Top Minimalist Header & Master Hero Bento */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-10 pb-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* Left 7 Columns: Minimalist Statement + Abstract Pipeline Schematic */}
          <div className="lg:col-span-7 p-6 sm:p-8 rounded-[6px] bg-[#0d173d] border border-[#243b82] flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-[6px] border border-white/20 bg-[#162b6b] text-xs font-mono text-white/80">
                <Columns size={14} weight="regular" className="text-white" />
                <span>KALE AUTONOMOUS ECOSYSTEM</span>
              </div>

              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-renaissance font-normal tracking-tight text-white leading-tight">
                Architectural Precision. <br />
                Deterministic Execution.
              </h1>

              <p className="text-sm sm:text-base text-white/80 leading-relaxed max-w-xl font-normal">
                An autonomous systems language engineered without legacy compromise. Direct LLVM IR compilation, stack-allocated primitives, and native hardware interop.
              </p>

              {/* Minimalist White Accent Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <Link
                  href="/projects/compiler"
                  className="px-4 py-2 rounded-[6px] bg-white text-[#162b6b] font-medium text-xs hover:bg-white/90 transition-colors flex items-center gap-2"
                >
                  <span>Explore Compiler</span>
                  <ArrowRight size={14} weight="bold" />
                </Link>
                <Link
                  href="/projects/editor"
                  className="px-4 py-2 rounded-[6px] bg-[#162b6b] border border-white/30 text-white font-normal text-xs hover:border-white transition-colors"
                >
                  <span>Flagship Editor</span>
                </Link>
              </div>
            </div>

            {/* Abstract Graphic: Compiler Pipeline Schematic */}
            <div className="pt-6 border-t border-[#243b82] space-y-2">
              <div className="text-[10px] uppercase font-mono tracking-wider text-white/60">
                Deterministic Translation Pipeline
              </div>
              <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 overflow-x-auto">
                <svg viewBox="0 0 540 50" className="w-full h-12 text-white" fill="none">
                  {/* Pipeline Nodes */}
                  <rect x="5" y="10" width="80" height="30" rx="3" stroke="rgba(255,255,255,0.4)" strokeWidth="1" fill="#0d173d" />
                  <text x="45" y="29" fill="#ffffff" fontSize="10" fontFamily="monospace" textAnchor="middle">Source .kl</text>

                  <path d="M 85 25 L 125 25" stroke="rgba(255,255,255,0.4)" strokeWidth="1" markerEnd="url(#arrow)" />

                  <rect x="125" y="10" width="85" height="30" rx="3" stroke="rgba(255,255,255,0.4)" strokeWidth="1" fill="#0d173d" />
                  <text x="167" y="29" fill="#ffffff" fontSize="10" fontFamily="monospace" textAnchor="middle">AST Binder</text>

                  <path d="M 210 25 L 250 25" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />

                  <rect x="250" y="10" width="90" height="30" rx="3" stroke="rgba(255,255,255,0.4)" strokeWidth="1" fill="#0d173d" />
                  <text x="295" y="29" fill="#ffffff" fontSize="10" fontFamily="monospace" textAnchor="middle">LLVM 18 IR</text>

                  <path d="M 340 25 L 380 25" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />

                  <rect x="380" y="10" width="75" height="30" rx="3" stroke="rgba(255,255,255,0.4)" strokeWidth="1" fill="#0d173d" />
                  <text x="417" y="29" fill="#ffffff" fontSize="10" fontFamily="monospace" textAnchor="middle">LLD Link</text>

                  <path d="M 455 25 L 485 25" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />

                  <rect x="485" y="10" width="50" height="30" rx="3" stroke="white" strokeWidth="1" fill="#162b6b" />
                  <text x="510" y="29" fill="#ffffff" fontSize="10" fontFamily="monospace" textAnchor="middle">x86_64</text>
                </svg>
              </div>
            </div>
          </div>

          {/* Right 5 Columns: Master Classical Lithograph Artwork */}
          <div className="lg:col-span-5 rounded-[6px] bg-[#0d173d] border border-[#243b82] p-3 flex flex-col justify-between">
            <div className="relative rounded-[6px] overflow-hidden border border-white/10 w-full aspect-[3/4]">
              <Image
                src="/assets/kale_hero_classical.jpg"
                alt="Classical Architectural Lithograph"
                fill
                className="object-cover"
                priority
              />
            </div>
            <div className="pt-3 flex items-center justify-between text-xs font-mono text-white/70 px-1">
              <span>CLASSICAL PERFECTION</span>
              <span>ANNO MMXXVI</span>
            </div>
          </div>
        </div>
      </section>

      {/* Abstract Architectural Bentos Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Bento 1: Memory Layout Abstract Graphic */}
          <div className="p-5 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono text-white/60">Memory Model</span>
              <Cpu size={16} weight="regular" className="text-white" />
            </div>
            <h3 className="text-sm font-medium text-white">Stack Primitives</h3>
            {/* Abstract Graphic: Stack Frame Allocation */}
            <div className="p-2.5 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-[10px] text-white/80 space-y-1">
              <div className="border border-white/20 p-1 text-center bg-[#162b6b]">0x7FFE00: Struct [f32; 4]</div>
              <div className="border border-white/20 p-1 text-center bg-[#162b6b]">0x7FFDF0: PieceTable Entry</div>
              <div className="border border-white/20 p-1 text-center bg-[#0d173d]">0x7FFDE0: Stack Frame Base</div>
            </div>
            <p className="text-xs text-white/70 leading-relaxed">
              Zero garbage collection pause. Struct values and arrays stack allocated with deterministic deallocation.
            </p>
          </div>

          {/* Bento 2: Frame Timing Abstract Graphic */}
          <div className="p-5 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono text-white/60">GPU Frame Budget</span>
              <Terminal size={16} weight="regular" className="text-white" />
            </div>
            <h3 className="text-sm font-medium text-white">144Hz Latency</h3>
            {/* Abstract Graphic: Frame Timeline */}
            <div className="p-2.5 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1.5">
              <div className="flex justify-between text-[10px] font-mono text-white/60">
                <span>Input: 0.8ms</span>
                <span>Budget: 6.94ms</span>
              </div>
              <div className="w-full h-2 rounded-[2px] bg-[#162b6b] overflow-hidden border border-white/20">
                <div className="h-full bg-white w-1/4"></div>
              </div>
              <div className="flex justify-between text-[9px] font-mono text-white/70">
                <span>Buffer Edit</span>
                <span>Atlas Quad Batch</span>
                <span>VSync</span>
              </div>
            </div>
            <p className="text-xs text-white/70 leading-relaxed">
              Piece Table buffer coupled with dynamic stb_truetype atlasing rendered in a single draw call.
            </p>
          </div>

          {/* Bento 3: Bare Metal OS Graphic */}
          <div className="p-5 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono text-white/60">Hardware Layer</span>
              <Atom size={16} weight="regular" className="text-white" />
            </div>
            <h3 className="text-sm font-medium text-white">Bare-Metal x86_64</h3>
            {/* Abstract Graphic: Multiboot Framebuffer */}
            <div className="p-2.5 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-[10px] text-white/80 space-y-1">
              <div className="flex items-center justify-between border-b border-white/10 pb-1">
                <span>Long Mode</span>
                <span className="text-white">64-bit</span>
              </div>
              <div className="flex items-center justify-between border-b border-white/10 pb-1">
                <span>Page Frames</span>
                <span className="text-white">4 KB Alloc</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Framebuffer</span>
                <span className="text-white">Direct LFB</span>
              </div>
            </div>
            <p className="text-xs text-white/70 leading-relaxed">
              Multiboot loader and IDT dispatcher running directly on physical hardware without host OS dependencies.
            </p>
          </div>

          {/* Bento 4: Distributed VCS Graphic */}
          <div className="p-5 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono text-white/60">Version Control</span>
              <GitBranch size={16} weight="regular" className="text-white" />
            </div>
            <h3 className="text-sm font-medium text-white">Git-Compatible VCS</h3>
            {/* Abstract Graphic: Commit DAG */}
            <div className="p-2.5 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-[10px] text-white/80 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-[2px] bg-white"></span>
                <span>C1 (Tree)</span>
              </div>
              <span>──&gt;</span>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-[2px] bg-white"></span>
                <span>C2 (Commit)</span>
              </div>
              <span>──&gt;</span>
              <span className="text-white">HEAD</span>
            </div>
            <p className="text-xs text-white/70 leading-relaxed">
              Native Git object database, SHA-1 tree packing, and distributed revision history written in pure Kale.
            </p>
          </div>
        </div>
      </section>

      {/* Monorepo Projects Registry Bento Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-10">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-6 pb-3 border-b border-[#243b82]">
          <div>
            <span className="text-xs uppercase font-mono tracking-widest text-white/60">
              The Grand Monorepo Registry
            </span>
            <h2 className="text-2xl font-renaissance font-normal text-white mt-1">
              Select an Architectural Pillar
            </h2>
          </div>
          <p className="text-xs text-white/60 font-mono mt-1 sm:mt-0">
            18 Autonomous Modules • Native x86_64
          </p>
        </div>

        {/* Minimalist Cards Grid (STRICTLY NO CARD HOVER ANIMATIONS) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {PROJECTS.map((project) => {
            const IconComponent = PROJECT_ICONS[project.slug] || Columns;

            return (
              <Link
                key={project.slug}
                href={`/projects/${project.slug}`}
                className="rounded-[6px] bg-[#0d173d] border border-[#243b82] p-5 flex flex-col justify-between space-y-4 hover:border-white/50 transition-colors"
              >
                {/* Header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-[6px] bg-[#162b6b] border border-white/20 text-white flex items-center justify-center">
                      <IconComponent size={16} weight="regular" />
                    </div>
                    <span className="text-[11px] font-mono text-white/60">
                      Pillar {project.romanNumeral}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-[6px] bg-[#162b6b] border border-white/20 text-white/80">
                    {project.version}
                  </span>
                </div>

                {/* Title & Path */}
                <div>
                  <h3 className="text-base font-normal text-white font-renaissance">
                    {project.name}
                  </h3>
                  <p className="text-xs text-white/60 font-mono mt-0.5">
                    {project.path}
                  </p>
                </div>

                {/* Tagline */}
                <p className="text-xs text-white/80 line-clamp-2 leading-relaxed font-normal">
                  {project.tagline}
                </p>

                {/* Action footer */}
                <div className="pt-3 border-t border-[#243b82] flex items-center justify-between text-xs text-white/80 font-normal">
                  <span>Inspect Blueprint & Code</span>
                  <ArrowUpRight size={14} weight="bold" className="text-white" />
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
