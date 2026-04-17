import { useCallback, useEffect, useState } from "react";

import {
  apiClient,
  type CallbackRecord,
  type ContainerInfo,
  type TunnelInfo
} from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

export function DashboardPage() {
  const [active, setActive] = useState<string | null>(null);
  const [containers, setContainers] = useState<ContainerInfo[]>([]);
  const [callbacks, setCallbacks] = useState<CallbackRecord[]>([]);
  const [tunnels, setTunnels] = useState<TunnelInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [a, c, cb, tn] = await Promise.all([
      apiClient.getActiveContainer(),
      apiClient.getContainers(),
      apiClient.getCallbacks(),
      apiClient.getTunnels()
    ]);
    setActive(a.active_container);
    setContainers(c);
    setCallbacks(cb);
    setTunnels(tn.tunnels);
  }, []);

  useEffect(() => {
    load().catch((err: unknown) => setError(String(err)));
    const t = setInterval(() => {
      load().catch((err: unknown) => setError(String(err)));
    }, 5000);
    return () => clearInterval(t);
  }, [load]);

  const running = containers.filter((c) => c.status.toLowerCase() === "running").length;
  const liveTunnels = tunnels.filter((t) => t.running).length;

  return (
    <section>
      <div className="page-head">
        <div>
          <h2>Dashboard</h2>
          <div className="subtitle">Overview of containers, tunnels, and recent callbacks.</div>
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <div className="stat-grid">
        <div className="stat-card">
          <div className="label">Active container</div>
          <div className="value">{active ?? "—"}</div>
          <div className="hint">target of MCP shell_exec tools</div>
        </div>
        <div className="stat-card">
          <div className="label">Containers</div>
          <div className="value">{containers.length}</div>
          <div className="hint">{running} running</div>
        </div>
        <div className="stat-card">
          <div className="label">Bore tunnels</div>
          <div className="value">{liveTunnels}</div>
          <div className="hint">{tunnels.length} total configured</div>
        </div>
        <div className="stat-card">
          <div className="label">Callbacks</div>
          <div className="value">{callbacks.length}</div>
          <div className="hint">HTTP inbox entries</div>
        </div>
      </div>

      <h3 style={{ marginTop: 24 }}>Containers</h3>
      {containers.length === 0 ? (
        <div className="empty">No containers yet — create one from the Containers page.</div>
      ) : (
        <div className="grid">
          {containers.slice(0, 6).map((c) => (
            <article className="card" key={c.id}>
              <div className="card-head">
                <h3>{c.name}</h3>
                {c.name === active ? (
                  <span className="badge badge-active">active</span>
                ) : (
                  <StatusBadge status={c.status} />
                )}
              </div>
              <div className="meta-grid">
                <span className="k">image</span>
                <span className="v">{c.image}</span>
                <span className="k">id</span>
                <span className="v">{c.id}</span>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
