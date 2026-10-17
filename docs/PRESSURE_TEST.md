# Pressure test: KMS Video Engine plan v1

This tests the plan in `KMS_VIDEO_ENGINE_PLAN.md` (2026-10-17). It checks the plan against the SSS Mistakes & Lessons Log, the KMS Campaign Mistakes & Lessons Log, Client Blueprint 06/07, and KMS 02 Offers & Pricing. The fixes are already applied to the plan as v2.

## 1. Assumptions

V = verified in a source. G = guessed.

| # | Assumption | V/G | Evidence or risk |
|---|---|---|---|
| 1 | rough-cut v1, color-grade and Resolve EDL builder exist | V | Notion Team Skills DB; scripts downloaded |
| 2 | They run end to end on the Mac today | **G** | Not seen running. Scripts are only on the Mac |
| 3 | lav-sync, handoff-check, content-strategist and engine.py exist locally | V (referenced) / G (working) | Paths cited in Notion; not inspected |
| 4 | Notion pipeline cards are the integration point | V | Steal Loop writes cards to the SYD and GRS pipelines |
| 5 | What to make comes from a brief | **Wrong** | The assignment is the **07 slot map** plus the **06 offer**. Template read order: "07 first… because it is the assignment" |
| 6 | One generic cut skill fits all formats | **G, likely wrong** | Formats differ in runtime (8–12s, 35–45s, 10–12 min), cut rules, audio spec and tier inclusions |
| 7 | Claude vision can reliably judge hook, brand and wrong-location footage | **G** | No test yet. Same family as the failed AI classifier (KMS log, 08-13) |
| 8 | A clip manifest can be built by extending sort-footage | **G, risky** | Logged failure: "AI sorter files a clip by one mid-clip frame" (KMS 08-13). Integrity check "that lies" (KMS 08-12) |
| 9 | Past jobs have raw + brief + FINAL for replay | **G** | Finals exist; matching briefs and raw sets are unconfirmed |
| 10 | Frame.io is a live feedback channel | **G, likely wrong** | Feedback today is Loom. No Frame.io mail in Gmail. f.io appears only in older Asana threads |
| 11 | Safe zone = 540px | **G, wrong** | The logged rule is: text and faces inside **y 285–1635**, clear of the bottom 250px, with a rendered overlay check (SSS 10-09) |
| 12 | 90-day exclusivity window | **G** | Number invented. A business call |
| 13 | Gates reduce effort for Syd | **G** | Syd "hates back and forth" (KMS 08-12). Four gates per job could add effort |
| 14 | The library can be indexed in place | **G** | Dropbox: renaming synced folders forces a re-upload. 3TB limit already hit |
| 15 | Client data stays isolated | V | Beacon rule: "client data never crosses between clients" |

## 2. Logic gaps

1. **"Rules aren't written down" does not mean "the polisher can check them."** About 40% of the checks are [V] judgments with unknown accuracy. The polisher has to report its confidence and be calibrated on the replay set before anyone trusts it.
2. **brief-builder had no upstream source.** It needs to read 07 (slot: stage, pillar, format, rotation week) and 06 (offer, CTA strength, close). It should then write the funnel tag back to the Content Pipeline row. Without the tag, Sprout can't count the mix.
3. **One story-cut for every format contradicts the evidence.** See §7, format families.
4. **footage-matcher trusts an index built by the classifier the logs say failed.** Coverage claims from the index are the exact logged failure ("transcript hit counts are a search index, never a coverage claim").
5. **Human finals are not ground truth.** The finals include mistakes that were sent back. The replay score has to weight *approved and performed* edits, using the monthly content review.
6. **The editor-shadow phase assumes editors' hours are still budgeted.** No hours field exists in KMS Asana, so the cost comparison can't be measured as specced.

## 3. Pre-mortem: it is 2026-11-17 and this failed

**The most likely cause** has already happened once, in the SSS log on 2026-10-05: *"Content ideation engine built in May, never scheduled, never ran."* That engine was scoped too broadly, nothing checked that it ran, and nobody depended on it. The v1 plan repeats every one of those conditions:
- 10 skills
- 6 phases
- no first real job
- no run log anyone sees off the Mac

**Runner-up:** an index or classifier claim treated as truth, e.g. "no CTA footage exists" (KMS log, 08-13, three rows).

**Fixes applied now:**
- **P0 is now a vertical slice.** One real GRS reel card goes from 07 slot → brief → existing rough-cut → polisher → feedback carry-forward → Syd, within week 1. Nothing counts as "built" until it has run on a paying job.
- **Every run logs** to `RUNS.log` in Dropbox. **Lindsey checks it every Monday**, the same proven pattern as beacon-engine-weekly.
- **Something real depends on it from day one:** GRS slot-map reels, which run on a weekly cadence.
- **Index output is labelled `PROVISIONAL`.** It is sampled at several points per clip, never one mid-clip frame. Coverage comes only from a full-shoot selection sheet. "Missing footage" claims need a full audio pass plus a check of every folder first.
- **Integrity checks** count every file type, including sidecars, and write an inode manifest before any move. The library is never renamed in place: the manifest is a sidecar file, so the Dropbox sync is untouched.

## 4. Simplest version that still gets the result

**Keep:**
1. **Format profiles** (§7). This is the biggest lever on error rate.
2. **Slot→brief.** It reads 07 and 06 and writes a one-screen brief. KMS 08-13: "A brief is instructions… Cap it at one screen."
3. **The existing rough-cut**, driven by the format profile.
4. **Polisher**, using the format's subset of checks.
5. **Carry-forward note tracker:** every Loom or Asana note from every draft gets re-checked on each new draft.

**Cut or defer:**

| Item | Decision |
|---|---|
| video-director orchestrator | Defer. One command per card for now |
| hook-lab and beat-map as separate skills | Fold in as steps of the short-form family |
| Full library manifest | Defer. Do the GRS zone only (317 files) |
| Zone grants and the exclusivity ledger | Defer. Only a reuse ledger for now |
| Gate-graduation metrics | Defer |
| Frame.io migration | Cut |
| Rule auto-promotion | Manual: Syd says "remember this", and the rule is added with its source tag |

That takes it from 10 skills to **3 skills plus N format profiles**.

## 5. What the plan touches downstream that it never mentioned

- **Lindsey:**
  - Owns Asana, Sprout and approvals, so she becomes the run-log checker.
  - Every published reel needs its Sprout funnel tag, or the 07 mix can't be counted.
- **Editors:**
  - Kavya and Teknikoz ($25–35/hr contracts, with late-penalty redlines in draft). Shadow mode changes their volume and income, so it needs a conversation before rollout, not after.
- **Clients:**
  - Approvals go out via Drive with the subject "Action required", and only Syd sends.
  - Hold every asset when a property isn't show-ready (KMS 09-16).
  - GRS Palm Deck: "Hold all assets."
- **Blueprint:**
  - Read **07** (slot) and **06** (offer, CTA strength, close).
  - Never write individual pieces into 06 or 07. Write them to the Content Pipeline row.
- **Money:**
  - **Tier inclusions limit what the engine may do.** CPR lesson, 10-03: Premium tier doesn't include Editorial-tier sound design or motion blur. Never "same as" a higher tier.
  - Max 2 revision rounds.
  - Presence Builder ($495/mo) is the library's commercial use but is marked *retiring*, so the library's business case needs confirming.
  - Don't deliver before a real Stripe charge clears.
  - Price consistency across Tonomo and the website.
- **Files:**
  - Canonical path: `Syd Meyer/Keys Media Studio Team Folder/KMS_Clients/<CODE>/<CODE>_PROJECTS/<PROJECT>`.
  - Don't create footage folders before the client code is confirmed.
  - Bump `_v#` on every export.
  - Never blind-write an Asana description; re-read it and diff first.
- **Disk:** pulling footage onto a full disk failed twice. The engine has to check free space before it pulls anything.

## 6. The three decisions most likely to be wrong

1. **A layered, generic skill stack built phase by phase.**
   - Instead: **format-first, vertical-slice-first.** One format family on one client, end to end, in week 1. Widen only after it has run.
   - This is the decision that matches the logged failure most closely.
2. **Frame.io as the feedback channel.**
   - Instead: **keep Loom**, which is what Syd actually does, and auto-ingest the transcripts from the Calls & Transcripts DB.
   - Revisit Frame.io only if timecode mapping from Loom turns out to be unreliable.
3. **Safe zone 540px and the 90-day exclusivity window.**
   - Instead: use the **logged safe-zone spec** (y 285–1635, bottom 250px clear), set per format profile, with a rendered overlay.
   - Make exclusivity a **config value with no default**. Syd sets it.

**llm-council:** not run. The three calls above are decided by your own logged evidence, not by opinion, so a council adds cost without adding information. It is worth running for the editor-transition question (§5), which is a people and money call, not a technical one.

## 7. Format families: one agent per family, one profile per format

You're right: the format has to be known *before* the job starts. Each family has a different pipeline, so each gets its own agent. Within a family, formats differ only in their parameters, so each format is a **profile file** and doesn't need its own agent.

| Family agent | Formats (profiles) | What's specific to it | What it can skip |
|---|---|---|---|
| **reel-agent** (short organic) | `R` slot reels (SYD 8–12s, KMS/GRS 35–45s), BTS fast-cut, podcast reel clips, teasers (30–50s) | Hook in frame 1, downbeat grid, one-word captions, loop point, one point per reel, 07 slot plus 06 CTA | Chapters, long-form audio mastering |
| **trial-agent** (IG trial reels / tests) | Trial reels, A/B/C hook variants | Only the first 3s change across variants. Variant naming `_HOOKA/B/C`. A test hypothesis is logged. Results go back to the monthly review | Full polish on the shared body: it is cut once and reused |
| **ad-agent** (paid) | GRS room/Rhum House ads, listing ads, offer reels | **Compliance first**: no price, fee or rate; no "SAFE"; no surname; verbatim-only words; no kids in adults-only assets; Palm Deck held. Hard CTA from 06. Platform specs. Coral only on the CTA | Trending audio (licensing), personality moments |
| **property-agent** (real estate) | Listing films (by tier: $400/$950/$1,500/$2,500), vacation-rental lifestyle films, Content Multiplier 3- and 6-packs, realtor clip libraries | **Tier inclusions gate the features** (CPR lesson). Address intro and end card. "Most vibey shots first." All folders used (50mm, drone). 4K/24fps export spec. Music + no-music version. Hold if not show-ready. Clip-pack mode exports long, stable, trimmed clips | Captions (mostly), hooks as claims |
| **longform-agent** | YouTube vlogs (10–12 min), podcast episodes, KID pod pipeline | Transcript-first story structure. A visual change every ~3s. Notes covered by B-roll. 48kHz/24-bit. Chapters. The 17-step pod template with the Syd lock 🔒 gate. Hard 6-hour budget | Downbeat grid and loop logic |

**Shared, used by every family:** ingest/verify, transcribe, Resolve EDL build, polisher engine, carry-forward note tracker, deliver/handoff-check. Each family only loads the polisher checks its profile lists, so no effort goes to checks that don't apply.

**A format profile file looks like this:** `formats/<FAMILY>/<FORMAT>.yaml`

```
runtime, aspect, fps, median_shot, max_hold, hook_rule, caption_style,
safe_zone, audio_targets, music_rule, export_spec, naming,
required_inputs, tier_includes/excludes, qc_checks[], gates[], skip[]
```

**Routing:** the Asana type code (R, LF, CAR, AD, LISTING…) plus the Content Pipeline card's format field picks the family and profile *before* anything loads. If the format is unknown or ambiguous, the job stops and asks. It never guesses.
