const Chart = require("/home/admin/ai-stack/ui-patches/chart.umd.min.js");
const defaults = Chart.defaults.plugins.legend.labels;
const mockChart = {
  data: {
    datasets: [{
      data: [13920, 940],
      label: "Số lượng tồn",
      backgroundColor: "#2563eb",
      borderColor: "#1d4ed8"
    }],
    labels: ["V1", "V2"]
  },
  options: {
    plugins: {
      legend: {
        labels: {
          boxWidth: 40,
          padding: 10
        }
      }
    }
  },
  getDatasetMeta(i) {
    return { controller: {}, data: [] };
  }
};

try {
  const res = defaults.generateLabels.call({ options: mockChart.options.plugins.legend }, mockChart);
  console.log("Success with .call({options}):", res);
} catch (e) {
  console.error("Failed:", e);
}
