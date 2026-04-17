import type { ContainerInfo } from "../api/client";
import { StatusBadge } from "./StatusBadge";

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
        {isActive ? <span className="badge badge-active">active</span> : <StatusBadge status={item.status} />}
      </div>
      <div className="meta-grid">
        <span className="k">id</span>
        <span className="v">{item.id}</span>
        <span className="k">status</span>
        <span className="v">{item.status}</span>
        <span className="k">image</span>
        <span className="v">{item.image}</span>
      </div>
      <div className="row">
        <button onClick={() => onActivate(item.name)} disabled={isActive}>
          {isActive ? "Active" : "Set Active"}
        </button>
        <button className="danger ghost" onClick={() => onDelete(item.name)}>
          Delete
        </button>
      </div>
    </article>
  );
}
