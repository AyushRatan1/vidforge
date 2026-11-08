# VidForge

Trend-to-video studio. Claude finds what's hot, researches it with sources, writes and directs the episode, and
reviews its own frames. A free CPU engine renders the video with voice, music and karaoke captions in Hindi or
English, Spanish, French, Italian or Portuguese. It saves every video to a library and posts to YouTube
Shorts and Instagram Reels with platform-safe captions and hashtags.

```
Trends (Google Trends, Google News, YouTube trending, niche searches, NASA APOD)
  -> Scout (Claude)                     ranked, risk-checked ideas per channel
  -> Research (Claude + web search)     fact sheet with source links
  -> Writer/Director (Claude)           script + animated scene spec (JSON)
  -> Stills -> QA (Claude vision)       unreadable text, wrong facts, weak hooks; auto-fixes once
  -> Render (free, CPU)                 Skia vector animation + Kokoro TTS + procedural music + FFmpeg
  -> Review in dashboard -> Publish     YouTube Data API, Instagram API, or schedule
```

One engine runs many channels: e.g. *Space Is Weird* (English, international), *Aasmaan Ki Baatein* (Hindi space),
a kids learning channel. Each channel has its own niche, language, voice, mascot and accounts.

## Quick start (local)

```bash
pip install -r requirements.txt     # Python 3.10+, and ffmpeg on PATH
python run.py setup                 # free voice model (~350 MB) and fonts
python run.py serve                 # http://127.0.0.1:8000
```

1. **Settings**: paste your Anthropic API key (or set `ANTHROPIC_API_KEY`). Pick a model per role. The writer
   defaults to Opus 5.5; switch it to Fable 5.1 for the deepest scripts. Add a free YouTube Data API key for trends.
2. **Channels**: one per niche and language.
3. **Trends**: *Scout trends*, pick an idea, *Make video*. Or type your own topic.
4. **Studio**: watch it render, check the fact sheet and QA notes, ask Claude for changes in plain words, publish.

Render the examples without any keys:

```bash
python run.py render examples/space_is_weird_01_voyager.json   # English
python run.py render examples/leonids_hi.json                  # Hindi
python run.py render examples/kids_counting_hi.json --preview  # half resolution, faster
```

## Live end-to-end test (uses your Claude credits)

```bash
ANTHROPIC_API_KEY=sk-ant-... python run.py e2e --language en            # scouts real trends itself
ANTHROPIC_API_KEY=sk-ant-... python run.py e2e --language hi --topic "NavIC vs GPS"
```

It prints every stage (trends, picked idea, sourced facts, scene count, QA score and issues, render time,
tokens and approximate cost) and saves `idea.json`, `facts.json`, `spec.json`, `qa.json`, `final.mp4` under
`data/out/e2e_*`. Expect a few minutes of Claude time plus about 3x real time to render on 2 cores.

## The free video engine

No GPU and no paid video API: Claude writes a scene spec (grammar in `agents/scene_guide.py`) and the engine
draws every frame.

- Backgrounds: space (stars, nebulae, meteors), sky (day/sunset/night), sunburst, paper, tech grid, underwater, images.
- Elements: shaped Hindi/English text (Devanagari renders correctly), animated counters (Indian or western
  grouping), colour emoji, 12 planet/moon/sun styles plus black hole and neutron star with pulsar beams, 11 mascot
  species with blinking and lip-sync, props (rocket, comet, Voyager probe, golden record, satellite, diya...),
  constellations, particles (confetti, meteors, sideways rain streaks...), arbitrary SVG.
- Motion: entrances, behaviours, keyframes, camera moves, transitions; `at_word` lands a visual on a spoken word.
- Audio: Kokoro TTS on CPU (Hindi hm_omega, hm_psi, hf_alpha, hf_beta; English af_heart, am_michael, bf_emma...),
  royalty-free procedural music in 8 moods (incl. `indian`, `devotional`), ducking, sound effects, -14 LUFS.
- Scenes are cached by content hash, so a revision only re-renders the scenes that changed.
- Real footage: stock clips from Pixabay (and Pexels if you have a key) play under the drawn layer.

### 3D "how it was built" videos (format `3d_build`)

Low-poly 3D dioramas that build themselves, like the cutaway architecture reels: the ground is cut open in
cross-section, a trench is dug, stone walls rise course by course, flights of steps drop in, pillared halls appear and
water fills the bottom while the camera glides through. Claude writes a `world3d` block (terrain, digs, objects, build
timings tied to the narration, camera path); `engine/world3d.py` renders it with three.js in headless Chrome (software
WebGL, no GPU) and the 2D engine adds voice, captions and labels on top.

- Kit: terrain with animated digs, rocky hills and cliffs (with a road winding up), walls with merlons, bastions, gates,
  palaces with jharokha balconies, tombs, minarets, stairs, ramps, pillars, pavilions, temple spires, arches, domes,
  water, boats, sledges, cut blocks, flags, wells, ladders, houses, towns, trees, grass, rocks and villagers (dig, pull,
  walk, carry, climb).
- Macros: `stepwell`, `pyramid`, `fort` and `temple` expand into the kit with build phases tied to scenes, and register
  anchors (`fort.gate`, `pyramid.top`, ...) that camera shots aim at: `{"shot": "medium", "target": "fort.gate",
  "angle": 30}` is framed automatically for 9:16 (subject in the upper middle, caption band clear).
- Styles: desert, golden, green, overcast, night.
- Try it: `python run.py render examples/built_rani_ki_vav.json` (Rani ki Vav), `examples/built_great_pyramid.json` or
  `examples/built_mehrangarh_fort.json` (each about 50 to 55 s). Use `stills` instead of `render` for QA frames only.
- Speed: about 0.25 to 0.5 s per frame on a 4-core runner at the default `VIDFORGE_3D_SCALE=0.75` (rendered at 75 percent
  size, upscaled to 1080x1920), so a 50 s Short adds roughly 6 to 12 minutes to a run.
- Pick it in Create (Format: 3D build) or let the scout choose it for history, architecture, travel, mythology and
  tech channels.

## Hosting

The app needs a long-running process (renders take minutes), ffmpeg and a disk. Serverless platforms
(Vercel, Lambda) don't fit. Pick one:

| Option | Cost | Good for |
|---|---|---|
| Your laptop/desktop + `python run.py serve` | free | getting started; autopilot runs only while it's on |
| Laptop + Cloudflare Tunnel (`cloudflared tunnel --url http://127.0.0.1:8000`) | free | reach the dashboard from your phone |
| Small VPS with Docker Compose (below) | a few dollars a month | 24/7 autopilot, recommended |
| Railway / Render / Fly.io with a persistent volume | similar | if you prefer a PaaS; set the env vars from `.env.example` |

Rendering speed scales with CPU cores: 2 vCPU renders about 3x real time (a 60 s Short in ~3 min). Use x86.

**VPS in 6 steps (Ubuntu, any provider):**

```bash
# 1. on the server
curl -fsSL https://get.docker.com | sh
git clone https://github.com/AyushRatan1/vidforge.git && cd vidforge
cp .env.example .env && nano .env        # set VIDFORGE_PASSWORD, PUBLIC_URL, DOMAIN, keys
# 2. point your domain's DNS A record at the server IP
# 3. start (Caddy gets HTTPS certificates automatically)
docker compose up -d --build
# 4. open https://your-domain, log in with VIDFORGE_USER / VIDFORGE_PASSWORD
# 5. Google Cloud OAuth client: add redirect URI  https://your-domain/oauth/youtube/callback
# 6. back up the ./data folder (database, encrypted keys, videos)
```

Security: the dashboard refuses to listen publicly without `VIDFORGE_PASSWORD`, keys are encrypted at rest
in `data/`, and `.env` / `data/` are git-ignored.

## Web UI on GitHub Pages, team data in Supabase (no server needed)

`ui/` is a static dark-mode studio at `https://<user>.github.io/vidforge/`. GitHub's runners make and post the
videos; a free Supabase project (Postgres) holds everything the team shares: API keys, every video with its
sources and review notes, daily stats, the autopilot plan and live job progress. Team members sign in with
email and password; the workflows use the service key.

- **Create**: topic (or leave empty for a trending one), narration language, channel, format, writer model, voice,
  music, aspect, length, handle, extra hashtags and notes. Every choice has a *Custom* option for your own value.
  Turn on *Post when it's ready* to publish to YouTube and Instagram as soon as the render passes review.
- **Library**: every video is kept forever as a GitHub Release (`video-<id>`) with the MP4, thumbnail, script,
  fact sheet with sources, review notes and ready-made captions, mirrored in the `videos` table. Search, filter
  to *Not posted yet*, edit the title, description and caption, then *Post now* or schedule.
- **Settings**: keys are saved once in the `settings` table (Claude, YouTube, Instagram, Pexels, model per role)
  and every workflow run loads them first. Repo secrets with the same names still work as a fallback.
- **Autopilot** and **Stats**: see below.

One-time setup (about 10 minutes):
1. Create a free project at [supabase.com](https://supabase.com). Copy the **Project URL** and the
   **service_role** key from *Project Settings -> API* (the service key never goes in the UI, only in GitHub).
2. In the Supabase dashboard open **SQL Editor -> New query**, paste the contents of `supabase/schema.sql`, Run.
   It creates the tables, row level security (signed-in team members only) and realtime for job progress.
3. Create the first team user: **Authentication -> Users -> Add user**, enter email and password, keep
   **Auto confirm user** on. Add more teammates the same way whenever you like.
4. In the GitHub repo add two **Actions secrets** (Settings -> Secrets and variables -> Actions):
   `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`. Nothing else is required.
5. Repo **Settings -> Pages -> Source: GitHub Actions**. The `pages` workflow deploys `ui/` on every push to `main`.
6. Open the Pages site, enter the Supabase URL and anon key when asked (Project Settings -> API, *anon public*),
   sign in with the user from step 3, open **Settings** and fill in the Anthropic key plus the YouTube and
   Instagram values (how to get them is under *Connecting accounts*). Done: the next run picks them up.

Each run spends Claude credits (the Library shows the cost of every video) and takes 8 to 12 minutes; runs queue
one at a time. The repo is public, so the library releases are public too. The database is private: only
signed-in users and the service key can read it. Without the two Supabase secrets everything still works the old
way (per-key GitHub secrets, no shared library data).

### Autopilot

The `draft-video` workflow also runs every hour (at :30) and asks the `autopilot` row whether a video is due:

- **Videos per day** and **Post hours (IST)**: with `videos_per_day = 3` and `post_hours = {9, 13, 18}`, the first
  video of the day is made once the clock passes 09:00 IST, the second after 13:00, the third after 18:00. Each
  run checks how many autopilot videos were made today (IST) and makes at most one.
- **Topics queue**: a list of `{text, language, niche, status}`. The first `queued` topic is used next and marked
  `running` with the video id, then `done` when the video is packaged. Leave language or niche empty to inherit.
- **Trending fill**: when the queue is empty, the scout picks a trending topic; language and niche rotate over
  the configured lists (first video `en`/`space`, second `hi`/`tech`, and so on).
- **Platforms** and **privacy** decide where the finished video is posted; **options** holds extra defaults
  (`voice`, `music`, `length`, `hashtags`, `notes`, `writer`).
- **Review gate**: a video is only auto-posted when Claude's frame review passes. A failing video (score below
  the pass mark) stays in the Library marked *Needs review*; post it from there after a look, or set
  `publish.force = true` in the options to post regardless.
- **Real footage**: for real-world channels (animals, food, travel, mythology, tech, stories, news, custom) the
  writer must give at least 60 percent of scenes a stock-footage background; a second writer pass enforces it.

Every autopilot video gets the id `ap-<YYYYMMDD-HHMMSS>` as job id, video id and release tag suffix, and
`source = autopilot` on its row. Turn it off with the **enabled** switch; the hourly run then exits in seconds.
`python run.py autopilot` prints the decision locally.

### Daily stats

The `stats` workflow runs at 07:45 IST (`python run.py stats`) and writes one row per video, platform and day:
views, likes, comments, and where the APIs allow it shares, saves, reach and watch time. Channel totals
(subscribers or followers, lifetime views, video count) go to `channel_stats`. YouTube per-video numbers use the
Data API with the OAuth token (or a plain `YOUTUBE_API_KEY`); watch time and shares need the
`yt-analytics.readonly` scope, which `python run.py youtube-auth` now requests. Instagram uses the insights
endpoint of the Instagram API with Instagram Login. One platform failing never blocks the other.

### Hashtags and captions

A metadata step writes platform-specific copy for every video, then hard rules are applied whatever the model says:

| | YouTube Shorts | Instagram Reels |
|---|---|---|
| Hashtags | 5 max in the description (the first 3 can show above the title), plus `#Shorts` in the title | 5 max (Instagram's cap since late 2025) |
| Text | title up to 100 chars, description up to 5,000, tags up to 480 chars | caption up to 2,200 chars |
| Always | your extra hashtags first, then the channel's brand tag, then topic tags; AI-assisted line | same |

Over-tagging gets Shorts ignored, so fewer, specific tags win.

### Faster machines

Public repos get GitHub's standard 4-core runners free and unlimited, and the renderer uses every core. To try
another runner, set it in **Settings -> Machine** (stored as the `RUNNER` repo variable). Blacksmith has 3,000
free minutes a month but only works for GitHub organizations, not personal repos: move the repo into a free
org first, install Blacksmith there, then pick a label such as `blacksmith-4vcpu-ubuntu-2404`.

## Connecting accounts

**YouTube** (for the GitHub Pages UI)
1. Google Cloud Console: new project, enable *YouTube Data API v3*, OAuth consent screen (add yourself as a test
   user), then create an OAuth client of type **Desktop app** and download its JSON.
2. On your computer: `python run.py youtube-auth client_secret.json`. Sign in with the channel's Google account.
   It prints `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET` and `YOUTUBE_REFRESH_TOKEN`; paste them in **Settings** on the Pages site (or save them as repo secrets).
3. Until the project passes Google's **YouTube API compliance audit**, every API upload is locked to private.
   Submit the audit on day one. Default quota: 10,000 units/day, 1,600 per upload, so about 6 uploads/day.
   Publish the consent screen to *In production* or the refresh token expires after 7 days.

For the local dashboard instead, create a *Web application* client with redirect URI
`http://127.0.0.1:8000/oauth/youtube/callback` (or `https://your-domain/...`), upload it in Settings and click
*Connect YouTube* on each channel.

**Instagram Reels**
1. Make the account Professional (Creator or Business).
2. Create a Meta app with *Instagram API with Instagram Login*, add the account as a tester, grant
   `instagram_business_basic` + `instagram_business_content_publish`, generate a long-lived token.
3. Paste the token in **Settings** on the Pages site (the account ID is looked up for you). Tokens last about 60 days.
   Limit: 50 API posts per 24 hours.

**From the command line**: `python run.py publish-video data/out/<id> --youtube --instagram --privacy public`
posts a finished folder using the same environment variables.

## Staying monetisable

- YouTube demonetises mass-produced, repetitive, template content ("inauthentic content"). The defaults push the
  other way: original mascot per channel, sourced facts, varied formats, QA, and your approval before publishing.
- Uploads set `containsSyntheticMedia: true` and add an AI-assisted line to the description (also required for
  India under the Feb 2026 IT Rules amendment).
- Kids channels: audience *kids* sets `selfDeclaredMadeForKids: true`; original songs and characters only.
- From 1 Feb 2027, new YPP applicants need 8,000 watch hours or 20M Shorts views in 90 days. Pair Shorts with
  long-form (`"aspect": "16:9"`) for watch hours. International English audiences pay far higher RPM than Indian ones.

## Layout

```
agents/   llm (Claude client + model routing), scout, research, writer, qa, metadata, formats, scene_guide
engine/   pipeline (spec -> mp4), renderer (Skia compositor), draw (all visuals), anim, audio, fonts, validate
trends/   free trend feeds
publish/  youtube.py, instagram.py
app/      FastAPI server, SQLite (secrets encrypted), job queue, scheduler, dashboard (static/index.html)
tools/    e2e.py (staged end-to-end flow), publish.py (post a folder), library.py (release notes),
          store.py (Supabase client), autopilot.py (hourly decision), stats.py (daily YouTube/Instagram pull)
ui/       GitHub Pages studio (index.html, app.js, styles.css, seal.js, vendor/)
.github/  draft-video (make, also hourly autopilot), publish-video (post from library), stats (daily), pages, ci
supabase/ schema.sql (tables, RLS, realtime)
examples/ Space Is Weird #1-3 (English), Leonids (Hindi), kids counting (Hindi), build_space_is_weird.py
tests/    offline tests (engine + agents against a fake Claude)
```
