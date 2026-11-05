import { fmt } from "../api.js";

export function KpiCard({ label, value, hint, tone = "default" }) {
  return (
    <div className={`kpi kpi-${tone}`}>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{typeof value === "number" ? fmt(value) : value}</div>
      {hint && <div className="kpi-hint">{hint}</div>}
    </div>
  );
}

export function Card({ title, children, className = "" }) {
  return (
    <section className={`card ${className}`}>
      {title && <h3>{title}</h3>}
      {children}
    </section>
  );
}

export function Async({ state, children }) {
  if (state.loading) return <p className="muted">Loading…</p>;
  if (state.error) return <p className="error">Could not load data: {state.error}. Is the FastAPI server running on port 8000?</p>;
  return children(state.data);
}

export const PALETTE = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2", "#db2777"];
