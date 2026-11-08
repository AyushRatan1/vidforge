// Library: every video as a glass card, with a detail Sheet for playback, captions and the Post now flow.
import {h, clear, Button, Card, Segmented, Switch, ChipGroup, Field, Input, Textarea, Status, Pill, PlatformMark, ListRow, Sheet, EmptyState, toast, icon} from "../components.js";
import {PUBLISH_WF} from "../db.js";
import {fmt, langName, compactTs, rand4} from "../format.js";

const FILTERS = [{value: "all", label: "All"}, {value: "ready", label: "Ready"}, {value: "posted", label: "Posted"}, {value: "making", label: "Making"}, {value: "failed", label: "Failed"}, {value: "autopilot", label: "Autopilot"}];
const PRIVACY = [{value: "public", label: "Public"}, {value: "unlisted", label: "Unlisted"}, {value: "private", label: "Private"}];

export function libraryPage(ctx, el, actions) {
  const {db} = ctx;
  let videos = [], filter = "all", q = "", loaded = false;
  const searchInput = Input({type: "search", placeholder: "Search titles and topics", "aria-label": "Search the library", onInput: e => { q = e.target.value.toLowerCase(); renderGrid(); }});
  const search = h("div", {class: "search"}, icon("search", {size: 18}), searchInput);
  const chips = ChipGroup(FILTERS, filter, {onChange: v => { filter = v; renderGrid(); }, ariaLabel: "Filter by status"});
  const count = h("span", {class: "micro num"});
  const mount = tb => tb.append(count);
  mount(actions);
  const grid = h("div", {class: "vid-grid stagger"});
  el.append(h("div", {class: "lib-tools"}, chips, search), grid);

  async function load() { videos = await db.listVideos(); loaded = true; renderGrid(); }

  function matches(v) {
    if (filter === "autopilot" && v.source !== "autopilot") return false;
    if (filter === "making" && !(v.status === "making" || v.status === "queued")) return false;
    if (["ready", "posted", "failed"].includes(filter) && v.status !== filter) return false;
    if (q && !`${v.title || ""} ${v.topic || ""} ${v.niche || ""}`.toLowerCase().includes(q)) return false;
    return true;
  }
  function renderGrid() {
    const list = videos.filter(matches);
    count.textContent = `${list.length} of ${videos.length}`;
    clear(grid);
    if (!videos.length) { grid.append(h("div", {style: {gridColumn: "1 / -1"}}, EmptyState({icon: "library", title: "No videos yet", text: "Every video you make is kept here as a GitHub Release with its MP4, captions and sources.", action: Button({label: "Make the first one", variant: "primary", onClick: () => ctx.go("create")})}))); return; }
    if (!list.length) { grid.append(h("div", {style: {gridColumn: "1 / -1"}}, EmptyState({icon: "search", title: "Nothing matches", text: q ? "Try a different search." : "No videos with this status yet.", compact: true}))); return; }
    for (const v of list) grid.append(card(v));
  }
  function card(v) {
    const status = v.status === "queued" ? "making" : v.status;
    return h("button", {class: "vid glass", type: "button", onClick: () => openSheet(v.id), "aria-label": `${v.title || v.topic || v.id}, ${status}`},
      h("div", {class: "vid-thumb"}, v.thumb_url ? h("img", {src: v.thumb_url, alt: "", loading: "lazy"}) : h("div", {class: "ph"}, icon("film", {size: 22}), h("span", {}, status === "making" ? "Rendering" : status === "failed" ? "No render" : "No thumbnail")),
        Status(status, {small: true}), v.duration ? h("span", {class: "vid-dur num"}, fmt.dur(v.duration)) : null),
      h("div", {class: "vid-body"}, h("div", {class: "vid-title"}, v.title || v.topic || "Working title pending"),
        h("div", {class: "vid-meta"}, h("span", {}, [langName(v.language), fmt.date(v.created_at)].filter(Boolean).join(", ")), h("span", {class: "marks"}, v.youtube_url ? PlatformMark("youtube", v.youtube_url, {size: 12}) : null, v.instagram_url ? PlatformMark("instagram", v.instagram_url, {size: 12}) : null))));
  }

  // ---------------------------------------------------------------- detail sheet
  let dialog = null, sheetId = null;
  async function openSheet(id) {
    const v = videos.find(x => x.id === id) || await db.getVideo(id);
    if (!v) { toast("That video is not in the library.", "err"); return; }
    sheetId = id;
    dialog?.close();
    dialog = Sheet({title: v.title || v.topic || v.id, wide: true, onClose: () => { sheetId = null; dialog = null; if (location.hash.startsWith("#/library/")) history.replaceState(null, "", location.pathname + location.search + "#/library"); }});
    renderSheet(v);
    dialog.open_();
  }
  function renderSheet(v) {
    Object.assign(dialog.dataset, {status: v.status || "", yt: v.youtube_url || "", ig: v.instagram_url || ""});
    dialog.setTitle(v.title || v.topic || v.id);
    const yt = v.meta?.youtube || {}, ig = v.meta?.instagram || {};
    const ytTitle = Input({value: yt.title || v.title || "", maxlength: 100});
    const ytDesc = Textarea({rows: 5, value: yt.description || ""});
    const igCap = Textarea({rows: 5, value: ig.caption || ""});
    const ytCount = h("span", {class: "counter"}), igCount = h("span", {class: "counter"});
    const countTags = (ta, out) => { const n = (ta.value.match(/#[\p{L}\p{N}_]+/gu) || []).length; out.textContent = `${n} of 5 hashtags`; out.classList.toggle("over", n > 5); };
    ytDesc.addEventListener("input", () => countTags(ytDesc, ytCount)); igCap.addEventListener("input", () => countTags(igCap, igCount));
    countTags(ytDesc, ytCount); countTags(igCap, igCount);

    const pub = {youtube: !v.youtube_url, instagram: !v.instagram_url && !!ig.caption, privacy: "public", publish_at: ""};
    const ytT = Switch(pub.youtube, x => pub.youtube = x, "YouTube"), igT = Switch(pub.instagram, x => pub.instagram = x, "Instagram");
    const privacy = Segmented(PRIVACY, "public", x => pub.privacy = x, {size: "sm", ariaLabel: "Privacy"});
    const when = Input({type: "datetime-local", "aria-label": "Schedule", onChange: e => pub.publish_at = e.target.value ? new Date(e.target.value).toISOString() : ""});
    const canPost = v.status === "ready" || v.status === "posted";
    const postBtn = Button({label: "Post now", variant: "primary", icon: "upload", disabled: !canPost, onClick: () => postNow(v, pub, {youtube: {title: ytTitle.value.trim(), description: ytDesc.value}, instagram: {caption: igCap.value}}, postBtn)});

    const issues = v.qa?.issues || [];
    const player = h("div", {class: "sheet-player"}, v.video_url ? h("video", {src: v.video_url, poster: v.thumb_url || null, controls: true, playsinline: true}) : h("div", {class: "phone-idle"}, icon("film", {size: 24}), v.status === "failed" ? "No video was produced." : "The video appears here when the render finishes."));
    const left = h("div", {class: "stack"}, player,
      h("div", {class: "actions"},
        v.video_url ? Button({label: "Download", variant: "secondary", size: "sm", icon: "download", href: v.video_url, download: `${v.id}.mp4`}) : null,
        v.release_url ? Button({label: "Open on GitHub", variant: "secondary", size: "sm", icon: "github", href: v.release_url, target: "_blank"}) : null,
        Button({label: "Copy caption", variant: "secondary", size: "sm", icon: "copy", onClick: () => navigator.clipboard.writeText(igCap.value || ytDesc.value).then(() => toast("Caption copied", "ok"), () => toast("Could not copy. Select the text and copy it.", "err"))})),
      h("dl", {class: "facts"},
        h("dt", {}, "Status"), h("dd", {}, Status(v.status), v.error ? h("span", {class: "micro", style: {color: "var(--err-text)"}}, v.error) : null),
        h("dt", {}, "Topic"), h("dd", {}, v.topic || h("span", {class: "tertiary"}, "Trending pick")),
        h("dt", {}, "Made"), h("dd", {}, fmt.dateTime(v.created_at), v.source === "autopilot" ? Pill("Autopilot", "accent", {small: true}) : null),
        h("dt", {}, "Details"), h("dd", {class: "num"}, [langName(v.language), v.format ? v.format.replaceAll("_", " ") : null, v.aspect, v.duration ? fmt.dur(v.duration) : null].filter(Boolean).join(", ")),
        h("dt", {}, "Cost"), h("dd", {class: "num"}, v.usd != null ? fmt.usd(v.usd) : "Unknown"),
        h("dt", {}, "Review"), h("dd", {}, v.qa_score != null ? h("span", {class: "num"}, `${v.qa_score} of 10`) : "Not reviewed", issues.length ? h("ul", {class: "sources", style: {width: "100%"}}, ...issues.map(i => h("li", {}, i))) : null),
        h("dt", {}, "Links"), h("dd", {}, h("span", {class: "marks"}, PlatformMark("youtube", v.youtube_url), PlatformMark("instagram", v.instagram_url)), !v.youtube_url && !v.instagram_url ? h("span", {class: "micro"}, "Not posted yet") : null)),
      v.sources?.length ? h("div", {class: "stack-sm"}, h("span", {class: "label"}, "Sources"), h("ul", {class: "sources"}, ...v.sources.slice(0, 8).map(s => h("li", {}, s.claim ? s.claim + " " : "", s.url ? h("a", {href: s.url, target: "_blank", rel: "noopener"}, s.title || safeHost(s.url)) : null)))) : null);

    const right = h("div", {class: "stack"},
      Card({title: "Captions", subtitle: "Edits are used for the next post", body: h("div", {class: "form"},
        Field({label: "YouTube title", control: ytTitle}),
        Field({label: "YouTube description", control: ytDesc, hint: ytCount}),
        Field({label: "Instagram caption", control: igCap, hint: igCount}))}),
      Card({title: "Post now", subtitle: canPost ? "Choose where this video goes" : "Available once the video is ready", body: h("div", {class: "list"},
        ListRow({title: "YouTube Shorts", sub: v.youtube_url ? "Already posted. Posting again makes a second video." : null, icon: "youtube", iconTone: "yt", control: ytT}),
        ListRow({title: "Instagram Reels", icon: "instagram", iconTone: "ig", control: igT}),
        ListRow({title: "Privacy", control: privacy}),
        ListRow({title: "Schedule", sub: "Leave empty to post right away", control: h("div", {style: {width: "220px", maxWidth: "50vw"}}, when)})),
        footer: h("div", {class: "cluster-between"}, h("span", {}, canPost ? "Posting starts a GitHub run. Links appear here when it finishes." : "Wait for the render to pass review."), postBtn)}));
    dialog.setBody(h("div", {class: "sheet-grid"}, left, right));
  }

  async function postNow(v, pub, overrides, btn) {
    if (!pub.youtube && !pub.instagram) { toast("Turn on at least one platform to post.", "err"); return; }
    const ts = compactTs() + rand4();
    const jobId = "pub-" + ts;
    const options = {publish: {...pub}, overrides, job_id: jobId,
      // flat copies so the current publish-video workflow reads them too
      youtube: pub.youtube, instagram: pub.instagram, privacy: pub.privacy, publish_at: pub.publish_at};
    btn.setBusy(true);
    try {
      await db.insertJob({id: jobId, kind: "publish", status: "queued", video_id: v.id, options});
      await db.dispatch(PUBLISH_WF, {video_id: v.id, request_id: jobId, options: JSON.stringify(options)});
      await db.updateVideo(v.id, {meta: {...(v.meta || {}), youtube: {...(v.meta?.youtube || {}), ...overrides.youtube}, instagram: {...(v.meta?.instagram || {}), ...overrides.instagram}}}).catch(() => {});
      toast("Posting started. Links appear here when it finishes.", "ok");
      dialog.close();
    } catch (e) { toast((e.message || "Could not start posting.") + (e.hint ? " " + e.hint : ""), "err"); btn.setBusy(false); }
  }

  let unsub = null;
  return {
    mount,
    async show(arg) {
      if (!loaded) await load();
      unsub ||= db.subscribe("videos", null, (rowObj, type) => {
        const i = videos.findIndex(x => x.id === rowObj.id);
        if (type === "DELETE") { if (i >= 0) videos.splice(i, 1); }
        else if (i >= 0) videos[i] = {...videos[i], ...rowObj}; else videos.unshift(rowObj);
        renderGrid();
        // Re-render the open sheet only when status or links changed, so typing is not lost.
        if (sheetId === rowObj.id && dialog?.open && (rowObj.status !== dialog.dataset.status || rowObj.youtube_url !== dialog.dataset.yt || rowObj.instagram_url !== dialog.dataset.ig)) renderSheet(videos.find(x => x.id === rowObj.id) || rowObj);
      });
      if (arg) openSheet(arg);
    },
  };
}

function safeHost(u) { try { return new URL(u).hostname; } catch { return u; } }
