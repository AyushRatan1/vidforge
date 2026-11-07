"""Content formats. A channel picks the formats it is allowed to make; the scout picks one per idea."""

FORMATS = {
    "space_facts": {
        "name": "Space and science facts",
        "audience": "general", "made_for_kids": False, "aspect": "9:16", "music": "cosmic",
        "look": "space or grid backgrounds, planets, comets, counters for every number, a recurring astronaut mascot",
        "structure": "hook with the most surprising number or date -> what it is -> why it happens (1-2 scenes) -> "
                     "the mind-blowing number as a counter -> how/when YOU can see or use it -> teaser for the next video",
    },
    "trend_explainer": {
        "name": "Trending topic explained",
        "audience": "general", "made_for_kids": False, "aspect": "9:16", "music": "upbeat",
        "look": "grid or gradient backgrounds, big labels, arrows, counters, emoji; neutral and factual",
        "structure": "hook: 'everyone is searching X, here is why' -> what happened (facts only) -> the one number "
                     "that matters -> what it means for a normal person -> what to watch next. No opinions, no blame.",
    },
    "story": {
        "name": "Story (mythology, history, folk tales, mystery)",
        "audience": "general", "made_for_kids": False, "aspect": "9:16", "music": "indian",
        "look": "paper background, warm palette, diya, mountains, characters as simple rigs, typewriter titles",
        "structure": "cold open on the most dramatic moment -> rewind to setup -> conflict -> twist -> moral or "
                     "lesser-known fact -> 'part 2' teaser. Retell in your own words; never copy a film or show.",
    },
    "facts_list": {
        "name": "Top-N facts / listicle",
        "audience": "general", "made_for_kids": False, "aspect": "9:16", "music": "upbeat",
        "look": "numbered badges (text with bg), counters, emoji, one visual per fact",
        "structure": "hook with fact #1 teased -> facts counting down -> best fact last -> question to the viewer",
    },
    "festival": {
        "name": "Festival origins and science",
        "audience": "general", "made_for_kids": False, "aspect": "9:16", "music": "devotional",
        "look": "sunset or paper backgrounds, diyas, sparkles, warm gold palette",
        "structure": "date + greeting hook -> the story behind it -> a surprising science/history angle -> "
                     "how it is celebrated across India -> wish the viewer. Respectful, no claims of miracles as fact.",
    },
    "quiz": {
        "name": "Quiz / guess the answer",
        "audience": "general", "made_for_kids": False, "aspect": "9:16", "music": "upbeat",
        "look": "options as coloured pills, a counter for the timer, confetti on the answer",
        "structure": "question -> 3 options -> 3-2-1 countdown -> answer reveal with one explanation -> next question teaser",
    },
    "kids_learning": {
        "name": "Kids learning song or rhyme (original)",
        "audience": "kids", "made_for_kids": True, "aspect": "9:16", "music": "playful",
        "look": "sunburst or sky backgrounds, the channel mascot character talking, big bright counters/letters, "
                "confetti and stars, slow pacing, repeated chorus lines",
        "structure": "mascot greets -> teach one concept (numbers, colours, animals, Hindi letters) with repetition -> "
                     "sing-along chorus line repeated 2-3 times -> praise the child. Original lyrics only; never use "
                     "existing copyrighted songs or characters. Calm pacing, no scary or unsafe behaviour shown.",
    },
    "kids_story": {
        "name": "Kids moral story (Panchatantra style, original retelling)",
        "audience": "kids", "made_for_kids": True, "aspect": "9:16", "music": "calm",
        "look": "sky or paper background, animal characters (talking=true when speaking), simple props",
        "structure": "introduce the friends -> a small problem -> a clever, kind solution -> the moral in one line. "
                     "Gentle, no violence, positive role models.",
    },
}


def format_brief(fmt_id: str) -> str:
    f = FORMATS.get(fmt_id) or FORMATS["space_facts"]
    return (f"Format: {f['name']} ({fmt_id})\nAudience: {f['audience']} (made_for_kids={f['made_for_kids']})\n"
            f"Default aspect: {f['aspect']}, music mood: {f['music']}\nLook: {f['look']}\nStructure: {f['structure']}")
