import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { api, CATEGORY_META, getUser } from "../api";
import { StatusBadge } from "../components/Widgets";

export default function Admin() {
  const user = getUser();
  const [items, setItems] = useState<any[]>([]);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<any>(null);
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState("verified");
  const [category, setCategory] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const allowed = !!user && (user.role === "ADMIN" || user.role === "MODERATOR");

  async function load(query = q) {
    const data = await api.adminReports(query);
    setItems(data.items);
  }

  useEffect(() => {
    if (allowed) load();
  }, [allowed]);

  if (!allowed) {
    return <Navigate to="/login" replace />;
  }

  async function apply() {
    if (!open) return;
    const updated = await api.adminStatus(open.id, {
      verification_status: status,
      reviewer_notes: notes,
      category: category || undefined,
    });
    setMsg("Status updated. Public map will show the new verification state.");
    setOpen(updated);
    load();
  }

  return (
    <main className="main" id="main">
      <h1>Moderator / Admin</h1>
      <p className="muted">AI-prioritized unverified and elevated-risk reports appear first.</p>
      <div className="filters">
        <input placeholder="Search reports" value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search reports" />
        <button className="ghost" type="button" onClick={() => load(q)}>Search</button>
      </div>
      {msg && <p className="toast">{msg}</p>}
      <table className="table">
        <thead>
          <tr>
            <th>ID</th><th>Type</th><th>Location</th><th>Status</th><th>AI</th><th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((i) => (
            <tr key={i.id}>
              <td>{i.id.slice(0, 8)}</td>
              <td>{CATEGORY_META[i.category]?.label}</td>
              <td>{i.location_label}</td>
              <td><StatusBadge status={i.verification_status} /></td>
              <td>{i.ai_risk_category}</td>
              <td><button className="ghost" type="button" onClick={() => { setOpen(i); setStatus(i.verification_status); setCategory(i.category); setNotes(i.reviewer_notes || ""); }}>Open</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      {open && (
        <aside className="drawer">
          <h2>Review {open.id.slice(0, 8)}</h2>
          {open.image_url && <img src={open.image_url} alt="Report photograph" style={{ width: "100%", borderRadius: 12 }} />}
          <p>{open.description}</p>
          <p>AI image: {open.ai_image_label || "n/a"}</p>
          <label>
            Status
            <select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="unverified">Unverified</option>
              <option value="under_review">Under Review</option>
              <option value="verified">Verified</option>
              <option value="rejected">Rejected</option>
              <option value="flagged">Flagged</option>
            </select>
          </label>
          <label>
            Category
            <select value={category} onChange={(e) => setCategory(e.target.value)}>
              {Object.entries(CATEGORY_META).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
          </label>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Reviewer notes / duplicate notes" />
          <button className="primary" type="button" onClick={apply}>Save review</button>
          <button className="ghost" type="button" onClick={() => setOpen(null)}>Close</button>
        </aside>
      )}
    </main>
  );
}
