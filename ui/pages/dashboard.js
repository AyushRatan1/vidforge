import {h, clear, icon, segmented, platformMark, statusPill, empty, fmt} from "../ui.js";
import {areaChart, barLineChart} from "../charts.js";
import {dayStr} from "../db.js";

const YT = "#FF453A", IG = "#FF375F", BLUE = "#0A84FF";

export function dashboardPage(ctx, el, toolbar) {
  const {db} = ctx;
  let platform = "all";
  let data = null;
  const seg = segmented([{value: "all", label: "All"}, {value: "youtube", label: "YouTube"}, {value: "instagram", label: "Instagram"}], platform, v => { platform = v; render(); });
  const refresh = h("button", {class: "btn icon", "aria-label": "Refresh", title: "Refresh", onClick: () => load(true)}, icon("refresh"));
  const mount = tb => tb.append(seg, refresh);
  mount(toolbar);

  const body = h("div", {});
  el.append(body);

  async function load(force) {
    if (data && !force) return;
    const [videos, stats, channel, jobs, autopilot] = await Promise.all([db.listVideos(), db.listStats(45), db.listChannelStats(45), db.listJobs(8), db.getAutopilot()]);
    data = {videos, stats, channel, jobs, autopilot};
    render();
  }

  function render() {
    if (!data) return;
    const {videos, stats, channel, jobs, autopilot} = data;
    const plat = r => platform === "all" || r.platform === platform;
    const days = [...Array(30)].map((_, i) => dayStr(new Date(Date.now() - (29 - i) * 864e5)));
    const today = days[29];
    const d7 = dayStr(new Date(Date.now() - 7 * 864e5)), d14 = dayStr(new Date(Date.now() - 14 * 864e5));

    // Daily totals per platform (stats rows hold cumulative-per-video snapshots per day; sum per day = views that day across videos)
    const perDay = {youtube: Object.fromEntries(days.map(d => [d, 0])), instagram: Object.fromEntries(days.map(d => [d, 0]))};
    const sum7 = {views: 0, likes: 0, comments: 0}, prev7 = {views: 0, likes: 0, comments: 0};
    for (const r of stats) {
      if (!plat(r)) continue;
      if (perDay[r.platform] && r.day in perDay[r.platform]) perDay[r.platform][r.day] += r.views || 0;
      const bucket = r.day > d7 ? sum7 : r.day > d14 ? prev7 : null;
      if (bucket) { bucket.views += r.views || 0; bucket.likes += r.likes || 0; bucket.comments += r.comments || 0; }
    }
    const latestChannel = p => [...channel].filter(c => c.platform === p).sort((a, b) => b.day.localeCompare(a.day));
    const followers = (p, offset) => latestChannel(p)[offset]?.followers ?? latestChannel(p)[0]?.followers ?? 0;
    const plats = platform === "all" ? ["youtube", "instagram"] : [platform];
    const followersNow = plats.reduce((a, p) => a + followers(p, 0), 0);
    const followersPrev = plats.reduce((a, p) => a + (latestChannel(p).find(c => c.day <= d7)?.followers ?? followers(p, 0)), 0);
    const postedIn = (from, to) => videos.filter(v => v.status === "posted" && (platform === "all" || (platform === "youtube" ? v.youtube_url : v.instagram_url)) && v.created_at.slice(0, 10) > from && (!to || v.created_at.slice(0, 10) <= to)).length;
    const spend = (from, to) => videos.filter(v => v.created_at.slice(0, 10) > from && (!to || v.created_at.slice(0, 10) <= to)).reduce((a, v) => a + (v.usd || 0), 0);

    const tiles = [
      ["Views", fmt.compact(sum7.views), sum7.views, prev7.views],
      ["Likes", fmt.compact(sum7.likes), sum7.likes, prev7.likes],
      ["Comments", fmt.compact(sum7.comments), sum7.comments, prev7.comments],
      [platform === "youtube" ? "Subscribers" : "Followers", fmt.compact(followersNow), followersNow, followersPrev],
      ["Videos posted", String(postedIn(d7)), postedIn(d7), postedIn(d14, d7)],
      ["Claude spend", fmt.usd(spend(d7)), spend(d7), spend(d14, d7), true],
    ];
    const statGrid = h("div", {class: "stat-grid"}, ...tiles.map(([label, value, cur, prev, inverse]) => {
      const up = cur > prev, same = cur === prev;
      return h("div", {class: "stat"}, h("div", {class: "stat-label"}, label), h("div", {class: "stat-value"}, value),
        h("div", {class: "stat-delta " + (same ? "" : (up !== !!inverse) ? "up" : "down")}, same ? null : icon(up ? "arrowUp" : "arrowDown"), h("span", {class: "num"}, fmt.pct(cur, prev))));
    }));
    const statNote = h("p", {class: "footnote tertiary", style: {margin: "-8px 0 20px 4px"}}, "Last 7 days, compared with the 7 days before. Stats are pulled daily at 07:45 IST.");

    // Views chart
    const series = plats.map(p => ({name: p === "youtube" ? "YouTube" : "Instagram", color: p === "youtube" ? YT : IG, values: days.map(d => perDay[p][d])}));
    const total30 = series.reduce((a, s) => a + s.values.reduce((x, y) => x + y, 0), 0);
    const chartEl = h("div", {class: "chart", style: {height: "260px"}});
    const viewsCard = h("div", {class: "card"},
      h("div", {class: "card-title"}, h("div", {}, h("div", {class: "footnote secondary"}, "Views, last 30 days"), h("div", {class: "chart-big num"}, fmt.compact(total30))),
        h("div", {class: "legend"}, ...series.map(s => h("span", {}, h("span", {class: "sw", style: {background: s.color}}), s.name)))),
      total30 ? chartEl : empty("No views yet", "Daily views appear here the morning after your first video is posted. Stats are pulled every day at 07:45 IST."));

    // Made per day + avg review score
    const counts = days.map(d => videos.filter(v => v.created_at.slice(0, 10) === d && v.status !== "failed").length);
    const scores = days.map(d => { const s = videos.filter(v => v.created_at.slice(0, 10) === d && v.qa_score != null); return s.length ? s.reduce((a, v) => a + v.qa_score, 0) / s.length : null; });
    const madeEl = h("div", {class: "chart", style: {height: "200px"}});
    const madeCard = h("div", {class: "card"},
      h("div", {class: "card-title"}, h("h3", {}, "Videos made and review score"),
        h("div", {class: "legend"}, h("span", {}, h("span", {class: "sw", style: {background: BLUE}}), "Made per day"), h("span", {}, h("span", {class: "sw", style: {background: "#30D158"}}), "Average score of 10"))),
      videos.length ? madeEl : empty("Nothing made yet", "Each day's videos and their average review score will show here.", h("button", {class: "btn primary", onClick: () => ctx.go("create")}, "Make a video")));

    // Top videos
    const withViews = videos.filter(v => v.status === "posted").map(v => ({...v, views: stats.filter(r => r.video_id === v.id && plat(r)).reduce((a, r) => a + (r.views || 0), 0)})).sort((a, b) => b.views - a.views).slice(0, 6);
    const topCard = h("div", {class: "card", style: {padding: "20px 0 8px"}},
      h("div", {class: "card-title", style: {padding: "0 20px"}}, h("h3", {}, "Top videos"), h("span", {class: "secondary"}, "by views")),
      withViews.length ? h("div", {}, ...withViews.map(v => h("button", {class: "row button inset-sep", type: "button", onClick: () => ctx.go("library", v.id)},
        thumb(v), h("div", {class: "row-main"}, h("div", {class: "row-title"}, v.title || v.topic || v.id), h("div", {class: "row-sub"}, h("span", {class: "marks"}, v.youtube_url ? platformMark("youtube", v.youtube_url) : null, v.instagram_url ? platformMark("instagram", v.instagram_url) : null), " Posted ", fmt.date(v.created_at))),
        h("span", {class: "row-value num"}, fmt.compact(v.views)))))
      : empty("No posted videos", "Once a video is posted it will be ranked here by views."));

    // Autopilot
    const ap = autopilot || {};
    const nextSlot = nextSlotLabel(ap);
    const todayCount = videos.filter(v => v.source === "autopilot" && v.created_at.slice(0, 10) === today).length;
    const queue = (ap.topics || []).filter(t => t.status !== "done").length;
    const apCard = h("div", {class: "card"},
      h("div", {class: "card-title"}, h("h3", {}, "Autopilot"), h("span", {class: "pill plain " + (ap.enabled ? "posted" : "")}, ap.enabled ? "On" : "Off")),
      h("div", {class: "ap-stat"},
        h("div", {}, h("div", {class: "k"}, "Next slot"), h("div", {class: "v"}, ap.enabled ? nextSlot : "Paused")),
        h("div", {}, h("div", {class: "k"}, "Videos today"), h("div", {class: "v num"}, `${todayCount} of ${ap.videos_per_day || 0}`)),
        h("div", {}, h("div", {class: "k"}, "Topics queued"), h("div", {class: "v num"}, String(queue))),
        h("div", {}, h("div", {class: "k"}, "Last run"), h("div", {class: "v", style: {fontSize: "17px"}}, ap.last_run_at ? fmt.ago(ap.last_run_at) : "Never"))),
      h("div", {style: {marginTop: "14px"}}, h("button", {class: "btn sm", onClick: () => ctx.go("create", "autopilot")}, ap.enabled ? "Adjust plan" : "Turn on")));

    // Recent runs
    const runsCard = h("div", {class: "card", style: {padding: "20px 0 8px"}},
      h("div", {class: "card-title", style: {padding: "0 20px"}}, h("h3", {}, "Recent runs")),
      jobs.length ? h("div", {}, ...jobs.map(j => h("div", {class: "row"}, h("div", {class: "row-main"}, h("div", {class: "row-title", style: {fontSize: "15px"}}, jobTitle(j, videos)), h("div", {class: "row-sub"}, j.stage && j.status !== "done" ? j.stage + ", " : "", fmt.ago(j.created_at), j.error ? ". " + j.error.slice(0, 80) : "")), statusPill(j.status))))
      : empty("No runs yet", "Every video made or posted shows up here with its status."));

    clear(body).append(statGrid, statNote, h("div", {class: "dash-grid"}, h("div", {class: "dash-col"}, viewsCard, madeCard, topCard), h("div", {class: "dash-col"}, apCard, runsCard)));
    if (total30) areaChart(chartEl, {series, days, height: 260});
    if (videos.length) barLineChart(madeEl, {days, counts, scores, height: 200});
  }

  function thumb(v) {
    return v.thumb_url ? h("img", {class: "thumb-sm", src: v.thumb_url, alt: "", loading: "lazy"}) : h("span", {class: "thumb-sm"});
  }

  // Live: refresh when a job or video changes
  let unsub = [];
  return {
    mount,
    async show() {
      await load();
      if (!unsub.length) unsub = [db.subscribe("jobs", null, () => load(true)), db.subscribe("videos", null, () => load(true))];
    },
  };
}

function jobTitle(j, videos) {
  const v = videos.find(x => x.id === (j.video_id || j.id));
  const what = j.kind === "publish" ? "Post" : j.kind === "stats" ? "Pull stats" : "Make";
  return `${what}: ${v?.title || v?.topic || j.options?.topic || (j.kind === "stats" ? "YouTube and Instagram" : "trending topic")}`;
}

function nextSlotLabel(ap) {
  const hours = [...(ap.post_hours || [])].sort((a, b) => a - b);
  if (!hours.length) return "No hours set";
  const now = new Date(Date.now() + 330 * 60000); // IST
  const hNow = now.getUTCHours() + now.getUTCMinutes() / 60;
  const next = hours.find(x => x > hNow);
  const hh = x => `${((x + 11) % 12) + 1}${x >= 12 ? " pm" : " am"}`;
  return next !== undefined ? `Today ${hh(next)}` : `Tomorrow ${hh(hours[0])}`;
}
