# Miss Log: Example Cloud Fundamentals (EX-100)

> **SAMPLE.** Made-up entries for a fictional exam, to show the format and feed the sample dashboard. Not real exam or practice-bank content.

**Status key:** 🆕 new · 🔁 reviewed once · ✅ solid (2+ correct spaced reviews) · 🔥 confident-wrong · ⚠️ source disagrees with the docs.

**Spaced review:** 1 → 3 → 7 → 14 days; a wrong review resets to 1 day.

---

### ✅ Who patches the guest OS on a rented virtual machine?
**Objective:** 1.1 · **Source:** session quiz Q3 · **Logged:** 2026-10-01 · **Confidence:** 2
**Correct:** The customer. The provider patches the host and hypervisor.
**Why:** With infrastructure as a service, everything from the OS up is yours. The provider only takes the OS over in managed services.
**Hook:** "If you can log in to it, you patch it."
**Miss type:** taught but not recalled
**Review log:** 2026-10-02 ✅ (conf 3) — next review 2026-10-05
**Review log:** 2026-10-05 ✅ (conf 3) — next review 2026-10-12
**Review log:** 2026-10-12 ✅ (conf 3) — next review 2026-10-26

### 🔁 Zone vs region failure scope
**Objective:** 1.2 · **Source:** session quiz Q5 · **Logged:** 2026-10-02 · **Confidence:** 2
**Correct:** Spreading across zones survives a data-centre failure; surviving a regional outage needs a second region.
**Why:** Zones are isolated sites within one region. A regional event can take out every zone in it.
**Hook:** Zones = rooms in one house; regions = different houses.
**Miss type:** taught but not recalled
**Review log:** 2026-10-03 ✅ (conf 2) — next review 2026-10-06
**Review log:** 2026-10-06 ❌ (conf 2) — next review 2026-10-07
**Review log:** 2026-10-07 ✅ (conf 3) — next review 2026-10-14

### 🆕🔥 Scaling out vs scaling up
**Objective:** 1.3a · **Source:** session quiz Q2 · **Logged:** 2026-10-03 · **Confidence:** 3
**Correct:** Adding more instances behind a load balancer is scaling *out* (horizontal).
**Why:** Up/down = a bigger or smaller machine; out/in = more or fewer machines. Answered "up" at confidence 3.
**Hook:** Out = more of them. Up = bigger one.
**Miss type:** taught but not recalled
**Review log:** 2026-10-04 ❌ (conf 3) — next review 2026-10-05
**Review log:** 2026-10-05 ✅ (conf 2) — next review 2026-10-08
**Review log:** 2026-10-08 ❌ (conf 3) — next review 2026-10-09

### 🔁 Elasticity vs scalability wording
**Objective:** 1.3a · **Source:** fact card recall · **Logged:** 2026-10-03 · **Confidence:** 1
**Correct:** Elasticity = scaling automatically with demand, both ways. Scalability = being able to grow at all.
**Why:** Questions that say "automatically" or "match demand" want elasticity.
**Hook:** Elastic snaps back.
**Miss type:** not taught (vocabulary)
**Review log:** 2026-10-04 ✅ (conf 2) — next review 2026-10-07
**Review log:** 2026-10-07 ❌ (conf 2) — next review 2026-10-08
**Review log:** 2026-10-08 ✅ (conf 2) — next review 2026-10-11

### ✅ RPO vs RTO
**Objective:** 1.3b · **Source:** session quiz Q6 · **Logged:** 2026-10-03 · **Confidence:** 2
**Correct:** RPO = how much data you can lose (time since the last good copy); RTO = how long until you're back up.
**Why:** The distractor swapped them.
**Hook:** Point = data point; Time = clock to recovery.
**Miss type:** reading slip
**Review log:** 2026-10-04 ✅ (conf 3) — next review 2026-10-07
**Review log:** 2026-10-07 ✅ (conf 3) — next review 2026-10-14

### 🔁 Least privilege applied to a temporary task
**Objective:** 2.1a · **Source:** mock 1 Q12 · **Logged:** 2026-10-09 · **Confidence:** 1
**Correct:** Grant a time-limited role for the task, not a permanent admin role.
**Why:** Least privilege covers duration as well as scope.
**Hook:** Smallest key, shortest time.
**Miss type:** taught but not recalled
**Review log:** 2026-10-10 ✅ (conf 2) — next review 2026-10-13

### 🆕🔥 MFA factor categories
**Objective:** 2.1b · **Source:** session quiz Q4 · **Logged:** 2026-10-06 · **Confidence:** 3
**Correct:** A password plus a security question is still *one* factor (both are something you know).
**Why:** MFA needs different categories: know / have / are.
**Hook:** Two secrets in your head are still one head.
**Miss type:** taught but not recalled
**Review log:** 2026-10-07 ❌ (conf 3) — next review 2026-10-08
**Review log:** 2026-10-08 ✅ (conf 2) — next review 2026-10-11
**Review log:** 2026-10-11 ❌ (conf 3) — next review 2026-10-12

### 🆕 Federation vs single sign-on
**Objective:** 2.1b · **Source:** session quiz Q6 · **Logged:** 2026-10-06 · **Confidence:** 2
**Correct:** Federation trusts an identity provider in *another* organisation; SSO is one sign-in across many apps.
**Why:** They often appear together but answer different questions.
**Hook:** Federation crosses a border.
**Miss type:** taught but not recalled

### 🆕 Customer-managed vs provider-managed keys
**Objective:** 2.2 · **Source:** session quiz Q7 · **Logged:** 2026-10-07 · **Confidence:** 2
**Correct:** Customer-managed keys let you rotate and revoke the key yourself.
**Why:** Both encrypt at rest; the difference is who controls the key's lifecycle.
**Hook:** Your key, your rotation.
**Miss type:** taught but not recalled
**Review log:** 2026-10-08 ✅ (conf 2) — next review 2026-10-11
**Review log:** 2026-10-11 ❌ (conf 2) — next review 2026-10-12

### 🔁 Archive tier retrieval time
**Objective:** 3.1 · **Source:** fact card recall · **Logged:** 2026-10-10 · **Confidence:** 1
**Correct:** Archive tiers trade cheap storage for slow (hours) and charged retrieval.
**Why:** The picked option assumed archive reads were instant.
**Hook:** Archive = the warehouse off-site: cheap shelf, slow truck.
**Miss type:** taught but not recalled
**Review log:** 2026-10-11 ✅ (conf 2) — next review 2026-10-14

### 🆕 Reserved vs on-demand pricing
**Objective:** 4.1 · **Source:** mock 1 Q30 (untaught objective) · **Logged:** 2026-10-09 · **Confidence:** 1
**Correct:** Steady, predictable workloads suit a reservation; spiky or short ones suit on-demand.
**Why:** A reservation trades commitment for a discount.
**Hook:** Commit for a discount.
**Miss type:** not taught
