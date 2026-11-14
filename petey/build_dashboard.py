"""Build Dashboard.html from exam.json, ObjectiveTracker.md and MissLog.md.

Usage:  python petey/build_dashboard.py               (your files, at the repo root)
        python petey/build_dashboard.py --dir examples/sample
Re-run after each session's close-out; the HTML is a snapshot, not live.
Standard library only.
"""
import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ID = r"\d+(?:\.\d+)+[a-z]?"  # objective IDs: 1.1, 1.3a, 12.4, 2.1.3


def parse_domains(text):
    """'## Domain N: Name (W%)' headings, in order."""
    out = []
    for m in re.finditer(r"^## Domain (\d+)\s*[:—–-]\s*(.+?)\s*\(([^()]*%)\)\s*$", text, re.M):
        out.append({"n": m.group(1), "name": m.group(2), "weight": m.group(3)})
    return out


def parse_tracker(text):
    objs, domain = [], None
    for line in text.splitlines():
        h = re.match(r"## Domain (\d+)", line)
        if h:
            domain = h.group(1)
            continue
        if line.startswith("## "):
            domain = None
            continue
        m = re.match(rf"\|\s*({ID})\s*\|(.*)", line)
        if not m or domain is None:
            continue
        cells = [c.strip() for c in m.group(2).split("|")] + [""] * 8
        scope, planned, _prior, status, quiz, _fire, _hands, date = cells[:8]
        q = re.match(r"(\d+)\s*/\s*(\d+)", quiz)
        inter = re.search(r"\+\s*(\d+)\s*/\s*(\d+)", quiz)
        objs.append({
            "id": m.group(1),
            "domain": domain,
            "scope": scope,
            "planned": planned,
            "status": "solid" if "✅" in status else "shaky" if "🟡" in status
                      else "paused" if "🔵" in status else "todo",
            "quiz": int(q.group(1)) if q else None,
            "quizOf": int(q.group(2)) if q else None,
            "interleaved": f"{inter.group(1)}/{inter.group(2)}" if inter else None,
            "date": date,
        })
    return objs


def parse_schedule(text):
    """Planned sessions per date from the 'Daily schedule' table (rows start with an ISO date)."""
    if "## Daily schedule" not in text:
        return []
    sec = text.split("## Daily schedule", 1)[1].split("\n## ", 1)[0]
    plan = []
    for line in sec.splitlines():
        m = re.match(r"\|\s*(\d{4}-\d{2}-\d{2})[^|]*\|([^|]*)\|", line)
        if not m:
            continue
        ids = re.findall(ID, m.group(2))
        if ids:
            plan.append((dt.date.fromisoformat(m.group(1)), ids))
    return sorted(plan)


def parse_mocks(text):
    """Rows of the tracker's 'Mock exams' table (used by build_game.py). A score cell is 'n/N' or 'n%'."""
    if "## Mock exams" not in text:
        return []
    sec = text.split("## Mock exams", 1)[1].split("\n## ", 1)[0]

    def pct(cell):
        m = re.match(r"(\d+)\s*/\s*(\d+)", cell)
        if m:
            return round(100 * int(m.group(1)) / int(m.group(2)))
        m = re.match(r"(\d+)\s*%", cell)
        return int(m.group(1)) if m else None

    mocks = []
    for line in sec.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 7 or cells[0] in ("Mock", "") or set(cells[0]) <= set("-"):
            continue
        name, planned, taken, overall, taught, untaught, notes = cells[:7]
        mocks.append({
            "name": name, "planned": planned, "taken": taken, "notes": notes,
            "overall": overall, "taught": taught, "untaught": untaught,
            "overallPct": pct(overall), "taughtPct": pct(taught), "untaughtPct": pct(untaught),
        })
    return mocks


def parse_misslog(text, today):
    entries = []
    for b in re.split(r"\n(?=### )", text):
        if not b.startswith("### ") or "Short question paraphrase" in b:
            continue
        head = b.splitlines()[0][4:]
        tag = re.search(rf"^\*\*(?:Objective|Domain):\*\*\s*({ID})", b, re.M)
        nexts = re.findall(r"next review (\d{4}-\d{2}-\d{2})", b)
        nxt = dt.date.fromisoformat(nexts[-1]) if nexts else None
        flags = re.match(r"^[^\w(\"'`]*", head).group(0)  # leading emoji before the title
        entries.append({
            "obj": tag.group(1) if tag else None,
            "title": head[len(flags):].strip(),
            "status": "solid" if "✅" in flags else "once" if "🔁" in flags else "new",
            "fire": "🔥" in flags,
            "due": nxt is None or nxt <= today,
        })
    return entries


def strength(o, ents):
    """0-100. Taught objectives only: 60% quiz, 40% MissLog retention. An open 🔥 caps it at 59."""
    if o["status"] in ("todo", "paused") or not o["quizOf"]:
        return None
    quiz = o["quiz"] / o["quizOf"]
    if ents:
        ret = sum(1 if e["status"] == "solid" else 0.5 if e["status"] == "once" else 0 for e in ents) / len(ents)
    else:
        ret = 1.0
    score = 100 * (0.6 * quiz + 0.4 * ret)
    if any(e["fire"] for e in ents):
        score = min(score, 59)
    return round(score)


def next_weekend_day(today):
    d = today + dt.timedelta(days=1)
    while d.weekday() < 5:
        d += dt.timedelta(days=1)
    return d


def petey_says(today, exam, objs, plan, gap, totals):
    """One or two short, plain sentences: pace first, then what to do next."""
    if today >= exam:
        return "Exam day's here or past. Trust the work."
    s = lambda n, w: f"{n} {w}{'' if n == 1 else 's'}"
    taught = [o for o in objs if o["score"] is not None]
    nxt = next((o for o in objs if o["status"] in ("todo", "paused")), None)
    parts = []
    if not taught and plan and today < plan[0][0]:
        parts.append(f"Plan's ready. First session: {plan[0][1][0]} on {plan[0][0]:%a %d %b}.")
    elif gap < 0:
        tip = f"Catch up with a double on {next_weekend_day(today):%a}" if gap >= -2 else "Use doubles and borrow from the buffer, not the mocks"
        parts.append(f"{s(-gap, 'session')} behind. {tip}.")
    elif gap > 0:
        parts.append(f"{s(gap, 'session')} ahead. Bank it, or take a rest day.")
    else:
        parts.append("On schedule.")
    if totals["fire"]:
        parts.append(f"Clear the 🔥 first ({totals['fire']} open).")
    elif totals["due"]:
        parts.append(f"{s(totals['due'], 'review')} due.")
    elif nxt and taught:
        parts.append(f"Next up: {nxt['id']}.")
    return " ".join(parts)


def build(base):
    cfg_path = base / "exam.json"
    if not cfg_path.exists():
        sys.exit(f"{cfg_path} not found. Run /init-exam in Claude Code first (or pass --dir examples/sample).")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    today = dt.date.fromisoformat(cfg["today"]) if cfg.get("today") else dt.date.today()  # "today" pins the sample
    exam = dt.date.fromisoformat(cfg["exam_date"])
    start = dt.date.fromisoformat(cfg["day0"])
    phases = [(p["label"], p.get("kind", "phase"), dt.date.fromisoformat(p["from"]), dt.date.fromisoformat(p["to"]))
              for p in cfg.get("phases", [])]

    tracker = (base / "ObjectiveTracker.md").read_text(encoding="utf-8")
    ml_path = base / "MissLog.md"
    misslog = ml_path.read_text(encoding="utf-8") if ml_path.exists() else ""
    domains = parse_domains(tracker)
    objs = parse_tracker(tracker)
    ents = parse_misslog(misslog, today)
    if not objs:
        sys.exit("No objective rows found in ObjectiveTracker.md (expected '## Domain N: Name (W%)' sections).")
    ids = {o["id"] for o in objs}
    status_of = {o["id"]: o["status"] for o in objs}
    for e in ents:
        if status_of.get(e["obj"]) in ("todo", "paused"):
            e["due"] = False  # parked: not due until its objective has been taught
    for o in objs:
        mine = [e for e in ents if e["obj"] == o["id"]]
        o["entries"] = len(mine)
        o["open"] = sum(e["status"] != "solid" for e in mine)
        o["solidEntries"] = sum(e["status"] == "solid" for e in mine)
        o["dueNow"] = sum(e["due"] for e in mine)
        o["fire"] = sum(e["fire"] for e in mine)
        o["score"] = strength(o, mine)
        o["items"] = sorted(
            [{"t": e["title"], "s": e["status"], "d": e["due"], "f": e["fire"]} for e in mine],
            key=lambda x: (not x["f"], not x["d"], x["s"] == "solid"),
        )
    unmapped = [e["title"] for e in ents if e["obj"] not in ids]
    plan = parse_schedule(tracker)
    dom_of = {o["id"]: o["domain"] for o in objs}

    end = exam - dt.timedelta(days=1)  # the last prep day is the day before the exam
    total_days = max((end - start).days + 1, 1)
    elapsed = min(max((today - start).days + 1, 0), total_days)
    taught = sum(o["status"] in ("solid", "shaky") for o in objs)
    planned_by_today = sum(len(i) for d, i in plan if d <= today)
    off = lambda d: (d - start).days
    segments = []
    for dom in domains:
        days = [d for d, i in plan if any(dom_of.get(x, x.split(".")[0]) == dom["n"] for x in i)]
        if days:
            segments.append({"label": "D" + dom["n"], "domain": dom["n"], "kind": "domain",
                             "from": off(min(days)), "to": off(max(days)) + 1,
                             "dates": f"{min(days):%d %b} – {max(days):%d %b}"})
    for label, kind, a, b in phases:
        segments.append({"label": label, "kind": kind, "from": off(a), "to": off(b) + 1,
                         "dates": f"{a:%d %b}" + ("" if a == b else f" – {b:%d %b}")})
    today_pos = min(max(off(today) + 1, 0), total_days)
    # Where the plan would be if it had taught exactly `taught` sessions (end-of-day units).
    cum, content_pos = 0, 0
    for d, i in plan:
        if cum + len(i) >= taught:
            content_pos = off(d) + (taught - cum) / len(i)
            break
        cum += len(i)
    else:
        content_pos = off(plan[-1][0]) + 1 if plan else 0
    gap = taught - planned_by_today
    totals = {
        "entries": len(ents),
        "due": sum(e["due"] for e in ents),
        "solid": sum(e["status"] == "solid" for e in ents),
        "once": sum(e["status"] == "once" for e in ents),
        "new": sum(e["status"] == "new" for e in ents),
        "fire": sum(e["fire"] for e in ents),
    }
    exam_text = f"{exam:%a %d %b %Y}" + (f", {cfg['exam_time']}" if cfg.get("exam_time") else "")
    data = {
        "exam": cfg.get("exam_name", "Exam"),
        "code": cfg.get("exam_code", ""),
        "examText": exam_text,
        "examShort": f"{exam.day} {exam:%b}",
        "today": today.isoformat(),
        "daysLeft": (exam - today).days,
        "petey": petey_says(today, exam, objs, plan, gap, totals) if cfg.get("petey_status", True) else "",
        "sample": bool(cfg.get("sample")),
        "domains": domains,
        "objectives": objs,
        "totals": totals,
        "unmapped": unmapped,
        "pace": {
            "start": start.isoformat(), "end": end.isoformat(),
            "elapsed": elapsed, "totalDays": total_days,
            "taught": taught, "sessions": len(objs),
            "plannedByToday": planned_by_today, "gap": gap,
            "segments": segments, "todayPos": today_pos, "contentPos": content_pos,
            "phaseKinds": [[label, kind] for label, kind, _a, _b in phases],
        },
    }
    title = html.escape(f"{data['exam']} progress · Petey")
    page = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    page = page.replace("__TITLE__", title)
    page = page.replace("__GENERATED__", html.escape(dt.datetime.now().strftime("%a %d %b %Y, %H:%M")))
    out = base / "Dashboard.html"
    out.write_text(page, encoding="utf-8")
    print(f"{out} written: {len(objs)} objectives, {len(ents)} MissLog entries, {len(unmapped)} unmapped")
    for t in unmapped:
        print("  unmapped (add an **Objective:** X.Y line):", t)


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=Fraunces:opsz,wght@9..144,400;9..144,600&display=swap">
<style>
/* Layout: header + Petey line, 4 figures, timeline, domain x objective heatmap, weakest list + detail panel. */
:root {
  --bg: #f5f8fb; --panel: #ffffff; --fg: #14202b; --muted: #5b6b79; --line: #d9e2ea;
  --accent: #1f7fbf;
  --s0: #e4eaf0;            /* not started */
  --weak: #d9534f; --mid: #e9a23b; --ok: #8cc56b; --strong: #2e9d5b;
  --display: "Fraunces", Georgia, serif;
  --body: "IBM Plex Sans", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, monospace;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0e1620; --panel: #16212d; --fg: #e3ebf2; --muted: #93a4b3; --line: #273645;
  --accent: #56b0ea; --s0: #223140;
  --weak: #e0605b; --mid: #e3a64a; --ok: #7fb862; --strong: #3fae6c; color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #0e1620; --panel: #16212d; --fg: #e3ebf2; --muted: #93a4b3; --line: #273645;
  --accent: #56b0ea; --s0: #223140;
  --weak: #e0605b; --mid: #e3a64a; --ok: #7fb862; --strong: #3fae6c; color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.5 var(--body); }
.wrap { max-width: 1180px; margin-inline: auto; padding-block: 28px 48px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 24px; }
.brand { display: flex; align-items: center; gap: 10px; color: var(--muted); font: 500 .8rem/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; margin-bottom: 8px; }
.brand .mark { display: inline-grid; place-items: center; width: 28px; height: 28px; border-radius: 8px; background: var(--accent); color: #fff; font: 600 .78rem/1 var(--mono); letter-spacing: 0; }
.sample { display: inline-block; margin-left: 6px; padding: 2px 8px; border-radius: 99px; background: var(--mid); color: #10202c; font: 600 .7rem/1.4 var(--mono); }
header h1 { font: 600 clamp(1.6rem, 3.5vw, 2.2rem)/1.15 var(--display); margin: 0; text-wrap: balance; }
header p { margin: 4px 0 0; color: var(--muted); max-width: 70ch; }
.says { margin-top: 12px; padding: 10px 14px; border-left: 3px solid var(--accent); background: var(--panel); border-radius: 0 8px 8px 0; max-width: 80ch; }
.says b { font-weight: 600; }
.figs { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 12rem), 1fr)); gap: 12px; }
.fig { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; }
.fig .v { font: 400 2rem/1.1 var(--display); font-variant-numeric: tabular-nums; }
.fig .l { color: var(--muted); font-size: .8rem; text-transform: uppercase; letter-spacing: .06em; }
.fig .n { color: var(--muted); font-size: .85rem; margin-top: 2px; }
section h2 { font: 500 1.1rem/1.3 var(--body); margin: 0 0 4px; }
section > p.note { color: var(--muted); margin: 0 0 12px; font-size: .9rem; max-width: 80ch; }
.matrix { display: grid; gap: 10px; }
.drow { display: grid; grid-template-columns: minmax(9rem, 15rem) 1fr; gap: 12px; align-items: stretch; }
.dlabel { padding: 8px 0; min-width: 0; }
.dlabel b { display: block; font-weight: 600; }
.dlabel span { color: var(--muted); font-size: .82rem; }
.cells { display: grid; grid-template-columns: repeat(auto-fill, minmax(6.2rem, 1fr)); gap: 6px; }
.cell { border: 0; border-radius: 8px; padding: 8px 10px; text-align: left; cursor: pointer; min-height: 74px;
  font: inherit; color: #10202c; display: grid; align-content: space-between; gap: 4px; position: relative; }
.cell:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.cell.sel { outline: 3px solid var(--fg); outline-offset: 2px; }
.cell .id { font: 600 1rem/1 var(--mono); }
.cell .sc { font: 500 .78rem/1.2 var(--mono); opacity: .85; }
.cell .top { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 2px 6px; }
.cell .badge { font: 500 .72rem/1 var(--mono); white-space: nowrap; }
.cell.todo { background: var(--s0); color: var(--muted); }
.legend { display: flex; flex-wrap: wrap; gap: 14px; font-size: .82rem; color: var(--muted); margin-top: 12px; }
.legend i { display: inline-block; width: 14px; height: 14px; border-radius: 4px; vertical-align: -2px; margin-right: 6px; }
.detail { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 18px 20px; display: grid; gap: 12px; }
.detail h3 { margin: 0; font: 600 1.2rem/1.3 var(--display); }
.kv { display: flex; flex-wrap: wrap; gap: 8px 20px; font-size: .9rem; }
.kv span { color: var(--muted); }
.items { list-style: none; margin: 0; padding: 0; display: grid; gap: 4px; max-height: 320px; overflow: auto; }
.items li { display: grid; grid-template-columns: 4.5rem 1fr; gap: 10px; font-size: .9rem; padding: 4px 0; border-bottom: 1px solid var(--line); min-width: 0; }
.items li em { font-style: normal; font-family: var(--mono); font-size: .76rem; color: var(--muted); }
.items li.due em { color: var(--mid); }
.items li.fire em { color: var(--weak); }
.weakest { display: grid; gap: 6px; }
.bar { display: grid; grid-template-columns: 3.4rem 1fr 3rem; gap: 10px; align-items: center; font-size: .88rem; }
.bar .track { height: 10px; background: var(--s0); border-radius: 99px; overflow: hidden; }
.bar .fill { height: 100%; border-radius: 99px; }
.bar b { font-family: var(--mono); font-weight: 500; }
.bar span:last-child { font-family: var(--mono); text-align: right; color: var(--muted); }
.two { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr)); gap: 24px; align-items: start; }
.pace { background: var(--panel); border: 1px solid var(--line); border-radius: 10px; padding: 16px 18px; display: grid; gap: 12px; }
.pace .verdict { font-size: .92rem; }
.pace .verdict b { font-weight: 600; }
.tl { position: relative; padding-top: 30px; padding-bottom: 34px; }
.tl .bar { position: relative; height: 26px; background: var(--s0); border-radius: 6px; display: block; }
.tl .seg { position: absolute; top: 0; bottom: 0; border-radius: 4px; display: flex; align-items: center; justify-content: center;
  font: 500 .72rem/1 var(--mono); color: #10202c; overflow: hidden; white-space: nowrap; border-right: 2px solid var(--panel); }
.seg.domain, .k-domain { background: color-mix(in srgb, var(--accent) 45%, var(--panel)); }
.seg.domain.done, .k-done { background: var(--accent); color: #fff; }
.seg.mocks, .k-mocks { background: color-mix(in srgb, var(--mid) 70%, var(--panel)); }
.seg.buffer, .k-buffer { background: color-mix(in srgb, var(--mid) 35%, var(--panel)); }
.seg.light, .k-light { background: color-mix(in srgb, var(--ok) 45%, var(--panel)); }
.seg.phase, .k-phase { background: color-mix(in srgb, var(--muted) 35%, var(--panel)); }
.tl .pin { position: absolute; top: 0; bottom: 0; width: 0; }
.tl .pin::before { content: ""; position: absolute; top: 22px; bottom: 28px; left: -1px; width: 2px; background: var(--fg); }
.tl .pin span { position: absolute; left: 0; transform: translateX(-50%); font: 500 .74rem/1.2 var(--body); white-space: nowrap; }
.tl .pin.today span { top: 0; }
.tl .pin.content::before { background: var(--strong); top: 30px; bottom: 22px; width: 3px; }
.tl .pin.content.behind::before { background: var(--weak); }
.tl .pin.content span { bottom: 0; color: var(--muted); }
.tl .ends { display: flex; justify-content: space-between; color: var(--muted); font-size: .76rem; margin-top: 4px; }
.tl .ends span:last-child { text-align: right; }
.tlkey { display: flex; flex-wrap: wrap; gap: 4px 16px; color: var(--muted); font-size: .8rem; }
.tlkey i { display: inline-block; width: 12px; height: 12px; border-radius: 3px; vertical-align: -2px; margin-right: 6px; }
footer { color: var(--muted); font-size: .8rem; }
@media (max-width: 560px) { .drow { grid-template-columns: 1fr; gap: 4px; } }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand"><span class="mark">PT</span><span>Petey · Cert PT</span><span id="sample"></span></div>
    <h1 id="h1"></h1>
    <p id="takeaway"></p>
    <div class="says" id="says" hidden></div>
  </header>

  <div class="figs" id="figs"></div>

  <section class="pace" id="pace" aria-label="Timeline: plan versus progress"></section>

  <section>
    <h2>Strength by objective</h2>
    <p class="note">Each cell is one study session. Colour = 60% quiz score + 40% MissLog retention (share of that objective's misses now ✅ solid; 🔁 counts half). An open 🔥 caps it at amber. Grey = not taught yet; the corner number is misses already logged. Click a cell for detail.</p>
    <div class="matrix" id="matrix"></div>
    <div class="legend">
      <span><i style="background:var(--strong)"></i>Strong 85+</span>
      <span><i style="background:var(--ok)"></i>OK 70–84</span>
      <span><i style="background:var(--mid)"></i>Shaky 55–69</span>
      <span><i style="background:var(--weak)"></i>Weak &lt;55</span>
      <span><i style="background:var(--s0)"></i>Not started</span>
    </div>
  </section>

  <div class="two">
    <section>
      <h2>Weakest taught objectives</h2>
      <p class="note">Lowest strength first: where to aim warm-ups and mock-phase review.</p>
      <div class="weakest" id="weakest"></div>
    </section>
    <section class="detail" id="detail" aria-live="polite"></section>
  </div>

  <footer>Snapshot built __GENERATED__ from ObjectiveTracker.md and MissLog.md by Cert PT. Re-run <code>python petey/build_dashboard.py</code> after each session. <span id="unmapped"></span></footer>
</div>
<script>
const D = __DATA__;
const band = s => s == null ? null : s >= 85 ? "strong" : s >= 70 ? "ok" : s >= 55 ? "mid" : "weak";
const bandName = {strong: "Strong", ok: "OK", mid: "Shaky", weak: "Weak"};
const plural = (n, w) => n + " " + w + (n === 1 ? "" : "s");
const el = (tag, attrs = {}, kids = []) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) k === "text" ? n.textContent = v : n.setAttribute(k, v);
  kids.forEach(k => n.append(k));
  return n;
};
const objs = D.objectives;
const taught = objs.filter(o => o.score != null);
const T = D.totals;

document.getElementById("h1").textContent = D.exam + (D.code ? " (" + D.code + ")" : "") + " progress";
if (D.sample) document.getElementById("sample").append(el("span", {class: "sample", text: "SAMPLE · made-up data"}));
if (D.petey) {
  const says = document.getElementById("says");
  says.append(el("b", {text: "Petey says: "}), document.createTextNode(D.petey));
  says.hidden = false;
}

// Header figures
const done = taught.length;
const figs = [
  ["Exam in", D.daysLeft >= 0 ? plural(D.daysLeft, "day") : "done", D.examText],
  ["Sessions taught", done + " / " + objs.length, objs.filter(o => o.status === "solid").length + " ✅ · " + objs.filter(o => o.status === "shaky").length + " 🟡"],
  ["MissLog due now", String(T.due), "of " + plural(T.entries, "entry").replace("entrys", "entries")],
  ["Misses now solid", T.entries ? Math.round(100 * T.solid / T.entries) + "%" : "–", T.solid + " ✅ · " + T.once + " 🔁 · " + T.new + " 🆕" + (T.fire ? " · " + T.fire + " 🔥" : "")],
];
const figsEl = document.getElementById("figs");
figs.forEach(([l, v, n]) => figsEl.append(el("div", {class: "fig"}, [el("div", {class: "l", text: l}), el("div", {class: "v", text: v}), el("div", {class: "n", text: n})])));

// Pace timeline: planned phases, today, and where the plan would be for the sessions actually taught
(() => {
  const P = D.pace, box = document.getElementById("pace");
  const fmt = iso => new Date(iso + "T00:00:00").toLocaleDateString(undefined, {day: "numeric", month: "short"});
  const pct = d => (100 * d / P.totalDays) + "%";
  box.append(el("h2", {text: "Timeline"}));
  const bar = el("div", {class: "bar"});
  P.segments.forEach(sg => {
    const mine = sg.domain ? objs.filter(o => o.domain === sg.domain) : [];
    const isDone = mine.length > 0 && mine.every(o => o.score != null);
    const n = el("div", {class: "seg " + sg.kind + (isDone ? " done" : ""), title: sg.label + ": " + sg.dates, text: sg.label});
    n.style.left = pct(sg.from);
    n.style.width = pct(sg.to - sg.from);
    bar.append(n);
  });
  const tl = el("div", {class: "tl"}, [bar]);
  const pin = (cls, pos, label) => { const p = el("div", {class: "pin " + cls}, [el("span", {text: label})]); p.style.left = pct(pos); return p; };
  const days = Math.round((P.contentPos - P.todayPos) * 10) / 10;
  tl.append(pin("today", P.todayPos, "Today"));
  tl.append(pin("content" + (days < 0 ? " behind" : ""), P.contentPos, "Content reached"));
  tl.append(el("div", {class: "ends"}, [el("span", {text: fmt(P.start)}), el("span", {text: fmt(P.end) + " · exam " + D.examShort})]));
  box.append(tl);
  const key = [["k-done", "domain taught"], ["k-domain", "domain planned"]];
  const known = ["mocks", "buffer", "light"];
  P.phaseKinds.forEach(([label, kind]) => key.push(["k-" + (known.includes(kind) ? kind : "phase"), label.toLowerCase()]));
  box.append(el("div", {class: "tlkey"}, key.map(([cls, text]) => el("span", {}, [el("i", {class: cls}), document.createTextNode(text)]))));
  const g = P.gap, v = el("div", {class: "verdict"});
  v.append(el("b", {text: g > 0 ? plural(g, "session") + " ahead" : g < 0 ? plural(-g, "session") + " behind" : "On schedule"}));
  v.append(document.createTextNode(" · " + P.taught + " of " + P.sessions + " sessions taught; the plan had " + P.plannedByToday + " done by the end of today. " +
    "Content reached is where the plan would be for the sessions taught" + (days ? " (" + plural(Math.abs(days), "day") + (days < 0 ? " behind today)." : " ahead of today).") : ", level with today.") +
    " Time used: day " + P.elapsed + " of " + P.totalDays + "."));
  box.append(v);
})();

// Takeaway
const weakest = [...taught].sort((a, b) => a.score - b.score);
const next = objs.find(o => o.status === "todo" || o.status === "paused");
document.getElementById("takeaway").textContent =
  done + " of " + objs.length + " sessions taught." +
  (weakest.length ? " Weakest so far: " + weakest.slice(0, 2).map(o => o.id + " (" + o.score + ")").join(" and ") + "." : "") +
  " " + plural(T.due, "MissLog review") + " due." + (next ? " Next up: " + next.id + "." : "");

// Matrix
const matrix = document.getElementById("matrix");
const cellsById = {};
D.domains.forEach(d => {
  const mine = objs.filter(o => o.domain === d.n);
  const ts = mine.filter(o => o.score != null);
  const avg = ts.length ? Math.round(ts.reduce((s, o) => s + o.score, 0) / ts.length) : null;
  const label = el("div", {class: "dlabel"}, [
    el("b", {text: "Domain " + d.n + " · " + d.weight}),
    el("span", {text: d.name + (avg != null ? " · avg " + avg + " over " + ts.length + "/" + mine.length : " · not started")}),
  ]);
  const cells = el("div", {class: "cells"});
  mine.forEach(o => {
    const b = band(o.score);
    const btn = el("button", {class: "cell" + (b ? "" : " todo"), type: "button", "aria-label": o.id + " " + (b ? bandName[b] + " " + o.score : "not started")});
    if (b) btn.style.background = "var(--" + b + ")";
    const top = el("span", {class: "top"}, [el("span", {class: "id", text: o.id})]);
    if (o.open) top.append(el("span", {class: "badge", text: (o.fire ? "🔥" : "") + o.open + " open"}));
    btn.append(top);
    btn.append(el("span", {class: "sc", text: b ? o.score + " · " + o.quiz + "/" + o.quizOf : (o.status === "paused" ? "paused" : "—")}));
    btn.addEventListener("click", () => show(o.id));
    cells.append(btn);
    cellsById[o.id] = btn;
  });
  matrix.append(el("div", {class: "drow"}, [label, cells]));
});

// Weakest list
const wk = document.getElementById("weakest");
if (!weakest.length) wk.append(el("p", {class: "note", text: "Nothing taught yet."}));
weakest.forEach(o => {
  const fill = el("div", {class: "fill"});
  fill.style.width = o.score + "%";
  fill.style.background = "var(--" + band(o.score) + ")";
  const row = el("div", {class: "bar"}, [el("b", {text: o.id}), el("div", {class: "track"}, [fill]), el("span", {text: String(o.score)})]);
  row.style.cursor = "pointer";
  row.addEventListener("click", () => show(o.id));
  wk.append(row);
});

// Detail panel
const detail = document.getElementById("detail");
const statusName = {solid: "✅ solid", shaky: "🟡 shaky", paused: "🔵 paused", todo: "⬜ not started"};
function show(id) {
  const o = objs.find(x => x.id === id);
  if (!o) return;
  Object.values(cellsById).forEach(c => c.classList.remove("sel"));
  if (cellsById[id]) cellsById[id].classList.add("sel");
  detail.replaceChildren();
  detail.append(el("h3", {text: o.id + " · " + o.scope}));
  const kv = el("div", {class: "kv"});
  const add = (k, v) => kv.append(el("div", {}, [el("span", {text: k + " "}), document.createTextNode(v)]));
  add("Status", statusName[o.status]);
  if (o.score != null) add("Strength", o.score + " (" + bandName[band(o.score)] + ")");
  if (o.quiz != null) add("Quiz", o.quiz + "/" + o.quizOf + (o.interleaved ? " (+" + o.interleaved + " interleaved)" : ""));
  add("Taught", o.date || "planned " + o.planned);
  add("MissLog", o.entries + " entries · " + o.solidEntries + " solid · " + o.dueNow + " due");
  detail.append(kv);
  if (o.items.length) {
    const ul = el("ul", {class: "items"});
    o.items.forEach(it => {
      const tag = it.f ? "🔥 open" : it.d ? "due" : it.s === "solid" ? "✅ solid" : it.s === "once" ? "🔁 once" : "🆕 new";
      ul.append(el("li", {class: it.f ? "fire" : it.d ? "due" : ""}, [el("em", {text: tag}), el("span", {text: it.t})]));
    });
    detail.append(ul);
  } else {
    detail.append(el("p", {class: "note", text: "No MissLog entries for this objective."}));
  }
}
if (objs.length) show((weakest[0] || next || objs[0]).id);
if (D.unmapped.length) document.getElementById("unmapped").textContent = plural(D.unmapped.length, "MissLog entry").replace("entrys", "entries") + " not mapped to an objective (add an **Objective:** line).";
</script>
</body>
</html>
"""

if __name__ == "__main__":
    sys.stdout.reconfigure(errors="replace")  # Windows consoles can't always print emoji in titles
    ap = argparse.ArgumentParser(description="Build Dashboard.html for Cert PT.")
    ap.add_argument("--dir", default=str(ROOT), help="folder with exam.json, ObjectiveTracker.md and MissLog.md (default: repo root)")
    build(Path(ap.parse_args().dir).resolve())
