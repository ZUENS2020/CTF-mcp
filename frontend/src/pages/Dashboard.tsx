import { useCallback, useEffect, useState } from "react";

import {
  apiClient,
  type CallbackRecord,
  type ContainerInfo
} from "../api/client";
import { StatusBadge } from "../components/StatusBadge";

export function DashboardPage() {
  const [containers, setContainers] = useState<ContainerInfo[]>([]);
  const [callbacks, setCallbacks] = useState<CallbackRecord[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [c, cb] = await Promise.all([
      apiClient.getContainers(),
      apiClient.getCallbacks()
    ]);
    setContainers(c);
    setCallbacks(cb);
  }, []);

  useEffect(() => {
    load().catch((err: unknown) => setError(String(err)));
    const t = setInterval(() => {
      load().catch((err: unknown) => setError(String(err)));
    }, 5000);
    return () => clearInterval(t);
  }, [load]);

  const running = containers.filter((c) => c.status.toLowerCase() === "running").length;

  return (
    <section>
      <div className="page-head">
        <div>
          <h2>Dashboard</h2>
          <div className="subtitle">Overview of containers and recent callbacks.</div>
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}

      <div className="stat-grid">
        <div className="stat-card">
          <div className="label">Containers</div>
          <div className="value">{containers.length}</div>
          <div className="hint">{running} running</div>
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
                <StatusBadge status={c.status} />
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
