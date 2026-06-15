"use client";
import { TrendingUp, Info, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { AGENT_COLORS, AGENT_ICONS, AGENT_NAMES } from "@/types";

interface AIAnalysisProps {
  agent: string;
  response: string;
  confidence: number;
  reasoning: string;
  impact: string;
  loading?: boolean;
}

export function AIAnalysisCard({ agent, response, confidence, reasoning, impact, loading }: AIAnalysisProps) {
  const [expanded, setExpanded] = useState(true);
  const agentColor = AGENT_COLORS[agent] || "#9f1239";
  const agentIcon  = AGENT_ICONS[agent] || "🤖";
  const confPct    = Math.round(confidence * 100);

  if (loading) {
    return (
      <div className="card-glass rounded-xl p-5 border border-steel-600/20">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-full bg-steel-600/20 animate-pulse" />
          <div className="h-4 w-32 bg-card rounded animate-pulse" />
        </div>
        <div className="space-y-2">
          {[80, 95, 70, 85].map((w, i) => (
            <div key={i} className={`h-3 bg-card rounded animate-pulse`} style={{ width: `${w}%` }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="card-glass rounded-xl border border-steel-600/20 overflow-hidden">
      {/* Header */}
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-card/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full flex items-center justify-center text-lg"
               style={{ background: `${agentColor}20`, border: `1px solid ${agentColor}30` }}>
            {agentIcon}
          </div>
          <div>
            <div className="font-semibold text-white text-sm">{AGENT_NAMES[agent] || `${agent} Specialist`} Analysis</div>
            <div className="text-xs text-muted-foreground">Multi-agent AI · Sherlock Engine</div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Confidence badge */}
          <div className="flex items-center gap-1.5">
            <div className="w-16 h-1.5 bg-surface-50 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${confPct}%`, background: agentColor }}
              />
            </div>
            <span className="text-xs font-mono text-white">{confPct}%</span>
          </div>
          {expanded ? <ChevronUp size={15} className="text-muted-foreground" /> : <ChevronDown size={15} className="text-muted-foreground" />}
        </div>
      </div>

      {/* Body */}
      {expanded && (
        <div className="px-4 pb-4 space-y-4">
          {/* Main response */}
          <div className="prose prose-invert prose-sm max-w-none">
            <div className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{response}</div>
          </div>

          {/* Reasoning & Impact */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 border-t border-card-border/30">
            <div className="p-3 rounded-lg bg-steel-600/10 border border-steel-600/20">
              <div className="flex items-center gap-1.5 mb-1.5">
                <Info size={12} className="text-steel-400" />
                <span className="text-xs font-semibold text-steel-400 uppercase tracking-wide">Reasoning</span>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">{reasoning}</p>
            </div>
            <div className="p-3 rounded-lg bg-green-500/10 border border-green-500/20">
              <div className="flex items-center gap-1.5 mb-1.5">
                <TrendingUp size={12} className="text-green-400" />
                <span className="text-xs font-semibold text-green-400 uppercase tracking-wide">Expected Impact</span>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed">{impact}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
