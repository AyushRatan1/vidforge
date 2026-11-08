// Dashboard: bento grid of live tiles. Data comes from db only; colours and layout from styles.css.
import {h, clear, Button, BentoTile, StatTile, Segmented, Switch, Status, Pill, PlatformMark, ProgressRing, ProgressBar, EmptyState, Skeleton, ListRow, toast, icon} from "../components.js";
import {areaChart} from "../charts.js";
import {fmt, dayStr, STAGES, stageIndex} from "../format.js";

export function dashboardPage(ctx, el, actions) {
  const {db} = ctx;
  let platform = "all", data = null, loading = false;
  const refresh = Button({variant: "icon", icon: "refresh", ariaLabel: "Refresh", onClick: () => load(true)});
  const mount = tb => tb.append(refresh);
  mount(actions);

  const grid = h("div", {class: "bento stagger", "aria-busy": "true"});
  el.append(h("div", {class: "page-intro"}, h("p", {}, ctx.demo ? "Sample data. Every tile updates live when a run changes." : "Last 7 days against the 7 before. Stats refresh daily at 07:45 IST.")), grid);
  skeleton();

  function skeleton() {
    clear(grid).append(
      BentoTile({span: "2x2", body: Skeleton({height: 280})}),
      ...[1, 2, 3, 4, 5, 6].map(() => BentoTile({body: Skeleton({lines: 3})})),
      BentoTile({span: "2x1", body: Skeleton({lines: 3})}), BentoTile({span: "2x1", body: Skeleton({lines: 3})}),
      BentoTile({span: "2x2", body: Skeleton({lines: 6})}), BentoTile({span: "2x1", body: Skeleton({lines: 4})}));
  }

  async function load(force) {
    if ((data && !force) || loading) return;
    loading = true;
    try {
      const [videos, stats, channel, jobs, autopilot] = await Promise.all([db.listVideos(), db.listStats(45), db.listChannelStats(45), db.listJobs(8), db.getAutopilot()]);
      data = {videos, stats, channel, jobs, autopilot};
      ctx.videosCache = videos;
      render();
    } catch (e) { clear(grid).append(BentoTile({span: "4x1", body: EmptyState({icon: "warning", title: "Could not load the dashboard", text: e.message + (e.hint ? " " + e.hint : ""), action: Button({label: "Try again", variant: "primary", onClick: () => load(true)})})})); }
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

    // Hero: views chart
    const series = plats.map(p => ({name: p === "youtube" ? "YouTube" : "Instagram", tone: p === "youtube" ? "yt" : "ig", values: days.map(d => perDay[p][d])}));
    const total30 = series.reduce((a, s) => a + s.values.reduce((x, y) => x + y, 0), 0);
    const chartEl = h("div", {class: "chart"});
    const seg = Segmented([{value: "all", label: "All"}, {value: "youtube", label: "YouTube"}, {value: "instagram", label: "Instagram"}], platform, v => { platform = v; render(); }, {size: "sm", ariaLabel: "Platform"});
    const hero = BentoTile({span: "2x2", class: "tile-hero",
      body: h("div", {class: "stack", style: {height: "100%"}},
        h("div", {class: "hero-chart-head"},
          h("div", {}, h("div", {class: "hero-chart-sub"}, "Views, last 30 days"), h("div", {class: "hero-chart-total num"}, fmt.compact(total30))),
          h("div", {class: "stack-sm", style: {alignItems: "end", justifyItems: "end"}}, seg, h("div", {class: "legend"}, ...series.map(s => h("span", {}, h("span", {class: `swatch tone-${s.tone}`}), s.name))))),
        total30 ? chartEl : EmptyState({icon: "activity", title: "No views yet", text: "Daily views appear here the morning after your first video is posted."}))});
    hero.prepend(h("div", {class: "aurora aurora-chart", "aria-hidden": "true"}));

    // Stat tiles
    const statTiles = [
      StatTile({label: "Views", value: fmt.compact(sum7.views), icon: "eye", delta: {cur: sum7.views, prev: prev7.views}, hint: "7 days"}),
      StatTile({label: "Likes", value: fmt.compact(sum7.likes), icon: "heart", delta: {cur: sum7.likes, prev: prev7.likes}, hint: "7 days"}),
      StatTile({label: "Comments", value: fmt.compact(sum7.comments), icon: "message", delta: {cur: sum7.comments, prev: prev7.comments}, hint: "7 days"}),
      StatTile({label: platform === "youtube" ? "Subscribers" : "Followers", value: fmt.compact(followersNow), icon: "users", delta: {cur: followersNow, prev: followersPrev}, hint: "vs 7 days ago"}),
      StatTile({label: "Posted", value: String(postedIn(d7)), icon: "send", delta: {cur: postedIn(d7), prev: postedIn(d14, d7)}, hint: "7 days", onClick: () => ctx.go("library")}),
      StatTile({label: "Claude spend", value: fmt.usd(spend(d7)), icon: "dollar", delta: {cur: spend(d7), prev: spend(d14, d7), inverse: true}, hint: "7 days"}),
    ];

    // Autopilot
    const ap = autopilot || {};
    const todayCount = videos.filter(v => v.source === "autopilot" && v.created_at.slice(0, 10) === today).length;
    const queue = (ap.topics || []).filter(t => t.status !== "done").length;
    const apSwitch = Switch(!!ap.enabled, async v => {
      try { const {updated_at, last_run_at, ...rest} = ap; data.autopilot = await db.saveAutopilot({...rest, enabled: v}); toast(v ? "Autopilot is on" : "Autopilot is paused", "ok"); render(); }
      catch (e) { apSwitch.set(!v); toast("Could not change autopilot: " + e.message, "err"); }
    }, "Autopilot on");
    const apTile = BentoTile({span: "2x1", title: "Autopilot", subtitle: ap.enabled ? "Hourly on GitHub" : "Paused",
      actions: h("div", {class: "cluster", style: {gap: "12px"}}, Pill(ap.enabled ? "On" : "Off", ap.enabled ? "ok" : "neutral", {dot: true}), apSwitch, Button({label: "Adjust plan", variant: "secondary", size: "sm", iconRight: "arrowRight", onClick: () => ctx.go("create", "autopilot")})),
      body: h("div", {class: "ap-grid"},
        kpi("Next slot, IST", ap.enabled ? nextSlotLabel(ap) : "Paused"),
        kpi("Today", `${todayCount} of ${ap.videos_per_day || 0}`),
        kpi("Queue", queue ? `${queue} topic${queue === 1 ? "" : "s"}` : (ap.trending_fill ? "Trending fill" : "Empty")),
        kpi("Last run", ap.last_run_at ? fmt.ago(ap.last_run_at) : "Never"))});

    // Making now
    const live = jobs.find(j => j.kind === "make" && (j.status === "running" || j.status === "queued")) || null;
    const liveVideo = live ? videos.find(v => v.id === (live.video_id || live.id)) : videos.find(v => v.status === "making" || v.status === "queued");
    const stage = (liveVideo?.stage || live?.stage || "").toLowerCase();
    let idx = stageIndex(STAGES, stage);
    const total = 7;
    if (idx < 0) idx = 0;
    const making = (live || liveVideo) ? h("div", {class: "making"},
      ProgressRing({value: Math.max(0.04, idx / total), size: 72, stroke: 6, label: `Step ${idx + 1} of ${total}`, children: h("span", {class: "ring-label num"}, `${idx + 1}/${total}`)}),
      h("div", {class: "stack-sm"},
        h("div", {class: "making-title"}, liveVideo?.title || live?.options?.topic || "Finding a trending topic"),
        h("div", {class: "making-stage"}, live?.status === "queued" ? "Waiting for a runner" : (STAGES[idx] || "Starting")),
        ProgressBar(Math.max(0.04, idx / total), {label: "Run progress"}),
        h("div", {class: "cluster"}, Status(live?.status || liveVideo?.status, {small: true}), live?.run_url ? h("a", {class: "micro", href: live.run_url, target: "_blank", rel: "noopener"}, "Watch the run") : null, h("span", {class: "micro"}, fmt.ago(live?.created_at || liveVideo?.created_at)))))
      : EmptyState({icon: "clapperboard", title: "Nothing is being made", text: "When a run starts, its step and progress show here.", compact: true, action: Button({label: "Make a video", variant: "secondary", size: "sm", onClick: () => ctx.go("create")})});
    const makingTile = BentoTile({span: "2x1", title: "Making now", subtitle: live ? "Live from the worker" : null, body: making});

    // Top videos
    const withViews = videos.filter(v => v.status === "posted").map(v => ({...v, views: stats.filter(r => r.video_id === v.id && plat(r)).reduce((a, r) => a + (r.views || 0), 0)})).sort((a, b) => b.views - a.views).slice(0, 6);
    const topTile = BentoTile({span: "2x2", title: "Top videos", subtitle: "By views" + (platform === "all" ? "" : ", " + (platform === "youtube" ? "YouTube" : "Instagram")),
      actions: Button({label: "Library", variant: "ghost", size: "sm", iconRight: "arrowRight", onClick: () => ctx.go("library")}),
      body: withViews.length ? h("div", {class: "list"}, ...withViews.map((v, i) => ListRow({title: v.title || v.topic || v.id, sub: h("span", {class: "cluster", style: {gap: "8px"}}, h("span", {class: "marks"}, v.youtube_url ? PlatformMark("youtube", v.youtube_url, {size: 12}) : null, v.instagram_url ? PlatformMark("instagram", v.instagram_url, {size: 12}) : null), "Posted " + fmt.date(v.created_at)),
        leading: h("span", {class: "cluster", style: {gap: "10px"}}, h("span", {class: "rank num"}, String(i + 1)), thumb(v)), value: fmt.compact(v.views), onClick: () => ctx.go("library", v.id)})))
        : EmptyState({icon: "flame", title: "No posted videos", text: "Once a video is posted it is ranked here by views.", compact: true})});

    // Recent runs
    const runsTile = BentoTile({span: "2x1", title: "Recent runs", subtitle: "Make, post and stats jobs",
      body: jobs.length ? h("div", {class: "list"}, ...jobs.slice(0, 4).map(j => ListRow({title: jobTitle(j, videos), sub: [j.stage && j.status !== "done" && j.status !== "failed" ? j.stage + ", " : "", fmt.ago(j.created_at), j.error ? ". " + j.error.slice(0, 80) : ""].join(""),
        control: Status(j.status, {small: true}), onClick: j.video_id ? () => ctx.go("library", j.video_id) : null})))
        : EmptyState({icon: "activity", title: "No runs yet", text: "Every video made or posted shows up here with its status.", compact: true})});

    clear(grid).append(hero, ...statTiles.slice(0, 4), statTiles[4], statTiles[5], apTile, makingTile, topTile, runsTile);
    if (total30) areaChart(chartEl, {series, days, height: 250});
  }

  const kpi = (k, v) => h("div", {class: "kpi"}, h("span", {class: "kpi-k"}, k), h("span", {class: "kpi-v num"}, v));
  const thumb = v => v.thumb_url ? h("img", {class: "thumb-sm", src: v.thumb_url, alt: "", loading: "lazy"}) : h("span", {class: "thumb-sm"}, icon("film", {size: 16}));

  let unsub = [], timer = null;
  return {
    mount,
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
  return next !== undefined ? `Today ${fmt.hour(next)}` : `Tomorrow ${fmt.hour(hours[0])}`;
}
