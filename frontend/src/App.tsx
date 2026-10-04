import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Landing from "./pages/Landing";
import Dashboard from "./pages/Dashboard";
import LiveMap from "./pages/LiveMap";
import RoutesPage from "./pages/Routes";
import Report from "./pages/Report";
import Analytics from "./pages/Analytics";
import About, { Emergency, HowAI, Sources } from "./pages/About";
import Login from "./pages/Login";
import Admin from "./pages/Admin";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/map" element={<LiveMap />} />
          <Route path="/routes" element={<RoutesPage />} />
          <Route path="/report" element={<Report />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/about" element={<About />} />
          <Route path="/ai" element={<HowAI />} />
          <Route path="/sources" element={<Sources />} />
          <Route path="/emergency" element={<Emergency />} />
          <Route path="/login" element={<Login />} />
          <Route path="/admin" element={<Admin />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
