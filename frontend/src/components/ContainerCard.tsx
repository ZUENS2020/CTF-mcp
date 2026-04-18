import type { ContainerInfo } from "../api/client";
import { StatusBadge } from "./StatusBadge";

type Props = {
  item: ContainerInfo;
  onDelete: (name: string) => void;
};

export function ContainerCard({ item, onDelete }: Props) {
  return (
    <article className="card">
      <div className="card-head">
        <h3>{item.name}</h3>
        <StatusBadge status={item.status} />
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
        <button className="danger ghost" onClick={() => onDelete(item.name)}>
          Delete
        </button>
      </div>
    </article>
  );
}
