import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Marker, Popup, TileLayer, Polyline, useMap } from "react-leaflet";
import L from "leaflet";
import { CATEGORY_META, Incident, timeAgo } from "../api";

const DEFAULT_TILE = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png";

function pinIcon(color: string) {
  return L.divIcon({
    className: "",
    html: `<div class="marker-pin" style="background:${color}"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 18],
    popupAnchor: [0, -16],
  });
}

function FlyTo({ lat, lng, zoom = 11 }: { lat: number; lng: number; zoom?: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lng], zoom);
  }, [lat, lng, zoom, map]);
  return null;
}

function FitLine({ coords }: { coords: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (coords.length) map.fitBounds(L.latLngBounds(coords), { padding: [40, 40] });
  }, [coords, map]);
  return null;
}

export function MapLegend() {
  return (
    <aside className="legend" aria-label="Map legend">
      <strong>Legend</strong>
      <ul>
        {Object.entries(CATEGORY_META).map(([k, v]) => (
          <li key={k}>
            <span className="dot" style={{ background: v.color }} />
            <span aria-hidden>{v.icon}</span> {v.label}
          </li>
        ))}
        <li><span className="dot" style={{ background: "#16a34a" }} /> Verified</li>
        <li><span className="dot" style={{ background: "#ca8a04" }} /> Unverified</li>
        <li><span className="dot" style={{ background: "#7c3aed" }} /> AI Estimated Risk (area)</li>
      </ul>
    </aside>
  );
}

export default function MapView({
  incidents,
  center,
  flyTo,
  routeCoords,
  clusters,
  userPos,
  onOpen,
  tileUrl,
}: {
  incidents: Incident[];
  center?: [number, number];
  flyTo?: { lat: number; lng: number } | null;
  routeCoords?: [number, number][];
  clusters?: { center: { lat: number; lng: number }; count: number; primary_type: string; area: string; time_window: string; verification_status: string; explanation: string }[];
  userPos?: { lat: number; lng: number } | null;
  onOpen: (inc: Incident) => void;
  tileUrl?: string;
}) {
  const start = center || [31.8, 77.2];
  const line = useMemo(() => routeCoords || [], [routeCoords]);

  return (
    <div className="map-wrap" role="region" aria-label="Live hazard map of Himachal Pradesh">
      <MapContainer center={start} zoom={8} style={{ height: "100%", width: "100%" }} aria-label="Interactive map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; CARTO'
          url={tileUrl || DEFAULT_TILE}
        />
        {flyTo && <FlyTo lat={flyTo.lat} lng={flyTo.lng} />}
        {line.length > 0 && (
          <>
            <Polyline positions={line} pathOptions={{ color: "#0f4c81", weight: 5, opacity: 0.85 }} />
            <FitLine coords={line} />
          </>
        )}
        {clusters?.map((c) => (
          <CircleMarker
            key={c.area + c.count}
            center={[c.center.lat, c.center.lng]}
            radius={18}
            pathOptions={{ color: "#7c3aed", fillOpacity: 0.2 }}
          >
            <Popup>
              <strong>INCIDENT CLUSTER</strong>
              <p>{c.count} reports</p>
              <p>Primary type: {c.primary_type.replace(/_/g, " ")}</p>
              <p>Area: {c.area}</p>
              <p>Time window: {c.time_window}</p>
              <p>Status: {c.verification_status} — Requires review</p>
              <p className="muted">{c.explanation}</p>
            </Popup>
          </CircleMarker>
        ))}
        {incidents.map((inc) => {
          const meta = CATEGORY_META[inc.category] || CATEGORY_META.other;
          return (
            <Marker key={inc.id} position={[inc.latitude, inc.longitude]} icon={pinIcon(meta.color)}>
              <Popup>
                <div>
                  <strong>HAZARD REPORT</strong>
                  <p>Type: {meta.label}</p>
                  <p>Location: {inc.location_label}</p>
                  <p>Reported: {timeAgo(inc.observed_at)}</p>
                  <p>Status: {inc.verification_status}</p>
                  <p>Source: {inc.source_kind || inc.source}</p>
                  <p>{inc.description}</p>
                  <p>AI Assessment: {inc.ai_risk_category || "Not computed"}</p>
                  <p>Data freshness: {inc.freshness?.status_label || "Unknown"}</p>
                  <button className="primary" type="button" onClick={() => onOpen(inc)}>
                    View Details
                  </button>
                </div>
              </Popup>
            </Marker>
          );
        })}
        {userPos && (
          <CircleMarker center={[userPos.lat, userPos.lng]} radius={8} pathOptions={{ color: "#0ea5e9" }}>
            <Popup>Your approximate location (browser geolocation)</Popup>
          </CircleMarker>
        )}
      </MapContainer>
      <MapLegend />
    </div>
  );
}
