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

export function ProjectDetailView({ project }: { project: ProjectInfo }) {
  const currentIndex = PROJECTS.findIndex((p) => p.slug === project.slug);
  const prevProject = currentIndex > 0 ? PROJECTS[currentIndex - 1] : PROJECTS[PROJECTS.length - 1];
  const nextProject = currentIndex < PROJECTS.length - 1 ? PROJECTS[currentIndex + 1] : PROJECTS[0];

  return (
    <div className="w-full min-h-screen pb-24 bg-[#162b6b] text-white">
      {/* Top Breadcrumb Header */}
      <section className="w-full border-b border-[#243b82] bg-[#0d173d] py-6">
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
              Pillar {project.romanNumeral} • {project.version}
            </span>
            <a
              href={`https://github.com/tomlin7/kale/tree/master/${project.path}`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-[6px] bg-white text-[#162b6b] text-xs font-medium hover:bg-white/90 transition-colors"
            >
              <span>Browse Source</span>
              <ArrowSquareOut size={14} weight="bold" />
            </a>
          </div>
        </div>
      </section>

      {/* Main Bento Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 pt-8 space-y-6">
        {/* Top Bento Row: Hero Overview + Classical Artwork */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left 7 Columns: Architecture & Metrics Bento */}
          <div className="lg:col-span-7 flex flex-col justify-between p-6 sm:p-8 rounded-[6px] bg-[#0d173d] border border-[#243b82]">
            <div className="space-y-4">
              <span className="text-[11px] font-mono uppercase tracking-widest text-white/60">
                {project.path}
              </span>

              <h1 className="text-3xl sm:text-4xl font-renaissance font-normal tracking-tight text-white leading-tight">
                {project.name}
              </h1>

              <p className="text-base text-white/90 font-normal">
                {project.subtitle}
              </p>

              <p className="text-sm text-white/80 leading-relaxed max-w-2xl">
                {project.description}
              </p>
            </div>

            {/* Quick Metrics Bento Tiles */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-6 mt-6 border-t border-[#243b82]">
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

          {/* Right 5 Columns: Classical Lithograph Artwork Bento */}
          <div className="lg:col-span-5 rounded-[6px] bg-[#0d173d] border border-[#243b82] p-3 flex flex-col justify-between">
            <div className="relative rounded-[6px] overflow-hidden border border-white/10 aspect-[4/3] w-full">
              <Image
                src={project.image}
                alt={project.name}
                fill
                className="object-cover"
                priority
              />
            </div>
            <div className="pt-3 flex items-center justify-between text-xs font-mono text-white/70 px-1">
              <span>CLASSICAL ARCHITECTURE</span>
              <span>ANNO MMXXVI</span>
            </div>
          </div>
        </div>

        {/* Middle Bento Row: Canonical Code + CLI Build Directives */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left 7 Columns: Codeblock with Darker Blue Tint (#0a1333) */}
          <div className="lg:col-span-7 rounded-[6px] bg-[#0d173d] border border-[#243b82] overflow-hidden flex flex-col">
            {/* Code Header */}
            <div className="px-5 py-3 bg-[#0a1333] border-b border-[#243b82] flex items-center justify-between text-xs font-mono text-white">
              <div className="flex items-center gap-2">
                <Code size={16} weight="regular" className="text-white" />
                <span className="font-medium">{project.codeSnippet.filename}</span>
              </div>
              <span className="uppercase text-[10px] text-white/60 tracking-wider">
                {project.codeSnippet.language}
              </span>
            </div>

            {/* Darker Blue Code Content */}
            <pre className="p-5 text-xs sm:text-sm font-mono text-white bg-[#0a1333] overflow-x-auto leading-relaxed flex-1">
              <code>{project.codeSnippet.code}</code>
            </pre>
          </div>

          {/* Right 5 Columns: CLI Compilation Directives Bento */}
          <div className="lg:col-span-5 p-6 rounded-[6px] bg-[#0d173d] border border-[#243b82] flex flex-col justify-between space-y-4">
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-sm font-renaissance font-normal text-white">
                <TerminalWindow size={18} weight="regular" className="text-white" />
                <span>Compiler & Linker Directives</span>
              </div>
              <p className="text-xs text-white/70 leading-relaxed">
                Deterministic CLI invocation to compile, link native dependencies, and verify symbols:
              </p>
              <div className="space-y-2 pt-1">
                {project.cliCommands.map((cmd, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-[6px] bg-[#0a1333] border border-white/10 font-mono text-xs text-white overflow-x-auto flex items-center gap-2"
                  >
                    <span className="text-white/40 select-none">$</span>
                    <code>{cmd}</code>
                  </div>
                ))}
              </div>
            </div>

            {/* Monorepo Specification Contract */}
            <div className="pt-4 border-t border-[#243b82] space-y-2">
              <div className="flex items-center gap-2 text-xs font-medium text-white">
                <ShieldCheck size={16} weight="regular" className="text-white" />
                <span>Monorepo Governance Contract</span>
              </div>
              <p className="text-xs text-white/70">
                Verified with GPG Key <span className="font-mono text-white">1B917D4779A6102E</span>. Stack allocated structs and zero dynamic runtime overhead.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Bento Row: Core Capabilities Grid */}
        <div className="p-6 rounded-[6px] bg-[#0d173d] border border-[#243b82] space-y-4">
          <div className="flex items-center gap-2 text-sm font-renaissance font-normal text-white">
            <Stack size={18} weight="regular" className="text-white" />
            <span>Architectural Capabilities</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
            {project.highlights.map((h, i) => (
              <div
                key={i}
                className="p-4 rounded-[6px] bg-[#162b6b] border border-white/10 flex flex-col justify-between"
              >
                <div className="flex items-center gap-2 text-sm font-medium text-white">
                  <CheckCircle size={16} weight="regular" className="text-white flex-shrink-0" />
                  <span>{h.title}</span>
                </div>
                <p className="text-xs text-white/80 mt-2 leading-relaxed">
                  {h.description}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer Navigation Bento: Prev / Next Projects */}
        <div className="grid grid-cols-2 gap-4 pt-2">
          <Link
            href={`/projects/${prevProject.slug}`}
            className="p-4 rounded-[6px] bg-[#0d173d] border border-[#243b82] hover:border-white/50 text-left transition-colors flex items-center justify-between"
          >
            <div>
              <span className="text-[10px] uppercase font-mono text-white/60 block">
                ← Previous Pillar
              </span>
              <span className="text-sm font-normal text-white block mt-0.5">
                {prevProject.name}
              </span>
            </div>
            <CaretLeft size={18} weight="bold" className="text-white" />
          </Link>

          <Link
            href={`/projects/${nextProject.slug}`}
            className="p-4 rounded-[6px] bg-[#0d173d] border border-[#243b82] hover:border-white/50 text-right transition-colors flex items-center justify-between"
          >
            <CaretRight size={18} weight="bold" className="text-white" />
            <div>
              <span className="text-[10px] uppercase font-mono text-white/60 block">
                Next Pillar →
              </span>
              <span className="text-sm font-normal text-white block mt-0.5">
                {nextProject.name}
              </span>
            </div>
          </Link>
        </div>
      </main>
    </div>
  );
}
