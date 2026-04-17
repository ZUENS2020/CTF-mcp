type Props = { status: string };

export function StatusBadge({ status }: Props) {
  const norm = status.toLowerCase();
  const cls =
    norm === "running"
      ? "badge-running"
      : norm === "exited" || norm === "dead" || norm === "stopped"
      ? "badge-exited"
      : norm === "created" || norm === "paused" || norm === "restarting"
      ? "badge-created"
      : "";
  return <span className={`badge ${cls}`}>{status}</span>;
}
