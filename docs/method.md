# The Cert PT method, and why each step exists

Cert PT is a study loop, not a question bank. Claude Code runs the loop. The rules it follows are in [`petey/method.md`](../petey/method.md). This page explains the reasoning behind them.

Most of the rules came from things going wrong while I studied for one exam, which I then fixed. Where a step rests on well-known learning research, that's named. Where it came from experience, that's said too.

**How it went:** I used this method for SnowPro Core (COF-C03): about five and a half weeks of study, including eleven days lost to illness, and a first-attempt pass at **805/1000** (pass mark 750). That's one person on one exam, so read it as a sign the method can work, not proof that it does.

## The shape of a session

```
Warm-up (spaced review) → Orient + guess → Teach → Fact card → Explain it back
→ Quiz (7 + 3 interleaved, with confidence) → Repair (→ MissLog) → Close out
```

One session covers one objective from the official guide (big objectives are split a/b) and takes about 60-80 minutes.

## Step by step

### 0. Warm-up: spaced review
**What:** 3-5 recall questions, before any new material, drawn from misses that are due and from older objectives.
**Why:** retrieval spread out over time beats rereading. This is the *spacing* and *testing* effects (e.g. Roediger & Karpicke, 2006). Doing it first, while you're fresh, makes sure it happens.
**Lessons:**
- At 3-5 reviews a day, a backlog of ~50 early misses was never reached, and many were missed again on a retake. Backlogs are now cleared at ~10 a day.
- "Most overdue first" pulled in misses from objectives that hadn't been taught yet, so the warm-up asked about things I'd seen once in a pre-study mock. It also made the backlog look about twice its real size. Misses on untaught objectives are now *parked* until their objective is taught.
- Exact names (functions, parameters, views) asked as free recall felt impossible and didn't match the exam, which is multiple choice. Names are now tested by recognition: pick the real one from plausible fakes, and recall only what it does.

### 1. Orient + guess first
**What:** one plain sentence per guide bullet, each mapped to the platform you already know. Then 2-3 unscored predictions on the tricky points.
**Why:** experienced people learn a new platform fastest as *differences* from one they know. Guessing before being told primes you to notice the answer (the *pretesting* effect). The guesses aren't scored, so a wrong one costs nothing.
**Lesson:** analogies have to come from a platform you actually know, and they have to be current. An out-of-date analogy teaches the wrong thing twice.

### 2. Teach, before any testing
**What:** short chunks with a check question after each, built from the docs overview page for each feature. Key claims cite the official docs URL.
**Why:** a cold diagnostic quiz on unfamiliar material measures nothing, because every answer is a guess, and it's demoralising. That was the first thing I dropped.
**Lessons:**
- When the tutor chose what to cover by judgment, about 1 in 3 questions on *taught* objectives in independent checks asked about facts it had never covered. Building coverage from the docs overview fixed most of that.
- **Adjacent rules interfere.** Teaching an exception (a case where the provider pays) one chunk after the normal rule (the consumer pays) flipped the normal rule within the hour. Exceptions now sit next to their rule in a 2-row table, and recurring questions like "who pays?" get one table across all the related features.
- **Name-decoding helps, up to a point.** Breaking a command name into parts (scope · subject · history) eliminates some options, but it usually leaves two near-identical names. A fake built from a familiar naming pattern beat a real name I'd met twenty minutes earlier. Teaching now contrasts each new name with the fake the pattern would suggest.
- Tutor notes drift. Two facts in the miss log turned out to be wrong or out of date when the docs were re-fetched weeks later. Overview pages are re-fetched at teach time, and old notes are re-checked before reuse.
- Long side discussions mid-teach meant a card was never actually read, and the check after it failed for that reason. After a detour, the card is shown again.

### 2b. Fact card
**What:** a top-up of 3-4 facts the teach didn't reach (defaults, limits, editions, the vocabulary questions use), each explained in two lines: what it does, and when you'd use it. Then 2-3 recall questions.
**Why:** exams test exact facts as well as concepts.
**Lessons:**
- A card that just listed feature names didn't teach anything. A name gives you nothing to reason with.
- Testing a fact before it had been taught repeated the cold-quiz problem. Nothing is tested before it has been on a card.
- Cards can bloat a session, so there's a cap of one per session.

### 3. Explain it back
**What:** summarise the objective from memory in a few sentences.
**Why:** free recall shows the gaps that recognition hides. It takes two minutes.

### 4. Quiz with confidence ratings
**What:** 10 questions in the style of the official sample questions (scenario, constraint, near-miss distractors): 7 on today's objective, plus 3 interleaved from earlier ones. You answer with **confidence 1-3**.
**Why:**
- *Interleaving* tests whether you can tell topics apart, which is what the real exam asks of you.
- Confidence ratings separate "didn't know" from "thought I knew". A **confident wrong answer** is the most dangerous kind on exam day, and research on the *hypercorrection effect* suggests it's also the most fixable once corrected (Butterfield & Metcalfe, 2001). These get flagged 🔥 and extra repair.

**Lessons:**
- Questions worded like the teaching test recognition of the tutor's phrasing, not recall. Quizzes now use the docs' terms.
- Some of the tutor's "wrong" options turned out to be valid. Every distractor is now checked against the docs before it's asked.
- Stems can be wrong or give the answer away too: one premise was wrong on checking the docs, one phrase ("before re-running") cued a distractor's job, and one follow-up ("what does it do?") told me a name was real. Stems now get the same check as the options.
- Once, the next question appeared before the last answer had been marked. Every answer is now marked before moving on.
- A check asked for two reasons; I gave two valid ones and was told I'd "missed the third". Grading now covers only what the question asked.
- The confidence scale shifted partway through (1 came to mean any toss-up, not just a pure guess), which made confidence counts from before and after the change look like a drop in certainty. Keep the scale fixed, or don't compare across the change.

### 5. Repair
**What:** for each miss, name the misconception, say why the right answer is right and why each distractor is wrong, then give a variant question. Log it to the MissLog.
**Why:** a miss is only useful if it changes your mental model and comes back for review.
**Lessons:**
- Classify every miss as *not taught*, *taught but not recalled*, *reading slip* or *entry slip*. Without that, it's easy to blame yourself for a teaching gap, or to treat a slip as a knowledge gap.
- A repair taught a rule for one cloud provider without saying loudly that another provider worked differently. That evening I applied the rule where it doesn't hold. A repair now states a rule's exception in the same breath, and the variant question tests it.
- A variant question tested the half of a rule the repair hadn't shown. Variants now test only what the repair showed.

### 6. Close out
**What:** update the tracker, add a "core rules + exceptions + one picture" block to QuickRef, note any method lesson, and rebuild the dashboard.
**Why:** rule-heavy topics feel like "a ton of overlapping rules". Squeezing each objective into a few rules plus their exceptions makes it reviewable, and exam questions mostly bite on the exceptions.

## Stamina: when to stop

**Rule:** at most ~3 sessions a day, with real breaks. Stop after two if the second ends late. In a third session, a shaky explain-back means stop before the quiz.
**Lesson:** sessions taught late in the evening scored fine on the day but didn't stick. The next morning I recalled almost none of one late session's rules. One fatigue-wrecked session was paused at 0/2. After a two-week gap, a recap card and a fresh quiz got 6/7, and both earlier misses were answered right: they had been fatigue, not gaps. Tired sessions now count as partly taught and get a recap and a fresh quiz rather than a resume.

## Hot topics: the guide is broader than its wording

**Rule:** collect the topics that pass reports mention, map each to the guide bullet it fits, and give each at least one fact card.
**Lesson:** this rule came from the exam itself. The real exam had several questions on a feature (Snowflake's Data Metric Functions) that I'd never studied. The study guide doesn't name it, and "teach only guide objectives" kept it out of every session. Yet my study plan listed it **first** among hot topics from pass reports, and nothing turned that list into teaching. It cost points, though not the pass. A topic the guide doesn't name can still be tested under a broader bullet (here, governance or data quality). So "not named in the guide" now means "check the hot topics", not "skip".

## The final week: retrieval mode

**Rule:** once everything is taught, no new teaching. Sessions are warm-up → timed questions with confidence → fast repair, with variant questions only for taught-but-forgotten misses.
**Lesson:** the first mock after finishing all the objectives scored *lower* on taught material than the one before. About half the misses were facts I'd been taught and had on my QuickRef but couldn't recall 2-4 weeks later, mostly from objectives whose reviews had fallen in the illness gap. More teaching wouldn't fix that; more retrieval would. A go/no-go rule set *before* the last mock kept the sit-or-reschedule decision honest.

## The miss log and spaced review

Every miss, and every correct answer at confidence 1, becomes an entry with a reason, a memory hook and a review log. It's re-tested at **1 → 3 → 7 → 14 days**. A wrong review resets it to 1 day. Two correct spaced reviews make it ✅ solid. Warm-ups take 🔥 confident-wrong entries first.

## Fact-checked against the official docs

The tutor cites the official docs for key claims, keeps a table of **renamed products** (old names creep in from training data and outdated banks), and flags any practice-bank answer that disagrees with the docs (⚠️). **No link means unverified.** It never claims a topic is "heavily tested" without saying why. Nobody, including the tutor, has real exam statistics.

## Measuring progress honestly

- **Practice banks are weak signals.** They can lag the current exam version, reuse questions across attempts, or contain outdated keys. Score them by official objective (taught / untaught / doubtful key) and use unseen questions.
- **State sample sizes.** Don't draw conclusions from 3-4 questions.
- **Leading indicators** are checked at the end of each domain: retention (warm-up hit rate), transfer (interleaved score), calibration (accuracy at confidence 3), an independent mock on taught objectives, reading slips, and pace.
- The **official practice test**, where one exists, is the only calibrated readiness signal. In my case the official practice test, a third-party bank and a run of unannounced mixed questions all landed at ~70-78%, and the real result was 805/1000. "Feels easier" didn't change the estimate. Agreement between independent signals did.

## Exam-day tactics that came out of the miss log

- Name the qualifiers (edition, default vs maximum, object type) before reading the options.
- Only change an answer if you can name the fact that makes your first choice wrong. Second-guessing cost a correct answer more than once.
- Defaults are often not round numbers. When torn between a round number and an odd one, the round one is often the distractor.
- On choose-two questions, say "I need two" before reading the options. Sending one answer was a repeated entry slip.

## References

- Roediger, H. L., & Karpicke, J. D. (2006). Test-enhanced learning: Taking memory tests improves long-term retention. *Psychological Science*, 17(3).
- Butterfield, B., & Metcalfe, J. (2001). Errors committed with high confidence are hypercorrected. *Journal of Experimental Psychology: Learning, Memory, and Cognition*, 27(6).
- Cepeda, N. J., et al. (2006). Distributed practice in verbal recall tasks: A review and quantitative synthesis. *Psychological Bulletin*, 132(3).
