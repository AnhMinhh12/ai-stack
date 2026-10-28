const Chart = require("/home/admin/ai-stack/ui-patches/chart.umd.min.js");

const item = {
  labels: ["Khuôn/Die V1", "Khuôn/Die V2"],
  values: [13920, 940],
  label: "Số lượng tồn",
  unit: "PCS",
  x_label: "Khuôn / Die"
};
const chartColors = ['#2563eb','#0d9488','#f59e0b','#dc2626','#7c3aed','#db2777','#65a30d','#0891b2'];
const formatNumber = val => new Intl.NumberFormat('vi-VN').format(val);

function buildChartConfig(kind, isDark) {
  const isPie = kind === 'pie';
  const textColor = isDark ? '#f1f5f9' : '#1e293b';
  const subColor = isDark ? '#94a3b8' : '#64748b';
  const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';

  let dataset;
  if (kind === 'pie') {
    dataset = {
      data: item.values,
      backgroundColor: chartColors,
      borderWidth: 2,
      borderColor: isDark ? '#0f172a' : '#ffffff'
    };
  } else if (kind === 'line') {
    dataset = {
      label: item.label,
      data: item.values,
      borderColor: '#2563eb',
      backgroundColor: 'rgba(37,99,235,0.12)',
      borderWidth: 2.5,
      tension: 0.3,
      fill: true,
      pointRadius: 6,
      pointBackgroundColor: '#2563eb',
      pointBorderColor: '#ffffff',
      pointBorderWidth: 2
    };
  } else {
    dataset = {
      label: item.label,
      data: item.values,
      backgroundColor: chartColors.slice(0, item.values.length),
      borderRadius: 6,
      borderWidth: 0
    };
  }

  const scales = isPie ? {} : {
    x: {
      grid: { display: false },
      ticks: { color: subColor, font: { size: 11 } }
    },
    y: {
      beginAtZero: true,
      grid: { color: gridColor },
      ticks: { color: subColor, font: { size: 11 }, callback: (v) => formatNumber(v) }
    }
  };

  const legend = isPie ? {
    display: true,
    position: 'bottom',
    labels: {
      color: textColor,
      font: { size: 12 },
      padding: 14,
      generateLabels(chart) {
        const total = item.values.reduce((sum, v) => sum + v, 0);
        return item.labels.map((lbl, i) => ({
          text: `${lbl}: ${formatNumber(item.values[i])} ${item.unit} (${total ? ((item.values[i]/total)*100).toFixed(1) : 0}%)`,
          fillStyle: chartColors[i % chartColors.length],
          strokeStyle: isDark ? '#0f172a' : '#ffffff',
          lineWidth: 1,
          hidden: false,
          index: i
        }));
      }
    }
  } : {
    display: false
  };

  return {
    type: kind,
    data: { labels: item.labels, datasets: [dataset] },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: legend,
        tooltip: { enabled: true }
      },
      scales: scales
    }
  };
}

for (const kind of ['pie', 'bar', 'line']) {
  const cfg = buildChartConfig(kind, false);
  console.log(`Config for ${kind} created successfully. Dataset count: ${cfg.data.datasets.length}`);
}
