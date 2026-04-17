import { ActiveBadge } from "./ActiveBadge";
import type { ContainerInfo } from "../api/client";

type Props = {
  item: ContainerInfo;
  isActive: boolean;
  onActivate: (name: string) => void;
  onDelete: (name: string) => void;
};

export function ContainerCard({ item, isActive, onActivate, onDelete }: Props) {
  return (
    <article className="card">
      <div className="card-head">
        <h3>{item.name}</h3>
        <ActiveBadge active={isActive} />
      </div>
      <p>Status: {item.status}</p>
      <p>Image: {item.image}</p>
      <div className="row">
        <button onClick={() => onActivate(item.name)} disabled={isActive}>
          Set Active
        </button>
        <button className="danger" onClick={() => onDelete(item.name)}>
          Delete
        </button>
      </div>
    </article>
  );
}
