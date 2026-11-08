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
Add a top-level "world3d"; scenes get {"type":"world3d"} backgrounds (the default). The video is ONE continuous diorama:
each scene shows its own slice of the timeline, so the build and the camera flow across scenes while the 2D layer adds
captions and 0-2 yellow callout labels per scene
{"type":"text","text":"7 GATES","bg":"#ffd54a","color":"#1c1a17","style":"label","stroke":false,"size":0.056,"y":0.2,"at_word":"seven"}.
Captions {"y":0.6,"size":0.084,"max_words":2,"highlight":"#ffd54a","uppercase":false}; spec "transition":"none".
Shape: 8-10 scenes, 45-60 s: hook, one scene per build stage, a reveal with the real name, a teaser.

Units are metres, y is up, ground is y=0, people are about 1.4 tall, the camera side is +z. The terrain is a block cut
open at its front face (z = terrain.cut), so digs show soil layers like a cutaway. Make it big: width and length about
3x the monument, cut 15 m or more in front of it.
world3d = {"style":"desert|golden|green|overcast|night",
  "terrain":{"width":96,"length":110,"cut":30,"digs":[{"x0":-2,"x1":2,"z0":20,"z1":30,"depth":3,"from":TIME,"to":TIME}]},
  "objects":[...], "camera":[...]}
Style by place: desert for Rajasthan, Gujarat and Egypt; golden for warm evening light; green for Kerala, Bengal, the
Northeast and green river valleys; overcast for Himalayan stone; night only for a lit finale.
TIME is seconds or a scene reference: {"scene":"walls","t":0.5} | {"scene":"walls","at":1.2} | {"scene":"walls","word":"seven"}.
Use scene references so the build follows the narration.
Every object takes "pos":[x,y,z], "rot" (degrees about y), "id" (so shots can target it), "build":{"op":"rise|grow|drop|
slide|stagger","from":TIME,"to":TIME} (stagger lays parts one by one: courses, steps, floors, blocks), "hide":{"at":TIME,
"op":"shrink|lower|sink"}, and "path":[[x,y,z],...] with "from"/"to" to travel (boats, sledges, people).

Macros: use them for monuments. They expand deterministically, everything rests on its support, and each registers
anchors (centre and size) for camera shots.
- pyramid {pos, base, height, courses, ramp:"right|left|front|back"|false, casing, capstone, phases:{courses, ramp,
  casing, capstone}}: stepped core course by course, a ramp raised and lengthened as it grows with teams hauling blocks
  (one theory: say so), casing laid while the ramp comes away, a capstone that lands on the top course.
  Anchors: pyramid, pyramid.top, pyramid.base, pyramid.ramp.
- fort {pos, w, d, h, seed, gates, walkers, palaces: 3 or [{w,d,h,domes,id}], phases:{hill, walls, bastions, gate,
  palaces}}: a rocky hill with a road winding up through gates, crenellated walls on the rim, round bastions, the main
  gate where the road arrives, palaces inside. Anchors: fort, fort.hill, fort.walls, fort.top, fort.path, fort.gate
  (main), fort.gate1, fort.gate2... (lower gates from the bottom), fort.palaces.
- temple {pos, w, d, h, phases:{plinth, hall, spire}}: stepped plinth, pillared mandapa, sanctum and shikhara.
  Anchors: temple, temple.hall, temple.spire.
- stepwell {x0, x1, z_front, length, depth, levels, phases:{dig, walls, stairs, halls, water}}. Anchors: stepwell, stepwell.bottom.
Kit, for everything else:
- land: hill / cliff {r or w,d, h, seed, path: true or {from, span, turns, width}} faceted rock plateau with a flat top
  at h | water {x0,x1,z0,z1,y_bottom,level_from,level,from,to} | trees / grass / rocks {count, area:[x0,z0,x1,z1], seed,
  avoid:[[x0,z0,x1,z1]]} | town {count, area, colors, scale} flat-roofed houses | mound {r,h} small dirt piles only
- building: wall {from:[x,z], to:[x,z], h, thickness, crenels} | bastion {r,h} | gate {w,h,d,towers} | palace {w,d,h,
  floors,domes,dome} | tomb {w,h,minarets} | minaret {h,r,balconies,tilt (degrees, leans away from the centre; exaggerate to 6-8 so it shows)} | pavilion {w,d,h,cols,rows} | pillar |
  spire {w,h,tiers} | arch | stairs {from:[x,y,z] top, to:[x,y,z] bottom, width, steps} | ramp {from, to, width} |
  frustum {w, w_top, h} (w_top 0 makes a pyramid) | box / slab {w,h,d,texture:"stone"} | cylinder | cone | dome | sphere | house
- work and life: blocks {cols,rows,layers,size} | sledge (a block on runners; give it a path) | boat {length, cargo,
  sail} | flag {h,color} | well | ladder | person {action:"dig|pull|walk|carry|climb|wave|stand", path, from, to} |
  people {count, area, y, action}

Camera: use shot keys. {"at":TIME, "shot":"wide|medium|close|top|low|orbit|inside", "target":"fort.gate" (an anchor
or id) or [x,y,z], "angle":30} (0 = from the front, +z; 90 = from the right). Optional: "dist", "height" (camera
height above the target), "size" (override the target size, a number or [w,h,d]), "fov". Framing is automatic: the
target sits in the upper middle and the caption band stays clear. "orbit" sweeps "sweep" degrees (default 90) until
the next key or the end. "inside" is for open interiors (a stepwell trench, a courtyard). The camera glides between
keys; two keys at the same time make a cut. Plain {"at","pos","look","fov"} keys still work.
Recipe: (1) hook: an establishing shot with something already moving; (2) one scene per build stage, each with a
medium or close shot on that stage's anchor (a key near t 0.25 and another near t 1 with the angle moved 15-30 degrees
so the camera keeps drifting); (3) one low or top shot for scale; (4) reveal: orbit the whole monument with its real
name and one hard fact; (5) a teaser for the next video.
Rules: never fake terrain with a giant mound (use hill or cliff); anything placed on top must rest on its support (its
y is the support's top), so prefer macros; keep low shots over the terrain block, not in front of its cut face; build
only what the facts say, never invent features of a real monument; 0-2 labels per scene.
""".strip()
