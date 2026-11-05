import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Async, Card, KpiCard } from "../components/Ui.jsx";
import { useApi } from "../api.js";

export default function Replenishment() {
  const state = useApi("/api/replenishment");
  return (
    <>
      <h2>HP Replenishment Orders</h2>
      <p className="muted">Devices ordered from HP to refill vendor-held stock.</p>
      <Async state={state}>
        {(d) => (
          <>
            <div className="kpi-row">
              <KpiCard label="Devices on order" value={d.total} hint="Vendor: HP" />
              {d.by_status.map((s) => (
                <KpiCard key={s.status} label={s.status} value={s.count} tone={s.status === "Delayed" ? "danger" : "default"} />
              ))}
            </div>
            <div className="grid-2">
              <Card title="On order by device type">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={d.by_device_type} layout="vertical" margin={{ left: 50 }}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis type="number" />
                    <YAxis type="category" dataKey="device_type" width={150} fontSize={12} /><Tooltip />
                    <Bar dataKey="count" name="Devices" fill="#2563eb" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
              <Card title="On order by layout">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={d.by_layout}>
                    <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="layout" /><YAxis /><Tooltip />
                    <Bar dataKey="count" name="Devices" fill="#16a34a" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>
            <Card title="Next deliveries (earliest first, top 200)">
              <div className="scroll">
                <table>
                  <thead><tr><th>PO</th><th>Serial</th><th>Model</th><th>Type</th><th>Layout</th><th>Ordered</th><th>ETA</th><th>Status</th></tr></thead>
                  <tbody>
                    {d.items.map((r) => (
                      <tr key={r.serial_number}>
                        <td>{r.po_number}</td><td>{r.serial_number}</td><td>{r.model}</td><td>{r.device_type}</td>
                        <td>{r.layout}</td><td>{r.order_date}</td><td>{r.expected_delivery}</td>
                        <td><span className={`pill pill-${r.status.replace(" ", "")}`}>{r.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        )}
      </Async>
    </>
  );
}
