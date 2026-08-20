#!/usr/bin/env python3
"""
Pull photo attachments out of a Messages (iMessage/SMS) conversation and drop
them into a Lightroom import folder.

Built for the recurring "AFIN sent new rock pics, get them into the Afie Edit
folder" job, but the contact and destination are both configurable.

Runs on macOS only, with no third-party dependencies. Terminal (or whatever is
running it) needs Full Disk Access -- see README.md.

    ./scripts/afin_pull.py --dry-run
    ./scripts/afin_pull.py
    ./scripts/afin_pull.py --from AFIN --dest ~/Pictures/Afie\\ Edit --since 14d
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------- constants

APPLE_EPOCH = 978307200  # 2001-01-01 UTC in unix seconds

CHAT_DB = Path.home() / "Library" / "Messages" / "chat.db"
ADDRESSBOOK_GLOB = str(
    Path.home()
    / "Library/Application Support/AddressBook/Sources/*/AddressBook-v22.abcddb"
)

# Extensions we treat as "a photo worth editing".
PHOTO_EXTS = {
    ".heic", ".heif", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".avif",
    # raw
    ".dng", ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".srf", ".sr2",
    ".raf", ".orf", ".rw2", ".pef", ".raw", ".3fr", ".iiq",
}

# Junk that rides along in threads and is never a photo you want to edit.
SKIP_EXTS = {".gif", ".pluginpayloadattachment", ".caf", ".mov", ".mp4", ".pdf", ".vcf"}

STATE_FILENAME = ".afin_pull_state.json"

DEFAULT_CONFIG_PATHS = [
    Path.home() / ".config" / "afin-pull" / "config.json",
    Path.home() / ".afin-pull.json",
]


# ---------------------------------------------------------------- utilities

class Bail(SystemExit):
    """Fatal, user-facing error."""

    def __init__(self, msg: str) -> None:
        super().__init__(f"error: {msg}")


def log(msg: str = "") -> None:
    print(msg, file=sys.stderr)


def apple_to_unix(value) -> float:
    """Messages stores dates as seconds (old) or nanoseconds (new) since 2001."""
    if not value:
        return 0.0
    # Anything past ~1e11 can only be nanoseconds; real second-counts are ~8e8.
    if value > 1e11:
        return value / 1e9 + APPLE_EPOCH
    return value + APPLE_EPOCH


def parse_since(raw: str | None) -> float | None:
    """Accept '14d', '36h', '2w', an ISO date, or None."""
    if not raw:
        return None
    raw = raw.strip().lower()
    m = re.fullmatch(r"(\d+)\s*([dhw])", raw)
    if m:
        n = int(m.group(1))
        unit = {"h": "hours", "d": "days", "w": "weeks"}[m.group(2)]
        return (datetime.now(timezone.utc) - timedelta(**{unit: n})).timestamp()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except ValueError:
            continue
    raise Bail(f"could not read --since {raw!r}; try 14d, 36h, 2w or 2026-08-01")


def digits_only(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def phone_key(s: str) -> str:
    """Last 10 digits, so +1 555 123 4567 == (555) 123-4567."""
    d = digits_only(s)
    return d[-10:] if len(d) >= 10 else d


def sha256_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def human_bytes(n: int) -> str:
    step = 1024.0
    val = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if val < step:
            return f"{val:.0f}{unit}" if unit == "B" else f"{val:.1f}{unit}"
        val /= step
    return f"{val:.1f}TB"


# ---------------------------------------------------------------- contacts

def lookup_contact_handles(name: str) -> set[str]:
    """Resolve a contact name to their phone numbers / emails via AddressBook.

    Best effort: no Contacts database, or a schema we don't recognise, just
    means we fall back to matching on the thread name instead.
    """
    handles: set[str] = set()
    needle = name.strip().lower()
    if not needle:
        return handles

    for db_path in glob.glob(ADDRESSBOOK_GLOB):
        try:
            conn = open_sqlite_readonly(Path(db_path), copy_wal=False)
        except Exception:
            continue
        try:
            rows = conn.execute(
                """
                SELECT ZABCDRECORD.Z_PK,
                       COALESCE(ZABCDRECORD.ZFIRSTNAME, ''),
                       COALESCE(ZABCDRECORD.ZLASTNAME, ''),
                       COALESCE(ZABCDRECORD.ZORGANIZATION, ''),
                       COALESCE(ZABCDRECORD.ZNICKNAME, '')
                FROM ZABCDRECORD
                """
            ).fetchall()
        except sqlite3.Error:
            conn.close()
            continue

        matched_pks = set()
        for pk, first, last, org, nick in rows:
            haystack = " ".join(x for x in (first, last, org, nick) if x).lower()
            if needle in haystack or haystack.startswith(needle):
                matched_pks.add(pk)

        for pk in matched_pks:
            for table, column in (
                ("ZABCDPHONENUMBER", "ZFULLNUMBER"),
                ("ZABCDEMAILADDRESS", "ZADDRESS"),
            ):
                try:
                    for (value,) in conn.execute(
                        f"SELECT {column} FROM {table} WHERE ZOWNER = ?", (pk,)
                    ):
                        if value:
                            handles.add(value.strip())
                except sqlite3.Error:
                    pass
        conn.close()

    return handles


# ---------------------------------------------------------------- sqlite

_SCRATCH_DIRS: dict[int, Path] = {}


def open_sqlite_readonly(path: Path, copy_wal: bool = True) -> sqlite3.Connection:
    """Open a database read-only.

    Messages keeps chat.db in WAL mode and holds it open, which makes a plain
    read-only connection flaky. Copying the db plus its -wal/-shm sidecars to a
    scratch dir first gives us a stable, consistent snapshot and guarantees we
    never write to the user's real database.
    """
    if not path.exists():
        raise Bail(f"{path} not found")

    if not copy_wal:
        uri = f"file:{path}?mode=ro"
        return sqlite3.connect(uri, uri=True)

    scratch = Path(tempfile.mkdtemp(prefix="afin-pull-"))
    target = scratch / path.name
    try:
        shutil.copy2(path, target)
    except PermissionError:
        shutil.rmtree(scratch, ignore_errors=True)
        raise Bail(
            f"permission denied reading {path}\n"
            "  Grant Full Disk Access to your terminal:\n"
            "  System Settings > Privacy & Security > Full Disk Access,\n"
            "  add Terminal (or iTerm / Claude Code), then restart it."
        )
    for suffix in ("-wal", "-shm"):
        sidecar = path.with_name(path.name + suffix)
        if sidecar.exists():
            try:
                shutil.copy2(sidecar, target.with_name(target.name + suffix))
            except OSError:
                pass

    conn = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    conn.execute("PRAGMA query_only = ON")
    # sqlite3.Connection has no __dict__, so park the scratch dir alongside it.
    _SCRATCH_DIRS[id(conn)] = scratch
    return conn


def close_sqlite(conn: sqlite3.Connection) -> None:
    scratch = _SCRATCH_DIRS.pop(id(conn), None)
    conn.close()
    if scratch:
        shutil.rmtree(scratch, ignore_errors=True)


# ---------------------------------------------------------------- chat lookup

def list_chats(conn: sqlite3.Connection) -> list[dict]:
    """Every chat, with its participants and last-message time."""
    rows = conn.execute(
        """
        SELECT c.ROWID,
               COALESCE(c.display_name, ''),
               COALESCE(c.chat_identifier, ''),
               MAX(m.date)
        FROM chat c
        LEFT JOIN chat_message_join cmj ON cmj.chat_id = c.ROWID
        LEFT JOIN message m ON m.ROWID = cmj.message_id
        GROUP BY c.ROWID
        """
    ).fetchall()

    participants: dict[int, list[str]] = {}
    for chat_id, handle in conn.execute(
        """
        SELECT chj.chat_id, COALESCE(h.id, '')
        FROM chat_handle_join chj
        JOIN handle h ON h.ROWID = chj.handle_id
        """
    ):
        participants.setdefault(chat_id, []).append(handle)

    chats = []
    for chat_id, display_name, identifier, last_date in rows:
        chats.append(
            {
                "id": chat_id,
                "display_name": display_name,
                "identifier": identifier,
                "handles": participants.get(chat_id, []),
                "last_ts": apple_to_unix(last_date),
            }
        )
    chats.sort(key=lambda c: c["last_ts"], reverse=True)
    return chats


def resolve_chats(conn: sqlite3.Connection, query: str) -> list[dict]:
    """Find the chats matching a name, phone number, or email."""
    needle = query.strip().lower()
    if not needle:
        raise Bail("--from cannot be empty")

    contact_handles = lookup_contact_handles(query)
    contact_phone_keys = {phone_key(h) for h in contact_handles if digits_only(h)}
    contact_emails = {h.lower() for h in contact_handles if "@" in h}

    needle_phone = phone_key(needle) if digits_only(needle) else ""

    matches = []
    for chat in list_chats(conn):
        handles_lower = [h.lower() for h in chat["handles"]]
        handle_phone_keys = {phone_key(h) for h in chat["handles"] if digits_only(h)}

        hit = False
        if needle in chat["display_name"].lower() and chat["display_name"]:
            hit = True
        elif needle in chat["identifier"].lower() and chat["identifier"]:
            hit = True
        elif any(needle in h for h in handles_lower):
            hit = True
        elif needle_phone and needle_phone in handle_phone_keys:
            hit = True
        elif contact_phone_keys & handle_phone_keys:
            hit = True
        elif contact_emails & set(handles_lower):
            hit = True

        if hit:
            matches.append(chat)

    return matches


# ---------------------------------------------------------------- attachments

def fetch_attachments(conn: sqlite3.Connection, chat_ids: list[int]) -> list[dict]:
    if not chat_ids:
        return []
    placeholders = ",".join("?" for _ in chat_ids)
    rows = conn.execute(
        f"""
        SELECT DISTINCT
               a.ROWID,
               COALESCE(a.guid, ''),
               COALESCE(a.filename, ''),
               COALESCE(a.transfer_name, ''),
               COALESCE(a.mime_type, ''),
               COALESCE(a.total_bytes, 0),
               m.date,
               m.is_from_me,
               COALESCE(m.text, '')
        FROM attachment a
        JOIN message_attachment_join maj ON maj.attachment_id = a.ROWID
        JOIN message m ON m.ROWID = maj.message_id
        JOIN chat_message_join cmj ON cmj.message_id = m.ROWID
        WHERE cmj.chat_id IN ({placeholders})
        ORDER BY m.date ASC
        """,
        chat_ids,
    ).fetchall()

    out = []
    for (
        rowid, guid, filename, transfer_name, mime, total_bytes,
        date, is_from_me, text,
    ) in rows:
        out.append(
            {
                "rowid": rowid,
                "guid": guid,
                "path": Path(os.path.expanduser(filename)) if filename else None,
                "name": transfer_name or (Path(filename).name if filename else ""),
                "mime": mime,
                "bytes": total_bytes,
                "ts": apple_to_unix(date),
                "from_me": bool(is_from_me),
                "text": text,
            }
        )
    return out


def is_photo(att: dict, min_bytes: int) -> tuple[bool, str]:
    """Return (keep, reason-if-skipped)."""
    name = att["name"] or (att["path"].name if att["path"] else "")
    ext = Path(name).suffix.lower()

    if ext in SKIP_EXTS:
        return False, f"not a photo ({ext or 'no extension'})"
    if ext not in PHOTO_EXTS:
        if att["mime"].startswith("image/"):
            pass  # trust the mime type when the extension is missing/odd
        else:
            return False, f"not a photo ({ext or att['mime'] or 'unknown type'})"
    if att["bytes"] and att["bytes"] < min_bytes:
        return False, f"too small ({human_bytes(att['bytes'])}) - probably a sticker"
    return True, ""


# ---------------------------------------------------------------- destination

def find_dest_folder(pattern: str = r"afi?e.*edit") -> Path | None:
    """Hunt for the Lightroom edit folder in the usual places."""
    rx = re.compile(pattern, re.IGNORECASE)
    roots = [
        Path.home() / "Pictures",
        Path.home() / "Desktop",
        Path.home() / "Documents",
        Path.home() / "Dropbox",
    ]
    roots += [Path(p) for p in glob.glob("/Volumes/*")]

    for root in roots:
        if not root.is_dir():
            continue
        try:
            # Shallow walk -- these folders live near the top, and a deep scan
            # of a photo library is painfully slow.
            for depth_root, dirnames, _ in os.walk(root):
                depth = len(Path(depth_root).relative_to(root).parts)
                if depth >= 3:
                    dirnames[:] = []
                    continue
                for d in dirnames:
                    if rx.search(d):
                        return Path(depth_root) / d
        except (PermissionError, OSError):
            continue
    return None


# ---------------------------------------------------------------- state

def load_state(state_path: Path) -> dict:
    if not state_path.exists():
        return {"copied_guids": [], "copied_hashes": [], "last_run": 0}
    try:
        data = json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError):
        log(f"warning: could not read {state_path}, starting fresh")
        return {"copied_guids": [], "copied_hashes": [], "last_run": 0}
    data.setdefault("copied_guids", [])
    data.setdefault("copied_hashes", [])
    data.setdefault("last_run", 0)
    return data


def save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(state_path)


def load_config(explicit: Path | None) -> dict:
    paths = [explicit] if explicit else DEFAULT_CONFIG_PATHS
    for path in paths:
        if path and path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError) as exc:
                raise Bail(f"could not read config {path}: {exc}")
    return {}


# ---------------------------------------------------------------- main

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="afin_pull.py",
        description="Copy photos from a Messages thread into a Lightroom folder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  afin_pull.py --list-chats\n"
            "  afin_pull.py --dry-run\n"
            "  afin_pull.py --from AFIN --dest '~/Pictures/Afie Edit' --since 14d\n"
        ),
    )
    p.add_argument("--from", dest="sender", default=None,
                   help="contact name, phone, or email (default: AFIN)")
    p.add_argument("--dest", default=None,
                   help="destination folder (default: auto-detect 'Afie Edit')")
    p.add_argument("--since", default=None,
                   help="only messages newer than this: 14d, 36h, 2w, or 2026-08-01. "
                        "Default: everything since the last successful run.")
    p.add_argument("--all", action="store_true",
                   help="ignore the last-run marker and consider the whole thread")
    p.add_argument("--include-mine", action="store_true",
                   help="also copy photos you sent (default: only received)")
    p.add_argument("--min-bytes", type=int, default=50_000,
                   help="skip attachments smaller than this (default: 50000)")
    p.add_argument("--prefix", default=None,
                   help="filename prefix (default: the --from value, uppercased)")
    p.add_argument("--dry-run", action="store_true",
                   help="show what would be copied, copy nothing")
    p.add_argument("--list-chats", action="store_true",
                   help="list recent threads and exit (use this to find the name)")
    p.add_argument("--config", type=Path, default=None,
                   help="config file (default: ~/.config/afin-pull/config.json)")
    p.add_argument("--open", dest="open_after", action="store_true",
                   help="reveal the destination folder in Finder when done")
    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)

    if sys.platform != "darwin":
        raise Bail(
            "this only runs on macOS -- it reads the local Messages database.\n"
            "  Run it on your Mac, not in a cloud/Linux session."
        )

    cfg = load_config(args.config)
    sender = args.sender or cfg.get("from") or "AFIN"
    prefix = args.prefix or cfg.get("prefix") or re.sub(r"\W+", "", sender).upper() or "MSG"
    min_bytes = args.min_bytes if args.min_bytes != 50_000 else cfg.get("min_bytes", 50_000)
    include_mine = args.include_mine or cfg.get("include_mine", False)

    conn = open_sqlite_readonly(CHAT_DB)
    try:
        if args.list_chats:
            log("Recent threads (newest first):\n")
            for chat in list_chats(conn)[:40]:
                when = (
                    datetime.fromtimestamp(chat["last_ts"]).strftime("%Y-%m-%d")
                    if chat["last_ts"] else "  never  "
                )
                label = chat["display_name"] or ", ".join(chat["handles"]) or chat["identifier"]
                print(f"  {when}  {label}")
            return 0

        chats = resolve_chats(conn, sender)
        if not chats:
            raise Bail(
                f"no thread matched {sender!r}.\n"
                "  Run with --list-chats to see what's there, then pass the exact\n"
                "  name or phone number with --from."
            )

        chat_ids = [c["id"] for c in chats]
        labels = [c["display_name"] or ", ".join(c["handles"]) for c in chats]
        log(f"Thread: {'; '.join(labels)}  ({len(chat_ids)} chat(s))")

        # ---- destination
        dest_raw = args.dest or cfg.get("dest")
        if dest_raw:
            dest = Path(os.path.expanduser(dest_raw))
        else:
            log("Looking for the Lightroom edit folder...")
            found = find_dest_folder()
            if not found:
                raise Bail(
                    "could not find a folder matching 'Afie Edit'.\n"
                    "  Pass it explicitly:  --dest '~/Pictures/Afie Edit'\n"
                    "  (or save it once in ~/.config/afin-pull/config.json)"
                )
            dest = found
        log(f"Destination: {dest}")

        if not dest.exists():
            if args.dry_run:
                log(f"  (would create {dest})")
            else:
                dest.mkdir(parents=True, exist_ok=True)
                log("  created it")
        elif not dest.is_dir():
            raise Bail(f"{dest} exists but is not a folder")

        # ---- window
        state_path = dest / STATE_FILENAME
        state = load_state(state_path)
        if args.all:
            since_ts = None
        elif args.since:
            since_ts = parse_since(args.since)
        elif state["last_run"]:
            since_ts = state["last_run"]
        else:
            since_ts = parse_since("30d")
        if since_ts:
            log(f"Window: since {datetime.fromtimestamp(since_ts):%Y-%m-%d %H:%M}")
        else:
            log("Window: entire thread")

        # ---- select
        seen_guids = set(state["copied_guids"])
        seen_hashes = set(state["copied_hashes"])

        attachments = fetch_attachments(conn, chat_ids)
        candidates, skipped, missing = [], [], []

        for att in attachments:
            if since_ts and att["ts"] < since_ts:
                continue
            if att["from_me"] and not include_mine:
                continue
            keep, reason = is_photo(att, min_bytes)
            if not keep:
                skipped.append((att, reason))
                continue
            if att["guid"] and att["guid"] in seen_guids:
                skipped.append((att, "already pulled"))
                continue
            if not att["path"] or not att["path"].exists():
                missing.append(att)
                continue
            candidates.append(att)

        if missing:
            log(f"\n{len(missing)} attachment(s) are not downloaded to this Mac:")
            for att in missing[:10]:
                log(f"  - {att['name']}")
            if len(missing) > 10:
                log(f"  ... and {len(missing) - 10} more")
            log("  Open the thread in Messages and scroll to them, then re-run.")

        if not candidates:
            log("\nNothing new to pull.")
            if skipped:
                log(f"({len(skipped)} attachment(s) skipped: "
                    f"{skipped[0][1]}, etc.)")
            return 0

        # ---- copy
        log(f"\n{len(candidates)} photo(s) to pull:\n")
        copied = 0
        total_bytes = 0
        for att in candidates:
            src = att["path"]
            digest = sha256_of(src)
            if digest in seen_hashes:
                log(f"  skip  {att['name']}  (duplicate of one already here)")
                continue

            stamp = datetime.fromtimestamp(att["ts"]).strftime("%Y-%m-%d_%H%M%S")
            safe_name = re.sub(r"[^\w.\-]+", "_", att["name"] or src.name)
            target = dest / f"{prefix}_{stamp}_{safe_name}"

            n = 2
            while target.exists():
                target = dest / f"{prefix}_{stamp}_{n}_{safe_name}"
                n += 1

            size = src.stat().st_size
            if args.dry_run:
                log(f"  would copy  {target.name}  ({human_bytes(size)})")
            else:
                shutil.copy2(src, target)
                log(f"  copied  {target.name}  ({human_bytes(size)})")
                seen_hashes.add(digest)
                if att["guid"]:
                    seen_guids.add(att["guid"])
            copied += 1
            total_bytes += size

        if args.dry_run:
            log(f"\nDry run: {copied} photo(s), {human_bytes(total_bytes)}. "
                "Nothing was written.")
            return 0

        state["copied_guids"] = sorted(seen_guids)
        state["copied_hashes"] = sorted(seen_hashes)
        state["last_run"] = time.time()
        save_state(state_path, state)

        log(f"\nDone: {copied} photo(s), {human_bytes(total_bytes)} into {dest}")
        log("\nIn Lightroom Classic: File > Import Photos, point at that folder.")
        log("(Or set it as an Auto Import watched folder and they land by themselves.)")

        if args.open_after:
            subprocess.run(["open", "-R", str(dest)], check=False)

        return 0
    finally:
        close_sqlite(conn)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
