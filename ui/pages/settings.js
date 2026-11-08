import {h, clear, icon, segmented, row, toast, fmt} from "../ui.js";
import {forgetProject} from "../app.js";
import {DEFAULTS} from "../config.js";

const README = "https://github.com/ayushratan1/vidforge#readme";
const SECRET = new Set(["anthropic_api_key", "github_token", "youtube_api_key", "youtube_client_secret", "youtube_refresh_token", "ig_access_token", "pexels_api_key", "pixabay_api_key"]);
const ENV = {anthropic_api_key: "ANTHROPIC_API_KEY", youtube_api_key: "YOUTUBE_API_KEY", youtube_client_id: "YOUTUBE_CLIENT_ID", youtube_client_secret: "YOUTUBE_CLIENT_SECRET", youtube_refresh_token: "YOUTUBE_REFRESH_TOKEN", ig_access_token: "IG_ACCESS_TOKEN", ig_user_id: "IG_USER_ID", pexels_api_key: "PEXELS_API_KEY", pixabay_api_key: "PIXABAY_API_KEY", github_token: "VF_GITHUB_TOKEN", github_repo: "VF_GITHUB_REPO", runner: "VF_RUNNER", models: "VF_MODELS"};

export function settingsPage(ctx, el, toolbar) {
  const {db} = ctx;
  let saved = {}, draft = {}, loaded = false;
  const saveBtn = h("button", {class: "btn primary", onClick: save}, "Save changes");
  const exportBtn = h("button", {class: "btn", onClick: exportEnv}, icon("download"), "Export .env");
  const mount = tb => tb.append(exportBtn, saveBtn);
  mount(toolbar);
  const body = h("div", {style: {maxWidth: "760px"}});
  el.append(body);

  async function load(force) {
    if (loaded && !force) return;
    saved = await db.getSettings(true);
    draft = {...saved}; delete draft.__updated;
    if (!draft.github_repo) draft.github_repo = DEFAULTS.githubRepo;
    loaded = true;
    render();
    updateSaveState();
  }
  const changed = () => Object.keys(draft).filter(k => (draft[k] || "") !== (saved[k] || ""));
  function updateSaveState() { const n = changed().length; saveBtn.disabled = !n; saveBtn.textContent = n ? `Save ${n} change${n > 1 ? "s" : ""}` : "Save changes"; }

  function input(key, placeholder, {mono = false, type = "text"} = {}) {
    const secret = SECRET.has(key);
    const inp = h("input", {class: "input" + (mono ? " mono" : ""), type: secret ? "password" : type, placeholder, autocomplete: "off", spellcheck: "false", value: draft[key] || "", "aria-label": key.replaceAll("_", " "), onInput: e => { draft[key] = e.target.value; updateSaveState(); state.replaceChildren(stateFor(key)); }});
    const state = h("span", {class: "footnote"}, stateFor(key));
    const wrap = h("div", {class: "input-wrap"}, inp);
    if (secret) wrap.append(h("button", {class: "btn plain sm reveal", type: "button", "aria-label": "Show value", onClick: ev => { const show = inp.type === "password"; inp.type = show ? "text" : "password"; ev.currentTarget.replaceChildren(icon(show ? "eyeOff" : "eye")); }}, icon("eye")));
    return {wrap, state, inp};
  }
  function stateFor(key) {
    if ((draft[key] || "") !== (saved[key] || "")) return h("span", {class: "secondary"}, "Not saved yet");
    if (saved[key]) return h("span", {class: "saved"}, icon("check"), "Saved", saved.__updated?.[key] ? " " + fmt.date(saved.__updated[key]) : "");
    return h("span", {class: "tertiary"}, "Not set");
  }
  function settingRow(key, title, placeholder, hint, extra = {}) {
    const {wrap, state} = input(key, placeholder, extra);
    return h("div", {class: "row stacked"}, h("div", {class: "row-head"}, h("div", {class: "row-title"}, title), state), wrap, hint ? h("div", {class: "hint"}, hint) : null, extra.after || null);
  }
  const group = (title, foot, ...rows) => h("section", {class: "group"}, h("div", {class: "group-title"}, title), h("div", {class: "list"}, ...rows), foot ? h("div", {class: "group-foot hint"}, foot) : null);
  const link = (href, text) => h("a", {href, target: "_blank", rel: "noopener"}, text);

  function render() {
    const models = parseModels(draft.models);
    const modelSel = role => h("select", {class: "input", "aria-label": role + " model", onChange: e => { models[role] = e.target.value; draft.models = Object.values(models).some(Boolean) ? JSON.stringify(Object.fromEntries(Object.entries(models).filter(([, v]) => v))) : ""; updateSaveState(); }},
      h("option", {value: ""}, "Default"), ...[["claude-opus-5-5", "Opus 5.5"], ["claude-fable-5-1", "Fable 5.1"], ["claude-sonnet-5-5", "Sonnet 5.5"]].map(([v, l]) => h("option", {value: v, selected: models[role] === v}, l)));
    const runner = segmented([{value: "", label: "GitHub standard"}, {value: "custom", label: "Custom"}], draft.runner && draft.runner !== "ubuntu-latest" ? "custom" : "", v => { draft.runner = v ? (saved.runner && saved.runner !== "ubuntu-latest" ? saved.runner : "self-hosted") : ""; runnerName.hidden = !v; runnerName.querySelector("input").value = draft.runner; updateSaveState(); });
    const runnerName = h("div", {hidden: !(draft.runner && draft.runner !== "ubuntu-latest")}, h("input", {class: "input mono", placeholder: "self-hosted or a larger runner label", value: draft.runner || "", "aria-label": "Runner label", onInput: e => { draft.runner = e.target.value; updateSaveState(); }}));

    const lookupOut = h("span", {class: "footnote secondary"});
    const lookup = h("button", {class: "btn sm", type: "button", onClick: async () => {
      const tok = draft.ig_access_token; if (!tok) { lookupOut.textContent = "Add an access token first."; return; }
      lookupOut.textContent = "Looking up";
      try { const r = await fetch(`https://graph.instagram.com/v26.0/me?fields=user_id,username&access_token=${encodeURIComponent(tok)}`); const j = await r.json(); if (j.error) throw new Error(j.error.message); draft.ig_user_id = String(j.user_id || j.id || ""); body.querySelector('[aria-label="ig user id"]').value = draft.ig_user_id; lookupOut.textContent = `@${j.username}`; updateSaveState(); }
      catch (e) { lookupOut.textContent = "Lookup failed: " + e.message; }
    }}, "Look up");

    clear(body).append(
      group("Claude", "The writer model can also be chosen per video on the Create page.",
        settingRow("anthropic_api_key", "API key", "sk-ant-...", h("span", {}, "From ", link("https://console.anthropic.com/settings/keys", "console.anthropic.com"), ". Every video costs about $0.50."), {mono: true}),
        h("div", {class: "row stacked"}, h("div", {class: "row-head"}, h("div", {class: "row-title"}, "Models per role"), h("span", {class: "footnote tertiary"}, "Optional")),
          h("div", {class: "form-row"}, ...["writer", "director", "reviewer", "scout"].map(r => h("div", {class: "field"}, h("label", {}, r.charAt(0).toUpperCase() + r.slice(1)), modelSel(r)))))),
      group("GitHub", "The token is used only to start workflows from this page. The worker itself uses the repository's own token.",
        settingRow("github_repo", "Repository", DEFAULTS.githubRepo, "The repository that runs the workflows, as owner/name."),
        settingRow("github_token", "Token", "github_pat_...", h("span", {}, link("https://github.com/settings/personal-access-tokens/new", "Create a fine-grained token"), " for only this repository with Actions read and write, Contents read."), {mono: true})),
      group("YouTube", h("span", {}, "Run ", h("code", {}, "python run.py youtube-auth client_secret.json"), " on your computer once; it prints the refresh token. The client id and secret come from the Google Cloud OAuth client (Desktop app)."),
        settingRow("youtube_client_id", "Client id", "....apps.googleusercontent.com", null, {mono: true}),
        settingRow("youtube_client_secret", "Client secret", "GOCSPX-...", null, {mono: true}),
        settingRow("youtube_refresh_token", "Refresh token", "1//0g...", null, {mono: true})),
      group("Instagram", "Needs a Business or Creator account linked to a Facebook Page, and a long-lived token with instagram_business_content_publish.",
        settingRow("ig_access_token", "Access token", "IGQW...", null, {mono: true}),
        settingRow("ig_user_id", "User id", "1784...", h("span", {}, "Optional. ", lookup, " ", lookupOut), {mono: true})),
      group("Footage", "Both are free. Without keys, videos use drawn frames only.",
        settingRow("pexels_api_key", "Pexels API key", "", link("https://www.pexels.com/api/new/", "Get a free Pexels key"), {mono: true}),
        settingRow("pixabay_api_key", "Pixabay API key", "", link("https://pixabay.com/api/docs/", "Get a free Pixabay key"), {mono: true})),
      group("Machine", "A GitHub standard runner is free for public repositories. A larger or self-hosted runner renders faster.",
        h("div", {class: "row stacked"}, h("div", {class: "row-head"}, h("div", {class: "row-title"}, "Runner"), runner), runnerName)),
      group("Trend data", "Lets the scout read what is rising on YouTube in your channels.",
        settingRow("youtube_api_key", "YouTube Data API key", "AIza...", link("https://console.cloud.google.com/apis/credentials", "Google Cloud credentials"), {mono: true})),
      group("Team", ctx.demo ? "Demo mode. Nothing is saved." : "Add or remove team members in Supabase, Authentication.",
        row({title: "Signed in as", value: ctx.user?.email || "", icon: "person"}),
        row({title: "Sign out", sub: "This device only", icon: "logout", onClick: async () => { await db.signOut(); location.reload(); }}),
        row({title: "Forget this project on this device", sub: "Goes back to the built-in project on next sign-in. Data stays in Supabase.", icon: "trash", iconColor: "var(--red)", onClick: () => { if (confirm("Forget the project connection on this device?")) { forgetProject(); location.reload(); } }})),
      h("p", {class: "footnote tertiary"}, "Keys are stored in your private Supabase project and read by the GitHub worker at run time. ", link(README, "Setup guide")));
  }

  async function save() {
    const patch = Object.fromEntries(changed().map(k => [k, draft[k] || ""]));
    saveBtn.disabled = true;
    try { saved = await db.saveSettings(patch); draft = {...saved}; delete draft.__updated; ctx.settings = saved; toast("Settings saved", "ok"); render(); }
    catch (e) { toast("Could not save: " + e.message + (e.hint ? " " + e.hint : ""), "err"); }
    finally { updateSaveState(); }
  }
  function exportEnv() {
    const lines = Object.entries(ENV).filter(([k]) => draft[k]).map(([k, env]) => `${env}=${quote(draft[k])}`);
    const blob = new Blob([`# VidForge settings exported ${new Date().toISOString()}\n` + lines.join("\n") + "\n"], {type: "text/plain"});
    const a = h("a", {href: URL.createObjectURL(blob), download: ".env"}); document.body.append(a); a.click(); a.remove();
    toast("Downloaded .env", "ok");
  }
  return {mount, async show() { await load(); }};
}

function parseModels(s) { try { return {...JSON.parse(s || "{}")}; } catch { return {}; } }
function quote(v) { return /[\s#"'\\$]/.test(v) ? JSON.stringify(v) : v; }
