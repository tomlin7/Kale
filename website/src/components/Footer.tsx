"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import {
  GithubLogo,
  XLogo,
  ShieldCheck,
  ArrowUpRight,
  Code,
  Terminal,
  Cpu,
  Browsers,
} from "@phosphor-icons/react";

export function Footer() {
  return (
    <footer className="relative w-full bg-[#162b6b] text-white overflow-hidden border-t border-[#243b82]">
      {/* 1. DITHERING & PERLIN NOISE FADE GRADIENT AT THE TOP TRANSITION */}
      <div className="absolute top-0 inset-x-0 h-40 pointer-events-none z-20">
        <svg
          className="w-full h-full"
          preserveAspectRatio="none"
          viewBox="0 0 1200 160"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Top Dithering Gradient Mask */}
            <pattern id="footer-dither-dense" width="4" height="4" patternUnits="userSpaceOnUse">
              <rect width="2" height="2" fill="#162b6b" />
              <rect x="2" y="2" width="2" height="2" fill="#162b6b" />
            </pattern>
            <linearGradient id="fade-to-content" x1="0" y1="0" x2="0" y2="100%">
              <stop offset="0%" stopColor="#162b6b" stopOpacity="1" />
              <stop offset="60%" stopColor="#162b6b" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#162b6b" stopOpacity="0" />
            </linearGradient>
          </defs>
          <rect width="100%" height="100%" fill="url(#fade-to-content)" />
        </svg>
      </div>

      {/* 2. DITHERED CLASSICAL SCENERY BACKGROUND (Inspiration: nous style blue dithered image) */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-25 mix-blend-screen">
        <Image
          src="/assets/kaleimages/HR-35WubIAAt3Wd.jpg"
          alt="Classical Architecture Texture"
          fill
          className="object-cover object-center"
        />
        {/* SVG Dither Screen Overlay */}
        <svg className="absolute inset-0 w-full h-full" fill="none">
          <defs>
            <pattern id="halftone-dither" width="6" height="6" patternUnits="userSpaceOnUse">
              <circle cx="3" cy="3" r="1.2" fill="#ffffff" fillOpacity="0.6" />
            </pattern>
            <filter id="dither-perlin-noise">
              <feTurbulence type="fractalNoise" baseFrequency="0.8" numOctaves="3" result="noise" />
              <feColorMatrix
                type="matrix"
                values="0 0 0 0 1
                        0 0 0 0 1
                        0 0 0 0 1
                        0 0 0 0.18 0"
              />
              <feComposite operator="in" in2="SourceGraphic" />
            </filter>
          </defs>
          <rect width="100%" height="100%" fill="url(#halftone-dither)" />
          <rect width="100%" height="100%" fill="#ffffff" filter="url(#dither-perlin-noise)" />
        </svg>
      </div>

      {/* 3. GIANT BACKGROUND WATERMARK TYPOGRAPHY (KALE ECOSYSTEM) */}
      <div className="absolute inset-x-0 top-12 sm:top-8 flex justify-center items-center pointer-events-none select-none z-0 overflow-hidden">
        <div className="font-renaissance text-[19vw] font-normal tracking-[-0.04em] text-white/[0.045] whitespace-nowrap leading-none scale-y-110">
          KALE ECOSYSTEM
        </div>
      </div>

      {/* 4. MAIN FOOTER CONTENT CONTAINER */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 pt-24 sm:pt-32 pb-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-12 gap-10 lg:gap-8 pb-16 border-b border-white/15">
          {/* Brand Col (4 Cols) */}
          <div className="lg:col-span-4 space-y-6">
            <div className="flex items-center gap-3">
              {/* Monogram Badge inspired by Nous logo frame */}
              <div className="px-2.5 py-1.5 rounded-[6px] bg-white text-[#162b6b] border border-white font-renaissance font-bold text-sm tracking-widest uppercase">
                KALE
              </div>
              <span className="text-xs font-mono uppercase tracking-widest text-white/70">
                {"//"} MONOREPO OS
              </span>
            </div>

            <p className="text-xs sm:text-sm text-white/80 leading-relaxed font-normal max-w-sm">
              The autonomous systems language engineered without compromise: direct LLVM 18 IR emission, stack-allocated primitives, zero runtime GC, and sub-millisecond graphics.
            </p>

            {/* Cryptographic GPG Signature Block */}
            <div className="p-3.5 rounded-[6px] bg-[#0d173d]/90 border border-white/20 space-y-2 max-w-sm backdrop-blur-sm">
              <div className="flex items-center justify-between text-[10px] font-mono text-white/70">
                <span className="flex items-center gap-1.5">
                  <ShieldCheck size={14} weight="regular" className="text-white" />
                  GPG RELEASE SIGNATURE
                </span>
                <span className="px-1.5 py-0.5 rounded-[4px] bg-white text-[#162b6b] text-[9px] font-mono font-semibold">
                  ED25519
                </span>
              </div>
              <div className="font-mono text-[11px] text-white tracking-widest break-all select-all p-2 rounded-[4px] bg-[#0a1333] border border-white/10">
                1B91 7D47 79A6 102E 8158 F092 71EF 06C3 C14C C82E
              </div>
            </div>
          </div>

          {/* Column 1: Core Architecture (2 Cols) */}
          <div className="lg:col-span-2 space-y-3 font-mono">
            <div className="text-[11px] uppercase tracking-widest text-white/50 flex items-center gap-1.5">
              <Code size={12} weight="regular" />
              <span>COMPILER</span>
            </div>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/projects/compiler" className="text-white/80 hover:text-white transition-colors">
                  LLVM 18 IR Engine
                </Link>
              </li>
              <li>
                <Link href="/projects/std" className="text-white/80 hover:text-white transition-colors">
                  Standard Library
                </Link>
              </li>
              <li>
                <Link href="/projects/lsp" className="text-white/80 hover:text-white transition-colors">
                  Language Server
                </Link>
              </li>
              <li>
                <Link href="/projects/pkg" className="text-white/80 hover:text-white transition-colors">
                  Package Archive
                </Link>
              </li>
              <li>
                <Link href="/projects/vcs" className="text-white/80 hover:text-white transition-colors">
                  Git-Compatible VCS
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 2: Graphics & Tools (2 Cols) */}
          <div className="lg:col-span-2 space-y-3 font-mono">
            <div className="text-[11px] uppercase tracking-widest text-white/50 flex items-center gap-1.5">
              <Terminal size={12} weight="regular" />
              <span>GRAPHICS</span>
            </div>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/projects/editor" className="text-white/80 hover:text-white transition-colors">
                  144Hz Text Editor
                </Link>
              </li>
              <li>
                <Link href="/projects/gui" className="text-white/80 hover:text-white transition-colors">
                  GUI Widget System
                </Link>
              </li>
              <li>
                <Link href="/projects/render" className="text-white/80 hover:text-white transition-colors">
                  GPU Text Quad Atlas
                </Link>
              </li>
              <li>
                <Link href="/projects/term" className="text-white/80 hover:text-white transition-colors">
                  VT100 Terminal
                </Link>
              </li>
              <li>
                <Link href="/projects/audio" className="text-white/80 hover:text-white transition-colors">
                  Waveform DSP Audio
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Bare-Metal Kernel (2 Cols) */}
          <div className="lg:col-span-2 space-y-3 font-mono">
            <div className="text-[11px] uppercase tracking-widest text-white/50 flex items-center gap-1.5">
              <Cpu size={12} weight="regular" />
              <span>KERNEL</span>
            </div>
            <ul className="space-y-2 text-xs">
              <li>
                <Link href="/projects/sys" className="text-white/80 hover:text-white transition-colors">
                  x86_64 Long Mode
                </Link>
              </li>
              <li>
                <Link href="/projects/sysmon" className="text-white/80 hover:text-white transition-colors">
                  Hardware Telemetry
                </Link>
              </li>
              <li>
                <Link href="/projects/fs_watch" className="text-white/80 hover:text-white transition-colors">
                  Kernel FS Inotify
                </Link>
              </li>
              <li>
                <Link href="/projects/physics" className="text-white/80 hover:text-white transition-colors">
                  Verlet 2D Engine
                </Link>
              </li>
              <li>
                <Link href="/projects/net" className="text-white/80 hover:text-white transition-colors">
                  Async Socket I/O
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 4: Ecosystem & External (2 Cols) */}
          <div className="lg:col-span-2 space-y-3 font-mono">
            <div className="text-[11px] uppercase tracking-widest text-white/50 flex items-center gap-1.5">
              <Browsers size={12} weight="regular" />
              <span>COMMUNITY</span>
            </div>
            <ul className="space-y-2 text-xs">
              <li>
                <a
                  href="https://github.com/tomlin7/kale"
                  target="_blank"
                  rel="noreferrer"
                  className="text-white/80 hover:text-white transition-colors flex items-center gap-1"
                >
                  <span>GitHub Repository</span>
                  <ArrowUpRight size={12} weight="bold" />
                </a>
              </li>
              <li>
                <span className="text-white/40 flex items-center gap-1">
                  <span>X / Twitter</span>
                  <span className="text-[9px] px-1 py-0.2 rounded-[3px] border border-white/20">SOON</span>
                </span>
              </li>
              <li>
                <span className="text-white/40 flex items-center gap-1">
                  <span>Discord</span>
                  <span className="text-[9px] px-1 py-0.2 rounded-[3px] border border-white/20">SOON</span>
                </span>
              </li>
              <li>
                <a
                  href="https://github.com/tomlin7/kale/releases"
                  target="_blank"
                  rel="noreferrer"
                  className="text-white/80 hover:text-white transition-colors flex items-center gap-1"
                >
                  <span>Tagged Releases</span>
                  <ArrowUpRight size={12} weight="bold" />
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/tomlin7/kale/blob/master/LICENSE"
                  target="_blank"
                  rel="noreferrer"
                  className="text-white/80 hover:text-white transition-colors flex items-center gap-1"
                >
                  <span>MIT License</span>
                  <ArrowUpRight size={12} weight="bold" />
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* 5. SUB-FOOTER BOTTOM BAR */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-white/60">
          {/* Social Icons */}
          <div className="flex items-center gap-3">
            <a
              href="https://github.com/tomlin7/kale"
              target="_blank"
              rel="noreferrer"
              aria-label="Kale GitHub"
              className="p-1.5 rounded-[6px] bg-[#0d173d] border border-white/20 text-white hover:border-white transition-colors"
            >
              <GithubLogo size={16} weight="fill" />
            </a>
            <span
              aria-label="Kale X (Twitter)"
              className="p-1.5 rounded-[6px] bg-[#0d173d] border border-white/10 text-white/40 cursor-not-allowed"
              title="Coming Soon"
            >
              <XLogo size={16} weight="bold" />
            </span>
          </div>

          {/* Copyright and License Note */}
          <div className="flex flex-wrap items-center justify-center gap-4 text-[11px]">
            <span>© 2026 KALE MONOREPO ECOSYSTEM</span>
            <span className="hidden sm:inline text-white/30">•</span>
            <span className="text-white/80">OPEN SOURCE</span>
            <span className="hidden sm:inline text-white/30">•</span>
            <span className="text-white/80">MIT LICENSE</span>
            <span className="hidden sm:inline text-white/30">•</span>
            <span>NATIVE x86_64</span>
          </div>

          <div className="text-[11px] text-white/50">
            DETERMINISTIC COMPILATION
          </div>
        </div>
      </div>
    </footer>
  );
}
