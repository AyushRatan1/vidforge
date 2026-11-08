// Settings: macOS System Settings style. Titled groups, each a box of rows with the label on the left and the control on the right.
// Keys and the exported .env names are the contract with the worker; do not rename them.
import {h, clear, Button, Card, Segmented, Field, Input, Select, SecretInput, ListRow, Pill, toast, icon} from "../components.js";
import {forgetProject} from "../app.js";
import {DEFAULTS} from "../config.js";
import {fmt} from "../format.js";
import {redirectUri, startYouTubeAuth, takePendingYouTubeAuth, finishYouTubeAuth} from "../youtube-auth.js";

const README = "https://github.com/ayushratan1/vidforge#readme";
const SECRET = new Set(["anthropic_api_key", "github_token", "youtube_api_key", "youtube_client_secret", "youtube_refresh_token", "ig_access_token", "pexels_api_key", "pixabay_api_key"]);
const ENV = {anthropic_api_key: "ANTHROPIC_API_KEY", youtube_api_key: "YOUTUBE_API_KEY", youtube_client_id: "YOUTUBE_CLIENT_ID", youtube_client_secret: "YOUTUBE_CLIENT_SECRET", youtube_refresh_token: "YOUTUBE_REFRESH_TOKEN", ig_access_token: "IG_ACCESS_TOKEN", ig_user_id: "IG_USER_ID", pexels_api_key: "PEXELS_API_KEY", pixabay_api_key: "PIXABAY_API_KEY", github_token: "VF_GITHUB_TOKEN", github_repo: "VF_GITHUB_REPO", runner: "VF_RUNNER", models: "VF_MODELS", brand_name: "VF_BRAND_NAME", brand_handle: "VF_HANDLE", brand_hashtag: "VF_BRAND_TAG"};
const MODELS = [{value: "", label: "Default"}, {value: "claude-opus-5-5", label: "Opus 5.5"}, {value: "claude-fable-5-1", label: "Fable 5.1"}, {value: "claude-sonnet-5-5", label: "Sonnet 5.5"}];

export function settingsPage(ctx, el, actions) {
  const {db} = ctx;
  let saved = {}, draft = {}, loaded = false;
  const exportBtn = Button({label: "Export .env", variant: "secondary", icon: "download", onClick: exportEnv});
  const mount = tb => tb.append(exportBtn);
  mount(actions);
  const body = h("form", {class: "settings", autocomplete: "off", onSubmit: e => e.preventDefault()});
  const saveBtn = Button({label: "Save changes", variant: "primary", onClick: save});
  const discardBtn = Button({label: "Discard", variant: "ghost", onClick: () => { draft = {...saved}; delete draft.__updated; if (!draft.github_repo) draft.github_repo = DEFAULTS.githubRepo; render(); updateSaveState(); }});
  const saveNote = h("span", {class: "secondary"});
  const savebar = h("div", {class: "savebar", hidden: true, role: "region", "aria-label": "Unsaved changes"}, saveNote, h("div", {class: "actions"}, discardBtn, saveBtn));
  el.append(h("p", {class: "page-intro settings-intro"}, "Keys are stored in your private Supabase project and read by the GitHub worker at run time."), body, savebar);

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
  function updateSaveState() {
    const n = changed().length;
    savebar.hidden = !n;
    saveBtn.querySelector(".btn-label").textContent = n ? `Save ${n} change${n > 1 ? "s" : ""}` : "Save changes";
    saveNote.textContent = n ? `${n} unsaved change${n > 1 ? "s" : ""}` : "";
  }

  const states = {};
  function stateFor(key) {
    const el = h("span", {class: "saved-state"});
    if ((draft[key] || "") !== (saved[key] || "")) { el.classList.add("is-dirty"); el.append("Not saved yet"); }
    else if (saved[key]) { el.classList.add("is-saved"); el.append(icon("check", {size: 12}), "Saved", saved.__updated?.[key] ? " " + fmt.date(saved.__updated[key]) : ""); }
    else el.append("Not set");
    return el;
  }
  function settingRow(key, title, placeholder, hint, {mono = false, after = null} = {}) {
    const label = key.replaceAll("_", " ");
    const onInput = e => { draft[key] = e.target.value; updateSaveState(); states[key].replaceWith(states[key] = stateFor(key)); };
    const control = SECRET.has(key) ? SecretInput({value: draft[key] || "", placeholder, onInput, ariaLabel: label, mono}) : Input({class: "input" + (mono ? " mono" : ""), placeholder, autocomplete: "off", spellcheck: "false", value: draft[key] || "", "aria-label": label, onInput});
    states[key] = stateFor(key);
    return h("div", {class: "field"}, h("div", {class: "field-label"}, h("div", {}, title), states[key]), control, hint ? h("div", {class: "hint"}, hint) : null, after);
  }
  const link = (href, text) => h("a", {href, target: "_blank", rel: "noopener"}, text);
  const groupCard = (title, subtitle, ic, foot, ...rows) => h("section", {class: "settings-group", "aria-label": title},
    h("h2", {class: "settings-group-title"}, title, h("span", {class: "micro", style: {fontWeight: 400, marginLeft: "8px"}}, subtitle)),
    Card({flush: true, body: h("div", {class: "rows"}, ...rows)}),
    foot ? h("p", {class: "settings-note"}, foot) : null);

  function render() {
    const models = parseModels(draft.models);
    const modelSel = role => Select(MODELS, models[role] || "", v => { models[role] = v; draft.models = Object.values(models).some(Boolean) ? JSON.stringify(Object.fromEntries(Object.entries(models).filter(([, x]) => x))) : ""; updateSaveState(); }, {"aria-label": role + " model"});
    const isCustom = draft.runner && draft.runner !== "ubuntu-latest";
    const runnerName = Input({class: "input mono", placeholder: "self-hosted or a larger runner label", value: draft.runner || "", "aria-label": "Runner label", onInput: e => { draft.runner = e.target.value; updateSaveState(); }});
    const runnerWrap = h("div", {hidden: !isCustom}, runnerName);
    const runner = Segmented([{value: "", label: "GitHub standard"}, {value: "custom", label: "Custom"}], isCustom ? "custom" : "", v => { draft.runner = v ? (saved.runner && saved.runner !== "ubuntu-latest" ? saved.runner : "self-hosted") : ""; runnerWrap.hidden = !v; runnerName.value = draft.runner; updateSaveState(); }, {size: "sm", ariaLabel: "Runner"});

    const lookupOut = h("span", {class: "micro"});
    const lookup = Button({label: "Look up", variant: "secondary", size: "sm", onClick: async () => {
      const tok = draft.ig_access_token; if (!tok) { lookupOut.textContent = "Add an access token first."; return; }
      lookupOut.textContent = "Looking up";
      try { const r = await fetch(`https://graph.instagram.com/v26.0/me?fields=user_id,username&access_token=${encodeURIComponent(tok)}`); const j = await r.json(); if (j.error) throw new Error(j.error.message); draft.ig_user_id = String(j.user_id || j.id || ""); body.querySelector('[aria-label="ig user id"]').value = draft.ig_user_id; lookupOut.textContent = `@${j.username}`; updateSaveState(); states.ig_user_id.replaceWith(states.ig_user_id = stateFor("ig_user_id")); }
      catch (e) { lookupOut.textContent = "Lookup failed: " + e.message; }
    }});

    clear(body).append(
      groupCard("Brand", "Shown on every video and in every caption", "play", "Leave empty to use the built-in channel names. A handle typed on the Create page wins for that one video.",
        settingRow("brand_name", "Channel name", "Hypercurious", "Used for the series badge Claude puts in the first scene."),
        settingRow("brand_handle", "Handle", "@hypercurious96", "Printed small at the bottom of every frame."),
        settingRow("brand_hashtag", "Brand hashtag", "#Hypercurious", "Added to every post, within the 5 hashtag limit.")),
      groupCard("Claude", "Writes, directs, reviews and scouts", "sparkles", "The writer model can also be chosen per video on the Create page.",
        settingRow("anthropic_api_key", "API key", "sk-ant-...", h("span", {}, "From ", link("https://console.anthropic.com/settings/keys", "console.anthropic.com"), ". Every video costs about $0.50."), {mono: true}),
        ...["writer", "director", "reviewer", "scout"].map(r => Field({label: r.charAt(0).toUpperCase() + r.slice(1) + " model", control: modelSel(r), hint: r === "writer" ? "Optional. Default uses the model the worker picks for each role." : null}))),
      groupCard("GitHub", "Runs the worker", "github", "The token is used only to start workflows from this page. The worker itself uses the repository's own token.",
        settingRow("github_repo", "Repository", DEFAULTS.githubRepo, "The repository that runs the workflows, as owner/name.", {mono: true}),
        settingRow("github_token", "Token", "github_pat_...", h("span", {}, link("https://github.com/settings/personal-access-tokens/new", "Create a fine-grained token"), " for only this repository with Actions read and write, Contents read."), {mono: true})),
      groupCard("YouTube", "Shorts upload", "youtube", h("span", {}, "Use a Google Cloud OAuth client of type Web application with the redirect URI ", h("code", {}, redirectUri()), ". Paste its id and secret, save, then press Connect and pick your channel."),
        settingRow("youtube_client_id", "Client id", "....apps.googleusercontent.com", null, {mono: true}),
        settingRow("youtube_client_secret", "Client secret", "GOCSPX-...", null, {mono: true}),
        youtubeConnectRow(),
        settingRow("youtube_refresh_token", "Refresh token", "Filled in by Connect", "Set automatically when you connect. Paste one only if you made it some other way.", {mono: true})),
      groupCard("Instagram", "Reels upload", "instagram", "Needs a Business or Creator account linked to a Facebook Page, and a long-lived token with instagram_business_content_publish.",
        settingRow("ig_access_token", "Access token", "IGQW...", null, {mono: true}),
        settingRow("ig_user_id", "User id", "1784...", h("span", {class: "cluster", style: {gap: "8px"}}, "Optional. ", lookup, lookupOut), {mono: true})),
      groupCard("Footage", "Free stock clips", "image", "Both are free for commercial use with no attribution required. Without a key, videos use drawn frames only.",
        settingRow("pixabay_api_key", "Pixabay API key", "", link("https://pixabay.com/api/docs/", "Get a free Pixabay key"), {mono: true}),
        settingRow("pexels_api_key", "Pexels API key", "", h("span", {class: "cluster", style: {gap: "8px"}}, Pill("Paused for new keys"), "Pexels paused new API keys in Nov 2026. Leave empty unless you already have one."), {mono: true})),
      groupCard("Machine", "Where renders run", "server", "A GitHub standard runner is free for public repositories. A larger or self-hosted runner renders faster.",
        h("div", {class: "field"}, h("div", {class: "field-label"}, "Runner"), h("div", {}, runner), runnerWrap)),
      groupCard("Trend data", "What the scout can read", "compass", "Lets the scout read what is rising on YouTube in your channels.",
        settingRow("youtube_api_key", "YouTube Data API key", "AIza...", link("https://console.cloud.google.com/apis/credentials", "Google Cloud credentials"), {mono: true})),
      groupCard("Team", "This device and project", "users", ctx.demo ? "Demo mode. Nothing is saved." : "Add or remove team members in Supabase, Authentication.",
        ListRow({title: "Signed in as", value: ctx.user?.email || ""}),
        ListRow({title: "Sign out", sub: "This device only", onClick: async () => { await db.signOut(); location.hash = "#/"; location.reload(); }}),
        ListRow({title: "Forget this project on this device", sub: "Goes back to the built-in project on next sign-in. Data stays in Supabase.", iconTone: "err", onClick: () => { if (confirm("Forget the project connection on this device?")) { forgetProject(); location.reload(); } }})),
      h("p", {class: "settings-note"}, "Settings keys are read by the GitHub worker at run time. ", link(README, "Setup guide")));
  }

  function youtubeConnectRow() {
    const [title, id] = (saved.youtube_channel || "").split("|");
    const ready = saved.youtube_client_id && saved.youtube_client_secret;
    const status = saved.youtube_refresh_token
      ? h("span", {class: "saved-state is-saved"}, icon("check", {size: 12}), title ? "Connected to " + title : "Connected")
      : h("span", {class: "saved-state"}, ready ? "Not connected" : "Save the client id and secret first");
    const btn = Button({label: saved.youtube_refresh_token ? "Reconnect" : "Connect YouTube", variant: saved.youtube_refresh_token ? "secondary" : "primary", size: "sm", icon: "youtube", disabled: !ready || changed().some(k => k.startsWith("youtube_client")),
      onClick: () => startYouTubeAuth(saved.youtube_client_id)});
    return h("div", {class: "field"}, h("div", {class: "field-label"}, h("div", {}, "Channel"), status),
      h("div", {class: "cluster", style: {gap: "8px"}}, btn, id ? h("a", {href: "https://www.youtube.com/channel/" + id, target: "_blank", rel: "noopener", class: "micro"}, "Open channel") : null),
      h("div", {class: "hint"}, "Opens Google sign-in. Choose the account and then the channel videos should go to."));
  }

  async function finishYouTube() {
    const pending = takePendingYouTubeAuth();
    if (!pending) return;
    try {
      const {refresh_token, channel} = await finishYouTubeAuth(pending, saved.youtube_client_id || "", saved.youtube_client_secret || "");
      saved = await db.saveSettings({youtube_refresh_token: refresh_token, youtube_channel: channel});
      draft = {...saved}; delete draft.__updated; if (!draft.github_repo) draft.github_repo = DEFAULTS.githubRepo; ctx.settings = saved;
      toast(channel ? `YouTube connected: ${channel.split("|")[0]}` : "YouTube connected", "ok");
      render(); updateSaveState();
    } catch (e) { toast("YouTube not connected: " + e.message, "err", {timeout: 12000}); }
  }

  async function save() {
    const patch = Object.fromEntries(changed().map(k => [k, draft[k] || ""]));
    saveBtn.setBusy(true);
    try { saved = await db.saveSettings(patch); draft = {...saved}; delete draft.__updated; if (!draft.github_repo) draft.github_repo = DEFAULTS.githubRepo; ctx.settings = saved; toast("Settings saved", "ok"); render(); }
    catch (e) { toast("Could not save: " + e.message + (e.hint ? " " + e.hint : ""), "err"); }
    finally { saveBtn.setBusy(false); updateSaveState(); }
  }
  function exportEnv() {
    const lines = Object.entries(ENV).filter(([k]) => draft[k]).map(([k, env]) => `${env}=${quote(draft[k])}`);
    const blob = new Blob([`# VidForge settings exported ${new Date().toISOString()}\n` + lines.join("\n") + "\n"], {type: "text/plain"});
    const a = h("a", {href: URL.createObjectURL(blob), download: ".env"}); document.body.append(a); a.click(); a.remove();
    toast("Downloaded .env", "ok");
  }
  return {mount, refresh: () => changed().length ? toast("Save or discard your changes first.", "info") : load(true), async show() { await load(); await finishYouTube(); }};
}

function parseModels(s) { try { return {...JSON.parse(s || "{}")}; } catch { return {}; } }
function quote(v) { return /[\s#"'\\$]/.test(v) ? JSON.stringify(v) : v; }
