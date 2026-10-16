import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import Farms from "./pages/Farms";
import Alerts from "./pages/Alerts";
import Advisory from "./pages/Advisory";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <nav style={{ display: "flex", gap: 16, padding: 16 }}>
        <Link to="/">Farms</Link><Link to="/alerts">Alerts</Link><Link to="/advisory">Advisory</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Farms />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/advisory" element={<Advisory />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
