import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, CATEGORY_META, Incident, timeAgo } from "../api";
import MapView from "../components/MapView";
import { Disclaimer, ErrorState, IncidentDetails, LoadingState, RiskCard, StatusBadge, WeatherCard } from "../components/Widgets";

export default function Dashboard() {
  const nav = useNavigate();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [analytics, setAnalytics] = useState<any>(null);
  const [weather, setWeather] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [clusters, setClusters] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<Incident | null>(null);
  const [why, setWhy] = useState(false);
  const [filters, setFilters] = useState({ category: "all", status: "all", hours: "" });
  const [health, setHealth] = useState<any>(null);

  async function load() {
    try {
      const [inc, an, cl, w, r, h] = await Promise.all([
        api.incidents(filters),
        api.analytics(),
        api.clusters(),
        api.weather(31.7084, 76.932),
        api.risk(31.7084, 76.932),
        api.health(),
      ]);
      setIncidents(inc.items);
      setAnalytics(an);
      setClusters(cl.items);
      setWeather(w);
      setRisk(r);
      setHealth(h);
    } catch (e: any) {
      setErr(e.message || "Unable to load incident data.");
    }
  }

  useEffect(() => {
    load();
  }, [filters.category, filters.status, filters.hours]);

  const k = analytics?.kpis || {};

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="card">
          <h3>Filters</h3>
          <div className="filters">
            <select aria-label="Hazard type" value={filters.category} onChange={(e) => setFilters({ ...filters, category: e.target.value })}>
              <option value="all">All types</option>
              {Object.entries(CATEGORY_META).map(([k, v]) => (
                <option key={k} value={k}>{v.label}</option>
              ))}
            </select>
            <select aria-label="Verification status" value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}>
              <option value="all">All statuses</option>
              <option value="verified">Verified</option>
              <option value="unverified">Unverified</option>
              <option value="under_review">Under review</option>
              <option value="flagged">Flagged</option>
            </select>
            <select aria-label="Time range" value={filters.hours} onChange={(e) => setFilters({ ...filters, hours: e.target.value })}>
              <option value="">Any time</option>
              <option value="6">Last 6 hours</option>
              <option value="24">Last 24 hours</option>
              <option value="168">Last 7 days</option>
            </select>
          </div>
        </div>
        <WeatherCard data={weather} />
        <RiskCard risk={risk} onWhy={() => setWhy(true)} />
        {why && risk && (
          <div className="card">
            <h3>Why this indicator?</h3>
            <p>{risk.why}</p>
            <p>Available inputs: {JSON.stringify(risk.input_information)}</p>
            <button className="ghost" type="button" onClick={() => setWhy(false)}>Close</button>
          </div>
        )}
        <Disclaimer />
      </aside>
      <main className="main" id="main">
        {health?.demo_mode && <p className="badge b-demo">DEMO MODE — sample and labeled demo data may be shown</p>}
        {err && <ErrorState text={err} />}
        {!analytics && !err && <LoadingState text="Loading dashboard…" />}
        <div className="kpis">
          {[
            ["Total incidents", k.total],
            ["Verified", k.verified],
            ["Unverified", k.unverified],
            ["Under review", k.under_review],
            ["Last 24 hours", k.last_24h],
            ["Clusters", k.clusters],
            ["AI risk areas", k.ai_risk_areas],
            ["Weather obs.", k.weather_observations],
          ].map(([t, v]) => (
            <div className="card kpi" key={String(t)}>
              <h3>{t}</h3>
              <p>{v ?? "—"}</p>
            </div>
          ))}
        </div>
        <MapView incidents={incidents} clusters={clusters} onOpen={setOpen} tileUrl={health?.map_tile_url} />
        <h3>Recent reports</h3>
        <div className="list">
          {incidents.length === 0 && <p className="muted">No reports found for the selected filters.</p>}
          {incidents.slice(0, 8).map((i) => (
            <div className="row-item" key={i.id}>
              <span aria-hidden>{CATEGORY_META[i.category]?.icon}</span>
              <div>
                <strong>{CATEGORY_META[i.category]?.label}</strong>
                <div className="muted">{i.location_label} · {timeAgo(i.observed_at)}</div>
              </div>
              <div>
                <StatusBadge status={i.verification_status} />
                <button className="ghost" type="button" onClick={() => setOpen(i)}>View</button>
              </div>
            </div>
          ))}
        </div>
      </main>
      {open && (
        <IncidentDetails incident={open} onClose={() => setOpen(null)} onSimilar={() => nav(`/report?cat=${open.category}&lat=${open.latitude}&lng=${open.longitude}`)} />
      )}
    </div>
  );
}
