import { useCallback, useEffect, useState } from "react";

import { apiClient, type CallbackRecord } from "../api/client";

export function CallbacksPage() {
  const [items, setItems] = useState<CallbackRecord[]>([]);
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
    try {
      await apiClient.clearCallbacks();
      await load();
    } catch (err: unknown) {
      setError(String(err));
    }
  }

  return (
    <section>
      <h2>Callbacks</h2>
      {error ? <p className="error">{error}</p> : null}
      <button onClick={onClear}>Clear Inbox</button>
      <div className="grid">
        {items.map((item) => (
          <article className="card" key={item.id}>
            <h3>#{item.id} token={item.token}</h3>
            <p>Source: {item.source_ip ?? "unknown"}</p>
            <p>At: {item.created_at}</p>
            <pre>{item.body || "<empty body>"}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}
