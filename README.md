# AFIN → Lightroom

Pulls new photos out of a Messages thread and drops them into a Lightroom
import folder, so "AFIN sent new rock pics" stops being a manual save-each-one
job.

**macOS only.** It reads the local Messages database, which only exists on your
Mac — it cannot work from a Claude session started on your phone or the web.

## One-time setup

### 1. Give your terminal Full Disk Access

Messages' database is protected. Without this, the script cannot read it.

**System Settings → Privacy & Security → Full Disk Access** → `+` → add
**Terminal** (or iTerm, or the Claude Code app — whichever you'll run it from),
then **quit and reopen** that app. The restart matters; the permission doesn't
apply to an already-running process.

### 2. Find the thread name

```sh
./scripts/afin_pull.py --list-chats
```

Note how the thread actually shows up — a contact name, a group name, or a bare
phone number. That's what you pass to `--from`.

### 3. Save your settings (optional but recommended)

```sh
mkdir -p ~/.config/afin-pull
cat > ~/.config/afin-pull/config.json <<'EOF'
{
  "from": "AFIN",
  "dest": "~/Pictures/Afie Edit",
  "prefix": "AFIN"
}
EOF
```

With that in place, the everyday command is just `./scripts/afin_pull.py`.

## Everyday use

```sh
# See what it would grab, without touching anything
./scripts/afin_pull.py --dry-run

# Actually pull them
./scripts/afin_pull.py

# Reveal the folder in Finder when it's done
./scripts/afin_pull.py --open
```

Then in **Lightroom Classic**: *File → Import Photos*, point at the folder.

Better: set that folder as an **Auto Import** watched folder
(*File → Auto Import → Auto Import Settings*) and new pics get pulled into your
catalogue on their own.

## What it picks up

**Copies:** photos *received* in that thread — HEIC, JPEG, PNG, TIFF, WebP, and
raw formats (DNG, CR2/CR3, NEF, ARW, RAF, ORF, RW2, …).

**Skips:** videos, GIFs, PDFs, contact cards, anything under 50 KB (stickers,
tapback thumbnails), photos *you* sent, and anything it has already pulled
before.

**Never touches your Messages data.** It snapshots `chat.db` to a temp
directory, opens that copy read-only, and copies files out. Nothing is written
back, and nothing is deleted from your phone or Mac.

### Files that aren't on this Mac yet

If photos live only in iCloud, the script lists them and skips them. Open the
thread in Messages, scroll so they download, then run it again.

## Repeat runs

Each destination folder keeps a `.afin_pull_state.json` marker recording what's
already been pulled and when it last ran. So:

- Running twice in a row does nothing the second time.
- By default each run only looks at messages **since the last run**.
- The first ever run looks back **30 days**.

Widen the window when you need to:

```sh
./scripts/afin_pull.py --since 14d      # last two weeks
./scripts/afin_pull.py --since 2026-08-01
./scripts/afin_pull.py --all            # the entire thread
```

Deleting `.afin_pull_state.json` resets the memory (files already in the folder
are still skipped by content hash, so you won't get duplicates).

## All options

| Flag | Does |
|---|---|
| `--from NAME` | Contact name, phone, or email. Resolves names via Contacts. Default `AFIN`. |
| `--dest PATH` | Destination folder. Default: auto-detects a folder matching `Afie Edit`. |
| `--since 14d` | Only messages newer than this — `14d`, `36h`, `2w`, or `2026-08-01`. |
| `--all` | Ignore the last-run marker; consider the whole thread. |
| `--include-mine` | Also copy photos *you* sent. |
| `--min-bytes N` | Size floor for "this is a real photo". Default `50000`. |
| `--prefix P` | Filename prefix. Default: the `--from` value, uppercased. |
| `--dry-run` | Print what would happen; write nothing. |
| `--list-chats` | List recent threads and exit. |
| `--open` | Reveal the destination in Finder when done. |
| `--config PATH` | Use a specific config file. |

## Naming

Files land as `AFIN_2026-08-19_143022_IMG_4471.HEIC` — prefix, the date and time
the message was sent, then the original filename. Sorting by name sorts them
chronologically, which is usually how you want to cull a batch.

## Troubleshooting

**`permission denied reading .../chat.db`** — Full Disk Access isn't applied.
Redo step 1, and make sure you fully quit and reopened the app.

**`no thread matched 'AFIN'`** — run `--list-chats` and use the exact label you
see, or pass her phone number instead: `--from '+15551234567'`.

**`could not find a folder matching 'Afie Edit'`** — pass it explicitly with
`--dest`, or put it in the config file.

**Nothing new to pull, but you know there is** — the window defaults to "since
last run". Try `--since 14d` or `--all`.
