export type Incident = {
  id: string;
  category: string;
  description: string;
  latitude: number;
  longitude: number;
  location_label?: string;
  observed_at: string;
  submitted_at: string;
  source: string;
  source_kind?: string;
  verification_status: string;
  image_url?: string | null;
  reviewer_notes?: string | null;
  ai_image_label?: string | null;
  ai_image_confidence?: number | null;
  ai_risk_category?: string | null;
  last_updated?: string | null;
  freshness?: Freshness;
  limitations?: string;
};

export type Freshness = {
  status: string;
  status_label: string;
  freshness_text: string;
  observed_at?: string | null;
  retrieved_at?: string;
  stale?: boolean;
  notice?: string | null;
};

const TOKEN_KEY = "hg_token";
const USER_KEY = "hg_user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setSession(token: string, user: object) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}
export function getUser(): { email: string; role: string; display_name?: string } | null {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}
export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

async function req(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (!(init.body instanceof FormData) && !headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const res = await fetch(path, { ...init, headers });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const j = await res.json();
      detail = j.detail || j.error || detail;
    } catch {
      /* ignore */
    }
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return res.json();
}

export const api = {
  health: () => req("/api/health"),
  incidents: (params: Record<string, string | number | undefined> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== "" && v !== "all") q.set(k, String(v));
    });
    return req(`/api/incidents?${q.toString()}`);
  },
  incident: (id: string) => req(`/api/incidents/${id}`),
  nearby: (lat: number, lng: number) => req(`/api/incidents/nearby?lat=${lat}&lng=${lng}`),
  createIncident: (fd: FormData) => req("/api/incidents", { method: "POST", body: fd }),
  analytics: () => req("/api/analytics"),
  clusters: () => req("/api/clusters"),
  weather: (lat: number, lng: number) => req(`/api/weather?lat=${lat}&lng=${lng}`),
  search: (q: string) => req(`/api/search?q=${encodeURIComponent(q)}`),
  risk: (lat: number, lng: number, rainfall_mm?: number) =>
    req("/api/ai/risk", { method: "POST", body: JSON.stringify({ latitude: lat, longitude: lng, rainfall_mm }) }),
  route: (start: string, destination: string) =>
    req("/api/routes/analyze", { method: "POST", body: JSON.stringify({ start, destination }) }),
  notifications: () => req("/api/notifications"),
  sources: () => req("/api/sources"),
  places: () => req("/api/places"),
  login: (email: string, password: string) => req("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (email: string, password: string, display_name: string) =>
    req("/api/auth/register", { method: "POST", body: JSON.stringify({ email, password, display_name }) }),
  adminReports: (q = "") => req(`/api/admin/reports${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  adminStatus: (id: string, body: object) =>
    req(`/api/admin/reports/${id}/status`, { method: "PATCH", body: JSON.stringify(body) }),
};

export const CATEGORY_META: Record<string, { label: string; color: string; icon: string }> = {
  landslide: { label: "Landslide", color: "#d62828", icon: "▲" },
  flood: { label: "Flood", color: "#1d4ed8", icon: "≋" },
  heavy_rain: { label: "Heavy Rain", color: "#2563eb", icon: "☂" },
  falling_rocks: { label: "Falling Rocks", color: "#d97706", icon: "⬤" },
  road_blockage: { label: "Road Blockage", color: "#ea580c", icon: "■" },
  damaged_road: { label: "Damaged Road", color: "#c2410c", icon: "▣" },
  waterlogging: { label: "Waterlogging", color: "#0284c7", icon: "≈" },
  other: { label: "Other", color: "#64748b", icon: "●" },
};

export function timeAgo(iso?: string | null) {
  if (!iso) return "Unknown time";
  const d = Date.parse(iso);
  const mins = Math.round((Date.now() - d) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} minutes ago`;
  const h = Math.round(mins / 60);
  if (h < 48) return `${h} hours ago`;
  return `${Math.round(h / 24)} days ago`;
}
