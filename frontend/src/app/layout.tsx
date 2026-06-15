import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tata Steel Sherlock — Autonomous Plant Intelligence System",
  description: "Multi-agent AI platform for industrial operations — predictive maintenance, safety, energy, and production intelligence",
  keywords: ["Tata Steel", "Sherlock", "AI", "industrial", "predictive maintenance", "safety"],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
