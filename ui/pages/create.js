import {h, clear, icon, segmented, toggle, chips, stepper, field, row, toast, fmt, LANGS, NICHES, FORMATS, WRITERS, opts, langName, nicheName} from "../ui.js";
import {DRAFT_WF} from "../db.js";

const VOICES = [["auto", "Auto"], ["af_heart", "Heart (warm)"], ["af_bella", "Bella (bright)"], ["am_adam", "Adam (deep)"], ["hf_alpha", "Alpha (Hindi)"], ["hm_omega", "Omega (Hindi)"]];
const MUSIC = [["auto", "Auto"], ["none", "None"], ["calm", "Calm"], ["upbeat", "Upbeat"], ["epic", "Epic"], ["playful", "Playful"]];
const STAGES = ["Find trend", "Research", "Write and direct", "Review frames", "Render video", "Write captions and hashtags", "Save to library", "Post to YouTube and Instagram"];

export function createPage(ctx, el, toolbar) {
  const {db} = ctx;
  let mode = "one";
  const seg = segmented([{value: "one", label: "Make one now"}, {value: "autopilot", label: "Autopilot"}], mode, v => setMode(v));
  const mount = tb => tb.append(seg);
  mount(toolbar);

  const one = h("div", {});
  const auto = h("div", {hidden: true});
  el.append(one, auto);
  function setMode(v) { mode = v; seg.set(v); one.hidden = v !== "one"; auto.hidden = v !== "autopilot"; if (v === "autopilot") autopilot.load(); }

  buildMakeOne(ctx, one);
  const autopilot = buildAutopilot(ctx, auto);

  return {mount, async show(arg) { setMode(arg === "autopilot" ? "autopilot" : "one"); }};
}

// ------------------------------------------------------------------ Make one now
function buildMakeOne(ctx, host) {
  const {db} = ctx;
  const st = {language: "en", niche: "space", format: "auto", footage: "auto", writer: "claude-opus-5-5", voice: "auto", music: "auto", aspect: "9:16", length: 45, publish: {youtube: false, instagram: false, privacy: "public", publish_at: ""}};

  const topic = h("textarea", {class: "input", rows: 3, placeholder: "What should the video be about? Leave empty and Claude picks something trending in the channel.", maxlength: 500});
  const lang = chips(opts(LANGS), st.language, {custom: true, onChange: v => st.language = v});
  const niche = chips(opts(NICHES), st.niche, {custom: true, onChange: v => st.niche = v});
  const format = chips(opts(FORMATS), st.format, {custom: true, onChange: v => st.format = v});
  const footage = chips([{value: "auto", label: "Real footage"}, {value: "off", label: "Drawn only"}], st.footage, {onChange: v => st.footage = v});
  const writer = chips(opts(WRITERS), st.writer, {onChange: v => st.writer = v});
  const voice = h("select", {class: "input", onChange: e => st.voice = e.target.value}, ...VOICES.map(([v, l]) => h("option", {value: v}, l)));
  const music = h("select", {class: "input", onChange: e => st.music = e.target.value}, ...MUSIC.map(([v, l]) => h("option", {value: v}, l)));
  const aspect = chips([{value: "9:16", label: "9:16"}, {value: "16:9", label: "16:9"}, {value: "1:1", label: "1:1"}], st.aspect, {onChange: v => st.aspect = v});
  const length = chips([20, 30, 45, 60, 90].map(n => ({value: n, label: n + "s"})), st.length, {onChange: v => st.length = v});
  const handle = h("input", {class: "input", placeholder: "@yourchannel"});
  const hashtags = h("input", {class: "input", placeholder: "#space #facts"});
  const notes = h("textarea", {class: "input", rows: 2, placeholder: "Anything the writer should know: tone, things to avoid, a hook you like."});

  const yt = toggle(false, v => st.publish.youtube = v, "Post to YouTube");
  const ig = toggle(false, v => st.publish.instagram = v, "Post to Instagram");
  const privacy = segmented([{value: "public", label: "Public"}, {value: "unlisted", label: "Unlisted"}, {value: "private", label: "Private"}], "public", v => st.publish.privacy = v);
  const when = h("input", {class: "input", type: "datetime-local", onChange: e => st.publish.publish_at = e.target.value ? new Date(e.target.value).toISOString() : ""});

  const makeBtn = h("button", {class: "btn primary lg", type: "button", onClick: make}, icon("sparkle"), "Make video");

  const publishBox = h("div", {class: "publish-box"},
    row({title: "YouTube Shorts", sub: "Posts as soon as the render passes review", icon: "youtube", iconColor: "#FF453A", control: yt}),
    row({title: "Instagram Reels", sub: "Needs a Business or Creator account", icon: "instagram", iconColor: "#FF375F", control: ig}),
    row({title: "Privacy", control: privacy}),
    row({title: "Schedule", sub: "Leave empty to post right away", control: h("div", {style: {width: "230px"}}, when)}));

  const form = h("div", {class: "form"},
    field("Topic", topic),
    h("div", {class: "field"}, h("label", {}, "Language"), lang),
    h("div", {class: "field"}, h("label", {}, "Channel"), niche),
    h("div", {class: "field"}, h("label", {}, "Format"), format),
    h("div", {class: "field"}, h("label", {}, "Footage"), footage, h("div", {class: "hint"}, "Real footage uses free clips from Pexels and Pixabay when they fit. Drawn only keeps every frame generated.")),
    h("details", {class: "disclosure"}, h("summary", {}, icon("chevron"), "More options"),
      h("div", {class: "form"},
        h("div", {class: "field"}, h("label", {}, "Writer model"), writer),
        h("div", {class: "form-row"}, field("Voice", voice), field("Music", music)),
        h("div", {class: "field"}, h("label", {}, "Aspect"), aspect),
        h("div", {class: "field"}, h("label", {}, "Length"), length),
        h("div", {class: "form-row"}, field("Handle", handle), field("Extra hashtags", hashtags)),
        field("Notes", notes))),
    h("div", {class: "field"}, h("label", {}, "Post when ready"), publishBox),
    h("div", {style: {display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap"}}, makeBtn, h("span", {class: "footnote secondary"}, "Takes 8 to 12 minutes on GitHub. Costs about $0.50 in Claude credits.")));

  // Phone preview and progress
  const screen = h("div", {class: "phone-screen"});
  const phone = h("div", {class: "phone"}, h("div", {class: "phone-notch"}), screen);
  const progress = h("div", {class: "progress"});
  const idle = () => clear(screen).append(h("div", {class: "phone-idle"}, icon("phone"), h("div", {class: "headline", style: {color: "var(--label)"}}, "Your video shows up here"), h("div", {style: {marginTop: "6px"}}, "Pick a topic and press Make video. Each step lights up as the worker gets to it.")));
  idle();
  host.append(h("div", {class: "create-grid"}, form, h("div", {class: "phone-col"}, phone, progress)));

  let unsubs = [], pollTimer = null, current = null;
  function cleanup() { unsubs.forEach(u => u()); unsubs = []; clearInterval(pollTimer); pollTimer = null; }

  function renderProgress(job, video) {
    clear(progress);
    const status = video?.status || job?.status;
    const stage = (video?.stage || job?.stage || "").toLowerCase();
    let activeIdx = STAGES.findIndex(sn => stage && sn.toLowerCase().startsWith(stage.slice(0, 6)));
    const failed = status === "failed" || job?.status === "failed";
    const done = status === "ready" || status === "posted" || job?.status === "done";
    const wantsPost = current?.options.publish?.youtube || current?.options.publish?.instagram;
    const stages = wantsPost ? STAGES : STAGES.slice(0, 7);
    if (done) activeIdx = stages.length;
    else if (activeIdx < 0 && stage && stage !== "queued") activeIdx = stages.length - 1;
    const head = h("div", {style: {display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "8px"}},
      h("span", {class: "headline"}, failed ? "Something went wrong" : done ? (status === "posted" ? "Posted" : "Ready") : job?.status === "queued" ? "Waiting for a runner" : "Making your video"),
      h("span", {class: "footnote secondary num"}, current?.id || ""));
    const list = h("div", {class: "steps"}, ...stages.map((sn, i) => h("div", {class: "step " + (failed && i === activeIdx ? "failed" : i < activeIdx ? "done" : i === activeIdx && !done ? "active" : "")},
      h("span", {class: "dot"}, i < activeIdx || done ? icon("check") : failed && i === activeIdx ? icon("x") : null), sn)));
    progress.append(head, list);
    if (failed) progress.append(h("div", {class: "muted-box", style: {marginTop: "10px", color: "var(--red)"}}, (job?.error || video?.error || "The run failed."), job?.run_url ? h("div", {style: {marginTop: "6px"}}, h("a", {href: job.run_url, target: "_blank", rel: "noopener"}, "Open the run log")) : null));
    if (job?.run_url && !failed) progress.append(h("div", {style: {marginTop: "10px"}}, h("a", {class: "footnote", href: job.run_url, target: "_blank", rel: "noopener"}, "Watch the run on GitHub")));
    if (done && video?.video_url) {
      if (!screen.querySelector("video")) clear(screen).append(h("video", {src: video.video_url, poster: video.thumb_url || null, controls: true, playsinline: true, autoplay: true, muted: true, loop: true}));
      progress.append(h("div", {class: "actions", style: {marginTop: "14px"}}, h("button", {class: "btn", onClick: () => ctx.go("library", video.id)}, "Open in Library"), h("button", {class: "btn plain", onClick: () => { cleanup(); current = null; idle(); clear(progress); makeBtn.disabled = false; }}, "Make another")));
    } else if (!done && !failed) {
      clear(screen).append(h("div", {class: "phone-idle"}, h("span", {class: "spin", style: {margin: "0 auto 12px"}}), h("div", {class: "headline", style: {color: "var(--label)"}}, video?.title && video.title !== current?.options.topic ? video.title : (current?.options.topic || "Finding a trending topic")), h("div", {style: {marginTop: "6px"}}, stage ? capital(stage) : "Queued")));
    }
  }
  const capital = s => s.charAt(0).toUpperCase() + s.slice(1);

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

export function compactTs() { const d = new Date(); const p = n => String(n).padStart(2, "0"); return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`; }
export function rand4() { const a = "abcdefghjkmnpqrstuvwxyz23456789"; return [...crypto.getRandomValues(new Uint8Array(4))].map(b => a[b % a.length]).join(""); }

// ------------------------------------------------------------------ Autopilot
function buildAutopilot(ctx, host) {
  const {db} = ctx;
  let ap = null, loaded = false, dirty = false;
  const saveBtn = h("button", {class: "btn primary lg", type: "button", onClick: save}, "Save changes");
  const savedNote = h("span", {class: "footnote secondary"});
  const body = h("div", {class: "form"});
  host.append(body);

  async function load() {
    if (loaded) return;
    ap = (await db.getAutopilot()) || {};
    ap = {enabled: false, videos_per_day: 3, post_hours: [9, 13, 18, 21], platforms: {youtube: true, instagram: true}, languages: ["en"], niches: ["space"], topics: [], trending_fill: true, privacy: "public", options: {}, ...ap};
    ap.options = {voice: "auto", music: "auto", length: 45, hashtags: [], notes: "", footage: "auto", ...(ap.options || {})};
    loaded = true;
    render();
  }
  const mark = () => { dirty = true; savedNote.textContent = "Unsaved changes"; };

  function render() {
    const enabled = toggle(ap.enabled, v => { ap.enabled = v; mark(); }, "Autopilot on");
    const perDay = stepper(ap.videos_per_day, 1, 6, v => { ap.videos_per_day = v; mark(); });
    const hours = chips([...Array(18)].map((_, i) => ({value: i + 6, label: hourLabel(i + 6)})), ap.post_hours, {multi: true, small: true, onChange: v => { ap.post_hours = v.sort((a, b) => a - b); mark(); }});
    const ytT = toggle(ap.platforms?.youtube, v => { ap.platforms = {...ap.platforms, youtube: v}; mark(); }, "YouTube");
    const igT = toggle(ap.platforms?.instagram, v => { ap.platforms = {...ap.platforms, instagram: v}; mark(); }, "Instagram");
    const langs = chips(opts(LANGS), ap.languages, {multi: true, custom: true, onChange: v => { ap.languages = v; mark(); }});
    const niches = chips(opts(NICHES), ap.niches, {multi: true, custom: true, onChange: v => { ap.niches = v; mark(); }});
    const privacy = segmented([{value: "public", label: "Public"}, {value: "unlisted", label: "Unlisted"}, {value: "private", label: "Private"}], ap.privacy, v => { ap.privacy = v; mark(); });
    const o = ap.options;
    const voice = h("select", {class: "input", onChange: e => { o.voice = e.target.value; mark(); }}, ...VOICES.map(([v, l]) => h("option", {value: v, selected: v === o.voice}, l)));
    const music = h("select", {class: "input", onChange: e => { o.music = e.target.value; mark(); }}, ...MUSIC.map(([v, l]) => h("option", {value: v, selected: v === o.music}, l)));
    const length = chips([20, 30, 45, 60, 90].map(n => ({value: n, label: n + "s"})), Number(o.length) || 45, {onChange: v => { o.length = v; mark(); }});
    const footage = chips([{value: "auto", label: "Real footage"}, {value: "off", label: "Drawn only"}], o.footage || "auto", {onChange: v => { o.footage = v; mark(); }});
    const hashtags = h("input", {class: "input", value: (o.hashtags || []).join(" "), placeholder: "#shorts #india", onInput: e => { o.hashtags = e.target.value.split(/[\s,]+/).filter(Boolean).map(t => t.startsWith("#") ? t : "#" + t); mark(); }});
    const notes = h("textarea", {class: "input", rows: 2, value: o.notes || "", placeholder: "Standing instructions for the writer", onInput: e => { o.notes = e.target.value; mark(); }});
    const trending = toggle(ap.trending_fill, v => { ap.trending_fill = v; mark(); }, "Pick trending topics when the queue is empty");

    // topic queue
    const addBox = h("textarea", {class: "input", rows: 3, placeholder: "Add topics, one per line"});
    const queueList = h("div", {class: "list topic-list"});
    const renderQueue = () => {
      clear(queueList);
      if (!ap.topics.length) { queueList.append(h("div", {class: "empty"}, h("strong", {}, "The queue is empty"), ap.trending_fill ? "Autopilot will pick trending topics in your channels until you add some." : "Add topics above, or turn on trending topics so autopilot never idles.")); return; }
      ap.topics.forEach((t, i) => {
        const langSel = h("select", {class: "mini-select", "aria-label": "Language", onChange: e => { t.language = e.target.value; mark(); }}, ...LANGS.map(([v, l]) => h("option", {value: v, selected: v === (t.language || ap.languages[0])}, l)));
        const nicheSel = h("select", {class: "mini-select", "aria-label": "Channel", onChange: e => { t.niche = e.target.value; mark(); }}, ...NICHES.map(([v, l]) => h("option", {value: v, selected: v === (t.niche || ap.niches[0])}, l)));
        const status = t.status || "queued";
        queueList.append(h("div", {class: "row"},
          h("div", {class: "row-main"}, h("div", {class: "topic-text"}, t.text), h("div", {class: "topic-meta"}, h("span", {class: "pill " + (status === "done" ? "done" : status === "running" ? "running" : "queued")}, status === "done" ? "Done" : status === "running" ? "Making" : "Queued"), status === "queued" ? [langSel, nicheSel] : h("span", {class: "footnote secondary"}, langName(t.language), ", ", nicheName(t.niche)), t.video_id ? h("button", {class: "btn plain sm", onClick: () => ctx.go("library", t.video_id)}, "Open video") : null)),
          h("button", {class: "btn icon sm", "aria-label": "Remove topic", onClick: () => { ap.topics.splice(i, 1); mark(); renderQueue(); }}, icon("x"))));
      });
    };
    renderQueue();
    const addBtn = h("button", {class: "btn", type: "button", onClick: () => {
      const lines = addBox.value.split("\n").map(s => s.trim()).filter(Boolean);
      if (!lines.length) return;
      for (const text of lines) ap.topics.push({text, language: ap.languages[0] || "en", niche: ap.niches[0] || "space", status: "queued"});
      addBox.value = ""; mark(); renderQueue();
    }}, icon("plus"), "Add");

    clear(body).append(
      h("div", {class: "list"},
        row({title: "Autopilot on", sub: "Runs hourly on GitHub and posts at the hours you pick", icon: "bolt", iconColor: "var(--blue)", control: enabled}),
        row({title: "Videos per day", control: perDay}),
        row({title: "Post times", sub: "IST", stacked: true, body: hours}),
        row({title: "YouTube Shorts", icon: "youtube", iconColor: "#FF453A", control: ytT}),
        row({title: "Instagram Reels", icon: "instagram", iconColor: "#FF375F", control: igT}),
        row({title: "Privacy", control: privacy})),
      h("div", {class: "field"}, h("label", {}, "Languages"), langs, h("div", {class: "hint"}, "Autopilot rotates through these.")),
      h("div", {class: "field"}, h("label", {}, "Channels"), niches),
      h("details", {class: "disclosure"}, h("summary", {}, icon("chevron"), "Defaults for every video"),
        h("div", {class: "form"},
          h("div", {class: "form-row"}, field("Voice", voice), field("Music", music)),
          h("div", {class: "field"}, h("label", {}, "Length"), length),
          h("div", {class: "field"}, h("label", {}, "Footage"), footage),
          field("Hashtags", hashtags), field("Notes", notes))),
      h("div", {class: "field"}, h("label", {}, "Topic queue"), addBox, h("div", {style: {display: "flex", justifyContent: "flex-end"}}, addBtn)),
      queueList,
      h("div", {class: "list"}, row({title: "When the queue is empty, pick trending topics", sub: "Claude scouts what is rising in your channels", control: trending})),
      h("div", {style: {display: "flex", gap: "12px", alignItems: "center"}}, saveBtn, savedNote));
  }

  async function save() {
    saveBtn.disabled = true;
    try {
      const {updated_at, last_run_at, ...rest} = ap;
      ap = {...ap, ...(await db.saveAutopilot(rest))};
      dirty = false; savedNote.textContent = "Saved " + fmt.dateTime(new Date().toISOString());
      toast(ap.enabled ? "Autopilot is on" : "Autopilot plan saved", "ok");
    } catch (e) { toast("Could not save: " + e.message, "err"); }
    finally { saveBtn.disabled = false; }
  }
  return {load};
}

function hourLabel(hh) { return `${((hh + 11) % 12) + 1}${hh >= 12 ? " pm" : " am"}`; }
