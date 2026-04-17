import { useEffect, useState } from "react";

import { apiClient, type ContainerInfo } from "../api/client";

export function DashboardPage() {
  const [active, setActive] = useState<string | null>(null);
  const [containers, setContainers] = useState<ContainerInfo[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([apiClient.getActiveContainer(), apiClient.getContainers()])
      .then(([a, c]) => {
        setActive(a.active_container);
        setContainers(c);
      })
      .catch((err: unknown) => setError(String(err)));
  }, []);

  return (
    <section>
      <h2>Dashboard</h2>
      {error ? <p className="error">{error}</p> : null}
      <p>Active container: <strong>{active ?? "None"}</strong></p>
      <p>Total containers: <strong>{containers.length}</strong></p>
    </section>
  );
}
