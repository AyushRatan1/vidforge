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
overlay {handle, progress_bar}, thumbnail {scene, t}, transition (default between scenes),
footage ("auto" | "off": allow real stock footage backgrounds), scenes[].

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
- {"type":"footage", "query":"cat playing", "dim":0.45, "blur":0, "tint":"#0b1030", "speed":1.0,
  "fallback":{"type":"space"}}  REAL stock video (Pexels/Pixabay, free to use) plays under your text, captions,
  counters and mascots. Use it for real-world subjects: animals, nature, cities, food, sports, people, history,
  mythology (temples, fire, mountains, ancient art), tech, festivals. `query` is 2-4 concrete VISUAL English words
  ("ganges aarti fire", "himalaya snow peaks", "cat playing"), never abstract ("success", "controversy") and never
  a copyrighted name (no film titles, no celebrities). Vary the query from scene to scene so clips differ. Keep text
  readable: dim 0.35-0.6 (a dark `tint` at that opacity sits over the video), blur 0-8 only when the clip is busy.
  `fallback` is the drawn background used when no clip is found. Astronomy stays on drawn `space` backgrounds.
  Episode field `footage`: "auto" (default) or "off" to disable footage for the whole video.

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

## 3D build worlds (format 3d_build: "how it was built" low-poly dioramas)
Add a top-level "world3d" and give scenes {"type":"world3d"} backgrounds (scenes without a background default to it).
The whole video is ONE continuous diorama; each scene shows its own slice of the timeline, so the build and the camera
flow across scenes while the 2D layer adds captions and labels. Keep 2D elements sparse: 0-2 per scene, mostly yellow
callout labels {"type":"text","text":"STEPWELL","bg":"#ffd54a","color":"#1c1a17","style":"label","stroke":false,"size":0.056,"y":0.2}.
Captions for this format: {"y":0.6,"size":0.084,"max_words":2,"highlight":"#ffd54a","uppercase":false}; spec "transition":"none".

Units are metres-ish; y is up, the ground surface is y=0, people are ~1.4 tall. The terrain block is cut open at its
front face (z = terrain.cut, facing the camera on +z), so anything dug up to that face is seen in cross-section with
coloured soil layers, like an architectural cutaway. Put the camera at +z looking towards -z.
world3d = {
  "style": "desert|golden|green|overcast|night",
  "terrain": {"width":44,"length":56,"cut":6,"strata":[["#d9bf8f",0.35],["#b98a5c",1.6],...] (optional),
              "digs":[{"x0":-1.2,"x1":1.2,"z0":3.4,"z1":6,"depth":5,"from":TIME,"to":TIME}]},   dig animates 0 -> depth
  "objects":[...], "camera":[{"at":TIME,"pos":[x,y,z],"look":[x,y,z],"fov":38,"ease":"inout|linear"}, ...]
}
TIME is seconds or a scene reference: {"scene":"dig","t":0.5} (fraction of that scene), {"scene":"dig","at":1.2},
or {"scene":"dig","word":"water","offset":0.2}. Prefer scene references so the build follows the narration.
Every object takes "pos":[x,y,z] (its base), "rot" (degrees around y), "build":{"op":"rise|grow|drop|slide|stagger",
"from":TIME,"to":TIME} (stagger reveals parts one by one: wall courses, steps, pillars) and "hide":{"at":TIME}.
Kit:
- box/slab {w,h,d,color,texture:"stone"} | cylinder {r,h,r_top,segments} | cone/pyramid {r,h} | dome {r} | sphere {r}
- mound {r,h,stretch} dirt pile | wall {from:[x,z],to:[x,z],h,thickness,courses,color} stone courses (stagger = laid row by row)
- stairs {from:[x,y,z] top,to:[x,y,z] bottom,width,steps} solid flight (stagger = steps drop in one by one)
- pillar {h,w} | pavilion {w,d,h,cols,rows,roof} pillared hall | spire {w,h,tiers} temple shikhara | arch {w,h,thickness}
- water {x0,x1,z0,z1,y_bottom,level_from,level,from,to} rising water | well {w,h,rope_from,rope_to,rope_start,rope_end} frame, pulley, bucket
- ladder {h,lean} | house {w,d,h,color,roof} | tree {scale,color} | trees/grass/rocks {count,area:[x0,z0,x1,z1],seed,avoid:[[x0,z0,x1,z1]]}
- person {action:"dig|pull|walk|carry|climb|wave|stand",path:[[x,y,z],...],from,to,cloth,skin,turban} | people {count,area,y,action}
- macro stepwell {x0,x1,z_front,length,depth,levels,phases:{dig,walls,stairs,halls,water}} expands into a lined trench,
  flights of steps, pillared halls on each landing and water (see the example).
Recipe that works: (1) hook: wide three-quarter shot of the site as it was, a tiny human-scale start (a well, a hut, a
mound); (2) one scene per build stage, each stage animating within its own scene; (3) the camera moves on every scene
(push in to the cutaway, glide along the structure, dip inside, rise out); (4) a wide reveal with the real name and one
hard fact; (5) a teaser. 8-10 scenes, 40-55 s. Build what the facts say; never invent features of a real monument.
""".strip()
