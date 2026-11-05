import { NavLink, Route, Routes } from "react-router-dom";
import Overview from "./pages/Overview.jsx";
import Replenishment from "./pages/Replenishment.jsx";
import StockAging from "./pages/StockAging.jsx";
import StockGrid from "./pages/StockGrid.jsx";

const NAV = [
  { to: "/", label: "Lease Lifecycle" },
  { to: "/replenishment", label: "Replenishment (HP)" },
  { to: "/aging", label: "HP Stock Aging" },
  { to: "/grid", label: "Stock Availability Grid" },
];

export default function App() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <h1>Asset Lifecycle</h1>
        <p className="muted">4-year lease tracking</p>
        <nav>
          {NAV.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.to === "/"} className={({ isActive }) => (isActive ? "active" : "")}>
              {n.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/replenishment" element={<Replenishment />} />
          <Route path="/aging" element={<StockAging />} />
          <Route path="/grid" element={<StockGrid />} />
        </Routes>
      </main>
    </div>
  );
}
