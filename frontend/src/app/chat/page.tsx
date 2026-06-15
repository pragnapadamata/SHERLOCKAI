"use client";
import { useEffect, useState, useRef, useCallback } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { chatAPI } from "@/lib/api";
import { ChatMessage, AGENT_COLORS, AGENT_ICONS } from "@/types";
import {
  Send, Bot, User, Loader2, ChevronDown, ChevronUp,
  Zap, Shield, Wrench, Factory, BarChart3, Brain,
  Trash2, Info, TrendingUp, Copy, Check,
  Plus, X, Box, FileText, Upload, ChevronRight, AlertTriangle
} from "lucide-react";

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

const AGENT_META: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  MAINTENANCE: { icon: Wrench,    color: "#f59e0b", label: "Predictive Reliability Specialist" },
  SAFETY:      { icon: Shield,    color: "#ef4444", label: "HSE Risk Analyst"      },
  ENERGY:      { icon: Zap,       color: "#10b981", label: "Energy Systems Optimizer"      },
  PRODUCTION:  { icon: Factory,   color: "#06b6d4", label: "Operations Flow Engineer"  },
  REPORTING:   { icon: BarChart3, color: "#db2777", label: "Executive Systems Reporter"   },
  SUPERVISOR:  { icon: Brain,     color: "#9f1239", label: "Sherlock Lead Orchestrator"  },
};

const SUGGESTED = [
  "Analyze gearbox vibration trend for wear prediction.",
  "Identify safety risks on Blast Furnace Hearth #2.",
];

const PLANTS = ["ALL", "Plant-A", "Plant-B", "Plant-C", "Plant-D"];

const MENU_ASSETS = [
  { id: "gearbox", label: "Main Reduction Gearbox" },
  { id: "mill", label: "Hot Strip Rolling Mill" },
  { id: "pump", label: "Blast Furnace Cooling Pump" },
  { id: "tower", label: "Closed-Loop Cooling Tower" },
  { id: "drive", label: "Power Transformer Substation" },
  { id: "conveyor", label: "Raw Ore Belt Conveyor" },
  { id: "crusher", label: "Primary Ore Crusher" },
  { id: "combustor", label: "Induced Draft Fan" },
  { id: "hearth", label: "Blast Furnace Hearth #2" },
  { id: "compressor", label: "Air Compressor Station" }
];

const MENU_INCIDENTS = [
  { id: "INC-2026-120", label: "INC-2026-120", desc: "Fan imbalance from incorrect blade pitch" },
  { id: "INC-2026-119", label: "INC-2026-119", desc: "Gearbox wear from stage-2 bearing friction" },
  { id: "INC-2026-118", label: "INC-2026-118", desc: "Lubrication failure from contaminated oil" }
];

const MENU_SOPS = [
  { id: "SOP-BF-02", label: "SOP-BF-02", desc: "Blast Furnace Startup Procedure" },
  { id: "SOP-TR-09", label: "SOP-TR-09", desc: "Power Transformer Degasification" },
  { id: "SOP-GB-05", label: "SOP-GB-05", desc: "Gearbox Oil Reclamation" }
];

function TypingIndicator() {
  return (
    <div className="flex items-end gap-3">
      <div className="w-8 h-8 rounded-full bg-steel-600/30 border border-steel-600/40 flex items-center justify-center flex-shrink-0">
        <Bot size={15} className="text-steel-400" />
      </div>
      <div className="card-glass rounded-2xl rounded-bl-sm px-4 py-3 border border-card-border max-w-xs">
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-steel-400 animate-bounce" style={{ animationDelay: "0ms" }} />
          <div className="w-1.5 h-1.5 rounded-full bg-steel-400 animate-bounce" style={{ animationDelay: "150ms" }} />
          <div className="w-1.5 h-1.5 rounded-full bg-steel-400 animate-bounce" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  );
}

function AgentBadge({ agent }: { agent: string }) {
  const meta = AGENT_META[agent] || AGENT_META.SUPERVISOR;
  const Icon = meta.icon;
  return (
    <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium border"
      style={{ background: `${meta.color}15`, borderColor: `${meta.color}30`, color: meta.color }}>
      <Icon size={10} />
      {meta.label}
    </div>
  );
}

function RoutingScores({ scores }: { scores: Record<string, number> }) {
  const sorted = Object.entries(scores).sort(([, a], [, b]) => b - a);
  const max = sorted[0]?.[1] || 1;
  return (
    <div className="space-y-1.5 mt-2">
      {sorted.map(([agent, score]) => (
        <div key={agent} className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground w-20 flex-shrink-0">{agent}</span>
          <div className="flex-1 h-1 bg-surface-50 rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all duration-500"
              style={{ width: `${(score / max) * 100}%`, background: AGENT_COLORS[agent] || "#9f1239" }} />
          </div>
          <span className="text-xs font-mono text-muted-foreground w-3">{score}</span>
        </div>
      ))}
    </div>
  );
}

function MessageBubble({ msg }: { msg: ChatMessage }) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied]     = useState(false);
  const isUser = msg.role === "user";

  const handleCopy = () => {
    navigator.clipboard.writeText(msg.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className={`flex items-end gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? "bg-steel-600" : "bg-steel-600/30 border border-steel-600/40"
      }`}>
        {isUser
          ? <User size={14} className="text-white" />
          : <Bot size={14} className="text-steel-400" />
        }
      </div>

      <div className={`flex flex-col gap-1.5 max-w-[75%] ${isUser ? "items-end" : "items-start"}`}>
        {/* Agent badge for assistant */}
        {!isUser && msg.agent && <AgentBadge agent={msg.agent} />}

        {/* Bubble */}
        <div className={`relative group rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-steel-600 text-white rounded-br-sm"
            : "card-glass border border-card-border rounded-bl-sm"
        }`}>
          <p className="text-sm leading-relaxed whitespace-pre-wrap text-white">{msg.content.replace(/\*/g, "")}</p>

          {/* Copy button */}
          <button onClick={handleCopy}
            className="absolute -top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded bg-card border border-card-border">
            {copied ? <Check size={11} className="text-green-400" /> : <Copy size={11} className="text-muted-foreground" />}
          </button>
        </div>

        {/* Confidence */}
        {!isUser && msg.confidence !== undefined && (
          <div className="flex items-center gap-2">
            <div className="w-20 h-1 bg-surface-50 rounded-full overflow-hidden">
              <div className="h-full rounded-full bg-steel-500" style={{ width: `${msg.confidence * 100}%` }} />
            </div>
            <span className="text-xs text-muted-foreground font-mono">{(msg.confidence * 100).toFixed(0)}% confidence</span>
          </div>
        )}

        {/* Expandable reasoning */}
        {!isUser && (msg.reasoning || msg.impact) && (
          <div className="w-full">
            <button onClick={() => setExpanded(v => !v)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-white transition-colors">
              <Info size={10} />
              {expanded ? "Hide" : "Show"} reasoning & impact
              {expanded ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
            </button>
            {expanded && (
              <div className="mt-2 space-y-2 animate-fade-in">
                {msg.reasoning && (
                  <div className="p-2.5 rounded-lg bg-steel-600/10 border border-steel-600/20">
                    <div className="flex items-center gap-1 mb-1">
                      <Info size={10} className="text-steel-400" />
                      <span className="text-xs font-semibold text-steel-400 uppercase tracking-wide">Reasoning</span>
                    </div>
                    <p className="text-xs text-gray-400 leading-relaxed">{msg.reasoning.replace(/\*/g, "")}</p>
                  </div>
                )}
                {msg.impact && (
                  <div className="p-2.5 rounded-lg bg-green-500/10 border border-green-500/20">
                    <div className="flex items-center gap-1 mb-1">
                      <TrendingUp size={10} className="text-green-400" />
                      <span className="text-xs font-semibold text-green-400 uppercase tracking-wide">Expected Impact</span>
                    </div>
                    <p className="text-xs text-gray-400 leading-relaxed">{msg.impact.replace(/\*/g, "")}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Timestamp */}
        <span className="text-xs text-gray-600">
          {msg.timestamp.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages,   setMessages]   = useState<ChatMessage[]>([]);
  const [input,      setInput]      = useState("");
  const [sending,    setSending]    = useState(false);
  const [selectedPlant, setSelectedPlant] = useState("ALL");
  const [routingScores, setRoutingScores] = useState<Record<string, number>>({});
  const [showPanel,  setShowPanel]  = useState(true);
  const [lastAgent,  setLastAgent]  = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLTextAreaElement>(null);

  // Popover menu and attached contexts state
  const [showMenu, setShowMenu] = useState(false);
  const [hoveredSubmenu, setHoveredSubmenu] = useState<"asset" | "incident" | "sop" | null>(null);
  const [attachedContexts, setAttachedContexts] = useState<Array<{
    type: "asset" | "incident" | "sop" | "file";
    id: string;
    label: string;
    text?: string;
  }>>([]);
  const menuRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMenu(false);
        setHoveredSubmenu(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const addContext = (type: "asset" | "incident" | "sop" | "file", id: string, label: string, text?: string) => {
    setAttachedContexts(prev => {
      if (prev.some(c => c.id === id)) return prev;
      return [...prev, { type, id, label, text }];
    });
    setShowMenu(false);
    setHoveredSubmenu(null);
  };

  const removeContext = (id: string) => {
    setAttachedContexts(prev => prev.filter(c => c.id !== id));
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const uploadId = "sys-upload-" + Date.now();
      const uploadingMsg: ChatMessage = {
        id: uploadId,
        role: "assistant",
        content: `⏳ Uploading and processing "${file.name}"...`,
        agent: "SUPERVISOR",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, uploadingMsg]);

      try {
        const res = await chatAPI.uploadFile(file);
        const data = res.data;
        
        addContext("file", file.name, file.name, data.text || "");
        
        setMessages(prev => prev.map(m => m.id === uploadId ? {
          ...m,
          content: `📁 File "${file.name}" uploaded and parsed successfully! ${data.summary || ""} The extracted text context is now attached to your next query.`
        } : m));
      } catch (err: any) {
        console.error(err);
        setMessages(prev => prev.map(m => m.id === uploadId ? {
          ...m,
          content: `⚠️ Failed to upload and process file "${file.name}": ${err.response?.data?.detail || err.message}`
        } : m));
      }
    }
  };

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, sending]);

  const send = useCallback(async (text: string) => {
    if (!text.trim() || sending) return;

    let formattedText = text.trim();
    if (attachedContexts.length > 0) {
      const contextsStr = attachedContexts.map(c => {
        if (c.type === "file" && c.text) {
          return `[FILE: ${c.label} (Content: ${c.text})]`;
        }
        return `[${c.type.toUpperCase()}: ${c.label}]`;
      }).join(" ");
      formattedText = `${formattedText} [Context: ${contextsStr}]`;
    }

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: text.trim(),
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setAttachedContexts([]);
    setSending(true);

    try {
      const history = messages.slice(-6).map(m => ({ role: m.role, content: m.content }));
      const res = await chatAPI.sendMessage(formattedText, selectedPlant, history);
      const d   = res.data;
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: d.response,
        agent: d.agent,
        confidence: d.confidence,
        reasoning: d.reasoning,
        impact: d.impact,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, assistantMsg]);
      setRoutingScores(d.routing_scores || {});
      setLastAgent(d.agent);
    } catch {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "⚠️ Unable to reach the Sherlock backend. Please check the server connection and try again.",
        timestamp: new Date(),
      }]);
    } finally {
      setSending(false);
      inputRef.current?.focus();
    }
  }, [messages, selectedPlant, sending, attachedContexts]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); }
  };

  const clearChat = () => {
    setMessages([]);
    setRoutingScores({});
    setLastAgent(null);
  };

  const lastAgentMeta = lastAgent ? AGENT_META[lastAgent] : null;

  return (
    <AppShell>
      <div className="flex flex-1 min-h-0 overflow-hidden flex-col">
        {/* Top bar */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-card-border/40 bg-surface/80 backdrop-blur-sm flex-shrink-0">
          <div>
            <h1 className="text-xl font-bold text-white">Sherlock AI</h1>
            <p className="text-sm text-muted-foreground mt-0.5">Multi-agent plant intelligence — powered by Sherlock AI</p>
          </div>
          <div className="flex items-center gap-3">
            {/* Plant selector */}
            <div className="flex items-center gap-1 bg-card border border-card-border rounded-lg p-1">
              {PLANTS.map(p => (
                <button key={p} onClick={() => setSelectedPlant(p)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-all ${selectedPlant === p ? "bg-steel-600 text-white" : "text-muted-foreground hover:text-white"}`}>
                  {p}
                </button>
              ))}
            </div>
            {/* Panel toggle */}
            <button onClick={() => setShowPanel(v => !v)}
              className="p-2 rounded-lg bg-card border border-card-border text-muted-foreground hover:text-white transition-all text-xs font-medium flex items-center gap-1.5">
              <Brain size={13} />
              {showPanel ? "Hide" : "Show"} Panel
            </button>
            {/* Clear */}
            {messages.length > 0 && (
              <button onClick={clearChat}
                className="p-2 rounded-lg bg-card border border-card-border text-muted-foreground hover:text-red-400 transition-all">
                <Trash2 size={14} />
              </button>
            )}
          </div>
        </div>

        {/* Body */}
        <div className="flex flex-1 overflow-hidden">

          {/* Chat area */}
          <div className="flex flex-col flex-1 overflow-hidden">

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
              {messages.length === 0 && (
                <div className="flex flex-col items-center justify-center h-full text-center gap-6 py-12">
                  {/* Hero */}
                  <div className="w-16 h-16 rounded-2xl bg-steel-600/20 border border-steel-600/30 flex items-center justify-center glow-steel">
                    <SherlockLogo className="w-10 h-10" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white mb-2">Sherlock Multi-Agent System</h2>
                    <p className="text-sm text-muted-foreground max-w-md">
                      Ask any question about plant operations. The Sherlock Lead Orchestrator routes your query
                      to the most relevant specialist — Predictive Reliability, HSE Risk, Energy Systems, Operations Flow, or Executive Systems.
                    </p>
                  </div>

                  {/* Agent chips */}
                  <div className="flex flex-wrap justify-center gap-2">
                    {Object.entries(AGENT_META).map(([key, meta]) => {
                      const Icon = meta.icon;
                      return (
                        <div key={key} className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border"
                          style={{ background: `${meta.color}10`, borderColor: `${meta.color}25`, color: meta.color }}>
                          <Icon size={11} />
                          {meta.label}
                        </div>
                      );
                    })}
                  </div>

                  {/* Suggested queries */}
                  <div className="w-full max-w-2xl">
                    <p className="text-xs text-muted-foreground uppercase tracking-wide mb-3 font-semibold">Suggested queries</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {SUGGESTED.map(q => (
                        <button key={q} onClick={() => send(q)}
                          className="text-left px-4 py-3 rounded-xl bg-card border border-card-border hover:border-steel-600/40 hover:bg-card-hover transition-all text-sm text-gray-300 hover:text-white">
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)}
              {sending && <TypingIndicator />}
              <div ref={bottomRef} />
            </div>

            {/* Suggested prompts strip (when chat has messages) */}
            {messages.length > 0 && (
              <div className="px-6 pb-2 flex gap-2 overflow-x-auto scrollbar-none flex-shrink-0">
                {SUGGESTED.slice(0, 4).map(q => (
                  <button key={q} onClick={() => send(q)} disabled={sending}
                    className="flex-shrink-0 px-3 py-1.5 rounded-full text-xs bg-card border border-card-border text-muted-foreground hover:text-white hover:border-steel-600/40 transition-all disabled:opacity-50">
                    {q.length > 40 ? q.slice(0, 40) + "…" : q}
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            <div className="px-6 pb-6 pt-2 flex-shrink-0 relative">
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                className="hidden" 
                accept=".pdf,.txt,.doc,.docx"
              />

              {showMenu && (
                <div ref={menuRef} className="absolute bottom-[84px] left-9 bg-[#0c1322]/95 border border-steel-600/40 rounded-xl shadow-2xl p-1 z-50 flex flex-col w-60 backdrop-blur-md animate-fade-in">
                  {/* Asset context */}
                  <div 
                    onMouseEnter={() => setHoveredSubmenu("asset")}
                    className="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer hover:bg-steel-600/20 transition-all group"
                  >
                    <div className="w-8 h-8 rounded-lg bg-steel-600/10 border border-steel-600/20 flex items-center justify-center text-steel-400 group-hover:text-white">
                      <Box size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-white">Asset context</p>
                      <p className="text-[10px] text-muted-foreground">Pin an asset</p>
                    </div>
                    <ChevronRight size={12} className="text-muted-foreground group-hover:text-white" />
                  </div>

                  {/* Incident context */}
                  <div 
                    onMouseEnter={() => setHoveredSubmenu("incident")}
                    className="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer hover:bg-steel-600/20 transition-all group"
                  >
                    <div className="w-8 h-8 rounded-lg bg-steel-600/10 border border-steel-600/20 flex items-center justify-center text-steel-400 group-hover:text-white">
                      <AlertTriangle size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-white">Incident context</p>
                      <p className="text-[10px] text-muted-foreground">Reference an incident</p>
                    </div>
                    <ChevronRight size={12} className="text-muted-foreground group-hover:text-white" />
                  </div>

                  {/* SOP manual */}
                  <div 
                    onMouseEnter={() => setHoveredSubmenu("sop")}
                    className="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer hover:bg-steel-600/20 transition-all group"
                  >
                    <div className="w-8 h-8 rounded-lg bg-steel-600/10 border border-steel-600/20 flex items-center justify-center text-steel-400 group-hover:text-white">
                      <FileText size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-white">SOP manual</p>
                      <p className="text-[10px] text-muted-foreground">Attach a procedure doc</p>
                    </div>
                    <ChevronRight size={12} className="text-muted-foreground group-hover:text-white" />
                  </div>

                  {/* Upload document */}
                  <div 
                    onMouseEnter={() => setHoveredSubmenu(null)}
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center gap-3 p-2.5 rounded-lg cursor-pointer hover:bg-steel-600/20 transition-all group border-t border-card-border/40 mt-1"
                  >
                    <div className="w-8 h-8 rounded-lg bg-steel-600/10 border border-steel-600/20 flex items-center justify-center text-steel-400 group-hover:text-white">
                      <Upload size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-white">Upload document</p>
                      <p className="text-[10px] text-muted-foreground">PDF or TXT as context</p>
                    </div>
                  </div>

                  {/* Submenus */}
                  {hoveredSubmenu === "asset" && (
                    <div className="absolute left-[242px] bottom-0 bg-[#0c1322]/95 border border-steel-600/40 rounded-xl shadow-2xl p-1.5 w-60 z-50 max-h-72 overflow-y-auto backdrop-blur-md animate-fade-in">
                      <p className="text-[10px] font-bold text-steel-400 uppercase tracking-wider px-2 py-1 border-b border-card-border/40 mb-1">ASSET</p>
                      {MENU_ASSETS.map(asset => (
                        <div 
                          key={asset.id}
                          onClick={() => addContext("asset", asset.id, asset.label)}
                          className="p-2 rounded-lg cursor-pointer hover:bg-steel-600/20 text-xs text-gray-300 hover:text-white transition-all text-left"
                        >
                          {asset.label}
                        </div>
                      ))}
                    </div>
                  )}

                  {hoveredSubmenu === "incident" && (
                    <div className="absolute left-[242px] bottom-0 bg-[#0c1322]/95 border border-steel-600/40 rounded-xl shadow-2xl p-1.5 w-64 z-50 backdrop-blur-md animate-fade-in">
                      <p className="text-[10px] font-bold text-steel-400 uppercase tracking-wider px-2 py-1 border-b border-card-border/40 mb-1">INCIDENT</p>
                      {MENU_INCIDENTS.map(inc => (
                        <div 
                          key={inc.id}
                          onClick={() => addContext("incident", inc.id, `${inc.id}: ${inc.desc}`)}
                          className="p-2 rounded-lg cursor-pointer hover:bg-steel-600/20 transition-all text-left"
                        >
                          <p className="text-xs font-semibold text-amber-500">{inc.label}</p>
                          <p className="text-[10px] text-gray-400 line-clamp-1 leading-relaxed">{inc.desc}</p>
                        </div>
                      ))}
                    </div>
                  )}

                  {hoveredSubmenu === "sop" && (
                    <div className="absolute left-[242px] bottom-0 bg-[#0c1322]/95 border border-steel-600/40 rounded-xl shadow-2xl p-1.5 w-64 z-50 backdrop-blur-md animate-fade-in">
                      <p className="text-[10px] font-bold text-steel-400 uppercase tracking-wider px-2 py-1 border-b border-card-border/40 mb-1">SOP MANUAL</p>
                      {MENU_SOPS.map(sop => (
                        <div 
                          key={sop.id}
                          onClick={() => addContext("sop", sop.id, `${sop.id}: ${sop.desc}`)}
                          className="p-2 rounded-lg cursor-pointer hover:bg-steel-600/20 transition-all text-left"
                        >
                          <p className="text-xs font-semibold text-cyan-400">{sop.label}</p>
                          <p className="text-[10px] text-gray-400 line-clamp-1 leading-relaxed">{sop.desc}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3 items-end card-glass rounded-2xl border border-card-border p-3">
                <button
                  onClick={() => setShowMenu(v => !v)}
                  disabled={sending}
                  className="flex-shrink-0 w-9 h-9 rounded-xl bg-steel-600/20 border border-steel-600/30 hover:bg-steel-600/30 text-steel-400 hover:text-white flex items-center justify-center transition-all duration-200 cursor-pointer"
                >
                  <Plus size={16} />
                </button>

                <div className="flex-1 flex flex-col">
                  {/* Attached Contexts */}
                  {attachedContexts.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-2 px-1">
                      {attachedContexts.map(ctx => (
                        <div key={ctx.type + "-" + ctx.id} className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] border bg-steel-600/10 border-steel-600/30 text-white animate-fade-in">
                          <span className="font-semibold text-steel-400 uppercase text-[9px] tracking-wider">{ctx.type}:</span>
                          <span className="truncate max-w-[150px]">{ctx.label}</span>
                          <button onClick={() => removeContext(ctx.id)} className="hover:text-red-400 text-muted-foreground ml-1.5 focus:outline-none">
                            <X size={10} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <textarea
                    ref={inputRef}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about maintenance, safety, energy, production, or request a report…"
                    rows={1}
                    disabled={sending}
                    className="w-full bg-transparent text-sm text-white placeholder:text-gray-600 resize-none focus:outline-none leading-relaxed max-h-32 disabled:opacity-60"
                    style={{ minHeight: "24px" }}
                  />
                </div>

                <button
                  onClick={() => send(input)}
                  disabled={!input.trim() || sending}
                  className="flex-shrink-0 w-9 h-9 rounded-xl bg-steel-600 hover:bg-steel-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-all glow-steel"
                >
                  {sending
                    ? <Loader2 size={15} className="animate-spin text-white" />
                    : <Send size={15} className="text-white" />
                  }
                </button>
              </div>
              <p className="text-xs text-gray-700 mt-2 text-center">
                Enter to send · Shift+Enter for new line · Responses powered by Sherlock AI
              </p>
            </div>
          </div>

          {/* Right panel - agent reasoning */}
          {showPanel && (
            <div className="w-72 flex-shrink-0 border-l border-card-border/40 bg-surface-50 flex flex-col overflow-hidden">
              <div className="px-4 py-4 border-b border-card-border/40">
                <h3 className="font-semibold text-white text-sm">Agent Panel</h3>
                <p className="text-xs text-muted-foreground mt-0.5">Routing & reasoning details</p>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-5">
                {/* Active agent */}
                {lastAgentMeta && lastAgent && (
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wide font-semibold mb-2">Active Agent</p>
                    <div className="p-3 rounded-xl border"
                      style={{ background: `${lastAgentMeta.color}10`, borderColor: `${lastAgentMeta.color}25` }}>
                      <div className="flex items-center gap-2">
                        {(() => { const Icon = lastAgentMeta.icon; return <Icon size={16} style={{ color: lastAgentMeta.color }} />; })()}
                        <span className="font-semibold text-sm text-white">{lastAgentMeta.label}</span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-1.5">
                        Routed by Sherlock Lead Orchestrator based on keyword analysis.
                      </p>
                    </div>
                  </div>
                )}

                {/* Routing scores */}
                {Object.keys(routingScores).length > 0 && (
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wide font-semibold mb-2">Routing Scores</p>
                    <div className="p-3 rounded-xl bg-card border border-card-border">
                      <RoutingScores scores={routingScores} />
                    </div>
                  </div>
                )}

                {/* All agents */}
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide font-semibold mb-2">Available Agents</p>
                  <div className="space-y-2">
                    {Object.entries(AGENT_META).map(([key, meta]) => {
                      const Icon = meta.icon;
                      const isActive = key === lastAgent;
                      return (
                        <div key={key} className={`flex items-center gap-2.5 p-2.5 rounded-lg border transition-all ${
                          isActive
                            ? "border-opacity-40 bg-opacity-10"
                            : "border-card-border bg-card/30"
                        }`}
                          style={isActive ? { borderColor: `${meta.color}40`, background: `${meta.color}08` } : {}}>
                          <div className="w-6 h-6 rounded-md flex items-center justify-center"
                            style={{ background: `${meta.color}20` }}>
                            <Icon size={12} style={{ color: meta.color }} />
                          </div>
                          <span className={`text-xs font-medium ${isActive ? "text-white" : "text-muted-foreground"}`}>
                            {meta.label}
                          </span>
                          {isActive && (
                            <div className="ml-auto w-1.5 h-1.5 rounded-full animate-pulse"
                              style={{ background: meta.color }} />
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Stats */}
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide font-semibold mb-2">Session</p>
                  <div className="p-3 rounded-xl bg-card border border-card-border space-y-2">
                    {[
                      { label: "Messages", value: messages.length },
                      { label: "User queries", value: messages.filter(m => m.role === "user").length },
                      { label: "AI responses", value: messages.filter(m => m.role === "assistant").length },
                      { label: "Plant context", value: selectedPlant },
                    ].map(({ label, value }) => (
                      <div key={label} className="flex justify-between">
                        <span className="text-xs text-muted-foreground">{label}</span>
                        <span className="text-xs font-mono text-white">{value}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
