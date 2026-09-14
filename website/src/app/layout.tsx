import type { Metadata } from "next";
import { Cinzel, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { TopNavCarousel } from "@/components/TopNavCarousel";

const cinzel = Cinzel({
  subsets: ["latin"],
  variable: "--font-cinzel",
  weight: ["400", "600", "700", "800"],
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata: Metadata = {
  title: "Kale Language Ecosystem | The Renaissance Systems Language",
  description: "A high-performance systems language with an autonomous ecosystem: GPU GUI, bare-metal OS, distributed VCS, and self-hosted compiler.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${cinzel.variable} ${inter.variable} ${jetbrainsMono.variable} dark`}>
      <body className="min-h-screen flex flex-col bg-[#050814] text-[#f8fafc] font-sans antialiased selection:bg-[#b91c1c] selection:text-white">
        <TopNavCarousel />
        <div className="flex-1 w-full">{children}</div>
        <footer className="w-full border-t border-[#1c274c] bg-[#070b19] py-8 text-center text-xs text-[#64748b] font-mono">
          <p>KALE PROGRAMMING LANGUAGE • ARCHITECTED FOR PERFECTION</p>
          <p className="mt-1 text-[11px] text-[#475569]">
            GPG Signed by 1B917D4779A6102E8158F09271EF06C3C14CC82E • Native x86_64
          </p>
        </footer>
      </body>
    </html>
  );
}
