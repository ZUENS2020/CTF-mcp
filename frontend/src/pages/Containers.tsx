import { FormEvent, useCallback, useEffect, useState } from "react";

import { apiClient, type ContainerInfo } from "../api/client";
import { ContainerCard } from "../components/ContainerCard";

export function ContainersPage() {
  const [items, setItems] = useState<ContainerInfo[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [name, setName] = useState("kali-1");
  const [image, setImage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    const [containers, activeResp] = await Promise.all([
      apiClient.getContainers(),
      apiClient.getActiveContainer()
    ]);
    setItems(containers);
    setActive(activeResp.active_container);
  }, []);

  useEffect(() => {
    load().catch((err: unknown) => setError(String(err)));
    const t = setInterval(() => {
      load().catch(() => void 0);
    }, 5000);
    return () => clearInterval(t);
  }, [load]);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setCreating(true);
    try {
      await apiClient.createContainer(name, image || undefined);
      await load();
    } catch (err: unknown) {
      setError(String(err));
    } finally {
      setCreating(false);
    }
  }

  async function onActivate(containerName: string) {
    setError(null);
    try {
      await apiClient.activateContainer(containerName);
      await load();
    } catch (err: unknown) {
      setError(String(err));
    }
  }

  async function onDelete(containerName: string) {
    if (!confirm(`Delete container "${containerName}"? This is irreversible.`)) return;
    setError(null);
    try {
      await apiClient.deleteContainer(containerName);
      await load();
    } catch (err: unknown) {
      setError(String(err));
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h2>Containers</h2>
          <div className="subtitle">Kali worker containers — one is the active MCP target.</div>
        </div>
        <button className="ghost" onClick={() => void load()}>Refresh</button>
      </div>

      {error ? <div className="error">{error}</div> : null}

      <form className="card" onSubmit={onCreate} style={{ marginBottom: 18 }}>
        <h3>Create container</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr auto", gap: 12, alignItems: "end" }}>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Image <span style={{ color: "var(--text-dim)" }}>(default: ctf-kali:latest)</span>
            <input
              value={image}
              onChange={(e) => setImage(e.target.value)}
              placeholder="ctf-kali:latest"
            />
          </label>
          <button type="submit" disabled={creating}>{creating ? "Creating..." : "Create"}</button>
        </div>
      </form>

      {items.length === 0 ? (
        <div className="empty">No containers — create one above.</div>
      ) : (
        <div className="grid">
          {items.map((item) => (
            <ContainerCard
              key={item.id}
              item={item}
              isActive={item.name === active}
              onActivate={onActivate}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </section>
  );
}
