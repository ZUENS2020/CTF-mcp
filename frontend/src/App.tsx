import { useEffect, useState } from "react";
import { NavLink, Route, Routes } from "react-router-dom";

import { apiClient } from "./api/client";
import { CallbacksPage } from "./pages/Callbacks";
import { ContainersPage } from "./pages/Containers";
import { DashboardPage } from "./pages/Dashboard";
import { SettingsPage } from "./pages/Settings";
import { TunnelsPage } from "./pages/Tunnels";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/containers", label: "Containers" },
  { to: "/tunnels", label: "Tunnels" },
  { to: "/callbacks", label: "Callbacks" },
  { to: "/settings", label: "Settings" }
];

export function App() {
  const [health, setHealth] = useState<"ok" | "fail" | "unknown">("unknown");

  useEffect(() => {
    let cancelled = false;
    async function ping() {
      try {
        const res = await apiClient.getHealth();
        if (!cancelled) setHealth(res.status === "ok" ? "ok" : "fail");
      } catch {
        if (!cancelled) setHealth("fail");
      }
    }
    ping();
    const t = setInterval(ping, 5000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  return (
    <div className="layout">
      <aside className="sidebar">
        <div>
          <h1><span className="brand-dot" /> CTF AutoPwn</h1>
          <div className="brand-sub">MCP Control Plane</div>
        </div>
        <nav>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === "/"} className="nav-link">
              {link.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className={`health-dot ${health === "ok" ? "ok" : health === "fail" ? "fail" : ""}`} />
          backend {health === "ok" ? "online" : health === "fail" ? "offline" : "..."}
        </div>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/containers" element={<ContainersPage />} />
          <Route path="/tunnels" element={<TunnelsPage />} />
          <Route path="/callbacks" element={<CallbacksPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
