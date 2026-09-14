import React from "react";
import Image from "next/image";
import Link from "next/link";
import { PROJECTS } from "@/data/projects";
import { ArrowRight, Sparkles, Terminal, Code2, Shield, Layers, Cpu, ArrowUpRight } from "lucide-react";

export default function HomePage() {
  const flagshipProjects = PROJECTS.slice(0, 6);

  return (
    <div className="w-full min-h-screen bg-[#050814] pb-24">
      {/* Renaissance Master Hero Banner */}
      <section className="relative w-full border-b border-[#1c274c] overflow-hidden bg-gradient-to-b from-[#0a1128] via-[#070c1e] to-[#050814] py-16 lg:py-24">
        {/* Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[450px] bg-[#b91c1c]/15 blur-[140px] pointer-events-none rounded-full" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          <div className="lg:col-span-7 space-y-6 z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#b91c1c]/50 bg-[#b91c1c]/10 text-red-300 text-xs font-renaissance tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              <span>THE RENAISSANCE OF SYSTEMS PROGRAMMING</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-renaissance font-extrabold tracking-tight text-[#f8fafc] leading-[1.12]">
              Uncompromising Speed. <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-red-400 via-rose-300 to-amber-200">
                Pristine Architecture.
              </span>
            </h1>

            <p className="text-base sm:text-lg text-[#94a3b8] leading-relaxed max-w-2xl">
              Kale is an autonomous systems programming language engineered for extreme performance. From bare-metal x86_64 microkernels to 144Hz GPU-rendered code editors, every layer is crafted with mathematical precision.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <Link
                href="/projects/compiler"
                className="px-6 py-3 rounded-lg bg-[#b91c1c] hover:bg-[#dc2626] text-white font-medium text-sm flex items-center gap-2 transition-all shadow-[0_0_20px_rgba(185,28,28,0.4)]"
              >
                <span>Explore Compiler (Pillar I)</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                href="/projects/editor"
                className="px-6 py-3 rounded-lg bg-[#0c1328] hover:bg-[#121c3b] border border-[#1c274c] hover:border-[#b91c1c] text-[#f8fafc] font-medium text-sm transition-all"
              >
                <span>Flagship Editor (Pillar II)</span>
              </Link>
            </div>
          </div>

          <div className="lg:col-span-5 relative">
            <div className="relative rounded-2xl border-2 border-[#b91c1c]/80 bg-[#0c1328] p-2.5 shadow-[0_0_40px_rgba(185,28,28,0.3)] overflow-hidden group">
              <div className="relative rounded-xl overflow-hidden aspect-[4/3]">
                <Image
                  src="/assets/kale_renaissance_art_1789420061623.jpg"
                  alt="Kale Renaissance Architecture"
                  fill
                  className="object-cover transition-transform duration-700 group-hover:scale-105"
                  priority
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#070b19] via-transparent to-transparent opacity-50" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Monorepo Projects Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-16">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-8 pb-4 border-b border-[#1c274c]">
          <div>
            <span className="text-xs uppercase font-mono tracking-widest text-red-400">
              The Grand Monorepo Registry
            </span>
            <h2 className="text-2xl sm:text-3xl font-renaissance font-bold text-[#f8fafc] mt-1">
              Select a Pillar to Inspect
            </h2>
          </div>
          <p className="text-xs text-[#94a3b8] font-mono mt-2 sm:mt-0">
            Click any project to navigate instantly without reload
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {PROJECTS.map((project) => (
            <Link
              key={project.slug}
              href={`/projects/${project.slug}`}
              className="group rounded-xl bg-[#090e21] border border-[#16203f] hover:border-[#b91c1c] hover:bg-[#0c142e] transition-all duration-200 overflow-hidden flex flex-col p-5 hover:shadow-[0_0_25px_rgba(185,28,28,0.25)]"
            >
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded bg-[#16203f] group-hover:bg-[#b91c1c] text-slate-300 group-hover:text-white flex items-center justify-center text-xs font-renaissance font-bold transition-colors">
                    {project.romanNumeral}
                  </div>
                  <span className="text-[11px] font-mono text-[#64748b] group-hover:text-[#94a3b8]">
                    {project.tier}
                  </span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#050814] border border-[#1c274c] text-slate-400">
                  {project.version}
                </span>
              </div>

              {/* Title & Subtitle */}
              <div className="mt-4">
                <h3 className="text-lg font-renaissance font-bold text-[#f8fafc] group-hover:text-red-300 transition-colors">
                  {project.name}
                </h3>
                <p className="text-xs text-[#94a3b8] mt-1 font-mono">
                  {project.path}
                </p>
              </div>

              {/* Tagline */}
              <p className="text-xs text-[#64748b] group-hover:text-[#94a3b8] mt-3 line-clamp-2 leading-relaxed flex-1">
                {project.tagline}
              </p>

              {/* Action footer */}
              <div className="mt-4 pt-3 border-t border-[#121c3b] flex items-center justify-between text-xs text-red-400 font-medium group-hover:text-red-300">
                <span>View Documentation & Code</span>
                <ArrowUpRight className="w-4 h-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
