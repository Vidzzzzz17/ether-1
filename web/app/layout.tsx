import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "Ether 1 — Multimodal Assistant", description: "A private workspace for chat, voice, images and ideas." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en"><body>{children}</body></html>; }

