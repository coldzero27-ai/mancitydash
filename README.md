# CFG Wall Dashboard — Manchester City & City Football Group

Full-screen 1920x1080 wall dashboard for office TVs. Man City hero zone
(next match, countdowns, titles/transfers flip card, news, latest video,
form & stats), CFG club spotlight loop, fixtures in GST (UTC+4), news ticker.

## Deploy (GitHub Pages)
1. Create a **private-feeling repo** (unguessable name recommended — page carries `noindex`).
2. Upload everything in this folder (keep the `assets/` structure and `.nojekyll`).
3. Settings → Pages → deploy from `main` / root.
4. Open `https://<user>.github.io/<repo>/` — done.
If Pages sticks at `deployment_queued`, it's GitHub-side: wait, re-run, or push a tiny commit.

## Updating content
- **Scores / table / stats / transfers / club data** → edit `results.json`, upload.
  The board refetches it every 5 minutes. Fields it understands are documented
  in the comment at the top of `index.html`. `results.json` overrides everything.
- **Ticker headlines** → edit `news.json` (refetched every 30 min).
- **New background video** → replace `assets/bg.mp4` (H.264 mp4, no audio,
  `-movflags +faststart`). Photo backdrop: `assets/bg.jpg` (1920x1080).
- **New crest / face / trophy** → drop the file into the matching `assets/`
  folder using the existing naming, and add/adjust the map entry in `index.html`.

## Live data (automatic)
- Fixtures: TheSportsDB (Man City id 133613), on load + every 6h — catches
  broadcast time changes, cup draws, friendlies. `results.json` outranks it.
- News card: BBC Sport Man City feed (thumbnails) via allorigins proxy, hourly.
- Latest video card: official Man City YouTube channel feed, hourly.
- Fallbacks: every live source fails silently to baked data / JSON files —
  the board never blanks.

## Controls (bottom-right, auto-hide in Present mode)
Background: video/photo · Tint: light/medium/dark · Present (fullscreen).

## Devices
Locked 16:9 stage, letterboxed on any screen. Times in GST with correct date
rollovers. Older Samsung Tizen browsers (pre-2022): backdrop-filter blur may
be ignored (cards fall back to plain translucency); no ES module import maps
are used, by design.

## Data sources (baked snapshot, verified 4-6 Jul 2026)
premierleague.com · mancity.com · skysports.com · ESPN. Fixture times beyond
opening weekend are provisional until broadcast picks.
