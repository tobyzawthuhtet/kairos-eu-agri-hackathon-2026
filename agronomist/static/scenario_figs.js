"use strict";
(async function () {
  const root = document.getElementById("figs");
  const sid = root.dataset.sid, op = root.dataset.op, lit = root.dataset.lit;
  const resp = await fetch(`/api/scenario/${sid}/series`);
  if (!resp.ok) { root.style.display = "none"; return; }
  const D = await resp.json();
  const between = D.operator === "between";
  const N = D.dates.length, P = D.provinces;
  const GREEN = "#2f4a1f", RED = "#9a3a2a";
  const cfg = {responsive: true, displaylogo: false, modeBarButtonsToRemove: ["select2d", "lasso2d"]};
  const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const month = D.dates.map(d => +d.slice(5, 7) - 1);
  // eligible[p][i]: crop stage active and any extra conditions (e.g. temperature band) hold
  const elig = P.map(p => D.stage_active.map((a, i) => a === 1 && p.v[i] != null && p.w.every(m => m[i] === 1)));
  const all = [];
  P.forEach((p, k) => p.v.forEach((v, i) => { if (elig[k][i]) all.push(v); }));
  all.sort((a, b) => a - b);
  const vmin = all.length ? all[0] : 0, vmax = all.length ? all[all.length - 1] : 1;
  const rng = (vmax - vmin) || 1;
  const parse = s => between ? String(s).split(/\s*-\s*(?=-?\d)/).map(Number) : [Number(s)];
  const cmp = (v, t) => between ? (v >= t[0] && v <= t[1]) : ({"<": v < t[0], "<=": v <= t[0], ">": v > t[0], ">=": v >= t[0]})[D.operator];
  const litT = parse(lit).every(x => !isNaN(x)) ? parse(lit) : (between ? D.threshold : [D.threshold]);
  let T = between ? D.threshold.slice() : [D.threshold];
  const i1 = document.getElementById("thr1"), i2 = document.getElementById("thr2"), rg = document.getElementById("thrrange");
  document.getElementById("thrlabel").textContent = `${D.feature_label} ${between ? "between" : D.operator} (${D.unit})`;
  if (between) { i2.style.display = ""; }
  const step = rng > 50 ? 1 : rng > 10 ? 0.5 : 0.1;
  rg.min = vmin - rng * .05; rg.max = vmax + rng * .05; rg.step = step; i1.step = step; i2.step = step;

  function fires(t) { // matrix [province][month] and total
    const m = P.map(() => Array(12).fill(0)); let tot = 0, provs = new Set(); const pts = {x: [], y: [], t: []};
    P.forEach((p, k) => p.v.forEach((v, i) => { if (elig[k][i] && cmp(v, t)) { m[k][month[i]]++; tot++; provs.add(k); pts.x.push(D.dates[i]); pts.y.push(v); pts.t.push(p.name); } }));
    return {m, tot, provs: provs.size, pts};
  }
  const base = fires(litT);
  const segs = []; // stage window shading
  let start = null;
  D.stage_active.forEach((a, i) => { if (a && start === null) start = i; if ((!a || i === N - 1) && start !== null) { segs.push([start, a && i === N - 1 ? i : i - 1]); start = null; } });
  const shapes = t => [
    ...segs.map(s => ({type: "rect", xref: "x", yref: "paper", x0: D.dates[s[0]], x1: D.dates[s[1]], y0: 0, y1: 1, fillcolor: "rgba(70,102,47,.10)", line: {width: 0}, layer: "below"})),
    ...t.map(v => ({type: "line", xref: "paper", x0: 0, x1: 1, yref: "y", y0: v, y1: v, line: {color: RED, width: 2, dash: "dash"}}))];

  function draw() {
    const f = fires(T);
    const traces = P.map(p => ({x: D.dates, y: p.v, type: "scatter", mode: "lines", line: {color: "rgba(120,135,95,.55)", width: 1}, name: p.name, hovertemplate: `${p.name}: %{y:.1f} ${D.unit}<extra></extra>`}));
    const med = D.dates.map((_, i) => { const a = P.map(p => p.v[i]).filter(v => v != null).sort((x, y) => x - y); return a.length ? a[Math.floor(a.length / 2)] : null; });
    traces.push({x: D.dates, y: med, type: "scatter", mode: "lines", line: {color: GREEN, width: 3}, name: "Median of provinces", hovertemplate: `Median: %{y:.1f} ${D.unit}<extra></extra>`});
    traces.push({x: f.pts.x, y: f.pts.y, text: f.pts.t, type: "scatter", mode: "markers", marker: {color: RED, size: 6}, name: "Would warn", hovertemplate: `%{text}: %{y:.1f} ${D.unit}<extra>would warn</extra>`});
    if (D.raif.length) traces.push({x: D.raif.map(r => r.date), y: D.raif.map(r => r.value), text: D.raif.map(r => r.province), type: "scatter", mode: "markers", yaxis: "y2", marker: {color: "#1b3f8f", symbol: "diamond", size: 10}, name: D.raif_label, hovertemplate: `%{text}: %{y}%<extra>RAIF report</extra>`});
    Plotly.react("fig-season", traces, {margin: {l: 55, r: D.raif.length ? 55 : 15, t: 28, b: 40}, title: {text: `${D.feature_label} through 2025 (green shading = crop stage when this scenario applies)`, font: {size: 14}},
      yaxis: {title: D.unit}, yaxis2: {overlaying: "y", side: "right", title: "RAIF %", showgrid: false}, shapes: shapes(between ? T : T), showlegend: false, hovermode: "closest", paper_bgcolor: "#fff", plot_bgcolor: "#fff"}, cfg);
    // sensitivity curve (single threshold) or distribution (band)
    if (!between) {
      const xs = Array.from({length: 120}, (_, k) => vmin - rng * .02 + (rng * 1.04) * k / 119);
      const cnt = t => all.filter(v => cmp(v, [t])).length;
      const ys = xs.map(cnt);
      Plotly.react("fig-sens", [{x: xs, y: ys, type: "scatter", mode: "lines", line: {color: GREEN, width: 3}, fill: "tozeroy", fillcolor: "rgba(70,102,47,.12)", name: "Province-days that would warn", hovertemplate: `threshold %{x:.1f} ${D.unit}: %{y} province-days<extra></extra>`},
        {x: [T[0]], y: [cnt(T[0])], type: "scatter", mode: "markers", marker: {color: RED, size: 13}, name: "Your value", hovertemplate: "your value<extra></extra>"},
        {x: [litT[0]], y: [cnt(litT[0])], type: "scatter", mode: "markers", marker: {color: "#555", size: 11, symbol: "diamond"}, name: "Source value", hovertemplate: "source value<extra></extra>"}],
        {margin: {l: 55, r: 15, t: 28, b: 45}, title: {text: "How many warnings at each threshold? (click to set)", font: {size: 14}}, xaxis: {title: `threshold (${D.unit})`}, yaxis: {title: "province-days that would warn"}, showlegend: true, legend: {orientation: "h", y: -0.28}, paper_bgcolor: "#fff", plot_bgcolor: "#fff"}, cfg)
        .then(g => { g.removeAllListeners && g.removeAllListeners("plotly_click"); g.on("plotly_click", e => { if (e.points[0].curveNumber === 0) setT([Math.round(e.points[0].x / step) * step]); }); });
    } else {
      Plotly.react("fig-sens", [{x: all, type: "histogram", nbinsx: 40, marker: {color: "rgba(70,102,47,.6)"}, name: "Eligible days", hovertemplate: `%{x} ${D.unit}: %{y} province-days<extra></extra>`}],
        {margin: {l: 55, r: 15, t: 28, b: 45}, title: {text: "Distribution of values while the scenario applies", font: {size: 14}}, xaxis: {title: D.unit}, yaxis: {title: "province-days"},
          shapes: [{type: "rect", xref: "x", yref: "paper", x0: T[0], x1: T[1], y0: 0, y1: 1, fillcolor: "rgba(154,58,42,.18)", line: {color: RED, width: 2}}], paper_bgcolor: "#fff", plot_bgcolor: "#fff"}, cfg);
    }
    Plotly.react("fig-heat", [{z: f.m, x: MONTHS, y: P.map(p => p.name), type: "heatmap", colorscale: [[0, "#f5f4ec"], [0.01, "#f6e6b0"], [1, "#9a3a2a"]], hovertemplate: "%{y}, %{x}: %{z} days<extra></extra>", colorbar: {thickness: 10, title: "days"}}],
      {margin: {l: 95, r: 10, t: 28, b: 40}, title: {text: "Where and when it would warn", font: {size: 14}}, yaxis: {autorange: "reversed", dtick: 1, tickfont: {size: 10}}, paper_bgcolor: "#fff", plot_bgcolor: "#fff"}, cfg);
    const share = all.length ? (100 * f.tot / all.length).toFixed(1) : "0";
    const tstr = between ? `${T[0]}–${T[1]}` : `${T[0]}`;
    document.getElementById("figsum").innerHTML = `At <b>${tstr} ${D.unit}</b> it would warn on <b>${f.tot}</b> province-days across <b>${f.provs}</b> of ${P.length} provinces (${share}% of days the scenario applies). Source value: <b>${base.tot}</b> province-days.`
      + (f.tot === 0 ? " <b>It never fires at this level.</b>" : f.tot > all.length * 0.5 ? " <b>It fires on most applicable days, so it may be too sensitive.</b>" : "");
    document.getElementById("figfoot").textContent = `Weather: ERA5-Land reanalysis, ${P.length} provinces${D.when.length ? "; extra conditions: " + D.when.map(w => `${w.label} ${w.op} ${Array.isArray(w.value) ? w.value.join("–") : w.value}`).join(", ") : ""}. ${D.raif.length ? "Blue diamonds are RAIF field reports (Andalusia only; reporting dates are approximate)." : ""}`;
  }
  function setT(t) { T = t; i1.value = t[0]; if (between) i2.value = t[1]; rg.value = t[0]; draw(); }
  i1.oninput = () => setT(between ? [Number(i1.value), T[1]] : [Number(i1.value)]);
  i2.oninput = () => setT([T[0], Number(i2.value)]);
  rg.oninput = () => between ? setT([Number(rg.value), Math.max(Number(rg.value), T[1])]) : setT([Number(rg.value)]);
  document.getElementById("thrreset").onclick = () => setT(litT.slice());
  document.getElementById("thruse").onclick = () => {
    const f = document.getElementById("threshold"); if (f) f.value = between ? `${T[0]}-${T[1]}` : String(T[0]);
    const r = document.getElementById("d2"); if (r) r.checked = true;
    document.querySelector("form.card").scrollIntoView({behavior: "smooth"});
  };
  setT(T);
})();
