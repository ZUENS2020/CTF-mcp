import { FormEvent, useEffect, useState } from "react";

import { apiClient } from "../api/client";

export function SettingsPage() {
  const [cfToken, setCfToken] = useState("");
  const [cfDomain, setCfDomain] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiClient
      .getConfig()
      .then((cfg) => {
        setCfToken(cfg.cf_token ?? "");
        setCfDomain(cfg.cf_domain ?? "");
      })
      .catch((err: unknown) => setError(String(err)));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setSaving(true);
    try {
      await apiClient.saveConfig({
        cf_token: cfToken || null,
        cf_domain: cfDomain || null
      });
      setMessage("Configuration saved.");
    } catch (err: unknown) {
      setError(String(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section>
      <div className="page-head">
        <div>
          <h2>Settings</h2>
          <div className="subtitle">Cloudflare Tunnel credentials for HTTP callbacks.</div>
        </div>
      </div>

      {error ? <div className="error">{error}</div> : null}
      {message ? <div className="success">{message}</div> : null}

      <form className="card" onSubmit={onSubmit} style={{ maxWidth: 640 }}>
        <label>
          Cloudflare Token
          <input
            value={cfToken}
            onChange={(e) => setCfToken(e.target.value)}
            placeholder="cfd_xxx..."
            autoComplete="off"
          />
        </label>
        <label>
          Callback Domain
          <input
            value={cfDomain}
            onChange={(e) => setCfDomain(e.target.value)}
            placeholder="cb.example.com"
            autoComplete="off"
          />
        </label>
        <div className="row">
          <button type="submit" disabled={saving}>
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </form>
    </section>
  );
}
