import { NavLink, Route, Routes } from "react-router-dom";

import { CallbacksPage } from "./pages/Callbacks";
import { ContainersPage } from "./pages/Containers";
import { DashboardPage } from "./pages/Dashboard";
import { SettingsPage } from "./pages/Settings";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/containers", label: "Containers" },
  { to: "/callbacks", label: "Callbacks" },
  { to: "/settings", label: "Settings" }
];

export function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>CTF AutoPwn</h1>
        <nav>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to} end={link.to === "/"} className="nav-link">
              {link.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/containers" element={<ContainersPage />} />
          <Route path="/callbacks" element={<CallbacksPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
