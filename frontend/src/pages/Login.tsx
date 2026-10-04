import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, getUser, setSession } from "../api";

export default function Login() {
  const nav = useNavigate();
  const existing = getUser();
  const [email, setEmail] = useState("admin@hillguard.local");
  const [password, setPassword] = useState("HillGuardAdmin123!");
  const [name, setName] = useState("");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [err, setErr] = useState<string | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    try {
      const res = mode === "login" ? await api.login(email, password) : await api.register(email, password, name);
      setSession(res.access_token, { email: res.email, role: res.role, display_name: res.display_name });
      nav(res.role === "USER" ? "/dashboard" : "/admin");
    } catch (ex: any) {
      setErr(ex.message);
    }
  }

  return (
    <main className="main" id="main">
      <div className="card" style={{ maxWidth: 420 }}>
        <h1>{mode === "login" ? "Sign in" : "Create account"}</h1>
        {existing && <p>Signed in as {existing.email} ({existing.role})</p>}
        {err && <p className="notice">{err}</p>}
        <form className="list" onSubmit={submit}>
          {mode === "register" && <input placeholder="Display name" value={name} onChange={(e) => setName(e.target.value)} />}
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} aria-label="Email" />
          <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} aria-label="Password" />
          <button className="primary" type="submit">{mode === "login" ? "Sign in" : "Register"}</button>
        </form>
        <button className="ghost" type="button" onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Need an account?" : "Have an account?"}
        </button>
        <p className="muted">Demo: admin@hillguard.local / HillGuardAdmin123! · user@hillguard.local / HillGuardUser123!</p>
      </div>
    </main>
  );
}
