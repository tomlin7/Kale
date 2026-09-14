"use client";

import React, { useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PROJECTS } from "@/data/projects";
import {
  CaretLeft,
  CaretRight,
  Columns,
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

export function TopNavCarousel() {
  const pathname = usePathname();
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: "left" | "right") => {
    if (scrollRef.current) {
      const offset = direction === "left" ? -320 : 320;
      scrollRef.current.scrollBy({ left: offset, behavior: "smooth" });
    }
  };

  useEffect(() => {
    if (scrollRef.current) {
      const activeEl = scrollRef.current.querySelector('[data-active="true"]');
      if (activeEl) {
        activeEl.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      }
    }
  }, [pathname]);

  return (
    <header className="sticky top-0 z-50 w-full bg-[#0d173d] border-b border-[#243b82]">
      {/* Brand & Monorepo Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-[6px] border border-white/30 bg-[#162b6b] flex items-center justify-center text-white">
            <Columns size={18} weight="regular" />
          </div>
          <div className="flex flex-col">
            <span className="font-renaissance tracking-wider text-base text-white font-normal">
              KALE
            </span>
            <span className="text-[10px] uppercase tracking-widest text-white/60 -mt-1 font-mono">
              Systems Monorepo
            </span>
          </div>
        </Link>

        {/* Global Action Links */}
        <div className="flex items-center gap-3 text-xs">
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-[6px] bg-[#162b6b] border border-white/20 text-white font-mono">
            <span className="w-1.5 h-1.5 rounded-[2px] bg-white"></span>
            <span>18 Modules</span>
          </div>
          <a
            href="https://github.com/tomlin7/kale"
            target="_blank"
            rel="noreferrer"
            className="px-3.5 py-1.5 rounded-[6px] bg-white text-[#162b6b] font-medium text-xs hover:bg-white/90 transition-colors"
          >
            Source Code
          </a>
        </div>
      </div>

      {/* Horizontal Project Carousel Strip */}
      <div className="relative w-full border-t border-[#243b82] bg-[#162b6b]">
        {/* Left Arrow Button */}
        <button
          onClick={() => scroll("left")}
          className="absolute left-2 top-1/2 -translate-y-1/2 z-20 w-7 h-7 rounded-[6px] bg-[#0d173d] border border-white/20 text-white hover:border-white/50 flex items-center justify-center transition-colors"
          aria-label="Scroll left"
        >
          <CaretLeft size={16} weight="bold" />
        </button>

        {/* Scrollable Container */}
        <div
          ref={scrollRef}
          className="flex items-center gap-2 overflow-x-auto px-12 py-2.5 no-scrollbar scroll-smooth"
        >
          {PROJECTS.map((p) => {
            const href = `/projects/${p.slug}`;
            const isActive = pathname === href;
            const IconComponent = PROJECT_ICONS[p.slug] || Columns;

            return (
              <Link
                key={p.slug}
                href={href}
                data-active={isActive}
                className={`flex-shrink-0 flex items-center gap-2.5 px-3 py-1.5 rounded-[6px] border transition-colors ${
                  isActive
                    ? "bg-[#0d173d] border-white text-white"
                    : "bg-[#0d173d]/70 border-[#243b82] text-white/80 hover:border-white/40 hover:text-white hover:bg-[#0d173d]"
                }`}
              >
                {/* Phosphor Icon instead of text initials */}
                <div
                  className={`w-6 h-6 rounded-[6px] flex items-center justify-center ${
                    isActive ? "bg-white text-[#162b6b]" : "bg-[#162b6b] text-white"
                  }`}
                >
                  <IconComponent size={14} weight="regular" />
                </div>

                {/* Project Title & Status */}
                <div className="flex flex-col text-left">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-normal text-white">
                      {p.name}
                    </span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded-[6px] font-mono bg-[#162b6b] border border-white/20 text-white/80">
                      {p.version}
                    </span>
                  </div>
                  <span className="text-[10px] text-white/60 font-mono truncate max-w-[140px]">
                    {p.path}
                  </span>
                </div>
              </Link>
            );
          })}
        </div>

        {/* Right Arrow Button */}
        <button
          onClick={() => scroll("right")}
          className="absolute right-2 top-1/2 -translate-y-1/2 z-20 w-7 h-7 rounded-[6px] bg-[#0d173d] border border-white/20 text-white hover:border-white/50 flex items-center justify-center transition-colors"
          aria-label="Scroll right"
        >
          <CaretRight size={16} weight="bold" />
        </button>
      </div>
    </header>
  );
}
