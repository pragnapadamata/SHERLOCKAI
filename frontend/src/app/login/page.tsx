"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Shield, Activity, Cpu, BarChart3 } from "lucide-react";

// Custom Sherlock AI Logo in Maroon and Silver SVG
function SherlockLogo({ className = "w-24 h-24" }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <filter id="silver-glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
        <filter id="maroon-glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3.5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {/* Hexagonal outer shield (Silver / Gray) */}
      <polygon
        points="50,5 90,25 90,75 50,95 10,75 10,25"
        stroke="#94a3b8"
        strokeWidth="1.5"
        strokeOpacity="0.8"
        filter="url(#silver-glow)"
      />
      
      {/* Secondary inner hexagon (Maroon) */}
      <polygon
        points="50,9 86,27 86,73 50,91 14,73 14,27"
        stroke="#9f1239"
        strokeWidth="1.2"
        strokeOpacity="0.6"
      />

      {/* Futuristic circuitry paths */}
      <path d="M14,35 L26,35 L30,40" stroke="#9f1239" strokeWidth="0.8" strokeOpacity="0.5" />
      <path d="M86,35 L74,35 L70,40" stroke="#9f1239" strokeWidth="0.8" strokeOpacity="0.5" />
      <circle cx="30" cy="40" r="1.2" fill="#9f1239" fillOpacity="0.8" />
      <circle cx="70" cy="40" r="1.2" fill="#9f1239" fillOpacity="0.8" />

      {/* Sherlock/Detective Hat - Maroon with Silver Details */}
      <path
        d="M33,40 C33,25 41,21 50,21 C59,21 67,25 67,40 Z"
        fill="#700c1e"
        stroke="#cbd5e1"
        strokeWidth="1.5"
      />
      <path
        d="M32.5,40 L67.5,40 L67,43 L33,43 Z"
        fill="#94a3b8"
      />
      <path
        d="M22,46 C34,42 66,42 78,46 C72,47.5 62,48.5 50,48.5 C38,48.5 28,47.5 22,46 Z"
        fill="#700c1e"
        stroke="#cbd5e1"
        strokeWidth="1.5"
      />

      {/* Sunglasses / Eye Shadow Silhouette */}
      <path
        d="M37,56 C40.5,56 43,54 45.5,56.5 C48,54 50.5,56 54,56 C57,59 54.5,64.5 50,64.5 C45.5,64.5 43,59 37,56 Z"
        stroke="#cbd5e1"
        strokeWidth="1.5"
        fill="#30050c"
      />
      <path d="M38.5,57 C40,57 42,55.5 43,57 C43.5,59 42,62 40,62 C38,62 37.5,59 38.5,57 Z" fill="#9f1239" fillOpacity="0.5" />
      <path d="M51,57 C52,55.5 54,57 55.5,57 C56.5,59 56,62 54,62 C52,62 50.5,59 51,57 Z" fill="#9f1239" fillOpacity="0.5" />

      {/* Collar Silhouette */}
      <path
        d="M28,70 L37,60 L45,70 M72,70 L63,60 L55,70"
        stroke="#cbd5e1"
        strokeWidth="1.5"
      />
    </svg>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleGetStarted = () => {
    setLoading(true);
    // Mock local session as "Plant Director"
    localStorage.setItem("sherlock_token", "demo-token-" + Date.now());
    localStorage.setItem("sherlock_user", JSON.stringify({
      id: "usr_demo",
      email: "admin@tatasteel.com",
      name: "Admin",
      role: "Plant Director",
      plant: "All Plants",
    }));
    // Redirect to dashboard after a slight simulated delay
    setTimeout(() => {
      router.push("/dashboard");
    }, 800);
  };

  return (
    <div className="min-h-screen bg-[#221d33] flex items-center justify-center p-4 animate-fade-in relative overflow-hidden">
      {/* Grid overlay */}
      <div
        className="fixed inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage:
            "linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px)",
          backgroundSize: "45px 45px",
        }}
      />

      {/* Ambient Lighting / Radial Glows */}
      <div className="absolute top-[-25%] left-[20%] right-[20%] h-[70%] rounded-full bg-[#9f1239] opacity-[0.09] blur-[130px] pointer-events-none" />
      <div className="absolute bottom-[-10%] left-[10%] w-[35%] h-[35%] rounded-full bg-slate-400 opacity-[0.02] blur-[110px] pointer-events-none" />

      <div className="w-full max-w-lg relative z-10 flex flex-col items-center">
        {/* Logo and Titles */}
        <div className="text-center mb-8 flex flex-col items-center">
          <div className="mb-4 relative">
            <SherlockLogo className="w-24 h-24 drop-shadow-[0_0_20px_rgba(159,18,57,0.5)]" />
          </div>
          <h1 className="text-4xl font-extrabold tracking-wider text-slate-100 flex items-center justify-center gap-2">
            <span className="text-slate-100 font-sans tracking-tight">SHERLOCK</span>
            <span className="text-[#9f1239] filter drop-shadow-[0_0_8px_rgba(159,18,57,0.7)] font-sans tracking-tight">AI</span>
          </h1>
          <p className="text-[11px] font-semibold text-slate-400 tracking-[0.25em] uppercase mt-2">
            Industrial Intelligence Platform
          </p>

          {/* Subheader tagline with lines */}
          <div className="flex items-center gap-4 w-full max-w-sm mt-5">
            <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent via-[#9f1239]/50 to-[#9f1239]" />
            <span className="text-[10px] text-slate-300 font-medium tracking-[0.2em] uppercase whitespace-nowrap">
              Autonomous &bull; Intelligent &bull; Reliable
            </span>
            <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent via-[#9f1239]/50 to-[#9f1239]" />
          </div>
        </div>

        {/* Welcome Card Container */}
        <div className="w-full max-w-md bg-gradient-to-b from-[#180307]/90 to-[#0c0104]/95 border border-[#450712]/50 rounded-2xl p-8 shadow-[0_12px_45px_rgba(0,0,0,0.6)] text-center relative overflow-hidden group">
          {/* Top highlight bar */}
          <div className="absolute top-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-slate-400 to-transparent opacity-80" />
          
          <h2 className="text-xl font-bold text-slate-100 mb-3 tracking-wide">
            Welcome to Sherlock AI
          </h2>
          
          <div className="w-12 h-[1px] bg-[#9f1239] mx-auto mb-5" />

          <p className="text-slate-300 text-xs leading-relaxed mb-8 max-w-xs mx-auto">
            Empowering industrial decision-making through autonomous plant agents, real-time intelligence, and predictive insights.
          </p>

          <button
            onClick={handleGetStarted}
            disabled={loading}
            className="w-full bg-gradient-to-r from-slate-200 via-slate-100 to-slate-300 hover:from-slate-100 hover:via-white hover:to-slate-200 disabled:opacity-60 text-[#450712] font-bold rounded-lg py-3.5 text-xs transition-all duration-300 flex items-center justify-center gap-2.5 shadow-[0_0_20px_rgba(159,18,57,0.25)] hover:shadow-[0_0_25px_rgba(255,255,255,0.2)] tracking-widest uppercase cursor-pointer border-none"
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin text-[#450712]" />
            ) : (
              <>
                <span className="text-sm font-semibold">&rarr;</span>
                <span>Get Started</span>
              </>
            )}
          </button>
        </div>

        {/* Feature Row Footer */}
        <div className="flex items-center justify-center gap-4 text-[10px] text-slate-400 font-medium mt-10 flex-wrap">
          <div className="flex items-center gap-1.5">
            <Shield size={12} className="text-[#9f1239]" />
            <span>Secure</span>
          </div>
          <span className="text-[#9f1239]/50">&bull;</span>
          <div className="flex items-center gap-1.5">
            <Activity size={12} className="text-[#9f1239]" />
            <span>Real-time</span>
          </div>
          <span className="text-[#9f1239]/50">&bull;</span>
          <div className="flex items-center gap-1.5">
            <Cpu size={12} className="text-[#9f1239]" />
            <span>AI-Powered</span>
          </div>
          <span className="text-[#9f1239]/50">&bull;</span>
          <div className="flex items-center gap-1.5">
            <BarChart3 size={12} className="text-[#9f1239]" />
            <span>Data-Driven</span>
          </div>
        </div>

        {/* Copyright */}
        <p className="text-center text-[9px] text-slate-600 mt-6 tracking-widest uppercase font-mono">
          &copy; 2026 Sherlock AI Technologies &bull; All Rights Reserved
        </p>
      </div>
    </div>
  );
}
