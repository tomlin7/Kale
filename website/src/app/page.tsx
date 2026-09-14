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
  GithubLogo,
  XLogo,
  Key,
  Sparkle,
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

function HatchingOverlay() {
  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-[0.08]" fill="none">
      <defs>
        <pattern id="hatch-pattern" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke="#ffffff" strokeWidth="1" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#hatch-pattern)" />
    </svg>
  );
}

/**
 * Metaphysical Art (Giorgio de Chirico) & Moebius Comic Graphic Illustration
 * Procedural SVG composed with native SVG feTurbulence (Perlin noise) filters.
 * Features:
 * - Stark Roman / Metaphysical arcade colonnade with receding linear perspective
 * - Exaggerated dramatic cast shadows across an uncanny empty plaza
 * - High-contrast digital color blocking (stark white stone, vermilion red monolith, midnight blue shadows)
 * - Moebius-style stippling and ink contour lines
 * - Native fractal Perlin noise grain texture
 */
function MetaphysicalPerlinGraphic() {
  return (
    <svg
      viewBox="0 0 700 380"
      className="w-full h-full object-cover select-none"
      preserveAspectRatio="xMidYMid slice"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        {/* Procedural Perlin Noise Filter (Stipple / Grain Texture) */}
        <filter id="perlin-grain" x="0%" y="0%" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" result="noise" />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 1
                    0 0 0 0 1
                    0 0 0 0 1
                    0 0 0 0.15 0"
            result="coloredNoise"
          />
          <feComposite operator="in" in2="SourceGraphic" />
        </filter>

        {/* Dense Metaphysical Plinth Perlin Noise */}
        <filter id="monolith-noise" x="0%" y="0%" width="100%" height="100%">
          <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="4" result="turbulence" />
          <feColorMatrix
            type="matrix"
            values="0 0 0 0 0.05
                    0 0 0 0 0.09
                    0 0 0 0 0.24
                    0 0 0 0.35 0"
          />
        </filter>

        {/* Moebius Stipple Pattern */}
        <pattern id="stipple-dots" width="8" height="8" patternUnits="userSpaceOnUse">
          <circle cx="2" cy="2" r="0.75" fill="#ffffff" fillOpacity="0.4" />
          <circle cx="6" cy="6" r="0.6" fill="#ffffff" fillOpacity="0.3" />
        </pattern>

        {/* Linear Plaza Shadow Gradient */}
        <linearGradient id="plaza-horizon" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="#08102b" />
          <stop offset="35%" stopColor="#0d173d" />
          <stop offset="100%" stopColor="#162b6b" />
        </linearGradient>

        {/* Stark Shadow Gradient for Arches */}
        <linearGradient id="arch-shadow" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#050a1d" />
          <stop offset="100%" stopColor="#0d173d" />
        </linearGradient>
      </defs>

      {/* Sky / Atmospheric Backplane */}
      <rect x="0" y="0" width="700" height="220" fill="#08102b" />

      {/* Surrealist Distant Low Horizon Glow */}
      <rect x="0" y="160" width="700" height="60" fill="#111f4d" />
      <line x1="0" y1="220" x2="700" y2="220" stroke="#ffffff" strokeWidth="1" strokeOpacity="0.3" />

      {/* Metaphysical Plaza Floor with Perspective Grid Lines (Giorgio de Chirico Plaza) */}
      <polygon points="0,220 700,220 700,380 0,380" fill="url(#plaza-horizon)" />
      
      {/* Receding Perspective Orthogonals to Vanishing Point (x=520, y=220) */}
      <g stroke="#ffffff" strokeWidth="0.8" strokeOpacity="0.18">
        <line x1="520" y1="220" x2="-80" y2="380" />
        <line x1="520" y1="220" x2="80" y2="380" />
        <line x1="520" y1="220" x2="240" y2="380" />
        <line x1="520" y1="220" x2="400" y2="380" />
        <line x1="520" y1="220" x2="560" y2="380" />
        <line x1="520" y1="220" x2="720" y2="380" />
        <line x1="520" y1="220" x2="880" y2="380" />
      </g>

      {/* Transverse Perspective Grid Lines */}
      <line x1="0" y1="235" x2="700" y2="235" stroke="#ffffff" strokeWidth="0.6" strokeOpacity="0.12" />
      <line x1="0" y1="260" x2="700" y2="260" stroke="#ffffff" strokeWidth="0.6" strokeOpacity="0.15" />
      <line x1="0" y1="300" x2="700" y2="300" stroke="#ffffff" strokeWidth="0.8" strokeOpacity="0.18" />
      <line x1="0" y1="350" x2="700" y2="350" stroke="#ffffff" strokeWidth="1" strokeOpacity="0.22" />

      {/* --- EXAGGERATED METAPHYSICAL CAST SHADOWS (De Chirico 45-degree harsh shadows) --- */}
      {/* Colonnade cast shadow across the plaza */}
      <polygon
        points="0,220 280,220 460,380 0,380"
        fill="#040816"
        fillOpacity="0.75"
      />
      {/* Monolith / Plinth cast shadow */}
      <polygon
        points="530,220 575,220 670,380 600,380"
        fill="#040816"
        fillOpacity="0.8"
      />

      {/* --- CLASSICAL METAPHYSICAL ARCADE (De Chirico Receding Colonnade) --- */}
      {/* Arcade Wall Body */}
      <polygon
        points="20,40 280,120 280,270 20,330"
        fill="#1e357d"
        stroke="#ffffff"
        strokeWidth="1.5"
      />

      {/* Arch 1 (Foreground, Tallest) */}
      <g>
        {/* Arch interior shadow */}
        <path
          d="M 40,325 L 40,130 Q 75,90 110,130 L 110,310 Z"
          fill="url(#arch-shadow)"
          stroke="#ffffff"
          strokeWidth="1.2"
        />
        {/* Pure Black Inner Void */}
        <path
          d="M 50,322 L 50,140 Q 75,108 100,140 L 100,308 Z"
          fill="#030611"
        />
        {/* Moebius Stipple hatching inside arch */}
        <path
          d="M 50,322 L 50,140 Q 75,108 100,140 L 100,308 Z"
          fill="url(#stipple-dots)"
        />
        {/* Arch Impost & Keystone Accent */}
        <line x1="36" y1="130" x2="114" y2="130" stroke="#ffffff" strokeWidth="1.5" />
        <rect x="71" y="90" width="8" height="12" fill="#ffffff" />
      </g>

      {/* Arch 2 (Middle) */}
      <g>
        <path
          d="M 130,305 L 130,150 Q 158,118 186,150 L 186,290 Z"
          fill="url(#arch-shadow)"
          stroke="#ffffff"
          strokeWidth="1.2"
        />
        <path
          d="M 138,302 L 138,158 Q 158,132 178,158 L 178,288 Z"
          fill="#030611"
        />
        <path
          d="M 138,302 L 138,158 Q 158,132 178,158 L 178,288 Z"
          fill="url(#stipple-dots)"
        />
        <line x1="126" y1="150" x2="190" y2="150" stroke="#ffffff" strokeWidth="1.5" />
        <rect x="154" y="118" width="7" height="10" fill="#ffffff" />
      </g>

      {/* Arch 3 (Background, Receding) */}
      <g>
        <path
          d="M 206,285 L 206,168 Q 228,142 250,168 L 250,274 Z"
          fill="url(#arch-shadow)"
          stroke="#ffffff"
          strokeWidth="1.2"
        />
        <path
          d="M 212,282 L 212,174 Q 228,154 244,174 L 244,272 Z"
          fill="#030611"
        />
        <line x1="202" y1="168" x2="254" y2="168" stroke="#ffffff" strokeWidth="1.5" />
        <rect x="225" y="142" width="6" height="8" fill="#ffffff" />
      </g>

      {/* Arcade Entablature & Roof Cornice */}
      <polygon
        points="15,40 285,120 285,108 15,28"
        fill="#ffffff"
        stroke="#ffffff"
        strokeWidth="1.5"
      />
      <line x1="15" y1="46" x2="285" y2="126" stroke="#0d173d" strokeWidth="1.5" />

      {/* --- SURREALIST PRIMARY COLOR BLOCK MONOLITH (Stark Red / Minimalist Accent) --- */}
      {/* High-contrast geometric plinth */}
      <g>
        {/* Monolith Front Face (Vibrant Vermilion Red) */}
        <polygon
          points="530,120 575,105 575,225 530,240"
          fill="#dc2626"
          stroke="#ffffff"
          strokeWidth="1.5"
        />
        {/* Monolith Top Face (Pure White) */}
        <polygon
          points="530,120 575,105 560,95 515,110"
          fill="#ffffff"
          stroke="#ffffff"
          strokeWidth="1.5"
        />
        {/* Monolith Side Face (Midnight Shadow) */}
        <polygon
          points="515,110 530,120 530,240 515,230"
          fill="#070e24"
          stroke="#ffffff"
          strokeWidth="1.5"
        />
        {/* Perlin noise texture over monolith face */}
        <polygon
          points="530,120 575,105 575,225 530,240"
          fill="#000000"
          fillOpacity="0.1"
          filter="url(#monolith-noise)"
        />
      </g>

      {/* Classical Geometric Sphere / Orb casting shadow (De Chirico Motif) */}
      <g>
        <circle cx="430" cy="275" r="22" fill="#ffffff" stroke="#ffffff" strokeWidth="1.5" />
        <circle cx="430" cy="275" r="22" fill="url(#stipple-dots)" />
        {/* Sphere 3D shading */}
        <path
          d="M 430,253 A 22,22 0 0,1 452,275 A 22,14 0 0,1 430,289 A 22,22 0 0,1 408,275 A 22,22 0 0,1 430,253 Z"
          fill="#0d173d"
          fillOpacity="0.5"
        />
        {/* Ground shadow ellipse */}
        <ellipse cx="448" cy="285" rx="26" ry="7" fill="#040816" fillOpacity="0.7" />
      </g>

      {/* Architectural Chimney / Distant Metaphysical Tower */}
      <polygon
        points="630,70 655,70 655,220 630,220"
        fill="#0d173d"
        stroke="#ffffff"
        strokeWidth="1.2"
      />
      <polygon
        points="625,70 660,70 655,62 630,62"
        fill="#ffffff"
        stroke="#ffffff"
        strokeWidth="1"
      />

      {/* Global Perlin Noise Grain Overlay across the entire artwork */}
      <rect
        x="0"
        y="0"
        width="700"
        height="380"
        fill="#ffffff"
        filter="url(#perlin-grain)"
        pointerEvents="none"
      />

      {/* Frame Border Accent */}
      <rect
        x="1"
        y="1"
        width="698"
        height="378"
        fill="none"
        stroke="#ffffff"
        strokeWidth="1"
        strokeOpacity="0.3"
      />

      {/* Typography Inscription In-Canvas */}
      <text
        x="680"
        y="365"
        fill="#ffffff"
        fillOpacity="0.5"
        fontSize="9"
        fontFamily="monospace"
        textAnchor="end"
      >
        METAPHYSICAL PROCEDURAL MATRIX // PERLIN NOISE &amp; PERSPECTIVE
      </text>
    </svg>
  );
}

export default function HomePage() {
  return (
    <div className="w-full min-h-screen bg-[#162b6b] text-white pb-32">
      {/* 1. MASTER UNIFIED HERO CARD (Image fills top, bottom, and right ends with zero margins) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-8 pb-6">
        <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden grid grid-cols-1 lg:grid-cols-12 items-stretch relative">
          <HatchingOverlay />

          {/* Left 7 Columns: Intro Content */}
          <div className="lg:col-span-7 p-8 sm:p-12 flex flex-col justify-between space-y-8 z-10">
            <div className="space-y-5">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-[6px] border border-white/20 bg-[#162b6b] text-xs font-mono text-white">
                <Columns size={14} weight="regular" className="text-white" />
                <span>AUTONOMOUS MONOREPO ECOSYSTEM</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-renaissance font-normal tracking-tight text-white leading-[1.12]">
                Architectural Precision. <br />
                Deterministic Systems.
              </h1>

              <p className="text-base sm:text-lg text-white/80 leading-relaxed max-w-xl font-normal">
                Kale is an autonomous systems programming language engineered without compromise: direct LLVM 18 IR emission, stack-allocated data structures, zero runtime garbage collection, and sub-millisecond graphics.
              </p>

              {/* White Accent Action Controls */}
              <div className="flex flex-wrap items-center gap-3 pt-3">
                <Link
                  href="/projects/compiler"
                  className="px-5 py-2.5 rounded-[6px] bg-white text-[#162b6b] font-medium text-xs hover:bg-white/90 transition-colors flex items-center gap-2"
                >
                  <span>Compiler Specification</span>
                  <ArrowRight size={14} weight="bold" />
                </Link>
                <Link
                  href="/projects/editor"
                  className="px-5 py-2.5 rounded-[6px] bg-[#162b6b] border border-white/30 text-white font-normal text-xs hover:border-white transition-colors"
                >
                  <span>144Hz Flagship Editor</span>
                </Link>
              </div>
            </div>

            {/* Abstract Graphic: Compiler Pipeline Schematic */}
            <div className="pt-8 border-t border-[#243b82] space-y-2">
              <div className="text-[10px] uppercase font-mono tracking-wider text-white/60">
                Deterministic Compilation Pipeline
              </div>
              <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 overflow-x-auto">
                <svg viewBox="0 0 540 50" className="w-full h-12 text-white" fill="none">
                  <rect x="5" y="10" width="80" height="30" rx="3" stroke="rgba(255,255,255,0.4)" strokeWidth="1" fill="#0d173d" />
                  <text x="45" y="29" fill="#ffffff" fontSize="10" fontFamily="monospace" textAnchor="middle">Source .kl</text>

                  <path d="M 85 25 L 125 25" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />

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

          {/* Right 5 Columns: Image fills top, bottom, and right ends fully with ZERO margins */}
          <div className="lg:col-span-5 relative min-h-[500px] lg:min-h-full border-t lg:border-t-0 lg:border-l border-[#243b82]">
            <Image
              src="/assets/kale_hero_classical.jpg"
              alt="Kale Classical Architecture"
              fill
              className="object-cover object-center"
              priority
            />
          </div>
        </div>
      </section>

      {/* 2. ABSTRACT SYSTEM PRINCIPLES BENTO SECTION */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Bento Tile 1: Memory Model */}
          <div className="p-6 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-4 relative overflow-hidden">
            <HatchingOverlay />
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono text-white/60">Memory Subsystem</span>
              <Cpu size={18} weight="regular" className="text-white" />
            </div>
            <h3 className="text-base font-normal text-white">Stack Primitives</h3>
            <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-[10px] text-white/90 space-y-1.5">
              <div className="border border-white/20 p-1.5 text-center bg-[#162b6b]">0x7FFE00: Struct [f32; 4]</div>
              <div className="border border-white/20 p-1.5 text-center bg-[#162b6b]">0x7FFDF0: PieceTable Entry</div>
              <div className="border border-white/20 p-1.5 text-center bg-[#0d173d]">0x7FFDE0: Base Frame Pointer</div>
            </div>
            <p className="text-xs text-white/70 leading-relaxed">
              No garbage collection pause. Struct values and arrays stack allocated with deterministic deallocation.
            </p>
          </div>

          {/* Bento Tile 2: Frame Timing */}
          <div className="p-6 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-4 relative overflow-hidden">
            <HatchingOverlay />
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono text-white/60">Graphics Pipeline</span>
              <Terminal size={18} weight="regular" className="text-white" />
            </div>
            <h3 className="text-base font-normal text-white">144Hz Latency</h3>
            <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-2">
              <div className="flex justify-between text-[10px] font-mono text-white/70">
                <span>Input: 0.8ms</span>
                <span>Budget: 6.94ms</span>
              </div>
              <div className="w-full h-2 rounded-[2px] bg-[#162b6b] overflow-hidden border border-white/20">
                <div className="h-full bg-white w-1/4"></div>
              </div>
              <div className="flex justify-between text-[9px] font-mono text-white/60">
                <span>Buffer Edit</span>
                <span>Atlas Quad Batch</span>
                <span>VSync</span>
              </div>
            </div>
            <p className="text-xs text-white/70 leading-relaxed">
              Piece Table buffer engine coupled with dynamic stb_truetype atlasing rendered in a single draw call.
            </p>
          </div>

          {/* Bento Tile 3: Bare Metal OS */}
          <div className="p-6 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-4 relative overflow-hidden">
            <HatchingOverlay />
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono text-white/60">Kernel Subsystem</span>
              <Atom size={18} weight="regular" className="text-white" />
            </div>
            <h3 className="text-base font-normal text-white">Bare-Metal x86_64</h3>
            <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-[10px] text-white/90 space-y-1.5">
              <div className="flex items-center justify-between border-b border-white/10 pb-1">
                <span>Execution Mode</span>
                <span className="text-white">64-bit Long Mode</span>
              </div>
              <div className="flex items-center justify-between border-b border-white/10 pb-1">
                <span>Paging</span>
                <span className="text-white">4 KB Physical Frame</span>
              </div>
              <div className="flex items-center justify-between">
                <span>Framebuffer</span>
                <span className="text-white">Direct Linear LFB</span>
              </div>
            </div>
            <p className="text-xs text-white/70 leading-relaxed">
              Multiboot loader and IDT dispatcher running directly on physical hardware without host OS dependencies.
            </p>
          </div>

          {/* Bento Tile 4: Version Control */}
          <div className="p-6 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-4 relative overflow-hidden">
            <HatchingOverlay />
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono text-white/60">Revision Control</span>
              <GitBranch size={18} weight="regular" className="text-white" />
            </div>
            <h3 className="text-base font-normal text-white">Git-Compatible VCS</h3>
            <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-[10px] text-white/90 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-[2px] bg-white"></span>
                <span>Tree (Blob)</span>
              </div>
              <span>──&gt;</span>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-[2px] bg-white"></span>
                <span>Commit</span>
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

      {/* 3. DEEP ARCHITECTURE SHOWCASE (Cards with half-card and 1/3 card edge-to-edge images) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Showcase Card A: Wide Landscape Split Card (Editor & Font Atlas) */}
        <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden grid grid-cols-1 lg:grid-cols-12 items-stretch">
          {/* Left 6 Columns: Image fills left half edge-to-edge */}
          <div className="lg:col-span-6 relative min-h-[380px] lg:min-h-full border-b lg:border-b-0 lg:border-r border-[#243b82]">
            <Image
              src="/assets/kaleimages/HR-35WubIAAt3Wd.jpg"
              alt="Architectural Panorama"
              fill
              className="object-cover object-center"
            />
          </div>

          {/* Right 6 Columns: Engineering Details */}
          <div className="lg:col-span-6 p-8 sm:p-10 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-xs font-mono text-white/70">
                <span>FLAGSHIP TOOL</span>
                <span>/</span>
                <span className="text-white">editor/</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-renaissance font-normal text-white">
                GPU-Batched Typography Engine
              </h2>
              <p className="text-sm text-white/80 leading-relaxed font-normal">
                Text rendering in Kale operates on dynamic stb_truetype bitmap atlasing. Each character glyph is uploaded into a unified texture array at start of frame, and text spans are batched into textured quad arrays drawn in a single state call.
              </p>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10">
                  <div className="text-[10px] uppercase font-mono text-white/60">Input Latency</div>
                  <div className="text-base font-medium text-white mt-0.5">&lt; 0.8ms</div>
                </div>
                <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10">
                  <div className="text-[10px] uppercase font-mono text-white/60">Buffer Speed</div>
                  <div className="text-base font-medium text-white mt-0.5">O(1) Piece Table</div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-[#243b82]">
              <Link
                href="/projects/editor"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-[6px] bg-white text-[#162b6b] text-xs font-medium hover:bg-white/90 transition-colors"
              >
                <span>Inspect Editor Architecture</span>
                <ArrowRight size={14} weight="bold" />
              </Link>
            </div>
          </div>
        </div>

        {/* Showcase Card B: Wide Landscape Split Card (Compiler & Linker) */}
        <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden grid grid-cols-1 lg:grid-cols-12 items-stretch">
          {/* Left 6 Columns: Engineering Details */}
          <div className="lg:col-span-6 p-8 sm:p-10 flex flex-col justify-between space-y-6">
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-xs font-mono text-white/70">
                <span>CORE COMPILER</span>
                <span>/</span>
                <span className="text-white">src/kale/</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-renaissance font-normal text-white">
                Direct LLVM IR & Native FFI
              </h2>
              <p className="text-sm text-white/80 leading-relaxed font-normal">
                Kale transforms high-level syntax into clean, unbloated LLVM IR. Native dynamic linking flags (-l and -L) connect directly to Windows Win32, GLFW3, OpenGL32, and SQLite3 libraries with zero foreign function overhead.
              </p>

              <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-xs text-white/90 space-y-1">
                <div className="text-white/50 text-[10px]">{"// Direct Native Linker Invocation"}</div>
                <div>python -m kale.cli build app.kl -o bin/app.exe -lglfw3 -lopengl32</div>
              </div>
            </div>

            <div className="pt-4 border-t border-[#243b82]">
              <Link
                href="/projects/compiler"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-[6px] bg-white text-[#162b6b] text-xs font-medium hover:bg-white/90 transition-colors"
              >
                <span>Inspect Compiler Pipeline</span>
                <ArrowRight size={14} weight="bold" />
              </Link>
            </div>
          </div>

          {/* Right 6 Columns: Image fills right half edge-to-edge */}
          <div className="lg:col-span-6 relative min-h-[380px] lg:min-h-full border-t lg:border-t-0 lg:border-l border-[#243b82]">
            <Image
              src="/assets/kaleimages/HR-35Y_bUAAMBp-.jpg"
              alt="Architectural Lithograph"
              fill
              className="object-cover object-center"
            />
          </div>
        </div>

        {/* Showcase Cards C & D: Side-by-Side Cards with 1/3 Image Fill */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Card C: Bare-metal OS with edge-to-edge top 1/3 image */}
          <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden flex flex-col justify-between">
            <div className="relative h-64 w-full border-b border-[#243b82]">
              <Image
                src="/assets/kaleimages/HQ35R2NaIAAZecs.jpg"
                alt="Classical Monument"
                fill
                className="object-cover object-top"
              />
            </div>
            <div className="p-6 sm:p-8 space-y-4 flex-1 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="text-xs font-mono text-white/70">OPERATING SYSTEM / sys/</div>
                <h3 className="text-xl font-renaissance font-normal text-white">
                  x86_64 Long Mode Microkernel
                </h3>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                  Multiboot header, GDT/IDT descriptors, and hardware linear framebuffer driving desktop widgets directly on bare metal without standard library runtime.
                </p>
              </div>
              <div className="pt-4 border-t border-[#243b82]">
                <Link
                  href="/projects/sys"
                  className="inline-flex items-center gap-2 text-xs font-medium text-white hover:underline"
                >
                  <span>Explore Kernel Architecture</span>
                  <ArrowRight size={14} weight="bold" />
                </Link>
              </div>
            </div>
          </div>

          {/* Card D: Distributed VCS with edge-to-edge top 1/3 image */}
          <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden flex flex-col justify-between">
            <div className="relative h-64 w-full border-b border-[#243b82]">
              <Image
                src="/assets/kaleimages/HQQA_vDbsAAFoJM.jpg"
                alt="Classical Archway"
                fill
                className="object-cover object-top"
              />
            </div>
            <div className="p-6 sm:p-8 space-y-4 flex-1 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="text-xs font-mono text-white/70">DISTRIBUTED VCS / vcs/</div>
                <h3 className="text-xl font-renaissance font-normal text-white">
                  Git-Compatible Object Database
                </h3>
                <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                  Pure Kale implementation of SHA-1 hash trees, zlib-compressed commit objects, packfile delta parsing, and distributed repository push/fetch.
                </p>
              </div>
              <div className="pt-4 border-t border-[#243b82]">
                <Link
                  href="/projects/vcs"
                  className="inline-flex items-center gap-2 text-xs font-medium text-white hover:underline"
                >
                  <span>Explore VCS Architecture</span>
                  <ArrowRight size={14} weight="bold" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. SYSTEMS BENCHMARK & COMPARISON METRICS */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="p-6 sm:p-8 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-6 relative overflow-hidden">
          <HatchingOverlay />
          <div className="flex flex-col sm:flex-row sm:items-end justify-between border-b border-[#243b82] pb-4">
            <div>
              <span className="text-[10px] uppercase font-mono tracking-widest text-white/60">
                Hardware & Runtime Telemetry
              </span>
              <h2 className="text-2xl font-renaissance font-normal text-white mt-1">
                Systems Performance Benchmark
              </h2>
            </div>
            <p className="text-xs font-mono text-white/60 mt-2 sm:mt-0">
              Native x86_64 Execution Targets
            </p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-[#243b82] text-white/60">
                  <th className="py-3 px-4 font-normal">Subsystem Metric</th>
                  <th className="py-3 px-4 font-normal text-white">Kale (Native LLVM)</th>
                  <th className="py-3 px-4 font-normal">C / Clang</th>
                  <th className="py-3 px-4 font-normal">Rust (rustc)</th>
                  <th className="py-3 px-4 font-normal">Zig</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#243b82]">
                <tr>
                  <td className="py-3.5 px-4 text-white font-medium">Input to Frame Latency</td>
                  <td className="py-3.5 px-4 text-white font-semibold">0.8 ms</td>
                  <td className="py-3.5 px-4 text-white/70">1.2 ms</td>
                  <td className="py-3.5 px-4 text-white/70">2.1 ms</td>
                  <td className="py-3.5 px-4 text-white/70">1.4 ms</td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 text-white font-medium">Garbage Collector Pause</td>
                  <td className="py-3.5 px-4 text-white font-semibold">0.0 ms (Zero GC)</td>
                  <td className="py-3.5 px-4 text-white/70">0.0 ms</td>
                  <td className="py-3.5 px-4 text-white/70">0.0 ms</td>
                  <td className="py-3.5 px-4 text-white/70">0.0 ms</td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 text-white font-medium">Cold Compilation Latency</td>
                  <td className="py-3.5 px-4 text-white font-semibold">&lt; 24 ms</td>
                  <td className="py-3.5 px-4 text-white/70">48 ms</td>
                  <td className="py-3.5 px-4 text-white/70">310 ms</td>
                  <td className="py-3.5 px-4 text-white/70">65 ms</td>
                </tr>
                <tr>
                  <td className="py-3.5 px-4 text-white font-medium">Heap Overhead for Structs</td>
                  <td className="py-3.5 px-4 text-white font-semibold">0 Bytes (Stack Only)</td>
                  <td className="py-3.5 px-4 text-white/70">0 Bytes</td>
                  <td className="py-3.5 px-4 text-white/70">0 Bytes</td>
                  <td className="py-3.5 px-4 text-white/70">0 Bytes</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* 5. PROCEDURAL METAPHYSICAL GRAPHICS & ARCHITECTURAL PHILOSOPHY BENTO */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden grid grid-cols-1 lg:grid-cols-12 items-stretch relative">
          <HatchingOverlay />

          {/* Left 7 Columns: Metaphysical Procedural SVG Graphic (Perlin Noise, Colonnade, Stark Shadows, Color Blocks) */}
          <div className="lg:col-span-7 relative min-h-[380px] lg:min-h-[460px] border-b lg:border-b-0 lg:border-r border-[#243b82] overflow-hidden bg-[#08102b] flex items-center justify-center">
            <MetaphysicalPerlinGraphic />
            <div className="absolute top-4 left-4 px-3 py-1 rounded-[6px] bg-[#0d173d]/90 border border-white/20 text-[10px] font-mono text-white flex items-center gap-1.5 backdrop-blur-sm">
              <Sparkle size={12} weight="fill" className="text-white" />
              <span>NATIVE SVG FRACTAL NOISE // DE CHIRICO ARCADE</span>
            </div>
            <div className="absolute bottom-4 left-4 right-4 hidden sm:flex items-center justify-between px-3 py-1.5 rounded-[6px] bg-[#0d173d]/90 border border-white/10 text-[9px] font-mono text-white/70 backdrop-blur-sm">
              <span>feTurbulence baseFrequency=0.65 (Perlin)</span>
              <span>Vanishing Point: (520, 220)</span>
              <span>Pittura Metafisica</span>
            </div>
          </div>

          {/* Right 5 Columns: Architectural & Surrealist Philosophy Specification */}
          <div className="lg:col-span-5 p-8 sm:p-10 flex flex-col justify-between space-y-6 z-10">
            <div className="space-y-4">
              <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-[6px] border border-white/20 bg-[#162b6b] text-[10px] font-mono text-white">
                <span>METAPHYSICAL SYSTEMS DOCTRINE</span>
              </div>

              <h2 className="text-2xl sm:text-3xl font-renaissance font-normal text-white leading-snug">
                Uncanny Stillness. <br />
                Geometric Solitude.
              </h2>

              <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                Drawing direct heritage from Giorgio de Chirico&apos;s <em>Pittura Metafisica</em> and Jean Giraud (Moebius)&apos; clean-line graphic formalism, Kale rejects decorative noise in both software architecture and visual expression.
              </p>

              <div className="space-y-2.5 pt-2">
                <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1">
                  <div className="text-[10px] uppercase font-mono text-white/60">I. Architectural Rigor</div>
                  <div className="text-xs text-white/90">
                    Stark classical columns and Roman arches mirror rigid deterministic type bounds. No dynamic indirection.
                  </div>
                </div>

                <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1">
                  <div className="text-[10px] uppercase font-mono text-white/60">II. Exaggerated Cast Shadows</div>
                  <div className="text-xs text-white/90">
                    Dramatic 45° black/midnight geometry exposes hardware reality. Zero hidden runtime abstractions or GC pauses.
                  </div>
                </div>

                <div className="p-3 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-1">
                  <div className="text-[10px] uppercase font-mono text-white/60">III. Procedural Perlin Grain</div>
                  <div className="text-xs text-white/90">
                    Pure mathematical turbulence rendered in-browser without raster assets. Deterministic from first principles.
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-[#243b82] flex items-center justify-between text-xs font-mono text-white/70">
              <span>ANNO MMXXVI</span>
              <span className="text-white">x86_64 PURE SYSTEM</span>
            </div>
          </div>
        </div>
      </section>

      {/* 6. COMMUNITY & GITHUB ECOSYSTEM LINKS BENTO */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Card A (7 Cols): Primary GitHub Repository & Clone Bento */}
          <div className="lg:col-span-7 rounded-[6px] bg-[#0d173d] border border-[#243b82] p-8 sm:p-10 flex flex-col justify-between space-y-6 relative overflow-hidden">
            <HatchingOverlay />
            <div className="space-y-4 z-10">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-[6px] bg-white text-[#162b6b] flex items-center justify-center">
                    <GithubLogo size={20} weight="fill" />
                  </div>
                  <div>
                    <span className="text-[10px] uppercase font-mono text-white/60 block">Official Repository</span>
                    <h3 className="text-xl font-renaissance font-normal text-white">tomlin7 / kale</h3>
                  </div>
                </div>
                <a
                  href="https://github.com/tomlin7/kale"
                  target="_blank"
                  rel="noreferrer"
                  className="px-4 py-2 rounded-[6px] bg-white text-[#162b6b] text-xs font-medium hover:bg-white/90 transition-colors flex items-center gap-1.5"
                >
                  <span>Star on GitHub</span>
                  <ArrowUpRight size={14} weight="bold" />
                </a>
              </div>

              <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal">
                The entire Kale monorepo—compiler, standard library, 144Hz editor, Git-compatible VCS, linear window manager, SQL engine, and bare-metal OS—is completely open source and distributed under the MIT license.
              </p>

              {/* Terminal Clone Command Snippet */}
              <div className="p-4 rounded-[6px] bg-[#0a1333] border border-white/10 space-y-2">
                <div className="flex items-center justify-between text-[10px] font-mono text-white/60">
                  <span>CLONE WITH SUBMODULES</span>
                  <span className="text-white/40">bash / zsh / pwsh</span>
                </div>
                <div className="flex items-center justify-between font-mono text-xs text-white">
                  <code className="text-white/90 selection:bg-white selection:text-[#0a1333] overflow-x-auto">
                    git clone --recurse-submodules https://github.com/tomlin7/kale.git
                  </code>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-[#243b82] grid grid-cols-3 gap-3 text-center z-10">
              <div className="p-2.5 rounded-[6px] bg-[#162b6b]/40 border border-white/10">
                <div className="text-[10px] font-mono text-white/60">BRANCH</div>
                <div className="text-xs font-mono font-medium text-white mt-0.5">master</div>
              </div>
              <div className="p-2.5 rounded-[6px] bg-[#162b6b]/40 border border-white/10">
                <div className="text-[10px] font-mono text-white/60">LICENSE</div>
                <div className="text-xs font-mono font-medium text-white mt-0.5">MIT Open</div>
              </div>
              <div className="p-2.5 rounded-[6px] bg-[#162b6b]/40 border border-white/10">
                <div className="text-[10px] font-mono text-white/60">CONTRIBUTIONS</div>
                <div className="text-xs font-mono font-medium text-white mt-0.5">Welcome</div>
              </div>
            </div>
          </div>

          {/* Card B (5 Cols): Ecosystem Channels (Twitter/X & Release GPG) */}
          <div className="lg:col-span-5 flex flex-col gap-5">
            {/* Twitter / X Dispatch Bento */}
            <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] p-6 flex flex-col justify-between flex-1 relative overflow-hidden">
              <HatchingOverlay />
              <div className="space-y-3 z-10">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-[6px] bg-[#162b6b] border border-white/20 text-white flex items-center justify-center">
                      <XLogo size={16} weight="bold" />
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-mono text-white/60 block">Social Transmission</span>
                      <h4 className="text-base font-renaissance font-normal text-white">X / Twitter</h4>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded-[6px] bg-[#162b6b] border border-white/20 text-[10px] font-mono text-white">
                    SOON
                  </span>
                </div>
                <p className="text-xs text-white/80 leading-relaxed font-normal">
                  Release dispatches, compiler benchmarks, 144Hz editor demos, and architectural whitepapers broadcast soon.
                </p>
              </div>

              <div className="pt-4 border-t border-[#243b82] flex items-center justify-between text-xs font-mono text-white/60 z-10">
                <span>@kalesystems</span>
                <span className="text-white/40">Broadcast Pending</span>
              </div>
            </div>

            {/* Cryptographic Verification Bento */}
            <div className="rounded-[6px] bg-[#0d173d] border border-[#243b82] p-6 flex flex-col justify-between flex-1 relative overflow-hidden">
              <HatchingOverlay />
              <div className="space-y-3 z-10">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-[6px] bg-[#162b6b] border border-white/20 text-white flex items-center justify-center">
                      <Key size={16} weight="regular" />
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-mono text-white/60 block">Security & Integrity</span>
                      <h4 className="text-base font-renaissance font-normal text-white">Signed Releases</h4>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded-[6px] bg-white text-[#162b6b] text-[10px] font-mono font-medium">
                    VERIFIED
                  </span>
                </div>
                <div className="p-2.5 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-[11px] text-white flex items-center justify-between">
                  <span className="text-white/60 text-[10px]">GPG:</span>
                  <span className="text-white tracking-wider">1B91 7D47 79A6 102E</span>
                </div>
              </div>

              <div className="pt-4 border-t border-[#243b82] flex items-center justify-between text-xs font-mono text-white/60 z-10">
                <span>Binary Provenance</span>
                <span className="text-white">Deterministic Build</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. MONOREPO MODULES REGISTRY GRID (18 projects with images & phosphor icons) */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-10">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 pb-4 border-b border-[#243b82]">
          <div>
            <span className="text-xs uppercase font-mono tracking-widest text-white/60">
              The Grand Monorepo Registry
            </span>
            <h2 className="text-2xl sm:text-3xl font-renaissance font-normal text-white mt-1">
              Select an Architectural Module
            </h2>
          </div>
          <p className="text-xs text-white/60 font-mono mt-2 sm:mt-0">
            18 Autonomous Modules • Native x86_64
          </p>
        </div>

        {/* 3-Column Bento Cards Grid (Zero Hover Animations) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {PROJECTS.map((project) => {
            const IconComponent = PROJECT_ICONS[project.slug] || Columns;

            return (
              <Link
                key={project.slug}
                href={`/projects/${project.slug}`}
                className="rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden flex flex-col justify-between hover:border-white/50 transition-colors group"
              >
                {/* 1/3 Height Card Image Header */}
                <div className="relative h-44 w-full border-b border-[#243b82]">
                  <Image
                    src={project.image}
                    alt={project.name}
                    fill
                    className="object-cover object-center"
                  />
                  <div className="absolute top-3 left-3 px-2 py-0.5 rounded-[6px] bg-[#0d173d]/90 border border-white/20 text-[10px] font-mono text-white">
                    {project.tier}
                  </div>
                  <div className="absolute top-3 right-3 px-2 py-0.5 rounded-[6px] bg-[#0d173d]/90 border border-white/20 text-[10px] font-mono text-white">
                    {project.version}
                  </div>
                </div>

                {/* Card Body */}
                <div className="p-5 space-y-3 flex-1 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-[6px] bg-[#162b6b] border border-white/20 text-white flex items-center justify-center">
                        <IconComponent size={14} weight="regular" />
                      </div>
                      <h3 className="text-base font-normal text-white font-renaissance">
                        {project.name}
                      </h3>
                    </div>
                    <div className="text-[11px] text-white/60 font-mono">
                      {project.path}
                    </div>
                    <p className="text-xs text-white/80 line-clamp-2 leading-relaxed font-normal pt-1">
                      {project.tagline}
                    </p>
                  </div>

                  {/* Footer Link */}
                  <div className="pt-3 border-t border-[#243b82] flex items-center justify-between text-xs text-white/80 font-normal">
                    <span>Inspect Specification</span>
                    <ArrowUpRight size={14} weight="bold" className="text-white" />
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>
    </div>
  );
}
