"use client";
import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: LucideIcon;
  iconColor?: string;
  trend?: number;
  trendLabel?: string;
  subValue?: string;
  status?: "good" | "warning" | "critical" | "neutral";
  large?: boolean;
}

const STATUS_CONFIGS = {
  good:     { bg: "from-[#10b981]/15 to-[#059669]/5",   border: "border-[#10b981]/30",  badge: "bg-[#10b981]/20 text-[#34d399]" },
  warning:  { bg: "from-[#f59e0b]/15 to-[#d97706]/5",   border: "border-[#f59e0b]/30",  badge: "bg-[#f59e0b]/20 text-[#fbbf24]" },
  critical: { bg: "from-[#ef4444]/15 to-[#dc2626]/5",   border: "border-[#ef4444]/30",  badge: "bg-[#ef4444]/20 text-[#f87171]" },
  neutral:  { bg: "from-[#94a3b8]/15 to-[#475569]/5",   border: "border-[#94a3b8]/30",  badge: "bg-[#94a3b8]/20 text-[#cbd5e1]" },
};

const SHADOW_CONFIGS = {
  good:     "hover:shadow-[0_0_25px_rgba(16,185,129,0.25)] hover:border-[#10b981]/60",
  warning:  "hover:shadow-[0_0_25px_rgba(245,158,11,0.25)] hover:border-[#f59e0b]/60",
  critical: "hover:shadow-[0_0_25px_rgba(239,68,68,0.25)] hover:border-[#ef4444]/60",
  neutral:  "hover:shadow-[0_0_25px_rgba(148,163,184,0.20)] hover:border-[#94a3b8]/60",
};

export function MetricCard({
  title, value, unit, icon: Icon, iconColor = "text-steel-400",
  trend, trendLabel, subValue, status = "neutral", large = false,
}: MetricCardProps) {
  const cfg = STATUS_CONFIGS[status];
  const shadowClass = SHADOW_CONFIGS[status] || SHADOW_CONFIGS.neutral;
  const isPositiveTrend = trend !== undefined && trend > 0;
  const isNeutralTrend  = trend === 0;

  return (
    <div className={`metric-card bg-gradient-to-br ${cfg.bg} border ${cfg.border} rounded-xl transition-all duration-300 hover:scale-[1.04] ${shadowClass} cursor-pointer ${large ? "p-6" : "p-4"}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className={`p-2 rounded-lg ${cfg.badge}`}>
          <Icon size={large ? 20 : 16} className={iconColor} />
        </div>
        {trend !== undefined && (
          <div className={`flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${
            isNeutralTrend ? "text-gray-400 bg-gray-500/10" :
            isPositiveTrend ? "text-green-400 bg-green-500/10" : "text-red-400 bg-red-500/10"
          }`}>
            {isNeutralTrend ? <Minus size={10} /> : isPositiveTrend ? <TrendingUp size={10} /> : <TrendingDown size={10} />}
            <span>{Math.abs(trend)}%</span>
          </div>
        )}
      </div>

      {/* Value */}
      <div className={`font-bold text-white ${large ? "text-4xl mb-1" : "text-2xl mb-0.5"}`}>
        {value}
        {unit && <span className={`font-normal ml-1 ${large ? "text-xl text-gray-400" : "text-lg text-gray-400"}`}>{unit}</span>}
      </div>

      {/* Title */}
      <div className="text-xs text-muted-foreground font-medium uppercase tracking-wide">{title}</div>

      {/* Sub value or trend label */}
      {(subValue || trendLabel) && (
        <div className="mt-2 text-xs text-muted-foreground">
          {subValue && <span>{subValue}</span>}
          {trendLabel && <span className="ml-1 text-gray-500">{trendLabel}</span>}
        </div>
      )}
    </div>
  );
}
