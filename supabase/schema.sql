-- VidForge database. Run once in the Supabase SQL editor (Dashboard -> SQL -> New query -> paste -> Run).
-- Everything the team sees lives here: keys (settings), every video, daily stats, the autopilot plan and jobs.
-- GitHub Actions talks to it with the service-role key; the web UI with a signed-in team member (RLS below).

create extension if not exists pgcrypto;

-- One row per key. Values are plain text in a private table: only signed-in team members and the service key can read them.
create table if not exists settings (
  key text primary key,
  value text not null default '',
  updated_at timestamptz not null default now()
);

create table if not exists videos (
  id text primary key,                        -- request id, also the GitHub release tag suffix (video-<id>)
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  status text not null default 'queued',      -- queued | making | ready | posted | failed
  stage text,                                 -- current or last step name
  title text,
  topic text,
  language text,
  niche text,
  format text,
  aspect text,
  duration numeric,
  qa_score numeric,
  usd numeric,
  release_url text,
  video_url text,                             -- direct MP4 download (GitHub release asset)
  thumb_url text,
  options jsonb not null default '{}'::jsonb, -- the options the video was made with
  meta jsonb not null default '{}'::jsonb,    -- youtube {title, description, hashtags, tags}, instagram {caption, hashtags}
  sources jsonb not null default '[]'::jsonb,
  qa jsonb not null default '{}'::jsonb,
  youtube_id text,
  youtube_url text,
  instagram_id text,
  instagram_url text,
  published jsonb not null default '{}'::jsonb,
  run_id text,
  error text,
  source text not null default 'manual'       -- manual | autopilot
);
create index if not exists videos_created_idx on videos (created_at desc);

-- One snapshot per video, platform and day.
create table if not exists stats (
  video_id text not null references videos(id) on delete cascade,
  platform text not null,                     -- youtube | instagram
  day date not null,
  views bigint default 0,
  likes bigint default 0,
  comments bigint default 0,
  shares bigint default 0,
  saves bigint default 0,
  reach bigint default 0,
  watch_time_s bigint default 0,
  captured_at timestamptz not null default now(),
  primary key (video_id, platform, day)
);

-- Whole-channel snapshot per platform and day.
create table if not exists channel_stats (
  platform text not null,
  day date not null,
  followers bigint default 0,                 -- subscribers on YouTube
  views bigint default 0,                     -- lifetime views
  videos bigint default 0,
  captured_at timestamptz not null default now(),
  primary key (platform, day)
);

-- A single row (id = 1) describing what runs on its own.
create table if not exists autopilot (
  id int primary key default 1 check (id = 1),
  enabled boolean not null default false,
  videos_per_day int not null default 3,
  post_hours int[] not null default '{9,13,18,21}',   -- IST hours when a video may go out
  platforms jsonb not null default '{"youtube": true, "instagram": true}'::jsonb,
  languages text[] not null default '{en}',
  niches text[] not null default '{space}',
  topics jsonb not null default '[]'::jsonb,  -- [{"text": "...", "language": "hi", "niche": "stories", "status": "queued|done", "video_id": "..."}]
  trending_fill boolean not null default true,-- when the queue is empty, pick a trending topic
  privacy text not null default 'public',
  options jsonb not null default '{}'::jsonb, -- extra defaults: voice, music, length, hashtags, notes, writer
  last_run_at timestamptz,
  updated_at timestamptz not null default now()
);
insert into autopilot (id) values (1) on conflict do nothing;

-- Work started from the UI or by autopilot; the workflow updates it as it goes.
create table if not exists jobs (
  id text primary key,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  kind text not null default 'make',          -- make | publish | stats
  status text not null default 'queued',      -- queued | running | done | failed
  stage text,
  video_id text,
  options jsonb not null default '{}'::jsonb,
  run_id text,
  run_url text,
  error text
);
create index if not exists jobs_created_idx on jobs (created_at desc);

-- keep updated_at fresh
create or replace function touch_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end $$;
do $$ declare t text; begin
  for t in select unnest(array['settings','videos','autopilot','jobs']) loop
    execute format('drop trigger if exists touch_%1$s on %1$s; create trigger touch_%1$s before update on %1$s for each row execute function touch_updated_at();', t);
  end loop;
end $$;

-- Row level security: signed-in team members get everything, anonymous visitors nothing.
alter table settings enable row level security;
alter table videos enable row level security;
alter table stats enable row level security;
alter table channel_stats enable row level security;
alter table autopilot enable row level security;
alter table jobs enable row level security;
do $$ declare t text; begin
  for t in select unnest(array['settings','videos','stats','channel_stats','autopilot','jobs']) loop
    execute format('drop policy if exists team_all on %1$s; create policy team_all on %1$s for all to authenticated using (true) with check (true);', t);
  end loop;
end $$;

-- Live updates for the UI (job progress, new videos).
do $$ begin
  alter publication supabase_realtime add table jobs;
  alter publication supabase_realtime add table videos;
exception when duplicate_object then null; end $$;
