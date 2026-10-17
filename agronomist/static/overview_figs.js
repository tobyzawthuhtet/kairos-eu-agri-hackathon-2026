"use strict";
(async function () {
  const D = await (await fetch("/api/overview")).json();
  const cfg = {responsive: true, displaylogo: false};
  const NAMES = D.stage_labels, ORDER = D.stage_order;
  const colors = ["#6c8fc4", "#46662f", "#7f9a52", "#e0b43a", "#d9a441", "#c9712e", "#9a3a2a", "#6e5a8a", "#8aa0a8"];
  // 1. crop calendar (Gantt on a 2025 axis; wrap-around stages split in two bars)
  const bars = [];
  ORDER.forEach((st, i) => {
    const [a, b] = D.stages[st], y = NAMES[st] || st;
    const seg = (s, e) => ({type: "bar", orientation: "h", y: [y], base: [`2025-${s}`], x: [new Date(`2025-${e}`) - new Date(`2025-${s}`) + 864e5], marker: {color: colors[i % colors.length]}, hovertemplate: `${y}: ${s} to ${e}<extra></extra>`, showlegend: false});
    if (a <= b) bars.push(seg(a, b)); else { bars.push(seg(a, "12-31")); bars.push(seg("01-01", b)); }
  });
  Plotly.newPlot("fig-cal", bars, {barmode: "overlay", margin: {l: 200, r: 15, t: 10, b: 35}, xaxis: {type: "date", range: ["2025-01-01", "2025-12-31"], tickformat: "%b"}, yaxis: {autorange: "reversed", categoryorder: "array", categoryarray: ORDER.map(k => NAMES[k] || k)}, paper_bgcolor: "#fff", plot_bgcolor: "#fff"}, cfg);
  // 2. scenario x month heatmap, click opens the scenario
  const rows = D.rules.map((r, i) => ({...r, m: D.months[i], total: D.months[i].reduce((a, b) => a + b, 0), si: ORDER.indexOf(r.stage)}))
    .sort((a, b) => a.si - b.si || a.hazard.localeCompare(b.hazard) || a.id.localeCompare(b.id));
  const labels = rows.map(r => `${r.id}${r.validated ? " ✔" : ""}`);
  Plotly.newPlot("fig-map", [{z: rows.map(r => r.m.map(v => Math.log10(1 + v))), customdata: rows.map(r => r.m), x: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], y: labels, type: "heatmap",
    colorscale: [[0, "#f5f4ec"], [0.001, "#f6e6b0"], [1, "#9a3a2a"]], showscale: false, xgap: 2, ygap: 2,
    text: rows.map(r => r.m.map(() => `${(D.sentences[r.id] || "").slice(0, 110)}…`)), hovertemplate: "%{y}<br>%{x}: %{customdata} province-days<br>%{text}<extra></extra>"}],
    {margin: {l: 190, r: 15, t: 10, b: 35}, yaxis: {autorange: "reversed", tickfont: {size: 11}}, xaxis: {side: "top"}, paper_bgcolor: "#fff", plot_bgcolor: "#fff"}, cfg)
    .then(g => g.on("plotly_click", e => { const id = rows[e.points[0].pointIndex[0]].id; location.href = `/scenario/${id}`; }));
  // 3. review progress by stage
  const stages = ORDER.map(k => NAMES[k] || k).filter(n => n in D.progress), keys = [["approved", "Approved", "#46662f"], ["modified", "With changes", "#7f9a52"], ["rejected", "Rejected", "#9a3a2a"], ["unsure", "Field check", "#e0b43a"], ["none", "Not reviewed", "#e9ebd9"]];
  Plotly.newPlot("fig-prog", keys.map(([k, l, c]) => ({type: "bar", orientation: "h", y: stages, x: stages.map(s => D.progress[s][k]), name: l, marker: {color: c}, hovertemplate: `%{y}: %{x} ${l.toLowerCase()}<extra></extra>`})),
    {barmode: "stack", margin: {l: 190, r: 10, t: 10, b: 40}, yaxis: {autorange: "reversed"}, legend: {orientation: "h", y: -0.2}, paper_bgcolor: "#fff", plot_bgcolor: "#fff"}, cfg);
  // 4. lists
  const never = rows.filter(r => r.total === 0), top = rows.slice().sort((a, b) => b.total - a.total).slice(0, 6);
  const link = r => `<a href="/scenario/${r.id}">${r.id}</a>`;
  document.getElementById("lists").innerHTML = `<p><b>Never fired in 2025 (${never.length})</b><br>${never.map(link).join(", ") || "none"}<br><span class="xs sub">May be too strict, or simply not triggered by the 2025 weather.</span></p>
    <p><b>Fired most</b><br>${top.map(r => `${link(r)} (${r.total} province-days)`).join("<br>")}<br><span class="xs sub">Check these are not too sensitive.</span></p>`;
})();
