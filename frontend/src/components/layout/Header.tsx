"use client";
import { Bell, RefreshCw, Clock } from "lucide-react";
import { useState, useEffect } from "react";

interface HeaderProps {
  title: string;
  subtitle?: string;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Header({ title, subtitle, onRefresh, isRefreshing }: HeaderProps) {
  const [currentTime, setCurrentTime] = useState("");

  useEffect(() => {
    const update = () => setCurrentTime(new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    update();
    const t = setInterval(update, 1000);
    return () => clearInterval(t);
  }, []);

  return (
    <header className="flex items-center justify-between px-6 py-4 border-b border-card-border/40 bg-surface/80 backdrop-blur-sm sticky top-0 z-10">
      <div>
        <h1 className="text-xl font-bold text-white">{title}</h1>
        {subtitle && <p className="text-sm text-muted-foreground mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-3">
        {/* Live clock */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-card-border text-xs text-muted-foreground font-mono">
          <Clock size={12} className="text-green-400" />
          <span className="text-green-400">{currentTime}</span>
        </div>

        {/* Refresh */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-card border border-card-border text-muted-foreground hover:text-white hover:bg-card-hover transition-all"
            title="Refresh data"
          >
            <RefreshCw size={15} className={isRefreshing ? "animate-spin text-steel-400" : ""} />
          </button>
        )}

        {/* Notifications */}
        <button className="relative p-2 rounded-lg bg-card border border-card-border text-muted-foreground hover:text-white hover:bg-card-hover transition-all">
          <Bell size={15} />
          <span className="absolute -top-0.5 -right-0.5 w-3.5 h-3.5 bg-red-500 rounded-full text-[9px] font-bold text-white flex items-center justify-center">3</span>
        </button>

        {/* Plant selector badge */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-steel-600/10 border border-steel-600/20 text-xs font-medium text-steel-300">
          <div className="w-1.5 h-1.5 rounded-full bg-steel-400 animate-pulse" />
          All Plants
        </div>
      </div>
    </header>
  );
}
