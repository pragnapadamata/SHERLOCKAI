"use client";
import { Shield, ChevronRight } from "lucide-react";
import { Alert } from "@/types";
import { formatDistanceToNow } from "date-fns";

const SEV_MAP = {
  CRITICAL: { dot: "bg-red-500",    text: "text-red-400",    border: "border-red-500/20",   bg: "bg-red-500/5"    },
  HIGH:     { dot: "bg-amber-500",  text: "text-amber-400",  border: "border-amber-500/20", bg: "bg-amber-500/5"  },
  MEDIUM:   { dot: "bg-yellow-500", text: "text-yellow-400", border: "border-yellow-500/20",bg: "bg-yellow-500/5" },
  LOW:      { dot: "bg-green-500",  text: "text-green-400",  border: "border-green-500/20", bg: "bg-green-500/5"  },
};

// Friendly asset names for live plant codes
const PLANT_LABELS: Record<string, string> = {
  "Plant-A": "Hot Strip Mill",
  "Plant-B": "Coke Oven",
  "Plant-C": "Power Station",
  "Plant-D": "Blast Furnace",
};
const assetLabel = (p: string) => PLANT_LABELS[p] || p;

export function AlertFeed({ alerts }: { alerts: Alert[] }) {
  return (
    <div className="space-y-2">
      {alerts.length === 0 && (
        <div className="text-center py-8 text-muted-foreground text-sm">
          <Shield size={32} className="mx-auto mb-2 text-green-500/40" />
          No active alerts
        </div>
      )}
      {alerts.map((alert) => {
        const cfg = SEV_MAP[alert.severity] || SEV_MAP.LOW;
        let timeAgo = "";
        try { timeAgo = formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true }); }
        catch { timeAgo = "recently"; }

        return (
          <div
            key={alert.id}
            className={`flex items-start gap-3 p-3 rounded-lg border ${cfg.border} ${cfg.bg} hover:border-opacity-60 transition-all cursor-pointer group`}
          >
            <div className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 ${cfg.dot} ${alert.severity === "CRITICAL" ? "animate-pulse" : ""}`} />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-white truncate">{alert.type}</span>
                <span className={`text-xs font-bold flex-shrink-0 ${cfg.text}`}>{alert.severity}</span>
              </div>
              <div className="text-xs text-muted-foreground mt-0.5">
                {assetLabel(alert.plant)} &middot; {alert.unit} &middot; risk {(alert.risk_score * 100).toFixed(0)}%
              </div>
              <div className="text-xs text-gray-600 mt-0.5">{timeAgo}</div>
            </div>
            <ChevronRight size={14} className="text-gray-600 group-hover:text-gray-400 flex-shrink-0 mt-1" />
          </div>
        );
      })}
    </div>
  );
}
