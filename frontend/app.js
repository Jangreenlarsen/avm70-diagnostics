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
const GROUP_ORDER = ["system", "inputs", "zone1", "audio", "video", "zone2"];
// Grupper der ikke vises som kort på forsiden (har deres egen menu).
const MENU_GROUPS = new Set(["version"]);

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
    if (c.status === "reconnecting" && c.next_retry_s) text += ` — retrying in ${c.next_retry_s} s`;
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
    if (MENU_GROUPS.has(v.group)) continue;
    if (!byGroup.has(v.group)) byGroup.set(v.group, []);
    byGroup.get(v.group).push(v);
  }
  for (const [group, values] of byGroup) {
    const card = el("article", { class: "card", dataset: { group } }, el("h2", {}, state.groups[group] || group));
    if (group === "inputs") values.sort((a, b) => inputOrder(a.code) - inputOrder(b.code));
    if (values.length === 0) {
      card.append(el("p", { class: "empty" }, group === "inputs" ? "Read once the input count is known" : "No data"));
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
    val.textContent = v.text === "" ? "(empty)" : v.text;
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
    v.updated_at ? `Last response: ${fmtTime(v.updated_at)} (${SOURCE_TEXT[v.source] || v.source || ""})` : "",
    v.changed_at ? `Last change: ${fmtTime(v.changed_at)} — ${ago(v.changed_at)}` : "",
  ].filter(Boolean).join("\n");
}

function updateValue(v) {
  const prev = state.values.get(v.code);
  state.values.set(v.code, v);
  if (MENU_GROUPS.has(v.group)) {
    if ($("#versions").open) renderVersions();
    return;
  }
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
  renderConnection();
  renderChangelog();
  renderCards();
  renderLog();
  renderTraffic();
  if ($("#versions").open) renderVersions();
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

$("#btn-connect").onclick = (e) => action(e.currentTarget, () => api("POST", "/api/connect"));
$("#btn-disconnect").onclick = (e) => action(e.currentTarget, () => api("POST", "/api/disconnect"));
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
    fillForm(await api("POST", "/api/settings/reset"));
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

// ---------------------------------------------------------------- versionsmenu

let appVersion = null;

/** Rækkerne i versionsmenuen: appen selv, enhedens identitet og alle
 *  koder i "version"-gruppen (i katalogets rækkefølge). */
function versionSections() {
  const pick = (codes) => codes.map((c) => state.values.get(c)).filter(Boolean);
  const versionValues = [...state.values.values()].filter((v) => v.group === "version");
  const network = versionValues.filter((v) => /^(NMSVER|NMHVER|RVER|RBD|NMR)$/.test(v.code));
  const device = versionValues.filter((v) => !network.includes(v));
  return [
    ["Device", [...pick(["IDM", "GCDN"]), ...device]],
    ["Network module", [...network, ...pick(["NMST"])]],
  ];
}

function versionText(v) {
  if (v.raw === null || v.raw === undefined) return v.status === "unknown" ? "—" : (v.status_text || v.status);
  if (v.raw.trim() === "") return "(not set)";
  return v.text;
}

function renderVersions() {
  const body = $("#versions-body");
  const children = [el("div", { class: "section" }, "This app")];
  children.push(el("div", { class: "row" },
    el("dt", {}, "AVM70 Diagnostics"),
    el("dd", {}, el("span", { class: "val" }, appVersion ? `v${appVersion.version} build ${appVersion.build}` : "—")),
  ));
  for (const [title, values] of versionSections()) {
    children.push(el("div", { class: "section" }, title));
    for (const v of values) {
      const dd = el("dd", {}, el("span", { class: "val" }, versionText(v)));
      if (v.status !== "ok" && v.status !== "unknown" && v.raw !== null) dd.append(" ", el("span", { class: "state" }, v.status_text || v.status));
      dd.append(el("span", { class: "raw" }, v.code));
      children.push(el("div", { class: "row" }, el("dt", {}, v.label), dd));
    }
  }
  body.replaceChildren(...children);
  const c = state.connection;
  $("#versions-refresh").disabled = !c || c.status !== "connected";
  $("#versions-hint").textContent = c && c.status === "connected"
    ? `Read from ${c.host}:${c.port}. "Refresh" queries the device again.`
    : "Not connected — showing the most recently read values.";
}

function versionsAsText() {
  const lines = [`AVM70 Diagnostics: v${appVersion?.version ?? "?"} build ${appVersion?.build ?? "?"}`];
  for (const [title, values] of versionSections()) {
    lines.push("", `[${title}]`);
    for (const v of values) lines.push(`${v.label} (${v.code}): ${versionText(v)}`);
  }
  return lines.join("\n");
}

/** Clipboard-API'et findes kun i en "secure context" (https/localhost) —
 *  åbnes appen fra mobilen via http://<pc-ip>:8070, må vi falde tilbage
 *  til det gamle execCommand("copy") via et midlertidigt tekstfelt. */
async function copyText(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }
  const ta = el("textarea", { readonly: "", style: "position:fixed;top:0;left:0;opacity:0" });
  ta.value = text;
  $("#versions").append(ta);
  ta.select();
  ta.setSelectionRange(0, text.length);
  const ok = document.execCommand("copy");
  ta.remove();
  if (!ok) throw new Error("The browser did not allow copying — select the text manually");
}

$("#btn-versions").onclick = () => {
  renderVersions();
  $("#versions").showModal();
};
$("#versions-close").onclick = () => $("#versions").close();
$("#versions-refresh").onclick = (e) => action(e.currentTarget, async () => {
  await api("POST", "/api/refresh?group=version");
  renderVersions();
  toast("Versions re-queried");
});
$("#versions-copy").onclick = async () => {
  try {
    await copyText(versionsAsText());
    toast("Version information copied");
  } catch (err) {
    toast(err.message, true);
  }
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

// ---------------------------------------------------------------- start

(async () => {
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
