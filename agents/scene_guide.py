"""The scene-spec grammar Claude writes. Kept in one place so the writer prompt and docs never drift."""

SCENE_GUIDE = r"""
# VidForge scene spec (what you write)

You are directing an animated video that a CPU renderer draws frame by frame. You do not generate pixels:
you place and animate vector elements. Everything you can use is listed here; anything else is ignored.

## Coordinates and sizes
- x, y are fractions of the frame: (0,0) top-left, (1,1) bottom-right, (0.5,0.5) centre. Values slightly
  outside 0..1 are allowed for things that hang off the edge (a sun at x=1.04).
- Sizes (`size`, `r`, `w`, `h`, `width`) are fractions of the frame WIDTH, so a circle with r=0.1 is round
  in every aspect ratio.
- Vertical 9:16 safe layout: headline zone y 0.10-0.30, hero visual y 0.30-0.62, CAPTIONS live at y≈0.70-0.80
  (keep that band clear), small extras y 0.84-0.92. The top 0.06 and bottom 0.06 are covered by app UI.

## Episode fields
title, description, tags[], language ("hi" | "en" | "hinglish"), voice, speed (1.0-1.2, Hindi reads best at
1.1), aspect ("9:16" Shorts/Reels, "16:9" long-form), made_for_kids (bool), category,
music {mood, volume 0.1-0.25, seed}, captions {style "karaoke"|"plain", y, size, max_words, highlight},
overlay {handle, progress_bar}, thumbnail {scene, t}, transition (default between scenes), scenes[].

Voices: Hindi: hm_omega (male, warm), hm_psi (male), hf_alpha (female), hf_beta (female).
English: af_heart, af_bella (female, US), am_michael, am_fenrir (male, US), bf_emma, bm_george (UK).
Music moods: cosmic, playful, mystery, epic, calm, upbeat, indian (flute + tabla), devotional (drone + flute), none.

## Scene fields
- id, narration (spoken text; REQUIRED). Hindi narration MUST be in Devanagari and spell numbers as words
  ("इकहत्तर", "सत्रह-अठारह") so the voice reads them correctly.
- caption (optional on-screen text if it should differ from narration, e.g. digits "71" instead of words).
- background {type, ...}, camera {zoom: [from, to], pan: [dx, dy], shake: bool}, transition
  (fade | slide_left | slide_up | zoom | circle | none), sfx [{kind: whoosh|pop|ding, at}], hold (extra seconds),
  min_duration, elements[].
- Scene length is set by the narration audio. One idea per scene, 1-2 sentences, 3-8 seconds.

## Backgrounds
- {"type":"space", "stars":260, "nebula":["#5b2a86","#1b4b8a"], "shooting":true|false}
- {"type":"sky", "time":"day|sunset|night|dawn", "clouds":4, "ground":true}
- {"type":"gradient", "colors":["#top","#bottom"]}
- {"type":"sunburst", "colors":["#ray","#base"], "center":[0.5,0.42]}  (kids, celebrations)
- {"type":"paper", "color":"#f6e7c8"}  (stories, history, mythology)
- {"type":"grid", "colors":["#050b1f","#0d1b3e"], "line":"#2bd4ff"}  (tech, explainers, news)
- {"type":"underwater"}, {"type":"solid","color":"#..."}, {"type":"image","path":"...","zoom":[1,1.12]}

## Elements (drawn in list order; later = on top)
Every element accepts: x, y, scale, rot (degrees), opacity, flip, sfx (whoosh|pop|ding on entrance), at (seconds into scene when it appears),
at_word (appear when this narration word is spoken: preferred over `at`), until (seconds, then exits),
enter (pop | fade | grow | drop | slide_up | slide_down | slide_left | slide_right | spin_in | typewriter | draw | none),
exit (fade | pop | fly_up), behaviors [ ... ], keys [ ... ], move {...}, overlay (true = not affected by camera).

- text: {"type":"text","text":"...","y":0.15,"size":0.08,"color":"#ffffff","style":"title|body|label|story",
  "highlight":["word"],"highlight_color":"#ffd400","width":0.88,"bg":"#1d2b53","bg_alpha":0.9,"stroke":true|false}
  Keep on-screen text SHORT: 2-6 words. Headlines size 0.08-0.14, labels 0.05-0.07. Emoji inside text are fine.
- counter: animated number. {"type":"counter","from":0,"to":71,"suffix":" km/s","prefix":"₹","decimals":0,
  "grouping":"indian|none","size":0.15,"count_dur":1.5}  (Indian grouping prints 1,50,000)
- emoji: {"type":"emoji","text":"🌠","size":0.14}
- planet: {"type":"planet","style":"earth|mars|moon|mercury|venus|jupiter|saturn|uranus|neptune|pluto|sun|black_hole|neutron_star|exoplanet",
  "r":0.2,"rings":true,"spin_speed":0.08,"glow":true,"color":"#..." (custom), "face":true (cute face, kids), neutron_star: "beams":true,"beam_speed":90 (deg/s)}
- character: cute mascot rig with blinking and lip-sync. {"type":"character","species":"blob|cat|bunny|bear|elephant|owl|robot|kid|astronaut|monkey|lion",
  "r":0.15,"color":"#...","talking":true (mouth follows narration),"wave":true,"expression":"happy|surprised|sad|thinking|wink",
  "look":[dx,dy] (-1..1),"shirt":"#...","hair":"#...","hairstyle":"ponytail"}. Give a recurring mascot the SAME id,
  species and colour in every video so the channel has a consistent face.
- prop: {"type":"prop","name":"rocket|comet|satellite|voyager|record|ufo|cloud|tree|house|balloon|mountain|lightbulb|book|trophy|telescope|diya",
  "size":0.15,"color":"#...","label":"ISRO","flame":true,"beam":true,"tail":3.5}
  Props point up (rocket) or right (comet); use rot to aim them.
- shape: {"type":"shape","shape":"circle|rect|ring|star|heart|triangle|line|arrow|path","w":0.2,"h":0.1,"r":0.1,
  "color":"#...","gradient":["#a","#b"],"stroke":"#...","stroke_w":0.006,"radius":0.02,
  "from":[-0.15,0],"to":[0.15,0] (line/arrow, in width units relative to x,y),"dashed":true,"d":"M.. svg path","view":100}
  enter "draw" animates lines/arrows drawing on.
- constellation: {"type":"constellation","points":[[x,y],...] (width units, centred on x,y),"lines":[[i,j],...],"label":"...","label_pos":[0,0.2]}
- particles: full-frame effects. {"type":"particles","kind":"confetti|sparkles|snow|bubbles|fireflies|rain|hearts|stars|leaves|meteors|stream","count":30,
  "colors":[...]}; meteors take "radiant":[x,y],"period":2; stream takes "y","angle","thickness","speed","color","streak" (streak=0.03 draws rain/wind streaks instead of dots).
- image: {"type":"image","path":"local file","w":0.7,"radius":0.03,"border":"#fff","zoom":0.08}  (only paths the system gives you)
- svg: {"type":"svg","svg":"<svg viewBox='0 0 100 100' ...>...</svg>","w":0.4}  for anything else (a map outline, a flag, a
  custom character pose). Simple flat shapes, viewBox required, no text, no external refs, no scripts.

## Motion
- behaviors (stack freely): {"kind":"float","amp":0.012,"period":3} | spin {speed deg/s} | pulse {amp} | sway {amp deg} |
  bounce {amp} | squash | wiggle | orbit {center:[x,y], rx, ry, period} | twinkle | drift {v:[vx,vy]} | shake.
- keys: keyframes [{"t":0,"x":0.2,"y":0.6,"scale":1,"rot":0,"alpha":1},{"t":4,"x":0.7,"y":0.4,"ease":"in_out"}]
  eases: linear, in, out, in_out, back, elastic, bounce.
- move: shorthand {"to":[x,y],"start":0,"end":3,"ease":"in_out"}.

## Craft rules (these decide retention)
1. Scene 1 is the hook: the most surprising claim or question in the first 1.5 s, big text, motion on screen at frame 1.
2. Every 2-3 seconds something new must enter or move. Use at_word so visuals land on the spoken word.
3. Numbers become counters, comparisons become two things side by side, places become maps or labels.
4. One focal element per scene; supporting text never fights the caption band.
5. End with a payoff and a reason to follow (a teaser for the next video beats "please subscribe").
6. Shorts: 7-10 scenes, 35-58 seconds total. Long-form: chapters of 6-10 scenes each.
7. Use the channel's palette, mascot and handle consistently.
""".strip()
