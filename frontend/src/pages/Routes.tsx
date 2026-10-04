import { FormEvent, useState } from "react";
import { api, CATEGORY_META, Incident, timeAgo } from "../api";
import MapView from "../components/MapView";
import { ErrorState, RiskCard, StatusBadge, WeatherCard } from "../components/Widgets";

export default function RoutesPage() {
  const [start, setStart] = useState("Shimla");
  const [dest, setDest] = useState("Manali");
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErr(null);
    try {
      const data = await api.route(start, dest);
      if (data.error) setErr(data.error);
      else setResult(data);
    } catch {
      setErr("Route service unavailable.");
    } finally {
      setLoading(false);
    }
  }

  const coords: [number, number][] =
    result?.route?.geometry?.coordinates?.map((c: number[]) => [c[1], c[0]]) || [];

  return (
    <div className="layout">
      <aside className="sidebar">
        <h2>Route Awareness</h2>
        <form onSubmit={onSubmit} className="list">
          <label>
            From
            <input value={start} onChange={(e) => setStart(e.target.value)} required />
          </label>
          <label>
            To
            <input value={dest} onChange={(e) => setDest(e.target.value)} required />
          </label>
          <button className="primary" type="submit" disabled={loading}>Generate route</button>
        </form>
        {result && (
          <div className="card">
            <h3>ROUTE AWARENESS</h3>
            {result.route?.is_demo && <span className="badge b-demo">Demo Data</span>}
            <p>Start: {result.summary.start}</p>
            <p>Destination: {result.summary.destination}</p>
            <p>Distance: {result.route.distance_km} km · ~{result.route.duration_min} min</p>
            <p>Reported incidents nearby: {result.summary.reported_nearby}</p>
            <p>Unverified: {result.summary.unverified} · Verified: {result.summary.verified}</p>
            <p>Weather observations: {result.summary.weather_observations}</p>
            <p>AI indicator: {result.summary.ai_indicator}</p>
            <p>Last checked: {result.summary.last_checked}</p>
            <p><strong>{result.summary.headline}</strong></p>
            <p className="muted">{result.summary.disclaimer}</p>
            <p className="muted">{result.route.notice}</p>
          </div>
        )}
        {result?.weather && <WeatherCard data={result.weather} />}
        {result?.risk && <RiskCard risk={result.risk} />}
      </aside>
      <main className="main" id="main">
        {err && <ErrorState text={err} />}
        <MapView
          incidents={(result?.incidents || []) as Incident[]}
          routeCoords={coords}
          onOpen={() => undefined}
        />
        <h3>Incidents near route</h3>
        {(result?.incidents || []).map((i: Incident) => (
          <div className="row-item" key={i.id}>
            <span>{CATEGORY_META[i.category]?.icon}</span>
            <div>
              {CATEGORY_META[i.category]?.label} · {i.location_label}
              <div className="muted">{timeAgo(i.observed_at)}</div>
            </div>
            <StatusBadge status={i.verification_status} />
          </div>
        ))}
      </main>
    </div>
  );
}
