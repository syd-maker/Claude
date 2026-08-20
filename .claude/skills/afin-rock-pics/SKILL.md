---
name: afin-rock-pics
description: Pull new photos from a WhatsApp or Messages/iMessage thread into a Lightroom import folder on macOS. Use whenever the user asks to grab, pull, fetch, or move pics/photos/rock pics out of WhatsApp, a text message, or an iMessage thread (from Afi, AFIN, Afie, or any named contact) and into Lightroom, the Afie Edit folder, or any edit/import folder. Also use for "get the new pics she sent into Lightroom", "check if Afi sent anything new", or setting this up to run automatically.
---

# Afi rock pics → Lightroom

Wraps `scripts/afin_pull.py`, which copies photo attachments out of a WhatsApp
or Messages thread into a Lightroom import folder.

Afi's thread is **WhatsApp**, on a UK number. The script defaults to `--source
auto` and checks both apps, so you rarely need to specify.

## Before anything else: check where you are running

This reads WhatsApp and Messages data that only exists on the user's Mac.

```sh
test -d ~/Library/Group\ Containers/group.net.whatsapp.WhatsApp.shared \
  -o -f ~/Library/Messages/chat.db && echo LOCAL || echo "NOT ON THE MAC"
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

- **`permission denied reading ...`** — Full Disk Access. Walk them through
  System Settings → Privacy & Security → Full Disk Access, adding their
  terminal, and **restarting it**. The restart is the step people miss.
- **`no thread matched ...`** — run `./scripts/afin_pull.py --list-chats`, show
  them the candidates, ask which one, then re-run with `--from '<that>'`. UK
  numbers match in any format, so `+44...`, `07...`, and `44...` are all fine.
- **`WhatsApp: no local data found`** — WhatsApp Desktop isn't installed or has
  never synced on this Mac. It has to be installed and signed in.
- **`WhatsApp: database unreadable`** — expected on newer WhatsApp versions.
  The script falls back to scanning the media folder; let it, and say so.
- **`could not find a folder matching 'Afie Edit'`** — ask for the path, then
  re-run with `--dest`. Offer to save it to
  `~/.config/afin-pull/config.json` so it isn't asked again.
- **"Nothing new to pull"** but they expect photos — the default window is
  "since the last run". Try `--since 14d`, then `--all`.
- **Attachments not downloaded** — the script lists them. Tell the user to open
  the chat *on the Mac* and scroll to those photos so they download, then run
  again. This is common with WhatsApp when they mostly use it on their phone.

## Widening the window

`--since 14d` / `--since 36h` / `--since 2026-08-01` / `--all`.

Reach for these when the user says "it missed some" or "go back further".

## Notes

- Received photos only by default. Add `--include-mine` if they want their own.
- Re-running is safe: already-pulled files are skipped by GUID and by content
  hash, so nothing duplicates.
- The script never writes to the Messages database and never deletes anything.
- Don't edit `.afin_pull_state.json` by hand; use `--all` to override the window.
