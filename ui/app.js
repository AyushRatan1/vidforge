// VidForge web app: connection, start page, app shell and hash routing (#/, #/dashboard, #/create, #/library, #/settings).
// Pages live in pages/*.js and talk to the data layer (db.js) only.
import {connectSupabase, connectDemo, DbError} from "./db.js";
import {DEFAULTS} from "./config.js";
import {h, clear, Button, Avatar, Card, Status, toast, icon} from "./components.js";
import {startPage, loadSample, brand} from "./pages/start.js";
import {dashboardPage} from "./pages/dashboard.js";
import {createPage} from "./pages/create.js";
import {libraryPage} from "./pages/library.js";
import {settingsPage} from "./pages/settings.js";
import {captureYouTubeRedirect} from "./youtube-auth.js";

const params = new URLSearchParams(location.search);
export const DEMO = params.has("demo");
// Google's YouTube sign-in returns here with ?code=&state=: keep the result for Settings and drop it from the URL.
if (captureYouTubeRedirect(params)) history.replaceState(null, "", location.pathname + "#/settings");
const root = document.getElementById("root");

const PAGES = [
  {id: "dashboard", title: "Dashboard", icon: "grid", section: "Workspace", make: dashboardPage},
  {id: "create", title: "Create", icon: "plusSquare", section: "Workspace", make: createPage},
  {id: "library", title: "Library", icon: "stack", section: "Workspace", make: libraryPage},
  {id: "settings", title: "Settings", icon: "settings", section: "Account", make: settingsPage},
];

// ------------------------------------------------------------------ routing
export function parseHash() { const s = location.hash.replace(/^#\/?/, ""); const [page, ...rest] = s.split("/"); return {page: page || "", arg: rest.length ? rest.join("/") : undefined}; }
export function navigate(page, arg) { const hash = "#/" + (page || "") + (arg ? "/" + arg : ""); if (location.hash !== hash) location.hash = hash; else window.dispatchEvent(new HashChangeEvent("hashchange")); }

// ------------------------------------------------------------------ stored project
function readProject() { try { return JSON.parse(localStorage.getItem("vf.sb") || "null"); } catch { return null; } }
function saveProject(p) { try { localStorage.setItem("vf.sb", JSON.stringify(p)); } catch {} }
export function forgetProject() { try { localStorage.removeItem("vf.sb"); for (const k of Object.keys(localStorage)) if (k.startsWith("vf.auth")) localStorage.removeItem(k); } catch {} }

// ------------------------------------------------------------------ main
async function main() {
  const project = readProject() || {url: DEFAULTS.supabaseUrl, key: DEFAULTS.supabaseAnonKey};
  let db;
  try { db = DEMO ? await connectDemo() : await connectSupabase(project.url, project.key); }
  catch (e) { return connectError(e); }

  const forceSignin = DEMO && params.has("signin");
  let session = forceSignin ? null : await db.getSession();
  const sample = await loadSample();

  const startEl = h("div", {id: "start"});
  const appEl = h("div", {id: "app-root", hidden: true});
  root.append(startEl, appEl);
  let shell = null;

  const onSignIn = async ({email, password}) => {
    if (forceSignin) throw new DbError("Email or password is wrong.", "Check both, or ask an admin to reset the password in Supabase.");
    try { await db.signIn(email, password); }
    catch (e) { throw new DbError(/invalid/i.test(e.message) ? "Email or password is wrong." : e.message, /invalid/i.test(e.message) ? "Check both, or ask an admin to reset the password in Supabase." : ""); }
    session = await db.getSession();
    navigate("dashboard");
  };
  const onProject = async ({url, key}) => {
    if (!/^https?:\/\//.test(url)) throw new DbError("That does not look like a project URL.", "It starts with https:// and ends with .supabase.co.");
    const test = await fetch(url.replace(/\/$/, "") + "/rest/v1/", {headers: {apikey: key}}).catch(() => null);
    if (!test || test.status === 401 || test.status === 403) throw new DbError("Supabase did not accept that key.", "Copy the publishable (anon) key, not the service key.");
    saveProject({url: url.replace(/\/$/, ""), key});
    location.reload();
  };
  const onOpen = () => navigate("dashboard");

  function renderStart() {
    clear(startEl).append(startPage({demo: DEMO, signedIn: !!session && !forceSignin, project, sample, onSignIn, onProject, onOpen}));
    document.title = "VidForge";
  }

  async function route() {
    const {page, arg} = parseHash();
    const wantsApp = PAGES.some(p => p.id === page);
    if (!wantsApp || !session) {
      if (wantsApp && !session) { history.replaceState(null, "", location.pathname + location.search + "#/"); }
      appEl.hidden = true; startEl.hidden = false;
      if (!startEl.firstChild) renderStart();
      if (wantsApp && !session) setTimeout(() => document.querySelector("#signin")?.scrollIntoView({block: "start"}), 50);
      return;
    }
    startEl.hidden = true; appEl.hidden = false;
    shell ||= await buildShell(db, session, appEl);
    await shell.go(page, arg);
  }

  window.addEventListener("hashchange", route);
  if (!location.hash || location.hash === "#") { if (session && !DEMO) history.replaceState(null, "", location.pathname + location.search + "#/dashboard"); else history.replaceState(null, "", location.pathname + location.search + "#/"); }
  else if (PAGES.some(p => location.hash === "#" + p.id || location.hash.startsWith("#" + p.id + "/"))) history.replaceState(null, "", location.pathname + location.search + "#/" + location.hash.slice(1)); // legacy #dashboard links
  await route();

  if (!DEMO) db.onAuth(s => { if (!s && session) { session = null; location.hash = "#/"; location.reload(); } });
  window.addEventListener("unhandledrejection", ev => { const e = ev.reason; if (e) toast((e.message || "Something went wrong.") + (e.hint ? " " + e.hint : ""), "err"); });
  if (DEMO) window.__vf = {db, navigate, get shell() { return shell; }};
  if (DEMO && params.has("selftest")) selfTest(db);
}

function connectError(e) {
  const cdn = /dynamically imported module/i.test(e.message || "");
  clear(root).append(h("div", {class: "start"}, h("nav", {class: "start-nav"}, brand(DEMO)), h("div", {class: "start-wrap", style: {maxWidth: "520px"}},
    Card({title: "Could not connect", body: h("div", {class: "stack"},
      h("p", {class: "secondary"}, cdn ? "The Supabase client did not load from cdn.jsdelivr.net. Check your connection or any blocker, then reload." : (e.message + (e.hint ? " " + e.hint : ""))),
      h("div", {class: "actions"}, Button({label: "Reload", variant: "primary", onClick: () => location.reload()}),
        cdn ? null : Button({label: "Forget this project and start over", variant: "ghost", onClick: () => { forgetProject(); location.reload(); }})))}))));
}

// ------------------------------------------------------------------ app shell
async function buildShell(db, session, host) {
  const user = session?.user || (await db.user());
  const ctx = {db, user, demo: DEMO, go: (id, arg) => navigate(id, arg), settings: await db.getSettings().catch(() => ({})), videosCache: []};
  const email = user?.email || (DEMO ? "demo@vidforge.app" : "");

  // sidebar: brand, sections, sign-in status
  const navItem = p => h("a", {class: "nav-item", href: "#/" + p.id, "data-page": p.id, title: p.title}, icon(p.icon, {size: 16}), h("span", {}, p.title));
  const sections = [...new Set(PAGES.map(p => p.section))];
  const sidebar = h("aside", {class: "sidebar"}, brand(DEMO),
    h("nav", {class: "sidebar-nav", "aria-label": "Main"}, ...sections.map(sec => h("div", {class: "nav-section"}, h("div", {class: "nav-label"}, sec), ...PAGES.filter(p => p.section === sec).map(navItem)))),
    h("div", {class: "sidebar-foot", title: email}, Avatar(email || "?", {size: 24}),
      h("div", {class: "account-text"}, h("span", {class: "account-name"}, email || "Signed in"), h("span", {class: "account-sub"}, DEMO ? "Demo, nothing is saved" : "Signed in"))));
  const tabbar = h("nav", {class: "tabbar", "aria-label": "Main"}, ...PAGES.map(navItem));

  // unified toolbar: title left, page controls, then search, refresh, new video, account
  const title = h("h1", {class: "toolbar-title", id: "page-title"});
  const pageActions = h("div", {class: "toolbar-actions", id: "page-actions"});
  const search = globalSearch(ctx);
  let current = null;
  const refreshBtn = Button({variant: "secondary", icon: "refresh", ariaLabel: "Refresh", onClick: async () => {
    if (!current?.inst?.refresh) return;
    refreshBtn.disabled = true;
    try { await current.inst.refresh(); } finally { refreshBtn.disabled = false; }
  }});
  const newBtn = Button({label: "New video", variant: "primary", icon: "plus", ariaLabel: "New video", onClick: () => navigate("create")});
  const menuPanel = h("div", {class: "menu-panel", role: "menu", "data-open": "false"},
    h("div", {class: "menu-head"}, h("strong", {}, email.split("@")[0] || "Team"), h("span", {class: "micro"}, email)),
    h("button", {class: "menu-item", role: "menuitem", onClick: () => { closeMenu(); navigate("settings"); }}, icon("settings"), "Settings"),
    h("a", {class: "menu-item", role: "menuitem", href: "https://github.com/ayushratan1/vidforge#readme", target: "_blank", rel: "noopener"}, icon("bookOpen"), "Setup guide"),
    h("button", {class: "menu-item", role: "menuitem", onClick: () => { closeMenu(); navigate(""); }}, icon("home"), "Start page"),
    h("button", {class: "menu-item danger", role: "menuitem", onClick: async () => { await db.signOut(); location.hash = "#/"; location.reload(); }}, icon("logout"), "Sign out"));
  const avatarBtn = h("button", {class: "avatar-btn", type: "button", "aria-haspopup": "menu", "aria-expanded": "false", "aria-label": "Account menu", onClick: () => { const open = menuPanel.dataset.open !== "true"; menuPanel.dataset.open = String(open); avatarBtn.setAttribute("aria-expanded", String(open)); }}, Avatar(email || "?", {size: 28}));
  const closeMenu = () => { menuPanel.dataset.open = "false"; avatarBtn.setAttribute("aria-expanded", "false"); };
  document.addEventListener("click", e => { if (!menu.contains(e.target)) closeMenu(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeMenu(); });
  const menu = h("div", {class: "menu"}, avatarBtn, menuPanel);
  const toolbar = h("header", {class: "toolbar"}, title, pageActions, h("div", {class: "toolbar-spacer"}), search, refreshBtn, newBtn, menu);

  const main = h("main", {class: "main", id: "main", tabIndex: -1}, toolbar);
  const app = h("div", {class: "app"}, sidebar, main);
  clear(host).append(app, tabbar);

  const pages = {};
  for (const p of PAGES) { const el = h("section", {class: "page", id: "page-" + p.id, "aria-labelledby": "page-title"}); main.append(el); pages[p.id] = {def: p, el, inst: null}; }

  let currentId = null;
  async function go(id, arg) {
    const page = pages[id] || pages.dashboard;
    current = page;
    for (const [k, p] of Object.entries(pages)) p.el.classList.toggle("active", k === page.def.id);
    for (const a of document.querySelectorAll(".nav-item")) a.dataset.page === page.def.id ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current");
    title.textContent = page.def.title;
    document.title = page.def.title + " · VidForge";
    clear(pageActions);
    if (!page.inst) page.inst = page.def.make(ctx, page.el, pageActions);
    else page.inst.mount?.(pageActions);
    refreshBtn.disabled = !page.inst.refresh;
    await page.inst.show?.(arg);
    if (currentId !== page.def.id) { window.scrollTo({top: 0}); main.focus({preventScroll: true}); }
    currentId = page.def.id;
  }
  return {go, ctx};
}

function globalSearch(ctx) {
  const input = h("input", {class: "input", type: "search", placeholder: "Search videos", "aria-label": "Search videos", autocomplete: "off"});
  const results = h("div", {class: "search-results", role: "listbox", "aria-label": "Results"});
  const wrap = h("div", {class: "search"}, icon("search", {size: 14}), input, h("kbd", {}, "/"), results);
  let videos = null;
  const run = async () => {
    const q = input.value.trim().toLowerCase();
    clear(results);
    if (!q) return;
    videos ||= await ctx.db.listVideos().catch(() => []);
    const hits = videos.filter(v => `${v.title || ""} ${v.topic || ""} ${v.niche || ""}`.toLowerCase().includes(q)).slice(0, 8);
    if (!hits.length) { results.append(h("div", {class: "search-hit", role: "option"}, h("span", {class: "search-hit-title secondary"}, "No videos match"))); return; }
    for (const v of hits) results.append(h("button", {class: "search-hit", role: "option", type: "button", onClick: () => { input.value = ""; clear(results); navigate("library", v.id); }},
      v.thumb_url ? h("img", {class: "thumb-xs", src: v.thumb_url, alt: ""}) : h("span", {class: "thumb-xs"}), h("span", {class: "search-hit-title"}, v.title || v.topic || v.id), Status(v.status)));
  };
  input.addEventListener("input", run);
  input.addEventListener("focus", () => { videos = null; run(); });
  document.addEventListener("click", e => { if (!wrap.contains(e.target)) clear(results); });
  document.addEventListener("keydown", e => { if (e.key === "/" && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName) && document.getElementById("app-root") && !document.getElementById("app-root").hidden) { e.preventDefault(); input.focus(); } if (e.key === "Escape") { clear(results); input.blur(); } });
  return wrap;
}

// ------------------------------------------------------------------ self test (?demo&selftest)
// Walks the main flows against the demo data layer and logs "SELFTEST OK" or the first failure.
async function selfTest(db) {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const errors = [];
  window.addEventListener("error", e => errors.push(e.message));
  window.addEventListener("unhandledrejection", e => errors.push(String(e.reason?.message || e.reason)));
  const btn = (root, text) => [...root.querySelectorAll("button")].find(b => b.textContent.trim() === text || b.getAttribute("aria-label") === text);
  try {
    navigate("create"); await wait(300);
    const create = document.querySelector("#page-create");
    create.querySelector("textarea").value = "Why Mars sunsets are blue";
    create.querySelectorAll(".switch")[0].click();
    btn(create, "Make video").click();
    await wait(14000);
    const steps = create.querySelectorAll(".step-done").length;
    if (steps < 7) throw new Error("make flow: only " + steps + " steps done");
    if (!create.querySelector(".phone-screen video")) throw new Error("make flow: no video in phone preview");
    navigate("create", "autopilot"); await wait(300);
    create.querySelector("textarea[placeholder^='Add topics']").value = "Topic A\nTopic B";
    btn(create, "Add").click();
    btn(create, "Save changes").click();
    await wait(500);
    if ((await db.getAutopilot()).topics.length < 7) throw new Error("autopilot: topics not saved");
    navigate("library", "20261108-0112-gl4s"); await wait(500);
    const dlg = document.querySelector("dialog.sheet[open]");
    if (!dlg) throw new Error("library: sheet did not open");
    dlg.querySelectorAll(".switch")[0].setAttribute("aria-checked", "true");
    btn(dlg, "Post now").click();
    await wait(3500);
    const v = await db.getVideo("20261108-0112-gl4s");
    if (v.status !== "posted") throw new Error("publish flow: status is " + v.status);
    navigate("settings"); await wait(300);
    const inp = document.querySelector('#page-settings input[aria-label="pexels api key"]');
    inp.value = "newkey"; inp.dispatchEvent(new Event("input"));
    btn(document.querySelector("#page-settings"), "Save 1 change").click();
    await wait(600);
    if ((await db.getSettings()).pexels_api_key !== "newkey") throw new Error("settings: not saved");
    navigate("dashboard"); await wait(1500);
    if (errors.length) throw new Error("console errors: " + errors.join(" | "));
    if (!document.querySelector("#page-dashboard .chart-svg")) throw new Error("dashboard: no chart");
    console.log("SELFTEST OK");
  } catch (e) { console.log("SELFTEST FAIL: " + e.message); }
}

main();
