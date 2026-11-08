// Create: "Make one now" (fields, options and dispatch identical in meaning to the worker contract) and "Autopilot" plan.
// Layout: grouped boxes with a label column on the left, controls on the right (macOS System Settings style).
import {h, clear, Button, Card, Segmented, Switch, ChipGroup, Stepper, Field, Input, Textarea, Select, Status, Pill, ProgressRing, StepList, ListRow, EmptyState, toast, icon} from "../components.js";
import {DRAFT_WF} from "../db.js";
import {fmt, LANGS, NICHES, FORMATS, WRITERS, VOICES, MUSIC, STAGES, opts, langName, nicheName, compactTs, rand4, stageIndex} from "../format.js";

export function createPage(ctx, el, actions) {
  let mode = "one";
  const seg = Segmented([{value: "one", label: "Make one now"}, {value: "autopilot", label: "Autopilot"}], mode, v => setMode(v), {size: "sm", ariaLabel: "Mode"});
  const mount = tb => tb.append(seg);
  mount(actions);

  const one = h("div", {});
  const auto = h("div", {hidden: true});
  el.append(one, auto);
  function setMode(v) { mode = v; seg.set(v); one.hidden = v !== "one"; auto.hidden = v !== "autopilot"; if (v === "autopilot") autopilot.load(); const hash = "#/create" + (v === "autopilot" ? "/autopilot" : ""); if (location.hash !== hash) history.replaceState(null, "", location.pathname + location.search + hash); }

  buildMakeOne(ctx, one);
  const autopilot = buildAutopilot(ctx, auto);
  return {mount, async show(arg) { setMode(arg === "autopilot" ? "autopilot" : "one"); }};
}

const PRIVACY = [{value: "public", label: "Public"}, {value: "unlisted", label: "Unlisted"}, {value: "private", label: "Private"}];
const LENGTHS = [20, 30, 45, 60, 90].map(n => ({value: n, label: n + "s"}));
const FOOTAGE = [{value: "auto", label: "Real footage"}, {value: "off", label: "Drawn only"}];
const ASPECTS = [{value: "9:16", label: "9:16"}, {value: "16:9", label: "16:9"}, {value: "1:1", label: "1:1"}];
const group = (label, control, hint) => Field({label, control, hint});
const rows = (...children) => h("div", {class: "rows"}, ...children);
const more = (summary, ...children) => h("details", {class: "disclosure disclosure-row"}, h("summary", {}, icon("chevronRight", {size: 14}), summary), rows(...children));
const num = v => /^\d+$/.test(String(v).trim()) ? Number(v) : v;

// ------------------------------------------------------------------ Make one now
function buildMakeOne(ctx, host) {
  const {db} = ctx;
  const st = {language: "en", niche: "space", format: "auto", footage: "auto", writer: "claude-opus-5-5", voice: "auto", music: "auto", aspect: "9:16", length: 45, publish: {youtube: false, instagram: false, privacy: "public", publish_at: ""}};

  const topic = Textarea({rows: 3, placeholder: "What should the video be about? Leave empty and Claude picks something trending in the channel.", maxlength: 500});
  const lang = ChipGroup(opts(LANGS), st.language, {custom: true, onChange: v => st.language = v, ariaLabel: "Language"});
  const niche = ChipGroup(opts(NICHES), st.niche, {custom: true, onChange: v => st.niche = v, ariaLabel: "Channel"});
  const format = ChipGroup(opts(FORMATS), st.format, {custom: true, onChange: v => st.format = v, ariaLabel: "Format"});
  const footage = ChipGroup(FOOTAGE, st.footage, {custom: true, onChange: v => st.footage = v, ariaLabel: "Footage"});
  const writer = ChipGroup(opts(WRITERS), st.writer, {custom: true, onChange: v => st.writer = v, ariaLabel: "Writer model"});
  const voice = Select(opts(VOICES), st.voice, v => st.voice = v, {"aria-label": "Voice"});
  const music = Select(opts(MUSIC), st.music, v => st.music = v, {"aria-label": "Music"});
  const aspect = ChipGroup(ASPECTS, st.aspect, {custom: true, onChange: v => st.aspect = v, ariaLabel: "Aspect"});
  const length = ChipGroup(LENGTHS, st.length, {custom: true, onChange: v => st.length = num(v), ariaLabel: "Length"});
  const handle = Input({placeholder: "@yourchannel"});
  const hashtags = Input({placeholder: "#space #facts"});
  const notes = Textarea({rows: 2, placeholder: "Anything the writer should know: tone, things to avoid, a hook you like."});

  const yt = Switch(false, v => st.publish.youtube = v, "Post to YouTube");
  const ig = Switch(false, v => st.publish.instagram = v, "Post to Instagram");
  const privacy = Segmented(PRIVACY, "public", v => st.publish.privacy = v, {size: "sm", ariaLabel: "Privacy"});
  const when = Input({type: "datetime-local", "aria-label": "Schedule", onChange: e => st.publish.publish_at = e.target.value ? new Date(e.target.value).toISOString() : ""});

  const makeBtn = Button({label: "Make video", variant: "primary", size: "lg", onClick: make});

  const publishCard = Card({title: "Post when ready", subtitle: "Leave both off to keep the video in the library", flush: true, body: rows(
    ListRow({title: "YouTube Shorts", sub: "Posts as soon as the render passes review", icon: "youtube", control: yt}),
    ListRow({title: "Instagram Reels", sub: "Needs a Business or Creator account", icon: "instagram", control: ig}),
    ListRow({title: "Privacy", control: privacy}),
    ListRow({title: "Schedule", sub: "Leave empty to post right away", control: h("div", {style: {width: "220px", maxWidth: "50vw"}}, when)}))});

  const form = h("div", {class: "create-main"},
    Card({title: "Brief", flush: true, body: rows(
      group("Topic", topic, "Optional. The scout picks a trending topic in the channel when this is empty."),
      group("Language", lang), group("Channel", niche), group("Format", format),
      group("Footage", footage, "Real footage uses free clips from Pixabay (and Pexels if you have a key) when they fit. Drawn only keeps every frame generated."))}),
    Card({title: "More options", subtitle: "Writer, voice, music, aspect, length", flush: true, body: more("Show options",
      group("Writer model", writer), group("Voice", voice), group("Music", music),
      group("Aspect", aspect), group("Length", length),
      group("Handle", handle), group("Extra hashtags", hashtags), group("Notes", notes))}),
    publishCard,
    h("div", {class: "submit-row"}, makeBtn, h("span", {class: "create-cost"}, "8 to 12 minutes on GitHub. About $0.50 in Claude credits.")));

  // Preview frame and progress
  const screen = h("div", {class: "phone-screen"});
  const phone = h("div", {class: "phone", role: "figure", "aria-label": "Preview"}, screen);
  const statusBody = h("div", {class: "stack-sm"});
  const statusCard = Card({class: "create-status", title: "Progress", subtitle: "Each step is marked as the worker gets to it", body: statusBody});
  const idle = () => { clear(screen).append(h("div", {class: "phone-idle"}, h("strong", {}, "Your video shows up here"), "Pick a topic and press Make video.")); clear(statusBody).append(StepList(STAGES.slice(0, 7), -1, {compact: true})); };
  idle();
  host.append(h("div", {class: "create-grid"}, form, h("aside", {class: "create-side"}, phone, statusCard)));

  let unsubs = [], pollTimer = null, current = null;
  function cleanup() { unsubs.forEach(u => u()); unsubs = []; clearInterval(pollTimer); pollTimer = null; }
  const capital = s => s.charAt(0).toUpperCase() + s.slice(1);

  function renderProgress(job, video) {
    const status = video?.status || job?.status;
    const stage = (video?.stage || job?.stage || "").toLowerCase();
    const wantsPost = current?.options.publish?.youtube || current?.options.publish?.instagram;
    const stages = wantsPost ? STAGES : STAGES.slice(0, 7);
    let activeIdx = stageIndex(stages, stage);
    const failed = status === "failed" || job?.status === "failed";
    const done = status === "ready" || status === "posted" || job?.status === "done";
    if (done) activeIdx = stages.length;
    else if (activeIdx < 0 && stage && stage !== "queued") activeIdx = stages.length - 1;
    const headline = failed ? "Something went wrong" : done ? (status === "posted" ? "Posted" : "Ready") : job?.status === "queued" ? "Waiting for a runner" : "Making your video";
    statusCard.querySelector(".card-title").textContent = headline;
    statusCard.querySelector(".card-sub").textContent = current?.id || "";

    clear(statusBody).append(StepList(stages, Math.max(0, activeIdx), {done, failed, compact: true}));
    if (failed) statusBody.append(h("div", {class: "form-error"}, icon("warning", {size: 14}), h("span", {}, (job?.error || video?.error || "The run failed."), job?.run_url ? [" ", h("a", {href: job.run_url, target: "_blank", rel: "noopener"}, "Open the run log")] : null)));
    if (job?.run_url && !failed) statusBody.append(h("a", {class: "hint", href: job.run_url, target: "_blank", rel: "noopener"}, "Watch the run on GitHub"));

    if (done && video?.video_url) {
      if (!screen.querySelector("video")) clear(screen).append(h("video", {src: video.video_url, poster: video.thumb_url || null, controls: true, playsinline: true, autoplay: true, muted: true, loop: true}));
      statusBody.append(h("div", {class: "actions", style: {marginTop: "8px"}}, Button({label: "Open in Library", variant: "secondary", size: "sm", onClick: () => ctx.go("library", video.id)}), Button({label: "Make another", variant: "ghost", size: "sm", onClick: () => { cleanup(); current = null; idle(); statusCard.querySelector(".card-title").textContent = "Progress"; statusCard.querySelector(".card-sub").textContent = "Each step is marked as the worker gets to it"; makeBtn.disabled = false; }})));
    } else if (!done) {
      const pct = failed ? Math.max(0, activeIdx) / stages.length : Math.max(0.03, Math.max(0, activeIdx) / stages.length);
      const title = video?.title && video.title !== current?.options.topic ? video.title : (current?.options.topic || "Finding a trending topic");
      let overlay = screen.querySelector(".phone-overlay");
      if (!overlay) { clear(screen); overlay = h("div", {class: "phone-overlay"}); screen.append(overlay); }
      clear(overlay).append(ProgressRing({value: pct, size: 72, stroke: 3, label: "Run progress"}), h("div", {class: "phone-overlay-title"}, title), h("div", {class: "phone-overlay-stage"}, failed ? "Failed" : stage ? capital(stage) : "Queued"));
      if (failed) statusBody.append(Button({label: "Try again", variant: "secondary", size: "sm", onClick: () => { cleanup(); current = null; idle(); makeBtn.disabled = false; }}));
    }
  }

  async function make() {
    const rid = "v-" + compactTs() + rand4();
    const options = {
      language: st.language, niche: st.niche, format: st.format, topic: topic.value.trim(), footage: st.footage,
      writer: st.writer, voice: st.voice, music: st.music, aspect: st.aspect, length: st.length,
      handle: handle.value.trim(), hashtags: hashtags.value.split(/[\s,]+/).filter(Boolean).map(t => t.startsWith("#") ? t : "#" + t), notes: notes.value.trim(),
      publish: {...st.publish},
    };
    makeBtn.disabled = true;
    cleanup();
    current = {id: rid, options};
    let job = {id: rid, status: "queued", stage: ""};
    renderProgress(job, null);
    try {
      await db.insertJob({id: rid, kind: "make", status: "queued", options});
      await db.dispatch(DRAFT_WF, {request_id: rid, options: JSON.stringify({...options, job_id: rid, source: "manual"})});
      toast("Video queued on GitHub", "ok");
    } catch (e) {
      job = {id: rid, status: "failed", stage: "Find trend", error: e.message + (e.hint ? " " + e.hint : "")};
      renderProgress(job, null); makeBtn.disabled = false; return;
    }
    let video = null;
    const onJob = j => { job = j; renderProgress(job, video); if (j.status === "done" || j.status === "failed") clearInterval(pollTimer); };
    const onVideo = v => { video = v; renderProgress(job, video); };
    unsubs = [db.subscribe("jobs", rid, onJob), db.subscribe("videos", rid, onVideo)];
    pollTimer = setInterval(async () => {
      const [j, v] = await Promise.all([db.listJobs(50).then(js => js.find(x => x.id === rid)), db.getVideo(rid)]);
      if (j) job = j; if (v) video = v; renderProgress(job, video);
      if (job.status === "done" || job.status === "failed" || video?.status === "ready" || video?.status === "posted") clearInterval(pollTimer);
    }, 10000);
  }
}

// ------------------------------------------------------------------ Autopilot
function buildAutopilot(ctx, host) {
  const {db} = ctx;
  let ap = null, loaded = false, dirty = false;
  const saveBtn = Button({label: "Save changes", variant: "primary", size: "lg", onClick: save});
  const savedNote = h("span", {class: "saved-state"});
  const body = h("div", {class: "create-main autopilot"});
  host.append(body);

  async function load() {
    if (loaded) return;
    ap = (await db.getAutopilot()) || {};
    ap = {enabled: false, videos_per_day: 3, post_hours: [9, 13, 18, 21], platforms: {youtube: true, instagram: true}, languages: ["en"], niches: ["space"], topics: [], trending_fill: true, privacy: "public", options: {}, ...ap};
    ap.options = {voice: "auto", music: "auto", length: 45, hashtags: [], notes: "", footage: "auto", ...(ap.options || {})};
    loaded = true;
    render();
  }
  const mark = () => { dirty = true; savedNote.className = "saved-state is-dirty"; clear(savedNote).append("Unsaved changes"); };

  function render() {
    const enabled = Switch(ap.enabled, v => { ap.enabled = v; mark(); }, "Autopilot on");
    const perDay = Stepper(ap.videos_per_day, 1, 6, v => { ap.videos_per_day = v; mark(); }, {label: "videos per day"});
    const hours = ChipGroup([...Array(18)].map((_, i) => ({value: i + 6, label: fmt.hour(i + 6)})), ap.post_hours, {multi: true, small: true, onChange: v => { ap.post_hours = v.sort((a, b) => a - b); mark(); }, ariaLabel: "Post times"});
    const ytT = Switch(ap.platforms?.youtube, v => { ap.platforms = {...ap.platforms, youtube: v}; mark(); }, "YouTube");
    const igT = Switch(ap.platforms?.instagram, v => { ap.platforms = {...ap.platforms, instagram: v}; mark(); }, "Instagram");
    const langs = ChipGroup(opts(LANGS), ap.languages, {multi: true, custom: true, onChange: v => { ap.languages = v; mark(); }, ariaLabel: "Languages"});
    const niches = ChipGroup(opts(NICHES), ap.niches, {multi: true, custom: true, onChange: v => { ap.niches = v; mark(); }, ariaLabel: "Channels"});
    const privacy = Segmented(PRIVACY, ap.privacy, v => { ap.privacy = v; mark(); }, {size: "sm", ariaLabel: "Privacy"});
    const o = ap.options;
    const voice = Select(opts(VOICES), o.voice, v => { o.voice = v; mark(); }, {"aria-label": "Voice"});
    const music = Select(opts(MUSIC), o.music, v => { o.music = v; mark(); }, {"aria-label": "Music"});
    const length = ChipGroup(LENGTHS, Number(o.length) || 45, {custom: true, onChange: v => { o.length = num(v); mark(); }, ariaLabel: "Length"});
    const footage = ChipGroup(FOOTAGE, o.footage || "auto", {custom: true, onChange: v => { o.footage = v; mark(); }, ariaLabel: "Footage"});
    const hashtags = Input({value: (o.hashtags || []).join(" "), placeholder: "#shorts #india", onInput: e => { o.hashtags = e.target.value.split(/[\s,]+/).filter(Boolean).map(t => t.startsWith("#") ? t : "#" + t); mark(); }});
    const notes = Textarea({rows: 2, value: o.notes || "", placeholder: "Standing instructions for the writer", onInput: e => { o.notes = e.target.value; mark(); }});
    const trending = Switch(ap.trending_fill, v => { ap.trending_fill = v; mark(); }, "Pick trending topics when the queue is empty");

    // topic queue
    const addBox = Textarea({rows: 3, placeholder: "Add topics, one per line", "aria-label": "New topics"});
    const queueList = h("div", {class: "list topic-list"});
    const queueCount = h("span", {class: "micro"});
    const renderQueue = () => {
      clear(queueList);
      const open = ap.topics.filter(t => t.status !== "done").length;
      queueCount.textContent = ap.topics.length ? `${open} waiting, ${ap.topics.length - open} done` : "";
      if (!ap.topics.length) { queueList.append(EmptyState({title: "The queue is empty.", text: ap.trending_fill ? "Autopilot picks trending topics in your channels until you add some." : "Add topics above, or turn on trending topics so autopilot never idles.", compact: true})); return; }
      ap.topics.forEach((t, i) => {
        const status = t.status || "queued";
        const langSel = h("select", {class: "mini-select", "aria-label": "Language", onChange: e => { t.language = e.target.value; mark(); }}, ...LANGS.map(([v, l]) => h("option", {value: v, selected: v === (t.language || ap.languages[0])}, l)));
        const nicheSel = h("select", {class: "mini-select", "aria-label": "Channel", onChange: e => { t.niche = e.target.value; mark(); }}, ...NICHES.map(([v, l]) => h("option", {value: v, selected: v === (t.niche || ap.niches[0])}, l)));
        queueList.append(ListRow({title: t.text,
          sub: h("span", {class: "topic-meta"}, Status(status === "running" ? "making" : status === "done" ? "done" : "queued"),
            status === "queued" ? [langSel, nicheSel] : h("span", {}, langName(t.language), ", ", nicheName(t.niche)),
            t.video_id ? Button({label: "Open video", variant: "ghost", size: "sm", onClick: () => ctx.go("library", t.video_id)}) : null),
          control: Button({variant: "icon", icon: "x", size: "sm", ariaLabel: `Remove topic: ${t.text}`, onClick: () => { ap.topics.splice(i, 1); mark(); renderQueue(); }})}));
      });
    };
    renderQueue();
    const addBtn = Button({label: "Add", variant: "secondary", onClick: () => {
      const lines = addBox.value.split("\n").map(s => s.trim()).filter(Boolean);
      if (!lines.length) { addBox.focus(); return; }
      for (const text of lines) ap.topics.push({text, language: ap.languages[0] || "en", niche: ap.niches[0] || "space", status: "queued"});
      addBox.value = ""; mark(); renderQueue();
    }});

    clear(body).append(
      Card({title: "Plan", subtitle: "Runs hourly on GitHub and posts at the hours you pick", flush: true, actions: Pill(ap.enabled ? "On" : "Off", ap.enabled ? "strong" : "neutral"), body: rows(
        ListRow({title: "Autopilot on", sub: "Turn off to pause without losing the plan", control: enabled}),
        ListRow({title: "Videos per day", control: perDay}),
        ListRow({title: "Post times", sub: "IST", stacked: true, body: hours}),
        ListRow({title: "YouTube Shorts", icon: "youtube", control: ytT}),
        ListRow({title: "Instagram Reels", icon: "instagram", control: igT}),
        ListRow({title: "Privacy", control: privacy}))}),
      Card({title: "What to make", flush: true, body: rows(group("Languages", langs, "Autopilot rotates through these."), group("Channels", niches))}),
      Card({title: "Defaults for every video", flush: true, body: more("Show defaults",
        group("Voice", voice), group("Music", music), group("Length", length), group("Footage", footage), group("Hashtags", hashtags), group("Notes", notes))}),
      Card({title: "Topic queue", subtitle: "Used in order, then trending topics if allowed", flush: true, actions: queueCount, body: rows(
        h("div", {class: "topic-add"}, addBox, h("div", {class: "cluster", style: {justifyContent: "flex-end"}}, addBtn)),
        queueList,
        ListRow({title: "When the queue is empty, pick trending topics", sub: "Claude scouts what is rising in your channels", control: trending}))}),
      h("div", {class: "submit-row"}, saveBtn, savedNote));
  }

  async function save() {
    saveBtn.setBusy(true);
    try {
      const {updated_at, last_run_at, ...rest} = ap;
      ap = {...ap, ...(await db.saveAutopilot(rest))};
      dirty = false; savedNote.className = "saved-state is-saved"; clear(savedNote).append(icon("check", {size: 12}), "Saved " + fmt.dateTime(new Date().toISOString()));
      toast(ap.enabled ? "Autopilot is on" : "Autopilot plan saved", "ok");
    } catch (e) { toast("Could not save: " + e.message, "err"); }
    finally { saveBtn.setBusy(false); }
  }
  return {load};
}
