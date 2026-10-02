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
  disconnected: "Afbrudt",
  connecting: "Forbinder…",
  reconnecting: "Genforbinder…",
  connected: "Forbundet",
};
const SOURCE_TEXT = { push: "push", poll: "poll", refresh: "opdatering", console: "konsol", probe: "probe", test: "test" };
const GROUP_ORDER = ["system", "inputs", "zone1", "audio", "video", "zone2"];

function fmtTime(iso) {
  const d = new Date(iso);
  return d.toLocaleTimeString("da-DK", { hour12: false }) + "." + String(d.getMilliseconds()).padStart(3, "0");
}

function ago(iso) {
  if (!iso) return "";
  const s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
  if (s < 60) return `${s} s siden`;
  if (s < 3600) return `${Math.floor(s / 60)} min siden`;
  return `${Math.floor(s / 3600)} t siden`;
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
    throw new Error(`Kan ikke nå appens backend (${err.message})`);
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
};

// ---------------------------------------------------------------- render: connection

function renderConnection() {
  const c = state.connection;
  if (!c) return;
  const pill = $("#conn-pill");
  pill.dataset.status = c.status;
  pill.textContent = STATUS_TEXT[c.status] || c.status;
  $("#conn-target").textContent = `${c.host}:${c.port}`;
  const running = c.status !== "disconnected";
  $("#btn-connect").disabled = running;
  $("#btn-disconnect").disabled = !running;
  $("#btn-refresh").disabled = c.status !== "connected";
  $("#btn-probe").disabled = c.status !== "connected";

  const banner = $("#conn-error");
  if (c.last_error && c.status !== "connected") {
    let text = c.last_error;
    if (c.status === "reconnecting" && c.next_retry_s) text += ` — nyt forsøg om ${c.next_retry_s} s`;
    banner.textContent = text;
    banner.hidden = false;
  } else {
    banner.hidden = true;
  }
}

// ---------------------------------------------------------------- render: cards

function renderCards() {
  const host = $("#cards");
  host.replaceChildren();
  const byGroup = new Map(GROUP_ORDER.map((g) => [g, []]));
  for (const v of state.values.values()) {
    if (!byGroup.has(v.group)) byGroup.set(v.group, []);
    byGroup.get(v.group).push(v);
  }
  for (const [group, values] of byGroup) {
    const card = el("article", { class: "card", dataset: { group } }, el("h2", {}, state.groups[group] || group));
    if (group === "inputs") values.sort((a, b) => inputOrder(a.code) - inputOrder(b.code));
    if (values.length === 0) {
      card.append(el("p", { class: "empty" }, group === "inputs" ? "Hentes når antal inputs er kendt" : "Ingen data"));
    } else {
      const dl = el("dl", { class: "rows" });
      for (const v of values) dl.append(renderRow(v));
      card.append(dl);
    }
    host.append(card);
  }
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
  const val = el("span", { class: "val" });
  if (v.raw === null || v.raw === undefined) {
    val.textContent = v.status === "unknown" ? "—" : "";
  } else {
    val.textContent = v.text === "" ? "(tom)" : v.text;
  }
  const dd = el("dd", {}, val);
  if (v.status !== "ok" && v.status !== "unknown") {
    dd.append(" ", el("span", { class: "state" }, v.status_text || v.status));
  }
  const rawText = `${v.code}${v.raw !== null && v.raw !== undefined ? " = " + JSON.stringify(v.raw) : ""}`;
  dd.append(el("span", { class: "raw" }, rawText));
  row.replaceChildren(el("dt", {}, v.label), dd);
  row.classList.toggle("stale", v.status !== "ok" && v.raw !== null);
  row.title = [
    v.updated_at ? `Seneste svar: ${fmtTime(v.updated_at)} (${SOURCE_TEXT[v.source] || v.source || ""})` : "",
    v.changed_at ? `Seneste ændring: ${fmtTime(v.changed_at)} — ${ago(v.changed_at)}` : "",
  ].filter(Boolean).join("\n");
}

function updateValue(v) {
  const prev = state.values.get(v.code);
  state.values.set(v.code, v);
  const row = document.getElementById(`row-${v.code}`);
  if (!row) { renderCards(); return; }
  fillRow(row, v);
  if (prev && prev.raw !== null && prev.raw !== v.raw) {
    row.classList.remove("flash");
    void row.offsetWidth; // genstart overgangen
    row.classList.add("flash");
    setTimeout(() => row.classList.remove("flash"), 60);
  }
}

// ---------------------------------------------------------------- render: log

const KIND_TEXT = { change: "Ændring", connection: "Forbindelse", error: "Fejl", info: "Info" };

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
  renderConnection();
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
  es.onerror = () => {
    // EventSource genforbinder selv; vis kun at backend er væk.
    const pill = $("#conn-pill");
    pill.dataset.status = "disconnected";
    pill.textContent = "Ingen kontakt til app-backend";
  };
}

// ---------------------------------------------------------------- actions

async function action(btn, fn) {
  btn.disabled = true;
  try { await fn(); }
  catch (err) { toast(err.message, true); }
  finally { renderConnection(); }
}

$("#btn-connect").onclick = (e) => action(e.currentTarget, () => api("POST", "/api/connect"));
$("#btn-disconnect").onclick = (e) => action(e.currentTarget, () => api("POST", "/api/disconnect"));
$("#btn-refresh").onclick = (e) => action(e.currentTarget, async () => {
  await api("POST", "/api/refresh");
  toast("Alle værdier genforespurgt");
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
  e.currentTarget.textContent = "Probe kører…";
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
    toast(`Probe færdig: ${ok} af ${rows.length} kommandoer svarede`);
  } finally {
    $("#btn-probe").textContent = "Kør probe";
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
  setupResult("Tester forbindelsen…", null);
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
  if (!confirm("Nulstil til standardværdierne fra .env?")) return;
  try {
    fillForm(await api("POST", "/api/settings/reset"));
    setupResult("Standardværdier gendannet og gemt", true);
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
    toast("Opsætning gemt");
  } catch (err) {
    setupResult(err.message, false);
  }
};

// ---------------------------------------------------------------- start

(async () => {
  try {
    const info = await api("GET", "/api/info");
    $("#app-version").textContent = `v${info.app.version} build ${info.app.build}`;
  } catch (err) {
    toast(err.message, true);
  }
  connectEvents();
  // "x s siden" i tooltips og fejlbanneret holdes friske uden fuld gen-render.
  setInterval(() => { for (const v of state.values.values()) { const r = document.getElementById(`row-${v.code}`); if (r) fillRow(r, v); } }, 10000);
})();
