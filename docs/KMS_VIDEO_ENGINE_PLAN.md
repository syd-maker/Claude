# KMS Video Engine: Plan

**Goal:** replace the human short-form editing pipeline (brief → rough cut → feedback → polish → delivery) with a layered, autonomous skill stack. It plugs into Beacon Engine and pulls from the Keys Collection Library on each client's behalf, while respecting gated zones.
**Status:** plan v1, 2026-10-17. It is grounded in about 80 Asana threads, 8 Loom transcripts, the Jul 14 and Sep 29 team meetings, SSS‑QC, the Efficiency Register, and the Notion skills `rough-cut` v1, `color-grade` and `beacon-engine` (Steal Loop).

---

## 0. What this plan is built on

1. **Part of it already exists.** `rough-cut` v1 (Oct 15) already runs verify → sort → lav‑sync → whisper → selects scorecard → Resolve assembly from a JSON EDL → self‑review → `handoff-check`. `study_reference_cut.py` already pulls the "DNA" (cuts, captions, tempo) out of finished edits. We extend these rather than rebuild them.
2. **The missing pieces are judgment and memory, not tools.** Every recurring Loom and Asana note concerns hooks, pacing against music, shot choice, text styling, brand rules, or forgotten past notes. None of these is written down in a form a machine can check.
3. **No zone or permission model exists anywhere.** Beacon only isolates data per client. "Grassy Flats" is just a folder, and the library is half‑migrated from `BY_CATEGORY/` to `ZONES/`. This has to be designed, and it needs one decision from you (§3).
4. **There is no API between Beacon and the edit.** Beacon is Supabase plus Notion sync, and the Steal Loop writes cards to Notion pipelines. **The Notion pipeline rail is the integration point:** `Footage matched → Rough cut → Review → Scheduled`.
5. **Execution has to happen on your Mac.** The footage (Dropbox and the studio drive), Resolve, whisper, `engine.py`, `lav-sync` and `handoff-check` all live there. This repo becomes the **versioned source of truth for the skills**, synced into `~/.claude/skills/`. The carousel creator and the local scripts should move in here too, because right now they exist only on one machine.

---

## 1. Architecture: layers

```
L4  ORCHESTRATOR   video-director        reads a pipeline card, routes, enforces gates, tracks state
L3  JUDGMENT       hook-lab · story-cut · polisher · feedback-loop
L2  CRAFT          footage-matcher · beat-map · caption-system · (color-grade: existing, human-gated)
L1  MECHANICS      ingest (sort-footage, lav-sync, whisper) · resolve-build · study-reference · deliver/handoff-check
L0  KNOWLEDGE      house rules · mistake bank · client blueprints · style DNA · library manifest · usage ledger
```

**Rules for the stack:**
- Each skill has exactly one job, plus a "Do NOT use for X (use Y)" line. This mirrors the Team Skills DB pattern.
- Skills never call each other directly. Only `video-director` chains them. That lets any skill be reused by other parts of the ecosystem (carousel, thumbnails, Sprout).
- Every hard rule carries its source tag, e.g. `[GRS sauna reel, Aug 12 Loom]`. A rule with no source gets deleted.
- Skills communicate through files, not chat: `brief.json → selects.csv → edl.json → review.json → qc.json → delivery/`. Every stage can be replayed and diffed.

---

## 2. The skills

| # | Skill | Job | Done when | Builds on |
|---|---|---|---|---|
| 1 | **video-director** | Reads the Notion pipeline card, resolves client and tier, runs the stages, and stops at the gates | The card has moved to `Review` with links to the export and the QC report | Steal Loop rail |
| 2 | **brief-builder** | Turns a card, a dump or Syd's voice notes into `brief.json`: THE POINT, MUST KEEPS/DELETES, format, runtime, hook claim, CTA, music lock, [MUST]/[SUGGESTED]/[EDITOR'S CALL] tags | Brief is valid against the schema; "No brief = no edit" | KID pod template, KEL brief format, Editor Briefs DB |
| 3 | **footage-matcher** | Finds clips for each beat across project footage and the library, filtered by the zone resolver (§3) and the usage ledger; writes `selects.csv`; marks gaps as `needs a shoot` | Every beat is covered or flagged; no blocked clip or reused clip | rough-cut selects step, Clip Selection Bank SOP |
| 4 | **beat-map** | Locked track → downbeats, bars of 8, energy curve → cut grid | Grid written; no cut lands on beat 3 | Aug 14 Loom "Use downbeats" |
| 5 | **story-cut** (rough-cut v2) | Builds the EDL: one point per reel, the image agrees with the sentence, the payoff in frame 1, runtime and median shot length taken from the client's DNA | EDL passes the polisher's structural checks | rough-cut v1 + `resolve_build_reel.py` |
| 6 | **hook-lab** | Writes 3 hook variants (A/B/C) where only the first 3 seconds differ: an action frame, a claim (number, stake, improbable), no fluff opener | 3 EDL variants, each scored | Hook Bank, POD14 slate, "falling = hook" |
| 7 | **caption-system** | One‑word captions in the client font, safe zone, shadow, hierarchy, the client's dictionary of known mis-transcriptions ("Grassy Plus"→Grassy Flats), verbatim-only check for GRS | Zero dictionary misses; safe zone respected | Efficiency Register, client fonts |
| 8 | **polisher** | Automated QC against the mistake bank (§5) plus visual and audio measurement; outputs pass/fail and fixes per check | All [MUST] checks pass | SSS‑QC 4 layers, the 19 Asana mistakes |
| 9 | **feedback-loop** | Loom, Frame.io or Asana comments → structured notes → EDL patch → re-render; promotes repeated notes to rules | Every note has a status of applied, rejected or asked; nothing left over from earlier drafts | §4 |
| 10 | **deliver** | Naming, export spec, the no-music version (frame-matched), 3 thumbnail stills, source-timecode log, handoff-check | `handoff-check` = `ready to send` | existing handoff-check |

`color-grade` stays human-in-the-loop under the existing rule: Claude never grades on its own. The polisher only *flags* color problems: yellow interiors, pink blacks, clipped highlights, nuclear greens, grey/flat footage.

---

## 3. Library access and gated zones

**The model.** Every clip gets a manifest row. This is the v2 "searchable manifest" already on the library roadmap, built ahead of schedule.

```
clip_id, path, category, keyname, zone, owner_client, access, people, kids_in_frame,
shot_type, motion, lens, time_of_day, location, quality (shake pct, exposure), tags, embedding
```

`access` takes one of three values:
- `open`: any KMS client.
- `zone:<ZONE>`: only clients granted that zone, e.g. `zone:GRASSY_FLATS`.
- `client:<CODE>`: private, client-property footage. The rule "If a realtor could say 'that's my listing'" means it stays theirs.

**How it's enforced.** A `library-access` resolver takes a client code and returns the allowed set. footage-matcher can only see that set, so a gated clip never even appears as a candidate. Every use is written to a **usage ledger** (client, asset, clip, source timecode, publish date). The ledger blocks reusing the same moment across assets, which Asana flagged repeatedly. If you choose to, it can also block the same clip going to two competing realtors.

**Building the index.** This is an extension of `sort-footage`: frame sampling, Claude vision tags, kids/people detection, and a shake/exposure score from `shake.py`. It runs once over the library, then on every closeout harvest. As part of this, the GRASSY FLATS folder (317 files mixing resort, Lagoon and cable-park footage) gets split into sub-zones.

**⚠ One decision needed from you.** Your sources disagree:
- (a) "All KMS clients get to pull from the Keys library."
- (b) Sales copy: "no other realtors have access unless client grants it."
- (c) A note: "shouldn't use same content for multiple clients."

Recommendation: **open library plus exclusivity windows.** Open clips are shareable, but the ledger blocks the same clip for a second client in the same market for N days. Zones are opt‑in grants.

---

## 4. The feedback loop (where the learning happens)

```
Draft → review (Syd/Lindsey Loom, Frame.io, Asana, client) → transcribe → parse → patch → re-render → polisher → next draft
                                                      └→ note bank → promote rule (after it recurs 2+ times) → skill reference files
```

1. **Ingest.** Loom transcripts (via the Calls & Transcripts DB or a Loom export), Frame.io comments (API), and Asana stories on the task.
2. **Parse** each note into `{timecode, scope: this-cut | client-rule | house-rule, category, instruction, severity, confidence}`. Ambiguous notes become one batched question to Syd, never a guess.
3. **Patch** the EDL deterministically: trim, swap, reorder, re-time to the beat grid, caption fixes. Changing a *locked* element (hook, music, approved shot) needs Syd's sign-off. This is Asana mistakes #2 and #16.
4. **Carry-forward check.** Every note from every earlier draft gets re-verified on the new draft. This is Asana mistake #19: "Several from the first draft were never addressed."
5. **Promote.** A note that recurs (2+ times, or once if Syd marks it "remember this forever") becomes a rule in the house or client file, tagged with its source. This is how the system gets better without anyone retraining it.

---

## 5. Polisher checklist (seed v1, from your own data)

Each check has a type: **[A]** automated measurement, **[V]** Claude vision/listen judgment, or **[H]** flag for a human.

| Area | Checks |
|---|---|
| Brief | Brief exists [A] · every MUST KEEP is present, every MUST DELETE is absent [A] · shots approved in the last draft are kept [A] · ref trait copied, not whole format [V] |
| Hook | Frame 1 is action or the payoff, not a face, text card or "hey guys" [V] · claim in the first 3 words [V] · no fluff opener or leftover false start [A, transcript] |
| Pacing | Median shot within ±20% of client DNA [A] · no clip over its cap (0.7s fast-cut / 3s long-form visual change) unless it's a hold [A] · cuts on downbeats, none on beat 3 [A] · loop point on movement [V] |
| Footage | Right property/location/year [V + metadata] · all folders used (50mm, drone, session 2) [A] · shake ≤ 60th pct [A] · no blocked zone, no reuse per ledger [A] · no kids in adults-only GRS assets [V] |
| Audio | Speech around -17 LUFS (event -23) [A] · music and SFX ≤ -32 dB under speech [A] · no muted channels [A] · no clipped words at Riverside gaps [A] · SFX match the scene and time of day (no waves in the Keys) [V] |
| Text | Client font only [V] · hierarchy present, shadow on bright footage [V] · left-aligned, never justified [V] · inside safe zone [A] · no emojis, no em-dashes [A] · spelling plus the client caption dictionary [A] · GRS: verbatim words only, no surname/"SAFE"/price [A] |
| Color | Not flat/log, no clipped highlights, no yellow interiors, no pink blacks, no nuclear greens, no orange beach [H flag, measured] |
| Format | One aspect ratio [A] · runtime within the brief [A] · export spec matches [A] · end card, CTA or contact card present [V] · naming `CLIENT_TYPE_DESC_CONTEXT_v#` [A] |

---

## 6. Knowledge base to extract (L0)

| File | Source |
|---|---|
| `_shared/HOUSE_RULES.md` | SSS‑QC, Efficiency Register, Loom principles, Asana themes (hooks, pacing, music, sound, text, color) |
| `_shared/MISTAKE_BANK.md` | The 19 Asana repeat mistakes, the 10 Kavya corrections, Claude's own failure list from rough-cut |
| `clients/<CODE>/BLUEPRINT.md` | Fonts, colors, music persona, runtime, CTA, compliance (GRS, AND, KID, SYD, KEL, CPR, BRT, KMS, JES, LFR) |
| `clients/<CODE>/CAPTION_DICT.txt` | Known mis-transcriptions |
| `dna/<CODE>/*.json` | `study_reference_cut.py` run over 5–10 approved finals per client and format |
| `library/manifest.parquet` + `ledger.csv` | §3 |

Still unread and worth ingesting: meetings from May 26, Jul 21, Jul 28, Sep 10, Sep 22 and Sep 8 (Beacon); the GRS Approvals & Client Feedback DB; the QC checklist sub-pages; Matt's Voice Log; Kavya's Loom .txt files in Dropbox; the Jul 24 Real-Estate workflow, which survives only in Fireflies.

Raw comment extracts from about 80 Asana threads are saved in the session scratchpad and still need to be folded into these files.

---

## 7. Gates and how autonomy grows

v1 keeps the four gates Syd already uses:
1. **Music lock:** Syd picks the track.
2. **Selects approval.**
3. **Hook pick (A/B/C).**
4. **Client send:** Syd sends.

Each gate records whether Syd **accepted it as is**. When a gate hits **≥ 90% acceptance over 20 jobs** for a client and format, it becomes notify-only. Color stays human.

**Metrics:**
- First-pass acceptance rate
- Revision rounds per asset (now 2–3)
- Notes per review
- Repeat-note rate (should trend to 0)
- Hours to deliver (target: under 6, per Syd)
- Performance from the monthly content review

---

## 8. Proving it works before going live

**Replay harness.** Take 10–20 past jobs where the raw footage, the brief and the approved FINAL all exist. Run the engine on the raw footage, then compare its output to the approved FINAL:
- DNA distance (shot length, caption coverage, tempo)
- Hook frame
- Polisher score
- How many of the Asana/Loom notes from the original job the engine would have avoided

A skill change ships only if the replay score doesn't regress. This is your eval suite.

---

## 9. Build order

| Phase | Deliverable | Depends on |
|---|---|---|
| **P0: Foundation** | Pull `rough-cut`, `color-grade`, the carousel skill and local scripts into this repo; write the skill template and sync script to `~/.claude/skills/`; write the brief/EDL/review/QC JSON schemas | Access to your Mac |
| **P1: Knowledge** | HOUSE_RULES, MISTAKE_BANK, BLUEPRINTs for GRS, KMS, SYD and KEL first; DNA runs on finals; finish ingesting the unread sources | Notion (done), Dropbox finals |
| **P2: Polisher** | Built first, because it is also the scorer for everything else, and it pays off immediately on human edits today | P1 |
| **P3: Library** | Manifest indexer, zone resolver, usage ledger, Grassy Flats split | Your zone decision (§3) |
| **P4: Cut** | brief-builder, beat-map, footage-matcher, story-cut, hook-lab, caption-system; replay harness | P2, P3 |
| **P5: Loop** | feedback-loop (Loom, Frame.io, Asana ingest), rule promotion | P4 |
| **P6: Orchestrate** | video-director on the Notion pipeline rail; Beacon card → `Review`; later a Supabase MCP for direct Beacon reads | P4–P5 |

Ship order for clients: **GRS reels first.** They have the richest rulebook, a defined zone, and constant volume. Then KMS/KEL real estate, then SYD, then KID podcast clips. Long-form comes last.

---

## 10. Open questions

1. **Library sharing rule:** open, exclusivity window, or grant-only? (§3)
2. **Feedback channel:** standardize on Frame.io (comments carry timecodes and survive) or keep Loom plus transcription? Frame.io notes were lost when an editor's account left.
3. **Editors' role after launch:** do Kavya and Teknikoz become reviewers or finishers of engine output, or are they phased out?
4. **Safe zone:** 484px or 540px? Both appear in the docs.
5. **Mac access:** do I run on your Mac via Claude Code locally (needed for P0 and P3), or should the library be mirrored somewhere a cloud session can reach?
