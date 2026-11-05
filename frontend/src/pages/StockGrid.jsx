import { useState } from "react";
import { Async, Card, KpiCard } from "../components/Ui.jsx";
import { fmt, useApi } from "../api.js";

const LABEL = { in_stock: "In stock", low_stock: "Low stock", out_of_stock: "Out of stock" };

export default function StockGrid() {
  const [threshold, setThreshold] = useState(25);
  const state = useApi(`/api/stock/grid?low_threshold=${threshold}`);

  return (
    <>
      <h2>Stock Availability Grid</h2>
      <p className="muted">HP vendor stock per layout (columns) and device type (rows).</p>
      <div className="filters">
        <label>Low-stock threshold (≤ devices):&nbsp;
          <input type="number" min="1" max="500" value={threshold} onChange={(e) => setThreshold(Math.max(1, Number(e.target.value) || 1))} />
        </label>
      </div>
      <Async state={state}>
        {(d) => {
          const lookup = Object.fromEntries(d.cells.map((c) => [`${c.device_type}|${c.layout}`, c]));
          return (
            <>
              <div className="kpi-row">
                <KpiCard label="In stock" value={d.summary.in_stock} tone="ok" hint="combinations" />
                <KpiCard label="Low stock" value={d.summary.low_stock} tone="warn" hint={`≤ ${d.low_threshold} devices`} />
                <KpiCard label="Out of stock" value={d.summary.out_of_stock} tone="danger" hint="0 devices" />
              </div>
              <Card>
                <div className="scroll">
                  <table className="stock-grid">
                    <thead>
                      <tr><th></th>{d.layouts.map((l) => <th key={l}>{l}</th>)}</tr>
                    </thead>
                    <tbody>
                      {d.device_types.map((t) => (
                        <tr key={t}>
                          <th className="row-head">{t}</th>
                          {d.layouts.map((l) => {
                            const c = lookup[`${t}|${l}`];
                            return (
                              <td key={l} className={`cell cell-${c.status}`} title={`${t} / ${l}: ${fmt(c.count)} in stock, ${c.on_order} on order`}>
                                <strong>{LABEL[c.status]}</strong>
                                <span>{fmt(c.count)} units{c.on_order > 0 && ` · ${c.on_order} on order`}</span>
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </>
          );
        }}
      </Async>
    </>
  );
}
