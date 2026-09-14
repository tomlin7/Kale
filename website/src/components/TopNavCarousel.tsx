"use client";

import React, { useRef, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { PROJECTS } from "@/data/projects";
import { ChevronLeft, ChevronRight, Sparkles, BookOpen, Layers, Code2 } from "lucide-react";

export function TopNavCarousel() {
  const pathname = usePathname();
  const scrollRef = useRef<HTMLDivElement>(null);

  const scroll = (direction: "left" | "right") => {
    if (scrollRef.current) {
      const offset = direction === "left" ? -320 : 320;
      scrollRef.current.scrollBy({ left: offset, behavior: "smooth" });
    }
  };

  // Scroll active item into view on load/route change
  useEffect(() => {
    if (scrollRef.current) {
      const activeEl = scrollRef.current.querySelector('[data-active="true"]');
      if (activeEl) {
        activeEl.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" });
      }
    }
  }, [pathname]);

  return (
    <header className="sticky top-0 z-50 w-full bg-[#070b19]/90 backdrop-blur-md border-b border-[#1c274c]">
      {/* Brand & Monorepo Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3 group">
          <div className="w-8 h-8 rounded border border-[#b91c1c] bg-[#1a0f1b] flex items-center justify-center text-[#f8fafc] font-renaissance font-bold text-sm shadow-[0_0_12px_rgba(185,28,28,0.5)] group-hover:border-[#e11d48] transition-colors">
            KL
          </div>
          <div className="flex flex-col">
            <span className="font-renaissance font-semibold tracking-wider text-base text-[#f8fafc] group-hover:text-red-400 transition-colors">
              KALE
            </span>
            <span className="text-[10px] uppercase tracking-widest text-[#94a3b8] -mt-1">
              Renaissance Monorepo
            </span>
          </div>
        </Link>

        {/* Global Action Links */}
        <div className="flex items-center gap-4 text-xs">
          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded bg-[#0c1328] border border-[#1c274c] text-[#cbd5e1]">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>18 Projects Integrated</span>
          </div>
          <a
            href="https://github.com/tomlin7/kale"
            target="_blank"
            rel="noreferrer"
            className="px-3 py-1 rounded border border-[#b91c1c]/60 bg-[#b91c1c]/10 text-red-300 hover:bg-[#b91c1c] hover:text-white transition-all duration-200"
          >
            GitHub Repository
          </a>
        </div>
      </div>

      {/* Horizontal Project Carousel Strip */}
      <div className="relative w-full border-t border-[#121c3b] bg-[#050814]">
        {/* Left Arrow Button */}
        <button
          onClick={() => scroll("left")}
          className="absolute left-1 top-1/2 -translate-y-1/2 z-20 w-7 h-7 rounded-full bg-[#0c1328]/90 border border-[#1c274c] text-slate-300 hover:text-white hover:border-[#b91c1c] flex items-center justify-center transition-all shadow-lg"
          aria-label="Scroll left"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>

        {/* Scrollable Container */}
        <div
          ref={scrollRef}
          className="flex items-center gap-2 overflow-x-auto px-10 py-2.5 no-scrollbar scroll-smooth"
        >
          {PROJECTS.map((p) => {
            const href = `/projects/${p.slug}`;
            const isActive = pathname === href;

            return (
              <Link
                key={p.slug}
                href={href}
                data-active={isActive}
                className={`flex-shrink-0 flex items-center gap-2.5 px-3.5 py-2 rounded-lg border transition-all duration-200 group ${
                  isActive
                    ? "bg-[#121c3b] border-[#b91c1c] text-[#f8fafc] shadow-[0_0_15px_rgba(185,28,28,0.35)]"
                    : "bg-[#090e21] border-[#16203f] text-[#94a3b8] hover:border-[#2a3c70] hover:text-[#e2e8f0] hover:bg-[#0c142e]"
                }`}
              >
                {/* Roman Numeral badge */}
                <div
                  className={`w-6 h-6 rounded flex items-center justify-center text-[10px] font-renaissance font-bold transition-colors ${
                    isActive
                      ? "bg-[#b91c1c] text-white"
                      : "bg-[#16203f] text-slate-400 group-hover:bg-[#1f2d57] group-hover:text-slate-200"
                  }`}
                >
                  {p.romanNumeral}
                </div>

                {/* Project Title & Status */}
                <div className="flex flex-col text-left">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium tracking-wide">
                      {p.name}
                    </span>
                    <span
                      className={`text-[9px] px-1.5 py-0.2 rounded font-mono ${
                        p.status === "Active"
                          ? "bg-emerald-950/80 border border-emerald-800/60 text-emerald-400"
                          : p.status === "Stable"
                          ? "bg-blue-950/80 border border-blue-800/60 text-blue-400"
                          : "bg-slate-900 border border-slate-700/60 text-slate-400"
                      }`}
                    >
                      {p.version}
                    </span>
                  </div>
                  <span className="text-[10px] text-[#64748b] group-hover:text-[#94a3b8] font-mono truncate max-w-[150px]">
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
          className="absolute right-1 top-1/2 -translate-y-1/2 z-20 w-7 h-7 rounded-full bg-[#0c1328]/90 border border-[#1c274c] text-slate-300 hover:text-white hover:border-[#b91c1c] flex items-center justify-center transition-all shadow-lg"
          aria-label="Scroll right"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
