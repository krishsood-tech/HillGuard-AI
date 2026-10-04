import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, CATEGORY_META, Incident } from "../api";
import MapView from "../components/MapView";
import { ErrorState, IncidentDetails, RiskCard, WeatherCard } from "../components/Widgets";

export default function LiveMap() {
  const [params] = useSearchParams();
  const nav = useNavigate();
  const [items, setItems] = useState<Incident[]>([]);
  const [clusters, setClusters] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [open, setOpen] = useState<Incident | null>(null);
  const [flyTo, setFlyTo] = useState<{ lat: number; lng: number } | null>(null);
  const [userPos, setUserPos] = useState<{ lat: number; lng: number } | null>(null);
  const [weather, setWeather] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [filter, setFilter] = useState("all");
  const [health, setHealth] = useState<any>(null);

  async function load(extra?: Record<string, string>) {
    try {
      const inc = await api.incidents({ category: extra?.category || filter, ...extra });
      setItems(inc.items);
      setClusters((await api.clusters()).items);
      setHealth(await api.health());
    } catch (e: any) {
      setErr("Unable to load incident data.");
    }
  }

  useEffect(() => {
    load();
  }, [filter]);

  useEffect(() => {
    const q = params.get("q");
    const lat = params.get("lat");
    const lng = params.get("lng");
    if (q) {
      api.search(q).then((res) => {
        if (!res.found) {
          setErr("No matching location in available data.");
          return;
        }
        setFlyTo({ lat: res.place.lat, lng: res.place.lng });
        setItems(res.nearby);
        setWeather(res.weather);
        setRisk(res.risk);
      });
    }
    if (lat && lng) {
      const la = Number(lat), ln = Number(lng);
      setFlyTo({ lat: la, lng: ln });
      if (params.get("me")) setUserPos({ lat: la, lng: ln });
      api.nearby(la, ln).then((r) => setItems(r.items));
      api.weather(la, ln).then(setWeather);
      api.risk(la, ln).then(setRisk);
    }
  }, [params]);

  return (
    <div className="layout">
      <aside className="sidebar">
        <h2>Live Map</h2>
        <p className="muted">Himachal Pradesh pilot. Not every location has real-time data.</p>
        <select aria-label="Filter category" value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All hazards</option>
          {Object.entries(CATEGORY_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
        </select>
        <button className="ghost" type="button" onClick={() => { setFlyTo({ lat: 31.8, lng: 77.2 }); load(); }}>Reset map</button>
        <WeatherCard data={weather} />
        <RiskCard risk={risk} />
      </aside>
      <main className="main" id="main">
        {err && <ErrorState text={err} />}
        <MapView
          incidents={items}
          clusters={clusters}
          flyTo={flyTo}
          userPos={userPos}
          onOpen={setOpen}
          tileUrl={health?.map_tile_url}
        />
      </main>
      {open && (
        <IncidentDetails
          incident={open}
          onClose={() => setOpen(null)}
          onSimilar={() => nav(`/report?cat=${open.category}&lat=${open.latitude}&lng=${open.longitude}`)}
        />
      )}
    </div>
  );
}
