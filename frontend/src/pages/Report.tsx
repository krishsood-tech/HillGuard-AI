import { FormEvent, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CircleMarker, MapContainer, TileLayer, useMapEvents } from "react-leaflet";
import { api, CATEGORY_META } from "../api";

function ClickCapture({ onPick }: { onPick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onPick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

export default function Report() {
  const [params] = useSearchParams();
  const [category, setCategory] = useState(params.get("cat") || "landslide");
  const [description, setDescription] = useState("");
  const [lat, setLat] = useState(Number(params.get("lat") || 31.7084));
  const [lng, setLng] = useState(Number(params.get("lng") || 76.932));
  const [observed, setObserved] = useState(new Date().toISOString().slice(0, 16));
  const [contact, setContact] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [msg, setMsg] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  async function useLocation() {
    navigator.geolocation.getCurrentPosition(
      (p) => {
        setLat(p.coords.latitude);
        setLng(p.coords.longitude);
      },
      () => setErr("Location permission denied. Select a point on the map or search."),
    );
  }

  async function findPlace(e: FormEvent) {
    e.preventDefault();
    const res = await api.search(search);
    if (res.found) {
      setLat(res.place.lat);
      setLng(res.place.lng);
    } else setErr("Location not found in available indexes.");
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    const fd = new FormData();
    fd.set("category", category);
    fd.set("description", description);
    fd.set("latitude", String(lat));
    fd.set("longitude", String(lng));
    fd.set("observed_at", new Date(observed).toISOString());
    if (contact) fd.set("contact_ref", contact);
    if (file) fd.set("image", file);
    try {
      const res = await api.createIncident(fd);
      setMsg(res);
    } catch (ex: any) {
      setErr(ex.message);
    }
  }

  return (
    <main className="main" id="main">
      <h1>Report an incident</h1>
      <p className="muted">Reports start as Unverified and need human review. Do not submit emergency calls here.</p>
      {err && <div className="notice" role="alert">{err}</div>}
      {msg && (
        <div className="card">
          <h3>Report submitted successfully.</h3>
          <p>Report ID: {msg.report_id}</p>
          <p>Submitted: {msg.submitted_at}</p>
          <p>Status: {msg.status}</p>
          {msg.ai_image && (
            <p>
              AI-assisted image triage: {msg.ai_image.classification} ({msg.ai_image.confidence}%) — {msg.ai_image.status}
            </p>
          )}
        </div>
      )}
      <div className="grid-2">
        <form className="card list" onSubmit={submit}>
          <label>
            Hazard type
            <select value={category} onChange={(e) => setCategory(e.target.value)} required>
              {Object.entries(CATEGORY_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
          </label>
          <label>
            Description
            <textarea required minLength={8} value={description} onChange={(e) => setDescription(e.target.value)} />
          </label>
          <label>
            Date/time observed
            <input type="datetime-local" value={observed} onChange={(e) => setObserved(e.target.value)} required />
          </label>
          <label>
            Photograph (JPG, PNG, WEBP)
            <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </label>
          <label>
            Optional contact / reference
            <input value={contact} onChange={(e) => setContact(e.target.value)} />
          </label>
          <p>Selected: {lat.toFixed(4)}, {lng.toFixed(4)}</p>
          <button className="ghost" type="button" onClick={useLocation}>Use my location</button>
          <button className="primary" type="submit">Submit report</button>
        </form>
        <div>
          <form onSubmit={findPlace} className="filters">
            <input placeholder="Search location" value={search} onChange={(e) => setSearch(e.target.value)} aria-label="Search location" />
            <button className="ghost" type="submit">Find</button>
          </form>
          <div className="map-wrap" style={{ height: 360, marginTop: 12 }}>
            <MapContainer center={[lat, lng]} zoom={10} style={{ height: "100%" }}>
              <TileLayer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" attribution="© OSM © CARTO" />
              <CircleMarker center={[lat, lng]} radius={10} pathOptions={{ color: "#d62828" }} />
              <ClickCapture onPick={(a, b) => { setLat(a); setLng(b); }} />
            </MapContainer>
          </div>
          <p className="muted">Click the map to set the incident location.</p>
        </div>
      </div>
    </main>
  );
}
