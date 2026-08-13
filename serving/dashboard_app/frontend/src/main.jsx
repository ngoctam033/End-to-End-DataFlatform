import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { ChartPanel } from "./components/ChartPanel";
import { DataTable } from "./components/DataTable";
import { KpiCard } from "./components/KpiCard";
import { Panel } from "./components/Panel";
import { StockTag } from "./components/StockTag";
import { chartCurrency, compactCurrency, fullNumber, percent } from "./utils/formatters";
import "./styles.css";

const emptyPayload = {
  kpis: {},
  daily_sales: [],
  sales_by_channel: [],
  top_products: [],
  inventory_alerts: [],
  logistics: [],
  customers: [],
};

function DashboardApp() {
  const [payload, setPayload] = useState(emptyPayload);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/dashboard");

      if (!response.ok) {
        throw new Error(`Dashboard API returned ${response.status}`);
      }

      const data = await response.json();
      setPayload({ ...emptyPayload, ...data });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const dailyRevenueOption = useMemo(
    () => ({
      color: ["#2563eb", "#0f9f8f"],
      tooltip: { trigger: "axis" },
      legend: { top: 0 },
      grid: { left: 52, right: 24, top: 42, bottom: 40 },
      xAxis: {
        type: "category",
        data: payload.daily_sales.map((row) => row.date_key),
        axisLabel: { color: "#69748a" },
      },
      yAxis: [
        {
          type: "value",
          axisLabel: { color: "#69748a", formatter: chartCurrency },
        },
        {
          type: "value",
          axisLabel: { color: "#69748a" },
        },
      ],
      series: [
        {
          name: "Net Revenue",
          type: "line",
          smooth: true,
          areaStyle: { opacity: 0.14 },
          data: payload.daily_sales.map((row) => row.net_revenue),
        },
        {
          name: "Orders",
          type: "bar",
          yAxisIndex: 1,
          barMaxWidth: 26,
          data: payload.daily_sales.map((row) => row.orders),
        },
      ],
    }),
    [payload.daily_sales],
  );

  const channelOption = useMemo(
    () => ({
      color: ["#2563eb", "#0f9f8f", "#c47a13", "#7c3aed"],
      tooltip: { trigger: "item", formatter: "{b}<br/>{c} VND ({d}%)" },
      series: [
        {
          name: "Revenue",
          type: "pie",
          radius: ["48%", "76%"],
          data: payload.sales_by_channel.map((row) => ({
            name: row.channel_code,
            value: row.net_revenue,
          })),
          label: { formatter: "{b}" },
        },
      ],
    }),
    [payload.sales_by_channel],
  );

  const productOption = useMemo(
    () => ({
      color: ["#0f9f8f"],
      tooltip: { trigger: "axis" },
      grid: { left: 104, right: 18, top: 18, bottom: 28 },
      xAxis: {
        type: "value",
        axisLabel: { color: "#69748a", formatter: chartCurrency },
      },
      yAxis: {
        type: "category",
        data: payload.top_products.map((row) => row.sku).reverse(),
        axisLabel: { color: "#69748a" },
      },
      series: [
        {
          name: "Revenue",
          type: "bar",
          barMaxWidth: 20,
          data: payload.top_products.map((row) => row.net_revenue).reverse(),
        },
      ],
    }),
    [payload.top_products],
  );

  return (
    <div className="dashboard-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Omnichannel D2C FMCG</p>
          <h1>ERP Data Platform Dashboard</h1>
        </div>
        <div className="topbar-actions">
          <span className={loading ? "status-pill loading" : "status-pill"}>
            {loading ? "Refreshing" : "Live Analytics"}
          </span>
          <button onClick={loadDashboard} disabled={loading}>
            Refresh
          </button>
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <main>
        <section className="kpi-grid">
          <KpiCard label="Total Orders" value={fullNumber(payload.kpis.total_orders)} />
          <KpiCard label="Net Revenue" value={compactCurrency(payload.kpis.net_revenue)} />
          <KpiCard label="Gross Margin" value={compactCurrency(payload.kpis.gross_margin)} />
          <KpiCard label="Margin Rate" value={percent(payload.kpis.gross_margin_rate)} />
          <KpiCard label="Units Sold" value={fullNumber(payload.kpis.units_sold)} />
        </section>

        <section className="visual-grid">
          <ChartPanel
            title="Daily Revenue Trend"
            meta={`${payload.daily_sales.length} days`}
            wide
            option={dailyRevenueOption}
          />
          <ChartPanel title="Revenue by Channel" meta="Omnichannel" option={channelOption} />
          <ChartPanel title="Top Products" meta="Revenue" option={productOption} />
        </section>

        <section className="table-grid">
          <Panel title="Inventory Health" meta="FMCG stock risk">
            <DataTable
              rows={payload.inventory_alerts}
              rowKey={(row) => `${row.warehouse_code}-${row.sku}`}
              columns={[
                { key: "warehouse_code", label: "Warehouse" },
                { key: "sku", label: "SKU" },
                { key: "available_qty", label: "Available", render: (row) => fullNumber(row.available_qty) },
                { key: "days_of_inventory", label: "DOI", render: (row) => row.days_of_inventory ?? "N/A" },
                { key: "stock_status", label: "Status", render: (row) => <StockTag value={row.stock_status} /> },
              ]}
            />
          </Panel>

          <Panel title="Logistics Performance" meta="Carrier SLA">
            <DataTable
              rows={payload.logistics}
              rowKey={(row) => row.carrier_code}
              columns={[
                { key: "carrier_code", label: "Carrier" },
                { key: "shipments", label: "Shipments", render: (row) => fullNumber(row.shipments) },
                { key: "avg_delivery_lead_days", label: "Lead Days" },
                { key: "on_time_delivery_rate", label: "OTD", render: (row) => percent(row.on_time_delivery_rate) },
              ]}
            />
          </Panel>

          <Panel title="Customer RFM" meta="Retention">
            <DataTable
              rows={payload.customers}
              rowKey={(row) => row.customer_code}
              columns={[
                { key: "customer_name", label: "Customer" },
                { key: "segment_name", label: "Segment" },
                { key: "frequency_orders", label: "Orders" },
                { key: "monetary_value", label: "Value", render: (row) => compactCurrency(row.monetary_value) },
                { key: "customer_status", label: "Status", render: (row) => <span className="tag">{row.customer_status}</span> },
              ]}
            />
          </Panel>
        </section>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<DashboardApp />);
