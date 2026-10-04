import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { Disclaimer } from "../components/Widgets";

export default function About() {
  return (
    <main className="main" id="main">
      <h1>About HillGuard AI</h1>
      <p><strong>Full name:</strong> Intelligent Mountain Disaster Risk and Safe Route Awareness System</p>
      <h2>Purpose</h2>
      <p>
        Help people living in or travelling through mountain regions understand possible landslides, flash floods,
        heavy rainfall, waterlogging, falling rocks, road blockages and related conditions using available reports,
        weather observations and experimental AI indicators.
      </p>
      <h2>Problem</h2>
      <p>Hazard information is fragmented across informal reports, maps and weather sources, especially in hill districts.</p>
      <h2>Solution</h2>
      <p>A map-centred awareness console with community reporting, moderator verification, clustering and route context.</p>
      <h2>Technology</h2>
      <p>React, Leaflet/OpenStreetMap, FastAPI, PostgreSQL/PostGIS (SQLite demo fallback), scikit-learn.</p>
      <h2>AI/ML components</h2>
      <p>Relative risk indicator, demonstration image triage, DBSCAN clustering. See <Link to="/ai">How AI Works</Link>.</p>
      <h2>Limitations</h2>
      <Disclaimer />
      <h2>Academic project</h2>
      <p>University: Shoolini University</p>
      <p>Programme: BCA — Artificial Intelligence and Machine Learning</p>
      <p>
        Related: <Link to="/sources">Data sources</Link> · <Link to="/emergency">Emergency information</Link>
      </p>
    </main>
  );
}

export function HowAI() {
  return (
    <main className="main" id="main">
      <h1>How AI Works</h1>
      <h2>Risk estimation</h2>
      <p>Uses available environmental/location/incident information to produce a relative category: Lower, Moderate, Elevated, Higher.</p>
      <h2>Image triage</h2>
      <p>Attempts to classify submitted hazard photographs as possible landslide, flood, obstruction, damage, rocks, or uncertain.</p>
      <h2>Incident clustering</h2>
      <p>Finds groups of reports based on location and time (DBSCAN). A cluster does not prove a disaster occurred.</p>
      <p className="notice">AI results are supporting indicators and may be incomplete or incorrect.</p>
      <Disclaimer />
    </main>
  );
}

export function Sources() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    api.sources().then(setData);
  }, []);
  if (!data) return <main className="main">Loading sources…</main>;
  return (
    <main className="main" id="main">
      <h1>Data sources & transparency</h1>
      {data.items.map((s: any) => (
        <div className="card" key={s.name}>
          <h3>{s.name}</h3>
          <p>Data: {s.data_type}</p>
          <p>Status: {s.status}</p>
          <p>Update frequency: {s.update_frequency}</p>
          <p>License / attribution: {s.license}</p>
          <p>Kind: {s.kind}</p>
        </div>
      ))}
      <h2>Source kinds</h2>
      {Object.entries(data.kinds).map(([k, v]) => (
        <p key={k}><strong>{k}:</strong> {String(v)}</p>
      ))}
    </main>
  );
}

export function Emergency() {
  const [health, setHealth] = useState<any>(null);
  useEffect(() => {
    api.health().then(setHealth);
  }, []);
  const e = health?.emergency || {};
  return (
    <main className="main" id="main">
      <div className="emergency">
        <h1>Emergency information</h1>
        <p>
          FOR OFFICIAL WARNINGS AND EMERGENCY INSTRUCTIONS, FOLLOW RELEVANT GOVERNMENT AUTHORITIES AND EMERGENCY SERVICES.
        </p>
        <p>HillGuard AI does not provide emergency response.</p>
        <ul>
          {e.imd && <li><a href={e.imd} rel="noreferrer" target="_blank">India Meteorological Department</a></li>}
          {e.ndma && <li><a href={e.ndma} rel="noreferrer" target="_blank">National Disaster Management Authority</a></li>}
          {e.hpsdma && <li><a href={e.hpsdma} rel="noreferrer" target="_blank">Himachal Pradesh SDMA</a></li>}
        </ul>
      </div>
    </main>
  );
}
