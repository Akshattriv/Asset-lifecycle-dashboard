import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Async, Card, KpiCard, PALETTE } from "../components/Ui.jsx";
import { fmt, useApi } from "../api.js";

const STATUS_FILTERS = [
  ["", "All"], ["expired", "Expired"], ["expiring_30", "≤ 30 days"], ["expiring_60", "≤ 60 days"],
  ["expiring_90", "≤ 90 days"], ["active", "Active (> 90 days)"],
];

function DeviceTable() {
  const [status, setStatus] = useState("expiring_90");
  const [layout, setLayout] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const qs = new URLSearchParams({ page, page_size: 10, ...(status && { status }), ...(layout && { layout }), ...(search && { search }) });
  const state = useApi(`/api/devices?${qs}`);

  const reset = (fn) => (e) => { fn(e.target.value); setPage(1); };

  return (
    <Card title="Devices by lease status">
      <div className="filters">
        <select value={status} onChange={reset(setStatus)}>
          {STATUS_FILTERS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <select value={layout} onChange={reset(setLayout)}>
          <option value="">All layouts</option>
          {["DE", "FR", "UK", "IT", "DK", "HU", "SE"].map((l) => <option key={l}>{l}</option>)}
        </select>
        <input placeholder="Search serial / asset tag" value={search} onChange={reset(setSearch)} />
      </div>
      <Async state={state}>
        {(d) => (
          <>
            <table>
              <thead>
                <tr><th>Serial</th><th>Asset tag</th><th>Vendor</th><th>Type</th><th>Layout</th><th>Lease end</th><th>Days left</th></tr>
              </thead>
              <tbody>
                {d.items.map((r) => (
                  <tr key={r.serial_number}>
                    <td>{r.serial_number}</td><td>{r.asset_tag}</td><td>{r.vendor}</td><td>{r.device_type}</td>
                    <td>{r.layout}</td><td>{r.lease_end}</td>
                    <td><span className={`pill pill-${r.lease_status}`}>{r.days_to_expiry < 0 ? "Expired" : `${r.days_to_expiry} d`}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <div className="pager">
              <span className="muted">{fmt(d.total)} devices</span>
              <button disabled={page <= 1} onClick={() => setPage(page - 1)}>Prev</button>
              <span>Page {page} / {Math.max(1, Math.ceil(d.total / d.page_size))}</span>
              <button disabled={page * d.page_size >= d.total} onClick={() => setPage(page + 1)}>Next</button>
            </div>
          </>
        )}
      </Async>
    </Card>
  );
}

export default function Overview() {
  const summary = useApi("/api/summary");
  const timeline = useApi("/api/lifecycle/timeline?months=12");
  const [days, setDays] = useState(90);
  const breakdown = useApi(`/api/lifecycle/breakdown?days=${days}`);

  return (
    <>
      <h2>Lease Lifecycle</h2>
      <Async state={summary}>
        {(s) => (
          <div className="kpi-row">
            <KpiCard label="Total deployed devices" value={s.total_devices} hint={`${s.hp_share_pct}% HP`} />
            <KpiCard label="Lease expired" value={s.expired} tone="danger" hint="Past 4-year tenure" />
            <KpiCard label="Expiring ≤ 30 days" value={s.expiring_30} tone="warn" />
            <KpiCard label="Expiring ≤ 60 days" value={s.expiring_60} tone="warn" />
            <KpiCard label="Expiring ≤ 90 days" value={s.expiring_90} tone="warn" />
          </div>
        )}
      </Async>

      <div className="grid-2">
        <Card title="Leases ending per month (next 12 months)">
          <Async state={timeline}>
            {(d) => (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={d}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Bar dataKey="count" name="Devices" fill="#2563eb" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Async>
        </Card>
        <Card title="Vendor mix">
          <Async state={summary}>
            {(s) => (
              <ResponsiveContainer width="100%" height={280}>
                <PieChart>
                  <Pie data={s.vendor_mix} dataKey="count" nameKey="vendor" innerRadius={55} outerRadius={95} paddingAngle={2}>
                    {s.vendor_mix.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                  </Pie>
                  <Tooltip /><Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Async>
        </Card>
      </div>

      <Card title="Expiring devices by layout and device type">
        <div className="filters">
          <label>Window:&nbsp;
            <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
              {[30, 60, 90, 180, 365].map((d) => <option key={d} value={d}>next {d} days</option>)}
            </select>
          </label>
        </div>
        <Async state={breakdown}>
          {(b) => (
            <div className="grid-2">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={b.by_layout}>
                  <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="layout" /><YAxis /><Tooltip />
                  <Bar dataKey="count" name="Devices" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={b.by_device_type} layout="vertical" margin={{ left: 50 }}>
                  <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" />
                  <YAxis type="category" dataKey="device_type" width={150} fontSize={12} /><Tooltip />
                  <Bar dataKey="count" name="Devices" fill="#7c3aed" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Async>
      </Card>

      <DeviceTable />
    </>
  );
}
