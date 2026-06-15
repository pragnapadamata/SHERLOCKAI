"use client";
import { useEffect, useState, useRef } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { RefreshCw, Wrench, ShieldAlert, Zap, Factory, AlertTriangle, CheckCircle, Clock, Send, MessageSquare } from "lucide-react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

// Color constants matching: Neon Cyan (#00E5FF), Critical Red (#FF4D4D), Industrial Orange (#FFB347)
const COL = {
  green: 0x00e5ff, // Neon Cyan as Good/Nominal
  amber: 0xffb347, // Industrial Orange
  red: 0xff4d4d,   // Critical Red
  cy: 0x00e5ff,
  pur: 0xa878ff
};

const hexHealth = (h: number) => h >= 70 ? COL.green : h >= 50 ? COL.amber : COL.red;
const hexRisk = (r: string) => r === "low" ? COL.green : r === "medium" ? COL.amber : COL.red;
const hexRul = (d: number) => d >= 60 ? COL.green : d >= 20 ? COL.amber : COL.red;
const cssHex = (n: number) => "#" + n.toString(16).padStart(6, "0");
const isoZone = (h: number) => h >= 80 ? "A" : h >= 60 ? "B" : h >= 40 ? "C" : "D";
const statusTxt = (h: number) => h >= 70 ? "NOMINAL" : h >= 50 ? "DEGRADING" : "CRITICAL";

const recFor = (a: any) => a.health < 50
  ? `Immediate intervention required. ${a.name} is in ISO Zone ${isoZone(a.health)} with ~${a.rul_days}d remaining life. Dispatch work order and stage spares now.`
  : a.health < 70
  ? `Schedule preventive maintenance within ${a.rul_days}d. Increase monitoring frequency and review vibration trend.`
  : `Operating within limits. Continue routine condition monitoring.`;

interface Asset {
  id: string;
  name: string;
  type: string;
  pos: [number, number];
  health: number;
  rul_days: number;
  risk: string;
}

const FALLBACK: { plant: string; assets: Asset[]; links: [string, string][] } = {
  plant: "Tata Steel — Integrated Works",
  assets: [
    { id: "gearbox",   name: "Main Reduction Gearbox",      type: "gearbox",   pos: [16, 14],  health: 45, rul_days: 6,   risk: "critical" },
    { id: "mill",      name: "Hot Strip Rolling Mill",      type: "mill",      pos: [10, 0],   health: 84, rul_days: 120, risk: "low" },
    { id: "pump",      name: "Blast Furnace Cooling Pump",  type: "pump",      pos: [-16, 6],  health: 62, rul_days: 34,  risk: "medium" },
    { id: "tower",     name: "Closed-Loop Cooling Tower",   type: "tower",     pos: [-6, 12],  health: 64, rul_days: 40,  risk: "medium" },
    { id: "drive",     name: "Power Transformer Substation",type: "drive",     pos: [24, 4],   health: 49, rul_days: 9,   risk: "high" },
    { id: "conveyor",  name: "Raw Ore Belt Conveyor",       type: "conveyor",  pos: [-15, -4], health: 83, rul_days: 110, risk: "low" },
    { id: "crusher",   name: "Primary Ore Crusher",         type: "crusher",   pos: [-26, -12], health: 55, rul_days: 22,  risk: "medium" },
    { id: "combustor", name: "Induced Draft Fan",           type: "combustor", pos: [12, -12], health: 90, rul_days: 200, risk: "low" },
    { id: "hearth",    name: "Blast Furnace Hearth #2",     type: "hearth",    pos: [-2, -10],  health: 77, rul_days: 85,  risk: "low" },
    { id: "compressor",name: "Air Compressor Station",     type: "compressor",pos: [-22, 16],  health: 70, rul_days: 50,  risk: "low" },
  ],
  links: [
    ["crusher", "conveyor"], ["conveyor", "hearth"], ["hearth", "combustor"],
    ["hearth", "tower"], ["tower", "pump"], ["pump", "mill"],
    ["mill", "drive"], ["drive", "gearbox"], ["tower", "drive"],
    ["compressor", "hearth"],
  ],
};

export default function SherlockDigitalTwinPage() {
  const [mounted, setMounted] = useState(false);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [links, setLinks] = useState<[string, string][]>([]);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [mode, setMode] = useState<"topology" | "health" | "risk" | "rul">("health");
  const [src, setSrc] = useState<"LIVE" | "DEMO">("DEMO");
  const [fps, setFps] = useState<number>(60);
  const [clock, setClock] = useState<string>("");
  const [workOrderSuccess, setWorkOrderSuccess] = useState<string | null>(null);
  const [timelineMode, setTimelineMode] = useState<"7d" | "30d">("7d");
  
  // Interactive comments state
  const [comments, setComments] = useState<Record<string, string[]>>({
    gearbox: [
      "AI Reliability: Anomaly pattern matched with gear fatigue. Micro-pitting probable.",
      "Operator (R. Kumar): Vibration spike noted on bearing casing. Inspection requested."
    ],
    mill: [
      "Operator (S. Sen): Rollers greased on 14 Jun shift change.",
      "AI Telemetry: Strip output thickness variance remains < 0.2%."
    ],
    pump: [
      "AI Telemetry: Flow output reduced by 4%. Minor cavitation detected.",
      "Operator (A. Patel): Suction valve calibrated."
    ],
    tower: [
      "Operator (M. Das): Checked nozzles, drift eliminators operational.",
      "AI Reliability: Fans stable, current draw normal."
    ],
    drive: [
      "AI Safety: Thermal alarm level-1 triggered at core coil.",
      "Operator (S. Sen): Load temporarily throttled by 10%."
    ],
    conveyor: [
      "Operator (R. Kumar): Belt tension tightened.",
      "AI Telemetry: Motor RPM synchronized with loader gate."
    ],
    crusher: [
      "AI Reliability: Peak shock loading spikes logged.",
      "Operator (A. Patel): Jam on intake hopper chute cleared."
    ],
    combustor: [
      "AI Safety: Temperature gradient normalized at stack base."
    ],
    hearth: [
      "AI Reliability: Hearth thermal model stable.",
      "Operator (M. Das): Replacing thermocouple #4 scheduled."
    ],
    compressor: [
      "Operator (M. Das): Cooling fans clean, pressure within nominal range.",
      "AI Telemetry: Compressor cycle time matches production demand."
    ]
  });

  const [openCommentAssetId, setOpenCommentAssetId] = useState<string | null>(null);

  // Live Agent simulation state
  const [agentLogs, setAgentLogs] = useState<string[]>([
    "[Sherlock Telemetry Sensor] 01:54:12 - Stream synchronized. Processing vibration spectrum at 12kHz.",
    "[Predictive Reliability Specialist] 01:54:15 - Tracking RUL for all 9 components. 2 assets flagged warning.",
    "[Sherlock Knowledge System] 01:54:18 - Searching historical cases. Match found for Gearbox pinion fatigue.",
    "[Sherlock Lead Orchestrator] 01:54:21 - Command network initialized. Plant operations active."
  ]);

  const [agentStates, setAgentStates] = useState<Record<string, string>>({
    telemetry: "MONITORING",
    reliability: "ANALYZING",
    knowledge: "STANDBY",
    maintenance: "IDLE",
    procurement: "IDLE",
    safety: "SECURE",
    supervisor: "ORCHESTRATING"
  });

  const canvasContainerRef = useRef<HTMLDivElement>(null);
  const labelsContainerRef = useRef<HTMLDivElement>(null);
  const labelRefs = useRef<Record<string, HTMLDivElement | null>>({});
  
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const focusTargetRef = useRef<THREE.Vector3 | null>(null);
  const cameraTargetPosRef = useRef<THREE.Vector3 | null>(null);
  const assetObjsRef = useRef<any[]>([]);
  const linkObjsRef = useRef<any[]>([]);

  // Clock tick
  useEffect(() => {
    setMounted(true);
    const tick = () => {
      const now = new Date();
      setClock(now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }));
    };
    tick();
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, []);

  // Fetch digital twin API data
  useEffect(() => {
    if (!mounted) return;
    
    async function load() {
      let data = FALLBACK;
      let source: "LIVE" | "DEMO" = "DEMO";
      try {
        const r = await fetch("http://127.0.0.1:8002/api/twin", { cache: "no-store" });
        if (r.ok) {
          data = await r.json();
          source = "LIVE";
        }
      } catch (e) {
        // use fallback if backend is offline
      }
      
      const OPT_POS: Record<string, [number, number]> = {
        crusher: [-26, -12],
        conveyor: [-15, -4],
        hearth: [-2, -10],
        combustor: [12, -12],
        tower: [-6, 12],
        pump: [-16, 6],
        mill: [10, 0],
        drive: [24, 4],
        gearbox: [16, 14],
        compressor: [-22, 16]
      };
      
      const updatedAssets = data.assets.map(a => ({
        ...a,
        pos: OPT_POS[a.id] || a.pos
      }));

      setAssets(updatedAssets);
      setLinks(data.links);
      setSrc(source);
    }
    load();
  }, [mounted]);

  // Live Agent Simulation logs
  useEffect(() => {
    if (!mounted) return;
    
    const interval = setInterval(() => {
      const msgs = [
        "[Sherlock Telemetry Sensor] Real-time vibration waveforms on Hot Strip Mill normalized.",
        "[Predictive Reliability Specialist] Recalculated stress fatigue curve for Blast Furnace Hearth.",
        "[HSE Risk Analyst] Scanning environment telemetry. Thermal thresholds within limits.",
        "[Sherlock Knowledge System] Querying repair playbook for Closed-Loop Cooling Tower.",
        "[Sherlock Logistics Agent] Sector D warehouse holds 3 spares for pump bearings.",
        "[Predictive Reliability Specialist] Drafted preventive check sheet for Induced Draft Combustor.",
        "[Sherlock Lead Orchestrator] Evaluating optimal throughput against plant health score."
      ];
      
      const selectLog = msgs[Math.floor(Math.random() * msgs.length)];
      const stamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      const fullLog = `[${selectLog.split("]")[0].substring(1)}] ${stamp} - ${selectLog.split("]")[1].trim()}`;
      
      setAgentLogs(prev => [fullLog, ...prev.slice(0, 19)]);

      const states = ["MONITORING", "ANALYZING", "STANDBY", "REASONING", "PROCESSING", "SECURE"];
      setAgentStates(prev => {
        const next = { ...prev };
        Object.keys(next).forEach(k => {
          if (Math.random() > 0.6) {
            next[k] = states[Math.floor(Math.random() * states.length)];
          }
        });
        return next;
      });
    }, 6000);

    return () => clearInterval(interval);
  }, [mounted]);

  // If user selects an asset, dispatch agent logs
  useEffect(() => {
    if (!selectedAsset) return;
    const stamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    setAgentLogs(prev => [
      `[Sherlock Lead Orchestrator] ${stamp} - Critical asset inspect triggered for: ${selectedAsset.name}.`,
      `[Sherlock Telemetry Sensor] ${stamp} - Pulling raw spectral vibrations & temperatures for ${selectedAsset.id}.`,
      `[Predictive Reliability Specialist] ${stamp} - ISO Zone analysis matches degradation pattern. Current zone: ${isoZone(selectedAsset.health)}.`,
      `[Sherlock Knowledge System] ${stamp} - Fetching maintenance recommendations from Sherlock knowledge base.`,
      ...prev.slice(0, 16)
    ]);
    setAgentStates({
      telemetry: "SCANNING",
      reliability: "EVALUATING",
      knowledge: "QUERYING",
      maintenance: "REASONING",
      procurement: "STANDBY",
      safety: "MONITORING",
      supervisor: "ORCHESTRATING"
    });
  }, [selectedAsset]);

  // WebGL Render Loop
  useEffect(() => {
    if (!mounted || assets.length === 0 || !canvasContainerRef.current) return;

    const width = canvasContainerRef.current.clientWidth;
    const height = canvasContainerRef.current.clientHeight;

    // 1. Scene & Fog Setup
    const scene = new THREE.Scene();
    sceneRef.current = scene;
    scene.fog = new THREE.FogExp2(0x0a0f1c, 0.0085); // holographic volumetric fog

    // Navy and black gradient background texture
    const bgCanvas = document.createElement("canvas");
    bgCanvas.width = 8;
    bgCanvas.height = 256;
    const grad = bgCanvas.getContext("2d")?.createLinearGradient(0, 0, 0, 256);
    if (grad) {
      grad.addColorStop(0, "#0a1329");
      grad.addColorStop(0.5, "#070b14");
      grad.addColorStop(1, "#03050a");
      const ctx = bgCanvas.getContext("2d");
      if (ctx) {
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 8, 256);
      }
    }
    scene.background = new THREE.CanvasTexture(bgCanvas);

    // 2. Camera Setup - Zoomed out to fit all 9 assets in the viewport
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 400);
    camera.position.set(30, 24, 45); // wide isometric view
    cameraRef.current = camera;

    // 3. Renderer Setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    canvasContainerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.06;
    controls.target.set(0, 1.0, 0); // centered target
    controls.minDistance = 15;
    controls.maxDistance = 75;
    controls.maxPolarAngle = Math.PI * 0.49;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.25;
    controlsRef.current = controls;

    // Clear target position if user manually orbits
    controls.addEventListener("start", () => {
      cameraTargetPosRef.current = null;
    });

    // 5. Lights — balanced for realistic, dimensional industrial metal
    scene.add(new THREE.HemisphereLight(0x9fc0ff, 0x0e1626, 1.0));
    scene.add(new THREE.AmbientLight(0xbcd2ff, 0.22));

    const dirLight = new THREE.DirectionalLight(0xdbe7ff, 1.2);
    dirLight.position.set(20, 30, 15);
    scene.add(dirLight);

    const fillLight = new THREE.DirectionalLight(0x8fb4ff, 0.42);
    fillLight.position.set(-18, 14, -12);
    scene.add(fillLight);

    const activeOrangeLight = new THREE.PointLight(0xffb347, 8, 25);
    activeOrangeLight.position.set(-2, 2, -10); // under Blast Furnace Hearth
    scene.add(activeOrangeLight);

    const activeCyanLight = new THREE.PointLight(0x00e5ff, 8, 25);
    activeCyanLight.position.set(16, 2, 14); // under Gearbox
    scene.add(activeCyanLight);

    // 6. Floor grid
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(200, 200),
      new THREE.MeshStandardMaterial({ color: 0x121a2e, roughness: 1, metalness: 0 })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.02;
    scene.add(floor);

    const grid = new THREE.GridHelper(160, 80, 0x1a3860, 0x0a1c36);
    grid.material.transparent = true;
    grid.material.opacity = 0.35;
    scene.add(grid);

    // Dynamic orange radial radar coordinate lines
    const lineMat = new THREE.LineBasicMaterial({ color: 0xffb347, transparent: true, opacity: 0.18 });
    for (let i = 0; i < 8; i++) {
      const angle = (i / 8) * Math.PI * 2;
      const pts = [new THREE.Vector3(0, 0.01, 0), new THREE.Vector3(Math.cos(angle) * 85, 0.01, Math.sin(angle) * 85)];
      const lineGeo = new THREE.BufferGeometry().setFromPoints(pts);
      scene.add(new THREE.Line(lineGeo, lineMat));
    }

    // 7. Custom 3D Asset Geometries Builder - Polished industrial silver steel material with diffuse light visibility
    const lighten = (c: number, f = 0.45) => {
      const r = (c >> 16) & 255;
      const g = (c >> 8) & 255;
      const b = c & 255;
      const nr = Math.round(r + (255 - r) * f);
      const ng = Math.round(g + (255 - g) * f);
      const nb = Math.round(b + (255 - b) * f);
      return (nr << 16) + (ng << 8) + nb;
    };
    const matSteel = (color = 0xd0d5e0, met = 0.25, rough = 0.4) => new THREE.MeshStandardMaterial({ color: lighten(color), metalness: met, roughness: rough });
    const matGlow = (color: number, intense = 1.0) => new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: intense,
      metalness: 0.2,
      roughness: 0.3
    });

    const box = (w: number, h: number, d: number, mat: THREE.Material, y = 0) => {
      const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
      mesh.position.y = y + h / 2;
      return mesh;
    };

    const cyl = (rt: number, rb: number, h: number, mat: THREE.Material, y = 0, seg = 24) => {
      const mesh = new THREE.Mesh(new THREE.CylinderGeometry(rt, rb, h, seg), mat);
      mesh.position.y = y + h / 2;
      return mesh;
    };

    const buildMesh = (type: string, health: number) => {
      const g = new THREE.Group();
      const matConcrete = new THREE.MeshStandardMaterial({ color: lighten(0x8a929f, 0.4), metalness: 0.12, roughness: 0.88 });
      const matCopper = new THREE.MeshStandardMaterial({ color: lighten(0xaa6040, 0.35), metalness: 0.9, roughness: 0.2 });

      if (type === "hearth") {
        // BLAST FURNACE (Centerpiece)
        // Concrete base pad
        g.add(box(4.5, 0.4, 4.5, matSteel(0x606570, 0.1, 0.85), 0));
        // Support columns
        g.add(box(0.3, 2.5, 0.3, matSteel(0x3a404a, 0.8, 0.3), 0.4).translateX(-2.0).translateZ(-2.0));
        g.add(box(0.3, 2.5, 0.3, matSteel(0x3a404a, 0.8, 0.3), 0.4).translateX(2.0).translateZ(-2.0));
        g.add(box(0.3, 2.5, 0.3, matSteel(0x3a404a, 0.8, 0.3), 0.4).translateX(-2.0).translateZ(2.0));
        g.add(box(0.3, 2.5, 0.3, matSteel(0x3a404a, 0.8, 0.3), 0.4).translateX(2.0).translateZ(2.0));
        // Mantle platform on top of columns
        g.add(box(4.5, 0.2, 4.5, matSteel(0x404550, 0.7, 0.4), 2.9));

        // Furnace body (stacked vertical components)
        // Cylindrical hearth at bottom
        g.add(cyl(1.8, 2.0, 1.8, matSteel(0x353840, 0.6, 0.5), 0.4));
        // Glowing molten core visible inside a middle chamber gap
        const moltenCore = cyl(1.5, 1.5, 0.4, matGlow(0xff3c00, 2.5), 1.0);
        g.add(moltenCore);
        // Outer tuyeres (pipes) around hearth
        for(let j=0; j<8; j++) {
          const angle = (j / 8) * Math.PI * 2;
          const tuyere = cyl(0.12, 0.12, 0.7, matCopper, 0, 8); // copper
          tuyere.rotation.z = 1.0;
          tuyere.position.set(Math.cos(angle)*1.7, 1.0, Math.sin(angle)*1.7);
          tuyere.rotation.y = -angle;
          g.add(tuyere);
        }

        // Flared stack (bosh + shaft)
        g.add(cyl(1.3, 1.7, 2.8, matSteel(0x707885, 0.8, 0.3), 3.1)); // shaft
        g.add(cyl(1.6, 1.3, 1.2, matSteel(0x5a606d, 0.8, 0.35), 5.9)); // top stack

        // Downcomer main gas pipe
        const downcomerCurve = new THREE.CatmullRomCurve3([
          new THREE.Vector3(0, 6.8, 0),
          new THREE.Vector3(1.8, 7.8, 0),
          new THREE.Vector3(2.8, 4.5, 1.2),
          new THREE.Vector3(2.5, 0.8, 2.0)
        ]);
        const downcomerGeo = new THREE.TubeGeometry(downcomerCurve, 16, 0.24, 8, false);
        g.add(new THREE.Mesh(downcomerGeo, matSteel(0x505663, 0.7, 0.45)));

        // Top platforms & railings
        g.add(box(3.2, 0.12, 3.2, matSteel(0x303540, 0.6, 0.5), 7.1));
        g.add(box(0.1, 7.5, 0.3, matSteel(0x404550, 0.8, 0.3)).translateX(-2.1).translateY(0.4));

        // Exhaust chimneys (two tall pipes on top of the furnace)
        const chimney1 = cyl(0.14, 0.14, 2.6, matSteel(0x707885, 0.7, 0.3), 7.22);
        chimney1.position.set(-0.6, 0, -0.6);
        const chimney2 = cyl(0.14, 0.14, 2.6, matSteel(0x707885, 0.7, 0.3), 7.22);
        chimney2.position.set(0.6, 0, 0.6);
        g.add(chimney1);
        g.add(chimney2);

        // Beacons blinks
        const beacons = [];
        for (let j = 0; j < 3; j++) {
          const angle = (j / 3) * Math.PI * 2;
          const beacon = new THREE.Mesh(new THREE.SphereGeometry(0.16, 8, 8), new THREE.MeshBasicMaterial({ color: 0xff3333 }));
          beacon.position.set(Math.cos(angle) * 1.5, 9.8, Math.sin(angle) * 1.5);
          g.add(beacon);
          beacons.push(beacon);
        }
        g.userData = { animType: "furnace", beacons };
      } 
      
      else if (type === "tower") {
        // COOLING TOWER
        const pts: THREE.Vector2[] = [];
        const profile = [[2.2, 0], [2.1, 0.8], [1.45, 3.2], [1.3, 4.6], [1.5, 5.8], [1.6, 6.2]];
        profile.forEach(([r, y]) => pts.push(new THREE.Vector2(r, y)));
        
        const latheGeo = new THREE.LatheGeometry(pts, 32);
        const latheMesh = new THREE.Mesh(latheGeo, matConcrete);
        latheMesh.position.y = 0.8;
        g.add(latheMesh);
        
        // Base basin floor and rim
        g.add(cyl(2.4, 2.4, 0.4, matSteel(0x5a606d, 0.2, 0.7), 0));
        
        // 16 concrete support columns around open base
        for(let j=0; j<16; j++) {
          const angle = (j / 16) * Math.PI * 2;
          const colMesh = cyl(0.08, 0.08, 0.8, matSteel(0x707885, 0.1, 0.8), 0.4);
          colMesh.position.set(Math.cos(angle) * 2.25, 0.4, Math.sin(angle) * 2.25);
          colMesh.rotation.z = 0.2; // slant outwards
          colMesh.rotation.y = -angle;
          g.add(colMesh);
        }

        // Cooling ribs
        for(let j=1; j<=4; j++) {
          const h = 0.8 + j * 1.2;
          const r = 2.1 - j * 0.2;
          const rib = new THREE.Mesh(new THREE.TorusGeometry(r, 0.04, 6, 32), matSteel(0x606673, 0.2, 0.8));
          rib.rotation.x = Math.PI / 2;
          rib.position.y = h;
          g.add(rib);
        }
        
        // Internal blue water surface
        const water = new THREE.Mesh(new THREE.CircleGeometry(1.9, 24), matGlow(0x00e5ff, 1.2));
        water.rotation.x = -Math.PI / 2;
        water.position.y = 0.45;
        g.add(water);
      } 
      
      else if (type === "mill") {
        // HOT STRIP ROLLING MILL
        g.add(box(5.5, 0.4, 3.2, matSteel(0x404552, 0.5, 0.6)));
        
        const standL = new THREE.Group();
        standL.add(box(0.8, 3.4, 0.6, matSteel(0x6a7488, 0.85, 0.25), 0.4).translateZ(-1.2));
        standL.add(box(0.8, 3.4, 0.6, matSteel(0x6a7488, 0.85, 0.25), 0.4).translateZ(1.2));
        standL.add(box(0.8, 0.6, 3.0, matSteel(0x5a6478, 0.8, 0.3), 3.4));
        standL.position.x = -1.6;
        g.add(standL);

        const standR = standL.clone();
        standR.position.x = 1.6;
        g.add(standR);

        // Walkways
        g.add(box(5.5, 0.08, 0.5, matSteel(0x303540, 0.3, 0.85), 2.2).translateZ(1.65));
        for(let j=0; j<4; j++) {
          const rx = -2.4 + j * 1.6;
          g.add(box(0.04, 0.9, 0.04, matSteel(0x707885, 0.8, 0.3), 2.2).translateX(rx).translateZ(1.85));
        }
        
        // Glowing hot steel strip
        const sheet = box(5.5, 0.10, 1.6, matGlow(0xff4500, 2.5), 1.0);
        g.add(sheet);

        // 4 Rollers spinning
        const rollers = [];
        const rollerSpecs = [
          { y: 0.6, r: 0.35 },
          { y: 1.1, r: 0.20 },
          { y: 1.5, r: 0.20 },
          { y: 2.0, r: 0.35 }
        ];
        for (const spec of rollerSpecs) {
          const roll = cyl(spec.r, spec.r, 2.6, matSteel(0xe0e6f2, 0.95, 0.1), 0, 16);
          roll.rotation.x = Math.PI / 2;
          roll.position.set(0, spec.y + 0.3, 0);
          g.add(roll);
          rollers.push(roll);

          const rollR = roll.clone();
          rollR.position.x = 1.6;
          g.add(rollR);
          rollers.push(rollR);

          const rollL = roll.clone();
          rollL.position.x = -1.6;
          g.add(rollL);
          rollers.push(rollL);
        }

        for(let j=0; j<6; j++) {
          const rx = j < 3 ? -3.4 - j*0.9 : 3.4 + (j-3)*0.9;
          const tableRoll = cyl(0.14, 0.14, 2.0, matSteel(0x8a92a5, 0.8, 0.4));
          tableRoll.rotation.x = Math.PI / 2;
          tableRoll.position.set(rx, 1.1, 0);
          g.add(tableRoll);
          rollers.push(tableRoll);
        }

        g.add(box(1.6, 1.6, 1.8, matSteel(0x404b5a, 0.75, 0.4), 0.4).translateZ(-1.8).translateX(-1.0));
        const mainShaft = cyl(0.25, 0.25, 1.2, matSteel(0xe0e6f2, 0.95, 0.1));
        mainShaft.rotation.x = Math.PI / 2;
        mainShaft.position.set(-1.0, 1.2, -1.0);
        g.add(mainShaft);

        g.userData = { animType: "rollers", rollers };
      } 
      
      else if (type === "gearbox") {
        // MAIN REDUCTION GEARBOX
        g.add(box(3.8, 0.3, 2.8, matSteel(0x5a606d, 0.15, 0.8), 0));

        const bottomCasing = box(3.2, 1.1, 2.2, matSteel(0x505865, 0.8, 0.35), 0.3);
        g.add(bottomCasing);
        
        g.add(box(3.4, 0.12, 2.4, matSteel(0x707886, 0.85, 0.3), 1.4));
        
        const topCasing = box(3.0, 0.9, 1.8, matSteel(0x505865, 0.8, 0.35), 1.52);
        g.add(topCasing);

        const flangeZ = [-1.15, 1.15];
        const flangeX = [-1.6, -1.1, -0.6, 0, 0.6, 1.1, 1.6];
        flangeZ.forEach(fz => {
          flangeX.forEach(fx => {
            const bolt = cyl(0.05, 0.05, 0.18, matSteel(0xbcbfce, 0.9, 0.2), 1.4);
            bolt.position.set(fx, 1.4, fz);
            g.add(bolt);
          });
        });

        for(let j=0; j<8; j++) {
          const fx = -1.4 + j * 0.4;
          g.add(box(0.05, 0.9, 0.15, matSteel(0x707886, 0.8, 0.3), 0.4).translateX(fx).translateZ(1.11));
          g.add(box(0.05, 0.9, 0.15, matSteel(0x707886, 0.8, 0.3), 0.4).translateX(fx).translateZ(-1.11));
        }

        const shaftIn = cyl(0.25, 0.25, 1.5, matSteel(0xe0e6f2, 0.9, 0.15));
        shaftIn.rotation.x = Math.PI / 2;
        shaftIn.position.set(-1.0, 1.0, 1.2);
        g.add(shaftIn);
        
        const shaftOut = cyl(0.42, 0.42, 1.5, matSteel(0xe0e6f2, 0.9, 0.15));
        shaftOut.rotation.x = Math.PI / 2;
        shaftOut.position.set(1.0, 1.0, 1.2);
        g.add(shaftOut);

        const coupIn = cyl(0.4, 0.4, 0.4, matSteel(0x8c94a5, 0.8, 0.3));
        coupIn.rotation.x = Math.PI / 2;
        coupIn.position.set(-1.0, 1.0, 1.5);
        g.add(coupIn);

        const coupOut = cyl(0.6, 0.6, 0.4, matSteel(0x8c94a5, 0.8, 0.3));
        coupOut.rotation.x = Math.PI / 2;
        coupOut.position.set(1.0, 1.0, 1.5);
        g.add(coupOut);

        const warningSlot = box(1.0, 0.25, 0.15, matGlow(health < 50 ? 0xff3333 : 0x00e5ff, 1.5));
        warningSlot.position.set(0, 1.6, 0.91);
        g.add(warningSlot);

        g.userData = { animType: "gearbox", warningSlot, bottomCasing, topCasing };
      } 
      
      else if (type === "conveyor") {
        // RAW ORE BELT CONVEYOR
        const trussL = new THREE.Group();
        trussL.add(box(8.5, 0.2, 1.4, matSteel(0x5a606d, 0.7, 0.4), 1.2));
        
        for(let j=0; j<5; j++) {
          const rx = -3.5 + j * 1.75;
          const d1 = cyl(0.04, 0.04, 1.4, matSteel(0x707886, 0.8, 0.3));
          d1.rotation.z = 0.8;
          d1.position.set(rx + 0.4, 0.6, 0.7);
          trussL.add(d1);

          const d2 = cyl(0.04, 0.04, 1.4, matSteel(0x707886, 0.8, 0.3));
          d2.rotation.z = -0.8;
          d2.position.set(rx + 0.4, 0.6, 0.7);
          trussL.add(d2);

          const d3 = d1.clone();
          d3.position.z = -0.7;
          trussL.add(d3);

          const d4 = d2.clone();
          d4.position.z = -0.7;
          trussL.add(d4);

          trussL.add(box(0.08, 1.2, 0.08, matSteel(0x404552, 0.8, 0.35), 0).translateX(rx).translateZ(0.7));
          trussL.add(box(0.08, 1.2, 0.08, matSteel(0x404552, 0.8, 0.35), 0).translateX(rx).translateZ(-0.7));
        }
        trussL.rotation.z = 0.22;
        trussL.position.set(0, 0.8, 0);
        g.add(trussL);

        const rollers = [];
        const r1 = cyl(0.42, 0.42, 1.5, matSteel(0xe0e6f2, 0.9, 0.2));
        r1.rotation.x = Math.PI / 2;
        r1.position.set(-4.0, 0.4, 0);
        g.add(r1);
        rollers.push(r1);

        const r2 = cyl(0.42, 0.42, 1.5, matSteel(0xe0e6f2, 0.9, 0.2));
        r2.rotation.x = Math.PI / 2;
        r2.position.set(4.0, 2.2, 0);
        g.add(r2);
        rollers.push(r2);

        for(let j=0; j<4; j++) {
          const rx = -2.5 + j * 1.6;
          const subRoll = cyl(0.12, 0.12, 1.4, matSteel(0x707886, 0.8, 0.3));
          subRoll.rotation.x = Math.PI / 2;
          subRoll.position.set(rx, 1.0 + rx*0.22, 0);
          g.add(subRoll);
          rollers.push(subRoll);
        }

        const belt = box(8.2, 0.04, 1.3, matSteel(0x1a1c22, 0.1, 0.85), 1.32);
        belt.rotation.z = 0.22;
        belt.position.set(0, 0.8, 0);
        g.add(belt);

        const ores = [];
        for (let j = 0; j < 5; j++) {
          const ore = new THREE.Mesh(
            new THREE.DodecahedronGeometry(0.24, 0),
            new THREE.MeshStandardMaterial({ color: 0x7a6c62, roughness: 0.9, metalness: 0.1 })
          );
          ore.position.set((j / 4 - 0.5) * 7.5, 1.2 + (j / 4 - 0.5) * 1.65, 0);
          g.add(ore);
          ores.push(ore);
        }

        g.userData = { animType: "rollers", rollers, ores };
      } 
      
      else if (type === "crusher") {
        // PRIMARY ORE CRUSHER
        g.add(box(4.0, 0.3, 4.0, matSteel(0x5a606d, 0.15, 0.85), 0));
        
        g.add(box(0.3, 1.8, 0.3, matSteel(0x404552, 0.8, 0.3), 0.3).translateX(-1.6).translateZ(-1.6));
        g.add(box(0.3, 1.8, 0.3, matSteel(0x404552, 0.8, 0.3), 0.3).translateX(1.6).translateZ(-1.6));
        g.add(box(0.3, 1.8, 0.3, matSteel(0x404552, 0.8, 0.3), 0.3).translateX(-1.6).translateZ(1.6));
        g.add(box(0.3, 1.8, 0.3, matSteel(0x404552, 0.8, 0.3), 0.3).translateX(1.6).translateZ(1.6));

        g.add(cyl(1.8, 2.0, 1.5, matSteel(0x4c525f, 0.75, 0.4), 0.3, 8));

        const feedChute = box(1.0, 0.4, 2.2, matSteel(0x606673, 0.7, 0.45));
        feedChute.rotation.x = 0.5;
        feedChute.position.set(-0.8, 3.4, -0.6);
        g.add(feedChute);

        const hopper = cyl(2.1, 1.5, 1.2, matSteel(0x606673, 0.7, 0.45), 1.8, 8);
        g.add(hopper);

        const jaw = cyl(0.8, 0.8, 1.2, matSteel(0x2d323c, 0.9, 0.2), 1.6);
        g.add(jaw);

        g.add(box(1.2, 1.0, 1.2, matSteel(0x354050, 0.6, 0.5), 0.3).translateX(2.0));

        g.userData = { animType: "crusher", jaw };
      } 
      
      else if (type === "compressor") {
        // AIR COMPRESSOR STATION
        g.add(box(3.8, 0.3, 2.6, matSteel(0x5a606d, 0.1, 0.8), 0));

        const tank = cyl(1.0, 1.0, 3.2, matSteel(0xd1aa34, 0.4, 0.45), 0.3);
        tank.rotation.z = Math.PI / 2;
        tank.position.y = 1.3;
        g.add(tank);

        const domeL = new THREE.Mesh(new THREE.SphereGeometry(1.0, 16, 16), matSteel(0xd1aa34, 0.4, 0.45));
        domeL.position.set(-1.6, 1.3, 0);
        g.add(domeL);
        const domeR = domeL.clone();
        domeR.position.x = 1.6;
        g.add(domeR);

        g.add(box(0.3, 0.4, 2.0, matSteel(0x404550, 0.8, 0.3), 0.3).translateX(-1.0));
        g.add(box(0.3, 0.4, 2.0, matSteel(0x404550, 0.8, 0.3), 0.3).translateX(1.0));

        g.add(box(1.0, 0.8, 1.0, matSteel(0x354050, 0.7, 0.45), 2.3).translateX(-0.6));
        g.add(box(0.8, 1.0, 0.8, matSteel(0x505a6d, 0.75, 0.4), 2.3).translateX(0.6));

        const bypassPipe = new THREE.Group();
        bypassPipe.add(cyl(0.08, 0.08, 0.6, matCopper));
        bypassPipe.position.set(0.6, 3.3, 0);
        g.add(bypassPipe);

        const fanShield = cyl(0.85, 0.85, 0.3, matSteel(0x404552, 0.5, 0.6), 2.3);
        fanShield.rotation.z = Math.PI / 2;
        fanShield.position.x = 1.1;
        g.add(fanShield);

        const fanGroup = new THREE.Group();
        const fanHub = cyl(0.2, 0.2, 0.15, matSteel(0xd0d5df, 0.9, 0.2));
        fanGroup.add(fanHub);
        for(let j=0; j<4; j++) {
          const blade = box(0.65, 0.06, 0.18, matSteel(0x303540, 0.2, 0.8));
          blade.rotation.y = (j * Math.PI) / 2;
          blade.translateX(0.25);
          fanGroup.add(blade);
        }
        fanGroup.position.set(1.2, 2.3, 0);
        g.add(fanGroup);

        g.userData = { animType: "fan", fanMesh: fanGroup };
      }

      else if (type === "drive") {
        // POWER TRANSFORMER
        g.add(box(4.6, 0.3, 3.4, matSteel(0x5a606d, 0.1, 0.85), 0));
        g.add(box(2.2, 1.8, 1.8, matSteel(0x464e5c, 0.8, 0.35), 0.3));

        for(let j=0; j<5; j++) {
          const zOffset = -0.8 + j * 0.4;
          g.add(box(0.1, 1.6, 0.8, matSteel(0x5a6473, 0.75, 0.4), 0.4).translateX(-1.2).translateZ(zOffset));
          g.add(box(0.1, 1.6, 0.8, matSteel(0x5a6473, 0.75, 0.4), 0.4).translateX(1.2).translateZ(zOffset));
        }

        const conservator = cyl(0.35, 0.35, 1.6, matSteel(0x404552, 0.75, 0.4), 2.1);
        conservator.rotation.z = Math.PI / 2;
        conservator.position.y = 2.45;
        g.add(conservator);

        for(let j=0; j<3; j++) {
          const xOffset = -0.6 + j * 0.6;
          const bushing = new THREE.Group();
          bushing.add(cyl(0.08, 0.16, 0.7, matSteel(0x654321, 0.1, 0.8), 2.1));
          bushing.add(cyl(0.02, 0.02, 0.2, matSteel(0xd0d5df, 0.9, 0.2), 2.8));
          bushing.position.x = xOffset;
          g.add(bushing);
        }

        const sparks = [];
        for(let j=0; j<3; j++) {
          const sparkCurve = new THREE.CatmullRomCurve3([
            new THREE.Vector3(-0.6, 3.0, 0),
            new THREE.Vector3(-0.3 + Math.random()*0.1, 3.2 + Math.random()*0.2, Math.random()*0.2),
            new THREE.Vector3(0.3 + Math.random()*0.1, 3.2 + Math.random()*0.2, Math.random()*0.2),
            new THREE.Vector3(0.6, 3.0, 0)
          ]);
          const sparkGeo = new THREE.TubeGeometry(sparkCurve, 8, 0.03, 4, false);
          const sparkMat = new THREE.MeshBasicMaterial({ color: 0x00e5ff, transparent: true, opacity: 0.95 });
          const sparkMesh = new THREE.Mesh(sparkGeo, sparkMat);
          g.add(sparkMesh);
          sparks.push(sparkMesh);
        }

        g.userData = { animType: "transformer", sparks };
      } 
      
      else if (type === "pump") {
        // PUMP STATION
        g.add(box(3.2, 0.3, 2.0, matSteel(0x5a606d, 0.1, 0.8), 0));

        const motor = cyl(0.7, 0.7, 1.8, matSteel(0x3a5372, 0.7, 0.4), 0.3);
        motor.rotation.z = Math.PI / 2;
        motor.position.set(-0.6, 1.0, 0);
        g.add(motor);
        
        for(let j=0; j<5; j++) {
          const rx = -1.2 + j * 0.3;
          const rib = new THREE.Mesh(new THREE.TorusGeometry(0.74, 0.03, 6, 24), matSteel(0x304560, 0.75, 0.45));
          rib.rotation.y = Math.PI / 2;
          rib.position.set(rx, 1.0, 0);
          g.add(rib);
        }

        const pumpVolute = cyl(0.9, 0.9, 0.7, matSteel(0x454b57, 0.8, 0.3), 0.3);
        pumpVolute.rotation.z = Math.PI / 2;
        pumpVolute.position.set(0.9, 1.0, 0);
        g.add(pumpVolute);

        const suctionPipe = cyl(0.22, 0.22, 1.1, matSteel(0x707886, 0.8, 0.3));
        suctionPipe.rotation.x = Math.PI / 2;
        suctionPipe.position.set(0.9, 1.0, 0.9);
        g.add(suctionPipe);

        const dischargePipe = cyl(0.2, 0.2, 1.2, matSteel(0x707886, 0.8, 0.3), 1.0);
        dischargePipe.position.set(0.9, 1.0, 0);
        g.add(dischargePipe);

        const valveWheel = new THREE.Mesh(new THREE.TorusGeometry(0.35, 0.05, 6, 16), matSteel(0xcc3333, 0.2, 0.6));
        valveWheel.rotation.x = Math.PI / 2;
        valveWheel.position.set(0.9, 1.8, 0);
        g.add(valveWheel);
        const valveSpindle = cyl(0.05, 0.05, 0.3, matSteel(0xe0e6f2, 0.9, 0.1), 1.5);
        valveSpindle.position.set(0.9, 0, 0);
        g.add(valveSpindle);

        const shaft = cyl(0.15, 0.15, 0.55, matSteel(0xe0e6f2, 0.95, 0.1));
        shaft.rotation.z = Math.PI / 2;
        shaft.position.set(0.28, 1.0, 0);
        g.add(shaft);

        g.userData = { animType: "pump", shaft };
      } 
      
      else if (type === "combustor") {
        // INDUCED DRAFT FAN
        g.add(box(3.6, 0.3, 3.2, matSteel(0x5a606d, 0.1, 0.8), 0));

        const casing = cyl(1.8, 1.8, 0.9, matSteel(0x525c6d, 0.8, 0.35), 0.3);
        casing.rotation.x = Math.PI / 2;
        casing.position.set(-0.2, 1.6, 0);
        g.add(casing);

        g.add(box(0.85, 2.4, 0.85, matSteel(0x525c6d, 0.8, 0.35), 1.4).translateX(1.2).translateY(0.4));

        const torusMesh = new THREE.Mesh(new THREE.TorusGeometry(1.2, 0.06, 6, 24), matSteel(0x8a92a5, 0.9, 0.2));
        torusMesh.position.set(-0.2, 1.6, 0.46);
        g.add(torusMesh);

        g.add(box(1.2, 1.1, 1.2, matSteel(0x3a485a, 0.7, 0.45), 0.3).translateX(-1.6).translateZ(-0.4));

        const fanGroup = new THREE.Group();
        const fanHub = cyl(0.28, 0.28, 0.85, matSteel(0xd0d5df, 0.9, 0.15));
        fanHub.rotation.x = Math.PI / 2;
        fanGroup.add(fanHub);

        for(let j=0; j<8; j++) {
          const blade = box(0.1, 1.15, 0.75, matSteel(0x303540, 0.5, 0.6));
          blade.rotation.z = (j * Math.PI) / 4;
          fanGroup.add(blade);
        }
        fanGroup.position.set(-0.2, 1.6, 0.05);
        g.add(fanGroup);

        g.userData = { animType: "fan", fanMesh: fanGroup };
      }

      // Add glowing status IoT indicator node to make shape nice & representable
      const iotColor = hexHealth(health);
      const iotNode = cyl(0.12, 0.12, 0.45, matGlow(iotColor, 1.5), 0);
      if (type === "hearth") iotNode.position.set(0, 9.8, 0);
      else if (type === "tower") iotNode.position.set(0, 7.0, 0);
      else if (type === "mill") iotNode.position.set(0, 4.0, 0);
      else if (type === "gearbox") iotNode.position.set(0, 2.6, 0);
      else if (type === "conveyor") iotNode.position.set(3.8, 3.2, 0);
      else if (type === "crusher") iotNode.position.set(0, 3.2, 0);
      else if (type === "compressor") iotNode.position.set(0, 3.3, 0);
      else if (type === "drive") iotNode.position.set(0, 3.8, 0);
      else if (type === "pump") iotNode.position.set(0.9, 2.0, 0);
      else if (type === "combustor") iotNode.position.set(-0.2, 3.4, 0);
      g.add(iotNode);

      g.traverse(o => {
        if (o instanceof THREE.Mesh) o.castShadow = true;
      });
      return g;
    };

    // 8. Build Scene Asset Units
    const tempAssetObjs: any[] = [];
    assets.forEach(a => {
      const grp = new THREE.Group();
      grp.position.set(a.pos[0], 0, a.pos[1]);

      // Foundation pad
      const pad = new THREE.Mesh(
        new THREE.CylinderGeometry(2.8, 3.0, 0.3, 24),
        matSteel(0x0f1a2e, 0.4, 0.6)
      );
      pad.position.y = 0.15;
      grp.add(pad);

      // Glowing Double Status Rings under the assets
      const rColor = hexHealth(a.health);
      
      // Main neon ring
      const ringMat = new THREE.MeshBasicMaterial({ color: rColor, transparent: true, opacity: 0.95 });
      const ring = new THREE.Mesh(new THREE.TorusGeometry(2.9, 0.08, 8, 48), ringMat);
      ring.rotation.x = Math.PI / 2;
      ring.position.y = 0.33;
      grp.add(ring);

      // Outer soft glowing pulse ring
      const ring2Mat = new THREE.MeshBasicMaterial({ color: rColor, transparent: true, opacity: 0.12 });
      const ring2 = new THREE.Mesh(new THREE.TorusGeometry(2.9, 0.24, 8, 48), ring2Mat);
      ring2.rotation.x = Math.PI / 2;
      ring2.position.y = 0.33;
      grp.add(ring2);

      // Custom models
      const model = buildMesh(a.type, a.health);
      model.position.y = 0.3;
      grp.add(model);

      scene.add(grp);

      // Elevated height offsets for labels to float cleanly above meshes
      const labelOffset = ({
        hearth: 10.8,
        tower: 8.0,
        mill: 4.8,
        gearbox: 3.4,
        conveyor: 4.6,
        crusher: 4.0,
        compressor: 4.0,
        drive: 4.6,
        pump: 3.2,
        combustor: 4.2
      })[a.type] || 4.2;

      tempAssetObjs.push({
        data: a,
        group: grp,
        ring,
        ring2,
        model,
        labelOffset
      });
    });
    assetObjsRef.current = tempAssetObjs;

    // 9. Build Telemetry Pipelines with Glide packets
    const tempLinkObjs: any[] = [];
    const byId: Record<string, any> = {};
    tempAssetObjs.forEach(o => {
      byId[o.data.id] = o;
    });

    links.forEach(([f, t]) => {
      const a = byId[f];
      const b = byId[t];
      if (!a || !b) return;

      const pa = a.group.position.clone().setY(0.5);
      const pb = b.group.position.clone().setY(0.5);
      // Elevate the center to make Bezier arch
      const mid = pa.clone().lerp(pb, 0.5).setY(3.2);

      const curve = new THREE.QuadraticBezierCurve3(pa, mid, pb);
      const tubeGeo = new THREE.TubeGeometry(curve, 32, 0.06, 8, false);

      const isCrit = a.data.health < 50 || b.data.health < 50;
      const tColor = isCrit ? COL.red : COL.cy;
      
      const mat = new THREE.MeshBasicMaterial({
        color: tColor,
        transparent: true,
        opacity: 0.5
      });
      const tube = new THREE.Mesh(tubeGeo, mat);
      scene.add(tube);

      // 3 data packet flow dots glide along pipelines
      const flowDots: THREE.Mesh[] = [];
      for (let j = 0; j < 3; j++) {
        const dot = new THREE.Mesh(
          new THREE.SphereGeometry(0.15, 8, 8),
          new THREE.MeshBasicMaterial({ color: tColor })
        );
        scene.add(dot);
        flowDots.push(dot);
      }

      tempLinkObjs.push({ tube, a, b, curve, flowDots, speeds: [0.15, 0.15, 0.15], offsets: [0, 0.33, 0.66] });
    });
    linkObjsRef.current = tempLinkObjs;

    // 10. Atmospheric Volumetric Particle Setup
    const particles: any[] = [];
    const bfPos = new THREE.Vector3(-2, 8.2, -10); // Blast Furnace top coordinates
    const ctPos = new THREE.Vector3(-6, 7.2, 12);  // Cooling Tower top coordinates

    // A. Blast Furnace Hearth Smoke (glowy red/orange smoke rising)
    for (let i = 0; i < 15; i++) {
      const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.12 + Math.random() * 0.16, 6, 6),
        new THREE.MeshBasicMaterial({
          color: 0xff4d4d,
          transparent: true,
          opacity: 0.65,
          blending: THREE.AdditiveBlending
        })
      );
      mesh.position.copy(bfPos).add(new THREE.Vector3(
        (Math.random() - 0.5) * 0.4,
        Math.random() * 1.5,
        (Math.random() - 0.5) * 0.4
      ));
      scene.add(mesh);
      particles.push({
        mesh,
        type: "smoke",
        vy: 1.2 + Math.random() * 0.8,
        vx: (Math.random() - 0.5) * 0.25,
        vz: (Math.random() - 0.5) * 0.25,
        origin: bfPos.clone(),
        maxHeight: 6.0
      });
    }

    // B. Cooling Tower Steam (white/cyan clean water vapor rising)
    for (let i = 0; i < 15; i++) {
      const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.18 + Math.random() * 0.22, 6, 6),
        new THREE.MeshBasicMaterial({
          color: 0x88f5ff,
          transparent: true,
          opacity: 0.4,
          blending: THREE.AdditiveBlending
        })
      );
      mesh.position.copy(ctPos).add(new THREE.Vector3(
        (Math.random() - 0.5) * 0.5,
        Math.random() * 1.5,
        (Math.random() - 0.5) * 0.5
      ));
      scene.add(mesh);
      particles.push({
        mesh,
        type: "steam",
        vy: 0.9 + Math.random() * 0.6,
        vx: (Math.random() - 0.5) * 0.2,
        vz: (Math.random() - 0.5) * 0.2,
        origin: ctPos.clone(),
        maxHeight: 5.5
      });
    }

    // C. Ambient grid holographic glowing embers
    for (let i = 0; i < 70; i++) {
      const mesh = new THREE.Mesh(
        new THREE.SphereGeometry(0.04 + Math.random() * 0.05, 4, 4),
        new THREE.MeshBasicMaterial({
          color: Math.random() > 0.4 ? 0x00e5ff : 0xffb347,
          transparent: true,
          opacity: 0.15 + Math.random() * 0.4
        })
      );
      mesh.position.set(
        (Math.random() - 0.5) * 70,
        Math.random() * 18,
        (Math.random() - 0.5) * 70
      );
      scene.add(mesh);
      particles.push({
        mesh,
        type: "ember",
        vy: (Math.random() - 0.5) * 0.22,
        vx: (Math.random() - 0.5) * 0.22,
        vz: (Math.random() - 0.5) * 0.22,
        life: Math.random() * 6,
        maxLife: 6 + Math.random() * 6
      });
    }

    // 11. Raycast Selection Handlers
    let downPt = { x: 0, y: 0 };
    const handleMouseDown = (e: MouseEvent) => {
      downPt = { x: e.clientX, y: e.clientY };
    };

    const handleMouseUp = (e: MouseEvent) => {
      if (Math.hypot(e.clientX - downPt.x, e.clientY - downPt.y) > 6) return; // ignore dragging

      const rect = renderer.domElement.getBoundingClientRect();
      const mouseX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const mouseY = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      const ray = new THREE.Raycaster();
      ray.setFromCamera(new THREE.Vector2(mouseX, mouseY), camera);

      const hitList = tempAssetObjs.map(o => o.group);
      const hits = ray.intersectObjects(hitList, true);

      if (hits.length > 0) {
        let hitObj = hits[0].object;
        while (hitObj.parent && hitObj.parent !== scene) {
          const matched = tempAssetObjs.find(o => o.group === hitObj.parent);
          if (matched) {
            setSelectedAsset(matched.data);
            controls.autoRotate = false;
            
            // Focus camera targets
            const p = matched.group.position;
            focusTargetRef.current = new THREE.Vector3(p.x, 1.2, p.z);
            cameraTargetPosRef.current = new THREE.Vector3(p.x + 7, p.y + 6, p.z + 9);
            break;
          }
          hitObj = hitObj.parent;
        }
      }
    };
    renderer.domElement.addEventListener("mousedown", handleMouseDown);
    renderer.domElement.addEventListener("mouseup", handleMouseUp);

    // 12. Frame Animation Loop
    let animId = 0;
    let lastTime = performance.now();
    let frameCount = 0;
    let fpsAccumulator = 0;

    const animate = (now: number) => {
      animId = requestAnimationFrame(animate);
      const dt = (now - lastTime) / 1000;
      lastTime = now;

      // Update FPS indicator
      frameCount++;
      fpsAccumulator += dt;
      if (fpsAccumulator >= 0.5) {
        setFps(Math.round(frameCount / fpsAccumulator));
        frameCount = 0;
        fpsAccumulator = 0;
      }

      // Base models bobs, ring pulses, hover scales
      tempAssetObjs.forEach((o, i) => {
        o.ring.rotation.z += dt * 0.45;
        o.model.position.y = 0.3 + Math.sin(now * 0.0015 + i) * 0.035;
        
        const isSel = selectedAsset?.id === o.data.id;
        const scale = isSel ? 1.15 : 1.0;
        o.model.scale.lerp(new THREE.Vector3(scale, scale, scale), 0.12);
        
        // Double rings pulsing brightness
        const pulse = 0.12 + 0.12 * Math.abs(Math.sin(now * 0.002 + i));
        (o.ring2.material as any).opacity = isSel ? 0.38 : pulse;

        // Custom geometries animations
        const userData = o.model.userData;
        if (userData.animType === "fan") {
          userData.fanMesh.rotation.y += dt * 7.5;
        } else if (userData.animType === "rollers") {
          userData.rollers.forEach((r: THREE.Mesh) => {
            r.rotation.x += dt * 5.0;
          });
          if (userData.ores) {
            userData.ores.forEach((ore: THREE.Mesh) => {
              ore.position.x += dt * 0.8;
              ore.position.y = 1.32 + ore.position.x * 0.22;
              if (ore.position.x > 3.8) {
                ore.position.x = -3.8;
              }
            });
          }
        } else if (userData.animType === "pump") {
          userData.shaft.rotation.x += dt * 7.0;
        } else if (userData.animType === "transformer") {
          // pulsing electricity arc meshes
          userData.sparks.forEach((spk: THREE.Mesh, sIdx: number) => {
            spk.visible = Math.random() > 0.45;
            (spk.material as any).opacity = 0.3 + 0.7 * Math.sin(now * 0.008 + sIdx);
          });
        } else if (userData.animType === "furnace") {
          // red beacons blinking
          userData.beacons.forEach((beac: THREE.Mesh) => {
            (beac.material as any).emissiveIntensity = Math.sin(now * 0.005) > 0 ? 1.3 : 0.25;
          });
        } else if (userData.animType === "gearbox") {
          if (o.data.health < 50) {
            const redPulse = 0.05 + 0.25 * Math.abs(Math.sin(now * 0.006));
            (userData.bottomCasing.material as any).emissive.setHex(0xff0000);
            (userData.bottomCasing.material as any).emissiveIntensity = redPulse;
            (userData.topCasing.material as any).emissive.setHex(0xff0000);
            (userData.topCasing.material as any).emissiveIntensity = redPulse;
            (userData.warningSlot.material as any).emissiveIntensity = 0.4 + 1.2 * Math.abs(Math.sin(now * 0.009));
          } else {
            (userData.bottomCasing.material as any).emissive.setHex(0x000000);
            (userData.topCasing.material as any).emissive.setHex(0x000000);
            (userData.warningSlot.material as any).emissiveIntensity = 1.0;
          }
        } else if (userData.animType === "crusher") {
          userData.jaw.rotation.x = Math.sin(now * 0.02) * 0.08;
          userData.jaw.rotation.z = Math.cos(now * 0.02) * 0.08;
        }
      });

      // Flow telemetries dots along pipelines
      tempLinkObjs.forEach(l => {
        l.offsets.forEach((off: number, oIdx: number) => {
          let t = off + dt * l.speeds[oIdx];
          if (t > 1.0) t = 0.0;
          l.offsets[oIdx] = t;
          const pos = l.curve.getPointAt(t);
          l.flowDots[oIdx].position.copy(pos);
        });
      });

      // Emitter particles animate
      particles.forEach(p => {
        if (p.type === "smoke" || p.type === "steam") {
          p.mesh.position.y += dt * p.vy;
          p.mesh.position.x += dt * p.vx;
          p.mesh.position.z += dt * p.vz;
          
          const relativeY = p.mesh.position.y - p.origin.y;
          const pct = relativeY / p.maxHeight;
          
          (p.mesh.material as any).opacity = Math.max(0, (p.type === "smoke" ? 0.65 : 0.4) * (1 - pct));
          p.mesh.scale.setScalar(1.0 + pct * 1.6);
          
          if (relativeY > p.maxHeight) {
            p.mesh.position.copy(p.origin).add(new THREE.Vector3(
              (Math.random() - 0.5) * 0.3,
              0,
              (Math.random() - 0.5) * 0.3
            ));
            p.mesh.scale.setScalar(1.0);
          }
        } else if (p.type === "ember") {
          p.mesh.position.y += dt * p.vy;
          p.mesh.position.x += dt * p.vx;
          p.mesh.position.z += dt * p.vz;
          
          p.life += dt;
          if (p.life > p.maxLife) {
            p.life = 0;
            p.mesh.position.set(
              (Math.random() - 0.5) * 70,
              Math.random() * 18,
              (Math.random() - 0.5) * 70
            );
          }
        }
      });

      // Smooth zoom transition interpolations
      if (focusTargetRef.current) {
        controls.target.lerp(focusTargetRef.current, 0.06);
        if (cameraTargetPosRef.current) {
          camera.position.lerp(cameraTargetPosRef.current, 0.06);
        }
      }
      controls.update();

      // Project 3D labels to screens coordinates
      const container = canvasContainerRef.current;
      if (container) {
        const cW = container.clientWidth;
        const cH = container.clientHeight;

        tempAssetObjs.forEach(o => {
          const tempV = new THREE.Vector3(o.group.position.x, o.labelOffset, o.group.position.z);
          tempV.project(camera);

          const x = (tempV.x * 0.5 + 0.5) * cW;
          const y = (tempV.y * -0.5 + 0.5) * cH;

          const el = labelRefs.current[o.data.id];
          if (el) {
            if (tempV.z > 1.0) {
              el.style.display = "none";
            } else {
              el.style.display = "block";
              el.style.transform = `translate(-50%, -100%) translate(${x}px, ${y}px)`;
            }
          }
        });
      }

      renderer.render(scene, camera);
    };

    animate(performance.now());

    // 13. Window Resize Handler
    const handleResize = () => {
      if (!canvasContainerRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = canvasContainerRef.current.clientWidth;
      const h = canvasContainerRef.current.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      if (rendererRef.current && canvasContainerRef.current) {
        try {
          canvasContainerRef.current.removeChild(rendererRef.current.domElement);
        } catch (e) {
          // ignore clean error
        }
      }
    };
  }, [mounted, assets, selectedAsset]);

  // Recolor / update visual modes on selected tab (Topology, Health, Risk, RUL)
  useEffect(() => {
    if (assets.length === 0 || assetObjsRef.current.length === 0) return;

    assetObjsRef.current.forEach(o => {
      let hex = hexHealth(o.data.health);
      let val = `HEALTH ${o.data.health}%`;
      let pct = o.data.health;

      if (mode === "risk") {
        hex = hexRisk(o.data.risk);
        val = `RISK ${o.data.risk.toUpperCase()}`;
        pct = o.data.risk === "low" ? 90 : o.data.risk === "medium" ? 60 : 30;
      } 
      else if (mode === "rul") {
        hex = hexRul(o.data.rul_days);
        val = `RUL ${o.data.rul_days}d`;
        pct = Math.min(100, (o.data.rul_days / 200) * 100);
      } 
      else if (mode === "topology") {
        hex = COL.cy;
        val = o.data.type.toUpperCase();
        pct = 100;
      }

      (o.ring.material as any).color.setHex(hex);
      (o.ring2.material as any).color.setHex(hex);

      // Directly update DOM element nodes to bypass React rendering bottleneck
      const textEl = document.getElementById(`lbl-val-${o.data.id}`);
      const progressEl = document.getElementById(`lbl-fill-${o.data.id}`);
      if (textEl) {
        textEl.textContent = val;
        textEl.style.color = cssHex(hex);
      }
      if (progressEl) {
        progressEl.style.width = `${pct}%`;
        progressEl.style.background = cssHex(hex);
      }
    });

    linkObjsRef.current.forEach(l => {
      const isCrit = mode === "topology" ? false : (l.a.data.health < 50 || l.b.data.health < 50);
      const color = isCrit ? COL.red : COL.cy;
      (l.tube.material as any).color.setHex(color);
      l.flowDots.forEach((d: THREE.Mesh) => (d.material as any).color.setHex(color));
    });
  }, [mode, assets]);

  const closeDetail = () => {
    setSelectedAsset(null);
    if (controlsRef.current) {
      controlsRef.current.autoRotate = true;
    }
    focusTargetRef.current = null;
    cameraTargetPosRef.current = null;
  };

  // Sparkline path generator helper
  const generateSparklineData = (assetId: string) => {
    const seed = assetId.charCodeAt(0) + assetId.charCodeAt(1);
    const points = [];
    for (let i = 0; i < 12; i++) {
      const val = 15 + Math.sin((i + seed) * 0.7) * 8 + Math.cos(i + seed) * 4;
      points.push(val);
    }
    const width = 110;
    const height = 24;
    const step = width / (points.length - 1);
    const min = Math.min(...points);
    const max = Math.max(...points);
    const range = max - min || 1;
    const coords = points.map((p, idx) => {
      const x = idx * step;
      const y = height - ((p - min) / range) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    });
    return `M ${coords.join(" L ")}`;
  };

  // Drawer historical trend data
  const getMockTelemetryData = (assetId: string, type: "vibration" | "temp" | "pressure") => {
    const isCritical = assetId === "gearbox" || assetId === "drive";
    const isDegraded = assetId === "pump" || assetId === "tower" || assetId === "crusher";
    
    let base = 50;
    if (type === "vibration") {
      base = isCritical ? 8.2 : isDegraded ? 4.8 : 1.9;
    } else if (type === "temp") {
      base = isCritical ? 92 : isDegraded ? 78 : 62;
    } else {
      base = isCritical ? 4.8 : isDegraded ? 3.4 : 2.1;
    }
    
    const points = [];
    const seed = assetId.charCodeAt(0) + type.charCodeAt(0);
    for (let i = 0; i < 15; i++) {
      const noise = Math.sin(i * 0.95 + seed) * (base * 0.08) + Math.cos(i * 1.5) * (base * 0.04);
      points.push(Math.max(0.1, base + noise));
    }
    // inject anomaly spike at tail for alerts
    if (isCritical) {
      points[points.length - 1] += base * 0.25;
      points[points.length - 2] += base * 0.15;
    } else if (isDegraded && Math.random() > 0.4) {
      points[points.length - 1] += base * 0.12;
    }
    return points;
  };

  const renderTrendSVG = (color: string, points: number[]) => {
    const w = 180;
    const h = 40;
    const step = w / (points.length - 1);
    const min = Math.min(...points);
    const max = Math.max(...points);
    const range = max - min || 1;
    const coords = points.map((p, idx) => {
      const x = idx * step;
      const y = h - ((p - min) / range) * (h - 6) - 3;
      return `${x},${y}`;
    });
    const pathD = `M ${coords.join(" L ")}`;
    const areaD = `${pathD} L ${w},${h} L 0,${h} Z`;
    return (
      <svg width={w} height={h} className="overflow-visible">
        <defs>
          <linearGradient id={`grad-${color}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.4" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>
        </defs>
        <path d={areaD} fill={`url(#grad-${color})`} />
        <path d={pathD} fill="none" stroke={color} strokeWidth="1.8" />
      </svg>
    );
  };

  const handleWorkOrder = (assetId: string) => {
    setWorkOrderSuccess(assetId);
    const stamp = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    setAgentLogs(prev => [
      `[Sherlock Lead Orchestrator] ${stamp} - DISPATCH: Work order generated for ${selectedAsset?.name}.`,
      `[Sherlock Logistics Agent] ${stamp} - RESERVED: Spare bearings and seals dispatched from sector D.`,
      `[Predictive Reliability Specialist] ${stamp} - SCHEDULED: Technician assigned to WO-2026-${selectedAsset?.id.toUpperCase()}.`,
      ...prev
    ]);
    setTimeout(() => {
      setWorkOrderSuccess(null);
    }, 4000);
  };

  const timeline7d = [
    { date: "16 Jun", asset: "Main Reduction Gearbox", type: "gearbox", rul: "6 days", prob: "94%", risk: "CRITICAL" },
    { date: "19 Jun", asset: "Main Rolling Mill Drive", type: "drive", rul: "9 days", prob: "88%", risk: "HIGH" },
    { date: "22 Jun", asset: "Primary Ore Crusher", type: "crusher", rul: "22 days", prob: "65%", risk: "MEDIUM" }
  ];
  
  const timeline30d = [
    { date: "16 Jun", asset: "Main Reduction Gearbox", type: "gearbox", rul: "6 days", prob: "94%", risk: "CRITICAL" },
    { date: "19 Jun", asset: "Main Rolling Mill Drive", type: "drive", rul: "9 days", prob: "88%", risk: "HIGH" },
    { date: "22 Jun", asset: "Primary Ore Crusher", type: "crusher", rul: "22 days", prob: "65%", risk: "MEDIUM" },
    { date: "08 Jul", asset: "Blast Furnace Cooling Pump", type: "pump", rul: "34 days", prob: "45%", risk: "MEDIUM" },
    { date: "14 Jul", asset: "Closed-Loop Cooling Tower", type: "tower", rul: "40 days", prob: "42%", risk: "LOW" }
  ];

  const activeTimeline = timelineMode === "7d" ? timeline7d : timeline30d;

  if (!mounted) {
    return (
      <div className="fixed inset-0 bg-[#0a0f1c] flex flex-col items-center justify-center gap-4 text-white font-sans">
        <RefreshCw size={24} className="animate-spin text-[#00e5ff]" />
        <span>Booting Digital Twin Command Center...</span>
      </div>
    );
  }

  return (
    <AppShell>
      <div className="relative w-full h-full min-h-[calc(100vh-0px)] bg-[#0a0f1c] overflow-hidden text-[#e7eefb] font-sans flex flex-col">
        
        {/* Dynamic style sheet to load fonts and maintain style fidelity */}
        <link href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet" />
        
        <style dangerouslySetInnerHTML={{__html: `
          :root {
            --cy: #00e5ff;
            --green: #00e5ff;
            --amber: #ffb347;
            --red: #ff4d4d;
            --pur: #a878ff;
            --txt: #e7eefb;
            --muted: #8ea0c0;
            --dim: #435b80;
            --mono: 'JetBrains Mono', monospace;
            --disp: 'Chakra Petch', sans-serif;
          }
          .twin-body {
            font-family: var(--disp);
            height: 100%;
            overflow: hidden;
            background: #070b14;
            color: var(--txt);
          }
          /* scan lines and screen effects */
          .scanlines {
            position: absolute;
            inset: 0;
            pointer-events: none;
            background: linear-gradient(
              rgba(18, 16, 16, 0) 50%, 
              rgba(0, 0, 0, 0.28) 50%
            ), linear-gradient(
              90deg, 
              rgba(0, 229, 255, 0.04), 
              rgba(255, 179, 71, 0.02), 
              rgba(255, 77, 77, 0.04)
            );
            background-size: 100% 4px, 6px 100%;
            opacity: 0.14;
            z-index: 5;
          }
          /* floating 3D tags - collapsible design to prevent overlap */
          .tag {
            width: 122px;
            height: 20px; /* compact default view */
            overflow: hidden;
            text-align: left;
            font-family: var(--disp);
            user-select: none;
            filter: drop-shadow(0 6px 12px rgba(0,0,0,.75));
            transition: height 0.22s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.2s ease, box-shadow 0.2s ease;
            position: relative;
            z-index: 1;
            background: rgba(7, 13, 26, 0.9);
            border: 1px solid rgba(0, 229, 255, 0.25);
            padding: 3px 6px;
            border-radius: 4px;
          }
          .tag:hover {
            height: 62px; /* expands to show mini sparkline & comments button */
            z-index: 100 !important;
            border-color: var(--cy);
            box-shadow: 0 0 16px rgba(0, 229, 255, 0.45);
          }
          .override-overflow {
            z-index: 150 !important;
          }
          .override-overflow .tag {
            overflow: visible !important;
            height: auto !important;
            z-index: 150 !important;
            border-color: var(--cy) !important;
          }
          .tag-details {
            opacity: 0;
            transition: opacity 0.18s ease;
            pointer-events: none;
          }
          .tag:hover .tag-details, .override-overflow .tag-details {
            opacity: 1;
            pointer-events: auto;
          }
          .tag .nm {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: .5px;
            color: #fff;
            background: rgba(7, 13, 26, 0.9);
            border: 1px solid rgba(0, 229, 255, 0.3);
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.15);
            padding: 4px 10px;
            border-radius: 6px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
          }
          .tag:hover .nm {
            border-color: var(--cy);
            box-shadow: 0 0 16px rgba(0, 229, 255, 0.55);
            background: rgba(12, 22, 40, 0.95);
          }
          .tag .hp {
            font-family: var(--mono);
            font-size: 9.5px;
            margin-top: 3px;
            display: flex;
            gap: 6px;
            align-items: center;
            justify-content: center;
          }
          .tag .hp .mini {
            width: 38px;
            height: 4px;
            border-radius: 3px;
            background: rgba(120, 150, 200,.2);
            overflow: hidden;
            display: inline-block;
          }
          .tag .hp .mini i {
            display: block;
            height: 100%;
          }

          /* ---- HUD ---- */
          .hud {
            position: absolute;
            z-index: 10;
            pointer-events: none;
          }
          .hud * {
            pointer-events: auto;
          }
          .topbar {
            top: 16px;
            left: 16px;
            right: 16px;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px 14px;
            padding: 10px 18px;
            background: rgba(13, 20, 36, 0.82);
            backdrop-filter: blur(14px);
            border: 1px solid rgba(148, 197, 255, 0.22);
            box-shadow: 0 0 0 1px rgba(255,255,255,0.05), 0 10px 36px rgba(0,0,0,0.45);
            border-radius: 14px;
          }
          .brand {
            display: flex;
            align-items: center;
            gap: 12px;
          }
          .brand .mk {
            width: 34px;
            height: 34px;
            border-radius: 6px;
            display: grid;
            place-items: center;
            background: linear-gradient(135deg, rgba(0,229,255,.25), rgba(61,123,255,.1));
            border: 1px solid rgba(0,229,255,.4);
          }
          .brand .mk svg {
            width: 20px;
            height: 20px;
          }
          .brand b {
            font-weight: 700;
            letter-spacing: 2px;
            font-size: 16px;
            font-family: var(--disp);
            color: #fff;
          }
          .brand small {
            display: block;
            font-family: var(--mono);
            font-size: 8px;
            letter-spacing: 2.5px;
            color: var(--muted);
          }
          
          /* top stats indicators */
          .hud-stat {
            display: flex;
            flex-direction: column;
            border-left: 1px solid rgba(255,255,255,0.14);
            padding-left: 13px;
          }
          .hud-stat .k {
            font-family: var(--mono);
            font-size: 8.5px;
            letter-spacing: 1.5px;
            color: var(--muted);
            text-transform: uppercase;
          }
          .hud-stat .val {
            font-family: var(--disp);
            font-size: 16px;
            font-weight: 700;
            color: #fff;
            margin-top: 2px;
          }
          
          .tabs {
            display: flex;
            gap: 6px;
          }
          .tab {
            font-family: var(--mono);
            font-size: 10.5px;
            letter-spacing: 1px;
            text-transform: uppercase;
            padding: 7px 12px;
            border-radius: 4px;
            border: 1px solid rgba(0,229,255,.15);
            background: rgba(12,20,36,.7);
            color: var(--muted);
            cursor: pointer;
            transition: .15s;
            display: flex;
            align-items: center;
            gap: 6px;
          }
          .tab:hover {
            color: var(--txt);
            border-color: rgba(0,229,255,.4);
          }
          .tab.on {
            color: var(--cy);
            border-color: rgba(0,229,255,.6);
            background: rgba(0,229,255,.12);
            box-shadow: 0 0 12px rgba(0,229,255,.2);
          }
          .tab .dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
          }
          .spacer {
            flex: 1;
          }
          
          /* pill status tags */
          .pill {
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: var(--mono);
            font-size: 10px;
            letter-spacing: 1px;
            padding: 6px 12px;
            border-radius: 4px;
            border: 1px solid rgba(255,255,255,.1);
            background: rgba(12,20,36,.7);
            color: var(--muted);
          }
          .pill b {
            color: var(--txt);
            font-weight: 700;
          }
          .pill .live {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: var(--cy);
            box-shadow: 0 0 0 0 rgba(0,229,255,.6);
            animation: lp 2s infinite;
          }
          @keyframes lp {
            70% { box-shadow: 0 0 0 7px transparent }
            100% { box-shadow: 0 0 0 0 transparent }
          }
          .pill .src {
            color: var(--amber);
          }

          /* Bottom Command Panel Container */
          .bottombar {
            bottom: 16px;
            left: 16px;
            right: 16px;
            height: 200px;
            display: flex;
            gap: 16px;
            pointer-events: none;
          }
          .bottombar .panel {
            background: rgba(8, 14, 26, 0.86);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 8px;
            padding: 14px;
            display: flex;
            flex-direction: column;
            pointer-events: auto;
            box-shadow: 0 4px 30px rgba(0,0,0,0.5);
          }
          .bottombar .p-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 8px;
            margin-bottom: 10px;
          }
          .bottombar .p-header h3 {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: var(--cy);
            font-family: var(--mono);
          }
          
          /* Failure timeline list styling */
          .timeline-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 6px;
            padding: 6px 10px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: var(--mono);
            font-size: 10.5px;
          }
          .timeline-card .date-badge {
            background: rgba(0,229,255,0.12);
            border: 1px solid rgba(0,229,255,0.3);
            color: var(--cy);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 9.5px;
            font-weight: 700;
          }
          .timeline-card.crit .date-badge {
            background: rgba(255,77,77,0.12);
            border: 1px solid rgba(255,77,77,0.3);
            color: var(--red);
          }
          .timeline-card.warn .date-badge {
            background: rgba(255,179,71,0.12);
            border: 1px solid rgba(255,179,71,0.3);
            color: var(--amber);
          }

          /* Agent Orchestration Grid */
          .agent-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 8px;
          }
          .agent-node {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 6px;
            padding: 8px;
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
          }
          .agent-node.active-node {
            border-color: rgba(0, 229, 255, 0.4);
            box-shadow: 0 0 10px rgba(0, 229, 255, 0.15);
            background: rgba(0, 229, 255, 0.03);
          }
          .agent-node .pulse-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            margin-bottom: 5px;
          }
          .agent-node .nm {
            font-size: 10.5px;
            font-weight: 700;
            color: #fff;
          }
          .agent-node .st {
            font-family: var(--mono);
            font-size: 8px;
            color: var(--muted);
            margin-top: 3px;
            letter-spacing: .5px;
          }
          
          /* Terminal Console logs */
          .terminal-log {
            background: rgba(0, 0, 0, 0.45);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 6px;
            padding: 8px 12px;
            flex-1;
            font-family: var(--mono);
            font-size: 10px;
            color: #b8c8e0;
            overflow-y: auto;
            max-height: 100px;
          }

          /* detail panel drawer */
          .detail {
            top: 90px;
            bottom: 232px;
            right: 16px;
            width: 360px;
            background: rgba(8, 14, 26, 0.88);
            border: 1px solid rgba(0, 229, 255, 0.25);
            border-radius: 8px;
            padding: 0;
            backdrop-filter: blur(15px);
            transform: translateX(120%);
            transition: transform .35s cubic-bezier(.4,0,.2,1);
            box-shadow: 0 16px 40px rgba(0,0,0,.8);
            overflow: hidden;
          }
          .detail.show {
            transform: none;
          }
          .detail .dh {
            padding: 14px 18px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            position: relative;
            background: rgba(0,0,0,0.15);
          }
          .detail .dh .x {
            position: absolute;
            top: 14px;
            right: 14px;
            width: 22px;
            height: 22px;
            border-radius: 4px;
            border: 1px solid rgba(255,255,255,0.15);
            background: transparent;
            color: var(--muted);
            cursor: pointer;
            display: grid;
            place-items: center;
            font-size: 12px;
          }
          .detail .dh .x:hover {
            color: var(--txt);
            border-color: rgba(255,255,255,0.3);
          }
          .detail .dh .t {
            font-size: 8px;
            font-family: var(--mono);
            letter-spacing: 2px;
            color: var(--cy);
            text-transform: uppercase;
            margin-bottom: 4px;
          }
          .detail .dh h3 {
            font-size: 15px;
            font-weight: 700;
            letter-spacing: .5px;
            padding-right: 26px;
            font-family: var(--disp);
            color: #fff;
          }
          .detail .body {
            padding: 16px;
            height: calc(100% - 62px);
            overflow-y: auto;
          }
          .detail .big {
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 10px;
          }
          .detail .big .v {
            font-size: 38px;
            font-weight: 700;
            line-height: 1;
            font-family: var(--disp);
          }
          .detail .big .u {
            font-family: var(--mono);
            font-size: 10.5px;
            color: var(--muted);
          }
          .detail .bar {
            height: 5px;
            border-radius: 4px;
            background: rgba(255,255,255,.08);
            overflow: hidden;
            margin-bottom: 16px;
          }
          .detail .bar i {
            display: block;
            height: 100%;
            border-radius: 4px;
            transition: width .6s;
          }
          
          /* Telemetry mini charts grid */
          .detail .telemetry-section {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 12px;
          }
          .detail .telemetry-card {
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: var(--mono);
            font-size: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            padding: 6px 0;
          }
          .detail .telemetry-card:last-child {
            border-bottom: none;
          }
          .detail .telemetry-card .k {
            color: var(--muted);
          }
          .detail .telemetry-card .val {
            font-weight: 700;
            color: #fff;
          }

          .detail .grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            margin-bottom: 12px;
          }
          .detail .cell {
            background: rgba(255,255,255,0.02);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 6px;
            padding: 8px 10px;
          }
          .detail .cell .k {
            font-family: var(--mono);
            font-size: 8.5px;
            letter-spacing: 1px;
            color: var(--muted);
            text-transform: uppercase;
          }
          .detail .cell .val {
            font-family: var(--mono);
            font-size: 12.5px;
            font-weight: 700;
            margin-top: 3px;
            color: #fff;
          }
          .detail .rec {
            font-size: 11px;
            line-height: 1.5;
            color: #b8c8e0;
            background: rgba(0,229,255,.06);
            border: 1px solid rgba(0,229,255,.2);
            border-radius: 6px;
            padding: 10px;
            margin-bottom: 14px;
          }
          .detail .rec b {
            color: var(--cy);
            font-family: var(--mono);
            font-size: 9px;
            letter-spacing: 1px;
            display: block;
            margin-bottom: 4px;
            text-transform: uppercase;
          }

          /* hints and overlays */
          .hud-hint {
            bottom: 232px;
            left: 16px;
            font-family: var(--mono);
            font-size: 9px;
            color: var(--muted);
            background: rgba(8,14,26,.8);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 4px;
            padding: 6px 10px;
            letter-spacing: .5px;
          }
          .hud-legend {
            bottom: 272px;
            left: 16px;
            display: flex;
            flex-direction: column;
            gap: 6px;
            background: rgba(8,14,26,.82);
            border: 1px solid rgba(0, 229, 255, 0.2);
            border-radius: 6px;
            padding: 10px 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.5);
          }
          .hud-legend .ttl {
            font-family: var(--mono);
            font-size: 9px;
            letter-spacing: 1.5px;
            color: var(--muted);
            text-transform: uppercase;
            margin-bottom: 2px;
          }
          .hud-legend .row {
            display: flex;
            align-items: center;
            gap: 8px;
            font-family: var(--mono);
            font-size: 9.5px;
            color: #b0c0df;
          }
          .hud-legend .row .sw {
            width: 14px;
            height: 5px;
            border-radius: 2px;
          }
        `}} />

        <div className="twin-body relative w-full h-full flex-1 flex flex-col">
          {/* Scan line effects */}
          <div className="scanlines z-5" />

          {/* WebGL Canvas Container */}
          <div ref={canvasContainerRef} className="absolute inset-0 w-full h-full z-0" />
          
          {/* Projected Floating Tags Overlay */}
          <div ref={labelsContainerRef} className="absolute inset-0 w-full h-full pointer-events-none z-10 overflow-hidden">
            {assets.map(a => {
              const hex = hexHealth(a.health);
              const cssH = cssHex(hex);
              return (
                <div
                  key={a.id}
                  ref={el => { labelRefs.current[a.id] = el; }}
                  className={`absolute hidden translate-x-[-50%] translate-y-[-100%] pointer-events-auto cursor-pointer ${openCommentAssetId === a.id ? "override-overflow" : ""}`}
                  style={{ left: 0, top: 0 }}
                  onClick={() => {
                    setSelectedAsset(a);
                    if (controlsRef.current) {
                      controlsRef.current.autoRotate = false;
                    }
                    const matched = assetObjsRef.current.find(o => o.data.id === a.id);
                    if (matched) {
                      const p = matched.group.position;
                      focusTargetRef.current = new THREE.Vector3(p.x, 1.2, p.z);
                      cameraTargetPosRef.current = new THREE.Vector3(p.x + 7, p.y + 6, p.z + 9);
                    }
                  }}
                >
                  <div className="tag">
                    {/* Floating Comment Bubble Box attached right above the tag */}
                    {openCommentAssetId === a.id && (
                      <div 
                        className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 w-64 bg-[#0a1426]/95 border border-[#00e5ff]/50 rounded-lg p-3 pointer-events-auto shadow-2xl text-left"
                        onClick={(e) => e.stopPropagation()}
                        onMouseDown={(e) => e.stopPropagation()}
                        onMouseUp={(e) => e.stopPropagation()}
                      >
                        <div className="flex items-center justify-between border-b border-[#00e5ff]/20 pb-1.5 mb-1.5 text-[9px] text-[#8ea0c0] font-bold font-mono">
                          <span>OPERATOR ANNOTATIONS</span>
                          <button 
                            className="text-gray-400 hover:text-white text-xs font-bold px-1"
                            onClick={(e) => {
                              e.stopPropagation();
                              setOpenCommentAssetId(null);
                            }}
                          >
                            ✕
                          </button>
                        </div>
                        <div className="max-h-24 overflow-y-auto mb-2 text-[10px] space-y-1 text-gray-300 pr-1 select-text font-mono">
                          {(comments[a.id] || []).map((c, idx) => (
                            <div key={idx} className="bg-white/5 p-1 rounded border border-white/5 break-words">
                              {c}
                            </div>
                          ))}
                          {(comments[a.id] || []).length === 0 && (
                            <div className="text-[#435b80] italic text-center py-2">No comment logs.</div>
                          )}
                        </div>
                        <form 
                          className="flex gap-1"
                          onSubmit={(e) => {
                            e.preventDefault();
                            const input = document.getElementById(`comment-input-${a.id}`) as HTMLInputElement;
                            if (input && input.value.trim()) {
                              const val = input.value.trim();
                              setComments(prev => ({
                                ...prev,
                                [a.id]: [...(prev[a.id] || []), `Operator: ${val}`]
                              }));
                              input.value = "";
                            }
                          }}
                        >
                          <input
                            id={`comment-input-${a.id}`}
                            type="text"
                            placeholder="Add comment..."
                            className="flex-1 bg-[#12202c] border border-white/20 rounded px-2 py-0.5 text-[10px] text-white focus:outline-none focus:border-[#00e5ff]"
                            onKeyDown={(e) => e.stopPropagation()}
                          />
                          <button 
                            type="submit"
                            className="bg-[#00e5ff] text-black font-bold text-[9px] px-2 rounded hover:bg-cyan-400"
                          >
                            Add
                          </button>
                        </form>
                      </div>
                    )}

                    {/* Compact Header */}
                    <div className="flex items-center justify-between gap-1.5 text-[10px] font-bold text-white leading-none">
                      <span className="truncate max-w-[85px]">{a.name}</span>
                      <span className="font-mono text-[9.5px] font-bold" style={{ color: cssH }}>{a.health}%</span>
                    </div>

                    {/* Hover reveal tags details */}
                    <div className="tag-details">
                      <div className="flex items-center justify-between gap-2.5 mb-1 mt-1.5 border-t border-white/10 pt-1">
                        <span className="text-[8.5px] text-gray-400 font-mono">RUL: {a.rul_days}d</span>
                        <button 
                          className="text-[#00e5ff] hover:text-white pointer-events-auto bg-[#12202c] border border-[#00e5ff]/30 px-1 py-0.2 rounded text-[8.5px] leading-none"
                          onClick={(e) => {
                            e.stopPropagation();
                            setOpenCommentAssetId(openCommentAssetId === a.id ? null : a.id);
                          }}
                        >
                          💬 {comments[a.id]?.length || 0}
                        </button>
                      </div>
                      
                      {/* Compact SVG trend sparkline */}
                      <svg width="105" height="18" className="overflow-visible opacity-85">
                        <path d={generateSparklineData(a.id)} fill="none" stroke={cssH} strokeWidth="1.2" />
                      </svg>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* ====================================================
              HUD OVERLAY LAYERS
              ==================================================== */}
          
          {/* Top Command HUD (Glass Panel) */}
          <div className="hud topbar">
            <div className="brand">
              <div className="mk">
                <svg viewBox="0 0 24 24" fill="none" stroke="var(--cy)" strokeWidth="2.5">
                  <circle cx="12" cy="12" r="9"/>
                  <path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4"/>
                </svg>
              </div>
              <div>
                <b>SHERLOCK AI</b>
                <small>COMMAND CENTER</small>
              </div>
            </div>

            {/* Glowing HUD Statistics */}
            <div className="hud-stat">
              <span className="k">Plant Health</span>
              <span className="val text-[#00e5ff] shadow-cyan-300">92%</span>
            </div>
            <div className="hud-stat">
              <span className="k">Monitored Assets</span>
              <span className="val">124</span>
            </div>
            <div className="hud-stat">
              <span className="k">Critical Alerts</span>
              <span className="val text-[#ff4d4d] animate-pulse">6</span>
            </div>
            <div className="hud-stat">
              <span className="k">Predicted Failures</span>
              <span className="val text-[#ffb347]">3</span>
            </div>
            <div className="hud-stat">
              <span className="k">Risk Exposure</span>
              <span className="val text-[#00e5ff]">₹42.6 L</span>
            </div>

            {/* Metric Mode Filter Tabs */}
            <div className="tabs ml-4">
              {[
                { id: "topology", label: "Topology", c: COL.cy },
                { id: "health", label: "Health", c: COL.green },
                { id: "risk", label: "Risk", c: COL.amber },
                { id: "rul", label: "RUL", c: COL.pur }
              ].map(t => (
                <div
                  key={t.id}
                  onClick={() => setMode(t.id as any)}
                  className={`tab ${mode === t.id ? "on" : ""}`}
                >
                  <span className="dot" style={{ background: cssHex(t.c) }} />
                  {t.label}
                </div>
              ))}
            </div>

            <div className="spacer" />

            {/* System clock, Agent Status, Stream Source */}
            <div className="pill">
              <span className="live" />
              <span>CLOCK</span>
              <b className="font-mono text-[#fff]">{clock}</b>
            </div>

            <div className="pill">
              <span>DATA</span>
              <b className="src" style={{ color: src === "LIVE" ? "var(--cy)" : "var(--amber)", textTransform: "uppercase" }}>
                {src}
              </b>
            </div>
          </div>

          {/* Bottom command bar (Timeline + Live Agent orchestration network) */}
          <div className="hud bottombar">
            {/* Timeline Failure Forecast Panel */}
            <div className="panel w-[32%]">
              <div className="p-header">
                <h3>FAILURE FORECAST</h3>
                <div className="flex gap-1.5">
                  <button 
                    onClick={() => setTimelineMode("7d")}
                    className={`px-2 py-0.5 rounded text-[9px] font-mono border transition-all ${timelineMode === "7d" ? "bg-[#00e5ff]/15 border-[#00e5ff]/50 text-[#00e5ff]" : "border-white/10 text-gray-400"}`}
                  >
                    7D
                  </button>
                  <button 
                    onClick={() => setTimelineMode("30d")}
                    className={`px-2 py-0.5 rounded text-[9px] font-mono border transition-all ${timelineMode === "30d" ? "bg-[#00e5ff]/15 border-[#00e5ff]/50 text-[#00e5ff]" : "border-white/10 text-gray-400"}`}
                  >
                    30D
                  </button>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
                {activeTimeline.map((item, idx) => (
                  <div 
                    key={idx} 
                    className={`timeline-card cursor-pointer hover:bg-white/5 transition-colors ${item.risk === "CRITICAL" ? "crit" : item.risk === "HIGH" ? "warn" : ""}`}
                    onClick={() => {
                      const asset = assets.find(a => a.id === item.type);
                      if (asset) {
                        setSelectedAsset(asset);
                        const matched = assetObjsRef.current.find(o => o.data.id === asset.id);
                        if (matched) {
                          const p = matched.group.position;
                          focusTargetRef.current = new THREE.Vector3(p.x, 1.2, p.z);
                          cameraTargetPosRef.current = new THREE.Vector3(p.x + 7, p.y + 6, p.z + 9);
                        }
                      }
                    }}
                  >
                    <span className="date-badge">{item.date}</span>
                    <span className="font-bold text-white truncate max-w-[100px]">{item.asset}</span>
                    <span className="text-gray-400 font-mono text-[9.5px]">RUL: {item.rul}</span>
                    <span className="font-mono text-gray-300">P(f): {item.prob}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Agent Collaboration Grid & Live stream console */}
            <div className="panel w-[68%]">
              <div className="p-header">
                <h3>AGENT ORCHESTRATION NETWORK</h3>
                <span className="text-[9px] font-mono text-gray-400">7 COGNITIVE NODE THREADS</span>
              </div>
              
              <div className="flex gap-4 flex-1 min-h-0">
                {/* Agent Nodes Grid */}
                <div className="w-[45%] flex flex-col justify-between">
                  <div className="grid grid-cols-4 gap-1.5">
                    {[
                      { key: "telemetry", name: "Telemetry", col: "bg-[#00e5ff]" },
                      { key: "reliability", name: "Reliability", col: "bg-[#00e5ff]" },
                      { key: "knowledge", name: "Knowledge", col: "bg-[#ffb347]" },
                      { key: "maintenance", name: "Maint.", col: "bg-purple-400" },
                      { key: "procurement", name: "Procure.", col: "bg-gray-400" },
                      { key: "safety", name: "Safety", col: "bg-green-400" },
                      { key: "supervisor", name: "Superv.", col: "bg-[#00e5ff]" },
                    ].map(node => {
                      const isActive = agentStates[node.key] !== "IDLE" && agentStates[node.key] !== "STANDBY";
                      return (
                        <div key={node.key} className={`agent-node ${isActive ? "active-node" : ""}`}>
                          <span className={`pulse-dot ${node.col} ${isActive ? "animate-ping" : ""}`} />
                          <span className="nm text-[9px] truncate max-w-full">{node.name}</span>
                          <span className="st truncate max-w-full">{agentStates[node.key]}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Live Console Terminal Log */}
                <div className="w-[55%] flex flex-col min-h-0">
                  <div className="terminal-log flex-1">
                    {agentLogs.map((log, idx) => {
                      let col = "text-[#8ea0c0]";
                      if (log.includes("[Telemetry")) col = "text-[#00e5ff]";
                      else if (log.includes("[Reliability")) col = "text-[#ffb347]";
                      else if (log.includes("[Supervisor")) col = "text-white font-bold";
                      else if (log.includes("[Safety")) col = "text-[#ff4d4d]";
                      
                      return (
                        <div key={idx} className={`${col} truncate mb-0.5`}>
                          {log}
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* HUD Legends and Help */}
          <div className="hud hud-legend">
            <div className="ttl">
              {mode === "health" ? "HEALTH INDEX" : mode === "risk" ? "RISK CRITERIA" : mode === "rul" ? "FORECAST RUL" : "NETWORK TOPOLOGY"}
            </div>
            <div className="row">
              <span className="sw" style={{ background: "var(--green)" }} />
              {mode === "health" ? "Nominal (> 70%)" : mode === "risk" ? "Low Risk" : mode === "rul" ? "RUL > 60d" : "Direct Link"}
            </div>
            <div className="row">
              <span className="sw" style={{ background: "var(--amber)" }} />
              {mode === "health" ? "Degraded (50–70%)" : mode === "risk" ? "Medium Risk" : mode === "rul" ? "RUL 20–60d" : "Substation Link"}
            </div>
            <div className="row">
              <span className="sw" style={{ background: "var(--red)" }} />
              {mode === "health" ? "Critical (< 50%)" : mode === "risk" ? "High / Critical" : mode === "rul" ? "RUL < 20d" : "Telemetry Bus"}
            </div>
          </div>

          <div className="hud hud-hint">
            DRAG to rotate twin · SCROLL to zoom · CLICK asset meshes to investigate
          </div>

          {/* Right-side Slideout AI Analyst Investigation Panel */}
          <div className={`hud detail ${selectedAsset ? "show" : ""}`}>
            {selectedAsset && (
              <>
                <div className="dh">
                  <button className="x" onClick={closeDetail}>✕</button>
                  <div className="t">ASSET IDENTIFIER: {selectedAsset.id.toUpperCase()}</div>
                  <h3>{selectedAsset.name}</h3>
                </div>
                <div className="body select-none">
                  {/* Health Score metrics */}
                  <div className="big">
                    <span className="v" style={{ color: cssHex(hexHealth(selectedAsset.health)) }}>{selectedAsset.health}%</span>
                    <span className="u">Condition Index</span>
                  </div>
                  <div className="bar">
                    <i style={{ width: `${selectedAsset.health}%`, background: cssHex(hexHealth(selectedAsset.health)) }} />
                  </div>
                  
                  {/* Diagnostics properties */}
                  <div className="grid">
                    <div className="cell">
                      <div className="k">Remaining Useful Life</div>
                      <div className="val" style={{ color: cssHex(hexRul(selectedAsset.rul_days)) }}>{selectedAsset.rul_days} days</div>
                    </div>
                    <div className="cell">
                      <div className="k">Risk Criticality</div>
                      <div className="val" style={{ color: cssHex(hexRisk(selectedAsset.risk)) }}>{selectedAsset.risk.toUpperCase()}</div>
                    </div>
                    <div className="cell">
                      <div className="k">Hologram ISO Zone</div>
                      <div className="val">{isoZone(selectedAsset.health)}</div>
                    </div>
                    <div className="cell">
                      <div className="k">Operational Status</div>
                      <div className="val" style={{ color: cssHex(hexHealth(selectedAsset.health)) }}>{statusTxt(selectedAsset.health)}</div>
                    </div>
                  </div>

                  {/* Real-time Telemetry sensor trend SVGs */}
                  <div className="telemetry-section select-text">
                    <h4 className="text-[9.5px] font-mono font-bold text-gray-400 tracking-wider mb-2.5 uppercase">REAL-TIME TELEMETRY STREAM</h4>
                    
                    <div className="telemetry-card">
                      <div>
                        <div className="k">VIBRATION SPECTRUM (ISO-10816)</div>
                        <div className="val font-mono text-[11px] mt-0.5">
                          {selectedAsset.id === "gearbox" ? "8.4 mm/s RMS" : selectedAsset.id === "drive" ? "5.6 mm/s RMS" : "1.8 mm/s RMS"}
                        </div>
                      </div>
                      <div className="ml-2">
                        {renderTrendSVG(
                          selectedAsset.health < 50 ? "var(--red)" : selectedAsset.health < 70 ? "var(--amber)" : "var(--cy)", 
                          getMockTelemetryData(selectedAsset.id, "vibration")
                        )}
                      </div>
                    </div>

                    <div className="telemetry-card">
                      <div>
                        <div className="k">THERMOCOUPLE TEMPERATURE</div>
                        <div className="val font-mono text-[11px] mt-0.5">
                          {selectedAsset.id === "gearbox" ? "88.4 °C" : selectedAsset.id === "drive" ? "91.2 °C" : "61.7 °C"}
                        </div>
                      </div>
                      <div className="ml-2">
                        {renderTrendSVG(
                          selectedAsset.health < 50 ? "var(--red)" : selectedAsset.health < 70 ? "var(--amber)" : "var(--cy)", 
                          getMockTelemetryData(selectedAsset.id, "temp")
                        )}
                      </div>
                    </div>

                    <div className="telemetry-card">
                      <div>
                        <div className="k">PRESSURE / MOTOR POWER</div>
                        <div className="val font-mono text-[11px] mt-0.5">
                          {selectedAsset.id === "gearbox" ? "4.8 bar" : selectedAsset.id === "drive" ? "2.6 bar" : "1.9 bar"}
                        </div>
                      </div>
                      <div className="ml-2">
                        {renderTrendSVG(
                          selectedAsset.health < 50 ? "var(--red)" : selectedAsset.health < 70 ? "var(--amber)" : "var(--cy)", 
                          getMockTelemetryData(selectedAsset.id, "pressure")
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Recommendation action block */}
                  <div className="rec">
                    <b>Recommended action dispatch</b>
                    <span>{recFor(selectedAsset)}</span>
                  </div>

                  {/* Comments annotations history list */}
                  <div className="mt-4 border-t border-white/10 pt-4">
                    <h4 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2 flex items-center justify-between">
                      <span>Operator log annotations</span>
                      <span className="text-[9px] bg-white/10 px-1.5 py-0.5 rounded text-white font-mono">
                        {comments[selectedAsset.id]?.length || 0} logs
                      </span>
                    </h4>
                    <div className="space-y-2 max-h-36 overflow-y-auto pr-1 select-text font-mono text-[10.5px]">
                      {(comments[selectedAsset.id] || []).map((c, idx) => (
                        <div key={idx} className="bg-white/5 border border-white/5 rounded p-2">
                          <div className="text-[#00e5ff] text-[8px] mb-1 font-bold">
                            {c.startsWith("AI") ? "🤖 AI RECOMMENDATION" : "👤 OPERATOR ANNOTATION"}
                          </div>
                          <div className="text-gray-200">{c.substring(c.indexOf(":") + 1).trim()}</div>
                        </div>
                      ))}
                    </div>
                    <form 
                      className="flex gap-2 mt-2"
                      onSubmit={(e) => {
                        e.preventDefault();
                        const input = document.getElementById("drawer-comment-input") as HTMLInputElement;
                        if (input && input.value.trim()) {
                          const val = input.value.trim();
                          setComments(prev => ({
                            ...prev,
                            [selectedAsset.id]: [...(prev[selectedAsset.id] || []), `Operator: ${val}`]
                          }));
                          input.value = "";
                        }
                      }}
                    >
                      <input
                        id="drawer-comment-input"
                        type="text"
                        placeholder="Add annotation note..."
                        className="flex-1 bg-[#12202c] border border-white/20 rounded px-2.5 py-1 text-xs text-white focus:outline-none focus:border-[#00e5ff]"
                      />
                      <button 
                        type="submit"
                        className="bg-[#00e5ff] hover:bg-cyan-400 text-black font-bold text-xs px-3 py-1 rounded transition-colors"
                      >
                        Submit
                      </button>
                    </form>
                  </div>

                  {/* Dispatch triggers */}
                  <div className="mt-4 pt-4 border-t border-white/10">
                    {workOrderSuccess === selectedAsset.id ? (
                      <div className="bg-green-500/10 border border-[#00e5ff] text-[#00e5ff] p-3 rounded-lg text-xs font-semibold text-center animate-pulse">
                        ✓ WORK ORDER DISPATCHED SUCCESSFUL
                        <div className="text-[9px] text-gray-300 font-normal mt-1 font-mono">TASK: WO-2026-{selectedAsset.id.toUpperCase()}</div>
                      </div>
                    ) : (
                      <button 
                        onClick={() => handleWorkOrder(selectedAsset.id)}
                        className="w-full bg-[#00e5ff] hover:bg-cyan-400 text-black font-bold text-xs py-2 rounded-lg transition-colors flex items-center justify-center gap-1.5"
                      >
                        <Wrench size={13} />
                        DISPATCH URGENT WORK ORDER
                      </button>
                    )}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
