#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

ScoreBat -> scorebat.json for the Man City wall dashboard video fallback.

 

Fetches the ScoreBat v3 feed (secret token, server-side only), finds the most

recent Manchester City match that has highlight videos, and writes the public

embed URL to scorebat.json. The board uses it when YouTube won't play.

 

Token lookup: env SCOREBAT_TOKEN, then config.json {"scorebat_token": "..."}.

"""

 

import json, os, re, sys, urllib.request

from datetime import datetime, timezone

 

FEED = "https://www.scorebat.com/video-api/v3/feed/?token="

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scorebat.json")

 

def token():

    t = os.environ.get("SCOREBAT_TOKEN", "").strip()

    if t:

        return t

    try:

        cfg = json.load(open(os.path.join(os.path.dirname(OUT), "config.json"), encoding="utf-8"))

        return str(cfg.get("scorebat_token", "")).strip()

    except Exception:

        return ""

 

def pick_city_match(feed):

    """Newest feed entry whose title involves Manchester City and has a video."""

    best = None

    for m in feed.get("response", []):

        try:

            title = str(m.get("title", ""))

            if not re.search(r"manchester\s+city", title, re.I):

                continue

            vids = m.get("videos") or []

            if not vids:

                continue

            date = str(m.get("date", ""))

            if best is None or date > best["date"]:

                src = None

                for v in vids:  # prefer the full-highlights video over single goals

                    emb = str(v.get("embed", ""))

                    mm = re.search(r"src=['\"]([^'\"]+)['\"]", emb)

                    if mm:

                        src = mm.group(1)

                        if re.search(r"highlight", str(v.get("title", "")), re.I):

                            break

                if src:

                    best = {"date": date, "title": title, "embed": src,

                            "thumbnail": str(m.get("thumbnail", ""))}

        except Exception:

            continue

    return best

 

def build():

    t = token()

    if not t:

        print("fetch_scorebat: no SCOREBAT_TOKEN / config.json token - skipping")

        return False

    req = urllib.request.Request(FEED + t, headers={"User-Agent": "dashboard-fetcher"})

    with urllib.request.urlopen(req, timeout=30) as r:

        feed = json.loads(r.read().decode("utf-8", "replace"))

    if isinstance(feed, dict) and feed.get("error"):

        print("fetch_scorebat: API error:", feed.get("error"))

        return False

    best = pick_city_match(feed if isinstance(feed, dict) else {"response": feed})

    if not best:

        print("fetch_scorebat: no City match with videos in the feed - keeping previous file")

        return False

    out = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),

           "source": "scorebat.com", "match": best["title"], "date": best["date"],

           "embed": best["embed"], "thumbnail": best["thumbnail"]}

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("fetch_scorebat: wrote scorebat.json (%s)" % best["title"])

    return True

 

if __name__ == "__main__":

    sys.exit(0 if build() else 1)