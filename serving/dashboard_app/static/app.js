const { createApp, nextTick } = Vue;

function compactCurrency(value) {
  const amount = Number(value || 0);
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(amount) + " VND";
}

function fullNumber(value) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

function percent(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

const app = createApp({
  data() {
    return {
      loading: true,
      kpis: {},
      dailySales: [],
      salesByChannel: [],
      topProducts: [],
      inventoryAlerts: [],
      logistics: [],
      customers: [],
      charts: {},
    };
  },
  mounted() {
    this.loadDashboard();
    window.addEventListener("resize", this.resizeCharts);
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.resizeCharts);
  },
  methods: {
    formatCurrency: compactCurrency,
    formatNumber: fullNumber,
    formatPercent: percent,
    async loadDashboard() {
      this.loading = true;
      const response = await fetch("/api/dashboard");
      const payload = await response.json();

      this.kpis = payload.kpis || {};
      this.dailySales = payload.daily_sales || [];
      this.salesByChannel = payload.sales_by_channel || [];
      this.topProducts = payload.top_products || [];
      this.inventoryAlerts = payload.inventory_alerts || [];
      this.logistics = payload.logistics || [];
      this.customers = payload.customers || [];

      await nextTick();
      this.renderCharts();
      this.loading = false;
    },
    chart(id) {
      if (!this.charts[id]) {
        this.charts[id] = echarts.init(document.getElementById(id));
      }
      return this.charts[id];
    },
    resizeCharts() {
      Object.values(this.charts).forEach((chart) => chart.resize());
    },
    renderCharts() {
      this.chart("dailyRevenueChart").setOption({
        color: ["#2563eb", "#0f9f8f"],
        tooltip: { trigger: "axis" },
        legend: { top: 0 },
        grid: { left: 52, right: 24, top: 42, bottom: 40 },
        xAxis: {
          type: "category",
          data: this.dailySales.map((row) => row.date_key),
          axisLabel: { color: "#69748a" },
        },
        yAxis: [
          {
            type: "value",
            axisLabel: { color: "#69748a", formatter: (value) => compactCurrency(value).replace(" VND", "") },
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
            data: this.dailySales.map((row) => row.net_revenue),
          },
          {
            name: "Orders",
            type: "bar",
            yAxisIndex: 1,
            barMaxWidth: 26,
            data: this.dailySales.map((row) => row.orders),
          },
        ],
      });

      this.chart("channelChart").setOption({
        color: ["#2563eb", "#0f9f8f", "#c47a13", "#7c3aed"],
        tooltip: { trigger: "item", formatter: "{b}<br/>{c} VND ({d}%)" },
        series: [
          {
            name: "Revenue",
            type: "pie",
            radius: ["48%", "76%"],
            data: this.salesByChannel.map((row) => ({
              name: row.channel_code,
              value: row.net_revenue,
            })),
            label: { formatter: "{b}" },
          },
        ],
      });

      this.chart("productChart").setOption({
        color: ["#0f9f8f"],
        tooltip: { trigger: "axis" },
        grid: { left: 104, right: 18, top: 18, bottom: 28 },
        xAxis: {
          type: "value",
          axisLabel: { color: "#69748a", formatter: (value) => compactCurrency(value).replace(" VND", "") },
        },
        yAxis: {
          type: "category",
          data: this.topProducts.map((row) => row.sku).reverse(),
          axisLabel: { color: "#69748a" },
        },
        series: [
          {
            name: "Revenue",
            type: "bar",
            barMaxWidth: 20,
            data: this.topProducts.map((row) => row.net_revenue).reverse(),
          },
        ],
      });
    },
  },
});

app.mount("#app");
