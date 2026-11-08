// Start page: shown before sign-in (and at #/). Hero with a phone preview, sample metrics, how it works, sign-in card.
import {h, clear, Button, Card, StatTile, Field, Input, Pill, PlatformMark, icon} from "../components.js";
import {fmt} from "../format.js";

const README = "https://github.com/ayushratan1/vidforge#readme";
const STEPS = [
  ["Find trend", "The scout reads what is rising on YouTube and Instagram in your channels and languages.", "compass"],
  ["Research", "Claude gathers the facts and keeps the sources so every claim can be checked.", "bookOpen"],
  ["Write and direct", "A script, a shot list and captions, written for a 45 second vertical video.", "penLine"],
  ["Render", "Voice, music, drawn frames and real footage are rendered on a GitHub runner.", "clapperboard"],
  ["Post", "The review passes, then it posts to YouTube Shorts and Instagram Reels at your hours.", "send"],
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
  root.append(h("div", {class: "aurora", "aria-hidden": "true"}));

  // nav
  const nav = h("nav", {class: "start-nav", "aria-label": "Start"},
    brand(demo),
    h("div", {class: "actions"},
      Button({label: "How it works", variant: "ghost", href: "#how"}),
      Button({label: "Guide", variant: "secondary", icon: "github", href: README, target: "_blank"}),
      signedIn ? Button({label: demo ? "Open demo" : "Open dashboard", variant: "primary", icon: "arrowRight", onClick: onOpen}) : Button({label: "Sign in", variant: "primary", onClick: () => scrollTo("#signin")})));

  // hero
  const phone = phoneFrame(sample);
  const hero = h("section", {class: "hero"},
    h("div", {class: "hero-copy stagger"},
      h("span", {class: "eyebrow"}, h("span", {class: "pill-dot"}), demo ? "Demo with sample data" : "Runs on GitHub Actions and Supabase"),
      h("h1", {}, "Short videos that make themselves, ", h("span", {class: "gradient-text"}, "on autopilot"), "."),
      h("p", {class: "hero-sub"}, "VidForge finds what is trending in your niche, researches it, writes and directs a vertical video, renders it and posts to YouTube Shorts and Instagram Reels at the hours you choose. You review the numbers."),
      h("div", {class: "hero-cta"},
        signedIn ? Button({label: demo ? "Open demo" : "Open dashboard", variant: "primary", size: "lg", icon: "arrowRight", onClick: onOpen})
          : Button({label: "Sign in", variant: "primary", size: "lg", icon: "arrowRight", onClick: () => scrollTo("#signin")}),
        demo && !signedIn ? Button({label: "Open demo", variant: "secondary", size: "lg", icon: "play", onClick: onOpen}) : Button({label: "See how it works", variant: "secondary", size: "lg", href: "#how"})),
      h("p", {class: "hero-note"}, "About $0.50 of Claude credits per video. Free GitHub runners for public repositories.")),
    h("div", {class: "hero-stage"}, phone,
      h("div", {class: "phone-float phone-float-a glass"}, icon("eye", {size: 18}), h("div", {}, h("div", {class: "micro"}, "Views, 30 days"), h("strong", {class: "num"}, fmt.compact(sample.views)))),
      h("div", {class: "phone-float phone-float-b glass"}, icon("zap", {size: 18}), h("div", {}, h("div", {class: "micro"}, "Next post"), h("strong", {}, "Today 6 pm IST")))));

  // metrics
  const metrics = h("section", {class: "section", "aria-label": "Sample metrics"},
    h("div", {class: "metrics stagger"},
      StatTile({label: "Views, 30 days", value: fmt.compact(sample.views), icon: "eye", sample: true, hint: "YouTube and Instagram"}),
      StatTile({label: "Videos posted", value: String(sample.posted), icon: "film", sample: true, hint: "Made and posted by the worker"}),
      StatTile({label: "Followers", value: fmt.compact(sample.followers), icon: "users", sample: true, hint: "Across both platforms"}),
      StatTile({label: "Cost per video", value: fmt.usd(sample.usd), icon: "dollar", sample: true, hint: "Claude credits, average"})));

  // how it works
  const how = h("section", {class: "section", id: "how"},
    h("div", {class: "section-head"}, h("div", {}, h("h2", {}, "How it works"), h("p", {}, "One run on GitHub takes 8 to 12 minutes. Each step lights up on the Create page while it happens.")),
      Pill("Five steps, no editing", "neutral")),
    h("div", {class: "rail-steps stagger"}, ...STEPS.map(([t, d, ic], i) => h("div", {class: "rail-step glass"},
      h("div", {class: "cluster-between"}, h("span", {class: "rail-step-n"}, String(i + 1)), h("span", {class: "stat-icon"}, icon(ic, {size: 18}))),
      h("h3", {}, t), h("p", {}, d), h("span", {class: "rail-arrow"}, icon("chevronRight", {size: 18}))))));

  // sign in
  const signin = h("section", {class: "section", id: "signin"},
    h("div", {class: "signin-wrap"},
      h("div", {class: "signin-copy"},
        h("h2", {}, signedIn ? "You are signed in" : "Sign in to your project"),
        h("p", {}, signedIn ? "Open the dashboard to see today's numbers, the live run and the queue." : "Use the email and password your team set up in Supabase. You stay signed in on this device."),
        h("ul", {},
          h("li", {}, icon("checkCircle", {size: 18}), "Keys stay in your private Supabase project, read by the worker at run time."),
          h("li", {}, icon("checkCircle", {size: 18}), "Every video is kept as a GitHub Release with its MP4, captions and sources."),
          h("li", {}, icon("checkCircle", {size: 18}), "Stats refresh daily at 07:45 IST."))),
      signedIn ? Card({class: "signin", body: h("div", {class: "stack"}, h("p", {class: "secondary"}, "Signed in on this device."), Button({label: demo ? "Open demo" : "Open dashboard", variant: "primary", size: "lg", icon: "arrowRight", onClick: onOpen, block: true}))})
        : signInCard({project, onSignIn, onProject, demo, onOpen})));

  root.append(nav, hero, metrics, how, signin, h("footer", {class: "start-foot"}, "VidForge. Built for Indian creators, works anywhere. ", h("a", {href: README, target: "_blank", rel: "noopener"}, "Setup guide")));
  return root;
}

function scrollTo(sel) { document.querySelector(sel)?.scrollIntoView({behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start"}); setTimeout(() => document.querySelector(sel + " input")?.focus({preventScroll: true}), 450); }

export function brand(demo) {
  return h("a", {class: "brand", href: "#/", "aria-label": "VidForge start page"}, h("span", {class: "brand-mark"}, icon("zap", {size: 18})),
    h("span", {class: "brand-text"}, h("span", {class: "brand-name"}, "VidForge"), h("span", {class: "brand-sub"}, demo ? "Demo with sample data" : "Short videos on autopilot")));
}

function phoneFrame(sample) {
  const screen = h("div", {class: "phone-screen"});
  if (sample.video) {
    const v = h("video", {src: sample.video, poster: sample.thumb || null, muted: true, autoplay: true, loop: true, playsinline: true, "aria-label": "Sample video: " + sample.title});
    v.muted = true;
    screen.append(v);
  } else if (sample.thumb) screen.append(h("img", {src: sample.thumb, alt: "Sample video thumbnail"}));
  else screen.append(h("div", {class: "phone-idle"}, icon("smartphone", {size: 28}), h("strong", {}, sample.title), "A sample video plays here once the demo files are served."));
  screen.append(h("div", {class: "phone-caption"}, icon("play", {size: 14}), h("span", {}, sample.title.length > 34 ? sample.title.slice(0, 33) + "…" : sample.title), h("span", {class: "marks"}, PlatformMark("youtube", "https://youtube.com", {size: 12}), PlatformMark("instagram", "https://instagram.com", {size: 12}))));
  return h("div", {class: "phone", role: "figure", "aria-label": "Phone showing a sample video"}, h("div", {class: "phone-notch"}), screen);
}

function signInCard({project, onSignIn, onProject, demo, onOpen}) {
  const err = h("div", {class: "form-error", role: "alert"});
  const email = Input({name: "email", type: "email", required: true, placeholder: "you@team.com", autocomplete: "username", inputmode: "email"});
  const password = Input({name: "password", type: "password", required: true, placeholder: "Password", autocomplete: "current-password"});
  const pwWrap = h("div", {class: "input-wrap"}, password, h("button", {type: "button", class: "input-affix", "aria-label": "Show password", "aria-pressed": "false", onClick: e => { const show = password.type === "password"; password.type = show ? "text" : "password"; e.currentTarget.setAttribute("aria-pressed", String(show)); e.currentTarget.setAttribute("aria-label", show ? "Hide password" : "Show password"); clear(e.currentTarget).append(icon(show ? "eyeOff" : "eye", {size: 18})); }}, icon("eye", {size: 18})));
  const submit = Button({label: "Sign in", variant: "primary", size: "lg", type: "submit", block: true});
  const form = h("form", {class: "form", onSubmit: async ev => {
    ev.preventDefault(); err.textContent = ""; submit.setBusy(true);
    try { await onSignIn({email: email.value.trim(), password: password.value}); }
    catch (e) { err.textContent = (e.message || "Something went wrong.") + (e.hint ? " " + e.hint : ""); submit.setBusy(false); email.focus(); }
  }});
  const host = (() => { try { return new URL(project.url).host; } catch { return project.url; } })();
  form.append(Field({label: "Email", control: email}), Field({label: "Password", control: pwWrap}), err, submit,
    demo ? Button({label: "Open demo instead", variant: "ghost", onClick: onOpen, block: true}) : null,
    h("details", {class: "disclosure"}, h("summary", {}, icon("chevronRight", {size: 16}), "Use a different project"),
      h("p", {class: "hint"}, "Connected to ", h("span", {class: "mono"}, host), ". Enter another Supabase project to use it on this device instead."),
      projectForm(onProject, project)));
  return Card({class: "signin", title: "Sign in", subtitle: "Remembers this device", body: form});
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
    h("details", {class: "disclosure"}, h("summary", {}, icon("chevronRight", {size: 16}), "Need a project? Steps"),
      h("ol", {}, h("li", {}, "Create a free project at supabase.com."),
        h("li", {}, "Open the SQL editor and run ", h("code", {}, "supabase/schema.sql"), " from the repository."),
        h("li", {}, "Add your team in Authentication, Users (email and password)."),
        h("li", {}, "Add the project URL and service key as GitHub secrets ", h("code", {}, "SUPABASE_URL"), " and ", h("code", {}, "SUPABASE_SERVICE_KEY"), "."),
        h("li", {}, h("a", {href: README, target: "_blank", rel: "noopener"}, "Full guide in the README")))));
}
