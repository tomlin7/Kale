import React from "react";
import Image from "next/image";
import Link from "next/link";
import { ProjectInfo, PROJECTS } from "@/data/projects";
import { 
  Terminal, 
  Cpu, 
  Layers, 
  Sparkles, 
  Code2, 
  ArrowRight, 
  CheckCircle2, 
  ShieldCheck, 
  ExternalLink,
  ChevronRight
} from "lucide-react";

export function ProjectDetailView({ project }: { project: ProjectInfo }) {
  // Find previous and next project for bottom pagination
  const currentIndex = PROJECTS.findIndex((p) => p.slug === project.slug);
  const prevProject = currentIndex > 0 ? PROJECTS[currentIndex - 1] : PROJECTS[PROJECTS.length - 1];
  const nextProject = currentIndex < PROJECTS.length - 1 ? PROJECTS[currentIndex + 1] : PROJECTS[0];

  return (
    <div className="w-full min-h-screen pb-24 bg-[#050814]">
      {/* Renaissance Hero Section */}
      <section className="relative w-full border-b border-[#1c274c] overflow-hidden bg-gradient-to-b from-[#0a1128] via-[#070c1e] to-[#050814]">
        {/* Background glow effects */}
        <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[900px] h-[350px] bg-[#b91c1c]/15 blur-[120px] pointer-events-none rounded-full" />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 pt-10 pb-12 lg:pt-14 lg:pb-16 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left Column: Metadata & Hero Title */}
          <div className="lg:col-span-7 flex flex-col space-y-5 z-10">
            {/* Breadcrumb / Tier Badge */}
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="px-2.5 py-1 rounded bg-[#0c1328] border border-[#1c274c] text-[#94a3b8] font-mono">
                {project.tier}
              </span>
              <span className="text-[#64748b]">/</span>
              <span className="px-2 py-0.5 rounded font-renaissance font-bold bg-[#b91c1c]/20 border border-[#b91c1c]/60 text-red-300">
                Pillar {project.romanNumeral}
              </span>
              <span className="px-2 py-0.5 rounded font-mono text-[11px] bg-emerald-950/60 border border-emerald-800/40 text-emerald-400">
                {project.status} • {project.version}
              </span>
            </div>

            {/* Title */}
            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-renaissance font-bold tracking-tight text-[#f8fafc] leading-[1.15]">
              {project.name}
            </h1>

            {/* Subtitle */}
            <p className="text-lg sm:text-xl font-renaissance text-[#e2e8f0]/90 italic">
              {project.subtitle}
            </p>

            {/* Tagline */}
            <p className="text-sm sm:text-base text-[#94a3b8] leading-relaxed max-w-2xl">
              {project.tagline}
            </p>

            {/* Quick Metrics Bar */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-3">
              {project.stats.map((stat, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-lg bg-[#0c1328]/80 border border-[#1c274c] flex flex-col"
                >
                  <span className="text-[10px] uppercase font-mono tracking-wider text-[#64748b]">
                    {stat.label}
                  </span>
                  <span className="text-sm sm:text-base font-semibold text-[#f8fafc] mt-0.5">
                    {stat.value}
                  </span>
                </div>
              ))}
            </div>

            {/* Repo Path & Quick Action */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-[#090e21] border border-[#16203f] font-mono text-xs text-slate-300">
                <span className="text-red-400">monorepo:</span>
                <span>{project.path}</span>
              </div>
              <a
                href={`https://github.com/tomlin7/kale/tree/master/${project.path}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-md bg-[#b91c1c] hover:bg-[#dc2626] text-white text-xs font-medium transition-all shadow-[0_0_15px_rgba(185,28,28,0.4)]"
              >
                <span>Browse Source</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>

          {/* Right Column: Classical Renaissance Etching Card */}
          <div className="lg:col-span-5 relative">
            <div className="relative rounded-xl border-2 border-[#b91c1c]/70 bg-[#0c1328] p-2 shadow-[0_0_30px_rgba(185,28,28,0.25)] overflow-hidden group">
              {/* Inner Decorative Arch Border */}
              <div className="relative rounded-lg overflow-hidden border border-[#1c274c] aspect-[4/3]">
                <Image
                  src={project.image}
                  alt={project.name}
                  fill
                  className="object-cover transition-transform duration-700 group-hover:scale-105"
                  priority
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#070b19] via-transparent to-transparent opacity-60" />
                
                {/* Floating Architectural Badge */}
                <div className="absolute bottom-3 left-3 right-3 p-2.5 rounded bg-[#070b19]/80 backdrop-blur-md border border-[#1c274c] flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-renaissance text-xs font-bold text-red-300">
                      ARCHITETTURA KALE
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      Anno MMXXVI
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400">
                    Verified Native
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Details */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-12 grid grid-cols-1 lg:grid-cols-12 gap-10">
        {/* Left 7 Columns: Architectural Overview, Key Features & Code */}
        <div className="lg:col-span-7 space-y-10">
          {/* Architectural Overview */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-[#1c274c]">
              <Layers className="w-5 h-5 text-red-400" />
              <h2 className="text-xl font-renaissance font-bold text-[#f8fafc]">
                Architectural Blueprint
              </h2>
            </div>
            <p className="text-sm sm:text-base text-[#94a3b8] leading-relaxed">
              {project.description}
            </p>
          </section>

          {/* Highlights */}
          <section className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-[#1c274c]">
              <Sparkles className="w-5 h-5 text-red-400" />
              <h2 className="text-xl font-renaissance font-bold text-[#f8fafc]">
                Core Pillars & Capabilities
              </h2>
            </div>
            <div className="grid grid-cols-1 gap-4">
              {project.highlights.map((h, i) => (
                <div
                  key={i}
                  className="p-4 rounded-lg bg-[#0c1328] border border-[#1c274c] hover:border-[#b91c1c]/60 transition-colors"
                >
                  <div className="flex items-center gap-2 text-sm font-semibold text-[#f8fafc]">
                    <CheckCircle2 className="w-4 h-4 text-red-400 flex-shrink-0" />
                    <span>{h.title}</span>
                  </div>
                  <p className="text-xs sm:text-sm text-[#94a3b8] mt-2 leading-relaxed">
                    {h.description}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* Code Snippet */}
          <section className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-[#1c274c]">
              <div className="flex items-center gap-2">
                <Code2 className="w-5 h-5 text-red-400" />
                <h2 className="text-xl font-renaissance font-bold text-[#f8fafc]">
                  Canonical Implementation
                </h2>
              </div>
              <span className="text-xs font-mono text-[#64748b]">
                {project.codeSnippet.filename}
              </span>
            </div>

            <div className="rounded-lg border border-[#1c274c] bg-[#050814] overflow-hidden shadow-inner">
              <div className="px-4 py-2 bg-[#090e21] border-b border-[#1c274c] flex items-center justify-between text-xs text-[#94a3b8] font-mono">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-600/70"></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-600/70"></span>
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-600/70"></span>
                  <span className="ml-2">{project.codeSnippet.filename}</span>
                </div>
                <span className="uppercase text-[10px] text-slate-500">
                  {project.codeSnippet.language}
                </span>
              </div>
              <pre className="p-4 text-xs sm:text-sm font-mono text-[#e2e8f0] overflow-x-auto leading-relaxed">
                <code>{project.codeSnippet.code}</code>
              </pre>
            </div>
          </section>
        </div>

        {/* Right 5 Columns: CLI, Build Directives & Navigation */}
        <div className="lg:col-span-5 space-y-8">
          {/* CLI Invocations */}
          <div className="p-5 rounded-xl bg-[#0c1328] border border-[#1c274c] space-y-4">
            <div className="flex items-center gap-2 text-sm font-renaissance font-bold text-[#f8fafc]">
              <Terminal className="w-4 h-4 text-red-400" />
              <span>Compilation & Verification CLI</span>
            </div>
            <p className="text-xs text-[#94a3b8]">
              Standard build commands to compile, link, and test this project within the monorepo:
            </p>
            <div className="space-y-2">
              {project.cliCommands.map((cmd, idx) => (
                <div
                  key={idx}
                  className="p-2.5 rounded bg-[#050814] border border-[#16203f] font-mono text-xs text-[#cbd5e1] overflow-x-auto flex items-center gap-2"
                >
                  <span className="text-red-400 select-none">$</span>
                  <code>{cmd}</code>
                </div>
              ))}
            </div>
          </div>

          {/* Monorepo Architecture Integration */}
          <div className="p-5 rounded-xl bg-[#0c1328] border border-[#1c274c] space-y-4">
            <div className="flex items-center gap-2 text-sm font-renaissance font-bold text-[#f8fafc]">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
              <span>Governance & Monorepo Contracts</span>
            </div>
            <ul className="text-xs text-[#94a3b8] space-y-2.5 list-disc list-inside">
              <li>
                Governed by canonical <span className="text-[#f8fafc] font-mono">agents.md</span> and <span className="text-[#f8fafc] font-mono">PLAN.md</span> specifications.
              </li>
              <li>
                Signed commits with GPG Key <span className="text-red-300 font-mono">1B917D4779A6102E</span>.
              </li>
              <li>
                Direct LLVM IR linking without dynamic runtime overhead.
              </li>
              <li>
                Rigorous automated regression tests in <span className="text-[#f8fafc] font-mono">tests/</span>.
              </li>
            </ul>
          </div>

          {/* Prev / Next Project Links */}
          <div className="pt-2 grid grid-cols-2 gap-3">
            <Link
              href={`/projects/${prevProject.slug}`}
              className="p-3 rounded-lg bg-[#0c1328] border border-[#1c274c] hover:border-[#b91c1c] text-left group transition-all"
            >
              <span className="text-[10px] uppercase font-mono text-[#64748b] block">
                ← Previous Pillar
              </span>
              <span className="text-xs font-semibold text-[#f8fafc] group-hover:text-red-300 truncate block mt-0.5">
                {prevProject.name}
              </span>
            </Link>

            <Link
              href={`/projects/${nextProject.slug}`}
              className="p-3 rounded-lg bg-[#0c1328] border border-[#1c274c] hover:border-[#b91c1c] text-right group transition-all"
            >
              <span className="text-[10px] uppercase font-mono text-[#64748b] block">
                Next Pillar →
              </span>
              <span className="text-xs font-semibold text-[#f8fafc] group-hover:text-red-300 truncate block mt-0.5">
                {nextProject.name}
              </span>
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
