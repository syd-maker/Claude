# Master prompt: KMS Video Engine, P0 vertical slice (run on Syd's Mac)

## How to launch

```bash
cd ~ && git clone https://github.com/syd-maker/Claude.git kms-engine 2>/dev/null; cd ~/kms-engine && git fetch origin && git checkout claude/video-engine-plan && git pull && claude
```

Then paste everything below the line. Before you start, check two things:
- Notion and Asana must be connected in this Claude Code session. Check with `/mcp`.
- Resolve **Studio** must be running if you want the scripted timeline build.

---

You are building and running **P0 of the KMS Video Engine** on Syd's Mac. The scope is **one real GRS slot reel, run end to end.** Nothing counts as built until it has run on that paying job. Read these first, in this order:
1. `docs/PRESSURE_TEST.md`. It wins over the plan wherever they conflict.
2. `docs/KMS_VIDEO_ENGINE_PLAN.md`.

## Locked decisions (do not reopen them)

- **First job:** reel-agent on the next due **GRS** Content Pipeline card (Notion `d75c4bdcb8cf47bfa24222a9fc9150da`).
- **Gates:**
  - **G1:** selects sheet plus music. Stop and wait for Syd's approval.
  - **G2:** the polished draft in `00_FOR_APPROVAL`. Stop. Syd sends anything to the client; you never do.
  - No other gates.
- **Library:** open to all KMS clients, with market exclusivity. A clip that was published for another client in the same town or key within `exclusivity_days` (config, default **90**) is blocked. `zone:` clips need a grant. `client:` clips never leave their owner.
- **Feedback:** Loom transcripts from the Calls & Transcripts DB, plus Asana stories. No Frame.io.
- **Safe zone (4:5 / feed crop):** text and faces stay inside y 285–1635, and the bottom 250px stays clear. Verify against a rendered overlay frame, never by eye.
- **Colour:** never grade. The polisher only flags colour problems.

## Hard rules (from the Mistakes & Lessons logs; breaking one is a failure)

1. **Report only what is provable.** Never say footage "doesn't exist" until you have checked every folder and drive (Dropbox included, via `rclone --include`) and run an audio pass. Transcript hit counts are a search index, never a coverage claim. Auto-sort and index output is labelled `PROVISIONAL`.
2. **A check that cannot fail is not a check.** Count every file type, sidecars included. Write an inode/md5 manifest before any move. Never rename or move anything in the Keys library or `SOURCE`. Use sidecar manifests only, because renaming a synced folder forces a full re-upload.
3. **Check free disk space before pulling footage.** If a pull isn't converging, stop. Pause Dropbox sync before bulk operations.
4. **Batch questions.** Syd hates back and forth. Investigate everything you can first, then ask once, leading with whatever is blocking.
5. **Briefs fit on one screen.** They are instructions, not a report.
6. **Re-read and diff before writing to any Notion or Asana field.** Never blind-write a description.
7. **Don't create or announce folders until the client code is confirmed.** Use the canonical path `Syd Meyer/Keys Media Studio Team Folder/KMS_Clients/<CODE>/<CODE>_PROJECTS/<PROJECT>`, or GRS's `_GRS_MASTER_INDEX.md`, which is the source of truth for GRS footage.
8. **Long jobs** run with `--timeout`. "Still running" means CPU time is advancing, not just that `pgrep` finds the process.
9. **Lav sync:** never sync by timecode. Match takes by transcript, then align with GCC-PHAT.
10. **Whisper:** long-file timestamps drift. Locate the line, then re-transcribe a 20–28s window at word level (`-ml 1 -sow`) to cut.
11. **Every run appends to `RUNS.log`**, both in the repo and in Dropbox `SSS_DATA/BEACON-ENGINE/RUNS.log`. Each entry records: timestamp, card, stage, result, and links. Lindsey checks it on Mondays.
12. **Exports:** name them `GRS_R_<DESC>_<CONTEXT>_v#` and bump `_v#` on every export, never overwriting. Check for muted channels.
13. **GRS compliance:**
    - No price, fee or rate.
    - No "SAFE".
    - No surnames.
    - On-screen words must be verbatim from the speaker.
    - No kids in Wreckers or Humidor assets.
    - Palm Deck: hold all assets.
    - Coral #FA886B on the CTA only.
    - Fonts: Montebello for headlines, Futura for body.
    - Stock footage only as 1–2s cutaways with no identifiable land. Bikes footage never from stock.

## Step A: Inventory (read-only, then report)

1. Find what exists locally. Write `docs/INVENTORY.md` with paths, versions, and a works/missing/broken status for each item:
   - `~/.claude/skills/` (the rough-cut package, lav-sync, handoff-check, content-strategist, verify-before-erase, sort-footage, color-grade, carousel, `_shared/`)
   - `~/scripts/lighthouse/` (engine.py, pipeline_scripts, `shake.py`, `watch.py`)
   - ffmpeg/ffprobe, whisper.cpp plus the model, rclone, python deps
   - Resolve version and whether scripting works
   - Dropbox root and free disk space
2. **Copy, never move,** each skill into `skills/` in this repo, and `_shared/` into `skills/_shared/`. Add `scripts/sync-skills.sh`, which mirrors `skills/` to `~/.claude/skills/` and backs up to `~/.claude/skills.bak-<date>` first. Don't run the sync yet.

## Step B: Minimal knowledge and structure

Build only what the GRS reel needs:

- `knowledge/_shared/HOUSE_RULES.md` and `knowledge/_shared/MISTAKE_BANK.md`
  - Sources: PRESSURE_TEST, the plan's §5, Notion "SSS - QC" (Drive `1u4uliLZ2yXJ2mLh6WodM8Y0-443hCttVc1yDiNBpyko`), the Efficiency Register (`3bb6dbac-9101-8121-b1cf-ce867ab646d0`), and the GRS-relevant Loom transcripts in Calls & Transcripts.
  - Every rule carries a source tag `[CLIENT job, date]`.
- `knowledge/clients/GRS/BLUEPRINT.md`, extracted from the GRS blueprint (`3bd6dbac-9101-8103-90c2-cb6172bb8ec5`) and GRS Brand & Content Standards (`3c86dbac-9101-815d-97b2-e7a38cbe538c`). It covers:
  - the offers/lanes table with CTA strength (06)
  - the pillars and slot rhythm (07)
  - compliance rules
  - fonts and colours
  - music persona ("active, adventure-seeking", never slow cinematic)
- `knowledge/clients/GRS/CAPTION_DICT.txt` (for example "Grassy Plus" → Grassy Flats, "masks" → masts).
- `formats/reel/GRS_R.yaml`, with fields:
  ```
  runtime, aspect, fps, median_shot, max_hold, hook_rule, caption_style,
  safe_zone, audio_targets, music_rule, export_spec, naming,
  required_inputs, tier_includes/excludes, qc_checks[], gates[], skip[]
  ```
- `library/config.yaml` (`exclusivity_days: 90`), `library/grants.csv`, `library/ledger.csv` (client, asset, clip, src_in, src_out, market, publish_date). Index **only** the GRASSY FLATS zone, as provisional sidecar rows. Sample several frames per clip, never one mid-clip frame. Propose the resort/Lagoon/cable-park split as a list for Syd to approve. Don't move anything.

## Step C: Calibrate the polisher before trusting it

1. Build `skills/polisher/`. Inputs: a video plus a format profile. Output: `qc.json`, where each check has pass/fail, a measured value, a confidence score, and a suggested fix. Mark each check as [A] automated, [V] vision judgment, or [H] human flag.
2. Run `study_reference_cut.py` on **3 Syd-approved GRS reel finals**, to get each final's "DNA" (cuts, captions, tempo). Set the profile's median_shot and runtime from those results.
3. Run the polisher on those 3 finals. Then run it on 2 earlier drafts that got notes, if they can be found via Asana or the Calls & Transcripts DB.
4. The polisher must flag the problems the notes named, and must **not** flag the approved finals for [MUST] failures. Write the results to `docs/POLISHER_CALIBRATION.md`. If any [V] check scores below 80% agreement, mark it advisory only.

## Step D: The vertical slice

1. **Slot.** Read the next due card in the GRS Content Pipeline. Pull its 07 slot (stage, pillar, format) and its 06 lane/offer (CTA strength, CTA line). If the format isn't a GRS reel, or is ambiguous, stop and ask.
2. **Brief.** Write a one-screen `brief.json` and `brief.md`: THE POINT, MUST KEEPS/DELETES, hook claim, CTA, runtime, and tier includes/excludes.
3. **Footage.**
   - Search by time window across all drives and the library, through the library-access filter and the ledger.
   - Lav sync and transcribe.
   - Build a whole-shoot `selects.csv` scorecard, with shake below the 60th percentile and "last full take is the keeper".
   - Mark any beat with no footage as `needs a shoot`.
   - Propose 2–3 music options that fit the brand persona, plus the beat grid (bars of 8, no cuts on beat 3).
4. **G1. Stop.** Send Syd one message containing: the brief, the selects summary, the music options, and the questions, all batched. Wait.
5. **Cut.** After G1 is approved:
   - Write `edl.json` → `resolve_build_reel.py`.
   - Frame 1 is action or the payoff.
   - Hook claim lands in the first 3 words.
   - One point.
   - Image agrees with the sentence.
   - Loop point on movement.
   - One-word captions per the profile.
   - SFX at least -32 dB under speech.
   - Speech at around -17 LUFS.
6. **Polish loop.** Run the polisher, fix, and re-run until every [MUST] passes. Allow at most 3 loops. Anything still failing goes in the G2 note.
7. **Deliver.**
   - Export `GRS_R_<DESC>_<CONTEXT>_v1`.
   - Render a safe-zone overlay frame.
   - Export 3 stills.
   - Log the source timecodes to `ledger.csv`.
   - Run `handoff-check`, which must say `ready to send`.
   - Put everything in `00_FOR_APPROVAL`.
   - Re-read the pipeline card, then set it to `Review` with links to the files.
   - Append to `RUNS.log`.
8. **G2. Stop.** Report the file path (`open -R`), the QC summary, and any open [H] flags.

## Step E: Feedback, when Syd's Loom or Asana notes arrive

1. Parse each note to `{timecode, scope: this-cut | client-rule | house-rule, category, instruction, severity}`. Map Loom timestamps to the draft using its transcript.
2. Patch the EDL.
3. Re-check **every note from every earlier draft**.
4. Re-render `_v2`, run the polisher, then G2 again.
5. Notes Syd marks "remember", or that come up a second time, get added to the BLUEPRINT or HOUSE_RULES with a source tag.
6. Cap: 2 revision rounds, per the brief template.

## Done when

- One GRS reel has passed G2 and Syd has accepted it.
- `RUNS.log` shows every stage.
- `docs/INVENTORY.md`, `docs/POLISHER_CALIBRATION.md` and `docs/P0_RETRO.md` are written. The retro covers what broke, the time per stage, and Syd's notes count compared with a typical human draft.
- Commit to branch `claude/video-engine-plan` and push.
- Only after that, propose P1: the next format families (trial, ad, property, longform), each a profile plus an agent, per PRESSURE_TEST §7.

## How to report back

Use short status lines. Lead every ask with **CLIENT / PROJECT / DELIVERABLE / STEP**. Deliver files with `open -R` plus the bold filename. Never guess out loud.
