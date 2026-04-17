import { FormEvent, useCallback, useEffect, useState } from "react";

import { apiClient, type ContainerInfo } from "../api/client";
import { ContainerCard } from "../components/ContainerCard";

export function ContainersPage() {
  const [items, setItems] = useState<ContainerInfo[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [name, setName] = useState("kali-1");
  const [image, setImage] = useState("");
  const [error, setError] = useState<string | null>(null);

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
  }, [load]);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setError(null);
    try {
      await apiClient.createContainer(name, image || undefined);
      await load();
    } catch (err: unknown) {
      setError(String(err));
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
      <h2>Containers</h2>
      {error ? <p className="error">{error}</p> : null}

      <form className="card" onSubmit={onCreate}>
        <h3>Create Container</h3>
        <label>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          Image (optional)
          <input value={image} onChange={(e) => setImage(e.target.value)} placeholder="kalilinux/kali-rolling:latest" />
        </label>
        <button type="submit">Create</button>
      </form>

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
    </section>
  );
}
