import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("sherlock_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("sherlock_token");
      localStorage.removeItem("sherlock_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authAPI = {
  login: (email: string, password: string) =>
    api.post("/api/auth/login", { email, password }),
};

// ── Dashboard ────────────────────────────────────────────────────────────────
export const dashboardAPI = {
  getKPIs: () => api.get("/api/dashboard/kpis"),
  getTimeseries: (plantId = "ALL") => api.get(`/api/dashboard/timeseries?plant_id=${plantId}`),
  getPlants: () => api.get("/api/dashboard/plants"),
};

// ── Maintenance ──────────────────────────────────────────────────────────────
export const maintenanceAPI = {
  getPredictions: (plantId = "ALL", limit = 50) =>
    api.get(`/api/maintenance/predictions?plant_id=${plantId}&limit=${limit}`),
  getTasks: (plantId = "ALL", status?: string) =>
    api.get(`/api/maintenance/tasks?plant_id=${plantId}${status ? `&status=${status}` : ""}`),
  getAnalytics: (plantId = "ALL") => api.get(`/api/maintenance/analytics?plant_id=${plantId}`),
  analyze: (plantId = "ALL") => api.post(`/api/maintenance/analyze?plant_id=${plantId}`),
};

// ── Safety ───────────────────────────────────────────────────────────────────
export const safetyAPI = {
  getIncidents: (plantId = "ALL", severity?: string) =>
    api.get(`/api/safety/incidents?plant_id=${plantId}${severity ? `&severity=${severity}` : ""}`),
  getAnalytics: (plantId = "ALL") => api.get(`/api/safety/analytics?plant_id=${plantId}`),
  analyze: (plantId = "ALL") => api.post(`/api/safety/analyze?plant_id=${plantId}`),
};

// ── Energy ───────────────────────────────────────────────────────────────────
export const energyAPI = {
  getConsumption: (plantId = "ALL") => api.get(`/api/energy/consumption?plant_id=${plantId}`),
  getAnalytics: (plantId = "ALL") => api.get(`/api/energy/analytics?plant_id=${plantId}`),
  analyze: (plantId = "ALL") => api.post(`/api/energy/analyze?plant_id=${plantId}`),
};

// ── Production ────────────────────────────────────────────────────────────────
export const productionAPI = {
  getSummary: (plantId = "ALL") => api.get(`/api/production/summary?plant_id=${plantId}`),
  getSchedule: () => api.get("/api/production/schedule"),
  analyze: (plantId = "ALL") => api.post(`/api/production/analyze?plant_id=${plantId}`),
};

// ── Chat ─────────────────────────────────────────────────────────────────────
export const chatAPI = {
  sendMessage: (message: string, plantId = "ALL", history: any[] = []) =>
    api.post("/api/chat/message", { message, plant_id: plantId, history }),
  getSuggestions: () => api.get("/api/chat/suggestions"),
  getAgents: () => api.get("/api/chat/agents"),
  uploadFile: (file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return api.post("/api/chat/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};

// ── Reports ───────────────────────────────────────────────────────────────────
export const reportsAPI = {
  getExecutiveSummary: () => api.get("/api/reports/executive-summary"),
  getMaintenanceReport: () => api.get("/api/reports/maintenance-report"),
  getSafetyReport: () => api.get("/api/reports/safety-report"),
  getEnergyReport: () => api.get("/api/reports/energy-report"),
  getBoardPdf: () =>
    api.get("/api/reports/board-pdf", { responseType: "blob", timeout: 60000 }),
};

// ── Live / Demo ───────────────────────────────────────────────────────────────
export const liveAPI = {
  getDashboard:  () => api.get("/api/dashboard/live"),
  getEvents:     () => api.get("/api/dashboard/live-events"),
  getReadings:   () => api.get("/api/demo/readings"),
  injectAlert:   (plant: string, alertType: string) =>
    api.post("/api/demo/inject-alert", { plant, alert_type: alertType }),
  getAlertTypes: () => api.get("/api/demo/alert-types"),
};
