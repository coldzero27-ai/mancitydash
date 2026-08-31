#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

fetch_news.py - writes feeds.json for the Man City wall dashboard.

 

Why this exists: the board's in-page news route goes through public CORS proxies,

and the office network blocks all of them (diag 26 Aug: three proxies failing or

timing out). This script fetches the news feeds SERVER-SIDE (GitHub Action every

30 min) and commits feeds.json next to the board - the board already prefers that

file when it is fresh (45-minute gate), so no board changes are needed.

 

Sources: BBC Sport Man City RSS + Google News search RSS. Items older than 72h

are dropped at the source, matching the board's freshness rule.

"""

import json, os, re, sys, urllib.request

from datetime import datetime, timezone, timedelta

from email.utils import parsedate_to_datetime

 

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feeds.json")

MAX_AGE_H = 72

SOURCES = [

    "https://feeds.bbci.co.uk/sport/football/teams/manchester-city/rss.xml",

    "https://news.google.com/rss/search?q=%22Manchester+City%22&hl=en-GB&gl=GB&ceid=GB:en",

]

 

def get(url):

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 dashboard-fetcher"})

    with urllib.request.urlopen(req, timeout=25) as r:

        return r.read().decode("utf-8", "replace")

 

def parse_items(xml):

    items = []

    for m in re.finditer(r"<item>([\s\S]*?)</item>", xml):

        block = m.group(1)

        t = re.search(r"<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?</title>", block)

        d = re.search(r"<pubDate>([\s\S]*?)</pubDate>", block)

        if not t:

            continue

        title = re.sub(r"\s+", " ", t.group(1)).strip()

        title = re.sub(r"\s+-\s+[A-Za-z0-9 .''&]+$", "", title)  # strip " - Source" suffix

        title = title.replace("&amp;", "&").replace("&#39;", "'").replace("&quot;", '"')

        when = None

        if d:

            try:

                when = parsedate_to_datetime(d.group(1).strip())

                if when.tzinfo is None:

                    when = when.replace(tzinfo=timezone.utc)

            except Exception:

                when = None

        items.append({"title": title, "time": when})

    return items

 

def build():

    now = datetime.now(timezone.utc)

    cutoff = now - timedelta(hours=MAX_AGE_H)

    seen, fresh = set(), []

    for url in SOURCES:

        try:

            for it in parse_items(get(url)):

                if it["time"] is None or it["time"] < cutoff:

                    continue

                key = re.sub(r"[^a-z0-9]+", "", it["title"].lower())[:60]

                if not it["title"] or len(it["title"]) < 15 or key in seen:

                    continue

                seen.add(key)

                fresh.append(it)

        except Exception as e:

            print("fetch_news: source failed:", url.split("/")[2], e)

    if not fresh:

        print("fetch_news: no fresh items - keeping previous feeds.json")

        return False

    fresh.sort(key=lambda x: x["time"], reverse=True)

    news = [{"title": it["title"], "img": None, "video": None,

             "time": it["time"].strftime("%Y-%m-%dT%H:%M:%SZ")} for it in fresh[:12]]

    out = {"updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),

           "source": "bbc + google news (server-side)",

           "news": news,

           "ticker": [n["title"] for n in news[:10]]}

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("fetch_news: wrote feeds.json (%d items, newest: %s)" % (len(news), news[0]["title"][:60]))

    return True

 

if __name__ == "__main__":

    sys.exit(0 if build() else 1)