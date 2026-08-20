# Afi pics → Lightroom

Pulls new photos out of a **WhatsApp** or **Messages** thread and drops them
into a Lightroom import folder, so "Afi sent new rock pics" stops being a
manual save-each-one job.

**macOS only.** It reads WhatsApp and Messages data stored on your Mac — it
cannot work from a Claude session started on your phone or the web.

## One-time setup

### 1. Give your terminal Full Disk Access

WhatsApp and Messages data is protected by macOS. Without this, the script
cannot read either one.

**System Settings → Privacy & Security → Full Disk Access** → `+` → add
**Terminal** (or iTerm, or the Claude Code app — whichever you'll run it from),
then **quit and reopen** that app. The restart matters; the permission doesn't
apply to an already-running process.

### 2. Find the thread name

```sh
./scripts/afin_pull.py --list-chats
```

This lists threads from **both** apps, tagged `WhatsApp` or `Messages`. Note
how Afi's thread actually shows up — a contact name or a bare number — and pass
that to `--from`.

UK numbers work in any format. `+44 7700 900123`, `07700 900123`, and
`447700900123` all resolve to the same chat, so use whichever you have.

### 3. Save your settings (optional but recommended)

```sh
mkdir -p ~/.config/afin-pull
cat > ~/.config/afin-pull/config.json <<'EOF'
{
  "from": "+447700900123",
  "source": "whatsapp",
  "dest": "~/Pictures/Afie Edit",
  "prefix": "AFI"
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

**Skips:** videos, voice notes, GIFs, PDFs, contact cards, anything under 50 KB
(stickers and thumbnails), photos *you* sent, and anything it has already
pulled before.

**Never touches your WhatsApp or Messages data.** It snapshots the database to
a temp directory, opens that copy read-only, and copies files out. Nothing is
written back, and nothing is deleted from your phone or Mac.

### Files that aren't on this Mac yet

Both apps keep some media in the cloud rather than on disk. The script lists
anything it can't find locally and skips it. Open the chat, scroll to those
photos so they download, then run it again.

WhatsApp in particular only keeps what you've actually viewed on the Mac. If
you've mostly used WhatsApp on your phone, open the chat on the Mac and scroll
back through the rock pics first.

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
| `--source APP` | `whatsapp`, `messages`, or `auto` (default — tries both). |
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

**`permission denied reading ...`** — Full Disk Access isn't applied. Redo
step 1, and make sure you fully quit and reopened the app.

**`no thread matched ...`** — run `--list-chats` and use the exact label you
see, or pass her number instead: `--from '+447700900123'`.

**`WhatsApp: no local data found on this Mac`** — WhatsApp Desktop isn't
installed, or has never synced. Install it and sign in, then open Afi's chat so
it downloads.

**`WhatsApp: database unreadable`** — WhatsApp moved its schema in a newer
version. The script falls back to scanning the media folder by phone number,
which still finds the photos but has less metadata. Nothing to fix.

**`could not find a folder matching 'Afie Edit'`** — pass it explicitly with
`--dest`, or put it in the config file.

**Nothing new to pull, but you know there is** — the window defaults to "since
last run". Try `--since 14d` or `--all`.
