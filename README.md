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

## VVIP ops runbook (resilience & manual control)
- **Priority everywhere:** `results.json` (manual) > fresh API > last local snapshot > baked list.
- **Sources go down?** Every successful pull is snapshotted in the display's browser
  (localStorage). Cards silently keep serving the last good data. Nothing blanks.
- **Fix a record fast:** move mouse (controls appear) → **Export data** → downloads
  `results.json` with the board's current effective data → edit any record (in Claude,
  a text editor, anywhere) → upload to the repo as `results.json` → all screens adopt
  it within ~5 min. The `fixtures` array replaces the whole list, so removing a record
  from the file removes it from the board.
- **All times:** stored as UTC in `utc` fields; rendered in GST (UTC+4) with correct
  date rollovers. Edit times in UTC; the board does the conversion.
- **Standings/form:** live from TheSportsDB (PL league table + City last-5), 6-hourly,
  snapshotted. Pre-season shows the 20 clubs at zero with a "season starts" note.
- **Still manual by design:** transfers, top scorer/assists (until an API-Football key
  is added), and anything you choose to pin via `results.json`.

## social.json (X / @ManCity pipeline)
Written automatically by a scheduled Claude Cowork task on an operator laptop
(X logged in via Claude in Chrome, GitHub connected). Schema:
`{"updated":"<ISO UTC>","posts":[{"text":"...","url":"https://x.com/ManCity/status/...","time":"<ISO UTC>"}]}`
Newest first, max 8. The board merges the top posts into the news rotation tagged
"X @ManCity" and refreshes every 15 min. Manual edits work the same way as results.json.

## Data aging policy
- **X posts (social.json):** anything older than 72h is dropped automatically at
  render, and a dead laptop's snapshot expires after 72h too. Old posts cannot linger.
- **News:** cached headlines keep showing (the wall never blanks), but the card badge
  escalates from CACHED to STALE once the snapshot passes 72h.
- **results.json:** manual data is authoritative and never auto-expires — instead its
  age is surfaced: if the file's `updated` field is 7+ days old, the footer shows a
  warning. Exported files carry `updated` automatically.
- **Fixtures:** past matches drop out of list and calendar ~2h after kickoff.
