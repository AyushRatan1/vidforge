"""Free trend signals for India. Each function returns a list of candidate dicts and never raises."""
from __future__ import annotations

import datetime as dt
import html
import re

import requests

UA = {"User-Agent": "VidForge/1.0 (trend research)"}
TIMEOUT = 15

YT_CATEGORIES = {"film": 1, "music": 10, "sports": 17, "gaming": 20, "people": 22, "comedy": 23,
                 "entertainment": 24, "news": 25, "howto": 26, "education": 27, "science": 28}


def _get(url, **kw):
    r = requests.get(url, headers=UA, timeout=TIMEOUT, **kw)
    r.raise_for_status()
    return r


def google_trends(geo: str = "IN") -> list[dict]:
    """Google Trends 'trending now' RSS (no key)."""
    try:
        import feedparser
        feed = feedparser.parse(_get(f"https://trends.google.com/trending/rss?geo={geo}").content)
        out = []
        for e in feed.entries:
            news = e.get("ht_news_item_title") or ""
            out.append({"source": "google_trends", "title": e.get("title", ""),
                        "signal": e.get("ht_approx_traffic", ""), "context": html.unescape(news),
                        "url": e.get("ht_news_item_url") or e.get("link", "")})
        return out
    except Exception as ex:
        return [{"source": "google_trends", "error": str(ex)}]


def google_news(topic: str | None = None, lang: str = "en") -> list[dict]:
    """Google News RSS for India. topic: None (top), WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT,
    SPORTS, SCIENCE, HEALTH."""
    hl, ceid = ("hi", "IN:hi") if lang == "hi" else ("en-IN", "IN:en")
    base = "https://news.google.com/rss"
    url = f"{base}/headlines/section/topic/{topic}?hl={hl}&gl=IN&ceid={ceid}" if topic else f"{base}?hl={hl}&gl=IN&ceid={ceid}"
    try:
        import feedparser
        feed = feedparser.parse(_get(url).content)
        return [{"source": f"google_news:{topic or 'top'}", "title": e.get("title", ""),
                 "signal": e.get("published", ""), "url": e.get("link", "")} for e in feed.entries[:30]]
    except Exception as ex:
        return [{"source": "google_news", "error": str(ex)}]


def _hours_since(iso: str) -> float:
    try:
        t = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return max(1.0, (dt.datetime.now(dt.timezone.utc) - t).total_seconds() / 3600)
    except Exception:
        return 24.0


def youtube_trending(api_key: str, region: str = "IN", category: str | None = None, n: int = 50) -> list[dict]:
    """YouTube 'most popular' chart for a region (1 quota unit per call)."""
    if not api_key:
        return [{"source": "youtube_trending", "error": "no YouTube Data API key"}]
    params = {"part": "snippet,statistics,contentDetails", "chart": "mostPopular", "regionCode": region,
              "maxResults": min(50, n), "key": api_key}
    if category and category in YT_CATEGORIES:
        params["videoCategoryId"] = YT_CATEGORIES[category]
    try:
        items = _get("https://www.googleapis.com/youtube/v3/videos", params=params).json().get("items", [])
    except Exception as ex:
        return [{"source": "youtube_trending", "error": str(ex)}]
    out = []
    for it in items:
        sn, st = it["snippet"], it.get("statistics", {})
        views = int(st.get("viewCount", 0))
        hrs = _hours_since(sn.get("publishedAt", ""))
        out.append({"source": f"youtube_trending:{category or 'all'}", "title": sn.get("title", ""),
                    "channel": sn.get("channelTitle"), "views": views, "views_per_hour": round(views / hrs),
                    "duration": it.get("contentDetails", {}).get("duration"), "tags": (sn.get("tags") or [])[:8],
                    "url": f"https://youtu.be/{it['id']}"})
    return out


def youtube_niche(api_key: str, query: str, region: str = "IN", days: int = 7, shorts: bool = True,
                  lang: str | None = "hi") -> list[dict]:
    """Top recent videos for a niche query, ranked by views/hour (≈101 quota units)."""
    if not api_key:
        return [{"source": "youtube_niche", "error": "no YouTube Data API key"}]
    after = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    params = {"part": "snippet", "q": query, "type": "video", "order": "viewCount", "regionCode": region,
              "publishedAfter": after, "maxResults": 25, "key": api_key,
              "videoDuration": "short" if shorts else "medium"}
    if lang:
        params["relevanceLanguage"] = lang
    try:
        ids = [i["id"]["videoId"] for i in _get("https://www.googleapis.com/youtube/v3/search", params=params).json().get("items", [])]
        if not ids:
            return []
        vids = _get("https://www.googleapis.com/youtube/v3/videos",
                    params={"part": "snippet,statistics", "id": ",".join(ids), "key": api_key}).json().get("items", [])
    except Exception as ex:
        return [{"source": "youtube_niche", "error": str(ex)}]
    out = []
    for it in vids:
        sn, st = it["snippet"], it.get("statistics", {})
        views = int(st.get("viewCount", 0))
        out.append({"source": f"youtube_niche:{query}", "title": sn.get("title", ""), "channel": sn.get("channelTitle"),
                    "views": views, "views_per_hour": round(views / _hours_since(sn.get("publishedAt", ""))),
                    "url": f"https://youtu.be/{it['id']}"})
    return sorted(out, key=lambda x: -x["views_per_hour"])


def nasa_apod(api_key: str = "DEMO_KEY") -> list[dict]:
    try:
        j = _get("https://api.nasa.gov/planetary/apod", params={"api_key": api_key or "DEMO_KEY"}).json()
        return [{"source": "nasa_apod", "title": j.get("title", ""), "context": (j.get("explanation") or "")[:400],
                 "url": j.get("hdurl") or j.get("url")}]
    except Exception as ex:
        return [{"source": "nasa_apod", "error": str(ex)}]


def reddit_top(sub: str = "india", n: int = 20) -> list[dict]:
    try:
        j = _get(f"https://www.reddit.com/r/{sub}/top.json", params={"t": "day", "limit": n}).json()
        return [{"source": f"reddit:{sub}", "title": c["data"]["title"], "signal": c["data"].get("score"),
                 "url": "https://reddit.com" + c["data"].get("permalink", "")} for c in j["data"]["children"]]
    except Exception as ex:
        return [{"source": f"reddit:{sub}", "error": str(ex)}]


NICHE_SOURCES = {
    # niche -> which free feeds to pull
    "space": [("news", "SCIENCE"), ("yt_cat", "science"), ("apod", None), ("trends", None)],
    "science": [("news", "SCIENCE"), ("yt_cat", "science"), ("trends", None)],
    "tech": [("news", "TECHNOLOGY"), ("yt_cat", "science"), ("trends", None)],
    "stories": [("trends", None), ("yt_cat", "entertainment"), ("news_hi", None)],
    "mythology": [("trends", None), ("yt_cat", "entertainment"), ("news_hi", None)],
    "kids": [("yt_cat", "education"), ("trends", None)],
    "news": [("trends", None), ("news", None), ("news_hi", None), ("yt_cat", "news")],
    "sports": [("news", "SPORTS"), ("yt_cat", "sports"), ("trends", None)],
    "general": [("trends", None), ("news", None), ("yt_cat", None)],
}


def gather(niche: str, yt_key: str = "", seed_queries: list[str] | None = None, nasa_key: str = "") -> list[dict]:
    items = []
    for kind, arg in NICHE_SOURCES.get(niche, NICHE_SOURCES["general"]):
        if kind == "trends":
            items += google_trends("IN")
        elif kind == "news":
            items += google_news(arg, "en")
        elif kind == "news_hi":
            items += google_news(None, "hi")
        elif kind == "yt_cat":
            items += youtube_trending(yt_key, "IN", arg, 30)
        elif kind == "apod":
            items += nasa_apod(nasa_key)
    for q in (seed_queries or [])[:3]:
        items += youtube_niche(yt_key, q)[:10]
    seen, out = set(), []
    for it in items:
        key = re.sub(r"\W+", " ", (it.get("title") or it.get("error", ""))).lower().strip()[:80]
        if key and key not in seen:
            seen.add(key)
            out.append(it)
    return out
