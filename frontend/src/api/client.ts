export type ContainerInfo = {
  id: string;
  name: string;
  status: string;
  image: string;
};

export type CallbackRecord = {
  id: number;
  token: string;
  source_ip: string | null;
  headers_json: string;
  body: string;
  created_at: string;
};

export type AppConfig = {
  cf_token: string | null;
  cf_domain: string | null;
};

export type TunnelInfo = {
  local_port: number;
  server: string;
  container?: string;
  desired: boolean;
  running: boolean;
  remote_host: string | null;
  remote_port: number | null;
  restart_count: number;
  started_at: string;
  last_exit_code: number | null;
  last_error: string | null;
  last_logs: string[];
};

// Relative base — nginx proxies /api, /mcp, /callback, /healthz to backend.
// For `vite dev` outside Docker, set VITE_API_BASE=http://127.0.0.1:8000 in .env.local.
const API_BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  getHealth: () => request<{ status: string }>("/healthz"),

  getContainers: () => request<ContainerInfo[]>("/api/containers"),
  createContainer: (name: string, image?: string) =>
    request<ContainerInfo>("/api/containers", {
      method: "POST",
      body: JSON.stringify({ name, image })
    }),
  deleteContainer: (name: string) =>
    request<{ message: string }>(`/api/containers/${encodeURIComponent(name)}`, { method: "DELETE" }),
  activateContainer: (name: string) =>
    request<{ active_container: string }>(
      `/api/containers/${encodeURIComponent(name)}/activate`,
      { method: "PUT" }
    ),
  getActiveContainer: () => request<{ active_container: string | null }>("/api/containers/active"),

  getCallbacks: () => request<CallbackRecord[]>("/api/callbacks"),
  clearCallbacks: () => request<{ message: string }>("/api/callbacks", { method: "DELETE" }),

  getConfig: () => request<AppConfig>("/api/config"),
  saveConfig: (config: Partial<AppConfig>) =>
    request<{ message: string }>("/api/config", {
      method: "PUT",
      body: JSON.stringify(config)
    }),

  getTunnels: () => request<{ tunnels: TunnelInfo[] }>("/api/tunnels")
};
