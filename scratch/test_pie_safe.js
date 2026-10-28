const item = {
  labels: ["Khuôn/Die V1", "Khuôn/Die V2"],
  values: [13920, 940],
  unit: "PCS"
};
const chartColors = ['#2563eb','#0d9488','#f59e0b','#dc2626','#7c3aed','#db2777','#65a30d','#0891b2'];
const formatNumber = val => new Intl.NumberFormat('vi-VN').format(val);

function makePieLegend(chart) {
  const total = item.values.reduce((sum, v) => sum + v, 0);
  return item.labels.map((lbl, i) => ({
    text: `${lbl}: ${formatNumber(item.values[i])} ${item.unit} (${total ? ((item.values[i]/total)*100).toFixed(1) : 0}%)`,
    fillStyle: chartColors[i % chartColors.length],
    strokeStyle: '#ffffff',
    lineWidth: 1,
    hidden: false,
    index: i
  }));
}

console.log("Pie legend items:", makePieLegend());
