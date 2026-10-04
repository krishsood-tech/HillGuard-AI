import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, CATEGORY_META } from "../api";
import MapView from "../components/MapView";

const COLORS = ["#d62828", "#1d4ed8", "#2563eb", "#d97706", "#ea580c", "#c2410c", "#0284c7", "#64748b"];

export default function Analytics() {
  const [data, setData] = useState<any>(null);
  useEffect(() => {
    api.analytics().then(setData);
  }, []);
  if (!data) return <main className="main">Loading analytics…</main>;
  const byType = Object.entries(data.by_type || {}).map(([k, v]) => ({ name: CATEGORY_META[k]?.label || k, value: v }));
  const byStatus = Object.entries(data.by_status || {}).map(([k, v]) => ({ name: k, value: v }));
  const dens = (data.density || []).map((d: any) => ({
    id: `${d.lat}${d.lng}${d.category}`,
    category: d.category,
    latitude: d.lat,
    longitude: d.lng,
    description: "Density point",
    observed_at: new Date().toISOString(),
    submitted_at: new Date().toISOString(),
    source: "analytics",
    verification_status: "verified",
  }));

  return (
    <main className="main" id="main">
      <h1>Analytics</h1>
      <p className="muted">Derived from available community reports. Not an official incident census.</p>
      <div className="kpis">
        {Object.entries(data.kpis).map(([k, v]) => (
          <div className="card kpi" key={k}><h3>{k.replace(/_/g, " ")}</h3><p>{String(v)}</p></div>
        ))}
      </div>
      <div className="grid-2">
        <div className="card" style={{ height: 320 }}>
          <h3>Incidents by type</h3>
          <ResponsiveContainer>
            <BarChart data={byType}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" hide />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#1d6fd6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card" style={{ height: 320 }}>
          <h3>Verification status</h3>
          <ResponsiveContainer>
            <PieChart>
              <Pie data={byStatus} dataKey="value" nameKey="name" outerRadius={90} label>
                {byStatus.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card" style={{ height: 320, marginTop: 16 }}>
        <h3>Reports over time</h3>
        <ResponsiveContainer>
          <LineChart data={data.over_time}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Line type="monotone" dataKey="count" stroke="#0f4c81" />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <h3>Incident density (map)</h3>
      <MapView incidents={dens} onOpen={() => undefined} />
    </main>
  );
}
