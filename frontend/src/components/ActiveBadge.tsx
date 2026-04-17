export function ActiveBadge({ active }: { active: boolean }) {
  return <span className={active ? "badge badge-active" : "badge"}>{active ? "ACTIVE" : "IDLE"}</span>;
}
