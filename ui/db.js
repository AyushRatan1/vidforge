// Data layer. Two implementations with the same methods: Supabase (the real thing) and demo (ui/demo/*.json).
// Pages only ever talk to the object returned here.
//
//   auth:       getSession() signIn(email, password) signOut() onAuth(cb) user()
//   settings:   getSettings() -> {key: value}   saveSettings({key: value})
//   videos:     listVideos(limit) getVideo(id) updateVideo(id, patch)
//   stats:      listStats(days) listChannelStats(days)
//   jobs:       listJobs(limit) insertJob(row)
//   autopilot:  getAutopilot() saveAutopilot(row)
//   live:       subscribe(table, id | null, cb) -> unsubscribe()      (demo: simulated)
//   worker:     dispatch(workflowFile, inputs)                        (GitHub API, token from settings)

import {DEFAULTS} from "./config.js";

const SUPABASE_ESM = "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.49.4/+esm";
export const DRAFT_WF = "draft-video.yml";
export const PUBLISH_WF = "publish-video.yml";

export class DbError extends Error {
  constructor(message, hint) { super(message); this.hint = hint; }
}

// ------------------------------------------------------------------ GitHub dispatch (shared by both)
async function githubDispatch(settings, workflow, inputs) {
  const token = settings.github_token, repo = settings.github_repo || DEFAULTS.githubRepo;
  if (!token) throw new DbError("No GitHub token saved.", "Add one in Settings, GitHub.");
  if (!repo || !repo.includes("/")) throw new DbError("No repository saved.", "Set it as owner/name in Settings, GitHub.");
  const headers = {Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"};
  let ref = "main";
  try {
    const r = await fetch(`https://api.github.com/repos/${repo}`, {headers});
    if (r.ok) ref = (await r.json()).default_branch || ref;
    else if (r.status === 401) throw new DbError("GitHub rejected the token.", "Create a new fine-grained token with Actions read and write.");
    else if (r.status === 404) throw new DbError(`Repository ${repo} was not found.`, "Check Settings, GitHub, or give the token access to it.");
  } catch (e) { if (e instanceof DbError) throw e; }
  const r = await fetch(`https://api.github.com/repos/${repo}/actions/workflows/${workflow}/dispatches`, {
    method: "POST", headers: {...headers, "Content-Type": "application/json"}, body: JSON.stringify({ref, inputs}),
  });
  if (r.status === 204) return {ok: true, ref};
  const text = await r.text().catch(() => "");
  if (r.status === 404) throw new DbError(`Workflow ${workflow} was not found on ${ref}.`, "Push the workflow file to the repository first.");
  if (r.status === 403) throw new DbError("The token cannot start workflows.", "It needs Actions read and write for this repository.");
  throw new DbError(`GitHub returned ${r.status}.`, text.slice(0, 200));
}

// ------------------------------------------------------------------ Supabase
export async function connectSupabase(url, anonKey) {
  const {createClient} = await import(SUPABASE_ESM);
  const sb = createClient(url, anonKey, {auth: {persistSession: true, autoRefreshToken: true, storageKey: "vf.auth"}});
  const unwrap = ({data, error}) => { if (error) throw new DbError(error.message, error.hint || error.details || ""); return data; };
  let settingsCache = null;

  const db = {
    mode: "supabase",
    async getSession() { return unwrap(await sb.auth.getSession()).session; },
    async signIn(email, password) { return unwrap(await sb.auth.signInWithPassword({email, password})); },
    async signOut() { settingsCache = null; await sb.auth.signOut(); },
    onAuth(cb) { const {data} = sb.auth.onAuthStateChange((_e, s) => cb(s)); return () => data.subscription.unsubscribe(); },
    async user() { return (await db.getSession())?.user || null; },

    async getSettings(fresh = false) {
      if (settingsCache && !fresh) return settingsCache;
      const rows = unwrap(await sb.from("settings").select("key,value,updated_at"));
      settingsCache = Object.fromEntries(rows.map(r => [r.key, r.value]));
      settingsCache.__updated = Object.fromEntries(rows.map(r => [r.key, r.updated_at]));
      return settingsCache;
    },
    async saveSettings(obj) {
      const rows = Object.entries(obj).map(([key, value]) => ({key, value: value ?? ""}));
      if (rows.length) unwrap(await sb.from("settings").upsert(rows, {onConflict: "key"}));
      settingsCache = null;
      return db.getSettings();
    },

    async listVideos(limit = 500) { return unwrap(await sb.from("videos").select("*").order("created_at", {ascending: false}).limit(limit)); },
    async getVideo(id) { return unwrap(await sb.from("videos").select("*").eq("id", id).maybeSingle()); },
    async updateVideo(id, patch) { return unwrap(await sb.from("videos").update(patch).eq("id", id).select().maybeSingle()); },

    async listStats(days = 60) {
      const since = dayStr(new Date(Date.now() - days * 864e5));
      return unwrap(await sb.from("stats").select("video_id,platform,day,views,likes,comments,shares,saves").gte("day", since).limit(20000));
    },
    async listChannelStats(days = 60) {
      const since = dayStr(new Date(Date.now() - days * 864e5));
      return unwrap(await sb.from("channel_stats").select("*").gte("day", since).order("day", {ascending: true}));
    },

    async listJobs(limit = 30) { return unwrap(await sb.from("jobs").select("*").order("created_at", {ascending: false}).limit(limit)); },
    async insertJob(row) { return unwrap(await sb.from("jobs").insert(row).select().single()); },

    async getAutopilot() { return unwrap(await sb.from("autopilot").select("*").eq("id", 1).maybeSingle()); },
    async saveAutopilot(row) { return unwrap(await sb.from("autopilot").upsert({...row, id: 1}, {onConflict: "id"}).select().single()); },

    subscribe(table, id, cb) {
      const name = `${table}-${id || "all"}-${Math.random().toString(36).slice(2, 7)}`;
      const filter = id ? {filter: `id=eq.${id}`} : {};
      const ch = sb.channel(name).on("postgres_changes", {event: "*", schema: "public", table, ...filter}, payload => cb(payload.new || payload.old, payload.eventType)).subscribe();
      return () => sb.removeChannel(ch);
    },

    async dispatch(workflow, inputs) { return githubDispatch(await db.getSettings(), workflow, inputs); },
  };
  return db;
}

// ------------------------------------------------------------------ Demo
export async function connectDemo() {
  const load = async name => { try { return await (await fetch(`demo/${name}.json`, {cache: "no-store"})).json(); } catch { return null; } };
  const [videos, stats, channel, jobs, autopilot, settings] = await Promise.all(["videos", "stats", "channel_stats", "jobs", "autopilot", "settings"].map(load));
  const state = {videos: videos || [], stats: stats || [], channel: channel || [], jobs: jobs || [], autopilot: autopilot || {id: 1}, settings: settings || {}};
  const subs = new Set();
  const emit = (table, rowObj, type = "UPDATE") => { for (const s of subs) if (s.table === table && (!s.id || s.id === rowObj.id)) s.cb(structuredClone(rowObj), type); };
  const sleep = ms => new Promise(r => setTimeout(r, ms));

  const db = {
    mode: "demo",
    async getSession() { return {user: {email: "demo@vidforge.app"}}; },
    async signIn() { return {}; },
    async signOut() {},
    onAuth() { return () => {}; },
    async user() { return {email: "demo@vidforge.app"}; },
    async getSettings() { return {...state.settings}; },
    async saveSettings(obj) { Object.assign(state.settings, obj); await sleep(250); return {...state.settings}; },
    async listVideos() { return structuredClone(state.videos); },
    async getVideo(id) { return structuredClone(state.videos.find(v => v.id === id) || null); },
    async updateVideo(id, patch) { const v = state.videos.find(v => v.id === id); if (v) Object.assign(v, patch, {updated_at: new Date().toISOString()}); return structuredClone(v); },
    async listStats() { return structuredClone(state.stats); },
    async listChannelStats() { return structuredClone(state.channel); },
    async listJobs(limit = 30) { return structuredClone([...state.jobs].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, limit)); },
    async insertJob(row) { const r = {created_at: new Date().toISOString(), updated_at: new Date().toISOString(), options: {}, ...row}; state.jobs.unshift(r); return structuredClone(r); },
    async getAutopilot() { return structuredClone(state.autopilot); },
    async saveAutopilot(row) { state.autopilot = {...state.autopilot, ...row, updated_at: new Date().toISOString()}; await sleep(250); return structuredClone(state.autopilot); },
    subscribe(table, id, cb) { const s = {table, id, cb}; subs.add(s); return () => subs.delete(s); },

    // Pretend the worker ran: walk a job through its stages and produce a video from a sample file.
    async dispatch(workflow, inputs) {
      await sleep(400);
      const jobId = inputs.request_id;
      const job = state.jobs.find(j => j.id === jobId);
      if (!job) return {ok: true, demo: true};
      const sample = state.videos.find(v => v.video_url) || {};
      const stages = workflow === PUBLISH_WF ? ["Fetch from library", "Post"] : ["Find trend", "Research", "Write and direct", "Review frames", "Render video", "Write captions and hashtags", "Save to library"];
      (async () => {
        job.status = "running"; job.run_url = "#demo-run"; emit("jobs", job);
        if (workflow === DRAFT_WF) {
          const o = JSON.parse(inputs.options || "{}");
          const v = {id: jobId, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), status: "making", stage: stages[0], title: o.topic ? o.topic.slice(0, 80) : "A trending topic, chosen by Claude", topic: o.topic || "", language: o.language, niche: o.niche, format: o.format, aspect: o.aspect, options: o, meta: {}, sources: [], qa: {}, published: {}, source: o.source || "manual"};
          state.videos.unshift(v); emit("videos", v, "INSERT");
          for (const st of stages) { job.stage = st; v.stage = st; emit("jobs", job); emit("videos", v); await sleep(1400); }
          Object.assign(v, {status: "ready", stage: "done", duration: sample.duration || 32, qa_score: 9, usd: 0.52, video_url: sample.video_url, thumb_url: sample.thumb_url, release_url: "#", meta: sample.meta || {}, sources: sample.sources || [], qa: {score: 9, pass: true, issues: []}});
          if (o.publish?.youtube || o.publish?.instagram) { v.stage = "Post to YouTube and Instagram"; emit("videos", v); await sleep(1400); v.status = "posted"; v.youtube_url = o.publish.youtube ? "https://youtube.com/shorts/demo" : null; v.instagram_url = o.publish.instagram ? "https://www.instagram.com/reel/demo/" : null; }
          emit("videos", v);
          job.status = "done"; job.stage = "done"; job.video_id = v.id; emit("jobs", job);
        } else {
          const v = state.videos.find(x => x.id === inputs.video_id);
          for (const st of stages) { job.stage = st; emit("jobs", job); await sleep(1200); }
          if (v) { const p = JSON.parse(inputs.options || "{}").publish || {}; v.status = "posted"; if (p.youtube) v.youtube_url = "https://youtube.com/shorts/demo"; if (p.instagram) v.instagram_url = "https://www.instagram.com/reel/demo/"; emit("videos", v); }
          job.status = "done"; job.stage = "done"; emit("jobs", job);
        }
      })();
      return {ok: true, demo: true};
    },
  };
  return db;
}

export const dayStr = d => d.toISOString().slice(0, 10);
