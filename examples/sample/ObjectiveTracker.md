# Objective Tracker: Example Cloud Fundamentals (EX-100)

> **SAMPLE.** A fictional exam with made-up progress, to show the file format and feed the sample dashboard. Not real exam content.

**Status:** ⬜ not started · 🔵 in progress (paused, see Resume note) · 🟡 taught, but quiz < 6/7 or an unresolved 🔥 · ✅ quiz ≥ 6/7 and no unresolved 🔥
**Quiz (/7)** = score on the 7 questions for that objective (add `(+N/3 interleaved)` for the other 3). **🔥** = confident-wrong count in that session.

## Daily schedule

13 sessions over 17 days, one a day with a double on Sat 3 Oct. Mocks Oct 21–27, buffer Oct 28–29, light day Oct 30, exam Sat Oct 31.

| Date | Session(s) | Notes |
|---|---|---|
| 2026-10-01 Thu | 1.1 | |
| 2026-10-02 Fri | 1.2 | |
| 2026-10-03 Sat | 1.3a + 1.3b | Double |
| 2026-10-05 Mon | 2.1a | |
| 2026-10-06 Tue | 2.1b | |
| 2026-10-07 Wed | 2.2 | |
| 2026-10-08 Thu | 2.3 | Then mock 1 |
| 2026-10-10 Sat | 3.1 | |
| 2026-10-12 Mon | 3.2 | Paused mid-session |
| 2026-10-13 Tue | 3.3 | Missed (no session) |
| 2026-10-15 Thu | 4.1 | |
| 2026-10-17 Sat | 4.2 | Then mock 2 |
| 2026-10-21 Wed → | Mock phase | See StudyPlan.md |

## Are we on track?

| Checkpoint | Date | Retention | Transfer | Calibration | Independent check | Verdict |
|---|---|---|---|---|---|---|
| End of Domain 1 | 2026-10-03 | 🟡 70% (7/10) | ✅ 3/3 avg | ✅ 1 🔥 | n/a | On track |
| End of Domain 2 | 2026-10-08 | ✅ 80% (8/10) | ✅ 2.5/3 avg | 🟡 1 🔥 open | 78% on taught objectives (mock 1, 40 Qs) | On track; drill 2.1b |
| End of Domain 3 | 2026-10-13 | | | | | |
| End of Domain 4 | 2026-10-17 | | | | | |

## Mock exams

Full-length practice exams, scored by official objective (taught / untaught, checked against the docs). `build_game.py` reads this table.

| Mock | Planned | Taken | Overall | Taught | Untaught | Notes |
|---|---|---|---|---|---|---|
| Mock 1 | 2026-10-09 | 2026-10-09 | 28/40 | 21/27 | 7/13 | SAMPLE, after Domain 2 |
| Mock 2 | 2026-10-18 | | | | | After Domain 4 |
| Official practice test | 2026-10-22 | | | | | The calibrated readiness signal |

## Resume note

**⏸ PAUSED: 3.2 (Mon Oct 12).** Reached step 2, teach chunk 2 of 3. Next on resume: chunk 3, fact card, explain-back, quiz.

## Domain 1: Cloud concepts (24%)

| # | Session scope (from guide) | Planned | Prior misses | Status | Quiz (/7) | 🔥 | Hands-on | Date |
|---|---|---|---|---|---|---|---|---|
| 1.1 | Service models; shared responsibility | 2026-10-01 | 0 | ✅ | 7/7 | 0 | | 2026-10-01 |
| 1.2 | Regions, zones, edge locations | 2026-10-02 | 0 | ✅ | 6/7 (+3/3 interleaved) | 0 | | 2026-10-02 |
| 1.3a | Scaling and elasticity | 2026-10-03 | 0 | 🟡 | 5/7 (+3/3 interleaved) | 1 | | 2026-10-03 |
| 1.3b | High availability and disaster recovery | 2026-10-03 | 0 | ✅ | 6/7 (+3/3 interleaved) | 0 | | 2026-10-03 |

## Domain 2: Security and identity (30%)

| # | Session scope (from guide) | Planned | Prior misses | Status | Quiz (/7) | 🔥 | Hands-on | Date |
|---|---|---|---|---|---|---|---|---|
| 2.1a | Identities, roles, least privilege | 2026-10-05 | 0 | ✅ | 7/7 (+2/3 interleaved) | 0 | | 2026-10-05 |
| 2.1b | Authentication methods; MFA; federation | 2026-10-06 | 0 | 🟡 | 4/7 (+3/3 interleaved) | 1 | | 2026-10-06 |
| 2.2 | Encryption at rest and in transit; key management | 2026-10-07 | 0 | ✅ | 6/7 (+3/3 interleaved) | 0 | | 2026-10-07 |
| 2.3 | Network controls; logging and monitoring | 2026-10-08 | 0 | ✅ | 6/7 (+2/3 interleaved) | 0 | | 2026-10-08 |

## Domain 3: Storage and data services (26%)

| # | Session scope (from guide) | Planned | Prior misses | Status | Quiz (/7) | 🔥 | Hands-on | Date |
|---|---|---|---|---|---|---|---|---|
| 3.1 | Object, block and file storage; storage tiers | 2026-10-10 | 0 | ✅ | 6/7 (+3/3 interleaved) | 0 | | 2026-10-10 |
| 3.2 | Relational vs non-relational databases | 2026-10-12 | 0 | 🔵 | | | | 2026-10-12 |
| 3.3 | Backups, snapshots, data lifecycle | 2026-10-13 | 0 | ⬜ | | | | |

## Domain 4: Billing and support (20%)

| # | Session scope (from guide) | Planned | Prior misses | Status | Quiz (/7) | 🔥 | Hands-on | Date |
|---|---|---|---|---|---|---|---|---|
| 4.1 | Pricing models; cost tools and budgets | 2026-10-15 | 0 | ⬜ | | | | |
| 4.2 | Support plans; service level agreements | 2026-10-17 | 0 | ⬜ | | | | |
