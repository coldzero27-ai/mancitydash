#!/usr/bin/env python3

# -*- coding: utf-8 -*-

"""

API-Football -> football.json for the Man City wall dashboard.

 

Pulls (4-5 requests per run, well inside the 100/day free cap):

  - all season fixtures for Man City (one call: past results + future fixtures)

  - per-player season stats (top scorer / top assists, PL)

 

Writes football.json next to this script. The dashboard reads it and:

  - fixtures replace the live fixture feed (better kickoff times)

  - results join the two-of-three agreement chain (TheSportsDB / ESPN / API-Football)

  - topScorer / topAssists feed the stat blocks (manual override still wins)

 

Key lookup order: env APIFOOTBALL_KEY, then config.json {"apifootball_key": "..."}.

Run modes: `python fetch_football.py` (once, exit code 0 on success) - used by

the GitHub Action; the local runner imports build() and loops it.

"""

 

import json, os, sys, urllib.request

from datetime import datetime, timezone, timedelta

 

API = "https://v3.football.api-sports.io"

TEAM_ID = 50          # Manchester City

PL_ID = 39            # Premier League

SEASON = 2026         # 2026/27 (API-Football seasons use the starting year)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "football.json")

 

# API-Football league id -> the board's competition codes

COMP = {39: "PL", 2: "UCL", 45: "FA", 48: "EFL", 528: "SHIELD",

        531: "SUPER", 15: "CWC"}

 

def key():

    k = os.environ.get("APIFOOTBALL_KEY", "").strip()

    if k:

        return k

    try:

        cfg = json.load(open(os.path.join(os.path.dirname(OUT), "config.json"), encoding="utf-8"))

        return str(cfg.get("apifootball_key", "")).strip()

    except Exception:

        return ""

 

def get(path, k):

    req = urllib.request.Request(API + path, headers={

        "x-apisports-key": k, "User-Agent": "dashboard-fetcher"})

    with urllib.request.urlopen(req, timeout=30) as r:

        return json.loads(r.read().decode("utf-8", "replace"))

 

def gst_datekey(iso_utc):

    """UTC ISO timestamp -> GST (UTC+4, no DST) calendar date key."""

    dt = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))

    return (dt.astimezone(timezone(timedelta(hours=4)))).strftime("%Y-%m-%d")

 

def transform_fixtures(payload):

    """API-Football fixtures response -> (future_fixtures, results_by_gst_date)."""

    fixtures, results = [], {}

    for row in payload.get("response", []):

        try:

            fx = row.get("fixture", {}) or {}

            lg = row.get("league", {}) or {}

            tm = row.get("teams", {}) or {}

            gl = row.get("goals", {}) or {}

            date = fx.get("date")            # ISO with offset

            if not date:

                continue

            utc = datetime.fromisoformat(date.replace("Z", "+00:00")) \

                  .astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

            home = (tm.get("home") or {}).get("name", "")

            away = (tm.get("away") or {}).get("name", "")

            lid = lg.get("id")

            lname = str(lg.get("name", ""))

            comp = COMP.get(lid, lname[:12] if lname else "OTHER")

            fr = "friendl" in lname.lower() or "club friendlies" in lname.lower()

            status = ((fx.get("status") or {}).get("short") or "").upper()

            if status in ("FT", "AET", "PEN"):

                hs, as_ = gl.get("home"), gl.get("away")

                if hs is None or as_ is None:

                    continue

                me_home = (tm.get("home") or {}).get("id") == TEAM_ID

                mine, theirs = (hs, as_) if me_home else (as_, hs)

                res = "W" if mine > theirs else ("D" if mine == theirs else "L")

                results[gst_datekey(utc)] = {"score": "%d-%d" % (hs, as_),

                                             "res": res, "fr": fr}

            elif status in ("NS", "TBD", "PST"):

                fixtures.append({"utc": utc, "comp": comp, "home": home,

                                 "away": away,

                                 "venue": ((fx.get("venue") or {}).get("name") or "")})

        except Exception:

            continue

    fixtures.sort(key=lambda f: f["utc"])

    return fixtures[:20], results

 

def transform_players(payload, want="goals"):

    """players response page -> best 'Name - N' by goals or assists (PL stats)."""

    best_name, best_n = None, 0

    for row in payload.get("response", []):

        try:

            name = (row.get("player") or {}).get("name", "")

            for st in row.get("statistics", []) or []:

                if ((st.get("league") or {}).get("id")) != PL_ID:

                    continue

                g = (st.get("goals") or {})

                n = g.get("total") if want == "goals" else g.get("assists")

                n = int(n or 0)

                if n > best_n:

                    best_n, best_name = n, name

        except Exception:

            continue

    if best_name and best_n > 0:

        surname = best_name.strip().split()[-1]

        return "%s - %d" % (surname, best_n)

    return None

 

def build():

    k = key()

    if not k:

        print("fetch_football: no APIFOOTBALL_KEY / config.json key - skipping")

        return False

    fx = get("/fixtures?team=%d&season=%d" % (TEAM_ID, SEASON), k)

    if fx.get("errors"):

        print("fetch_football: API error:", fx["errors"])

        return False

    fixtures, results = transform_fixtures(fx)

    scorer = assists = None

    page, pages = 1, 1

    while page <= min(pages, 3):   # squad fits in <=3 pages; hard cap for quota safety

        pl = get("/players?team=%d&league=%d&season=%d&page=%d"

                 % (TEAM_ID, PL_ID, SEASON, page), k)

        if pl.get("errors"):

            break

        pages = ((pl.get("paging") or {}).get("total") or 1)

        s = transform_players(pl, "goals")

        a = transform_players(pl, "assists")

        def better(cur, new):

            if not new:

                return cur

            if not cur:

                return new

            return new if int(new.rsplit(" ", 1)[1]) > int(cur.rsplit(" ", 1)[1]) else cur

        scorer = better(scorer, s)

        assists = better(assists, a)

        page += 1

    out = {"updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),

           "source": "api-football (api-sports.io)",

           "fixtures": fixtures, "results": results,

           "topScorer": scorer or "", "topAssists": assists or ""}

    if not fixtures and not results:

        print("fetch_football: empty payload - keeping previous football.json")

        return False

    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print("fetch_football: wrote football.json (%d fixtures, %d results, scorer=%s, assists=%s)"

          % (len(fixtures), len(results), out["topScorer"] or "-", out["topAssists"] or "-"))

    return True

 

if __name__ == "__main__":

    sys.exit(0 if build() else 1)