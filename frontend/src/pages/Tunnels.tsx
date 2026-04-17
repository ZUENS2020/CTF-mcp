import { useCallback, useEffect, useState } from "react";

import { apiClient, type TunnelInfo } from "../api/client";

export function TunnelsPage() {
  const [tunnels, setTunnels] = useState<TunnelInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const { tunnels } = await apiClient.getTunnels();
    setTunnels(tunnels);
  }, []);

  useEffect(() => {
    load().catch((err: unknown) => setError(String(err)));
    const t = setInterval(() => {
      load().catch(() => void 0);
    }, 3000);
    return () => clearInterval(t);
  }, [load]);

  return (
    <section>
      <div className="page-head">
        <div>
          <h2>Bore Tunnels</h2>
          <div className="subtitle">
            Read-only view of bore TCP tunnels managed by the backend. Create/stop via MCP tools{" "}
            <code>start_bore</code> / <code>stop_bore</code>.
          </div>
        </div>
        <button className="ghost" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error">{error}</div> : null}

      {tunnels.length === 0 ? (
        <div className="empty">
          No tunnels. Call <code>start_bore(local_port=4444)</code> via MCP to open one.
        </div>
      ) : (
        <div className="grid">
          {tunnels.map((t) => {
            const remote =
              t.remote_host && t.remote_port ? `${t.remote_host}:${t.remote_port}` : "—";
            const statusClass = t.running
              ? "badge-running"
              : t.desired
              ? "badge-created"
              : "badge-exited";
            const statusLabel = t.running
              ? "running"
              : t.desired
              ? "starting"
              : "stopped";
            return (
              <article className="card" key={t.local_port}>
                <div className="card-head">
                  <h3>:{t.local_port} → {t.server}</h3>
                  <span className={`badge ${statusClass}`}>{statusLabel}</span>
                </div>
                <div className="meta-grid">
                  <span className="k">public</span>
                  <span className="v">{remote}</span>
                  {t.container ? (
                    <>
                      <span className="k">container</span>
                      <span className="v">{t.container}</span>
                    </>
                  ) : null}
                  <span className="k">restarts</span>
                  <span className="v">{t.restart_count}</span>
                  <span className="k">started</span>
                  <span className="v">{t.started_at}</span>
                  {t.last_exit_code !== null ? (
                    <>
                      <span className="k">last exit</span>
                      <span className="v">{t.last_exit_code}</span>
                    </>
                  ) : null}
                  {t.last_error ? (
                    <>
                      <span className="k">error</span>
                      <span className="v" style={{ color: "var(--danger)" }}>{t.last_error}</span>
                    </>
                  ) : null}
                </div>
                {t.last_logs.length > 0 ? (
                  <pre>{t.last_logs.slice(-10).join("\n")}</pre>
                ) : null}
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
