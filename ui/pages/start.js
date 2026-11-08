// Start page: shown before sign-in (and at #/). One headline, a video frame, how it works, sign in. No decoration.
import {h, clear, Button, Card, Field, Input, icon} from "../components.js";

const README = "https://github.com/ayushratan1/vidforge#readme";
const STEPS = [
  ["Find trend", "Reads what is rising on YouTube and Instagram in your channels and languages."],
  ["Research", "Gathers the facts and keeps the sources so every claim can be checked."],
  ["Write and direct", "A script, a shot list and captions for a 45 second vertical video."],
  ["Render", "Voice, music, drawn frames and real footage, rendered on a GitHub runner."],
  ["Post", "After review it posts to YouTube Shorts and Instagram Reels at your hours."],
];

// Sample numbers for the start page. Taken from demo data when it is served, otherwise these constants.
const FALLBACK = {views: 212400, posted: 11, followers: 4860, usd: 0.52, title: "Why Mars sunsets are blue", video: null, thumb: null};

export async function loadSample() {
  try {
    const get = async n => (await fetch(`demo/${n}.json`, {cache: "no-store"})).json();
    const [videos, stats, channel] = await Promise.all([get("videos"), get("stats"), get("channel_stats")]);
    const posted = videos.filter(v => v.status === "posted");
    const views = stats.reduce((a, r) => a + (r.views || 0), 0);
    const latest = p => [...channel].filter(c => c.platform === p).sort((a, b) => b.day.localeCompare(a.day))[0]?.followers || 0;
    const usd = videos.filter(v => v.usd).reduce((a, v) => a + v.usd, 0) / Math.max(1, videos.filter(v => v.usd).length);
    const sample = posted.find(v => v.video_url && v.thumb_url) || posted.find(v => v.video_url) || videos.find(v => v.video_url) || {};
    const ok = await fetch(sample.video_url || "", {method: "HEAD"}).then(r => r.ok).catch(() => false);
    return {views, posted: posted.length, followers: latest("youtube") + latest("instagram"), usd, title: sample.title || FALLBACK.title, video: ok ? sample.video_url : null, thumb: ok ? sample.thumb_url : null};
  } catch { return {...FALLBACK}; }
}

export function startPage({demo, signedIn, project, sample, onSignIn, onProject, onOpen}) {
  const root = h("div", {class: "start"});
  const openLabel = demo ? "Open demo" : "Open dashboard";

  const nav = h("nav", {class: "start-nav", "aria-label": "Start"},
    brand(demo),
    h("div", {class: "actions"},
      Button({label: "Setup guide", variant: "ghost", href: README, target: "_blank"}),
      signedIn ? Button({label: openLabel, variant: "primary", onClick: onOpen}) : Button({label: "Sign in", variant: "primary", onClick: () => scrollTo("#signin")})));

  const hero = h("section", {class: "start-hero"},
    h("div", {class: "start-copy"},
      h("h1", {class: "start-title"}, "Short videos that make and post themselves."),
      h("p", {class: "start-sub"}, "VidForge finds a trend, writes and renders a vertical video, and posts it to YouTube and Instagram at your hours."),
      h("div", {class: "start-cta"},
        signedIn ? Button({label: openLabel, variant: "primary", size: "lg", onClick: onOpen}) : Button({label: "Sign in", variant: "primary", size: "lg", onClick: () => scrollTo("#signin")}),
        demo && !signedIn ? Button({label: "Open demo", variant: "secondary", size: "lg", onClick: onOpen}) : null),
      h("p", {class: "start-note"}, demo ? "Demo with sample data. Nothing you do here is saved." : "About $0.50 of Claude credits per video. Runs on GitHub Actions and Supabase.")),
    videoFrame(sample));

  const how = Card({title: "How it works", subtitle: "One run takes 8 to 12 minutes", flush: true,
    body: h("ol", {class: "how", id: "how"}, ...STEPS.map(([t, d], i) => h("li", {class: "how-item"}, h("span", {class: "how-n num"}, String(i + 1)), h("div", {}, h("div", {class: "how-name"}, t), h("div", {class: "how-text"}, d)))))});

  const signin = h("div", {id: "signin"},
    signedIn ? Card({class: "signin", title: "You are signed in", subtitle: "On this device", body: h("div", {class: "stack"}, h("p", {class: "secondary"}, "Open the dashboard to see today's numbers, the live run and the queue."), Button({label: openLabel, variant: "primary", size: "lg", onClick: onOpen, block: true}))})
      : signInCard({project, onSignIn, onProject, demo, onOpen}));

  root.append(nav, h("main", {class: "start-wrap"}, hero, h("div", {class: "start-grid"}, how, signin)),
    h("footer", {class: "start-foot"}, "Keys stay in your private Supabase project. Every video is kept as a GitHub Release. ", h("a", {href: README, target: "_blank", rel: "noopener"}, "Setup guide")));
  return root;
}

function scrollTo(sel) { document.querySelector(sel)?.scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start"}); setTimeout(() => document.querySelector(sel + " input")?.focus({preventScroll: true}), 450); }

export function brand(demo) {
  return h("a", {class: "brand", href: "#/", "aria-label": demo ? "VidForge start page, demo" : "VidForge start page"}, h("span", {class: "brand-mark"}, icon("play", {size: 10})), h("span", {class: "brand-name"}, "VidForge"));
}

function videoFrame(sample) {
  const screen = h("div", {class: "phone-screen"});
  if (sample.video) {
    const v = h("video", {src: sample.video, poster: sample.thumb || null, muted: true, autoplay: true, loop: true, playsinline: true, "aria-label": "Sample video: " + sample.title});
    v.muted = true;
    screen.append(v);
  } else if (sample.thumb) screen.append(h("img", {src: sample.thumb, alt: "Sample video thumbnail"}));
  else screen.append(h("div", {class: "phone-idle"}, h("strong", {}, sample.title), "A sample video plays here once the demo files are served."));
  return h("figure", {class: "phone", style: {margin: 0}, "aria-label": "Sample video"}, screen,
    h("figcaption", {class: "phone-caption"}, h("span", {}, sample.title), h("span", {class: "marks", "aria-label": "YouTube and Instagram"}, icon("youtube", {size: 14}), icon("instagram", {size: 14}))));
}

function signInCard({project, onSignIn, onProject, demo, onOpen}) {
  const err = h("div", {class: "form-error", role: "alert"});
  const email = Input({name: "email", type: "email", required: true, placeholder: "you@team.com", autocomplete: "username", inputmode: "email"});
  const password = Input({name: "password", type: "password", required: true, placeholder: "Password", autocomplete: "current-password"});
  const pwWrap = h("div", {class: "input-wrap"}, password, h("button", {type: "button", class: "input-affix", "aria-label": "Show password", "aria-pressed": "false", onClick: e => { const show = password.type === "password"; password.type = show ? "text" : "password"; e.currentTarget.setAttribute("aria-pressed", String(show)); e.currentTarget.setAttribute("aria-label", show ? "Hide password" : "Show password"); clear(e.currentTarget).append(icon(show ? "eyeOff" : "eye", {size: 14})); }}, icon("eye", {size: 14})));
  const submit = Button({label: "Sign in", variant: "primary", size: "lg", type: "submit", block: true});
  const form = h("form", {class: "form", onSubmit: async ev => {
    ev.preventDefault(); err.textContent = ""; submit.setBusy(true);
    try { await onSignIn({email: email.value.trim(), password: password.value}); }
    catch (e) { err.textContent = (e.message || "Something went wrong.") + (e.hint ? " " + e.hint : ""); submit.setBusy(false); email.focus(); }
  }});
  const host = (() => { try { return new URL(project.url).host; } catch { return project.url; } })();
  form.append(Field({label: "Email", control: email}), Field({label: "Password", control: pwWrap}), err, submit,
    demo ? Button({label: "Open demo instead", variant: "ghost", onClick: onOpen, block: true}) : null,
    h("details", {class: "disclosure"}, h("summary", {}, icon("chevronRight", {size: 14}), "Use a different project"),
      h("p", {class: "hint"}, "Connected to ", h("span", {class: "mono"}, host), ". Enter another Supabase project to use it on this device instead."),
      projectForm(onProject, project)));
  return Card({class: "signin", title: "Sign in", subtitle: "Use the email and password your team set up in Supabase", body: form});
}

function projectForm(onSubmit, prefill) {
  const err = h("div", {class: "form-error", role: "alert"});
  const url = Input({name: "url", type: "url", required: true, placeholder: "https://xxxx.supabase.co", autocomplete: "off", value: prefill.url || ""});
  const key = Input({name: "key", class: "input mono", required: true, placeholder: "sb_publishable_... or eyJhbGciOi...", autocomplete: "off", value: prefill.key || ""});
  const btn = Button({label: "Use this project", variant: "secondary", onClick: async () => {
    err.textContent = ""; btn.setBusy(true);
    try { await onSubmit({url: url.value.trim(), key: key.value.trim()}); }
    catch (e) { err.textContent = (e.message || "Something went wrong.") + (e.hint ? " " + e.hint : ""); }
    finally { btn.setBusy(false); }
  }});
  return h("div", {class: "form", style: {gap: "12px"}},
    h("p", {class: "hint"}, "Both values are on the Supabase dashboard under Project Settings, API. They are kept on this device only."),
    Field({label: "Project URL", control: url}), Field({label: "Publishable key", control: key}), err, btn,
    h("details", {class: "disclosure"}, h("summary", {}, icon("chevronRight", {size: 14}), "Need a project? Steps"),
      h("ol", {}, h("li", {}, "Create a free project at supabase.com."),
        h("li", {}, "Open the SQL editor and run ", h("code", {}, "supabase/schema.sql"), " from the repository."),
        h("li", {}, "Add your team in Authentication, Users (email and password)."),
        h("li", {}, "Add the project URL and service key as GitHub secrets ", h("code", {}, "SUPABASE_URL"), " and ", h("code", {}, "SUPABASE_SERVICE_KEY"), "."),
        h("li", {}, h("a", {href: README, target: "_blank", rel: "noopener"}, "Full guide in the README")))));
}
