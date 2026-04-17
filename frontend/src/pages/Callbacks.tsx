import { useCallback, useEffect, useState } from "react";

import { apiClient, type CallbackRecord } from "../api/client";

type ViewMode = "body" | "headers";

function formatHeaders(json: string): string {
  try {
    const parsed = JSON.parse(json);
    return Object.entries(parsed)
      .map(([k, v]) => `${k}: ${v}`)
      .join("\n");
  } catch {
    return json;
  }
}

export function CallbacksPage() {
  const [items, setItems] = useState<CallbackRecord[]>([]);
  const [view, setView] = useState<Record<number, ViewMode>>({});
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const rows = await apiClient.getCallbacks();
    setItems(rows);
  }, []);

  useEffect(() => {
    load().catch((err: unknown) => setError(String(err)));
    const timer = setInterval(() => {
      load().catch((err: unknown) => setError(String(err)));
    }, 3000);
    return () => clearInterval(timer);
  }, [load]);

  async function onClear() {
    if (!confirm("Clear all callback records?")) return;
    try {
      await apiClient.clearCallbacks();
      await load();
    } catch (err: unknown) {
      setError(String(err));
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h2>Callbacks</h2>
          <div className="subtitle">Incoming HTTP callbacks (auto-refresh every 3s).</div>
        </div>
        <div className="toolbar" style={{ margin: 0 }}>
          <button className="ghost" onClick={() => void load()}>Refresh</button>
          <button className="danger" onClick={onClear} disabled={items.length === 0}>
            Clear Inbox
          </button>
        </div>
      </div>

      {error ? <div className="error">{error}</div> : null}

      {items.length === 0 ? (
        <div className="empty">No callbacks received yet. POST to /callback/&lt;token&gt; to test.</div>
      ) : (
        <div className="grid">
          {items.map((item) => {
            const mode = view[item.id] ?? "body";
            return (
              <article className="card" key={item.id}>
                <div className="card-head">
                  <h3>#{item.id} · {item.token}</h3>
                  <span className="badge">{item.source_ip ?? "unknown"}</span>
                </div>
                <div className="meta-grid">
                  <span className="k">received</span>
                  <span className="v">{item.created_at}</span>
                </div>
                <div className="row" style={{ marginTop: 8 }}>
                  <button
                    className={mode === "body" ? "" : "ghost"}
                    onClick={() => setView({ ...view, [item.id]: "body" })}
                  >
                    Body
                  </button>
                  <button
                    className={mode === "headers" ? "" : "ghost"}
                    onClick={() => setView({ ...view, [item.id]: "headers" })}
                  >
                    Headers
                  </button>
                </div>
                <pre>
                  {mode === "body"
                    ? item.body || "<empty body>"
                    : formatHeaders(item.headers_json)}
                </pre>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
