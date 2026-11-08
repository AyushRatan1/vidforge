// VidForge web app: sign-in, shell, routing. Pages live in pages/*.js and talk to the data layer only.
import {connectSupabase, connectDemo, DbError} from "./db.js";
import {DEFAULTS} from "./config.js";
import {h, clear, icon, toast, field} from "./ui.js";
import {dashboardPage} from "./pages/dashboard.js";
import {createPage} from "./pages/create.js";
import {libraryPage} from "./pages/library.js";
import {settingsPage} from "./pages/settings.js";

const README = "https://github.com/ayushratan1/vidforge#readme";
const params = new URLSearchParams(location.search);
export const DEMO = params.has("demo");
const root = document.getElementById("root");

const PAGES = [
  {id: "dashboard", title: "Dashboard", icon: "grid", make: dashboardPage},
  {id: "create", title: "Create", icon: "plusCircle", make: createPage},
  {id: "library", title: "Library", icon: "library", make: libraryPage},
  {id: "settings", title: "Settings", icon: "gear", make: settingsPage},
];

const brand = () => h("div", {class: "brand"}, h("span", {class: "brand-mark"}, icon("bolt")), h("div", {}, h("div", {class: "brand-name"}, "VidForge"), h("div", {class: "brand-sub"}, DEMO ? "Demo with sample data" : "Short videos on autopilot")));

// ------------------------------------------------------------------ sign in
function readProject() { try { return JSON.parse(localStorage.getItem("vf.sb") || "null"); } catch { return null; } }
function saveProject(p) { try { localStorage.setItem("vf.sb", JSON.stringify(p)); } catch {} }
export function forgetProject() { try { localStorage.removeItem("vf.sb"); for (const k of Object.keys(localStorage)) if (k.startsWith("vf.auth")) localStorage.removeItem(k); } catch {} }

function projectForm(onSubmit, prefill) {
  const err = h("div", {class: "error", role: "alert"});
  const url = h("input", {class: "input", name: "url", type: "url", required: true, placeholder: "https://xxxx.supabase.co", autocomplete: "off", value: prefill.url || ""});
  const key = h("input", {class: "input mono", name: "key", required: true, placeholder: "sb_publishable_... or eyJhbGciOi...", autocomplete: "off", value: prefill.key || ""});
  const btn = h("button", {class: "btn", type: "button", onClick: async () => {
    err.textContent = ""; btn.disabled = true;
    try { await onSubmit({url: url.value.trim(), key: key.value.trim()}); }
    catch (e) { err.textContent = (e.message || "Something went wrong.") + (e.hint ? " " + e.hint : ""); }
    finally { btn.disabled = false; }
  }}, "Use this project");
  return h("div", {class: "form", style: {gap: "12px", marginTop: "12px"}},
    h("p", {class: "footnote secondary", style: {margin: 0}}, "Both values are on the Supabase dashboard under Project Settings, API. They are kept on this device only."),
    field("Project URL", url), field("Publishable key", key), err, btn,
    h("details", {}, h("summary", {}, "Need a project? Steps"),
      h("ol", {}, h("li", {}, "Create a free project at supabase.com."),
        h("li", {}, "Open the SQL editor and run ", h("code", {}, "supabase/schema.sql"), " from the repository."),
        h("li", {}, "Add your team in Authentication, Users (email and password)."),
        h("li", {}, "Add the project URL and service key as GitHub secrets ", h("code", {}, "SUPABASE_URL"), " and ", h("code", {}, "SUPABASE_SERVICE_KEY"), "."),
        h("li", {}, h("a", {href: README, target: "_blank", rel: "noopener"}, "Full guide in the README")))));
}

function signInCard(project, onSignIn, onProject) {
  const err = h("div", {class: "error", role: "alert"});
  const busy = h("span", {class: "spin", hidden: true});
  const email = h("input", {class: "input", name: "email", type: "email", required: true, placeholder: "you@team.com", autocomplete: "username"});
  const password = h("input", {class: "input", name: "password", type: "password", required: true, placeholder: "Password", autocomplete: "current-password"});
  const submit = h("button", {class: "btn primary lg", type: "submit"}, busy, "Sign in");
  const form = h("form", {class: "signin", onSubmit: async ev => {
    ev.preventDefault(); err.textContent = ""; busy.hidden = false; submit.disabled = true;
    try { await onSignIn({email: email.value.trim(), password: password.value}); }
    catch (e) { err.textContent = (e.message || "Something went wrong.") + (e.hint ? " " + e.hint : ""); }
    finally { busy.hidden = true; submit.disabled = false; }
  }});
  const host = (() => { try { return new URL(project.url).host; } catch { return project.url; } })();
  form.append(brand(), h("h1", {}, "Sign in"),
    h("p", {class: "subhead secondary", style: {margin: 0}}, "Use the email and password your team set up. You stay signed in on this device."),
    field("Email", email), field("Password", password), err, submit,
    h("details", {}, h("summary", {}, "Use a different project"),
      h("p", {class: "footnote tertiary", style: {margin: "8px 0 0"}}, "Connected to ", h("span", {class: "mono"}, host), ". Enter another project to use it on this device instead."),
      projectForm(onProject, project)));
  return h("div", {class: "signin-wrap"}, form);
}

async function connect() {
  if (DEMO && params.has("signin")) { clear(root).append(signInCard({url: DEFAULTS.supabaseUrl}, async () => { throw new DbError("Email or password is wrong.", "Check both, or ask an admin to reset the password in Supabase."); }, async () => {})); return new Promise(() => {}); }
  if (DEMO) return connectDemo();
  const stored = readProject();
  const project = stored || {url: DEFAULTS.supabaseUrl, key: DEFAULTS.supabaseAnonKey};
  const db = await connectSupabase(project.url, project.key);
  if (!(await db.getSession())) {
    await new Promise(resolve => {
      clear(root).append(signInCard(project,
        async ({email, password}) => {
          try { await db.signIn(email, password); }
          catch (e) { throw new DbError(/invalid/i.test(e.message) ? "Email or password is wrong." : e.message, /invalid/i.test(e.message) ? "Check both, or ask an admin to reset the password in Supabase." : ""); }
          resolve();
        },
        async ({url, key}) => {
          if (!/^https?:\/\//.test(url)) throw new DbError("That does not look like a project URL.", "It starts with https:// and ends with .supabase.co.");
          const test = await fetch(url.replace(/\/$/, "") + "/rest/v1/", {headers: {apikey: key}}).catch(() => null);
          if (!test || test.status === 401 || test.status === 403) throw new DbError("Supabase did not accept that key.", "Copy the publishable (anon) key, not the service key.");
          saveProject({url: url.replace(/\/$/, ""), key});
          location.reload();
        }));
    });
  }
  db.onAuth(s => { if (!s) location.reload(); });
  return db;
}

// ------------------------------------------------------------------ shell
async function main() {
  let db;
  try { db = await connect(); }
  catch (e) {
    const cdn = /dynamically imported module/i.test(e.message || "");
    clear(root).append(h("div", {class: "signin-wrap"}, h("div", {class: "signin"}, brand(), h("h1", {}, "Could not connect"),
      h("p", {class: "secondary subhead", style: {margin: 0}}, cdn ? "The Supabase client did not load from cdn.jsdelivr.net. Check your connection or any blocker, then reload." : (e.message + (e.hint ? " " + e.hint : ""))),
      h("button", {class: "btn primary", onClick: () => location.reload()}, "Reload"),
      cdn ? null : h("button", {class: "btn plain sm", onClick: () => { forgetProject(); location.reload(); }}, "Forget this project and start over"))));
    return;
  }

  const user = await db.user();
  const ctx = {db, user, demo: DEMO, go: null, settings: await db.getSettings().catch(() => ({}))};

  const navItem = p => h("button", {class: "nav-item", type: "button", "data-page": p.id, onClick: () => go(p.id)}, icon(p.icon), h("span", {}, p.title));
  const sidebar = h("nav", {class: "sidebar", "aria-label": "Main"}, brand(), ...PAGES.map(navItem),
    h("div", {class: "sidebar-foot"}, h("span", {class: "who"}, user?.email || ""), h("span", {}, DEMO ? "Nothing here is saved" : "Stats refresh daily at 07:45 IST")));
  const tabbar = h("nav", {class: "tabbar", "aria-label": "Main"}, ...PAGES.map(navItem));
  const main = h("main", {class: "main"});
  const toolbarTitle = h("h1", {class: "large-title"});
  const toolbarActions = h("div", {class: "toolbar-actions"});
  const toolbar = h("header", {class: "toolbar"}, toolbarTitle, toolbarActions);
  main.append(toolbar);
  clear(root).append(h("div", {class: "app"}, sidebar, main), tabbar);

  const pages = {};
  for (const p of PAGES) { const el = h("section", {class: "page", id: "page-" + p.id, "aria-labelledby": "title"}); main.append(el); pages[p.id] = {def: p, el, inst: null}; }

  async function go(id, arg) {
    const page = pages[id] ? pages[id] : pages.dashboard;
    for (const [k, p] of Object.entries(pages)) p.el.classList.toggle("active", k === page.def.id);
    for (const b of document.querySelectorAll(".nav-item")) b.toggleAttribute("aria-current", false), b.dataset.page === page.def.id ? b.setAttribute("aria-current", "page") : b.removeAttribute("aria-current");
    toolbarTitle.textContent = page.def.title;
    clear(toolbarActions);
    const hash = "#" + page.def.id + (arg ? "/" + arg : "");
    if (location.hash !== hash) history.replaceState(null, "", location.pathname + location.search + hash);
    if (!page.inst) { page.inst = page.def.make(ctx, page.el, toolbarActions); }
    else page.inst.mount?.(toolbarActions);
    await page.inst.show?.(arg);
    window.scrollTo({top: 0});
  }
  ctx.go = go;
  window.addEventListener("hashchange", () => { const [id, arg] = location.hash.slice(1).split("/"); go(id, arg); });
  const [id, arg] = (location.hash || "#dashboard").slice(1).split("/");
  go(id, arg);

  window.addEventListener("unhandledrejection", ev => { const e = ev.reason; if (e) toast((e.message || "Something went wrong.") + (e.hint ? " " + e.hint : ""), "err"); });
  if (DEMO) window.__vf = ctx;
  if (DEMO && params.has("selftest")) selfTest(ctx, go);
}

// ?demo&selftest walks the main flows against the demo data layer and logs "SELFTEST OK" or the first failure.
async function selfTest(ctx, go) {
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const errors = [];
  window.addEventListener("error", e => errors.push(e.message));
  window.addEventListener("unhandledrejection", e => errors.push(String(e.reason?.message || e.reason)));
  try {
    await go("create"); await wait(100);
    document.querySelector("#page-create textarea").value = "Why Mars sunsets are blue";
    [...document.querySelectorAll("#page-create .switch")][0].click();
    [...document.querySelectorAll("#page-create .btn.primary")].find(b => b.textContent.includes("Make video")).click();
    await wait(14000);
    const steps = document.querySelectorAll("#page-create .step.done").length;
    if (steps < 7) throw new Error("make flow: only " + steps + " steps done");
    if (!document.querySelector("#page-create .phone-screen video")) throw new Error("make flow: no video in phone preview");
    await go("create", "autopilot"); await wait(100);
    document.querySelector("#page-create textarea[placeholder^='Add topics']").value = "Topic A\nTopic B";
    [...document.querySelectorAll("#page-create button")].find(b => b.textContent.trim() === "Add").click();
    [...document.querySelectorAll("#page-create button")].find(b => b.textContent.trim() === "Save changes").click();
    await wait(400);
    if ((await ctx.db.getAutopilot()).topics.length < 7) throw new Error("autopilot: topics not saved");
    await go("library", "20261108-0112-gl4s"); await wait(300);
    const dlg = document.querySelector("dialog.sheet[open]");
    if (!dlg) throw new Error("library: sheet did not open");
    [...dlg.querySelectorAll(".switch")][0].setAttribute("aria-checked", "true");
    dlg.querySelector("button.btn.primary").click();
    await wait(3500);
    const v = await ctx.db.getVideo("20261108-0112-gl4s");
    if (v.status !== "posted") throw new Error("publish flow: status is " + v.status);
    await go("settings"); await wait(100);
    const inp = document.querySelector('#page-settings input[aria-label="pexels api key"]');
    inp.value = "newkey"; inp.dispatchEvent(new Event("input"));
    [...document.querySelectorAll(".toolbar .btn.primary")][0].click();
    await wait(500);
    if ((await ctx.db.getSettings()).pexels_api_key !== "newkey") throw new Error("settings: not saved");
    await go("dashboard"); await wait(300);
    if (errors.length) throw new Error("console errors: " + errors.join(" | "));
    console.log("SELFTEST OK");
  } catch (e) { console.log("SELFTEST FAIL: " + e.message); }
}

main();
