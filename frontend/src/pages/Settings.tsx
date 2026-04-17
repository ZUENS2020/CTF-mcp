import { FormEvent, useEffect, useState } from "react";

import { apiClient } from "../api/client";

export function SettingsPage() {
  const [cfToken, setCfToken] = useState("");
  const [cfDomain, setCfDomain] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

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
    try {
      await apiClient.saveConfig({
        cf_token: cfToken,
        cf_domain: cfDomain
      });
      setMessage("Saved");
    } catch (err: unknown) {
      setError(String(err));
    }
  }

  return (
    <section>
      <h2>Settings</h2>
      {error ? <p className="error">{error}</p> : null}
      {message ? <p>{message}</p> : null}
      <form className="card" onSubmit={onSubmit}>
        <label>
          Cloudflare Token
          <input value={cfToken} onChange={(e) => setCfToken(e.target.value)} />
        </label>
        <label>
          Callback Domain
          <input value={cfDomain} onChange={(e) => setCfDomain(e.target.value)} />
        </label>
        <button type="submit">Save</button>
      </form>
    </section>
  );
}
