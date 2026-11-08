import {h, clear, icon, segmented, toggle, field, row, platformMark, statusPill, empty, toast, fmt, langName} from "../ui.js";
import {PUBLISH_WF} from "../db.js";
import {compactTs, rand4} from "./create.js";

export function libraryPage(ctx, el, toolbar) {
  const {db} = ctx;
  let videos = [], filter = "all", q = "", loaded = false;
  const search = h("div", {class: "search"}, icon("search"), h("input", {class: "input", type: "search", placeholder: "Search titles and topics", "aria-label": "Search", onInput: e => { q = e.target.value.toLowerCase(); renderGrid(); }}));
  const seg = segmented([["all", "All"], ["ready", "Ready"], ["posted", "Posted"], ["failed", "Failed"], ["autopilot", "Autopilot"]].map(([value, label]) => ({value, label})), filter, v => { filter = v; renderGrid(); });
  const count = h("span", {class: "footnote secondary num"});
  const mount = tb => tb.append(count);
  mount(toolbar);
  const grid = h("div", {class: "vid-grid"});
  el.append(h("div", {class: "lib-tools"}, search, seg), grid);

  async function load() { videos = await db.listVideos(); loaded = true; renderGrid(); }

  function matches(v) {
    if (filter === "autopilot" && v.source !== "autopilot") return false;
    if (["ready", "posted", "failed"].includes(filter) && v.status !== filter) return false;
    if (q && !`${v.title || ""} ${v.topic || ""} ${v.niche || ""}`.toLowerCase().includes(q)) return false;
    return true;
  }
  function renderGrid() {
    const list = videos.filter(matches);
    count.textContent = `${list.length} of ${videos.length}`;
    clear(grid);
    if (!videos.length) { grid.append(h("div", {style: {gridColumn: "1 / -1"}}, empty("No videos yet", "Every video you make is kept here as a GitHub Release with its MP4, captions and sources.", h("button", {class: "btn primary", onClick: () => ctx.go("create")}, "Make the first one")))); return; }
    if (!list.length) { grid.append(h("div", {style: {gridColumn: "1 / -1"}}, empty("Nothing matches", q ? "Try a different search." : "No videos with this status yet."))); return; }
    for (const v of list) grid.append(card(v));
  }
  function card(v) {
    const status = v.status === "queued" || v.status === "making" ? "making" : v.status;
    return h("div", {class: "vid", role: "button", tabIndex: 0, onClick: () => openSheet(v.id), onKeydown: e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); openSheet(v.id); } }},
      h("div", {class: "vid-thumb"}, v.thumb_url ? h("img", {src: v.thumb_url, alt: "", loading: "lazy"}) : h("div", {class: "ph"}, icon("film"), h("span", {}, v.status === "making" || v.status === "queued" ? "Rendering" : v.status === "failed" ? "No render" : (v.niche ? v.niche.charAt(0).toUpperCase() + v.niche.slice(1) : "Video"))),
        h("span", {class: "pill " + status}, statusLabel(status)), v.duration ? h("span", {class: "dur num"}, fmt.dur(v.duration)) : null),
      h("div", {class: "vid-body"}, h("div", {class: "vid-title"}, v.title || v.topic || "Working title pending"),
        h("div", {class: "vid-meta"}, h("span", {}, langName(v.language), v.language ? ", " : "", fmt.date(v.created_at)), h("span", {class: "marks"}, v.youtube_url ? platformMark("youtube", v.youtube_url) : null, v.instagram_url ? platformMark("instagram", v.instagram_url) : null))));
  }

  // ---------------------------------------------------------------- detail sheet
  let dialog = null, sheetId = null;
  async function openSheet(id) {
    const v = videos.find(x => x.id === id) || await db.getVideo(id);
    if (!v) { toast("That video is not in the library.", "err"); return; }
    sheetId = id;
    dialog?.remove();
    dialog = h("dialog", {class: "sheet", onClose: () => { sheetId = null; dialog.remove(); }});
    document.body.append(dialog);
    renderSheet(v);
    dialog.showModal();
  }
  function renderSheet(v) {
    Object.assign(dialog.dataset, {status: v.status || "", yt: v.youtube_url || "", ig: v.instagram_url || ""});
    const yt = v.meta?.youtube || {}, ig = v.meta?.instagram || {};
    const ytTitle = h("input", {class: "input", value: yt.title || v.title || "", maxlength: 100});
    const ytDesc = h("textarea", {class: "input", rows: 5, value: yt.description || ""});
    const igCap = h("textarea", {class: "input", rows: 5, value: ig.caption || ""});
    const ytCount = h("div", {class: "counter"}), igCount = h("div", {class: "counter"});
    const countTags = (ta, out) => { const n = (ta.value.match(/#[\p{L}\p{N}_]+/gu) || []).length; out.textContent = `${n} of 5 hashtags`; out.classList.toggle("over", n > 5); };
    ytDesc.addEventListener("input", () => countTags(ytDesc, ytCount)); igCap.addEventListener("input", () => countTags(igCap, igCount));
    countTags(ytDesc, ytCount); countTags(igCap, igCount);

    const pub = {youtube: !v.youtube_url, instagram: !v.instagram_url && !!ig.caption, privacy: "public", publish_at: ""};
    const ytT = toggle(pub.youtube, x => pub.youtube = x, "YouTube"), igT = toggle(pub.instagram, x => pub.instagram = x, "Instagram");
    const privacy = segmented([{value: "public", label: "Public"}, {value: "unlisted", label: "Unlisted"}, {value: "private", label: "Private"}], "public", x => pub.privacy = x);
    const when = h("input", {class: "input", type: "datetime-local", onChange: e => pub.publish_at = e.target.value ? new Date(e.target.value).toISOString() : ""});
    const postBtn = h("button", {class: "btn primary", disabled: v.status !== "ready" && v.status !== "posted", onClick: () => postNow(v, pub, {youtube: {title: ytTitle.value.trim(), description: ytDesc.value}, instagram: {caption: igCap.value}}, postBtn)}, icon("upload"), "Post now");

    const issues = v.qa?.issues || [];
    const body = h("div", {class: "sheet-body"},
      h("div", {}, h("div", {class: "sheet-player"}, v.video_url ? h("video", {src: v.video_url, poster: v.thumb_url || null, controls: true, playsinline: true}) : h("div", {class: "phone-idle", style: {height: "100%", display: "grid", placeItems: "center"}}, v.status === "failed" ? "No video was produced." : "The video appears here when the render finishes.")),
        h("div", {class: "actions", style: {marginTop: "12px"}},
          v.video_url ? h("a", {class: "btn sm", href: v.video_url, download: `${v.id}.mp4`}, icon("download"), "Download") : null,
          v.release_url ? h("a", {class: "btn sm", href: v.release_url, target: "_blank", rel: "noopener"}, icon("ext"), "Open on GitHub") : null,
          h("button", {class: "btn sm", onClick: () => navigator.clipboard.writeText(igCap.value || ytDesc.value).then(() => toast("Caption copied", "ok"))}, icon("copy"), "Copy caption"))),
      h("div", {class: "sheet-col"},
        h("dl", {class: "kv"},
          h("dt", {}, "Status"), h("dd", {}, statusPill(v.status), v.error ? h("span", {class: "footnote", style: {color: "var(--red)", marginLeft: "8px"}}, v.error) : null),
          h("dt", {}, "Topic"), h("dd", {}, v.topic || h("span", {class: "secondary"}, "Trending pick")),
          h("dt", {}, "Made"), h("dd", {}, fmt.dateTime(v.created_at), v.source === "autopilot" ? h("span", {class: "pill plain", style: {marginLeft: "8px"}}, "Autopilot") : null),
          h("dt", {}, "Details"), h("dd", {class: "num"}, [langName(v.language), v.format ? v.format.replaceAll("_", " ") : null, v.aspect, v.duration ? fmt.dur(v.duration) : null].filter(Boolean).join(", ")),
          h("dt", {}, "Cost"), h("dd", {class: "num"}, v.usd != null ? fmt.usd(v.usd) : "Unknown"),
          h("dt", {}, "Review"), h("dd", {}, v.qa_score != null ? h("span", {class: "num"}, `${v.qa_score} of 10`) : "Not reviewed", issues.length ? h("ul", {style: {margin: "6px 0 0", paddingLeft: "18px"}}, ...issues.map(i => h("li", {class: "issue"}, i))) : null),
          h("dt", {}, "Links"), h("dd", {}, h("span", {class: "marks"}, platformMark("youtube", v.youtube_url), platformMark("instagram", v.instagram_url), !v.youtube_url && !v.instagram_url ? h("span", {class: "footnote secondary", style: {marginLeft: "6px"}}, "Not posted yet") : null))),
        field("YouTube title", ytTitle),
        h("div", {class: "field"}, h("label", {}, "YouTube description"), ytDesc, ytCount),
        h("div", {class: "field"}, h("label", {}, "Instagram caption"), igCap, igCount),
        h("div", {class: "field"}, h("label", {}, "Post now"), h("div", {class: "publish-box"},
          row({title: "YouTube Shorts", sub: v.youtube_url ? "Already posted. Posting again makes a second video." : null, icon: "youtube", iconColor: "#FF453A", control: ytT}),
          row({title: "Instagram Reels", icon: "instagram", iconColor: "#FF375F", control: igT}),
          row({title: "Privacy", control: privacy}),
          row({title: "Schedule", sub: "Leave empty to post right away", control: h("div", {style: {width: "230px"}}, when)}),
          h("div", {class: "row"}, h("div", {class: "row-main footnote secondary"}, v.status === "ready" || v.status === "posted" ? "Edits above are used for this post." : "Available once the video is ready."), postBtn))),
        v.sources?.length ? h("div", {}, h("div", {class: "group-title", style: {padding: "0 0 8px"}}, "Sources"), h("ul", {class: "sources", style: {margin: 0, paddingLeft: "18px"}}, ...v.sources.slice(0, 8).map(s => h("li", {}, s.claim ? s.claim + " " : "", s.url ? h("a", {href: s.url, target: "_blank", rel: "noopener"}, s.title || new URL(s.url).hostname) : null)))) : null));
    clear(dialog).append(h("div", {class: "sheet-head"}, h("h2", {}, v.title || v.topic || v.id), h("button", {class: "btn icon sm", "aria-label": "Close", onClick: () => dialog.close()}, icon("x"))), body);
  }

  async function postNow(v, pub, overrides, btn) {
    if (!pub.youtube && !pub.instagram) { toast("Turn on at least one platform to post.", "err"); return; }
    const ts = compactTs() + rand4();
    const jobId = "pub-" + ts;
    const options = {publish: {...pub}, overrides, job_id: jobId,
      // flat copies so the current publish-video workflow reads them too
      youtube: pub.youtube, instagram: pub.instagram, privacy: pub.privacy, publish_at: pub.publish_at};
    btn.disabled = true;
    try {
      await db.insertJob({id: jobId, kind: "publish", status: "queued", video_id: v.id, options});
      await db.dispatch(PUBLISH_WF, {video_id: v.id, request_id: jobId, options: JSON.stringify(options)});
      await db.updateVideo(v.id, {meta: {...(v.meta || {}), youtube: {...(v.meta?.youtube || {}), ...overrides.youtube}, instagram: {...(v.meta?.instagram || {}), ...overrides.instagram}}}).catch(() => {});
      toast("Posting started. Links appear here when it finishes.", "ok");
      dialog.close();
    } catch (e) { toast((e.message || "Could not start posting.") + (e.hint ? " " + e.hint : ""), "err"); btn.disabled = false; }
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
        // Re-render the open sheet only when something other than edits changed (status or links), so typing is not lost.
        if (sheetId === rowObj.id && dialog?.open && (rowObj.status !== dialog.dataset.status || rowObj.youtube_url !== dialog.dataset.yt || rowObj.instagram_url !== dialog.dataset.ig)) renderSheet(videos.find(x => x.id === rowObj.id) || rowObj);
      });
      if (arg) openSheet(arg);
    },
  };
}

function statusLabel(s) { return {making: "Making", ready: "Ready", posted: "Posted", failed: "Failed", queued: "Making"}[s] || s; }
