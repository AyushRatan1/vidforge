// Dashboard: a plain grid of equal boxes. Metrics row, views chart, Autopilot + Making now | Recent runs, Top videos.
// Data comes from db only; colours and layout from styles.css.
import {h, clear, Button, Card, Grid, StatTile, Segmented, Switch, Status, PlatformMark, ProgressBar, StepList, EmptyState, Skeleton, ListRow, Table, toast} from "../components.js";
import {lineChart, lineKey} from "../charts.js";
import {fmt, dayStr, STAGES, stageIndex} from "../format.js";

export function dashboardPage(ctx, el, actions) {
  const {db} = ctx;
  let platform = "all", data = null, loading = false;
  const mount = () => {};
  mount(actions);

  const intro = h("p", {class: "page-intro"}, ctx.demo ? "Sample data. Last 7 days compared with the 7 before." : "Last 7 days compared with the 7 before. Stats refresh daily at 07:45 IST.");
  const grid = h("div", {class: "dash", "aria-busy": "true"});
  el.append(intro, grid);
  skeleton();

  function skeleton() {
    const box = n => Card({body: Skeleton({lines: n})});
    clear(grid).append(Grid(4, [1, 2, 3, 4].map(() => box(3))), Card({body: Skeleton({height: 240})}), Grid(2, [box(6), box(6)]));
  }

  async function load(force) {
    if ((data && !force) || loading) return;
    loading = true;
    try {
      const [videos, stats, channel, jobs, autopilot] = await Promise.all([db.listVideos(), db.listStats(45), db.listChannelStats(45), db.listJobs(8), db.getAutopilot()]);
      data = {videos, stats, channel, jobs, autopilot};
      ctx.videosCache = videos;
      render();
    } catch (e) { clear(grid).append(Card({title: "Could not load the dashboard", body: EmptyState({compact: true, title: e.message + (e.hint ? " " + e.hint : ""), action: Button({label: "Try again", variant: "secondary", onClick: () => load(true)})})})); }
    finally { loading = false; grid.setAttribute("aria-busy", "false"); }
  }

  function render() {
    if (!data) return;
    const {videos, stats, channel, jobs, autopilot} = data;
    const plat = r => platform === "all" || r.platform === platform;
    const days = [...Array(30)].map((_, i) => dayStr(new Date(Date.now() - (29 - i) * 864e5)));
    const today = days[29];
    const d7 = dayStr(new Date(Date.now() - 7 * 864e5)), d14 = dayStr(new Date(Date.now() - 14 * 864e5));

    const perDay = {youtube: Object.fromEntries(days.map(d => [d, 0])), instagram: Object.fromEntries(days.map(d => [d, 0]))};
    const sum7 = {views: 0, likes: 0, comments: 0}, prev7 = {views: 0, likes: 0, comments: 0};
    for (const r of stats) {
      if (!plat(r)) continue;
      if (perDay[r.platform] && r.day in perDay[r.platform]) perDay[r.platform][r.day] += r.views || 0;
      const bucket = r.day > d7 ? sum7 : r.day > d14 ? prev7 : null;
      if (bucket) { bucket.views += r.views || 0; bucket.likes += r.likes || 0; bucket.comments += r.comments || 0; }
    }
    const latestChannel = p => [...channel].filter(c => c.platform === p).sort((a, b) => b.day.localeCompare(a.day));
    const followers = p => latestChannel(p)[0]?.followers ?? 0;
    const plats = platform === "all" ? ["youtube", "instagram"] : [platform];
    const followersNow = plats.reduce((a, p) => a + followers(p), 0);
    const followersPrev = plats.reduce((a, p) => a + (latestChannel(p).find(c => c.day <= d7)?.followers ?? followers(p)), 0);
    const postedIn = (from, to) => videos.filter(v => v.status === "posted" && (platform === "all" || (platform === "youtube" ? v.youtube_url : v.instagram_url)) && v.created_at.slice(0, 10) > from && (!to || v.created_at.slice(0, 10) <= to)).length;
    const spend = (from, to) => videos.filter(v => v.created_at.slice(0, 10) > from && (!to || v.created_at.slice(0, 10) <= to)).reduce((a, v) => a + (v.usd || 0), 0);
    const platName = platform === "youtube" ? "YouTube" : platform === "instagram" ? "Instagram" : "";

    // Metrics row
    const metrics = Grid(4, [
      StatTile({label: "Views", value: fmt.compact(sum7.views), delta: {cur: sum7.views, prev: prev7.views}}),
      StatTile({label: "Likes", value: fmt.compact(sum7.likes), delta: {cur: sum7.likes, prev: prev7.likes}}),
      StatTile({label: platform === "youtube" ? "Subscribers" : "Followers", value: fmt.compact(followersNow), delta: {cur: followersNow, prev: followersPrev}, deltaLabel: "vs 7 days ago"}),
      StatTile({label: "Posted", value: String(postedIn(d7)), delta: {cur: postedIn(d7), prev: postedIn(d14, d7)}, onClick: () => ctx.go("library")}),
    ]);

    // Views chart
    const series = plats.map(p => ({name: p === "youtube" ? "YouTube" : "Instagram", tone: p === "youtube" ? "yt" : "ig", values: days.map(d => perDay[p][d])}));
    const total30 = series.reduce((a, s) => a + s.values.reduce((x, y) => x + y, 0), 0);
    const chartEl = h("div", {class: "chart"});
    const seg = Segmented([{value: "all", label: "All"}, {value: "youtube", label: "YouTube"}, {value: "instagram", label: "Instagram"}], platform, v => { platform = v; render(); }, {size: "sm", ariaLabel: "Platform"});
    const chartBox = Card({title: "Views", subtitle: "Last 30 days" + (platName ? ", " + platName : ""), actions: seg,
      body: h("div", {class: "stack"},
        h("div", {class: "chart-total"}, h("span", {class: "chart-total-n num"}, fmt.compact(total30)), h("div", {class: "legend"}, ...series.map(s => h("span", {}, lineKey(s.tone), s.name)))),
        total30 ? chartEl : EmptyState({compact: true, title: "No views yet", text: "Daily views appear here the morning after your first video is posted."}))});

    // Autopilot
    const ap = autopilot || {};
    const todayCount = videos.filter(v => v.source === "autopilot" && v.created_at.slice(0, 10) === today).length;
    const queue = (ap.topics || []).filter(t => t.status !== "done").length;
    const apSwitch = Switch(!!ap.enabled, async v => {
      try { const {updated_at, last_run_at, ...rest} = ap; data.autopilot = await db.saveAutopilot({...rest, enabled: v}); toast(v ? "Autopilot is on" : "Autopilot is paused", "ok"); render(); }
      catch (e) { apSwitch.set(!v); toast("Could not change autopilot: " + e.message, "err"); }
    }, "Autopilot on");
    const spend7 = spend(d7), spendPrev = spend(d14, d7);
    const apBox = Card({title: "Autopilot", subtitle: ap.enabled ? "On, runs hourly on GitHub" : "Paused", flush: true,
      actions: h("div", {class: "cluster"}, apSwitch, Button({label: "Adjust plan", variant: "secondary", size: "sm", onClick: () => ctx.go("create", "autopilot")})),
      body: h("div", {class: "kv"},
        kv("Next slot", ap.enabled ? nextSlotLabel(ap) : "Paused"),
        kv("Made today", `${todayCount} of ${ap.videos_per_day || 0}`),
        kv("Queue", queue ? `${queue} topic${queue === 1 ? "" : "s"}` : (ap.trending_fill ? "Trending fill" : "Empty")),
        kv("Last run", ap.last_run_at ? fmt.ago(ap.last_run_at) : "Never"),
        kv("Claude spend, 7 days", fmt.usd(spend7), spendPrev ? fmt.pct(spend7, spendPrev) + " vs prior 7 days" : null))});

    // Making now
    const live = jobs.find(j => j.kind === "make" && (j.status === "running" || j.status === "queued")) || null;
    const liveVideo = live ? videos.find(v => v.id === (live.video_id || live.id)) : videos.find(v => v.status === "making" || v.status === "queued");
    const stage = (liveVideo?.stage || live?.stage || "").toLowerCase();
    let idx = stageIndex(STAGES, stage);
    const total = 7;
    if (idx < 0) idx = 0;
    const making = (live || liveVideo) ? h("div", {class: "making"},
        h("div", {class: "making-title"}, liveVideo?.title || live?.options?.topic || "Finding a trending topic"),
        h("div", {class: "making-stage num"}, live?.status === "queued" ? "Waiting for a runner" : `Step ${idx + 1} of ${total}: ${STAGES[idx] || "Starting"}`),
        ProgressBar(Math.max(0.04, idx / total), {label: "Run progress"}),
        h("div", {class: "making-meta"}, Status(live?.status || liveVideo?.status), h("span", {}, fmt.ago(live?.created_at || liveVideo?.created_at)), live?.run_url ? h("a", {href: live.run_url, target: "_blank", rel: "noopener"}, "Watch the run") : null),
        StepList(STAGES.slice(0, total), live?.status === "queued" ? -1 : idx, {compact: true}))
      : EmptyState({compact: true, title: "Nothing is being made.", text: "When a run starts, its step and progress show here."});
    const makingBox = Card({title: "Making now", subtitle: live ? "Live from the worker" : null, body: making,
      actions: (live || liveVideo) ? null : Button({label: "Make a video", variant: "secondary", size: "sm", onClick: () => ctx.go("create")})});

    // Recent runs
    const runsBox = Card({title: "Recent runs", subtitle: "Make, post and stats jobs", flush: true,
      body: jobs.length ? h("div", {class: "list"}, ...jobs.slice(0, 8).map(j => ListRow({title: jobTitle(j, videos), sub: [j.stage && j.status !== "done" && j.status !== "failed" ? j.stage + ", " : "", fmt.ago(j.created_at), j.error ? ". " + j.error.slice(0, 80) : ""].join(""),
        control: Status(j.status), onClick: j.video_id ? () => ctx.go("library", j.video_id) : null})))
        : EmptyState({compact: true, title: "No runs yet.", text: "Every video made or posted shows up here with its status."})});

    // Top videos
    const withViews = videos.filter(v => v.status === "posted").map(v => ({...v, views: stats.filter(r => r.video_id === v.id && plat(r)).reduce((a, r) => a + (r.views || 0), 0)})).sort((a, b) => b.views - a.views).slice(0, 6);
    const topBox = Card({title: "Top videos", subtitle: "By views" + (platName ? ", " + platName : ""), flush: true,
      actions: Button({label: "Open library", variant: "ghost", size: "sm", onClick: () => ctx.go("library")}),
      body: withViews.length ? Table({caption: "Top videos by views", onRow: v => ctx.go("library", v.id), rows: withViews, columns: [
          {key: "thumb", label: "", width: "62px", render: thumb},
          {key: "title", label: "Title", render: v => h("span", {class: "cell-title"}, v.title || v.topic || v.id)},
          {key: "platforms", label: "Platforms", width: "96px", class: "hide-sm", render: v => h("span", {class: "marks"}, PlatformMark("youtube", v.youtube_url), PlatformMark("instagram", v.instagram_url))},
          {key: "views", label: "Views", align: "right", width: "96px", render: v => h("span", {class: "num"}, fmt.int(v.views))},
          {key: "posted", label: "Posted", align: "right", width: "96px", render: v => h("span", {class: "muted num"}, fmt.date(v.created_at))},
        ]})
        : EmptyState({compact: true, title: "No posted videos.", text: "Once a video is posted it is ranked here by views."})});

    clear(grid).append(metrics, chartBox, h("div", {class: "grid grid-2"}, h("div", {class: "dash-col"}, apBox, makingBox), runsBox), topBox);
    if (total30) lineChart(chartEl, {series, days, height: 240, fill: series.length === 1});
  }

  const kv = (k, v, note) => h("div", {class: "kv-row"}, h("span", {class: "kv-k"}, k), h("span", {class: "kv-v num"}, v, note ? h("span", {class: "micro"}, note) : null));
  const thumb = v => v.thumb_url ? h("img", {class: "thumb-sm", src: v.thumb_url, alt: "", loading: "lazy"}) : h("span", {class: "thumb-sm"});

  let unsub = [], timer = null;
  return {
    mount,
    refresh: () => load(true),
    async show() {
      const had = !!data;
      await load();
      if (had) render(); // redraw charts now that the page is visible
      if (!unsub.length) unsub = [db.subscribe("jobs", null, () => schedule()), db.subscribe("videos", null, () => schedule())];
    },
  };
  function schedule() { clearTimeout(timer); timer = setTimeout(() => load(true), 400); }
}

function jobTitle(j, videos) {
  const v = videos.find(x => x.id === (j.video_id || j.id));
  const what = j.kind === "publish" ? "Post" : j.kind === "stats" ? "Pull stats" : "Make";
  return `${what}: ${v?.title || v?.topic || j.options?.topic || (j.kind === "stats" ? "YouTube and Instagram" : "trending topic")}`;
}

function nextSlotLabel(ap) {
  const hours = [...(ap.post_hours || [])].sort((a, b) => a - b);
  if (!hours.length) return "No hours set";
  const now = new Date(Date.now() + 330 * 60000);
  const hNow = now.getUTCHours() + now.getUTCMinutes() / 60;
  const next = hours.find(x => x > hNow);
  return next !== undefined ? `Today ${fmt.hour(next)} IST` : `Tomorrow ${fmt.hour(hours[0])} IST`;
}
