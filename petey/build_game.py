"""Build GameDashboard.html: a gamified view of the same data as Dashboard.html.

Usage:  python petey/build_game.py               (your files, at the repo root)
        python petey/build_game.py --dir examples/sample
Re-run after build_dashboard.py at each close-out; the HTML is a snapshot, not live.
XP, streaks, quests, badges and the readiness bar are all derived from exam.json,
ObjectiveTracker.md (incl. its "Mock exams" table) and MissLog.md. Standard library only.
"""
import argparse
import datetime as dt
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_dashboard import (ROOT, parse_domains, parse_misslog, parse_mocks,  # noqa: E402
                             parse_schedule, parse_tracker, strength)

# Readiness bands (strength 0-100, same score as Dashboard.html).
GREEN, AMBER = 80, 60
# Exam-ready rule. Judgment, not calibrated: only the vendor's official practice test is.
READY_STRENGTH = 75     # domain-weighted strength, untaught units counted as 0
READY_MOCK = 80         # latest mock, taught-objective %

# XP rules. Showing up earns something; getting it right earns more.
XP_REVIEW = {"ok": 10, "part": 5, "miss": 3}
XP_CONF3_BONUS = 5          # a correct answer given at confidence 3
XP_LOGGED = 2               # capturing a miss in the MissLog
XP_TAUGHT = 100             # an objective taught (✅ or 🟡)
XP_SOLID = 50               # ...and closed out ✅
XP_PER_QUIZ_POINT = 10      # per x/7
XP_PER_INTERLEAVED = 5      # per x/3
XP_MOCK = 200               # sitting a full mock
XP_MOCK_TAUGHT_BONUS = 5    # per taught-% point above 50

# Set in main() from exam.json.
HERE = TODAY = EXAM = PREP_START = None
EXAM_NAME = ""
DOMAINS = []                # (n, name, weight %) with ranges as their midpoint


def weight_pct(text):
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", text)]
    return sum(nums) / len(nums) if nums else 0.0


def review_events(misslog):
    """(date, kind, conf3) for every dated review-log line."""
    out = []
    for line in re.findall(r"^\*\*Review log:\*\* (.*)$", misslog, re.M):
        m = re.match(r"(\d{4}-\d{2}-\d{2})\s+(.*)", line)
        if not m:
            continue
        day = dt.date.fromisoformat(m.group(1))
        rest = m.group(2)
        low = rest.lower()
        if any(w in low for w in ("not scored", "parked", "re-taught", "voided")):
            continue
        verdict = rest.split("(")[0].split(":")[0]
        if low.startswith("logged"):
            out.append((day, "logged", False))
        elif "taught in" in low and "✅" not in verdict:
            continue
        elif "✅" in verdict:
            out.append((day, "ok", "conf 3" in rest))
        elif "🟡" in verdict or "partial" in verdict.lower():
            out.append((day, "part", False))
        elif "❌" in verdict:
            out.append((day, "miss", False))
    return out


def build():
    tracker = (HERE / "ObjectiveTracker.md").read_text(encoding="utf-8")
    ml = HERE / "MissLog.md"
    misslog = ml.read_text(encoding="utf-8") if ml.exists() else ""
    objs = parse_tracker(tracker)
    ents = parse_misslog(misslog, TODAY)
    for o in objs:
        m = re.match(r"(\d+)", o["interleaved"] or "")
        o["interleaved"] = int(m.group(1)) if m else None
    mocks = parse_mocks(tracker)
    plan = parse_schedule(tracker)
    events = review_events(misslog)

    # ---- XP, by day ----
    xp_by_day, reviews_by_day = {}, {}
    def add(day, n):
        xp_by_day[day] = xp_by_day.get(day, 0) + n
    for day, kind, c3 in events:
        if kind == "logged":
            add(day, XP_LOGGED)
            continue
        add(day, XP_REVIEW[kind] + (XP_CONF3_BONUS if c3 else 0))
        reviews_by_day[day] = reviews_by_day.get(day, 0) + 1
    sessions_by_day = {}
    for o in objs:
        if o["status"] in ("solid", "shaky") and re.match(r"\d{4}-\d{2}-\d{2}", o["date"] or ""):
            day = dt.date.fromisoformat(o["date"])
            sessions_by_day[day] = sessions_by_day.get(day, 0) + 1
            add(day, XP_TAUGHT + (XP_SOLID if o["status"] == "solid" else 0)
                + XP_PER_QUIZ_POINT * (o["quiz"] or 0) + XP_PER_INTERLEAVED * (o["interleaved"] or 0))
    bosses = []
    for m in mocks:
        taken = re.match(r"\d{4}-\d{2}-\d{2}", m["taken"] or "")
        if taken:
            day = dt.date.fromisoformat(taken.group(0))
            tp = m["taughtPct"] or 0
            add(day, XP_MOCK + XP_MOCK_TAUGHT_BONUS * max(tp - 50, 0))
        bosses.append({
            "name": m["name"], "planned": m["planned"], "taken": bool(taken),
            "overall": m["overall"], "taught": m["taught"], "taughtPct": m["taughtPct"],
            "result": None if not taken else ("defeated" if (m["taughtPct"] or 0) >= 80 else "scraped"),
        })
    total_xp = sum(xp_by_day.values())

    # ---- Streak: consecutive active days ending today (or yesterday, if today hasn't started) ----
    active = set(xp_by_day)
    day = TODAY if TODAY in active else TODAY - dt.timedelta(days=1)
    streak = 0
    while day in active:
        streak += 1
        day -= dt.timedelta(days=1)
    best = run = 0
    if active:
        d, last = min(active), max(active)
        while d <= last:
            run = run + 1 if d in active else 0
            best = max(best, run)
            d += dt.timedelta(days=1)

    # ---- Badges ----
    taught = [o for o in objs if o["status"] in ("solid", "shaky")]
    comebacks = 0
    for b in re.split(r"\n(?=### )", misslog):
        lines = re.findall(r"^\*\*Review log:\*\* \S+ (.*)$", b, re.M)
        missed = False
        for l in lines:
            v = l.split("(")[0]
            if "❌" in v and not l.lower().startswith("logged"):
                missed = True
            elif missed and "✅" in v:
                comebacks += 1
                break
    best_review_day = max(reviews_by_day.values(), default=0)
    domain_done = {}
    for n, name, _w in DOMAINS:
        mine = [o for o in objs if o["id"].startswith(n + ".")]
        domain_done[n] = {"name": name, "done": sum(o["status"] in ("solid", "shaky") for o in mine), "of": len(mine),
                          "solid": sum(o["status"] == "solid" for o in mine)}
    fires_open = sum(e["fire"] for e in ents)
    badges = [
        {"icon": "dumbbell", "name": "First rep", "desc": "Teach your first objective", "got": len(taught) >= 1},
        {"icon": "target", "name": "Perfect seven", "desc": "Score 7/7 on an objective quiz",
         "got": any(o["quiz"] == 7 for o in objs), "count": sum(o["quiz"] == 7 for o in objs)},
        {"icon": "layers", "name": "Hat-trick", "desc": "Three objectives in one day",
         "got": max(sessions_by_day.values(), default=0) >= 3},
        {"icon": "checklist", "name": "Backlog buster", "desc": "20+ reviews in a single day", "got": best_review_day >= 20},
        {"icon": "rotate", "name": "Comeback", "desc": "Turn 10 misses into later correct reviews",
         "got": comebacks >= 10, "progress": f"{min(comebacks, 10)}/10"},
        {"icon": "shield", "name": "Ice cold", "desc": "No confident-wrong items open", "got": fires_open == 0},
        {"icon": "flame", "name": "On a roll", "desc": "7-day study streak", "got": best >= 7, "progress": f"{min(best, 7)}/7"},
        {"icon": "mountain", "name": "Solid ground", "desc": "25 MissLog entries solid",
         "got": sum(e["status"] == "solid" for e in ents) >= 25,
         "progress": f"{min(sum(e['status'] == 'solid' for e in ents), 25)}/25"},
        {"icon": "sword", "name": "Boss slayer", "desc": "≥ 80% on taught objectives in a mock",
         "got": any(b["result"] == "defeated" for b in bosses)},
    ]
    for n, d in domain_done.items():
        badges.append({"icon": "map", "name": f"Domain {n} cleared", "desc": d["name"],
                       "got": d["done"] == d["of"], "progress": f"{d['done']}/{d['of']}"})

    # ---- Today's quests ----
    today_ids = next((i for d, i in plan if d == TODAY), [])
    by_id = {o["id"]: o for o in objs}
    quests = []
    for i in today_ids:
        o = by_id.get(i, {})
        quests.append({"name": f"Clear objective {i}", "detail": o.get("scope", ""),
                       "done": o.get("status") in ("solid", "shaky") and o.get("date") == TODAY.isoformat(),
                       "xp": f"+{XP_TAUGHT}–{XP_TAUGHT + XP_SOLID + 7 * XP_PER_QUIZ_POINT + 3 * XP_PER_INTERLEAVED} XP"})
    done_today = reviews_by_day.get(TODAY, 0)
    quests.append({"name": "Daily reviews", "detail": f"{min(done_today, 10)}/10 spaced reviews today",
                   "done": done_today >= 10, "xp": "+3–15 XP each"})
    quests.append({"name": "Keep the streak alive", "detail": f"Day {streak if TODAY in active else streak + 1} if you study today",
                   "done": TODAY in active, "xp": "streak"})

    # ---- Readiness: strength per unit, per domain, overall ----
    untaught = {o["id"] for o in objs if o["status"] in ("todo", "paused")}
    for e in ents:
        if e["obj"] in untaught:
            e["due"] = False
    units = []
    for o in objs:
        mine = [e for e in ents if e["obj"] == o["id"]]
        s = strength(o, mine)
        units.append({"id": o["id"], "scope": o["scope"], "score": s, "quiz": o["quiz"],
                      "band": None if s is None else ("green" if s >= GREEN else "amber" if s >= AMBER else "red"),
                      "due": sum(e["due"] for e in mine), "open": sum(e["status"] != "solid" for e in mine),
                      "fire": sum(e["fire"] for e in mine)})
    weight = {n: w for n, _name, w in DOMAINS}
    rows, overall_num, taught_num, taught_den = [], 0.0, 0.0, 0.0
    for n, name, w in DOMAINS:
        mine = [u for u in units if u["id"].startswith(n + ".")]
        scored = [u["score"] for u in mine if u["score"] is not None]
        taught_avg = round(sum(scored) / len(scored)) if scored else None
        exam_avg = sum(u["score"] or 0 for u in mine) / max(len(mine), 1)   # untaught = 0
        overall_num += w * exam_avg
        if scored:
            taught_num += w * taught_avg
            taught_den += w
        rows.append({"n": n, "name": name, "weight": w, "units": mine, "taught": len(scored), "of": len(mine),
                     "strength": taught_avg, "exam": round(exam_avg),
                     "band": None if taught_avg is None else ("green" if taught_avg >= GREEN else "amber" if taught_avg >= AMBER else "red")})
    overall = round(overall_num / (sum(w for _n, _name, w in DOMAINS) or 100))
    taught_strength = round(taught_num / taught_den) if taught_den else None
    # Focus: weakest units first, weighted by the domain's exam share per unit; untaught units come after taught weak ones.
    per_unit_w = {r["n"]: r["weight"] / max(r["of"], 1) for r in rows}
    focus = []
    for u in units:
        w = per_unit_w[u["id"].split(".")[0]]
        if u["score"] is None:
            focus.append({**u, "why": "not taught yet", "pri": 1000 + w})
        elif u["score"] < GREEN:
            gap = GREEN - u["score"]
            reasons = [f"strength {u['score']}"]
            if u["quiz"] is not None and u["quiz"] < 6:
                reasons.append(f"quiz {u['quiz']}/7")
            if u["due"]:
                reasons.append(f"{u['due']} review{'s' if u['due'] != 1 else ''} due")
            if u["fire"]:
                reasons.append(f"{u['fire']} 🔥")
            focus.append({**u, "why": " · ".join(reasons), "pri": gap * w})
    taught_focus = sorted([f for f in focus if f["pri"] < 1000], key=lambda f: -f["pri"])[:5]
    latest_mock = next((b for b in reversed(bosses) if b["taken"]), None)
    checks = [
        {"label": "Every unit taught", "ok": not untaught, "detail": f"{len(units) - len(untaught)}/{len(units)} taught"},
        {"label": f"Weighted strength ≥ {READY_STRENGTH}", "ok": overall >= READY_STRENGTH,
         "detail": f"{overall} (untaught units count as 0)"},
        {"label": f"No red units", "ok": not any(u["band"] == "red" for u in units),
         "detail": ", ".join(u["id"] for u in units if u["band"] == "red") or "none"},
        {"label": f"Latest mock ≥ {READY_MOCK}% on taught objectives",
         "ok": bool(latest_mock and (latest_mock["taughtPct"] or 0) >= READY_MOCK),
         "detail": f"{latest_mock['name']}: {latest_mock['taughtPct']}%" if latest_mock else "no mock yet"},
        {"label": "No open 🔥 items", "ok": fires_open == 0, "detail": f"{fires_open} open"},
    ]
    # One readiness bar. Full (100%) only when every check passes.
    reds = sum(u["band"] == "red" for u in units)
    mock_pct = None
    if latest_mock:
        m = re.match(r"(\d+)\s*/\s*(\d+)", latest_mock["overall"] or "")
        mock_pct = round(100 * int(m.group(1)) / int(m.group(2))) if m else latest_mock["taughtPct"]
    parts = [
        {"name": "Strength", "max": 60, "got": round(60 * min(overall / READY_STRENGTH, 1)),
         "how": f"exam-weighted strength {overall} of {READY_STRENGTH} (untaught units count as 0)"},
        {"name": "Mock", "max": 25, "got": round(25 * min((mock_pct or 0) / READY_MOCK, 1)),
         "how": f"latest mock {mock_pct}% overall of {READY_MOCK}%" if mock_pct is not None else "no mock yet"},
        {"name": "No red units", "max": 15, "got": max(15 - 5 * reds, 0),
         "how": f"{reds} red unit{'s' if reds != 1 else ''} (−5 each)"},
    ]
    pct = sum(p["got"] for p in parts)
    if not all(c["ok"] for c in checks):
        pct = min(pct, 99)          # the bar only fills when you're actually ready
    readiness = {"rows": rows, "overall": overall, "taughtStrength": taught_strength, "focus": taught_focus,
                 "next": [f["id"] for f in sorted([f for f in focus if f["pri"] >= 1000], key=lambda f: f["id"])][:4],
                 "checks": checks, "pct": pct, "parts": parts, "green": GREEN, "amber": AMBER,
                 "maxCols": max((len(r["units"]) for r in rows), default=1)}

    # ---- Activity grid (GitHub-style): Monday of the prep-start week → Sunday of exam week ----
    first = min([PREP_START] + list(xp_by_day)) if xp_by_day else PREP_START
    start = first - dt.timedelta(days=first.weekday())
    end = EXAM + dt.timedelta(days=6 - EXAM.weekday())
    peak = max(xp_by_day.values(), default=1)
    recent = []
    d = start
    while d <= end:
        xp = xp_by_day.get(d, 0)
        lvl = 0 if xp == 0 else min(4, 1 + int(4 * xp / (peak + 1)))
        recent.append({"date": d.isoformat(), "label": d.strftime("%a %d %b"), "xp": xp, "lvl": lvl,
                       "reviews": reviews_by_day.get(d, 0), "sessions": sessions_by_day.get(d, 0),
                       "future": d > TODAY, "today": d == TODAY, "exam": d == EXAM, "dow": d.weekday()})
        d += dt.timedelta(days=1)
    active_days = sum(1 for r in recent if r["xp"] and not r["future"])

    data = {
        "today": TODAY.isoformat(), "daysLeft": (EXAM - TODAY).days, "exam": EXAM.strftime("%a %d %b"),
        "streak": streak, "bestStreak": best,
        "xpToday": xp_by_day.get(TODAY, 0), "badges": badges, "bosses": bosses, "quests": quests,
        "recent": recent, "activeDays": active_days, "domains": [{"n": n, **d} for n, d in domain_done.items()], "readiness": readiness,
        "stats": {"reviews": sum(reviews_by_day.values()), "comebacks": comebacks,
                  "due": sum(e["due"] and not e.get("parked") for e in ents)},
        "rules": [f"Correct review +{XP_REVIEW['ok']} (+{XP_CONF3_BONUS} at conf 3)",
                  f"Partial +{XP_REVIEW['part']} · miss +{XP_REVIEW['miss']} (showing up counts)",
                  f"Objective taught +{XP_TAUGHT}, closed ✅ +{XP_SOLID}, +{XP_PER_QUIZ_POINT} per quiz point",
                  f"Mock sat +{XP_MOCK}, +{XP_MOCK_TAUGHT_BONUS} per taught-% point above 50"],
    }
    page = TEMPLATE.replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
    page = page.replace("__TITLE__", html.escape(f"Quest - {EXAM_NAME}"))
    page = page.replace("__GENERATED__", html.escape(dt.datetime.now().strftime("%a %d %b %Y, %H:%M")))
    (HERE / "GameDashboard.html").write_text(page, encoding="utf-8")
    print(f"{HERE / 'GameDashboard.html'} written: {total_xp} XP, streak {streak} (best {best}), "
          f"{sum(b['got'] for b in badges)}/{len(badges)} badges")


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Saira+Condensed:wght@500;600;700&family=Saira:wght@400;500;600&display=swap">
<style>
:root {
  --bg: #eef4fa; --panel: #ffffff; --fg: #10202c; --muted: #5b6b79; --line: #d6e1ea;
  --accent: #c76a00; --accent2: #c76a00; --gold: #d99a1e; --good: #2e9d5b; --warn: #e9a23b; --bad: #d9534f;
  --track: #dde7ef; --locked: #c4cfd9;
  --head: "Saira Condensed", "Arial Narrow", sans-serif; --mono: "Saira Condensed", "Arial Narrow", sans-serif;
  --body: "Saira", system-ui, sans-serif;
  color-scheme: light;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg: #0b131c; --panel: #142030; --fg: #e3ebf2; --muted: #93a4b3; --line: #243445;
  --accent: #f5a524; --accent2: #f5a524; --gold: #f0b94a; --good: #3fae6c; --warn: #e3a64a; --bad: #e0605b;
  --track: #213040; --locked: #3a4a5a; color-scheme: dark; } }
:root[data-theme="dark"] {
  --bg: #0b131c; --panel: #142030; --fg: #e3ebf2; --muted: #93a4b3; --line: #243445;
  --accent: #f5a524; --accent2: #f5a524; --gold: #f0b94a; --good: #3fae6c; --warn: #e3a64a; --bad: #e0605b;
  --track: #213040; --locked: #3a4a5a; color-scheme: dark; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg); font: 15px/1.5 var(--body); font-variant-numeric: tabular-nums; }
.wrap { max-width: 1100px; margin-inline: auto; padding: 24px 16px 48px; display: grid; gap: 18px; }
.wrap > * { min-width: 0; }
.card { background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 16px 18px; }
h1 { margin: 0; font: 700 clamp(1.8rem, 5vw, 2.6rem)/1 var(--head); text-transform: uppercase; letter-spacing: .02em; }
h2 { margin: 0 0 10px; font: 600 1.15rem/1.2 var(--head); text-transform: uppercase; letter-spacing: .04em; }
.sub { color: var(--muted); margin: 4px 0 0; }
.hero { display: grid; grid-template-columns: auto 1fr; gap: 18px; align-items: center; }
.size { width: 92px; height: 92px; border-radius: 18px; display: grid; place-items: center;
  background: linear-gradient(135deg, var(--accent), var(--accent2)); color: #fff; font: 700 1.9rem/1 var(--head); }
.size small { display: block; font: 500 .62rem/1 var(--mono); letter-spacing: .12em; text-transform: uppercase; opacity: .85; margin-top: 4px; }
.bar { height: 14px; background: var(--track); border-radius: 99px; overflow: hidden; margin: 8px 0 4px; }
.bar > i { display: block; height: 100%; background: var(--accent); border-radius: 99px; }
.ladder { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 8px; }
.ladder span { font: 500 .72rem/1 var(--mono); padding: 4px 6px; border-radius: 6px; background: var(--track); color: var(--muted); }
.ladder span.on { background: var(--accent); color: #fff; }
.figs { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 9.5rem), 1fr)); gap: 12px; }
.fig .v { font: 700 2.5rem/1 var(--head); font-variant-numeric: tabular-nums; }
.fig .l { color: var(--muted); font-size: .78rem; text-transform: uppercase; letter-spacing: .06em; }
.grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr)); gap: 18px; }
.quest { display: grid; grid-template-columns: 28px 1fr auto; gap: 10px; align-items: center; padding: 10px 0; border-top: 1px solid var(--line); }
.quest:first-of-type { border-top: 0; }
.chk { width: 24px; height: 24px; border-radius: 7px; border: 2px solid var(--line); display: grid; place-items: center; font-size: .85rem; }
.quest.done .chk { background: var(--good); border-color: var(--good); color: #fff; }
.quest.done .qn { text-decoration: line-through; color: var(--muted); }
.qd { color: var(--muted); font-size: .85rem; }
.xp { font: 500 .78rem/1 var(--mono); color: var(--accent2); white-space: nowrap; }
.chart { display: grid; grid-template-columns: repeat(14, 1fr); gap: 4px; align-items: end; height: 120px; }
.col { display: grid; align-content: end; height: 100%; }
.col i { display: block; background: var(--accent); border-radius: 4px 4px 0 0; min-height: 2px; }
.col.today i { background: var(--accent2); }
.col b { font: 400 .62rem/1.2 var(--mono); color: var(--muted); text-align: center; margin-top: 4px; white-space: nowrap; overflow: hidden; }
.act { display: flex; gap: 6px; overflow-x: auto; padding-bottom: 4px; }
.actdays { display: grid; grid-template-rows: repeat(7, 16px); gap: 4px; font: .66rem/16px var(--mono); color: var(--muted); }
.actgrid { display: grid; grid-auto-flow: column; grid-template-rows: repeat(7, 16px); grid-auto-columns: 16px; gap: 4px; }
.ad { width: 16px; height: 16px; border-radius: 4px; border: 0; padding: 0; cursor: pointer; }
.ad.a0, .actleg .a0 { background: var(--track); }
.ad.a1, .actleg .a1 { background: color-mix(in srgb, var(--good) 35%, var(--track)); }
.ad.a2, .actleg .a2 { background: color-mix(in srgb, var(--good) 60%, var(--track)); }
.ad.a3, .actleg .a3 { background: color-mix(in srgb, var(--good) 80%, var(--track)); }
.ad.a4, .actleg .a4 { background: var(--good); }
.ad.future { background: transparent; box-shadow: inset 0 0 0 1px var(--line); cursor: default; }
.ad.today { outline: 2px solid var(--accent); outline-offset: 1px; }
.ad.exam { background: var(--accent2); box-shadow: none; }
.ad.pad { visibility: hidden; }
.actfoot { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-top: 8px; font-size: .8rem; }
.actleg { color: var(--muted); display: inline-flex; gap: 3px; align-items: center; }
.actleg i { width: 11px; height: 11px; border-radius: 3px; display: inline-block; }
.badges { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 9.5rem), 1fr)); gap: 10px; }
.badge { border: 1px solid var(--line); border-radius: 12px; padding: 10px; text-align: center; }
.badge .i { display: grid; place-items: center; width: 44px; height: 44px; margin: 2px auto 6px; border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 14%, transparent); color: var(--accent); }
.badge .i svg, .boss .e svg { width: 24px; height: 24px; }
.badge .n { font-weight: 600; font-size: .9rem; }
.badge .d { color: var(--muted); font-size: .76rem; }
.badge .p { font: 500 .72rem/1 var(--mono); color: var(--muted); margin-top: 4px; }
.badge.got { border-color: var(--gold); box-shadow: inset 0 0 0 1px var(--gold); }
.badge:not(.got) .i { background: var(--track); color: var(--locked); }
.boss { display: grid; grid-template-columns: 36px 1fr auto; gap: 10px; align-items: center; padding: 9px 0; border-top: 1px solid var(--line); }
.boss:first-of-type { border-top: 0; }
.boss .e { display: grid; place-items: center; width: 36px; height: 36px; border-radius: 50%; background: var(--track); color: var(--muted); }
.boss .e.defeated { background: color-mix(in srgb, var(--good) 18%, transparent); color: var(--good); }
.boss .e.scraped { background: color-mix(in srgb, var(--accent) 16%, transparent); color: var(--accent); }
.tag { font: 500 .72rem/1 var(--mono); padding: 4px 7px; border-radius: 6px; white-space: nowrap; }
.tag.defeated { background: var(--good); color: #fff; }
.tag.scraped { background: var(--warn); color: #241600; }
.tag.waiting { background: var(--track); color: var(--muted); }
.hp { height: 6px; background: var(--track); border-radius: 99px; overflow: hidden; margin-top: 4px; position: relative; }
.hp i { display: block; height: 100%; background: var(--good); }
.hp .t { position: absolute; top: -2px; bottom: -2px; left: 80%; width: 2px; background: var(--fg); opacity: .6; }
.dom { margin: 8px 0; }
.dom .top { display: flex; justify-content: space-between; gap: 8px; font-size: .9rem; }
.dom .top span { color: var(--muted); font: .78rem var(--mono); white-space: nowrap; }
.rhead { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
.rpct { font: 700 2.8rem/1 var(--head); font-variant-numeric: tabular-nums; }
.rbar { height: 22px; background: var(--track); border-radius: 99px; overflow: hidden; margin: 10px 0 8px; }
.rbar > i { display: block; height: 100%; border-radius: 99px; transition: width .6s; }
.parts { display: flex; flex-wrap: wrap; gap: 8px; }
.part { font-size: .82rem; border: 1px solid var(--line); border-radius: 8px; padding: 5px 9px; }
.part b { font-family: var(--mono); }
.part .qd { font-size: .74rem; }
.ready-top { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr)); gap: 16px; align-items: start; }
.verdict { display: inline-block; font: 700 1.3rem/1 var(--head); padding: 8px 14px; border-radius: 10px; letter-spacing: .04em; }
.verdict.READY { background: var(--good); color: #fff; }
.verdict.ALMOST { background: var(--warn); color: #241600; }
.verdict.NOT { background: var(--bad); color: #fff; }
.big { font: 700 2.4rem/1 var(--head); font-variant-numeric: tabular-nums; }
.checks { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; font-size: .9rem; }
.checks li { display: grid; grid-template-columns: 22px 1fr; gap: 6px; }
.checks .d { color: var(--muted); font-size: .8rem; }
.heatwrap { display: flex; gap: 20px; flex-wrap: wrap; align-items: flex-start; margin-top: 14px; }
.heat { display: grid; grid-template-columns: 2.2rem repeat(var(--cols), 26px) 3rem; gap: 5px; align-items: center; }
.heat .h { font: 500 .72rem/1 var(--mono); color: var(--muted); text-align: center; }
.heat .rl { font: 600 .82rem/1 var(--mono); }
.heat .ds { font: 600 .82rem/1 var(--mono); text-align: right; }
.sq { width: 26px; height: 26px; border-radius: 6px; border: 0; padding: 0; cursor: pointer; }
.sq:focus-visible, .sq.sel { outline: 2px solid var(--fg); outline-offset: 2px; }
.sq.green { background: #3fae6c; } .sq.amber { background: #e9a23b; } .sq.red { background: #d9534f; }
.sq.none { background: var(--track); }
.sq.empty { background: transparent; cursor: default; }
.detail { flex: 1 1 16rem; min-width: 0; font-size: .88rem; border-left: 3px solid var(--line); padding-left: 12px; min-height: 4rem; }
.detail b { font-family: var(--mono); }
.detail .qd { margin-top: 2px; }
.legend { display: flex; gap: 12px; flex-wrap: wrap; color: var(--muted); font-size: .8rem; margin-top: 10px; }
.legend i { display: inline-block; width: 12px; height: 12px; border-radius: 3px; vertical-align: -2px; margin-right: 4px; }
.focus { counter-reset: f; list-style: none; margin: 0; padding: 0; }
.focus li { display: grid; grid-template-columns: 3.2rem 1fr; gap: 10px; padding: 8px 0; border-top: 1px solid var(--line); }
.focus li:first-child { border-top: 0; }
.focus .id { font: 700 1rem/1.4 var(--mono); }
.rules { color: var(--muted); font-size: .85rem; margin: 0; padding-left: 18px; }
footer { color: var(--muted); font-size: .8rem; }
@media (max-width: 520px) { .hero { grid-template-columns: 1fr; } .chart b { display: none; } }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>__TITLE__</h1>
    <p class="sub" id="countdown"></p>
  </header>

  <section class="figs" id="figs" aria-label="Stats"></section>

  <section class="card" aria-label="Exam readiness">
    <div class="rhead"><h2 style="margin:0">Exam readiness</h2><span class="rpct" id="rpct"></span></div>
    <div class="rbar" role="progressbar" aria-valuemin="0" aria-valuemax="100" id="rbar"><i></i></div>
    <div class="parts" id="parts"></div>
    <p class="sub" style="font-size:.8rem">Full bar = exam-ready: every unit taught, strength ≥ 75, no red units, latest mock ≥ 80%, no 🔥. My judgment rule, not a prediction; only the vendor's official practice test is calibrated.</p>
    <div class="heatwrap"><div class="heat" id="heat" role="grid" aria-label="Strength by domain and unit"></div>
      <div class="detail" id="detail" aria-live="polite"><span class="qd">Hover or tap a square for detail.</span></div></div>
    <div class="legend"><span><i style="background:#3fae6c"></i>Strong ≥ 80</span><span><i style="background:#e9a23b"></i>Shaky 60-79</span>
      <span><i style="background:#d9534f"></i>Weak &lt; 60</span><span><i style="background:var(--track)"></i>Not taught</span>
      <span>Strength = 60% quiz + 40% spaced-review hit rate (an open 🔥 caps it at 59)</span></div>
  </section>


  <div class="grid2">
    <section class="card"><h2>Today's quests</h2><div id="quests"></div></section>
    <section class="card"><h2>Study activity</h2>
      <div class="act"><div class="actdays"><span>Mon</span><span></span><span>Wed</span><span></span><span>Fri</span><span></span><span>Sun</span></div>
        <div class="actgrid" id="actgrid"></div></div>
      <div class="actfoot"><span class="qd" id="actinfo"></span>
        <span class="actleg">Less <i class="a0"></i><i class="a1"></i><i class="a2"></i><i class="a3"></i><i class="a4"></i> More</span></div></section>
  </div>

  <section class="card"><h2>Boss fights (mock exams)</h2><div id="bosses"></div>
    <p class="sub" style="font-size:.82rem">Bar = taught-objective score; the line marks the 80% target.</p></section>

  <section class="card"><h2>Badges</h2><div class="badges" id="badges"></div></section>

  <section class="card"><h2>How XP works</h2><ul class="rules" id="rules"></ul></section>
  <footer>Snapshot built __GENERATED__ from ObjectiveTracker.md and MissLog.md. Re-run <code>python petey/build_game.py</code> to refresh.</footer>
</div>
<script>
const D = __DATA__;
const $ = id => document.getElementById(id);
const el = (t, a = {}, kids = []) => { const e = document.createElement(t);
  for (const [k, v] of Object.entries(a)) k === "text" ? e.textContent = v : e.setAttribute(k, v);
  for (const k of [].concat(kids)) e.append(k); return e; };
// Line icons, 24x24, drawn with currentColor strokes.
const ICONS = {
  dumbbell: "M6.5 7v10M17.5 7v10M3.5 9.5v5M20.5 9.5v5M6.5 12h11",
  target: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 7.5a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9zM12 11.2a.8.8 0 1 0 0 1.6.8.8 0 0 0 0-1.6z",
  layers: "M12 3 3 7.5 12 12l9-4.5L12 3zM3 12l9 4.5 9-4.5M3 16.5 12 21l9-4.5",
  checklist: "M10 6h10M10 12h10M10 18h10M3.5 6l1.5 1.5L7.5 5M3.5 12l1.5 1.5 2.5-2.5M3.5 18l1.5 1.5 2.5-2.5",
  rotate: "M3 12a9 9 0 1 0 2.6-6.4L3 8M3 3v5h5",
  shield: "M12 3l7.5 3v5.5c0 4.6-3.2 8.3-7.5 9.5-4.3-1.2-7.5-4.9-7.5-9.5V6L12 3zM8.5 12l2.5 2.5 4.5-5",
  flame: "M12 21c-3.9 0-6.5-2.7-6.5-6.2 0-3.6 2.9-5.6 3.9-9.3 2.3 1.4 3.4 3.6 3.6 5.6 1-.6 1.6-1.8 1.7-3.1 2.2 1.8 3.8 4.2 3.8 6.8 0 3.5-2.6 6.2-6.5 6.2zM12 21c-1.6 0-2.7-1.1-2.7-2.6 0-1.6 1.4-2.5 2.7-4.2 1.3 1.7 2.7 2.6 2.7 4.2 0 1.5-1.1 2.6-2.7 2.6z",
  mountain: "M2.5 20 9 9l4 6.5 2.5-3.8L21.5 20h-19zM9 9l1.6 2.7",
  sword: "M14.5 3.5H20.5v6L10 20l-2.5-2.5 1.5-1.5L4 11l1.5-1.5L9 13l1.5-1.5L14.5 3.5zM5.5 15.5l3 3M3 21l2.5-2.5",
  map: "M9 4 3 6.5v13.5L9 17.5l6 2.5 6-2.5V4l-6 2.5L9 4zM9 4v13.5M15 6.5V20",
  trophy: "M8 4h8v5a4 4 0 0 1-8 0V4zM8 6H4.5v1.5A3 3 0 0 0 8 10.5M16 6h3.5v1.5a3 3 0 0 1-3.5 3M12 13v4M8.5 20.5h7M10 17h4v3.5h-4z",
  swords: "M4 4l9.5 9.5M4 4h3.5l9 9M16.5 13.5 19 16M20 4l-9.5 9.5M20 4h-3.5l-4 4M7.5 13.5 5 16M3.5 17.5l3 3M17.5 20.5l3-3",
  flag: "M5.5 21V3.5M5.5 4h12l-2.5 4.25L17.5 12.5h-12",
};
const icon = name => { const NS = "http://www.w3.org/2000/svg", s = document.createElementNS(NS, "svg");
  s.setAttribute("viewBox", "0 0 24 24"); s.setAttribute("fill", "none"); s.setAttribute("stroke", "currentColor");
  s.setAttribute("stroke-width", "1.8"); s.setAttribute("stroke-linecap", "round"); s.setAttribute("stroke-linejoin", "round");
  s.setAttribute("aria-hidden", "true");
  const p = document.createElementNS(NS, "path"); p.setAttribute("d", ICONS[name] || ICONS.flag); s.append(p); return s; };

$("countdown").textContent = `${D.daysLeft} days to the exam (${D.exam}). Level up before then.`;
[[D.streak + (D.streak === 1 ? " day" : " days"), "Streak", `best ${D.bestStreak}`],
 ["+" + D.xpToday, "XP today", ""],
 [D.stats.reviews, "Reviews done", ""],
 [D.stats.comebacks, "Comebacks", "missed, then nailed"],
 [D.stats.due, "Reviews due", "the backlog boss"]].forEach(([v, l, n]) =>
  $("figs").append(el("div", {class: "card fig"}, [el("div", {class: "l", text: l}), el("div", {class: "v", text: v}), el("div", {class: "sub", text: n})])));

D.quests.forEach(q => $("quests").append(el("div", {class: "quest" + (q.done ? " done" : "")}, [
  el("div", {class: "chk", text: q.done ? "✓" : ""}),
  el("div", {}, [el("div", {class: "qn", text: q.name}), el("div", {class: "qd", text: q.detail})]),
  el("div", {class: "xp", text: q.xp})])));

const actDefault = `${D.activeDays} study days · exam day in amber. Hover or tap a day.`;
$("actinfo").textContent = actDefault;
D.recent.forEach(r => {
  const desc = r.exam ? `${r.label}: exam day` : r.future ? `${r.label}` :
    `${r.label}: ${r.xp} XP` + (r.reviews ? ` · ${r.reviews} review${r.reviews > 1 ? "s" : ""}` : "") + (r.sessions ? ` · ${r.sessions} objective${r.sessions > 1 ? "s" : ""}` : "") + (r.xp ? "" : " · no study");
  const b = el("button", {type: "button", class: `ad a${r.lvl}` + (r.future ? " future" : "") + (r.today ? " today" : "") + (r.exam ? " exam" : ""),
    title: desc, "aria-label": desc});
  const show = () => { $("actinfo").textContent = desc; };
  b.addEventListener("mouseenter", show); b.addEventListener("focus", show); b.addEventListener("click", show);
  $("actgrid").append(b);
});
$("actgrid").addEventListener("mouseleave", () => { $("actinfo").textContent = actDefault; });

D.bosses.forEach(b => { const hp = el("div", {class: "hp"}, [el("i"), el("span", {class: "t"})]);
  hp.firstElementChild.style.width = (b.taughtPct || 0) + "%";
  const tag = b.result ? el("span", {class: "tag " + b.result, text: b.result === "defeated" ? "DEFEATED" : "SURVIVED"}) : el("span", {class: "tag waiting", text: b.planned});
  $("bosses").append(el("div", {class: "boss"}, [el("div", {class: "e " + (b.result || "")}, [icon(b.taken ? (b.result === "defeated" ? "trophy" : "swords") : "flag")]),
    el("div", {}, [el("div", {text: b.name}), el("div", {class: "qd", text: b.taken ? `Overall ${b.overall} · taught ${b.taught}` : "Not yet fought"}), b.taken ? hp : ""]), tag])); });


D.badges.forEach(b => $("badges").append(el("div", {class: "badge" + (b.got ? " got" : "")}, [
  el("div", {class: "i"}, [icon(b.icon)]), el("div", {class: "n", text: b.name + (b.count > 1 ? ` ×${b.count}` : "")}),
  el("div", {class: "d", text: b.desc}), el("div", {class: "p", text: b.got ? "UNLOCKED" : (b.progress || "locked")})])));

D.rules.forEach(r => $("rules").append(el("li", {text: r})));

const R = D.readiness;
$("rpct").textContent = R.pct + "%";
const fill = $("rbar").firstElementChild; fill.style.width = R.pct + "%";
fill.style.background = R.pct >= 100 ? "var(--good)" : R.pct >= 75 ? "var(--accent)" : "var(--bad)";
$("rbar").setAttribute("aria-valuenow", R.pct);
R.parts.forEach(p => $("parts").append(el("div", {class: "part"}, [el("span", {text: p.name + " "}), el("b", {text: `${p.got}/${p.max}`}), el("div", {class: "qd", text: p.how})])));
const heat = $("heat"); heat.style.setProperty("--cols", R.maxCols);
heat.append(el("span"));
for (let i = 0; i < R.maxCols; i++) heat.append(el("span", {class: "h", text: i + 1}));
heat.append(el("span", {class: "h", text: "avg"}));
const showUnit = (u, r, btn) => { document.querySelectorAll(".sq.sel").forEach(s => s.classList.remove("sel")); btn.classList.add("sel");
  const d = $("detail"); d.innerHTML = "";
  d.append(el("div", {}, [el("b", {text: u.id}), " " + u.scope]));
  d.append(el("div", {class: "qd", text: u.score == null ? "Not taught yet" :
    [`strength ${u.score}`, u.quiz != null ? `quiz ${u.quiz}/7` : "", u.due ? `${u.due} review${u.due > 1 ? "s" : ""} due` : "",
     u.open ? `${u.open} open MissLog items` : "", u.fire ? `${u.fire} 🔥` : ""].filter(Boolean).join(" · ")}));
  d.append(el("div", {class: "qd", text: `D${r.n} ${r.name} (${r.weight}% of exam): ${r.taught}/${r.of} taught` + (r.strength == null ? "" : `, avg ${r.strength}`)}));
};
R.rows.forEach(r => {
  heat.append(el("span", {class: "rl", text: "D" + r.n, title: `${r.name} · ${r.weight}% of exam`}));
  for (let i = 0; i < R.maxCols; i++) { const u = r.units[i];
    if (!u) { heat.append(el("span", {class: "sq empty"})); continue; }
    const b = el("button", {class: "sq " + (u.band || "none"), type: "button",
      "aria-label": `${u.id}: ` + (u.score == null ? "not taught" : `strength ${u.score}`),
      title: `${u.id} · ` + (u.score == null ? "not taught" : `strength ${u.score}`)});
    b.addEventListener("mouseenter", () => showUnit(u, r, b)); b.addEventListener("focus", () => showUnit(u, r, b));
    b.addEventListener("click", () => showUnit(u, r, b));
    heat.append(b); }
  heat.append(el("span", {class: "ds", text: r.strength == null ? "–" : r.strength,
    style: "color:" + (r.band ? `var(--${{green: "good", amber: "warn", red: "bad"}[r.band]})` : "var(--muted)")}));
});
</script>
</body>
</html>
"""


def main():
    global HERE, TODAY, EXAM, PREP_START, EXAM_NAME, DOMAINS
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=str(ROOT), help="folder holding exam.json, ObjectiveTracker.md, MissLog.md")
    HERE = Path(ap.parse_args().dir).resolve()
    cfg_path = HERE / "exam.json"
    if not cfg_path.exists():
        sys.exit(f"{cfg_path} not found. Run /init-exam in Claude Code first (or pass --dir examples/sample).")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    TODAY = dt.date.fromisoformat(cfg["today"]) if cfg.get("today") else dt.date.today()  # "today" pins the sample
    EXAM = dt.date.fromisoformat(cfg["exam_date"])
    PREP_START = dt.date.fromisoformat(cfg["day0"])
    EXAM_NAME = cfg.get("exam_name", "Exam")
    tracker = (HERE / "ObjectiveTracker.md").read_text(encoding="utf-8")
    DOMAINS = [(d["n"], d["name"], weight_pct(d["weight"])) for d in parse_domains(tracker)]
    if not DOMAINS:
        sys.exit("No '## Domain N: Name (W%)' sections found in ObjectiveTracker.md.")
    build()


if __name__ == "__main__":
    main()
