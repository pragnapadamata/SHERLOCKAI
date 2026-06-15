"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard, Wrench, ShieldAlert, Zap, Factory,
  MessageSquare, BarChart3, ChevronLeft, ChevronRight, Layers,
} from "lucide-react";
import { useState, useEffect } from "react";

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

const NAV_ITEMS = [
  { href: "/dashboard",    icon: LayoutDashboard, label: "Sherlock Control Center", badge: null },
  { href: "/digital-twin", icon: Layers,          label: "Live Digital Twin",       badge: "Live" },
  { href: "/chat",         icon: MessageSquare,   label: "Sherlock AI Command",     badge: null },
  { href: "/maintenance",  icon: Wrench,          label: "Predictive Reliability",  badge: "3" },
  { href: "/safety",       icon: ShieldAlert,     label: "HSE Risk Management",     badge: "!" },
  { href: "/production",   icon: Factory,         label: "Operations Scheduling",   badge: null },
  { href: "/energy",       icon: Zap,             label: "Energy Efficiency",       badge: null },
  { href: "/reports",      icon: BarChart3,       label: "Executive Reports",       badge: null },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const [user, setUser] = useState<{ name: string; role: string; email: string } | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const u = localStorage.getItem("sherlock_user");
      if (u) setUser(JSON.parse(u));
    }
  }, []);



  return (
    <aside
      className={`flex flex-col h-screen bg-[#1a0712]/70 backdrop-blur-xl border-r border-card-border/40 transition-all duration-300 ${
        collapsed ? "w-16" : "w-64"
      }`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-card-border/40">
        <div className="w-8 h-8 flex items-center justify-center flex-shrink-0">
          <SherlockLogo className="w-8 h-8 drop-shadow-[0_0_10px_rgba(159,18,57,0.5)]" />
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <div className="text-sm font-bold text-white truncate">Tata Steel</div>
            <div className="text-xs text-steel-400 font-medium">Sherlock Platform</div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto text-muted-foreground hover:text-white transition-colors"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* System Status */}
      {!collapsed && (
        <div className="mx-3 my-3 px-3 py-2 rounded-lg bg-green-500/10 border border-green-500/20">
          <div className="flex items-center gap-2">
            <div className="status-dot-green" />
            <span className="text-xs text-green-400 font-medium">All Systems Operational</span>
          </div>
        </div>
      )}

      {/* Nav items */}
      <nav className="flex-1 px-2 py-2 space-y-0.5 overflow-y-auto">
        {NAV_ITEMS.map(({ href, icon: Icon, label, badge }) => {
          const active = pathname === href || pathname.startsWith(href);
          return (
            <Link href={href} key={href}>
              <div
                className={`nav-item ${active ? "active" : ""} ${collapsed ? "justify-center px-2" : ""}`}
                title={collapsed ? label : undefined}
              >
                <Icon size={18} className={active ? "text-steel-400" : ""} />
                {!collapsed && (
                  <span className="flex-1">{label}</span>
                )}
                {!collapsed && badge && (
                  <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
                    badge === "!" ? "bg-red-500 text-white" : "bg-amber-500/20 text-amber-400"
                  }`}>
                    {badge}
                  </span>
                )}
              </div>
            </Link>
          );
        })}
      </nav>

    </aside>
  );
}
