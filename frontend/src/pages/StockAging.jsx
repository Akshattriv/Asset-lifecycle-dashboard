import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Async, Card, KpiCard, PALETTE } from "../components/Ui.jsx";
import { fmt, useApi } from "../api.js";

const BANDS = ["0-30 days", "31-90 days", "91-365 days", "1-2 years", "> 2 years"];
const TONES = ["default", "warn", "warn", "danger"];

export default function StockAging() {
  const state = useApi("/api/stock/aging");
  return (
    <>
      <h2>HP Stock Aging</h2>
      <p className="muted">How long devices have been sitting in HP's vendor stock since receipt.</p>
      <Async state={state}>
        {(d) => (
          <>
            <div className="kpi-row">
              <KpiCard label="Total HP stock" value={d.total} />
              {d.thresholds.map((t, i) => (
                <KpiCard key={t.label} label={`Older than ${t.label.replace("> ", "")}`} value={t.count} hint={`${t.pct}% of stock`} tone={TONES[i]} />
              ))}
            </div>
            <div className="grid-2">
              <Card title="Stock by age band">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={d.bands}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="band" fontSize={12} /><YAxis /><Tooltip />
                    <Bar dataKey="count" name="Devices" fill="#0891b2" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
              <Card title="Age bands by device type">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={d.by_device_type} layout="vertical" margin={{ left: 50 }}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" />
                    <YAxis type="category" dataKey="device_type" width={150} fontSize={11} /><Tooltip /><Legend />
                    {BANDS.map((b, i) => <Bar key={b} dataKey={b} stackId="a" fill={PALETTE[i]} />)}
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>
            <Card title="Oldest devices in stock">
              <table>
                <thead><tr><th>Serial</th><th>Model</th><th>Type</th><th>Layout</th><th>Received</th><th>Age (days)</th></tr></thead>
                <tbody>
                  {d.oldest.map((r) => (
                    <tr key={r.serial_number}>
                      <td>{r.serial_number}</td><td>{r.model}</td><td>{r.device_type}</td><td>{r.layout}</td>
                      <td>{r.received_date}</td><td>{fmt(r.age_days)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Card>
          </>
        )}
      </Async>
    </>
  );
}
