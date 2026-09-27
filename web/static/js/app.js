/* The Democratic Funnel - dashboard (single-page app).
   The data is fetched once (/api/data) and the map boundaries once (/api/geo). Pages are built the first time they
   are opened and then kept, so switching pages is instant and the map is never loaded twice. */
"use strict";

const IEC = "https://www.elections.org.za";
const PORTAL = "https://registertovote.elections.org.za";
const FINDER = "https://maps.elections.org.za/vsfinder/";
const GROUPS = ["Low registration", "Low turnout", "Both low", "Healthy"];
const GROUP_CLASS = { "Low registration": "g-lowreg", "Low turnout": "g-lowturn", "Both low": "g-both", "Healthy": "g-healthy" };
const PROV_SHORT = { "Eastern Cape": "EC", "Free State": "FS", "Gauteng": "GP", "KwaZulu-Natal": "KZN", "Limpopo": "LIM",
                     "Mpumalanga": "MP", "Northern Cape": "NC", "North West": "NW", "Western Cape": "WC" };
const NOT_A_CAUSE = "A link is not proof of a cause: patterns across municipalities cannot show why individuals act.";

let DATA = null, GEO = null, geoPromise = null;
const built = {};                 // pages already built
const charts = [];                // {canvas, make, chart} so charts can be redrawn when the theme changes

/* ------------------------------------------------------------------ small helpers */
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const pct = (x, d = 0) => (x === null || x === undefined || isNaN(x)) ? "–" : (x * 100).toFixed(d) + "%";
const num = (x) => (x === null || x === undefined || isNaN(x)) ? "–" : Math.round(x).toLocaleString("en-ZA").replace(/,/g, " ");
const millions = (x) => (x / 1e6).toFixed(1) + " m";
const pts = (x) => (x >= 0 ? "+" : "−") + Math.abs(x).toFixed(1) + " pts";
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const pill = (g) => `<span class="pill ${GROUP_CLASS[g]}">${g}</span>`;
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const byCode = () => Object.fromEntries(DATA.rows.map((r) => [r.Code, r]));
const label = (r) => `${r.Municipality} (${r.Province})`;
const turnoutLabel = () => DATA.national.has_pred ? "Predicted turnout 2026" : "Turnout 2021";

function colours() {
  return { ink: css("--ink"), ink2: css("--ink2"), line: css("--line"), navy: css("--navy"), blue: css("--blue"),
           amber: css("--amber"), crimson: css("--crimson"), green: css("--green"), lblue: css("--lblue"),
           lamber: css("--lamber"), panel: css("--panel"), accent: css("--accent") };
}
const groupColour = (g, c = colours()) => ({ "Low registration": c.blue, "Low turnout": c.amber, "Both low": c.crimson, "Healthy": c.green }[g]);

/* ------------------------------------------------------------------ searchable dropdown */
// combo(root, onPick, {keep}): root holds an <input>, a .combo-arrow button and a .combo-list <ul>.
// The arrow (or clicking into the box) always opens the full list; typing filters it. keep = leave the name in the box.
function combo(root, onPick, opts = {}) {
  const input = $("input", root), list = $(".combo-list", root), arrow = $(".combo-arrow", root);
  const all = [...DATA.rows].sort((a, b) => a.Municipality.localeCompare(b.Municipality));
  let items = [], active = -1, typed = false;
  const draw = () => {
    const q = typed ? input.value.trim().toLowerCase() : "";
    items = q ? all.filter((r) => label(r).toLowerCase().includes(q)) : all;
    active = Math.min(active, items.length - 1);
    list.innerHTML = items.length ? items.map((r, i) => `<li role="option" data-i="${i}" class="${i === active ? "active" : ""} ${label(r) === input.value ? "sel" : ""}">
      ${esc(r.Municipality)}<small>${r.Province}</small></li>`).join("") : `<li class="none">No municipality matches "${esc(input.value)}"</li>`;
  };
  const open = () => { root.classList.add("open"); input.setAttribute("aria-expanded", "true"); draw();
                       const sel = $("li.sel", list); if (sel) sel.scrollIntoView({ block: "nearest" }); };
  const close = () => { root.classList.remove("open"); input.setAttribute("aria-expanded", "false"); typed = false; active = -1; };
  const pick = (r) => { input.value = opts.keep ? label(r) : ""; close(); input.blur(); onPick(r); };
  input.addEventListener("focus", () => { if (opts.keep) input.select(); typed = false; open(); });
  input.addEventListener("click", () => { if (!root.classList.contains("open")) open(); });
  input.addEventListener("input", () => { typed = true; active = 0; open(); });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault(); if (!root.classList.contains("open")) open();
      active = Math.max(0, Math.min(items.length - 1, active + (e.key === "ArrowDown" ? 1 : -1))); draw();
      const a = $("li.active", list); if (a) a.scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter") { e.preventDefault(); if (items[Math.max(active, 0)]) pick(items[Math.max(active, 0)]); }
    else if (e.key === "Escape") { close(); input.blur(); }
  });
  arrow.addEventListener("mousedown", (e) => { e.preventDefault(); });
  arrow.addEventListener("click", () => { if (root.classList.contains("open")) close(); else { typed = false; input.focus(); open(); } });
  list.addEventListener("mousedown", (e) => e.preventDefault());
  list.addEventListener("click", (e) => { const li = e.target.closest("li[data-i]"); if (li) pick(items[+li.dataset.i]); });
  input.addEventListener("blur", () => setTimeout(close, 120));
  return { set: (r) => { input.value = label(r); } };
}

/* ------------------------------------------------------------------ charts */
function chartDefaults() {
  const c = colours();
  Chart.defaults.font.family = "Inter, 'Segoe UI', sans-serif";
  Chart.defaults.font.size = 13;
  Chart.defaults.color = c.ink2;
  Chart.defaults.borderColor = c.line;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.boxWidth = 8;
  Chart.defaults.plugins.tooltip.backgroundColor = c.ink;
  Chart.defaults.plugins.tooltip.titleColor = c.panel;
  Chart.defaults.plugins.tooltip.bodyColor = c.panel;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.cornerRadius = 10;
  Chart.defaults.maintainAspectRatio = false;
}

// writes each bar's value next to it (dataset option: valueLabel: (v) => "text")
const valueLabels = {
  id: "valueLabels",
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    chart.data.datasets.forEach((ds, i) => {
      if (!ds.valueLabel || !chart.isDatasetVisible(i)) return;
      chart.getDatasetMeta(i).data.forEach((bar, j) => {
        const v = ds.data[j];
        if (v === null || v === undefined) return;
        const horizontal = chart.options.indexAxis === "y";
        ctx.save();
        ctx.fillStyle = ds.valueColor || colours().ink;
        ctx.font = `600 ${ds.valueSize || 12}px Inter, sans-serif`;
        ctx.textBaseline = "middle";
        if (horizontal) { ctx.textAlign = "left"; ctx.fillText(ds.valueLabel(v), bar.x + 5, bar.y); }
        else { ctx.textAlign = "center"; ctx.fillText(ds.valueLabel(v), bar.x, bar.y - 10); }
        ctx.restore();
      });
    });
  },
};

function makeChart(canvas, make) {
  const entry = { canvas, make, chart: new Chart(canvas, make()) };
  charts.push(entry);
  return entry;
}
function redrawCharts() {
  chartDefaults();
  charts.forEach((e) => { e.chart.destroy(); e.chart = new Chart(e.canvas, e.make()); });
}
const pctAxis = (extra = {}) => ({ ticks: { callback: (v) => Math.round(v * 100) + "%" }, ...extra });

/* ------------------------------------------------------------------ theme */
function toggleTheme() {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("df-theme", next); } catch (e) {}
  redrawCharts();
  if (MAP.map) { setTiles(); restyleMap(); }
}

/* ------------------------------------------------------------------ router */
const PAGES = {
  overview: ["Overview", "The national picture: where people are lost between being eligible, registering and voting.", buildOverview],
  map: ["Map", "Every municipality by its problem group or rate. Filter, hover for the numbers, click to open its profile.", buildMap],
  profile: ["Municipality profile", "Look up any municipality: its funnel, its problem, what to send, and its 2026 outlook.", buildProfile],
  priority: ["Priority list", "Municipalities ranked by how far they are below a typical municipality, with the gap split into its two parts.", buildPriority],
  participation: ["Electoral participation", "Registration and turnout 2011 to 2026, by province and municipality, who registers, and what goes with low turnout.", buildParticipation],
  recommendations: ["Recommendations", "Evidence-linked responses to each type of gap: what the data shows, the evidence, a possible response, and what further evidence is needed.", buildRecommendations],
  "voter-education": ["Voter education", "How to take part in the local government elections on 4 November 2026. Information only, no political persuasion.", buildVoterEducation],
  about: ["About", "The problem, how we measured it, how the forecast works, our data sources and the limitations.", buildAbout],
  team: ["Our team", "Team UL, University of Limpopo · DIRISA Student Datathon Challenge 2026", buildTeam],
};

function route() {
  const [name, arg] = (location.hash.replace(/^#\/?/, "") || "overview").split("/");
  const page = PAGES[name] ? name : "overview";
  if (!built[page]) {
    const sec = document.createElement("section");
    sec.className = "page";
    sec.id = "page-" + page;
    sec.innerHTML = `<h1 class="page-title">${PAGES[page][0]}</h1><p class="page-sub">${PAGES[page][1]}</p><div class="body"></div>`;
    $("#pages").appendChild(sec);
    built[page] = true;
    $$(".page").forEach((p) => p.classList.remove("on"));
    sec.classList.add("on");
    PAGES[page][2]($(".body", sec));
  }
  $$(".page").forEach((p) => p.classList.toggle("on", p.id === "page-" + page));
  $$(".rail-nav a").forEach((a) => a.classList.toggle("on", a.dataset.page === page));
  if (page === "map" && MAP.map) setTimeout(() => MAP.map.invalidateSize(), 30);
  if (page === "profile") {
    const code = arg ? decodeURIComponent(arg) : (PROFILE_SHOWN || DEFAULT_PROFILE);
    if (code !== PROFILE_SHOWN) showProfile(code);
  }
  window.scrollTo({ top: 0 });
  document.title = PAGES[page][0] + " · The Democratic Funnel";
}

/* ------------------------------------------------------------------ 1. overview */
function buildOverview(body) {
  const n = DATA.national;
  const reg21 = n.registered_2021 / n.adults, vote21 = n.votes_2021 / n.adults, vote16 = n.votes_2016 / n.adults;
  body.innerHTML = `
  <div class="grid g-hero">
    <div class="card hero">
      <div class="card-head"><h3>${n.has_pred ? "2026 outlook" : "Turnout"}</h3>
        <div class="tabs"><button class="tab on" data-v="t">Turnout</button><button class="tab" data-v="r">Registration</button></div></div>
      <div class="big" id="hero-big">${n.has_pred ? pct(n.pred_2026, 1) : pct(n.turnout_2021, 1)}</div>
      <div class="muted small" id="hero-lab">${n.has_pred ? `predicted turnout on 4 November 2026 (range ${pct(n.pred_2026_low)}–${pct(n.pred_2026_high)})` : "turnout in 2021"}</div>
      <div class="chart-box" style="height:190px;margin-top:8px"><canvas id="ov-hero"></canvas></div>
    </div>
    <div class="grid g3">
      <div class="card stat lav"><div><div class="big">${Math.round(100 * n.reg_rate_2026)} of 100</div>
        <div class="lab">adults are registered to vote in 2026</div></div>
        <div class="stat-foot"><span class="icon-tile"><span class="msr">how_to_reg</span></span>
        <span class="delta">${pts(100 * (n.reg_rate_2026 - reg21))} since 2021</span></div></div>
      <div class="card stat mint"><div><div class="big">${Math.round(100 * vote21)} of 100</div>
        <div class="lab">adults actually voted in 2021</div></div>
        <div class="stat-foot"><span class="icon-tile"><span class="msr">how_to_vote</span></span>
        <span class="delta">${pts(100 * (vote21 - vote16))} since 2016</span></div></div>
      <div class="card stat cream"><div><div class="big">${millions(n.youth_not_registered)}</div>
        <div class="lab">young adults (18–29) are not registered</div></div>
        <div class="stat-foot"><span class="icon-tile"><span class="msr">school</span></span>
        <span class="delta">${pct(n.youth_reg_rate)} of 18–29s registered</span></div></div>
    </div>
  </div>

  <div class="grid g-row2" style="margin-top:18px">
    <div class="card">
      <div class="card-head"><h3 style="font-size:20px;font-weight:800;margin:0">Where to act first</h3>
        <div class="controls" style="margin:0">
          <select class="select" id="ov-prov"><option value="">All provinces</option>${Object.keys(PROV_SHORT).sort().map((p) => `<option>${p}</option>`).join("")}</select>
          <select class="select" id="ov-group"><option value="">All problems</option>${GROUPS.slice(0, 3).map((g) => `<option>${g}</option>`).join("")}</select>
        </div></div>
      <div class="scroll-x"><table class="tbl"><thead><tr><th>Municipality</th><th class="num">Registered</th><th class="num">${n.has_pred ? "Turnout 2026" : "Turnout 2021"}</th>
        <th class="hide-sm">Problem</th><th class="num hide-sm">To reach typical</th></tr></thead><tbody id="ov-rows"></tbody></table></div>
      <div style="margin-top:12px"><a class="link-more" href="#/priority">See the full priority list</a></div>
    </div>
    <div class="promo">
      <h3>Not on the <span class="tag">voters' roll</span> yet?</h3>
      <p>Check your registration in a minute, or register online before the roll closes for 4 November 2026.</p>
      <a class="cta" href="${PORTAL}" target="_blank" rel="noopener">Check my registration</a>
      <div class="deco"></div><div class="deco two"></div>
    </div>
  </div>

  <div class="grid g2" style="margin-top:18px">
    <div class="card"><h3>The funnel, 2021: out of every 100 adults</h3>
      <div class="chart-box" style="height:200px"><canvas id="ov-funnel"></canvas></div>
      <div class="caption">About ${Math.round(100 - 100 * reg21)} of every 100 adults were lost before registering, and another 35
      after registering. The official turnout figure only shows the second loss.</div></div>
    <div class="card"><h3>Every municipality falls into one of the four groups</h3>
      <div class="groups">${GROUPS.map((g) => `<div class="group">${pill(g)}<b>${n.groups[g]}</b></div>`).join("")}</div>
      <div class="caption">Compared with a typical municipality, using the 2026 roll and ${turnoutLabel().toLowerCase()}.
      Open the <a href="#/map">Map</a> to see where they are, or the <a href="#/profile">profile</a> to look up your own.</div></div>
  </div>`;

  // ${Math.round(100 * reg21 - 100 * vote21)} 

  // hero chart: turnout (actual + forecast) or registration
  let heroView = "t";
  makeChart($("#ov-hero"), () => {
    const c = colours(), years = ["2011", "2016", "2021", "2026"];
    const t = [n.turnout_2011, n.turnout_2016, n.turnout_2021, null];
    const f = [null, null, n.turnout_2021, n.has_pred ? n.pred_2026 : null];
    const r = [n.reg_rate_2011, n.reg_rate_2016, n.reg_rate_2021, n.reg_rate_2026];
    const line = (data, colour, dash) => ({ data, borderColor: colour, backgroundColor: colour + "22", fill: !dash, tension: .35,
                                           pointRadius: 4, pointBackgroundColor: colour, borderDash: dash ? [6, 5] : [], spanGaps: false, borderWidth: 2.5 });
    const datasets = heroView === "t" ? [{ label: "Turnout", ...line(t, c.navy) }, { label: "Forecast", ...line(f, c.navy, true) }]
                                      : [{ label: "Registration rate", ...line(r, c.blue) }];
    return { type: "line", data: { labels: years, datasets },
             options: { plugins: { legend: { display: false }, tooltip: { callbacks: { label: (x) => `${x.dataset.label}: ${pct(x.raw, 1)}` } } },
                        scales: { y: pctAxis({ min: heroView === "t" ? .35 : .5, max: heroView === "t" ? .65 : .8, grid: { color: colours().line } }),
                                  x: { grid: { display: false } } } } };
  });
  const heroEntry = charts[charts.length - 1];
  $$(".hero .tab", body).forEach((b) => b.addEventListener("click", () => {
    heroView = b.dataset.v;
    $$(".hero .tab", body).forEach((x) => x.classList.toggle("on", x === b));
    $("#hero-big").textContent = heroView === "t" ? (n.has_pred ? pct(n.pred_2026, 1) : pct(n.turnout_2021, 1)) : pct(n.reg_rate_2026, 1);
    $("#hero-lab").textContent = heroView === "t" ? (n.has_pred ? `predicted turnout on 4 November 2026 (range ${pct(n.pred_2026_low)}–${pct(n.pred_2026_high)})` : "turnout in 2021")
                                                  : "of adults are registered for 2026 (all years use the Census 2022 population)";
    heroEntry.chart.destroy(); heroEntry.chart = new Chart(heroEntry.canvas, heroEntry.make());
  }));

  // where to act first
  const fill = () => {
    const prov = $("#ov-prov").value, grp = $("#ov-group").value;
    const rows = DATA.rows.filter((r) => r["Problem group"] !== "Healthy" && (!prov || r.Province === prov) && (!grp || r["Problem group"] === grp)).slice(0, 6);
    $("#ov-rows").innerHTML = rows.map((r) => `<tr class="click" data-code="${r.Code}">
      <td><div class="who"><span class="tile">${PROV_SHORT[r.Province]}</span><div><b>${esc(r.Municipality)}</b><span>${r.Province}</span></div></div></td>
      <td class="num">${pct(Math.min(r["Registration rate 2026"], 1))}</td><td class="num">${pct(r["Turnout used"])}</td>
      <td class="hide-sm">${pill(r["Problem group"])}</td>
      <td class="num hide-sm">${r["Registrations needed to reach typical"] > 0 ? num(r["Registrations needed to reach typical"]) + " reg." : num(r["Extra voters needed to reach typical"]) + " voters"}</td></tr>`).join("")
      || `<tr><td colspan="5" class="muted">No municipality matches these filters.</td></tr>`;
    $$("#ov-rows tr.click").forEach((tr) => tr.addEventListener("click", () => { location.hash = "#/profile/" + tr.dataset.code; }));
  };
  $("#ov-prov").addEventListener("change", fill); $("#ov-group").addEventListener("change", fill); fill();

  // funnel
  makeChart($("#ov-funnel"), () => {
    const c = colours(), vals = [100, 100 * reg21, 100 * vote21];
    return { type: "bar", plugins: [valueLabels],
             data: { labels: ["May vote", "Registered", "Voted"],
                     datasets: [{ data: vals, backgroundColor: [c.navy, c.blue, c.amber], borderRadius: 10, barThickness: 34,
                                  valueLabel: (v) => Math.round(v), valueSize: 15 }] },
             options: { indexAxis: "y", plugins: { legend: { display: false }, tooltip: { callbacks: { label: (x) => `${Math.round(x.raw)} of 100 adults` } } },
                        scales: { x: { max: 112, display: false }, y: { grid: { display: false }, ticks: { font: { weight: 600 } } } } } };
  });
}

/* ------------------------------------------------------------------ 2. map (built once, kept alive) */
const MAP = { map: null, layer: null, tiles: null, legend: null, measure: "group", prov: "", groups: new Set(GROUPS) };
const MEASURES = {
  group: { name: "Problem group" },
  pred: { name: "Predicted turnout 2026", col: "Predicted turnout 2026", from: "#fff1cc", to: "#9a6200" },
  reg: { name: "Registration rate 2026", col: "Registration rate 2026", from: "#e3eefc", to: "#12427f", cap: 1 },
  t21: { name: "Turnout 2021", col: "Turnout 2021", from: "#fff1cc", to: "#9a6200" },
};
function mix(a, b, t) {
  const p = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const [x, y] = [p(a), p(b)];
  return "#" + x.map((v, i) => Math.round(v + (y[i] - v) * t).toString(16).padStart(2, "0")).join("");
}
function rangeOf(col, cap) {
  const v = DATA.rows.map((r) => Math.min(r[col], cap || 9)).filter((x) => x !== null && !isNaN(x));
  return [Math.min(...v), Math.max(...v)];
}
function featureFill(r) {
  const m = MEASURES[MAP.measure];
  if (MAP.measure === "group") return groupColour(r["Problem group"]);
  const [lo, hi] = rangeOf(m.col, m.cap);
  const v = Math.min(r[m.col], m.cap || 9);
  return mix(m.from, m.to, (v - lo) / (hi - lo || 1));
}
function restyleMap() {
  if (!MAP.layer) return;
  const rows = byCode(), c = colours();
  MAP.layer.setStyle((f) => {
    const r = rows[f.properties.muni_code];
    const shown = r && (!MAP.prov || r.Province === MAP.prov) && MAP.groups.has(r["Problem group"]);
    return { fillColor: r ? featureFill(r) : "#ccc", fillOpacity: shown ? .85 : .08, color: c.panel, weight: shown ? .8 : .3 };
  });
  updateLegend();
}
function setTiles() {
  // no background tiles: the municipalities are the map, which keeps it light and fast
}
function updateLegend() {
  if (!MAP.legend) return;
  const m = MEASURES[MAP.measure], div = MAP.legend.getContainer();
  if (MAP.measure === "group") {
    const counts = {};
    DATA.rows.forEach((r) => { if (!MAP.prov || r.Province === MAP.prov) counts[r["Problem group"]] = (counts[r["Problem group"]] || 0) + 1; });
    div.innerHTML = "<b>Problem group</b><br>" + GROUPS.map((g) => `<i style="background:${groupColour(g)}"></i>${g} (${counts[g] || 0})`).join("<br>");
  } else {
    const [lo, hi] = rangeOf(m.col, m.cap);
    div.innerHTML = `<b>${m.name}</b><div class="bar" style="background:linear-gradient(90deg,${m.from},${m.to})"></div>
                     <div class="ends"><span>${pct(lo)}</span><span>${pct(hi)}${m.cap ? "+" : ""}</span></div>`;
  }
}
function buildMap(body) {
  body.innerHTML = `
  <div class="controls">
    <select class="select" id="map-measure">${Object.entries(MEASURES).map(([k, m]) => `<option value="${k}">${m.name}</option>`).join("")}</select>
    <select class="select" id="map-prov"><option value="">All provinces</option>${Object.keys(PROV_SHORT).sort().map((p) => `<option>${p}</option>`).join("")}</select>
    ${GROUPS.map((g) => `<button class="chip on" data-g="${g}"><i style="background:${groupColour(g)}"></i>${g}</button>`).join("")}
  </div>
  <div class="card flat" style="padding:10px"><div id="map-canvas"><div class="map-wait"><div class="spinner"></div></div></div></div>
  <div class="caption">Hover (or tap) a municipality for its numbers, and click it to open its profile. The groups cluster by region,
  which points to regional causes. Boundaries: Municipal Demarcation Board, 2026.</div>`;

  $("#map-measure").addEventListener("change", (e) => { MAP.measure = e.target.value; restyleMap(); });
  $("#map-prov").addEventListener("change", (e) => {
    MAP.prov = e.target.value; restyleMap();
    if (!MAP.layer) return;
    const b = L.latLngBounds([]);
    MAP.layer.eachLayer((l) => { const r = byCode()[l.feature.properties.muni_code]; if (!MAP.prov || (r && r.Province === MAP.prov)) b.extend(l.getBounds()); });
    if (b.isValid()) MAP.map.fitBounds(b, { padding: [10, 10] });
  });
  $$(".chip", body).forEach((ch) => ch.addEventListener("click", () => {
    const g = ch.dataset.g;
    MAP.groups.has(g) ? MAP.groups.delete(g) : MAP.groups.add(g);
    ch.classList.toggle("on", MAP.groups.has(g)); restyleMap();
  }));

  geoPromise.then(() => {
    $("#map-canvas").innerHTML = "";
    MAP.map = L.map("map-canvas", { preferCanvas: true, zoomSnap: .25, scrollWheelZoom: false, attributionControl: false });
    setTiles();
    const rows = byCode();
    MAP.layer = L.geoJSON(GEO, {
      onEachFeature: (f, l) => {
        const r = rows[f.properties.muni_code];
        if (!r) return;
        l.bindTooltip(() => `<b>${esc(r.Municipality)}</b><br>${r.Province} · ${r.Type}<br>
          Registration 2026: ${r["Census caution"] ? "over 100% (Census caution)" : pct(r["Registration rate 2026"], 1)}<br>
          Turnout 2021: ${pct(r["Turnout 2021"], 1)}<br>${DATA.national.has_pred ? `Predicted 2026: ${pct(r["Predicted turnout 2026"], 1)}<br>` : ""}
          ${pill(r["Problem group"])}`, { sticky: true, className: "mtip" });
        l.on("click", () => { location.hash = "#/profile/" + r.Code; });
        l.on("mouseover", () => l.setStyle({ weight: 2.2, color: colours().ink }));
        l.on("mouseout", () => restyleMap());
      },
    }).addTo(MAP.map);
    MAP.legend = L.control({ position: "bottomleft" });
    MAP.legend.onAdd = () => L.DomUtil.create("div", "legend");
    MAP.legend.addTo(MAP.map);
    restyleMap();
    MAP.map.fitBounds(MAP.layer.getBounds(), { padding: [8, 8] });
  });
}

/* ------------------------------------------------------------------ 3. municipality profile */
let profileChart = [];
function buildProfile(body) {
  body.innerHTML = `
  <div class="prof-pick"><div class="combo" id="prof-combo"><span class="msr">location_city</span>
    <input id="prof-input" placeholder="Type or pick a municipality" autocomplete="off" role="combobox" aria-expanded="false">
    <button class="combo-arrow" type="button" tabindex="-1" aria-label="Show all municipalities"><span class="msr">expand_more</span></button>
    <ul class="combo-list" role="listbox"></ul></div></div>
  <div id="prof-out"><div class="empty"><span class="msr">location_city</span>Start typing a name above, use the search at the top,
  or click a municipality on the <a href="#/map">map</a>.</div></div>`;
  PROFILE_COMBO = combo($("#prof-combo"), (r) => { location.hash = "#/profile/" + r.Code; }, { keep: true });
}
let PROFILE_COMBO = null, PROFILE_SHOWN = null;
const DEFAULT_PROFILE = "LIM354";            // Polokwane, home of the University of Limpopo
function showProfile(code) {
  const r = byCode()[code];
  if (!r) return;
  PROFILE_SHOWN = code;
  PROFILE_COMBO.set(r);
  const n = DATA.national, g = r["Problem group"], caution = r["Census caution"];
  const reg = num(r["Registrations needed to reach typical"]), vot = num(r["Extra voters needed to reach typical"]);
  let send = {
    "Low registration": `<b>Send: a registration drive.</b> About <b>${reg}</b> more registrations would bring ${esc(r.Municipality)} to the typical level (${pct(r["Typical registration rate"])} of adults).`,
    "Low turnout": `<b>Send: voter mobilisation.</b> About <b>${vot}</b> more voters would bring turnout to the typical level (${pct(r["Typical turnout"])}).`,
    "Both low": `<b>Send: a registration drive and voter mobilisation.</b> About <b>${reg}</b> more registrations and <b>${vot}</b> more voters would bring it to the typical level.`,
    "Healthy": "<b>Nothing urgent.</b> Registration and turnout are at or above a typical municipality.",
  }[g];
  if (r["Young adults not registered"] > 0) send += ` Young adults are the biggest group missing: <b>${num(r["Young adults not registered"])}</b> people aged 18–29 are not registered.`;
  const meaning = { "Low registration": "below a typical municipality on registration, but those who are registered vote",
                    "Low turnout": "well registered, but fewer registered voters turn out than in a typical municipality",
                    "Both low": "below a typical municipality at both steps: registering and voting",
                    "Healthy": "at or above a typical municipality on both registration and turnout" }[g];
  const p = r["Predicted turnout 2026"], lo = r["Predicted turnout 2026 (low)"], hi = r["Predicted turnout 2026 (high)"];
  const covid = r["After COVID (2024)"];
  const regTxt = caution ? "over 100%*" : pct(r["Registration rate 2026"]);
  $("#prof-out").innerHTML = `
  <div class="prof-head"><h2>${esc(r.Municipality)}</h2>${pill(g)}<span class="muted">${r.Type} municipality, ${r.Province}</span></div>
  <p>This municipality is <b>${meaning}</b>.</p>
  <div class="note">${send}</div>
  <div class="grid g2">
    <div class="card"><h3>Out of every 100 adults</h3>
      <div class="chart-box" style="height:230px"><canvas id="prof-funnel"></canvas></div>
      <div class="kv" style="margin-top:14px">
        <div><b>${regTxt}</b><span>registration rate · typical ${pct(r["Typical registration rate"])}</span></div>
        <div><b>${pct(r["Turnout used"])}</b><span>${n.has_pred ? "turnout outlook 2026" : "turnout 2021"} · typical ${pct(r["Typical turnout"])}</span></div>
        <div><b>${pct(r["Youth registration rate"])}</b><span>of 18–29s registered · all adults ${regTxt}</span></div>
      </div></div>
    <div class="card"><h3>Turnout, and the 2026 forecast</h3>
      <div class="chart-box" style="height:230px"><canvas id="prof-trend"></canvas></div>
      ${n.has_pred ? `<p style="margin-top:12px"><b>Predicted turnout 2026: ${pct(p, 1)}</b> (likely range ${pct(lo)} – ${pct(hi)}): its 2021
        turnout plus the national change of ${pts(100 * (p - r["Turnout 2021"]))} that the 2024 national election points to, the same change for every municipality.</p>` : ""}
      ${covid ? `<p><b>After COVID: ${covid}.</b> This municipality ${covid.startsWith("recovered")
        ? "did relatively better in the 2024 national election than in 2021, so 2021 probably understated it"
        : "fell further behind the rest of the country in the 2024 national election than it usually does"}. If that carries into 2026,
        turnout would be about <b>${pct(r["Predicted turnout 2026 (COVID recovery)"], 1)}</b> (COVID recovery scenario).</p>` : ""}
      ${r["Worse than expected in 2021"] ? `<div class="note warn"><b>Fell much more than the country in 2021:</b> one of the 15 municipalities whose
        turnout fell furthest below the national change. Something local happened that our data cannot see.</div>` : ""}
      <div class="caption">${NOT_A_CAUSE} Youth figures are about registration only: the IEC does not publish turnout by age.</div></div>
  </div>
  ${caution ? `<div class="note warn">*More people are registered here than the Census 2022 counted adults. The Census sample is small in this
    municipality, so its registration rate is not reliable.</div>` : ""}`;

  profileChart.forEach((e) => { e.chart.destroy(); charts.splice(charts.indexOf(e), 1); });
  profileChart = [];
  profileChart.push(makeChart($("#prof-funnel"), () => {
    const c = colours(), reg100 = Math.min(r["Registered per 100 adults"], 100), vote100 = r["Voters per 100 adults"];
    const typR = 100 * r["Typical registration rate"], typV = typR * r["Typical turnout"];
    return { type: "bar", plugins: [valueLabels],
             data: { labels: ["May vote", "Registered", n.has_pred ? "Will vote" : "Voted (2021)"],
                     datasets: [{ label: r.Municipality, data: [100, reg100, vote100], backgroundColor: [c.navy, c.blue, c.amber], borderRadius: 8,
                                  valueLabel: (v) => Math.round(v) },
                                { label: "Typical municipality", data: [null, typR, typV], backgroundColor: c.lblue, borderRadius: 8,
                                  valueLabel: (v) => Math.round(v) }] },
             options: { indexAxis: "y", plugins: { tooltip: { callbacks: { label: (x) => `${x.dataset.label}: ${Math.round(x.raw)} of 100` } } },
                        scales: { x: { max: 118, display: false }, y: { grid: { display: false } } } } };
  }));
  profileChart.push(makeChart($("#prof-trend"), () => {
    const c = colours(), labels = ["2011", "2016", "2021", "2026"];
    const own = [r["Turnout 2011"], r["Turnout 2016"], r["Turnout 2021"], null];
    const nat = [n.turnout_2011, n.turnout_2016, n.turnout_2021, null];
    const ds = [{ label: "National", data: nat, borderColor: c.navy, borderDash: [3, 4], pointRadius: 3, borderWidth: 2, tension: .3 },
                { label: r.Municipality, data: own, borderColor: c.amber, backgroundColor: c.amber, pointRadius: 5, borderWidth: 3, tension: .3 }];
    if (n.has_pred) {
      ds.push({ label: "Forecast 2026", data: [null, null, r["Turnout 2021"], p], borderColor: c.amber, borderDash: [6, 5], pointRadius: [0, 0, 0, 6], borderWidth: 3 });
      ds.push({ label: "Likely range", data: [null, null, null, lo], borderColor: c.navy, pointRadius: 0, showLine: false });
      ds.push({ label: "Likely range ", data: [null, null, null, hi], borderColor: c.navy, pointRadius: 0, showLine: false });
    }
    return { type: "line", plugins: [{ id: "range", afterDatasetsDraw(ch) {
               if (!n.has_pred) return;
               const x = ch.scales.x.getPixelForValue(3), y1 = ch.scales.y.getPixelForValue(lo), y2 = ch.scales.y.getPixelForValue(hi);
               const ctx = ch.ctx; ctx.save(); ctx.strokeStyle = colours().navy; ctx.lineWidth = 2;
               ctx.beginPath(); ctx.moveTo(x, y1); ctx.lineTo(x, y2); ctx.moveTo(x - 6, y1); ctx.lineTo(x + 6, y1); ctx.moveTo(x - 6, y2); ctx.lineTo(x + 6, y2); ctx.stroke(); ctx.restore(); } }],
             data: { labels, datasets: ds },
             options: { plugins: { legend: { labels: { filter: (i) => !i.text.startsWith("Likely range") } },
                                   tooltip: { callbacks: { label: (x) => `${x.dataset.label}: ${pct(x.raw, 1)}` } } },
                        scales: { y: pctAxis({ grid: { color: colours().line } }), x: { grid: { display: false } } } } };
  }));
}

/* ------------------------------------------------------------------ 4. priority list */
function csvDownload(rows, cols, file) {
  const q = (v) => (v === null || v === undefined) ? "" : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : v;
  const text = [cols.map(q).join(","), ...rows.map((r) => cols.map((c) => q(r[c])).join(","))].join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type: "text/csv" }));
  a.download = file; a.click(); URL.revokeObjectURL(a.href);
}
function buildPriority(body) {
  const tl = turnoutLabel();
  body.innerHTML = `
  <div class="controls">
    <select class="select" id="pr-prov"><option value="">All provinces</option>${Object.keys(PROV_SHORT).sort().map((p) => `<option>${p}</option>`).join("")}</select>
    ${GROUPS.map((g) => `<button class="chip ${g === "Healthy" ? "" : "on"}" data-g="${g}"><i style="background:${groupColour(g)}"></i>${g}</button>`).join("")}
    <button class="btn primary" id="pr-csv"><span class="msr" style="font-size:17px;vertical-align:-3px">download</span> Download this list (CSV)</button>
  </div>
  <div class="card"><h3>The top 15: how far below a typical municipality</h3>
    <div class="chart-box" style="height:470px"><canvas id="pr-chart"></canvas></div>
    <div class="caption">Blue: the part of the shortfall from people not registering. Amber: the part from registered voters not voting.
    Ranked using the 2026 roll and ${tl.toLowerCase()}.</div></div>
  <h2 class="sec">All municipalities on this list</h2>
  <div class="table-wrap"><table class="tbl"><thead><tr><th class="num">Rank</th><th>Municipality</th><th>Problem</th><th>What to send</th>
    <th class="num">Registration 2026</th><th class="num">${tl}</th><th class="num">Registrations needed</th><th class="num">Extra voters needed</th>
    <th class="num">Young adults not registered</th></tr></thead><tbody id="pr-rows"></tbody></table></div>
  <div class="caption" id="pr-count"></div>`;
  const groups = new Set(GROUPS.slice(0, 3));
  let rows = [];
  const entry = makeChart($("#pr-chart"), () => {
    const c = colours(), top = rows.slice(0, 15);
    return { type: "bar",
             data: { labels: top.map((r) => r.Municipality),
                     datasets: [{ label: "Registration part", data: top.map((r) => r["Shortfall: registration part"]), backgroundColor: c.blue, borderRadius: 4 },
                                { label: "Turnout part", data: top.map((r) => r["Shortfall: turnout part"]), backgroundColor: c.amber, borderRadius: 4 }] },
             options: { indexAxis: "y", plugins: { tooltip: { callbacks: { label: (x) => `${x.dataset.label}: ${x.raw.toFixed(2)}` } } },
                        scales: { x: { stacked: true, title: { display: true, text: "How far below a typical municipality" }, grid: { color: colours().line } },
                                  y: { stacked: true, grid: { display: false } } } } };
  });
  const fill = () => {
    const prov = $("#pr-prov").value;
    rows = DATA.rows.filter((r) => groups.has(r["Problem group"]) && (!prov || r.Province === prov));
    $("#pr-rows").innerHTML = rows.map((r) => `<tr class="click" data-code="${r.Code}"><td class="num">${r["Priority rank"]}</td>
      <td><div class="who"><span class="tile">${PROV_SHORT[r.Province]}</span><div><b>${esc(r.Municipality)}</b><span>${r.Province}</span></div></div></td>
      <td>${pill(r["Problem group"])}</td><td>${r["What to send"]}</td><td class="num">${pct(Math.min(r["Registration rate 2026"], 1))}</td>
      <td class="num">${pct(r["Turnout used"])}</td><td class="num">${num(r["Registrations needed to reach typical"])}</td>
      <td class="num">${num(r["Extra voters needed to reach typical"])}</td><td class="num">${num(r["Young adults not registered"])}</td></tr>`).join("");
    $$("#pr-rows tr.click").forEach((tr) => tr.addEventListener("click", () => { location.hash = "#/profile/" + tr.dataset.code; }));
    $("#pr-count").textContent = `${rows.length} municipalities shown. Registration rates above 100% (Census caution) are counted as 100%.`;
    entry.chart.destroy(); entry.chart = new Chart(entry.canvas, entry.make());
  };
  $("#pr-prov").addEventListener("change", fill);
  $$(".chip", body).forEach((ch) => ch.addEventListener("click", () => {
    const g = ch.dataset.g; groups.has(g) ? groups.delete(g) : groups.add(g); ch.classList.toggle("on", groups.has(g)); fill();
  }));
  $("#pr-csv").addEventListener("click", () => csvDownload(rows, ["Priority rank", "Municipality", "Province", "Problem group", "What to send",
    "Registration rate 2026", "Turnout used", "Registrations needed to reach typical", "Extra voters needed to reach typical",
    "Young adults not registered", "Shortfall: registration part", "Shortfall: turnout part"], "democratic_funnel_priority_list.csv"));
  fill();
}

/* ------------------------------------------------------------------ 5. electoral participation (the 07_eda charts) */
function heatColour(v) {
  return v < 0 ? mix("#f7f7f7", "#2166ac", Math.min(-v, 1)) : mix("#f7f7f7", "#b2182b", Math.min(v, 1));
}
function buildParticipation(body) {
  const n = DATA.national, e = DATA.eda, bp = DATA.provinces;
  const fall = bp.map((p) => 100 * (p.t2021 - p.t2016));
  const low = e.lowest10, rose = low.filter((r) => r.t2021 > r.t2016).map((r) => r.name);
  const corr = e.corr;
  body.innerHTML = `
  <h2 class="sec" style="margin-top:0">Turnout and registration</h2>
  <div class="card"><div class="chart-box" style="height:340px"><canvas id="pa-1"></canvas></div>
    <div class="caption">All registration rates use the 2022 Census, so earlier years are understated. 4 November 2026 has not happened yet.</div></div>
  <p>More adults are on the roll than ever: the registration rate rose from <b>${pct(n.reg_rate_2011)}</b> (2011) to <b>${pct(n.reg_rate_2026)}</b> (2026).
  But turnout <b>fell from ${pct(n.turnout_2016)} to ${pct(n.turnout_2021)} in 2021</b>, the COVID election. The problem is less getting people
  registered and more getting registered voters to the polls.</p>

  <h2 class="sec">How does turnout differ between provinces?</h2>
  <div class="card"><div class="chart-box" style="height:560px"><canvas id="pa-2"></canvas></div></div>
  <p>Turnout fell in <b>every province</b> in 2021, by about <b>${Math.round(-Math.max(...fall))} to ${Math.round(-Math.min(...fall))} points</b>.
  <b>${bp[0].province}</b> had the highest turnout in 2021 (${pct(bp[0].t2021)}); the lowest was <b>${bp[bp.length - 1].province}</b> (${pct(bp[bp.length - 1].t2021, 1)}).</p>
  <div class="table-wrap" style="max-height:none"><table class="tbl"><thead><tr><th>Province</th><th class="num">Turnout 2011</th><th class="num">Turnout 2016</th>
    <th class="num">Turnout 2021</th><th class="num">Share of all adults who voted, 2021</th><th class="num">Change 2016 → 2021</th></tr></thead><tbody>
    ${[...bp].sort((a, b) => (a.t2021 - a.t2016) - (b.t2021 - b.t2016)).map((p) => `<tr><td>${p.province}</td><td class="num">${pct(p.t2011, 1)}</td>
      <td class="num">${pct(p.t2016, 1)}</td><td class="num">${pct(p.t2021, 1)}</td><td class="num">${pct(p.p2021, 1)}</td>
      <td class="num">${pts(100 * (p.t2021 - p.t2016))}</td></tr>`).join("")}</tbody></table></div>

  <h2 class="sec">The top 10 municipalities with the lowest turnout, 2011–2021</h2>
  <div class="card"><div class="chart-box" style="height:600px"><canvas id="pa-3"></canvas></div>
    <div class="caption">Ranked by average turnout over the 2011, 2016 and 2021 elections. 2011 turnout for municipalities created or re-drawn
    in 2016 is an estimate (results moved onto today's boundaries).</div></div>
  <p><b>${low[0].name} (${low[0].province})</b> has the lowest average turnout (${pct(low[0].avg, 1)}).${rose.length ? ` Turnout <b>rose</b> in 2021 in
  ${rose.join(", ")}${rose.length === 1 && rose[0] === "Collins Chabane" ? ": it was created in 2016, so its 2011 figure is an estimate, and it is in this list because of its low 2016 turnout" : ""}.` : ""}
  Low turnout is a share of <i>registered</i> voters: a municipality with low turnout may still have a full roll, and the other way round.</p>

  <h2 class="sec">People who registered (2026)</h2>
  <div class="card"><div class="chart-box" style="height:200px"><canvas id="pa-4"></canvas></div></div>
  <p><b>Young adults (18–29)</b> have by far the lowest participation: <b>${pct(n.youth_reg_rate)}</b> are registered, against
  <b>${pct(n.older_reg_rate)}</b> of adults aged 30 and older, and they are registered at a lower rate than adults overall in
  ${n.youth_below} of ${DATA.rows.length} municipalities. This is registration only: the IEC does not publish turnout by age.</p>

  <h2 class="sec">Correlation: what goes with low registration and low turnout, 2021</h2>
  <div class="note"><b>A link is not proof of a cause.</b> A pattern across municipalities cannot show why individuals do or do not vote.
  So we talk about what is <b>associated</b> with low turnout, not what causes it.</div>
  <div class="card"><table class="heat"><thead><tr><th></th><th>Registration vs typical</th><th>Turnout vs typical</th></tr></thead><tbody>
    ${corr.rows.map((name, i) => `<tr><th class="row">${name}</th><td style="background:${heatColour(corr.reg[i])}">${corr.reg[i].toFixed(2)}</td>
      <td style="background:${heatColour(corr.turn[i])}">${corr.turn[i].toFixed(2)}</td></tr>`).join("")}</tbody></table>
    <div class="caption">Blue: lower when the characteristic is higher. Red: higher when it is higher. 1 or −1 is a perfect link, 0 is none.</div></div>
  <ul>
    <li><b>Registration and turnout are only loosely related</b> (correlation <b>${corr.reg_turn.toFixed(2)}</b>): the two leaks are largely different problems.</li>
    <li><b>Density matters most:</b> denser municipalities had lower turnout in 2021 (<b>${corr.turn[4].toFixed(2)}</b>).</li>
    <li><b>Services and education:</b> their simple links with turnout in 2021 are weak. Tested properly in our model, better-serviced municipalities
      fell more in 2021 only, not before. It points to COVID hitting urban-type places, not to services driving turnout.</li>
    <li><b>Neighbours matter:</b> turnout is strongly related to neighbours' turnout (<b>${corr.turn[5].toFixed(2)}</b>, see the next chart).</li>
  </ul>

  <h2 class="sec">Turnout clusters geographically</h2>
  <div class="card"><div class="chart-box" style="height:380px"><canvas id="pa-6"></canvas></div></div>
  <p><b>Yes.</b> A municipality's turnout is strongly related to its neighbours' turnout in the same election (correlation <b>${e.cluster.fit.r.toFixed(2)}</b>),
  and still clearly related to their turnout at the previous election (<b>${e.cluster.r_prev.toFixed(2)}</b>). Low turnout is regional.
  <b>Was 2021 just COVID?</b> In cities the 2021 drop was COVID; in rural municipalities turnout is really falling: in 2024 the densest municipalities
  returned to their normal pattern, while the least dense are still below theirs.</p>

  <h2 class="sec">Population density: denser municipalities have lower turnout</h2>
  <div class="card"><div class="chart-box" style="height:380px"><canvas id="pa-7"></canvas></div></div>
  <p>Denser municipalities had lower turnout than a typical municipality in 2021 (correlation <b>${e.density.fit.r.toFixed(2)}</b>): metros and large urban
  municipalities lost more voters between registration and the ballot box. Density stands in for many things at once (urban living, migration, COVID
  restrictions in 2021), so this is a link, not a cause.</p>

  <h2 class="sec">The 2021 election in context</h2>
  <div class="note"><b>What the data shows.</b> National turnout fell from ${pct(n.turnout_2016, 1)} (2016) to ${pct(n.turnout_2021, 1)} (2021), a change of
  ${pts(100 * (n.turnout_2021 - n.turnout_2016))}. <b>Every province fell</b>, from ${pts(Math.max(...fall))} to ${pts(Math.min(...fall))}.
  Registered voters: ${millions(n.registered_2016)} (2016) and ${millions(n.registered_2021)} (2021).<br>
  <b>Context.</b> The 2021 election was held under COVID-19 restrictions on gatherings and campaigning. A drop across every province is consistent with a
  national cause, but this data cannot separate the effect of the pandemic from other reasons turnout may have changed.</div>
  <h2 class="sec">Not included</h2>
  <div class="note"><b>2006 results, the 2024 national election and municipal by-elections are not part of these comparisons.</b> We use the three most
  recent municipal elections on today's boundaries. National and municipal elections are not directly comparable, and single by-elections are not a
  reliable measure of municipal or national engagement.</div>
  <h2 class="sec">What the data can't tell you</h2>
  <div class="note warn">Election data shows <b>where</b> and <b>how much</b> participation differs. It cannot show <b>why</b>. Explanations such as
  transport barriers, documentation problems, lack of information, residential mobility, political attitudes, dissatisfaction or administrative
  barriers are <b>possible explanations that need further evidence</b>. They are not conclusions of this analysis or of the model.</div>`;

  makeChart($("#pa-1"), () => {
    const c = colours();
    return { type: "line", plugins: [valueLabels],
             data: { labels: ["2011", "2016", "2021", "2026"],
                     datasets: [{ label: "Registration rate (% of adults who may vote)", data: [n.reg_rate_2011, n.reg_rate_2016, n.reg_rate_2021, n.reg_rate_2026],
                                  borderColor: c.blue, backgroundColor: c.blue, pointRadius: 6, borderWidth: 3, tension: .25 },
                                { label: "Turnout (% of registered voters)", data: [n.turnout_2011, n.turnout_2016, n.turnout_2021, null],
                                  borderColor: c.amber, backgroundColor: c.amber, pointRadius: 6, pointStyle: "rect", borderWidth: 3, tension: .25 }] },
             options: { plugins: { tooltip: { callbacks: { label: (x) => `${x.dataset.label}: ${pct(x.raw, 1)}` } } },
                        scales: { y: pctAxis({ min: 0, max: 1, title: { display: true, text: "Percentage" }, grid: { color: colours().line } }),
                                  x: { title: { display: true, text: "Local government election year" }, grid: { display: false } } } } };
  });
  const hbars = (labels, series, max, xTitle, yTitle) => () => {
    const c = colours(), cols = { 2011: c.lblue, 2016: c.lamber, 2021: c.amber };
    return { type: "bar", plugins: [valueLabels],
             data: { labels, datasets: [2011, 2016, 2021].map((y) => ({ label: String(y), data: series(y), backgroundColor: cols[y], borderRadius: 4,
                                                                      valueLabel: (v) => pct(v, 1), valueSize: 11 })) },
             options: { indexAxis: "y", plugins: { tooltip: { callbacks: { label: (x) => `${x.dataset.label}: ${pct(x.raw, 1)}` } } },
                        scales: { x: pctAxis({ min: 0, max, title: { display: true, text: xTitle }, grid: { color: colours().line } }),
                                  y: { title: { display: true, text: yTitle }, grid: { display: false } } } } };
  };
  makeChart($("#pa-2"), hbars(bp.map((p) => p.province), (y) => bp.map((p) => p["t" + y]), .8, "Turnout rate", "Province"));
  makeChart($("#pa-3"), hbars(low.map((r) => `${r.name} (${r.province})`), (y) => low.map((r) => r["t" + y]), .62, "Turnout rate", "Municipality"));
  makeChart($("#pa-4"), () => {
    const c = colours(), yr = n.youth_registered, ya = n.youth_adults, or = n.registered_2026 - yr, oa = n.adults - ya;
    return { type: "bar", plugins: [valueLabels],
             data: { labels: ["18–29", "30+"], datasets: [{ data: [yr / ya, or / oa], backgroundColor: [c.blue, c.navy], borderRadius: 8, barThickness: 44,
                     valueLabel: (v) => v === yr / ya ? `${pct(v, 1)}  (${(yr / 1e6).toFixed(1)}m of ${(ya / 1e6).toFixed(1)}m)` : `${pct(v, 1)}  (${(or / 1e6).toFixed(1)}m of ${(oa / 1e6).toFixed(1)}m)`,
                     valueSize: 13 }] },
             options: { indexAxis: "y", plugins: { legend: { display: false }, tooltip: { callbacks: { label: (x) => pct(x.raw, 1) } } },
                        scales: { x: pctAxis({ min: 0, max: 1.2, title: { display: true, text: "Registration rate, 2026" }, grid: { color: colours().line } }),
                                  y: { title: { display: true, text: "Age" }, grid: { display: false } } } } };
  });
  const scatter = (d, xTitle, yTitle, logX, bandColour, lineColour) => () => {
    const c = colours();
    const pts_ = d.points.map((p) => ({ x: p[0], y: p[1], name: p[2] }));
    const f = d.fit, fit = f.x.map((x, i) => ({ x, y: f.y[i] }));
    const ds = [{ type: "scatter", label: "Municipality", data: pts_, backgroundColor: c.amber + "cc", borderColor: c.panel, borderWidth: 1, pointRadius: 5 },
                { type: "line", label: "Trend", data: fit, borderColor: lineColour(c), borderWidth: 3, pointRadius: 0 }];
    if (bandColour) {
      ds.push({ type: "line", label: "band-hi", data: f.x.map((x, i) => ({ x, y: f.hi[i] })), borderWidth: 0, pointRadius: 0, fill: false });
      ds.push({ type: "line", label: "band-lo", data: f.x.map((x, i) => ({ x, y: f.lo[i] })), borderWidth: 0, pointRadius: 0, fill: "-1",
                backgroundColor: bandColour(c) });
    }
    return { type: "scatter", data: { datasets: ds }, plugins: [{ id: "rlabel", afterDraw(ch) {
               const ctx = ch.ctx; ctx.save(); ctx.fillStyle = colours().accent; ctx.font = "700 14px Inter, sans-serif";
               ctx.fillText(`correlation = ${f.r.toFixed(2)}`, ch.chartArea.left + 10, ch.chartArea.top + 18); ctx.restore(); } }],
             options: { plugins: { legend: { display: false },
                                   tooltip: { filter: (x) => x.datasetIndex === 0, callbacks: { label: (x) => `${x.raw.name}: ${logX ? num(x.raw.x) + " people/km²" : pct(x.raw.x, 1)} → ${pct(x.raw.y, 1)}` } } },
                        scales: { x: logX ? { type: "logarithmic", title: { display: true, text: xTitle },
                                              ticks: { autoSkip: false, maxRotation: 0, callback: (v) => [1, 10, 100, 1000].includes(v) ? num(v) : "" }, grid: { color: colours().line } }
                                          : pctAxis({ title: { display: true, text: xTitle }, grid: { color: colours().line } }),
                                  y: pctAxis({ title: { display: true, text: yTitle }, grid: { color: colours().line } }) } } };
  };
  makeChart($("#pa-6"), scatter(e.cluster, "Neighbours' average turnout, 2021", "Own turnout, 2021", false, null, (c) => c.navy));
  makeChart($("#pa-7"), scatter(e.density, "People per km² (log scale)", "Turnout vs typical municipality, 2021", true, (c) => c.blue + "33", (c) => c.blue));
}

/* ------------------------------------------------------------------ 6. recommendations */
function recBlock(title, finding, evidence, response, further) {
  const rows = [["What the data shows", finding], ["Evidence", evidence], ["Possible response", response], ["Further evidence needed", further]];
  return `<div class="rec"><h3>${title}</h3>${rows.map(([k, v]) => `<div class="row"><div class="k">${k}</div><div>${v}</div></div>`).join("")}</div>`;
}
function buildRecommendations(body) {
  const n = DATA.national, rows = DATA.rows;
  const lowReg = rows.filter((r) => ["Low registration", "Both low"].includes(r["Problem group"])).length;
  const lowTurn = rows.filter((r) => ["Low turnout", "Both low"].includes(r["Problem group"])).length;
  body.innerHTML = `
  <p>Each recommendation is tied to a finding in the data. For every one we separate <b>what the data shows</b>, <b>the evidence</b>, <b>a possible
  response</b>, and <b>what further evidence is needed</b>. Municipalities are not ranked or scored here: the data shows where a gap exists, not why.</p>
  ${recBlock("1 · Registration",
    `${millions(n.adults - n.registered_2026)} eligible adults (${pct(1 - n.reg_rate_2026)}) are not on the 2026 voters' roll. In <b>${lowReg}</b> municipalities registration is below a typical municipality.`,
    `2026 registration figures (IEC, September 2026) compared with citizens aged 18+ (Census 2022). Typical (median) registration rate: ${pct(n.typical_reg)}.`,
    "Make registration information easier to find and understand; publicise the ways to register (online, at IEC offices, at registration events); explain the documents needed; focus voter education where registration gaps are documented.",
    "Why people are not registered in each place, for example address changes, missing identity documents, information gaps or mobility. That needs local or survey research; this data cannot show it.")}
  ${recBlock("2 · Turnout",
    `In 2021, ${pct(1 - n.turnout_2021, 1)} of registered voters did not vote (${millions(n.registered_2021 - n.votes_2021)} people). In <b>${lowTurn}</b> municipalities turnout is expected to be below a typical municipality.`,
    `IEC results: turnout was ${pct(n.turnout_2011, 1)} (2011), ${pct(n.turnout_2016, 1)} (2016) and ${pct(n.turnout_2021, 1)} (2021, held under COVID-19 restrictions). Every province fell in 2021.`,
    "Improve public information about voting: dates, voting-station locations, procedures and special votes; make that information simple and available in local languages; support voters to confirm their details before election day.",
    "Local barriers to voting (distance, transport, work, queues, trust) are possible explanations, not findings. Research with communities is needed before choosing between them.")}
  ${recBlock("3 · Youth participation",
    `${millions(n.youth_not_registered)} adults aged 18–29 are not registered: ${pct(n.youth_share_of_missing)} of everyone missing from the roll. Young adults are registered at a lower rate than adults overall in <b>${n.youth_below} of ${rows.length}</b> municipalities.`,
    `Youth registration rate ${pct(n.youth_reg_rate)} against ${pct(n.older_reg_rate)} for adults aged 30+ (IEC registration by age, Census 2022).`,
    "Expand youth-focused voter education; communicate through channels young people use; explain what municipalities are responsible for; make registration and voting information easy to access on a phone.",
    "Turnout by age is not published, so we cannot say how young people vote once registered. Youth-specific research is needed on why registration is lower.")}
  ${recBlock("4 · Data and research",
    `Some questions cannot be answered with the available data. In <b>${n.census_caution}</b> small municipalities more people are registered than the Census counted adults.`,
    "Population figures come only from Census 2022; youth turnout is not published; 2011 results had to be moved onto today's boundaries; past elections could not predict which municipalities would do better or worse than the national change, so the 2026 forecast is the same national change for everyone, give or take about 5 points.",
    "Publish turnout by age group at municipal level; publish registration by age for past elections; update population estimates between censuses; combine these numbers with community-level research.",
    "Better data would show whether the gaps found here persist, and why they occur.")}
  <div class="note"><b>What this page does not claim.</b> ${NOT_A_CAUSE} The responses above are options to consider, not conclusions of the model.</div>

  <h2 class="sec">Where is each gap documented?</h2>
  <p class="muted small">Listed alphabetically, not ranked. Use it to find the municipalities where a particular gap exists.</p>
  <div class="controls">
    <button class="chip on" data-gap="reg">Registration gap</button><button class="chip" data-gap="turn">Turnout gap</button>
    <button class="chip" data-gap="youth">Youth registration gap</button>
    <select class="select" id="rc-prov"><option value="">All provinces</option>${Object.keys(PROV_SHORT).sort().map((p) => `<option>${p}</option>`).join("")}</select>
    <button class="btn primary" id="rc-csv"><span class="msr" style="font-size:17px;vertical-align:-3px">download</span> Download (CSV)</button>
  </div>
  <div class="table-wrap" style="max-height:420px"><table class="tbl"><thead id="rc-head"></thead><tbody id="rc-rows"></tbody></table></div>
  <div class="caption" id="rc-count"></div>`;
  let gap = "reg", out = [], cols = [];
  const fill = () => {
    const prov = $("#rc-prov").value;
    let t = rows.filter((r) => !prov || r.Province === prov);
    if (gap === "reg") { t = t.filter((r) => ["Low registration", "Both low"].includes(r["Problem group"])); cols = [["Registration rate 2026", "Registration rate 2026", "p"], ["Registrations needed to reach typical", "Registrations to reach typical", "n"]]; }
    else if (gap === "turn") { t = t.filter((r) => ["Low turnout", "Both low"].includes(r["Problem group"])); cols = [["Turnout 2021", "Turnout 2021", "p"], ["Turnout used", "Turnout outlook 2026", "p"], ["Extra voters needed to reach typical", "Extra voters to reach typical", "n"]]; }
    else { t = t.filter((r) => r["Youth registration rate"] < r["Typical youth registration rate"]); cols = [["Youth registration rate", "Youth registration rate", "p"], ["Young adults not registered", "Young adults not registered", "n"]]; }
    out = t.sort((a, b) => a.Municipality.localeCompare(b.Municipality));
    $("#rc-head").innerHTML = `<tr><th>Municipality</th><th>Province</th>${cols.map((c) => `<th class="num">${c[1]}</th>`).join("")}</tr>`;
    $("#rc-rows").innerHTML = out.map((r) => `<tr class="click" data-code="${r.Code}"><td><b>${esc(r.Municipality)}</b></td><td>${r.Province}</td>
      ${cols.map((c) => `<td class="num">${c[2] === "p" ? pct(Math.min(r[c[0]], 1)) : num(r[c[0]])}</td>`).join("")}</tr>`).join("");
    $$("#rc-rows tr.click").forEach((tr) => tr.addEventListener("click", () => { location.hash = "#/profile/" + tr.dataset.code; }));
    $("#rc-count").textContent = `${out.length} municipalities. 'Typical' = the median municipality. Rates above 100% (Census caution) are shown as 100%.`;
  };
  $$("[data-gap]", body).forEach((b) => b.addEventListener("click", () => { gap = b.dataset.gap; $$("[data-gap]", body).forEach((x) => x.classList.toggle("on", x === b)); fill(); }));
  $("#rc-prov").addEventListener("change", fill);
  $("#rc-csv").addEventListener("click", () => csvDownload(out, ["Municipality", "Province", ...cols.map((c) => c[0])], `democratic_funnel_${gap}_gap.csv`));
  fill();
}

/* ------------------------------------------------------------------ 7. voter education */
function buildVoterEducation(body) {
  const card = (icon, title, html) => `<div class="card info"><span class="icon-tile"><span class="msr">${icon}</span></span><h3>${title}</h3>${html}</div>`;
  body.innerHTML = `
  <p>South Africa's next local government elections are on <b>4 November 2026</b>. Here is how to make sure you can vote. Always check the
  <b>Electoral Commission (IEC)</b> for the latest official information.</p>
  <div class="grid g3">
    ${card("how_to_reg", "Am I registered?", `<p>SMS your ID number to <b>32810</b> (costs R1), or check online on the <a href="${PORTAL}" target="_blank" rel="noopener">IEC voter portal</a>. You will see whether you are registered and where your voting station is.</p>`)}
    ${card("location_on", "Where do I vote?", `<p>You vote at the voting station where you are registered. Find it with the <a href="${FINDER}" target="_blank" rel="noopener">IEC voting station finder</a>, the official IEC app, or by SMS to <b>32810</b>.</p>`)}
    ${card("edit_note", "How do I register?", `<ol><li>You must be a <b>South African citizen</b> aged <b>16 or older</b> (you can vote from 18).</li><li>Register <b>online</b> at <a href="${PORTAL}" target="_blank" rel="noopener">registertovote.elections.org.za</a>, at your <b>local IEC office</b>, at your voting station during a <b>registration weekend</b>, or at an IEC registration event.</li><li>Nobody can register for you: you must do it yourself.</li><li>Registration closes when the election is proclaimed, so do not wait.</li></ol>`)}
    ${card("badge", "What do I need?", `<p>One of these original documents from Home Affairs:</p><ul><li>green, barcoded ID book</li><li>smart ID card</li><li>valid Temporary Identity Certificate</li></ul><p>No other identification is accepted. Bring the same document when you vote.</p>`)}
    ${card("home_work", "What if I have moved?", `<p>You must <b>update your registration</b> when you move, so that you vote in the ward where you now live. You can do this <a href="${PORTAL}" target="_blank" rel="noopener">online</a> or at your local IEC office before registration closes.</p>`)}
    ${card("accessible", "What are special votes?", `<p>If you cannot vote at your voting station on election day, you can <b>apply for a special vote</b>. Voters who are physically infirm, disabled or pregnant can ask for a <b>home visit</b>; others vote at their voting station before election day. Apply within the period set by the IEC: see <a href="${IEC}" target="_blank" rel="noopener">elections.org.za</a>.</p>`)}
  </div>
  <h2 class="sec">Why do local elections matter?</h2>
  <p>Your <b>municipal council</b> makes decisions that affect daily life. Municipalities are responsible for services such as:</p>
  <ul><li><b>water</b> and <b>sanitation</b></li><li><b>electricity</b> distribution in many areas</li><li><b>refuse removal</b></li>
      <li><b>local roads</b>, streetlights and storm-water drains</li><li>local <b>planning</b>, building approvals, parks and community facilities</li></ul>
  <p>In local government elections you vote for a <b>ward councillor</b> (the person who represents your ward) and for a <b>party</b> on the proportional
  ballot; outside the metros there is also a party ballot for the district council. These votes decide who governs your municipality for the next five years.</p>
  <div class="note">This page gives voter information only. It does not recommend any party or candidate. For official information, visit
  <a href="${IEC}" target="_blank" rel="noopener">elections.org.za</a>.</div>`;
}

/* ------------------------------------------------------------------ 8. about */
function buildAbout(body) {
  const n = DATA.national;
  body.innerHTML = `
  <div class="grid g2">
    <div class="card"><h3>The problem</h3><p>South Africa votes for its local councils on <b>4 November 2026</b>. People drop out of local democracy at two
      points: adults who never <b>register</b>, and registered voters who do not <b>vote</b>. The turnout figure in the news only measures the second,
      because it is calculated among registered voters. The two leaks need different responses: registration drives for the first, voter education
      and mobilisation for the second.</p></div>
    <div class="card"><h3>How we measure it</h3><p>For each municipality: <b>registration rate</b> = registered ÷ adults who may vote; <b>turnout</b> =
      votes cast ÷ registered; <b>real participation</b> = registration rate × turnout. Each municipality is compared with the <b>typical (median)
      municipality</b>, which places it in one of four problem groups.</p></div>
  </div>
  <h2 class="sec">How the forecast works, in plain words</h2>
  <p>2026 turnout = 2021 turnout + a <b>national change</b>, taken from turnout in the 2024 national election. Every municipality gets the same change.</p>
  <p>We also built a statistical model (a hierarchical regression, with municipalities grouped inside provinces) to predict which municipalities would do
  better or worse than the national change. We tested it fairly: trained on 2011 → 2016 and predicting 2016 → 2021, it was <b>not more accurate</b>
  than giving every municipality the same national change, and it did not rank municipalities correctly. Most of the change between elections is national,
  and differences between municipalities were hard to predict, so the dashboard uses the national change alone.</p>
  <p>Every forecast comes with a <b>range</b>, not a single number: the spread of this approach's errors when it was tested on 2021 (8 in 10
  municipalities fell inside it).</p>
  <h2 class="sec">Data sources</h2>
  <table class="tbl"><thead><tr><th>Source</th><th>Used for</th></tr></thead><tbody>
    <tr><td>IEC municipal election results 2011, 2016, 2021</td><td>registered voters, votes cast, turnout</td></tr>
    <tr><td>IEC national election results 2019, 2024</td><td>the national change in turnout expected for 2026, and the COVID rebound</td></tr>
    <tr><td>IEC voter registration statistics, September 2026</td><td>the 2026 roll, including ages 18–29</td></tr>
    <tr><td>Stats SA Census 2022</td><td>adults who may vote (citizens 18+), services, education</td></tr>
    <tr><td>Municipal Demarcation Board</td><td>boundaries, area, neighbours</td></tr>
    <tr><td>IEC municipal atlas</td><td>2011 results moved onto today's boundaries</td></tr></tbody></table>
  <h2 class="sec">Limitations, stated honestly</h2>
  <ul>
    <li><b>${NOT_A_CAUSE}</b></li>
    <li><b>Youth figures are about registration only.</b> The IEC does not publish turnout by age at municipal level.</li>
    <li><b>Census undercount and small samples.</b> In ${n.census_caution} small municipalities more people are registered than the Census counted adults;
      their registration rate is flagged and counted as 100%.</li>
    <li><b>2021 was a COVID election.</b> Its low turnout is partly a one-off, which is why 2026 is given as a range.</li>
    <li><b>Boundaries changed in 2016.</b> 2011 results were moved onto today's boundaries using area shares.</li>
    <li><b>Registration is a snapshot</b> from September 2026; it changes until the roll closes.</li>
    <li><b>Small sample.</b> 213 municipalities and two past changes in turnout.</li>
  </ul>`;
}

/* ------------------------------------------------------------------ 9. team */
function buildTeam(body) {
  const team = ["Eshley", "Morongwa", "Mthokozisi", "Nkululeko", "Khwathisedzo", "Thato"];
  body.innerHTML = `<div class="team-grid">${team.map((t) => `<div class="member"><div class="ring">
    <img src="${window.STATIC}img/team/${t.toLowerCase()}.jpg" alt="${t}" loading="lazy"></div><b>${t}</b><span>Team UL</span></div>`).join("")}</div>`;
}

/* ------------------------------------------------------------------ start */
function start() {
  chartDefaults();
  $("#theme-btn").addEventListener("click", toggleTheme);
  // team pop-up in the header: the chip opens and closes it; a click anywhere else closes it
  const teamWrap = $(".team-wrap");
  $("#team-btn").addEventListener("click", (e) => {
    e.stopPropagation();
    teamWrap.classList.toggle("open");
    $("#team-btn").setAttribute("aria-expanded", teamWrap.classList.contains("open"));
  });
  document.addEventListener("click", (e) => { if (!teamWrap.contains(e.target)) teamWrap.classList.remove("open"); });
  $(".team-pop-link").addEventListener("click", () => teamWrap.classList.remove("open"));
  // follow the system setting live, unless the viewer picked a theme themselves
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
    let saved = null; try { saved = localStorage.getItem("df-theme"); } catch (x) {}
    if (!saved) { document.documentElement.dataset.theme = e.matches ? "dark" : "light"; redrawCharts(); if (MAP.map) { setTiles(); restyleMap(); } }
  });
  fetch("api/data").then((r) => r.json()).then((d) => {
    DATA = d;
    // start loading the map boundaries straight away, once, so the map is ready when it is opened
    geoPromise = fetch("api/geo").then((r) => r.json()).then((g) => { GEO = g; });
    combo($("#search-combo"), (r) => { location.hash = "#/profile/" + r.Code; });
    $("#loading").remove();
    window.addEventListener("hashchange", route);
    route();
  }).catch(() => { $("#loading").innerHTML = "The data could not be loaded. Please refresh the page."; });
}
document.addEventListener("DOMContentLoaded", start);
