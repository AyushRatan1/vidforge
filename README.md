# VidForge

Trend-to-video studio. Claude finds what's hot, researches it with sources, writes and directs the episode, and
reviews its own frames. A free CPU engine renders the video with voice, music and karaoke captions in Hindi or
English. You approve, and it posts to YouTube and Instagram Reels.

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

**GitHub Actions drafts:** `.github/workflows/daily-draft.yml` can run the end-to-end flow on GitHub's runners and
attach the video as a downloadable artifact (add `ANTHROPIC_API_KEY` as a repo secret). It's manual-run only by
default; uncomment the schedule to make it daily. Nothing is published from Actions.

## Connecting accounts

**YouTube**
1. Google Cloud Console: new project, enable *YouTube Data API v3*, create an OAuth client (*Web application*)
   with redirect URI `http://127.0.0.1:8000/oauth/youtube/callback` (local) or `https://your-domain/oauth/youtube/callback`.
2. Upload the client JSON in Settings, then *Connect YouTube* on each channel.
3. Until the project passes Google's **YouTube API compliance audit**, every API upload is locked to private.
   Submit the audit on day one. Default quota: 10,000 units/day, 1,600 per upload, so about 6 uploads/day.

**Instagram Reels**
1. Make the account Professional (Creator or Business).
2. Create a Meta app with *Instagram API with Instagram Login*, add the account as a tester, grant
   `instagram_business_basic` + `instagram_business_content_publish`, generate a long-lived token.
3. Paste the token into the channel. Tokens last about 60 days. Limit: 50 API posts per 24 hours.

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
agents/   llm (Claude client + model routing), scout, research, writer, qa, formats, scene_guide
engine/   pipeline (spec -> mp4), renderer (Skia compositor), draw (all visuals), anim, audio, fonts, validate
trends/   free trend feeds
publish/  youtube.py, instagram.py
app/      FastAPI server, SQLite (secrets encrypted), job queue, scheduler, dashboard (static/index.html)
tools/    e2e.py live end-to-end test
examples/ Space Is Weird #1-3 (English), Leonids (Hindi), kids counting (Hindi), build_space_is_weird.py
tests/    offline tests (engine + agents against a fake Claude)
```
