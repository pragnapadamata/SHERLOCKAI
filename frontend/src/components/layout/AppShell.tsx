"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "./Sidebar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Demo mode: auto-login if no token
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("sherlock_token");
      if (!token) {
        // Set demo user automatically
        localStorage.setItem("sherlock_token", "demo-token");
        localStorage.setItem("sherlock_user", JSON.stringify({
          id: "usr_001",
          name: "Sherlock Architect",
          role: "Sherlock AI Architect",
          email: "admin@tatasteel.com",
          plant: "All Plants",
        }));
      }
      setReady(true);
    }
  }, [router]);

  if (!ready) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-surface">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-steel-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground text-sm">Loading Sherlock…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden relative bg-[#0a0f1c]">
      {/* Background Watermark Tata Logo */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden z-0 select-none">
        <svg
          role="img"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
          className="w-[600px] h-[600px] text-black opacity-[0.06]"
          fill="currentColor"
        >
          <path d="M9.774 11.568c.193-1.322.168-2.013-1.768-1.906-2.223.124-4.476.265-7.849 1.027A5.63 5.63 0 0 0 0 12c0 1.52.618 2.99 1.787 4.254 1.06 1.144 2.556 2.095 4.326 2.752a15.48 15.48 0 0 0 2.014.588c.13-.527.959-3.907 1.616-7.823l.03-.202m14.07-.88c-3.372-.762-5.624-.902-7.846-1.026-1.937-.107-1.962.584-1.768 1.906l.046.298c.65 3.848 1.458 7.16 1.598 7.72C20.595 18.508 24 15.516 24 12c0-.443-.054-.88-.157-1.311m-.491-1.324a7.163 7.163 0 0 0-1.14-1.618c-1.06-1.144-2.555-2.095-4.325-2.752-1.784-.662-3.82-1.011-5.887-1.011-2.068 0-4.103.35-5.887 1.01-1.77.658-3.266 1.61-4.326 2.753A7.17 7.17 0 0 0 .648 9.366c2.304-.557 6.245-1.293 9.904-1.37.353-.008.596.105.756.307.196.248.18 1.128.175 1.522l-.104 10.18a18.507 18.507 0 0 0 1.244 0l-.104-10.18c-.005-.394-.02-1.274.175-1.522.16-.202.403-.315.756-.308 3.658.078 7.597.813 9.902 1.37z" />
        </svg>
      </div>

      <Sidebar />
      <main className="flex-1 overflow-auto bg-transparent relative z-10">
        {children}
      </main>
    </div>
  );
}
