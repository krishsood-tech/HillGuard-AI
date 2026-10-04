import { FormEvent, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Bell, LocateFixed, UserRound } from "lucide-react";
import { api, clearSession, getUser } from "../api";

export default function Layout() {
  const nav = useNavigate();
  const user = getUser();
  const [msg, setMsg] = useState<string | null>(null);
  const [notes, setNotes] = useState<any[] | null>(null);
  const [q, setQ] = useState("");

  async function locate() {
    if (!navigator.geolocation) {
      setMsg("Geolocation is not supported in this browser. Use search instead.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        nav(`/map?lat=${pos.coords.latitude}&lng=${pos.coords.longitude}&me=1`);
      },
      () => setMsg("Location permission denied. You can search a place instead."),
    );
  }

  async function onSearch(e: FormEvent) {
    e.preventDefault();
    if (!q.trim()) return;
    nav(`/map?q=${encodeURIComponent(q.trim())}`);
  }

  async function toggleNotes() {
    if (notes) {
      setNotes(null);
      return;
    }
    const data = await api.notifications();
    setNotes(data.items);
  }

  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <header className="topbar">
        <NavLink to="/dashboard" className="brand" aria-label="HillGuard AI home">
          <span className="brand-mark">HG</span>
          HillGuard AI
        </NavLink>
        <nav className="nav" aria-label="Primary">
          <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/dashboard">Dashboard</NavLink>
          <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/map">Live Map</NavLink>
          <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/routes">Route Awareness</NavLink>
          <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/report">Report Incident</NavLink>
          <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/analytics">Analytics</NavLink>
          <NavLink className={({ isActive }) => (isActive ? "active" : "")} to="/about">About</NavLink>
        </nav>
        <div className="top-actions">
          <form onSubmit={onSearch} style={{ display: "flex", gap: 6 }}>
            <input
              aria-label="Search Himachal Pradesh location"
              placeholder="Search Himachal Pradesh location..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </form>
          <button className="icon-btn" type="button" onClick={locate} aria-label="Use my location">
            <LocateFixed size={16} />
          </button>
          <button className="icon-btn" type="button" onClick={toggleNotes} aria-label="Notifications">
            <Bell size={16} />
          </button>
          <NavLink to="/login" className="icon-btn" aria-label="User profile">
            <UserRound size={16} /> {user?.role || "Guest"}
          </NavLink>
          {(user?.role === "ADMIN" || user?.role === "MODERATOR") && (
            <NavLink to="/admin" className="primary">Admin</NavLink>
          )}
          {user && (
            <button className="ghost" type="button" onClick={() => { clearSession(); nav("/"); }}>
              Sign out
            </button>
          )}
        </div>
      </header>
      {notes && (
        <aside className="drawer" aria-label="Information notifications">
          <h3>Information centre</h3>
          <p className="muted">These are informational notices, not official emergency alerts.</p>
          {notes.map((n) => (
            <div key={n.id} className="card">
              <strong>{n.title}</strong>
              <p>{n.body}</p>
              <span className="badge b-na">{n.official_label}</span>
            </div>
          ))}
          <button className="ghost" type="button" onClick={() => setNotes(null)}>Close</button>
        </aside>
      )}
      <Outlet />
      <nav className="mobile-nav" aria-label="Mobile">
        <NavLink to="/dashboard">Home</NavLink>
        <NavLink to="/map">Map</NavLink>
        <NavLink to="/report">Report</NavLink>
        <NavLink to="/routes">Route</NavLink>
        <NavLink to="/about">About</NavLink>
      </nav>
      {msg && (
        <div className="toast" role="status">
          {msg}
          <button className="ghost" type="button" onClick={() => setMsg(null)}>OK</button>
        </div>
      )}
    </>
  );
}
