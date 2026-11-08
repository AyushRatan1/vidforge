// Formatting helpers and the option lists shared by Create, Library and Dashboard.

export const fmt = {
  int: n => (n ?? 0).toLocaleString("en-IN"),
  compact: n => { n = n ?? 0; if (n >= 1e7) return (n / 1e7).toFixed(1).replace(/\.0$/, "") + " Cr"; if (n >= 1e5) return (n / 1e5).toFixed(1).replace(/\.0$/, "") + " L"; if (n >= 1e3) return (n / 1e3).toFixed(n >= 1e4 ? 0 : 1).replace(/\.0$/, "") + "K"; return String(Math.round(n)); },
  usd: n => "$" + (n ?? 0).toFixed(2),
  dur: s => { s = Math.round(s || 0); return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; },
  date: iso => iso ? new Date(iso).toLocaleDateString("en-IN", {day: "numeric", month: "short"}) : "",
  dateTime: iso => iso ? new Date(iso).toLocaleString("en-IN", {day: "numeric", month: "short", hour: "numeric", minute: "2-digit"}) : "",
  ago: iso => { if (!iso) return ""; const m = Math.round((Date.now() - new Date(iso)) / 60000); if (m < 1) return "just now"; if (m < 60) return m + " min ago"; const hh = Math.round(m / 60); if (hh < 24) return hh + " h ago"; return Math.round(hh / 24) + " d ago"; },
  pct: (a, b) => { if (!b) return a ? "new" : "0%"; const p = Math.round(((a - b) / b) * 100); return (p > 0 ? "+" : "") + p + "%"; },
  hour: hh => `${((hh + 11) % 12) + 1}${hh >= 12 ? " pm" : " am"}`,
};

export const LANGS = [["en", "English"], ["hi", "Hindi"], ["hinglish", "Hinglish"], ["es", "Spanish"], ["fr", "French"], ["it", "Italian"], ["pt", "Portuguese"]];
export const NICHES = [["space", "Space"], ["science", "Science"], ["tech", "Tech"], ["stories", "Stories"], ["mythology", "Mythology"], ["kids", "Kids"], ["news", "News explained"], ["sports", "Sports"], ["animals", "Animals"], ["food", "Food"], ["travel", "Travel"], ["history", "History"], ["architecture", "Architecture"], ["trending", "Anything trending"]];
export const FORMATS = [["auto", "Auto"], ["3d_build", "3D build"], ["facts", "Facts explainer"], ["trend", "Trend explained"], ["story", "Story"], ["toplist", "Top list"], ["festival", "Festival story"], ["quiz", "Quiz"], ["kids_learning", "Kids learning"], ["kids_story", "Kids story"]];
export const WRITERS = [["claude-opus-5-5", "Opus 5.5"], ["claude-fable-5-1", "Fable 5.1"], ["claude-sonnet-5-5", "Sonnet 5.5"]];
export const VOICES = [["auto", "Auto"], ["af_heart", "Heart (warm)"], ["af_bella", "Bella (bright)"], ["am_adam", "Adam (deep)"], ["hf_alpha", "Alpha (Hindi)"], ["hm_omega", "Omega (Hindi)"]];
export const MUSIC = [["auto", "Auto"], ["none", "None"], ["calm", "Calm"], ["upbeat", "Upbeat"], ["epic", "Epic"], ["playful", "Playful"]];
export const STAGES = ["Find trend", "Research", "Write and direct", "Review frames", "Render video", "Write captions and hashtags", "Save to library", "Post to YouTube and Instagram"];

export const opts = pairs => pairs.map(([value, label]) => ({value, label}));
export const langName = code => Object.fromEntries(LANGS)[code] || code || "";
export const nicheName = code => Object.fromEntries(NICHES)[code] || code || "";

export const dayStr = d => d.toISOString().slice(0, 10);
export function compactTs() { const d = new Date(); const p = n => String(n).padStart(2, "0"); return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`; }
export function rand4() { const a = "abcdefghjkmnpqrstuvwxyz23456789"; return [...crypto.getRandomValues(new Uint8Array(4))].map(b => a[b % a.length]).join(""); }

// Index of a worker stage name (case-insensitive, exact first, then prefix) in a stage list, or -1.
export function stageIndex(stages, stage) {
  const st = (stage || "").toLowerCase().trim();
  if (!st) return -1;
  const exact = stages.findIndex(sn => sn.toLowerCase() === st);
  if (exact >= 0) return exact;
  return stages.findIndex(sn => sn.toLowerCase().startsWith(st.slice(0, 8)) || st.startsWith(sn.toLowerCase().slice(0, 8)));
}
