"use strict";

// ---------------------------------------------------------------- helpers

const $ = (sel) => document.querySelector(sel);
const el = (tag, attrs = {}, ...children) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k === "dataset") Object.assign(node.dataset, v);
    else node.setAttribute(k, v);
  }
  for (const c of children) if (c !== null && c !== undefined) node.append(c);
  return node;
};

const STATUS_TEXT = {
  disconnected: "Disconnected",
  connecting: "Connecting…",
  reconnecting: "Reconnecting…",
  connected: "Connected",
};
const SOURCE_TEXT = { push: "push", poll: "poll", refresh: "refresh", console: "console", probe: "probe", test: "test" };
// FEATURES.md #23: hvilke grupper der vises som kort på hvilken side.
const PAGE_GROUPS = {
  overview: ["zone1", "audio", "video", "zone2"],
  device: ["system", "version", "network", "inputs", "settings", "faults"],
};
const HARDWARE_FAULT_COUNT = 8;  // FCQ0001-0008 er hardwaretællere (FEATURES.md #21)

function fmtTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-GB", { hour12: false }) + "." + String(d.getMilliseconds()).padStart(3, "0");
}

function ago(iso) {
  if (!iso) return "";
  const s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return `${s} s ago`;
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  return `${Math.floor(s / 3600)} h ago`;
}

let toastTimer;
function toast(message, bad = false) {
  const t = $("#toast");
  t.textContent = message;
  t.className = "toast" + (bad ? " bad" : "");
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { t.hidden = true; }, bad ? 7000 : 3500);
}

/** fetch-wrapper der altid giver backendens specifikke fejlbesked videre.
 *  FastAPI's egne valideringsfejl har `detail` som en *liste* af objekter,
 *  vores egne som en streng — begge former håndteres. */
async function api(method, path, body) {
  let res;
  try {
    res = await fetch(path, {
      method,
      headers: body !== undefined ? { "Content-Type": "application/json" } : {},
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    throw new Error(`Cannot reach the app backend (${err.message})`);
  }
  let data = null;
  try { data = await res.json(); } catch { /* tomt eller ikke-JSON svar — håndteres nedenfor */ }
  if (!res.ok) {
    const d = data && data.detail;
    let msg;
    if (typeof d === "string") msg = d;
    else if (Array.isArray(d)) msg = d.map((e) => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`).join("; ");
    else msg = `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

// ---------------------------------------------------------------- state

const state = {
  connection: null,
  settings: null,
  groups: {},
  values: new Map(),
  log: [],
  traffic: [],
  changelog: { started_at: null, baseline: [], entries: [], dropped: 0 },
  logmode: null,
  faults: {},
};

// ---------------------------------------------------------------- render: connection

function connected() {
  return Boolean(state.connection && state.connection.status === "connected");
}

function renderConnection() {
  const c = state.connection;
  if (!c) return;
  const pill = $("#conn-pill");
  pill.dataset.status = c.status;
  pill.textContent = STATUS_TEXT[c.status] || c.status;
  $("#conn-target").textContent = `${c.host}:${c.port}`;
  // Én knap: Connect når appen ikke forsøger at forbinde, ellers Disconnect.
  const running = c.status !== "disconnected";
  const btn = $("#btn-conn");
  btn.textContent = running ? "Disconnect" : "Connect";
  btn.classList.toggle("primary", !running);
  $("#btn-refresh").disabled = c.status !== "connected";
  $("#btn-probe").disabled = c.status !== "connected";
  for (const b of document.querySelectorAll("[data-needs-connection]")) b.disabled = !connected();

  const banner = $("#conn-error");
  if (c.last_error && c.status !== "connected") {
    let text = c.last_error;
    if (c.status === "reconnecting" && c.next_retry_s) text += ` — retrying in ${c.next_retry_s} s`;
    banner.textContent = text;
    banner.hidden = false;
  } else {
    banner.hidden = true;
  }
}

// ---------------------------------------------------------------- render: kort

const val = (code) => state.values.get(code);
const ok = (code) => { const v = val(code); return v && v.status === "ok" && v.raw !== null ? v : null; };
const txt = (code, fallback = "—") => { const v = ok(code); return v ? (v.raw.trim() === "" ? fallback : v.text) : fallback; };

function cardShell(group, title, tools = []) {
  const card = el("article", { class: "card", dataset: { group } });
  const head = el("header", { class: "card-head" }, el("h2", {}, title));
  if (tools.length) head.append(el("div", { class: "card-actions" }, ...tools));
  card.append(head);
  return card;
}

function rowsList(values) {
  const dl = el("dl", { class: "rows" });
  for (const v of values) dl.append(renderRow(v));
  return dl;
}

function sectionTitle(text) {
  return el("div", { class: "rows-section" }, text);
}

function renderCards() {
  for (const [page, groups] of Object.entries(PAGE_GROUPS)) {
    const host = $(`#cards-${page}`);
    host.replaceChildren(...groups.map(renderGroupCard).filter(Boolean));
  }
  renderTiles();
  renderConnection();
}

function groupValues(group) {
  return [...state.values.values()].filter((v) => v.group === group);
}

function renderGroupCard(group) {
  const title = state.groups[group] || group;
  if (group === "faults") return renderFaultCard(cardShell(group, title), groupValues(group));
  if (group === "version") return renderVersionCard(title);
  if (group === "network") return renderNetworkCard(title);
  if (group === "settings") return renderSettingsCard(title);
  if (group === "inputs") return renderInputsCard(title);
  const values = groupValues(group);
  if (group === "inputs") values.sort((a, b) => inputOrder(a.code) - inputOrder(b.code));
  const card = cardShell(group, title);
  card.append(values.length ? rowsList(values)
    : el("p", { class: "empty" }, group === "inputs" ? "Read once the input count is known" : "No data"));
  return card;
}

function refreshButton(id, group, message) {
  const b = el("button", { class: "small", id, "data-needs-connection": "" }, "Refresh");
  b.disabled = !connected();
  b.onclick = (e) => action(e.currentTarget, async () => {
    await api("POST", `/api/refresh?group=${group}`);
    toast(message);
  });
  return b;
}

function renderVersionCard(title) {
  const copy = el("button", { class: "small" }, "Copy all");
  copy.onclick = async () => {
    try { await copyText(versionsAsText()); toast("Version information copied"); }
    catch (err) { toast(err.message, true); }
  };
  const card = cardShell("version", title, [copy, refreshButton("versions-refresh", "version", "Versions re-queried")]);
  const dl = el("dl", { class: "rows" });
  dl.append(sectionTitle("This app"));
  dl.append(staticRow("AVM70 Diagnostics", appVersion ? `v${appVersion.version} build ${appVersion.build}` : "—"));
  dl.append(staticRow("System owner", (state.settings && state.settings.owner) || "—"));
  for (const [section, values] of versionSections()) {
    if (!values.length) continue;
    dl.append(sectionTitle(section));
    for (const v of values) dl.append(renderRow(v));
  }
  card.append(dl);
  return card;
}

function renderNetworkCard(title) {
  const card = cardShell("network", title, [refreshButton("network-refresh", "network", "Network information re-read")]);
  const dl = el("dl", { class: "rows" });
  for (const [section, codes] of NETWORK_SECTIONS) {
    const values = codes.map(val).filter(Boolean);
    if (!values.length) continue;
    dl.append(sectionTitle(section));
    for (const v of values) dl.append(renderRow(v));
  }
  card.append(dl);
  card.append(el("p", { class: "card-note" },
    "While connected, this app holds the AVM70's only control connection — the Anthem app and ARC room correction cannot connect at the same time."));
  return card;
}

// Indstillingerne i overskuelige sektioner (FEATURES.md #23).
const SETTINGS_SECTIONS = [
  ["Power and standby", ["GCCSTBY", "GCSHDMIB", "GCNSPO"]],
  ["HDMI and CEC", ["GCCECC", "GCCPFC", "GCCTVA"]],
  ["Volume and inputs at power-on", ["GCMMV", "GCMPOV", "GCMPOI", "GCZ2MMV", "GCZ2POV", "GCZ2POI"]],
  ["Muting", ["GCHMMO", "GCMLOWS", "GCMDOWS"]],
  ["Updates", ["GCAU", "GCBU"]],
  ["Control", ["GCTCP", "GCFIR", "GCRIR", "GCT1C", "GCT1P", "GCT2C", "GCT2P", "GCT3C", "GCT3P"]],
];

function renderSettingsCard(title) {
  const card = cardShell("settings", title, [refreshButton("settings-refresh", "settings", "Settings re-read")]);
  const dl = el("dl", { class: "rows" });
  const shown = new Set();
  for (const [section, codes] of SETTINGS_SECTIONS) {
    const values = codes.map(val).filter(Boolean);
    if (!values.length) continue;
    dl.append(sectionTitle(section));
    for (const v of values) { dl.append(renderRow(v)); shown.add(v.code); }
  }
  // Nye indstillinger fra backend, som endnu ikke er placeret i en sektion.
  const rest = groupValues("settings").filter((v) => !shown.has(v.code));
  if (rest.length) { dl.append(sectionTitle("Other")); for (const v of rest) dl.append(renderRow(v)); }
  card.append(dl);
  return card;
}

/** Én række pr. input: navn, og rumkorrektion som undertekst. */
function renderInputsCard(title) {
  const card = cardShell("inputs", title, [refreshButton("inputs-refresh", "inputs", "Inputs re-read")]);
  const numbers = [...new Set(groupValues("inputs").map((v) => Number(v.code.match(/^IS(\d+)/)[1])))].sort((a, b) => a - b);
  if (!numbers.length) {
    card.append(el("p", { class: "empty" }, "Read once the input count is known"));
    return card;
  }
  const current = ok("Z1INP") ? Number(ok("Z1INP").raw) : null;
  const dl = el("dl", { class: "rows" });
  for (const n of numbers) {
    const name = val(`IS${n}IN`);
    const arc = val(`IS${n}ARC`);
    const nameText = name && name.raw !== null ? (name.raw.trim() ? name.text : "(not set)") : "—";
    const dd = el("dd", {}, el("span", { class: "val" }, nameText));
    if (n === current) dd.append(" ", el("span", { class: "badge" }, "selected"));
    if (arc && arc.raw !== null) dd.append(el("span", { class: "sub-val" }, `Room correction: ${arc.text}`));
    dd.append(el("span", { class: "raw" }, `IS${n}IN / IS${n}ARC`));
    // id efter navne-koden, så updateValue opdaterer rækken uden at gentegne alt
    dl.append(el("div", { class: "row", id: `row-IS${n}IN` }, el("dt", {}, `Input ${n}`), dd));
  }
  card.append(dl);
  return card;
}

function staticRow(label, value) {
  return el("div", { class: "row" }, el("dt", {}, label), el("dd", {}, el("span", { class: "val" }, value)));
}

/** Fejlregister-kort: hardwaretællere altid, kommandotællere kun hvis > 0. */
function renderFaultCard(card, values) {
  values.sort((a, b) => a.code.localeCompare(b.code));
  const f = state.faults || {};
  const hw = values.slice(0, HARDWARE_FAULT_COUNT);
  const nonzero = values.slice(HARDWARE_FAULT_COUNT).filter((v) => v.raw !== null && v.raw.trim() !== "0" && v.raw.trim() !== "");
  const reread = el("button", { class: "small", id: "faults-refresh" }, "Re-read");
  reread.disabled = !connected() || f.reading;
  reread.onclick = (e) => action(e.currentTarget, async () => {
    await api("POST", "/api/faults/refresh");
    toast("Fault counters re-read");
  });
  card.querySelector(".card-head").append(el("div", { class: "card-actions" }, reread));
  card.append(el("p", { class: "card-note" },
    f.reading ? "Reading…" : f.read_at ? `Read ${fmtTime(f.read_at)}` : f.error || "Read after connecting"));
  if (values.length === 0) return card;
  const dl = el("dl", { class: "rows" });
  dl.append(sectionTitle("Hardware"));
  for (const v of hw) dl.append(renderRow(v));
  dl.append(sectionTitle(`Command fault counters — ${nonzero.length} of ${values.length - hw.length} not zero`));
  for (const v of nonzero) dl.append(renderRow(v));
  card.append(dl);
  return card;
}

function inputOrder(code) {
  const m = code.match(/^IS(\d+)(IN|ARC)$/);
  return m ? Number(m[1]) * 2 + (m[2] === "ARC" ? 1 : 0) : 0;
}

function renderRow(v) {
  const row = el("div", { class: "row", id: `row-${v.code}` });
  fillRow(row, v);
  return row;
}

function fillRow(row, v) {
  const value = el("span", { class: "val" });
  if (v.raw === null || v.raw === undefined) {
    value.textContent = v.status === "unknown" ? "—" : "";
  } else {
    value.textContent = v.raw.trim() === "" ? "(not set)" : v.text;
  }
  const dd = el("dd", {}, value);
  if (v.status !== "ok" && v.status !== "unknown") {
    // "Zone is off" er forventet når zonen er slukket — nedtonet, ikke en advarsel.
    dd.append(" ", el("span", { class: v.status === "zone_off" ? "state quiet" : "state" }, v.status_text || v.status));
  }
  const rawText = v.code.startsWith("@") ? "device web API"
    : `${v.code}${v.raw !== null && v.raw !== undefined ? " = " + JSON.stringify(v.raw) : ""}`;
  dd.append(el("span", { class: "raw" }, rawText));
  row.replaceChildren(el("dt", {}, v.label), dd);
  row.classList.toggle("stale", v.status !== "ok" && v.raw !== null);
  row.title = [
    v.updated_at ? `Last response: ${fmtTime(v.updated_at)} (${SOURCE_TEXT[v.source] || v.source || ""})` : "",
    v.changed_at ? `Last change: ${fmtTime(v.changed_at)} — ${ago(v.changed_at)}` : "",
  ].filter(Boolean).join("\n");
}

let tilesTimer = null;
function updateValue(v) {
  const prev = state.values.get(v.code);
  state.values.set(v.code, v);
  const row = v.group === "inputs" ? null : document.getElementById(`row-${v.code}`);
  if (!row) {
    if (PAGE_GROUPS.overview.includes(v.group) || PAGE_GROUPS.device.includes(v.group)) renderCards();
  } else {
    fillRow(row, v);
    if (prev && prev.raw !== null && prev.raw !== v.raw) {
      row.classList.remove("flash");
      void row.offsetWidth; // genstart overgangen
      row.classList.add("flash");
      setTimeout(() => row.classList.remove("flash"), 60);
    }
  }
  // Værdier kommer i bølger (en hel poll-runde); felterne tegnes én gang pr. bølge.
  clearTimeout(tilesTimer);
  tilesTimer = setTimeout(renderTiles, 50);
}

// ---------------------------------------------------------------- overview-felter (FEATURES #23)

function tile(label, main, sub, tone = "") {
  return el("div", { class: `tile ${tone}` },
    el("div", { class: "tile-label" }, label),
    el("div", { class: "tile-main" }, main),
    el("div", { class: "tile-sub" }, sub || "\u00a0"));
}

function inputName(zone) {
  const n = ok(`Z${zone}INP`);
  if (!n) return "—";
  const name = ok(`IS${n.raw.trim()}IN`);
  return name && name.raw.trim() ? name.text : `Input ${n.raw.trim()}`;
}

function renderTiles() {
  const tiles = [];
  // Hovedzone
  const on = ok("Z1POW") && ok("Z1POW").raw === "1";
  const muted = ok("Z1MUT") && ok("Z1MUT").raw === "1";
  tiles.push(tile("Main zone", on ? inputName(1) : txt("Z1POW"),
    on ? `${txt("Z1VOL")}${muted ? " · MUTED" : ""}` : "", !ok("Z1POW") ? "" : on ? (muted ? "warn" : "ok") : "off"));
  // Lyd
  const noAudio = ok("Z1AIF") && ok("Z1AIF").raw.trim() === "0";
  const audioSub = ["Z1AIC", "Z1SRT", "Z1BDP"].map((c) => ok(c))
    .filter((v) => v && v.raw.trim() !== "" && v.raw.trim() !== "0").map((v) => v.text).join(" · ");
  tiles.push(tile("Audio", noAudio ? "No input signal" : txt("Z1AIN", txt("Z1AIF")), noAudio ? "Nothing to decode from the selected source" : audioSub,
    !ok("Z1AIF") ? "" : noAudio ? (on ? "bad" : "off") : "ok"));
  tiles.push(tile("Listening mode", txt("Z1ALM"), ok("Z1DYN") ? `Dynamics ${txt("Z1DYN")}` : ""));
  // Video
  const noVideo = ok("Z1VIR") && ok("Z1VIR").raw.trim() === "0";
  const res = ok("Z1IRH") && ok("Z1IRV") && ok("Z1IRH").raw.trim() !== "0" ? `${ok("Z1IRH").raw} × ${ok("Z1IRV").raw}` : "";
  tiles.push(tile("Video", txt("Z1VIR"), res, !ok("Z1VIR") ? "" : noVideo ? "off" : "ok"));
  // Zone 2
  const z2on = ok("Z2POW") && ok("Z2POW").raw === "1";
  tiles.push(tile("Zone 2", z2on ? inputName(2) : txt("Z2POW"), z2on ? txt("Z2VOL") : "", z2on ? "ok" : "off"));
  // Sundhed: hardwarefejl, Wi-Fi, log mode
  const hw = [...state.values.values()].filter((v) => v.group === "faults").sort((a, b) => a.code.localeCompare(b.code))
    .slice(0, HARDWARE_FAULT_COUNT);
  const hwFaults = hw.filter((v) => v.status === "ok" && v.raw.trim() !== "0").length;
  const health = hw.length === 0 ? "—" : hwFaults ? `${hwFaults} hardware fault${hwFaults > 1 ? "s" : ""}` : "No hardware faults";
  const wifi = ok("@WIFI_QUALITY") ? `Wi-Fi ${txt("@WIFI_QUALITY")}${ok("@WIFI_SIGNAL") ? ` (${txt("@WIFI_SIGNAL")})` : ""}` : "";
  const rec = state.logmode && state.logmode.active ? "Log mode REC" : "";
  tiles.push(tile("Health", health, [wifi, rec].filter(Boolean).join(" · "), hw.length === 0 ? "" : hwFaults ? "bad" : "ok"));
  $("#tiles").replaceChildren(...tiles);
}

// ---------------------------------------------------------------- render: log

const KIND_TEXT = { change: "Change", connection: "Connection", error: "Error", info: "Info" };

function logRow(e) {
  return el("tr", { class: `kind-${e.kind}` },
    el("td", { class: "ts" }, fmtTime(e.ts)),
    el("td", {}, KIND_TEXT[e.kind] || e.kind),
    el("td", {}, e.source ? (SOURCE_TEXT[e.source] || e.source) : ""),
    el("td", {}, e.text),
  );
}

function renderLog() {
  const onlyChanges = $("#log-changes-only").checked;
  const rows = state.log.filter((e) => !onlyChanges || e.kind === "change").slice(-500).reverse();
  $("#log-body").replaceChildren(...rows.map(logRow));
}

function addLog(e) {
  state.log.push(e);
  if (state.log.length > 1000) state.log.shift();
  if ($("#log-changes-only").checked && e.kind !== "change") return;
  const body = $("#log-body");
  body.prepend(logRow(e));
  while (body.childElementCount > 500) body.lastElementChild.remove();
}

// ---------------------------------------------------------------- render: traffic

function trafficVisible(t) {
  return !($("#traffic-hide-poll").checked && t.origin === "poll");
}

function trafficLine(t) {
  const isPush = t.dir === "rx" && t.origin === "push";
  const cls = t.dir === "tx" ? "tx" : isPush ? "rx-push" : "rx";
  const arrow = t.dir === "tx" ? "→" : "←";
  const tag = t.dir === "rx" && isPush ? " [push]" : t.origin !== "push" ? ` [${SOURCE_TEXT[t.origin] || t.origin}]` : "";
  return el("div", { class: cls }, el("span", { class: "ts" }, fmtTime(t.ts) + " "), `${arrow} ${t.line}${tag}`);
}

function renderTraffic() {
  const lines = state.traffic.filter(trafficVisible).slice(-600);
  const pre = $("#traffic-body");
  pre.replaceChildren(...lines.map(trafficLine));
  pre.scrollTop = pre.scrollHeight;
}

function addTraffic(t) {
  state.traffic.push(t);
  if (state.traffic.length > 2000) state.traffic.shift();
  if ($("#traffic-pause").checked || !trafficVisible(t)) return;
  const pre = $("#traffic-body");
  const atBottom = pre.scrollHeight - pre.scrollTop - pre.clientHeight < 30;
  pre.append(trafficLine(t));
  while (pre.childElementCount > 600) pre.firstElementChild.remove();
  if (atBottom) pre.scrollTop = pre.scrollHeight;
}

// ---------------------------------------------------------------- SSE

function applySnapshot(s) {
  state.connection = s.connection;
  state.settings = s.settings;
  state.groups = s.groups;
  state.values = new Map(s.values.map((v) => [v.code, v]));
  state.log = s.log;
  state.traffic = s.traffic;
  state.changelog = s.changelog || state.changelog;
  state.faults = s.faults || {};
  mergeLogmode(s.logmode || null);
  renderConnection();
  renderChangelog();
  renderLogmode();
  renderCards();
  renderLog();
  renderTraffic();
}

function connectEvents() {
  const es = new EventSource("/api/events");
  es.addEventListener("reset", (e) => applySnapshot(JSON.parse(e.data)));
  es.addEventListener("connection", (e) => { state.connection = JSON.parse(e.data); renderConnection(); });
  es.addEventListener("value", (e) => updateValue(JSON.parse(e.data)));
  es.addEventListener("log", (e) => addLog(JSON.parse(e.data)));
  es.addEventListener("traffic", (e) => addTraffic(JSON.parse(e.data)));
  es.addEventListener("changelog", (e) => { state.changelog = JSON.parse(e.data); renderChangelog(); });
  es.addEventListener("changelog_entry", (e) => addChangelogEntry(JSON.parse(e.data)));
  es.addEventListener("logmode", (e) => { mergeLogmode(JSON.parse(e.data)); renderLogmode(); });
  es.addEventListener("logmode_line", (e) => addLogmodeLine(JSON.parse(e.data)));
  es.addEventListener("faults", (e) => { state.faults = JSON.parse(e.data); renderCards(); });
  es.addEventListener("logmode_counts", (e) => {
    if (state.logmode) { state.logmode.counts = JSON.parse(e.data); renderLogmodeStatus(); }
  });
  es.onerror = () => {
    // EventSource genforbinder selv; vis kun at backend er væk.
    const pill = $("#conn-pill");
    pill.dataset.status = "disconnected";
    pill.textContent = "No contact with app backend";
  };
}

// ---------------------------------------------------------------- actions

async function action(btn, fn) {
  btn.disabled = true;
  try { await fn(); }
  catch (err) { toast(err.message, true); }
  finally {
    // Slå knappen til igen; renderConnection() slår derefter de
    // forbindelsesafhængige knapper fra igen, hvis de skal være det.
    btn.disabled = false;
    renderConnection();
  }
}

$("#btn-conn").onclick = (e) => action(e.currentTarget, () =>
  api("POST", state.connection && state.connection.status !== "disconnected" ? "/api/disconnect" : "/api/connect"));
$("#btn-refresh").onclick = (e) => action(e.currentTarget, async () => {
  await api("POST", "/api/refresh");
  toast("All values re-queried");
});

// tabs
for (const tab of document.querySelectorAll(".tabs button")) {
  tab.onclick = () => {
    for (const t of document.querySelectorAll(".tabs button")) {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on));
      $(`#tab-${t.dataset.tab}`).hidden = !on;
    }
    if (tab.dataset.tab === "traffic") renderTraffic();
  };
}

$("#log-changes-only").onchange = renderLog;
$("#log-clear").onclick = () => { state.log = []; renderLog(); };
$("#traffic-hide-poll").onchange = renderTraffic;
$("#traffic-pause").onchange = () => { if (!$("#traffic-pause").checked) renderTraffic(); };
$("#traffic-clear").onclick = () => { state.traffic = []; renderTraffic(); };

// konsol
$("#console-form").onsubmit = async (e) => {
  e.preventDefault();
  const input = $("#console-input");
  // Intet automatisk "?": en set-kommando som Z1POW1 må ikke stille blive
  // til en forespørgsel — backend afviser den med en tydelig besked.
  const cmd = input.value.trim();
  if (cmd === "") return;
  const out = $("#console-out");
  try {
    const r = await api("POST", "/api/query", { command: cmd });
    let text;
    if (r.status === "ok") text = `${r.code}? → ${JSON.stringify(r.value)}${r.decoded && r.decoded !== r.value ? `  (${r.decoded})` : ""}`;
    else text = `${r.code}? → ${r.status_text || r.status}${r.raw ? `  [${r.raw}]` : ""}`;
    out.prepend(el("div", { class: r.status === "ok" ? "st-ok" : "st-warn" }, text));
  } catch (err) {
    out.prepend(el("div", { class: "st-bad" }, `${cmd} → ${err.message}`));
  }
  input.select();
};

// probe
$("#btn-probe").onclick = (e) => action(e.currentTarget, async () => {
  e.currentTarget.textContent = "Probe running…";
  try {
    const rows = await api("POST", "/api/probe");
    const body = $("#probe-body");
    body.replaceChildren(...rows.map((r) => el("tr", {},
      el("td", { class: "code" }, r.code),
      el("td", {}, r.label),
      el("td", { class: r.status === "ok" ? "st-ok" : r.status === "invalid" ? "st-bad" : "st-warn" },
        r.status === "ok" ? "OK" : (r.status_text || r.status)),
      el("td", { class: "code" }, r.value === null ? "" : JSON.stringify(r.value)),
      el("td", {}, r.decoded ?? ""),
    )));
    $("#probe-table").hidden = false;
    const ok = rows.filter((r) => r.status === "ok").length;
    toast(`Probe finished: ${ok} of ${rows.length} commands answered`);
  } finally {
    $("#btn-probe").textContent = "Run probe";
  }
});

// ---------------------------------------------------------------- setup dialog

const dialog = $("#setup");
const form = $("#setup-form");

function fillForm(s) {
  for (const [k, v] of Object.entries(s)) {
    const input = form.elements.namedItem(k);
    if (!input) continue;
    if (input.type === "checkbox") input.checked = Boolean(v);
    else input.value = v;
  }
}

function readForm() {
  const f = form.elements;
  return {
    host: f.host.value,
    port: Number(f.port.value),
    poll_interval: Number(f.poll_interval.value),
    connect_timeout: Number(f.connect_timeout.value),
    query_timeout: Number(f.query_timeout.value),
    auto_reconnect: f.auto_reconnect.checked,
    auto_connect: f.auto_connect.checked,
    log_poll_interval: Number(f.log_poll_interval.value),
    owner: f.owner.value,
  };
}

function setupResult(text, ok) {
  const box = $("#setup-result");
  box.textContent = text;
  box.className = "setup-result " + (ok === true ? "ok" : ok === false ? "bad" : "");
  box.hidden = false;
}

$("#btn-setup").onclick = async () => {
  $("#setup-result").hidden = true;
  try {
    fillForm(await api("GET", "/api/settings"));
  } catch (err) {
    toast(err.message, true);
    return;
  }
  dialog.showModal();
};
$("#setup-cancel").onclick = () => dialog.close();

$("#setup-test").onclick = async (e) => {
  const btn = e.currentTarget;
  btn.disabled = true;
  setupResult("Testing the connection…", null);
  try {
    const r = await api("POST", "/api/settings/test", readForm());
    setupResult(r.message, r.ok);
  } catch (err) {
    setupResult(err.message, false);
  } finally {
    btn.disabled = false;
  }
};

$("#setup-reset").onclick = async () => {
  if (!confirm("Reset to the default values from .env?")) return;
  try {
    state.settings = await api("POST", "/api/settings/reset");
    fillForm(state.settings);
    setupResult("Defaults restored and saved", true);
  } catch (err) {
    setupResult(err.message, false);
  }
};

form.onsubmit = async (e) => {
  e.preventDefault();
  if (!form.reportValidity()) return;
  try {
    state.settings = await api("PUT", "/api/settings", readForm());
    dialog.close();
    toast("Setup saved");
  } catch (err) {
    setupResult(err.message, false);
  }
};

// ---------------------------------------------------------------- versioner og netværk (kort på Device-siden)

let appVersion = null;

/** Versionskortets sektioner (enhedens identitet står i System-kortet). */
function versionSections() {
  const versionValues = groupValues("version");
  const module = versionValues.filter((v) => /^(NMSVER|NMHVER|RVER|RBD|NMR)$/.test(v.code));
  return [
    ["Device", versionValues.filter((v) => !module.includes(v))],
    ["Network module", module],
  ];
}

function versionText(v) {
  if (v.raw === null || v.raw === undefined) return v.status === "unknown" ? "—" : (v.status_text || v.status);
  if (v.raw.trim() === "") return "(not set)";
  return v.text;
}

function versionsAsText() {
  const lines = [
    `AVM70 Diagnostics: v${appVersion?.version ?? "?"} build ${appVersion?.build ?? "?"}`,
    `System owner: ${(state.settings && state.settings.owner) || "-"}`,
    `Model: ${txt("IDM", "-")}`,
    `Device name: ${txt("GCDN", "-")}`,
  ];
  for (const [title, values] of versionSections()) {
    lines.push("", `[${title}]`);
    for (const v of values) lines.push(`${v.label} (${v.code}): ${versionText(v)}`);
  }
  return lines.join("\n");
}

/** Clipboard-API'et findes kun i en "secure context" (https/localhost) —
 *  ellers falder vi tilbage til execCommand("copy") via et skjult tekstfelt. */
async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const ta = el("textarea", { readonly: "", style: "position:fixed;top:0;left:0;opacity:0" });
  ta.value = text;
  document.body.append(ta);
  ta.select();
  ta.setSelectionRange(0, text.length);
  const done = document.execCommand("copy");
  ta.remove();
  if (!done) throw new Error("The browser did not allow copying — select the text manually");
}

const NETWORK_SECTIONS = [
  ["Control protocol", ["NMST", "GCIPSTT", "GCIPSTM", "GCIPSTI", "GCIPSTS", "GCIPSTG", "GCIPSDN", "EMAC", "WMAC", "GCTXS"]],
  ["Wi-Fi", ["@NET_STATE", "@WIFI_STATE", "@WIFI_SSID", "@WIFI_BSSID", "@WIFI_IP", "@WIFI_BAND",
    "@WIFI_CHANNEL", "@WIFI_SIGNAL", "@WIFI_QUALITY", "@WIFI_SECURITY", "@WIFI_CREDENTIALS"]],
  ["Ethernet and other", ["@WIRED_CABLE", "@WIRED_STATE", "@WIRED_IP", "@GATEWAYS", "@DNS", "@SOFTAP"]],
];

// ---------------------------------------------------------------- sider og "Codes"-kontakt (FEATURES #23)

const PAGES = ["overview", "device", "logs", "tools"];

function showPage(page) {
  if (!PAGES.includes(page)) page = "overview";
  for (const p of PAGES) $(`#page-${p}`).hidden = p !== page;
  for (const b of document.querySelectorAll(".pages button")) {
    if (b.dataset.page === page) b.setAttribute("aria-current", "page");
    else b.removeAttribute("aria-current");
  }
  if (page === "logs") renderTraffic();
  if (location.hash !== `#${page}`) history.replaceState(null, "", `#${page}`);
}

for (const b of document.querySelectorAll(".pages button")) b.onclick = () => showPage(b.dataset.page);
window.addEventListener("hashchange", () => showPage(location.hash.slice(1)));

function applyShowCodes(on) {
  document.body.classList.toggle("show-codes", on);
  $("#show-codes").checked = on;
}
$("#show-codes").onchange = (e) => {
  applyShowCodes(e.currentTarget.checked);
  try { localStorage.setItem("avm70.showCodes", e.currentTarget.checked ? "1" : "0"); }
  catch { /* privat vindue/blokeret lager — kontakten virker stadig for denne visning */ }
};

// ---------------------------------------------------------------- rapport (FEATURES #12)

/** Henter diagnoserapporten og gemmer den som fil. fetch + blob i stedet
 *  for et almindeligt link, så en fejl fra backend kan vises som toast. */
async function downloadFile(path, fallbackName) {
  let res;
  try {
    res = await fetch(path);
  } catch (err) {
    throw new Error(`Cannot reach the app backend (${err.message})`);
  }
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try { const d = await res.json(); if (typeof d.detail === "string") msg = d.detail; } catch { /* ikke-JSON fejlsvar — HTTP-status er det bedste vi har */ }
    throw new Error(msg);
  }
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match ? match[1] : fallbackName;
  const url = URL.createObjectURL(await res.blob());
  const a = el("a", { href: url, download: filename });
  document.body.append(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
  return filename;
}

/** Kører appen som Windows-app (exe), gemmes rapporten via en rigtig
 *  "Save as"-dialog i launcheren — WebView2 dropper blob-downloads stille. */
function desktopApi() {
  return window.pywebview && window.pywebview.api && window.pywebview.api.save ? window.pywebview.api : null;
}

/** Gem en eksport ("report" | "changelog"): "Save As" i app-vinduet,
 *  almindelig download i browseren. */
async function saveExport(kind, path, fallbackName) {
  const desktop = desktopApi();
  if (desktop) {
    let r;
    try { r = await desktop.save(kind); }
    catch (err) { throw new Error((err && err.message) || String(err)); }
    if (r && r.saved) toast(`Saved: ${r.path}`);
    return;  // annulleret "Save as" er ikke en fejl
  }
  const name = await downloadFile(path, fallbackName);
  toast(`Downloaded: ${name}`);
}

$("#btn-report").onclick = (e) => {
  const btn = e.currentTarget;
  btn.textContent = "⬇ Preparing…";
  action(btn, () => saveExport("report", "/api/export", "AVM70_report.txt"))
    .finally(() => { btn.textContent = "⬇ Report"; });
};

// ---------------------------------------------------------------- ændringslog (FEATURES #14)

const GROUP_TITLE = (g) => state.groups[g] || g;

function shownValue(text, raw) {
  if (raw === null || raw === undefined) return "—";
  if (raw.trim() === "") return "(not set)";
  return text ?? raw;
}

function changelogRow(e) {
  if (e.kind === "connection") {
    return el("tr", { class: "cl-marker" }, el("td", { class: "ts" }, fmtTime(e.ts)), el("td", { colspan: "4" }, e.text));
  }
  const to = shownValue(e.new_text, e.new_raw);
  return el("tr", { class: e.kind === "first" ? "cl-first" : "" },
    el("td", { class: "ts" }, fmtTime(e.ts)),
    el("td", {}, SOURCE_TEXT[e.source] || e.source),
    el("td", {}, `${e.label} `, el("span", { class: "raw" }, e.code)),
    el("td", {}, e.kind === "first" ? "(first value)" : shownValue(e.old_text, e.old_raw)),
    el("td", {}, to),
  );
}

function renderChangelogStatus() {
  const cl = state.changelog;
  const changes = cl.entries.filter((e) => e.kind !== "connection").length;
  $("#cl-status").textContent = cl.started_at
    ? `Started ${new Date(cl.started_at).toLocaleString("en-GB", { hour12: false })} · ${cl.baseline.length} initial values · ${changes} change${changes === 1 ? "" : "s"}`
      + (cl.dropped ? ` · oldest ${cl.dropped} dropped` : "")
    : "Not started yet — starts after the first complete read of the device.";
  $("#cl-baseline-title").textContent = `Initial values (${cl.baseline.length})`;
}

function renderChangelog() {
  const cl = state.changelog;
  renderChangelogStatus();
  $("#cl-baseline-body").replaceChildren(...cl.baseline.map((v) => el("tr", {},
    el("td", {}, GROUP_TITLE(v.group)),
    el("td", {}, v.label),
    el("td", {}, shownValue(v.text, v.raw)),
    el("td", { class: "code" }, v.code),
  )));
  const rows = cl.entries.slice(-1000).reverse().map(changelogRow);
  $("#cl-body").replaceChildren(...(rows.length ? rows
    : [el("tr", {}, el("td", { colspan: "5", class: "empty" }, cl.started_at ? "No changes since the log started." : "—"))]));
}

function addChangelogEntry(e) {
  state.changelog.entries.push(e);
  if (state.changelog.entries.length > 20000) state.changelog.entries.shift();
  const body = $("#cl-body");
  if (body.querySelector("td.empty")) body.replaceChildren();
  body.prepend(changelogRow(e));
  while (body.childElementCount > 1000) body.lastElementChild.remove();
  renderChangelogStatus();
}

$("#cl-save").onclick = (e) => action(e.currentTarget, () => saveExport("changelog", "/api/changelog/export", "AVM70_changelog.txt"));
$("#cl-new").onclick = (e) => {
  if (!confirm("Start a new change log? The current initial values and logged changes are cleared (save them first if you need them).")) return;
  action(e.currentTarget, async () => {
    state.changelog = await api("POST", "/api/changelog/reset");
    renderChangelog();
    toast(state.changelog.started_at ? "New change log started" : "The log starts after the next complete read");
  });
};

// ---------------------------------------------------------------- log mode (FEATURES #15)

function logmodeLine(e) {
  const block = el("div", { class: `k-${e.kind}` }, e.line);
  if (!e.detail || e.detail.length === 0) return block;
  const indent = " ".repeat(37);  // tid (23) + 2 + type-kolonne (12), som i filen
  return el("div", {}, block, ...e.detail.map((d) => el("div", { class: "detail" }, indent + d)));
}

const lastSeq = (lm) => (lm && lm.lines.length ? lm.lines[lm.lines.length - 1].seq : 0);

/** BUGS.md #3: et HTTP-svar eller et øjebliksbillede kan være ÆLDRE end de
 *  linjer SSE allerede har leveret. Behold de nyeste linjer for samme session. */
function mergeLogmode(next) {
  const cur = state.logmode;
  if (cur && next && cur.started_at === next.started_at && lastSeq(cur) > lastSeq(next)) {
    next = { ...next, lines: cur.lines };
  }
  state.logmode = next;
}

function renderLogmodeStatus() {
  const lm = state.logmode;
  const active = Boolean(lm && lm.active);
  $("#lm-rec").hidden = !active;
  const btn = $("#lm-toggle");
  btn.textContent = active ? "Disable log mode" : "Enable log mode";
  btn.classList.toggle("primary", !active);
  $("#lm-save").disabled = !lm;
  if (!lm) {
    $("#lm-status").textContent = "Polls every parameter at a fixed interval and logs INIT, then OK or the changes.";
    $("#lm-file").textContent = "";
    return;
  }
  const c = lm.counts || {};
  const when = new Date(lm.started_at).toLocaleString("en-GB", { hour12: false });
  $("#lm-status").textContent = `${active ? "Logging" : "Stopped"} · every ${lm.interval} s · started ${when} · `
    + `${c.cycles || 0} polls, ${c.ok || 0} OK, ${c.changes || 0} changes, ${c.push || 0} push, ${c.incomplete || 0} incomplete`;
  $("#lm-file").textContent = lm.file ? `Recording to: ${lm.file}` : "";
}

function renderLogmode() {
  renderLogmodeStatus();
  const lm = state.logmode;
  const pre = $("#lm-body");
  pre.replaceChildren(...(lm ? lm.lines.map(logmodeLine) : []));
  if ($("#lm-follow").checked) pre.scrollTop = pre.scrollHeight;
}

function addLogmodeLine(e) {
  if (!state.logmode) return;
  if (e.seq <= lastSeq(state.logmode)) return;  // allerede vist (BUGS.md #3)
  state.logmode.lines.push(e);
  if (state.logmode.lines.length > 2000) state.logmode.lines.shift();
  if (e.kind === "stopped") state.logmode.active = false;
  const pre = $("#lm-body");
  pre.append(logmodeLine(e));
  while (pre.childElementCount > 2000) pre.firstElementChild.remove();
  if ($("#lm-follow").checked) pre.scrollTop = pre.scrollHeight;
  renderLogmodeStatus();
}

$("#lm-toggle").onclick = (e) => action(e.currentTarget, async () => {
  const active = state.logmode && state.logmode.active;
  mergeLogmode(await api("POST", active ? "/api/logmode/stop" : "/api/logmode/start"));
  renderLogmode();
  toast(active ? "Log mode stopped" : `Log mode started — polling every ${state.logmode.interval} s`);
});
$("#lm-save").onclick = (e) => action(e.currentTarget, () => saveExport("logmode", "/api/logmode/export", "AVM70_log.txt"));
$("#lm-setup").onclick = () => $("#btn-setup").click();

// ---------------------------------------------------------------- start

(async () => {
  let showCodes = false;
  try { showCodes = localStorage.getItem("avm70.showCodes") === "1"; }
  catch { /* privat vindue/blokeret lager — standard er skjulte koder */ }
  applyShowCodes(showCodes);
  showPage(location.hash.slice(1) || "overview");
  try {
    const info = await api("GET", "/api/info");
    appVersion = info.app;
    $("#app-version").textContent = `v${info.app.version} build ${info.app.build}`;
  } catch (err) {
    toast(err.message, true);
  }
  connectEvents();
  // "x s siden" i tooltips og fejlbanneret holdes friske uden fuld gen-render.
  setInterval(() => { for (const v of state.values.values()) { const r = document.getElementById(`row-${v.code}`); if (r) fillRow(r, v); } }, 10000);
})();
