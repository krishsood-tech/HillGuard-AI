import { CATEGORY_META, Incident, timeAgo } from "../api";

export function FreshnessBadge({ status, label, text }: { status?: string; label?: string; text?: string }) {
  const cls = status === "recent" ? "b-recent" : status === "aging" ? "b-aging" : status === "stale" ? "b-stale" : "b-na";
  const icon = status === "recent" ? "🟢" : status === "aging" ? "🟡" : status === "stale" ? "🔴" : "⚪";
  return (
    <span className={`badge ${cls}`}>
      <span aria-hidden>{icon}</span> {label || "Unavailable"} {text ? `· ${text}` : ""}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    verified: "b-verified",
    unverified: "b-unverified",
    under_review: "b-review",
    rejected: "b-rejected",
    flagged: "b-flagged",
  };
  return <span className={`badge ${map[status] || "b-na"}`}>{status.replace(/_/g, " ")}</span>;
}

export function SourceBadge({ source }: { source: string }) {
  return <span className="badge b-na">{source}</span>;
}

export function Disclaimer() {
  return (
    <p className="muted">
      HillGuard AI is an academic prototype. It does not replace government warnings, emergency services,
      disaster-management authorities, official weather advisories, or local authorities. AI-assisted
      indicators are not guaranteed predictions. Absence of reports does not mean a location is safe.
    </p>
  );
}

export function IncidentDetails({ incident, onClose, onSimilar }: { incident: Incident; onClose: () => void; onSimilar: () => void }) {
  const meta = CATEGORY_META[incident.category] || CATEGORY_META.other;
  return (
    <aside className="drawer" role="dialog" aria-label="Incident details">
      <button className="ghost" onClick={onClose} type="button">Close</button>
      <h2>{meta.icon} {meta.label}</h2>
      <p>Report ID: {incident.id}</p>
      <StatusBadge status={incident.verification_status} />
      <p>{incident.description}</p>
      <p>Location: {incident.location_label}</p>
      <p>Coordinates: {incident.latitude.toFixed(4)}, {incident.longitude.toFixed(4)}</p>
      <p>Observed: {incident.observed_at} ({timeAgo(incident.observed_at)})</p>
      <p>Submitted: {incident.submitted_at}</p>
      <p>Source: {incident.source_kind || incident.source}</p>
      {incident.image_url && (
        <img src={incident.image_url} alt={`Uploaded photograph for ${meta.label} report`} style={{ width: "100%", borderRadius: 12 }} />
      )}
      {incident.ai_image_label && (
        <div className="card">
          <h3>AI-assisted image triage</h3>
          <p>Classification: {incident.ai_image_label}</p>
          <p>Model confidence: {incident.ai_image_confidence}% (demonstration / uncalibrated)</p>
          <p>Status: Requires Human Review</p>
          <p className="muted">Possible hazard identified; human verification required. Not a confirmed hazard.</p>
        </div>
      )}
      {incident.ai_risk_category && (
        <div className="card">
          <h3>AI-assisted risk indicator</h3>
          <p>{incident.ai_risk_category}</p>
          <p className="muted">Experimental decision-support indicator — not an official warning.</p>
        </div>
      )}
      <FreshnessBadge status={incident.freshness?.status} label={incident.freshness?.status_label} text={incident.freshness?.freshness_text} />
      <p className="muted">{incident.limitations}</p>
      {incident.reviewer_notes && <p>Reviewer notes: {incident.reviewer_notes}</p>}
      <p>Last updated: {incident.last_updated}</p>
      <button className="primary" type="button" onClick={onSimilar}>Report similar incident</button>
    </aside>
  );
}

export function WeatherCard({ data }: { data: any }) {
  if (!data) return <div className="card">Weather: loading…</div>;
  if (!data.available) return <div className="card">Weather service temporarily unavailable.</div>;
  const v = data.values || {};
  return (
    <div className="card">
      <h3>Weather {data.is_demo && <span className="badge b-demo">Demo Data</span>}</h3>
      <p>{data.location}</p>
      <p>{v.condition} · {v.temperature_c}°C</p>
      <p>Rainfall: {v.rainfall_mm ?? "n/a"} · Humidity: {v.humidity ?? "n/a"} · Wind: {v.wind_kmh ?? "n/a"}</p>
      <p className="muted">Source: {data.source}</p>
      <FreshnessBadge status={data.freshness?.status} label={data.freshness?.status_label} text={data.freshness?.freshness_text} />
      {data.freshness?.stale && <p>Data may be outdated.</p>}
      <p className="muted">Last updated / retrieved: {data.freshness?.retrieved_at}</p>
    </div>
  );
}

export function RiskCard({ risk, onWhy }: { risk: any; onWhy?: () => void }) {
  if (!risk) return null;
  return (
    <div className="card">
      <h3>AI-ASSISTED RISK INDICATOR {risk.is_demo && <span className="badge b-demo">Demo Data</span>}</h3>
      <p style={{ fontSize: 28, margin: "8px 0" }}>{risk.risk_category}</p>
      <p>Reason: {(risk.factors || []).join(" + ")}</p>
      <p>Analysis: {risk.analysis_timestamp}</p>
      <p>Model: {risk.model_version}</p>
      <p>Data coverage: {risk.data_coverage}</p>
      <p className="muted">{risk.notice}</p>
      {onWhy && (
        <button className="ghost" type="button" onClick={onWhy}>
          Why?
        </button>
      )}
    </div>
  );
}

export function EmptyState({ text }: { text: string }) {
  return <div className="card muted">{text}</div>;
}

export function ErrorState({ text }: { text: string }) {
  return <div className="notice" role="alert">{text}</div>;
}

export function LoadingState({ text = "Loading…" }: { text?: string }) {
  return <div className="card">{text}</div>;
}
