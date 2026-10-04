import { Link } from "react-router-dom";
import { Disclaimer } from "../components/Widgets";

export default function Landing() {
  return (
    <div className="hero">
      <div className="hero-inner">
        <p className="badge b-demo">Academic prototype · Shoolini University</p>
        <h1>HillGuard AI</h1>
        <h2>Intelligent Mountain Disaster Risk & Safe Route Awareness System</h2>
        <p>
          Understand mountain conditions, reported hazards, weather information and route risks through
          one intelligent map-based platform.
        </p>
        <div className="hero-actions">
          <Link className="primary" to="/map">Explore Live Map</Link>
          <Link className="ghost" to="/report">Report an Incident</Link>
        </div>
        <div className="mtn" aria-hidden="true" />
        <Disclaimer />
      </div>
    </div>
  );
}
