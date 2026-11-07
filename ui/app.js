// VidForge web UI: drives the repo's GitHub Actions workflows from a static page (GitHub Pages).
import {seal} from "./seal.js";
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const API = "https://api.github.com";
const DRAFT_WF = "draft-video.yml";
const PUBLISH_WF = "publish-video.yml";
const params = new URLSearchParams(location.search);
const DEMO = params.has("demo");

// ------------------------------------------------------------------ option groups
const GROUPS = {
  language: {def: "en", opts: [["en", "English"], ["hi", "हिन्दी"], ["hinglish", "Hinglish"], ["es", "Español"], ["fr", "Français"], ["it", "Italiano"], ["pt", "Português"]]},
  niche: {def: "space", opts: [["space", "Space"], ["science", "Science"], ["tech", "Tech"], ["stories", "Stories"], ["mythology", "Mythology"], ["kids", "Kids"], ["news", "News explained"], ["sports", "Sports"], ["general", "Anything trending"]]},
  format: {def: "auto", opts: [["auto", "Auto"], ["space_facts", "Facts explainer"], ["trend_explainer", "Trend explained"], ["story", "Story"], ["facts_list", "Top list"], ["festival", "Festival story"], ["quiz", "Quiz"], ["kids_learning", "Kids learning"], ["kids_story", "Kids story"]]},
  writer: {def: "claude-opus-5-5", opts: [["claude-opus-5-5", "Opus 5.5"], ["claude-fable-5-1", "Fable 5.1"], ["claude-sonnet-5-5", "Sonnet 5.5"]]},
  voice: {def: "", opts: [["", "Auto"], ["af_heart", "Heart, US"], ["am_michael", "Michael, US"], ["bf_emma", "Emma, UK"], ["bm_george", "George, UK"], ["hm_omega", "Omega, Hindi"], ["hf_alpha", "Alpha, Hindi"]]},
  music: {def: "", opts: [["", "Auto"], ["cosmic", "Cosmic"], ["mystery", "Mystery"], ["epic", "Epic"], ["upbeat", "Upbeat"], ["calm", "Calm"], ["playful", "Playful"], ["indian", "Indian"], ["devotional", "Devotional"], ["none", "No music"]]},
  aspect: {def: "9:16", opts: [["9:16", "Short 9:16"], ["16:9", "Long 16:9"], ["1:1", "Square"]]},
  length: {def: "", opts: [["", "Auto"], ["30", "30s"], ["45", "45s"], ["60", "60s"], ["90", "90s"]]},
  privacy: {def: "public", opts: [["public", "Public"], ["unlisted", "Unlisted"], ["private", "Private"]]},
  dprivacy: {def: "public", opts: [["public", "Public"], ["unlisted", "Unlisted"], ["private", "Private"]]},
  runner: {def: "ubuntu-latest", opts: [["ubuntu-latest", "GitHub standard"], ["ubuntu-24.04", "Ubuntu 24.04"]]},
};
const MUSIC_MOODS = new Set(GROUPS.music.opts.map(o => o[0]));
const groups = {};
const saved = JSON.parse(localStorage.getItem("vf.form") || "{}");

function makeGroup(el) {
  const name = el.dataset.group, spec = GROUPS[name], customKind = el.dataset.custom;
  el.innerHTML = `<span class="group-label" id="gl-${name}">${el.dataset.label}</span><div class="chips" role="group" aria-labelledby="gl-${name}"></div>`;
  const chips = $(".chips", el);
  let customInput = null, value = spec.def, isCustom = false;
  const all = [...spec.opts];
  for (const [v, label] of all) chips.insertAdjacentHTML("beforeend", `<button type="button" class="chip" data-v="${esc(v)}">${esc(label)}</button>`);
  if (customKind) {
    chips.insertAdjacentHTML("beforeend", `<button type="button" class="chip custom" data-custom>Custom</button>`);
    customInput = document.createElement(customKind === "textarea" ? "textarea" : "input");
    if (customKind !== "textarea") customInput.type = customKind === "number" ? "number" : "text";
    customInput.className = "custom-in"; customInput.placeholder = el.dataset.customPlaceholder || "";
    customInput.setAttribute("aria-label", `${el.dataset.label}, custom value`);
    customInput.rows = 2; customInput.hidden = true;
    el.appendChild(customInput);
    customInput.addEventListener("input", () => persist());
  }
  const render = () => {
    $$(".chip", chips).forEach(c => c.setAttribute("aria-pressed", String(c.hasAttribute("data-custom") ? isCustom : !isCustom && c.dataset.v === value)));
    if (customInput) customInput.hidden = !isCustom;
  };
  const persist = () => { if (el.closest("#composeForm")) { saved[name] = api.get(); localStorage.setItem("vf.form", JSON.stringify(saved)) } };
  chips.addEventListener("click", e => {
    const c = e.target.closest(".chip"); if (!c) return;
    if (c.hasAttribute("data-custom")) { isCustom = true; render(); customInput.focus() }
    else { isCustom = false; value = c.dataset.v; render() }
    persist(); el.dispatchEvent(new Event("change"));
  });
  const api = {
    get: () => isCustom ? (customInput.value || "").trim() : value,
    set(v) {
      if (v == null) return;
      if (all.some(o => o[0] === v)) { isCustom = false; value = v } else if (customInput) { isCustom = true; customInput.value = v }
      render();
    },
    isCustom: () => isCustom,
  };
  render();
  return api;
}

// ------------------------------------------------------------------ helpers
function esc(s) { return String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c])) }
const sleep = ms => new Promise(r => setTimeout(r, ms));
const fmtDur = s => s >= 60 ? `${Math.floor(s / 60)}m ${String(Math.round(s % 60)).padStart(2, "0")}s` : `${Math.max(0, Math.round(s))}s`;
const since = iso => (Date.now() - new Date(iso).getTime()) / 1000;
function toast(m) { const t = $("#toast"); t.textContent = m; t.style.display = "block"; clearTimeout(t._h); t._h = setTimeout(() => t.style.display = "none", 4500) }
function rid() {
  const n = new Date(), p = x => String(x).padStart(2, "0");
  return `${n.getFullYear()}${p(n.getMonth() + 1)}${p(n.getDate())}-${p(n.getHours())}${p(n.getMinutes())}-${Math.random().toString(36).slice(2, 6)}`;
}
const ICON = {
  yt: `<svg viewBox="0 0 24 24"><rect x="2" y="5" width="20" height="14" rx="4" fill="#FF3D3D"/><path d="M10 9v6l5-3z" fill="#fff"/></svg>`,
  ig: `<svg viewBox="0 0 24 24" fill="none" stroke="#FF7AB8" stroke-width="2.2"><rect x="3" y="3" width="18" height="18" rx="5.5"/><circle cx="12" cy="12" r="4"/></svg>`,
};

// ------------------------------------------------------------------ config + GitHub API
const cfg = {
  load() {
    const s = JSON.parse(localStorage.getItem("vf.cfg") || sessionStorage.getItem("vf.cfg") || "{}");
    this.repo = s.repo || guessRepo(); this.token = s.token || ""; this.remember = s.remember !== false;
  },
  save() {
    localStorage.removeItem("vf.cfg"); sessionStorage.removeItem("vf.cfg");
    (this.remember ? localStorage : sessionStorage).setItem("vf.cfg", JSON.stringify({repo: this.repo, token: this.token, remember: this.remember}));
  },
};
function guessRepo() {
  const m = location.hostname.match(/^([^.]+)\.github\.io$/), seg = location.pathname.split("/").filter(Boolean)[0];
  return m && seg ? `${m[1]}/${seg}` : "AyushRatan1/vidforge";
}
class GhError extends Error { constructor(status, msg) { super(msg); this.status = status } }
async function gh(path, {method = "GET", body} = {}) {
  if (DEMO) return demoApi(path, method, body);
  const r = await fetch(API + path, {method, cache: "no-store", headers: {
    Authorization: `Bearer ${cfg.token}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
    ...(body ? {"Content-Type": "application/json"} : {})}, body: body ? JSON.stringify(body) : undefined});
  if (!r.ok) { let m = r.statusText; try { m = (await r.json()).message || m } catch (e) {} throw new GhError(r.status, m) }
  return r.status === 204 ? null : r.json();
}
const R = () => `/repos/${cfg.repo}`;
function explain(e) {
  if (e.status === 401) return "GitHub rejected the token. Paste a fresh one in Connect.";
  if (e.status === 403) return "The token is missing a permission. Check the list in Connect.";
  if (e.status === 404) return "Not found. Check the repository name in Connect.";
  if (e.status === 422) return "GitHub refused the request: " + e.message;
  return e.message || String(e);
}

// ------------------------------------------------------------------ tabs
function showTab(name) {
  for (const t of ["create", "library", "connect"]) {
    $("#p-" + t).hidden = t !== name;
    $("#tab-" + t).setAttribute("aria-selected", String(t === name));
  }
  if (location.hash !== "#" + name) history.replaceState(null, "", location.pathname + location.search + "#" + name);
  if (name === "library") loadLibrary(true);
  if (name === "connect") fillConnect();
}
$$(".tabs button").forEach(b => b.addEventListener("click", () => showTab(b.id.replace("tab-", ""))));
$("#connChip").addEventListener("click", () => showTab("connect"));

// ------------------------------------------------------------------ screen
function frameState({big, small, pct = 0, live = false, video = null, poster = null}) {
  const sc = $("#screen"), fr = $("#frame");
  fr.classList.toggle("live", live);
  $$("video,img,.live-pill", sc).forEach(n => n.remove());
  let msg = $(".msg", sc);
  if (video) {
    msg.hidden = true;
    const v = document.createElement("video");
    Object.assign(v, {src: video, controls: true, playsInline: true, preload: "metadata"});
    if (poster) v.poster = poster;
    sc.appendChild(v);
  } else {
    msg.hidden = false; $("#screenBig").textContent = big || ""; $("#screenSmall").textContent = small || "";
  }
  $("#bar").style.width = pct + "%";
  if (live) sc.insertAdjacentHTML("afterbegin", '<div class="live-pill"><span class="tally"></span>Making on GitHub</div>');
}

// ------------------------------------------------------------------ connection
async function connect(quiet) {
  if (!cfg.token && !DEMO) { setConn("", "Connect GitHub"); return false }
  try {
    const repo = await gh(R());
    setConn("ok", repo.full_name + (repo.private ? " (private)" : ""));
    if (repo.private) toast("Library previews need a public repository; downloads still work from GitHub.");
    refreshSecretBadges();
    return true;
  } catch (e) { setConn("bad", "Connection problem"); if (!quiet) toast(explain(e)); return false }
}
function setConn(state, text) { $("#connDot").className = "dot " + (state || ""); $("#connText").textContent = text }

// ------------------------------------------------------------------ create
function collectOptions() {
  const o = {language: groups.language.get() || "en", niche: groups.niche.get() || "space", format: groups.format.get() || "auto",
    topic: $("#topic").value.trim(), writer: groups.writer.get() || "claude-opus-5-5", aspect: groups.aspect.get()};
  const voice = groups.voice.get(); if (voice) o.voice = voice;
  const music = groups.music.get(); let notes = $("#notes").value.trim();
  if (music) { if (MUSIC_MOODS.has(music)) o.music = music; else notes = (notes ? notes + " " : "") + `Music: ${music}.` }
  const len = groups.length.get(); if (len) o.length = Number(len) || len;
  if ($("#handle").value.trim()) o.handle = $("#handle").value.trim();
  if ($("#hashtags").value.trim()) o.hashtags = $("#hashtags").value.trim();
  if (notes) o.notes = notes;
  const yt = $("#postYT").checked, ig = $("#postIG").checked;
  if (yt || ig) {
    o.publish = {youtube: yt, instagram: ig, privacy: groups.privacy.get() || "public"};
    if ($("#publishAt").value) o.publish.publish_at = new Date($("#publishAt").value).toISOString();
  }
  return o;
}
["topic", "handle", "hashtags", "notes"].forEach(id => $("#" + id).addEventListener("input", e => { saved[id] = e.target.value; localStorage.setItem("vf.form", JSON.stringify(saved)) }));
["postYT", "postIG"].forEach(id => $("#" + id).addEventListener("change", () => { $("#postExtra").hidden = !($("#postYT").checked || $("#postIG").checked) }));

$("#composeForm").addEventListener("submit", async e => {
  e.preventDefault();
  if (!cfg.token && !DEMO) { showTab("connect"); return toast("Connect GitHub first.") }
  const id = rid(), options = collectOptions();
  const btn = $("#makeBtn"); btn.disabled = true; btn.textContent = "Starting…";
  try {
    await gh(`${R()}/actions/workflows/${DRAFT_WF}/dispatches`, {method: "POST", body: {ref: "main", inputs: {request_id: id, options: JSON.stringify(options)}}});
    const job = {kind: "draft", rid: id, options, startedAt: Date.now()};
    localStorage.setItem("vf.active", JSON.stringify(job));
    track(job);
  } catch (err) { toast(explain(err)); resetMake() }
});
function resetMake() { const b = $("#makeBtn"); b.disabled = false; b.textContent = "Make video" }

// ------------------------------------------------------------------ run tracking
const DRAFT_STAGES = [
  {id: "prepare", name: "Prepare machine", screen: "Warming up", hint: "Installing the free voice and video tools."},
  {id: "Find trend", name: "Find trend", screen: "Finding the trend", hint: "Claude is reading what people search right now."},
  {id: "Research", name: "Research", screen: "Checking facts", hint: "Claude is searching the web and collecting sources."},
  {id: "Write and direct", name: "Write and direct", screen: "Writing the script", hint: "Every scene, caption and animation is being directed."},
  {id: "Review frames", name: "Review frames", screen: "Reviewing frames", hint: "Claude looks at the frames and fixes anything off."},
  {id: "Render video", name: "Render video", screen: "Rendering", hint: "Drawing every frame, recording the voice, mixing music."},
  {id: "Write captions and hashtags", name: "Captions and hashtags", screen: "Writing captions", hint: "Titles, captions and hashtags for each platform."},
  {id: "Save to library", name: "Save to library", screen: "Saving", hint: "Adding it to your library."},
  {id: "Post to YouTube and Instagram", name: "Post", screen: "Posting", hint: "Uploading to your accounts."},
];
const PUBLISH_STAGES = [
  {id: "prepare", name: "Prepare machine"}, {id: "Fetch from library", name: "Fetch from library"}, {id: "Post", name: "Post"},
];

async function findRun(workflow, id) {
  for (let i = 0; i < 40; i++) {
    const r = await gh(`${R()}/actions/workflows/${workflow}/runs?event=workflow_dispatch&per_page=20`);
    const run = (r.workflow_runs || []).find(x => (x.display_title || "").includes(id));
    if (run) return run;
    await sleep(3000);
  }
  throw new Error("GitHub didn't start the run. Check the Actions tab of your repository.");
}

function stageView(steps, stages, firstWorkName) {
  const byName = Object.fromEntries(steps.map(s => [s.name, s]));
  const fi = steps.findIndex(s => s.name === firstWorkName);
  const prep = fi > 0 ? steps.slice(0, fi) : steps.filter(s => !stages.some(st => st.id === s.name));
  const view = {};
  for (const st of stages) {
    const ss = st.id === "prepare" ? prep : [byName[st.id]].filter(Boolean);
    let status = "wait", start = null, end = null;
    if (ss.length) {
      if (ss.some(s => s.conclusion === "failure")) status = "fail";
      else if (ss.every(s => s.status === "completed")) status = ss.every(s => s.conclusion === "skipped") ? "skip" : "done";
      else if (ss.some(s => s.status !== "queued" && s.status !== "pending")) status = "run";
      start = ss.map(s => s.started_at).filter(Boolean).sort()[0] || null;
      end = status === "done" ? ss.map(s => s.completed_at).filter(Boolean).sort().pop() : null;
    }
    view[st.id] = {status, start, end};
  }
  return view;
}

let trackToken = null;
async function track(job) {
  const tok = Symbol(); trackToken = tok;
  const isDraft = job.kind === "draft";
  if (isDraft) { const b = $("#makeBtn"); b.disabled = true; b.textContent = "Making your video…"; if ($("#p-create").hidden) showTab("create") }
  if (isDraft) { frameState({big: "Queued", small: "GitHub is picking up the request.", pct: 2, live: true}); renderSteps(job, {}, null) }
  try {
    const wf = isDraft ? DRAFT_WF : PUBLISH_WF;
    const run = job.runId ? await gh(`${R()}/actions/runs/${job.runId}`) : await findRun(wf, job.rid);
    Object.assign(job, {runId: run.id, url: run.html_url}); localStorage.setItem(isDraft ? "vf.active" : "vf.activePub", JSON.stringify(job));
    while (trackToken === tok || !isDraft) {
      const [r, jobs] = await Promise.all([gh(`${R()}/actions/runs/${job.runId}`), gh(`${R()}/actions/runs/${job.runId}/jobs`)]);
      const steps = jobs.jobs?.[0]?.steps || [];
      if (isDraft) {
        const stages = DRAFT_STAGES.filter(s => s.id !== "Post to YouTube and Instagram" || job.options?.publish);
        const view = stageView(steps, stages, "Find trend");
        renderSteps(job, view, r, stages);
        if (r.status === "completed") { localStorage.removeItem("vf.active"); resetMake(); return finishDraft(job, r, view, stages) }
      } else {
        const view = stageView(steps, PUBLISH_STAGES, "Fetch from library");
        const cur = PUBLISH_STAGES.find(s => view[s.id].status === "run");
        pubStatus(r.status === "queued" ? "Queued on GitHub…" : cur ? `${cur.name}…` : "Working…");
        if (r.status === "completed") { localStorage.removeItem("vf.activePub"); return finishPublish(job, r) }
      }
      await sleep(5000);
    }
  } catch (e) {
    if (isDraft) { resetMake(); frameState({big: "Couldn't follow the run", small: explain(e)}) } else pubStatus(explain(e), "bad");
  }
}

function renderSteps(job, view, run, stages = DRAFT_STAGES) {
  const done = stages.filter(s => view[s.id]?.status === "done").length;
  const cur = stages.find(s => view[s.id]?.status === "run");
  const queued = !run || run.status === "queued" || run.status === "waiting" || run.status === "pending";
  if (queued) frameState({big: "Queued", small: "Waiting for a machine, or for the previous video to finish.", pct: 3, live: true});
  else if (cur) frameState({big: cur.screen, small: cur.hint, pct: Math.max(4, Math.round(done / stages.length * 100)), live: true});
  const o = job.options || {};
  const title = o.topic ? o.topic.charAt(0).toUpperCase() + o.topic.slice(1) : "A trending topic";
  $("#side").innerHTML = `
    <h2>${esc(title)}</h2>
    <ol class="steps">${stages.map(s => {
      const v = view[s.id] || {status: "wait"};
      const t = v.status === "done" && v.start && v.end ? fmtDur((new Date(v.end) - new Date(v.start)) / 1000)
        : v.status === "run" && v.start ? fmtDur(since(v.start)) : v.status === "skip" ? "skipped" : "";
      const name = s.id === "Find trend" && o.topic ? "Use your topic" : s.name;
      return `<li class="${v.status}"><span>${esc(name)}</span><span class="t">${t}</span></li>`;
    }).join("")}</ol>
    <div class="actions">
      ${job.url ? `<a class="btn ghost" href="${esc(job.url)}" target="_blank" rel="noopener">Open run on GitHub</a>` : ""}
      ${run && run.status !== "completed" ? `<button class="btn ghost" id="cancelRun" type="button">Cancel</button>` : ""}
    </div>`;
  const c = $("#cancelRun");
  if (c) c.onclick = async () => { try { await gh(`${R()}/actions/runs/${run.id}/cancel`, {method: "POST"}); toast("Cancelling…") } catch (e) { toast(explain(e)) } };
}

async function finishDraft(job, run, view, stages) {
  const failed = stages.find(s => view[s.id]?.status === "fail");
  let rel = null;
  try { rel = await gh(`${R()}/releases/tags/video-${job.rid}`) } catch (e) {}
  if (rel) {
    const item = toItem(rel);
    showOnCreate(item);
    if (failed?.id === "Post to YouTube and Instagram") toast("Saved to your library, but posting failed. Details are on the video.");
    else toast("Your video is ready.");
    libCache = null;
    return;
  }
  const why = run.conclusion === "cancelled" ? "The run was cancelled."
    : ["Find trend", "Research", "Write and direct"].includes(failed?.id) ? `It stopped at "${failed.name}". Check the Claude key in Connect, then open the run log.`
    : `It stopped at "${failed ? failed.name : "an early step"}". The run log on GitHub says why.`;
  frameState({big: "That one didn't make it", small: why});
}

function showOnCreate(item) {
  frameState({video: item.video, poster: item.thumb});
  const s = item.summary;
  $("#side").innerHTML = `
    <h2>${esc(item.title)}</h2>
    <dl class="facts">${factRows(item)}</dl>
    <div class="posted">${postedRows(item)}</div>
    <div class="actions">
      <button class="btn primary" type="button" id="openItem">Post or edit captions</button>
      <a class="btn ghost" href="${esc(item.video)}" download>Download MP4</a>
    </div>
    ${item.sources.length ? `<h3 class="sub">Sources</h3><ul class="sources">${item.sources.slice(0, 6).map(f => `<li>${esc(f.claim)} <a href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.title || "source")}</a></li>`).join("")}</ul>` : ""}`;
  $("#openItem").onclick = () => openDetail(item);
}

// ------------------------------------------------------------------ library
let libCache = null, libPage = 1, libDone = false;
function parseBody(body) {
  const i = (body || "").indexOf("<!-- vidforge"); if (i < 0) return {};
  const j = body.indexOf("-->", i + 13);
  try { return JSON.parse(body.slice(i + 13, j).trim()) } catch (e) { return {} }
}
function toItem(rel) {
  const d = parseBody(rel.body), asset = n => (rel.assets || []).find(a => a.name === n)?.browser_download_url;
  return {id: rel.tag_name.replace(/^video-/, ""), tag: rel.tag_name, release: rel, url: rel.html_url,
    title: d.summary?.title || rel.name || rel.tag_name, summary: d.summary || {}, meta: d.meta || {}, published: d.published || {},
    sources: d.sources || [], qa: d.qa || {}, video: asset("final.mp4"), thumb: asset("thumbnail.jpg"),
    created: d.summary?.created || rel.created_at};
}
function factRows(item) {
  const s = item.summary, rows = [];
  if (s.duration) rows.push(["Length", Math.round(s.duration) + "s"]);
  if (s.language) rows.push(["Language", s.language]);
  if (s.qa_score != null) rows.push(["Review", s.qa_score + "/10"]);
  if (s.usd != null) rows.push(["Claude cost", "$" + Number(s.usd).toFixed(2)]);
  return rows.map(([k, v]) => `<div><dt>${k}</dt><dd>${esc(v)}</dd></div>`).join("");
}
function postedRows(item) {
  const out = [];
  for (const [k, label] of [["youtube", "YouTube"], ["instagram", "Instagram"]]) {
    const p = item.published[k]; if (!p) continue;
    out.push(p.url ? `<div>${k === "youtube" ? ICON.yt.replace("<svg", '<svg class="ico"') : ICON.ig.replace("<svg", '<svg class="ico"')} <a href="${esc(p.url)}" target="_blank" rel="noopener">Posted on ${label}</a>${p.privacy ? ` (${esc(p.privacy)})` : ""}</div>`
      : `<div class="err">${label}: ${esc(p.error || "failed")}</div>`);
  }
  return out.join("");
}
async function loadLibrary(reset) {
  const grid = $("#libGrid");
  if (!cfg.token && !DEMO) { grid.innerHTML = `<p class="empty">Connect GitHub to see your library.</p>`; return }
  if (reset && libCache) return renderLibrary();
  if (reset) { libCache = []; libPage = 1; libDone = false; grid.innerHTML = `<p class="empty">Loading…</p>` }
  try {
    const rels = await gh(`${R()}/releases?per_page=50&page=${libPage}`);
    libCache.push(...rels.filter(r => r.tag_name.startsWith("video-")).map(toItem));
    libDone = rels.length < 50; libPage++;
    renderLibrary();
  } catch (e) { grid.innerHTML = `<p class="empty">${esc(explain(e))}</p>` }
}
function renderLibrary() {
  const q = $("#libSearch").value.trim().toLowerCase(), unposted = $("#libUnposted").checked;
  const items = (libCache || []).filter(i => (!q || i.title.toLowerCase().includes(q)) && (!unposted || !Object.values(i.published).some(p => p?.url)));
  $("#libMore").hidden = libDone;
  $("#libGrid").innerHTML = items.length ? items.map(i => {
    const marks = [["youtube", "yt"], ["instagram", "ig"]].map(([k, ic]) => i.published[k] ? `<span class="${i.published[k].url ? "" : "fail"}" title="${k}">${ICON[ic]}</span>` : "").join("");
    const d = new Date(i.created);
    return `<button class="tile ${i.summary.aspect === "16:9" ? "wide" : ""}" data-id="${esc(i.id)}" type="button">
      <div class="thumb">${i.thumb ? `<img loading="lazy" alt="" src="${esc(i.thumb)}">` : ""}<div class="marks">${marks}</div></div>
      <div class="tt">${esc(i.title)}</div>
      <div class="mm"><span>${d.toLocaleDateString(undefined, {day: "numeric", month: "short"})}</span>${i.summary.duration ? `<span>${Math.round(i.summary.duration)}s</span>` : ""}${i.summary.language ? `<span>${esc(i.summary.language)}</span>` : ""}</div>
    </button>`;
  }).join("") : `<p class="empty">${libCache?.length ? "Nothing matches." : "Videos you make are saved here for good. Make your first one in Create."}</p>`;
  $$(".tile", $("#libGrid")).forEach(t => t.onclick = () => openDetail(libCache.find(i => i.id === t.dataset.id)));
}
$("#libSearch").addEventListener("input", renderLibrary);
$("#libUnposted").addEventListener("change", renderLibrary);
$("#libMore").addEventListener("click", () => loadLibrary(false));

// ------------------------------------------------------------------ detail + publish
let current = null;
const dlg = $("#detail");
$("#dClose").onclick = () => dlg.close();
dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close() });
function openDetail(item) {
  current = item;
  $("#dTitle").textContent = item.title;
  const sc = $("#dScreen"); sc.innerHTML = "";
  if (item.video) { const v = document.createElement("video"); Object.assign(v, {src: item.video, controls: true, playsInline: true, preload: "metadata"}); if (item.thumb) v.poster = item.thumb; sc.appendChild(v) }
  $("#dScreen").parentElement.style.aspectRatio = item.summary.aspect === "16:9" ? "16/9" : item.summary.aspect === "1:1" ? "1/1" : "9/16";
  $("#dFacts").innerHTML = factRows(item);
  $("#dPosted").innerHTML = postedRows(item);
  $("#dDownload").href = item.video || "#"; $("#dRelease").href = item.url;
  const yt = item.meta.youtube || {}, ig = item.meta.instagram || {};
  $("#pTitle").value = yt.title || item.title; $("#pDesc").value = yt.description || ""; $("#pCaption").value = ig.caption || "";
  $("#pYT").checked = !item.published.youtube?.url; $("#pIG").checked = false;
  updateCapCount();
  $("#pStatus").textContent = ""; $("#pStatus").className = "status";
  $("#dSources").innerHTML = item.sources.length ? `<h3>Sources</h3><ul class="sources">${item.sources.slice(0, 8).map(f => `<li>${esc(f.claim)} <a href="${esc(f.url)}" target="_blank" rel="noopener">${esc(f.title || "source")}</a></li>`).join("")}</ul>` : "";
  if (!dlg.open) dlg.showModal();
}
function updateCapCount() {
  const c = $("#pCaption").value, tags = (c.match(/(^|\s)#[^\s#]+/g) || []).length;
  $("#pCapCount").textContent = `${c.length}/2200`;
  $("#pTagHint").textContent = tags > 5 ? `Instagram allows 5 hashtags; this caption has ${tags}. Extra ones may be dropped.` : `${tags} of 5 hashtags. Instagram now caps captions at 5.`;
}
$("#pCaption").addEventListener("input", updateCapCount);
$("#pCopy").onclick = () => navigator.clipboard.writeText($("#pCaption").value).then(() => toast("Caption copied"));
function pubStatus(t, kind = "") { const s = $("#pStatus"); s.textContent = t; s.className = "status " + kind }
$("#pGo").onclick = async () => {
  if (!current) return;
  const yt = $("#pYT").checked, ig = $("#pIG").checked;
  if (!yt && !ig) return pubStatus("Switch on YouTube or Instagram first.", "bad");
  const id = rid();
  const options = {youtube: yt, instagram: ig, privacy: groups.dprivacy.get() || "public",
    overrides: {youtube: {title: $("#pTitle").value.trim(), description: $("#pDesc").value.trim()}, instagram: {caption: $("#pCaption").value.trim()}}};
  if ($("#pAt").value) options.publish_at = new Date($("#pAt").value).toISOString();
  $("#pGo").disabled = true; pubStatus("Starting…");
  try {
    await gh(`${R()}/actions/workflows/${PUBLISH_WF}/dispatches`, {method: "POST", body: {ref: "main", inputs: {video_id: current.id, request_id: id, options: JSON.stringify(options)}}});
    await track({kind: "publish", rid: id, videoId: current.id, startedAt: Date.now()});
  } catch (e) { pubStatus(explain(e), "bad") } finally { $("#pGo").disabled = false }
};
async function finishPublish(job, run) {
  try {
    const item = toItem(await gh(`${R()}/releases/tags/video-${job.videoId}`));
    const i = (libCache || []).findIndex(x => x.id === item.id); if (i >= 0) libCache[i] = item;
    if (dlg.open && current?.id === item.id) openDetail(item);
    renderLibrary();
    const errs = Object.entries(item.published).filter(([, p]) => p.error);
    pubStatus(run.conclusion === "success" ? "Posted." : errs.length ? `Posting failed: ${errs.map(([k, p]) => `${k}: ${p.error}`).join("; ")}` : "Posting failed. Open the run on GitHub for details.", run.conclusion === "success" ? "ok" : "bad");
  } catch (e) { pubStatus(run.conclusion === "success" ? "Posted." : "Posting failed.", run.conclusion === "success" ? "ok" : "bad") }
}

// ------------------------------------------------------------------ connect
function fillConnect() {
  $("#repoIn").value = cfg.repo; $("#tokenIn").value = cfg.token; $("#rememberIn").checked = cfg.remember;
  refreshSecretBadges(); loadRunner();
}
$("#saveGh").onclick = async () => {
  cfg.repo = $("#repoIn").value.trim().replace(/^https:\/\/github\.com\//, "").replace(/\/$/, "");
  cfg.token = $("#tokenIn").value.trim(); cfg.remember = $("#rememberIn").checked;
  setStatus("#ghStatus", "Checking…");
  if (await connect(true)) { cfg.save(); setStatus("#ghStatus", "Connected.", "ok"); libCache = null; resume() }
  else setStatus("#ghStatus", "Couldn't connect. Check the repository name and token permissions.", "bad");
};
$("#forgetGh").onclick = () => { cfg.token = ""; cfg.save(); $("#tokenIn").value = ""; setConn("", "Connect GitHub"); setStatus("#ghStatus", "Token removed from this browser.") };
function setStatus(sel, t, kind = "") { const s = typeof sel === "string" ? $(sel) : sel; s.textContent = t; s.className = "status " + kind }

let secretNames = null;
async function refreshSecretBadges() {
  if (!cfg.token && !DEMO) return;
  try { secretNames = new Set((await gh(`${R()}/actions/secrets?per_page=100`)).secrets.map(s => s.name)) }
  catch (e) { secretNames = null }
  $$("[data-secret-badge]").forEach(b => {
    if (!secretNames) { b.textContent = ""; b.className = "badge"; return }
    const on = secretNames.has(b.dataset.secretBadge);
    b.textContent = on ? "Connected" : "Not set"; b.className = "badge " + (on ? "ok" : "no");
  });
}

async function putSecrets(pairs) {
  const key = await gh(`${R()}/actions/secrets/public-key`);
  for (const [name, value] of pairs) {
    await gh(`${R()}/actions/secrets/${name}`, {method: "PUT", body: {encrypted_value: await seal(value, key.key), key_id: key.key_id}});
  }
}
const SECRET_FORMS = {
  anthropic: () => [["ANTHROPIC_API_KEY", $("#anthropicIn").value.trim()]],
  youtube: () => [["YOUTUBE_CLIENT_ID", $("#ytId").value.trim()], ["YOUTUBE_CLIENT_SECRET", $("#ytSecret").value.trim()], ["YOUTUBE_REFRESH_TOKEN", $("#ytRefresh").value.trim()]],
  instagram: () => [["IG_ACCESS_TOKEN", $("#igToken").value.trim()], ["IG_USER_ID", $("#igUser").value.trim()]],
  trends: () => [["YOUTUBE_API_KEY", $("#ytApiKey").value.trim()]],
};
$$("[data-save-secrets]").forEach(btn => btn.addEventListener("click", async () => {
  const kind = btn.dataset.saveSecrets, st = $(`[data-status="${kind}"]`);
  let pairs = SECRET_FORMS[kind]().filter(([, v]) => v);
  const required = {anthropic: 1, youtube: 3, instagram: 1, trends: 1}[kind];
  if (pairs.length < required) return setStatus(st, kind === "youtube" ? "Fill in all three values." : "Paste the value first.", "bad");
  if (kind === "instagram" && !$("#igUser").value.trim()) {
    try {
      const r = await fetch(`https://graph.instagram.com/me?fields=user_id,username&access_token=${encodeURIComponent($("#igToken").value.trim())}`);
      const j = await r.json(); if (j.user_id) { pairs.push(["IG_USER_ID", String(j.user_id)]); setStatus(st, `Found @${j.username}.`) }
    } catch (e) { /* looked up during posting instead */ }
  }
  btn.disabled = true; setStatus(st, "Saving…");
  try {
    await putSecrets(pairs);
    $$(`#card-${kind === "trends" ? "trends" : kind === "anthropic" ? "claude" : kind} input`).forEach(i => i.value = "");
    setStatus(st, "Saved as encrypted repository secrets.", "ok"); refreshSecretBadges();
  } catch (e) { setStatus(st, explain(e), "bad") } finally { btn.disabled = false }
}));
async function loadRunner() {
  try { const v = await gh(`${R()}/actions/variables/RUNNER`); groups.runner.set(v.value) } catch (e) { groups.runner.set("ubuntu-latest") }
}
$("#saveRunner").onclick = async () => {
  const value = groups.runner.get() || "ubuntu-latest";
  setStatus("#runnerStatus", "Saving…");
  try {
    try { await gh(`${R()}/actions/variables/RUNNER`, {method: "PATCH", body: {name: "RUNNER", value}}) }
    catch (e) { if (e.status === 404) await gh(`${R()}/actions/variables`, {method: "POST", body: {name: "RUNNER", value}}); else throw e }
    setStatus("#runnerStatus", `New videos will run on ${value}.`, "ok");
  } catch (e) { setStatus("#runnerStatus", explain(e), "bad") }
};

// ------------------------------------------------------------------ demo mode (?demo): sample data, no GitHub
async function demoApi(path, method) {
  await sleep(80);
  const job = JSON.parse(localStorage.getItem("vf.active") || "{}"), t = (Date.now() - (job.startedAt || Date.now())) / 1000;
  if (/\/repos\/[^/]+\/[^/]+$/.test(path)) return {full_name: cfg.repo + " (demo)", private: false};
  if (method !== "GET") return null;
  if (path.includes("/actions/secrets?")) return {secrets: [{name: "ANTHROPIC_API_KEY"}, {name: "YOUTUBE_REFRESH_TOKEN"}]};
  if (path.includes("/actions/variables/RUNNER")) return {value: "ubuntu-latest"};
  if (path.includes("/runs?")) return {workflow_runs: [{id: 1, display_title: `draft ${job.rid}`, html_url: "#", status: "in_progress"}]};
  if (/\/actions\/runs\/\d+$/.test(path)) return {id: 1, html_url: "#", status: t > 30 ? "completed" : "in_progress", conclusion: t > 30 ? "success" : null};
  if (path.endsWith("/jobs")) {
    const names = ["Set up job", "Run actions/checkout@v4", "Install tools", "Find trend", "Research", "Write and direct", "Review frames", "Render video", "Write captions and hashtags", "Save to library"];
    const at = [0, 1, 2, 5, 8, 12, 16, 20, 26, 28, 30];
    const t0 = job.startedAt || Date.now();
    return {jobs: [{steps: names.map((n, i) => ({name: n, status: t >= at[i + 1] ? "completed" : t >= at[i] ? "in_progress" : "queued",
      conclusion: t >= at[i + 1] ? "success" : null, started_at: t >= at[i] ? new Date(t0 + at[i] * 1000).toISOString() : null,
      completed_at: t >= at[i + 1] ? new Date(t0 + at[i + 1] * 1000).toISOString() : null}))}]};
  }
  const rels = await (await fetch("demo/releases.json")).json();
  if (path.includes("/releases/tags/")) return rels.find(r => path.endsWith(r.tag_name)) || rels[0];
  if (path.includes("/releases?")) return rels;
  throw new GhError(404, "demo: " + path);
}

// ------------------------------------------------------------------ boot
function resume() {
  const j = JSON.parse(localStorage.getItem("vf.active") || "null");
  if (j && Date.now() - j.startedAt < 90 * 60 * 1000) track(j); else localStorage.removeItem("vf.active");
}
for (const el of $$("[data-group]")) groups[el.dataset.group] = makeGroup(el);
for (const k of ["language", "niche", "format", "writer", "voice", "music", "aspect", "length"]) if (saved[k] != null) groups[k].set(saved[k]);
for (const id of ["topic", "handle", "hashtags", "notes"]) if (saved[id]) $("#" + id).value = saved[id];
cfg.load();
const startTab = (location.hash || "#create").slice(1);
if (DEMO) {
  localStorage.removeItem("vf.active");
  setConn("ok", "Demo mode"); refreshSecretBadges();
  showTab(["create", "library", "connect"].includes(startTab) ? startTab : "create");
  if (params.has("autostart")) $("#makeBtn").click();
  if (params.get("open")) { libCache = null; await loadLibrary(true); const it = libCache.find(i => i.id === params.get("open")); if (it) { showOnCreate(it); if (params.has("dialog")) openDetail(it) } }
} else {
  showTab(["create", "library", "connect"].includes(startTab) ? startTab : "create");
  if (cfg.token) { if (await connect(false)) resume() }
  else { setConn("", "Connect GitHub"); frameState({big: "Connect GitHub to start.", small: "Open Connect and paste a token. It takes a minute."}) }
}
