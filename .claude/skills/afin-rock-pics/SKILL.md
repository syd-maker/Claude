---
name: afin-rock-pics
description: Pull new photos from a Messages/iMessage thread into a Lightroom import folder on macOS. Use whenever the user asks to grab, pull, fetch, or move pics/photos/rock pics out of a text message or iMessage thread (from AFIN, Afie, or any named contact) and into Lightroom, the Afie Edit folder, or any edit/import folder. Also use for "get the new pics she sent into Lightroom", "check if AFIN sent anything new", or setting this up to run automatically.
---

# AFIN rock pics → Lightroom

Wraps `scripts/afin_pull.py`, which copies photo attachments out of a Messages
thread into a Lightroom import folder.

## Before anything else: check where you are running

This reads `~/Library/Messages/chat.db`, which only exists on the user's Mac.

```sh
test -f ~/Library/Messages/chat.db && echo LOCAL || echo "NOT ON THE MAC"
```

If that prints `NOT ON THE MAC`, stop. Tell the user this session is running in
a cloud container (started from the phone or web) and the job needs a Claude
Code session on their Mac. Do not try to work around it.

## Normal run

Show them what's coming first — it costs nothing and avoids surprises:

```sh
./scripts/afin_pull.py --dry-run
```

Report what it found, then pull for real:

```sh
./scripts/afin_pull.py
```

Tell them the count and the destination folder. Mention Lightroom's *File →
Import Photos* only if they seem unsure what to do next.

## When it fails

Read the error — the script's messages are specific and usually say what to do.

- **`permission denied reading .../chat.db`** — Full Disk Access. Walk them
  through System Settings → Privacy & Security → Full Disk Access, adding their
  terminal, and **restarting it**. The restart is the step people miss.
- **`no thread matched ...`** — run `./scripts/afin_pull.py --list-chats`, show
  them the candidates, ask which one, then re-run with `--from '<that>'`.
- **`could not find a folder matching 'Afie Edit'`** — ask for the path, then
  re-run with `--dest`. Offer to save it to
  `~/.config/afin-pull/config.json` so it isn't asked again.
- **"Nothing new to pull"** but they expect photos — the default window is
  "since the last run". Try `--since 14d`, then `--all`.
- **Attachments not downloaded** — the script lists them. Tell the user to open
  the thread in Messages and scroll to those photos so iCloud fetches them,
  then run again.

## Widening the window

`--since 14d` / `--since 36h` / `--since 2026-08-01` / `--all`.

Reach for these when the user says "it missed some" or "go back further".

## Notes

- Received photos only by default. Add `--include-mine` if they want their own.
- Re-running is safe: already-pulled files are skipped by GUID and by content
  hash, so nothing duplicates.
- The script never writes to the Messages database and never deletes anything.
- Don't edit `.afin_pull_state.json` by hand; use `--all` to override the window.
