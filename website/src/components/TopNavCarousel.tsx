"use client";

import React, { useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PROJECTS } from "@/data/projects";
import {
  CaretLeft,
  CaretRight,
  House,
  GithubLogo,
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

  const isHome = pathname === "/";

  return (
    <header className="sticky top-0 z-50 w-full bg-[#0d173d] border-b border-[#243b82] shadow-sm">
      <div className="w-full flex items-center justify-between px-3 sm:px-4 h-12 gap-2">
        {/* Home / Overview Tab */}
        <Link
          href="/"
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] text-xs font-mono border transition-colors flex-shrink-0 ${
            isHome
              ? "bg-white text-[#162b6b] border-white font-medium"
              : "bg-[#162b6b]/60 border-white/20 text-white/80 hover:text-white hover:border-white/40"
          }`}
        >
          <House size={14} weight="bold" />
          <span className="tracking-wider">OVERVIEW</span>
        </Link>

        {/* Separator */}
        <div className="h-4 w-[1px] bg-[#243b82] flex-shrink-0" />

        {/* Scrollable Architectural Tabs Container */}
        <div className="relative flex-1 flex items-center overflow-hidden">
          {/* Scroll Left Button */}
          <button
            onClick={() => scroll("left")}
            className="absolute left-0 top-1/2 -translate-y-1/2 z-20 w-6 h-6 rounded-[6px] bg-[#0d173d] border border-white/20 text-white hover:border-white flex items-center justify-center transition-colors shadow-md"
            aria-label="Scroll left"
          >
            <CaretLeft size={12} weight="bold" />
          </button>

          {/* Tabs Ribbon */}
          <div
            ref={scrollRef}
            className="flex items-center gap-1.5 overflow-x-auto px-8 py-1 no-scrollbar scroll-smooth w-full"
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
                  className={`flex-shrink-0 flex items-center gap-2 px-2.5 py-1 rounded-[6px] border text-xs transition-colors font-mono ${
                    isActive
                      ? "bg-white text-[#162b6b] border-white font-medium"
                      : "bg-[#162b6b]/40 border-white/10 text-white/70 hover:border-white/30 hover:text-white hover:bg-[#162b6b]/80"
                  }`}
                >
                  <IconComponent size={13} weight="regular" />
                  <span className="font-sans font-normal">{p.name}</span>
                  <span
                    className={`text-[9px] px-1 py-0.2 rounded-[4px] ${
                      isActive ? "bg-[#162b6b]/15 text-[#162b6b]" : "bg-[#0d173d] text-white/50"
                    }`}
                  >
                    {p.version}
                  </span>
                </Link>
              );
            })}
          </div>

          {/* Scroll Right Button */}
          <button
            onClick={() => scroll("right")}
            className="absolute right-0 top-1/2 -translate-y-1/2 z-20 w-6 h-6 rounded-[6px] bg-[#0d173d] border border-white/20 text-white hover:border-white flex items-center justify-center transition-colors shadow-md"
            aria-label="Scroll right"
          >
            <CaretRight size={12} weight="bold" />
          </button>
        </div>

        {/* Separator */}
        <div className="h-4 w-[1px] bg-[#243b82] flex-shrink-0" />

        {/* Highlighted GitHub Action Link */}
        <a
          href="https://github.com/tomlin7/kale"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-[6px] bg-white text-[#162b6b] text-xs font-medium hover:bg-white/90 transition-colors flex-shrink-0"
        >
          <GithubLogo size={15} weight="fill" />
          <span className="hidden sm:inline">GitHub</span>
        </a>
      </div>
    </header>
  );
}
