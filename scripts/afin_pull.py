#!/usr/bin/env python3
"""
Pull photo attachments out of a WhatsApp or Messages (iMessage/SMS) conversation
and drop them into a Lightroom import folder.

Built for the recurring "AFIN sent new rock pics, get them into the Afie Edit
folder" job, but the contact, source app, and destination are all configurable.

Runs on macOS only, with no third-party dependencies. Terminal (or whatever is
running it) needs Full Disk Access -- see README.md.

    ./scripts/afin_pull.py --list-chats
    ./scripts/afin_pull.py --dry-run
    ./scripts/afin_pull.py --from '+447700900123' --dest ~/Pictures/Afie\\ Edit
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

# WhatsApp has moved its data around across versions, so probe every layout we
# know about. The native Mac app uses a group container; the older Electron
# build used Application Support.
WHATSAPP_ROOTS = [
    Path.home() / "Library/Group Containers/group.net.whatsapp.WhatsApp.shared",
    Path.home() / "Library/Group Containers/group.net.whatsapp.family",
    Path.home() / "Library/Containers/desktop.WhatsApp/Data/Library/Application Support/WhatsApp",
    Path.home() / "Library/Application Support/WhatsApp",
]
WHATSAPP_DB_NAMES = ["ChatStorage.sqlite", "ChatSearchV5.sqlite"]

# Extensions we treat as "a photo worth editing".
PHOTO_EXTS = {
    ".heic", ".heif", ".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".avif",
    # raw
    ".dng", ".cr2", ".cr3", ".nef", ".nrw", ".arw", ".srf", ".sr2",
    ".raf", ".orf", ".rw2", ".pef", ".raw", ".3fr", ".iiq",
}

# Junk that rides along in threads and is never a photo you want to edit.
SKIP_EXTS = {
    ".gif", ".pluginpayloadattachment", ".caf", ".mov", ".mp4", ".pdf", ".vcf",
    ".opus", ".m4a", ".webm", ".thumb",
}

STATE_FILENAME = ".afin_pull_state.json"

DEFAULT_CONFIG_PATHS = [
    Path.home() / ".config" / "afin-pull" / "config.json",
    Path.home() / ".afin-pull.json",
]

_SCRATCH_DIRS: dict[int, Path] = {}


# ---------------------------------------------------------------- utilities

class Bail(SystemExit):
    """Fatal, user-facing error."""

    def __init__(self, msg: str) -> None:
        super().__init__(f"error: {msg}")


def log(msg: str = "") -> None:
    print(msg, file=sys.stderr)


def apple_to_unix(value) -> float:
    """Apple stores dates as seconds (Core Data) or nanoseconds (newer Messages)."""
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
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc).timestamp()
        except ValueError:
            continue
    raise Bail(f"could not read --since {raw!r}; try 14d, 36h, 2w or 2026-08-01")


def digits_only(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def phone_key(s: str) -> str:
    """Last 10 digits, so +44 7700 900123 == 07700 900123 == 447700900123."""
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
    val = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if val < 1024.0:
            return f"{val:.0f}{unit}" if unit == "B" else f"{val:.1f}{unit}"
        val /= 1024.0
    return f"{val:.1f}TB"


# ---------------------------------------------------------------- sqlite

def open_sqlite_readonly(path: Path, copy_wal: bool = True) -> sqlite3.Connection:
    """Open a database read-only.

    Both Messages and WhatsApp keep their databases in WAL mode and hold them
    open, which makes a plain read-only connection flaky. Copying the db plus
    its -wal/-shm sidecars to a scratch dir first gives a stable snapshot and
    guarantees we never write to the user's real data.
    """
    if not path.exists():
        raise Bail(f"{path} not found")

    if not copy_wal:
        return sqlite3.connect(f"file:{path}?mode=ro", uri=True)

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


def table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """WhatsApp renames columns between versions, so never assume a schema."""
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    except sqlite3.Error:
        return set()


def pick_column(available: set[str], *candidates: str) -> str | None:
    for name in candidates:
        if name in available:
            return name
    return None


# ---------------------------------------------------------------- contacts

def lookup_contact_handles(name: str) -> set[str]:
    """Resolve a contact name to phone numbers / emails via the Contacts database.

    Best effort: no Contacts database, or a schema we don't recognise, just means
    we fall back to matching on the thread name instead.
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
                SELECT Z_PK,
                       COALESCE(ZFIRSTNAME, ''), COALESCE(ZLASTNAME, ''),
                       COALESCE(ZORGANIZATION, ''), COALESCE(ZNICKNAME, '')
                FROM ZABCDRECORD
                """
            ).fetchall()
        except sqlite3.Error:
            conn.close()
            continue

        matched = {
            pk for pk, first, last, org, nick in rows
            if needle in " ".join(x for x in (first, last, org, nick) if x).lower()
        }
        for pk in matched:
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


def chat_matches(query: str, label: str, handles: list[str],
                 contact_handles: set[str]) -> bool:
    """Does this thread match what the user typed?"""
    needle = query.strip().lower()
    handles_lower = [h.lower() for h in handles]
    handle_keys = {phone_key(h) for h in handles if digits_only(h)}

    contact_keys = {phone_key(h) for h in contact_handles if digits_only(h)}
    contact_emails = {h.lower() for h in contact_handles if "@" in h}
    needle_key = phone_key(needle) if digits_only(needle) else ""

    if label and needle in label.lower():
        return True
    if any(needle in h for h in handles_lower):
        return True
    if needle_key and needle_key in handle_keys:
        return True
    if contact_keys & handle_keys:
        return True
    if contact_emails & set(handles_lower):
        return True
    return False


# ---------------------------------------------------------------- Messages

def messages_list_chats(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT c.ROWID, COALESCE(c.display_name, ''),
               COALESCE(c.chat_identifier, ''), MAX(m.date)
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
        FROM chat_handle_join chj JOIN handle h ON h.ROWID = chj.handle_id
        """
    ):
        participants.setdefault(chat_id, []).append(handle)

    chats = [
        {
            "source": "messages",
            "id": chat_id,
            "label": display_name or identifier,
            "handles": participants.get(chat_id, []),
            "last_ts": apple_to_unix(last_date),
        }
        for chat_id, display_name, identifier, last_date in rows
    ]
    chats.sort(key=lambda c: c["last_ts"], reverse=True)
    return chats


def messages_fetch_attachments(conn: sqlite3.Connection,
                               chat_ids: list[int]) -> list[dict]:
    if not chat_ids:
        return []
    placeholders = ",".join("?" for _ in chat_ids)
    rows = conn.execute(
        f"""
        SELECT DISTINCT a.ROWID, COALESCE(a.guid, ''), COALESCE(a.filename, ''),
               COALESCE(a.transfer_name, ''), COALESCE(a.mime_type, ''),
               COALESCE(a.total_bytes, 0), m.date, m.is_from_me
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
    for rowid, guid, filename, transfer, mime, total, date, from_me in rows:
        path = Path(os.path.expanduser(filename)) if filename else None
        out.append({
            "guid": guid or f"msg:{rowid}",
            "path": path,
            "name": transfer or (path.name if path else ""),
            "mime": mime,
            "bytes": total,
            "ts": apple_to_unix(date),
            "from_me": bool(from_me),
        })
    return out


# ---------------------------------------------------------------- WhatsApp

def find_whatsapp_store() -> tuple[Path | None, Path | None]:
    """Locate (ChatStorage.sqlite, media root). Either may be None."""
    db_path = media_root = None
    for root in WHATSAPP_ROOTS:
        if not root.is_dir():
            continue
        if db_path is None:
            for name in WHATSAPP_DB_NAMES:
                for candidate in (root / name, root / "Message" / name):
                    if candidate.is_file():
                        db_path = candidate
                        break
                if db_path:
                    break
        if media_root is None:
            for candidate in (root / "Message", root / "Media", root):
                if (candidate / "Media").is_dir():
                    media_root = candidate
                    break
        if db_path and media_root:
            break
    return db_path, media_root


def whatsapp_list_chats(conn: sqlite3.Connection) -> list[dict]:
    cols = table_columns(conn, "ZWACHATSESSION")
    if not cols:
        return []
    jid_col = pick_column(cols, "ZCONTACTJID", "ZJID")
    name_col = pick_column(cols, "ZPARTNERNAME", "ZDISPLAYNAME", "ZNAME")
    date_col = pick_column(cols, "ZLASTMESSAGEDATE", "ZMESSAGEDATE")
    if not jid_col:
        return []

    select = f"SELECT Z_PK, COALESCE({jid_col}, '')"
    select += f", COALESCE({name_col}, '')" if name_col else ", ''"
    select += f", {date_col}" if date_col else ", 0"
    select += " FROM ZWACHATSESSION"

    chats = []
    try:
        for pk, jid, name, last in conn.execute(select):
            # JIDs look like 447700900123@s.whatsapp.net or ...@g.us for groups
            number = jid.split("@", 1)[0]
            chats.append({
                "source": "whatsapp",
                "id": pk,
                "jid": jid,
                "label": name or number,
                "handles": [number] if number.isdigit() else [jid],
                "last_ts": apple_to_unix(last),
            })
    except sqlite3.Error as exc:
        log(f"warning: could not read WhatsApp chat list ({exc})")
        return []

    chats.sort(key=lambda c: c["last_ts"], reverse=True)
    return chats


def whatsapp_fetch_attachments(conn: sqlite3.Connection, chat_ids: list[int],
                               media_root: Path | None) -> list[dict]:
    if not chat_ids:
        return []
    msg_cols = table_columns(conn, "ZWAMESSAGE")
    media_cols = table_columns(conn, "ZWAMEDIAITEM")
    if not msg_cols or not media_cols:
        return []

    session_col = pick_column(msg_cols, "ZCHATSESSION", "ZCHATSESSIONID")
    date_col = pick_column(msg_cols, "ZMESSAGEDATE", "ZSENTDATE")
    from_me_col = pick_column(msg_cols, "ZISFROMME", "ZFROMME")
    link_col = pick_column(media_cols, "ZMESSAGE", "ZMESSAGEID")
    path_col = pick_column(media_cols, "ZMEDIALOCALPATH", "ZLOCALPATH", "ZMEDIAPATH")
    size_col = pick_column(media_cols, "ZFILESIZE", "ZMEDIASIZE")
    # ZVCARDSTRING doubles as the mime type on media rows -- a schema quirk.
    mime_col = pick_column(media_cols, "ZVCARDSTRING", "ZMIMETYPE")
    title_col = pick_column(media_cols, "ZTITLE", "ZMEDIANAME")

    if not (session_col and link_col and path_col):
        return []

    placeholders = ",".join("?" for _ in chat_ids)
    select = f"""
        SELECT mi.Z_PK, COALESCE(mi.{path_col}, ''),
               {f'COALESCE(mi.{size_col}, 0)' if size_col else '0'},
               {f"COALESCE(mi.{mime_col}, '')" if mime_col else "''"},
               {f"COALESCE(mi.{title_col}, '')" if title_col else "''"},
               {f'm.{date_col}' if date_col else '0'},
               {f'COALESCE(m.{from_me_col}, 0)' if from_me_col else '0'}
        FROM ZWAMEDIAITEM mi
        JOIN ZWAMESSAGE m ON mi.{link_col} = m.Z_PK
        WHERE m.{session_col} IN ({placeholders})
    """
    try:
        rows = conn.execute(select, chat_ids).fetchall()
    except sqlite3.Error as exc:
        log(f"warning: could not read WhatsApp media table ({exc})")
        return []

    out = []
    for pk, rel_path, size, mime, title, date, from_me in rows:
        if not rel_path:
            continue
        path = Path(rel_path)
        if not path.is_absolute() and media_root:
            path = media_root / rel_path
        out.append({
            "guid": f"wa:{pk}",
            "path": path,
            "name": title or path.name,
            "mime": mime if "/" in (mime or "") else "",
            "bytes": size,
            "ts": apple_to_unix(date),
            "from_me": bool(from_me),
        })
    out.sort(key=lambda a: a["ts"])
    return out


def whatsapp_scan_media_folder(media_root: Path, jids: list[str]) -> list[dict]:
    """Fallback when the database is unreadable.

    WhatsApp files received media under Media/<JID>/, so we can find the photos
    without parsing anything -- less metadata, but it works when the schema has
    moved or the db is locked.
    """
    found = []
    media_dir = media_root / "Media"
    if not media_dir.is_dir():
        return found

    wanted_keys = {phone_key(j.split("@", 1)[0]) for j in jids}
    for entry in media_dir.iterdir():
        if not entry.is_dir():
            continue
        if phone_key(entry.name.split("@", 1)[0]) not in wanted_keys:
            continue
        for path in entry.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in PHOTO_EXTS:
                continue
            try:
                stat = path.stat()
            except OSError:
                continue
            found.append({
                "guid": f"wafile:{path}",
                "path": path,
                "name": path.name,
                "mime": "",
                "bytes": stat.st_size,
                "ts": stat.st_mtime,
                "from_me": False,
            })
    found.sort(key=lambda a: a["ts"])
    return found


# ---------------------------------------------------------------- filtering

def is_photo(att: dict, min_bytes: int) -> tuple[bool, str]:
    name = att["name"] or (att["path"].name if att["path"] else "")
    ext = Path(name).suffix.lower()

    if ext in SKIP_EXTS:
        return False, f"not a photo ({ext})"
    if ext not in PHOTO_EXTS and not att["mime"].startswith("image/"):
        return False, f"not a photo ({ext or att['mime'] or 'unknown type'})"
    if att["bytes"] and att["bytes"] < min_bytes:
        return False, f"too small ({human_bytes(att['bytes'])}) - probably a sticker"
    return True, ""


# ---------------------------------------------------------------- destination

def find_dest_folder(pattern: str = r"afi?e.*edit") -> Path | None:
    rx = re.compile(pattern, re.IGNORECASE)
    roots = [Path.home() / d for d in ("Pictures", "Desktop", "Documents", "Dropbox")]
    roots += [Path(p) for p in glob.glob("/Volumes/*")]

    for root in roots:
        if not root.is_dir():
            continue
        try:
            for dirpath, dirnames, _ in os.walk(root):
                # Shallow walk -- these folders live near the top, and a deep
                # scan of a photo library is painfully slow.
                if len(Path(dirpath).relative_to(root).parts) >= 3:
                    dirnames[:] = []
                    continue
                for d in dirnames:
                    if rx.search(d):
                        return Path(dirpath) / d
        except (PermissionError, OSError):
            continue
    return None


# ---------------------------------------------------------------- state

def load_state(state_path: Path) -> dict:
    blank = {"copied_guids": [], "copied_hashes": [], "last_run": 0}
    if not state_path.exists():
        return blank
    try:
        data = json.loads(state_path.read_text())
    except (json.JSONDecodeError, OSError):
        log(f"warning: could not read {state_path}, starting fresh")
        return blank
    for key, default in blank.items():
        data.setdefault(key, default)
    return data


def save_state(state_path: Path, state: dict) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(state_path)


def load_config(explicit: Path | None) -> dict:
    for path in ([explicit] if explicit else DEFAULT_CONFIG_PATHS):
        if path and path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError) as exc:
                raise Bail(f"could not read config {path}: {exc}")
    return {}


# ---------------------------------------------------------------- gathering

def gather(source: str, sender: str, want_list: bool) -> tuple[list[dict], list[dict], list[str]]:
    """Return (chats, attachments, notes) for the requested source(s)."""
    chats: list[dict] = []
    attachments: list[dict] = []
    notes: list[str] = []
    contact_handles = lookup_contact_handles(sender) if sender else set()

    if source in ("auto", "whatsapp"):
        db_path, media_root = find_whatsapp_store()
        if db_path is None and media_root is None:
            notes.append("WhatsApp: no local data found on this Mac")
        else:
            wa_chats: list[dict] = []
            conn = None
            if db_path:
                try:
                    conn = open_sqlite_readonly(db_path)
                    wa_chats = whatsapp_list_chats(conn)
                except Bail as exc:
                    notes.append(f"WhatsApp: {exc}")
                except sqlite3.Error as exc:
                    notes.append(f"WhatsApp: database unreadable ({exc})")
            try:
                if want_list:
                    chats.extend(wa_chats)
                else:
                    matched = [
                        c for c in wa_chats
                        if chat_matches(sender, c["label"], c["handles"], contact_handles)
                    ]
                    chats.extend(matched)
                    if matched and conn:
                        attachments.extend(whatsapp_fetch_attachments(
                            conn, [c["id"] for c in matched], media_root))
                    if matched and not attachments and media_root:
                        notes.append("WhatsApp: database gave nothing, scanning the media folder")
                        attachments.extend(whatsapp_scan_media_folder(
                            media_root, [c["jid"] for c in matched]))
                    elif not matched and media_root and not wa_chats:
                        # No readable db at all -- try matching folders by number.
                        scanned = whatsapp_scan_media_folder(media_root, [sender])
                        if scanned:
                            notes.append("WhatsApp: matched by media folder (no database)")
                            chats.append({
                                "source": "whatsapp", "id": -1, "jid": sender,
                                "label": f"{sender} (media folder)",
                                "handles": [sender], "last_ts": 0,
                            })
                            attachments.extend(scanned)
            finally:
                if conn:
                    close_sqlite(conn)

    if source in ("auto", "messages"):
        if not CHAT_DB.exists():
            notes.append("Messages: no chat.db on this Mac")
        else:
            conn = open_sqlite_readonly(CHAT_DB)
            try:
                msg_chats = messages_list_chats(conn)
                if want_list:
                    chats.extend(msg_chats)
                else:
                    matched = [
                        c for c in msg_chats
                        if chat_matches(sender, c["label"], c["handles"], contact_handles)
                    ]
                    chats.extend(matched)
                    if matched:
                        attachments.extend(
                            messages_fetch_attachments(conn, [c["id"] for c in matched]))
            finally:
                close_sqlite(conn)

    return chats, attachments, notes


# ---------------------------------------------------------------- main

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="afin_pull.py",
        description="Copy photos from a WhatsApp or Messages thread into a Lightroom folder.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  afin_pull.py --list-chats\n"
            "  afin_pull.py --dry-run\n"
            "  afin_pull.py --from '+447700900123' --dest '~/Pictures/Afie Edit'\n"
        ),
    )
    p.add_argument("--from", dest="sender", default=None,
                   help="contact name, phone number, or email (default: AFIN)")
    p.add_argument("--source", choices=("auto", "whatsapp", "messages"), default=None,
                   help="which app to read (default: auto, tries both)")
    p.add_argument("--dest", default=None,
                   help="destination folder (default: auto-detect 'Afie Edit')")
    p.add_argument("--since", default=None,
                   help="only messages newer than this: 14d, 36h, 2w, or 2026-08-01")
    p.add_argument("--all", action="store_true",
                   help="ignore the last-run marker and consider the whole thread")
    p.add_argument("--include-mine", action="store_true",
                   help="also copy photos you sent (default: only received)")
    p.add_argument("--min-bytes", type=int, default=None,
                   help="skip attachments smaller than this (default: 50000)")
    p.add_argument("--prefix", default=None,
                   help="filename prefix (default: the --from value)")
    p.add_argument("--dry-run", action="store_true",
                   help="show what would be copied, copy nothing")
    p.add_argument("--list-chats", action="store_true",
                   help="list recent threads from both apps and exit")
    p.add_argument("--config", type=Path, default=None,
                   help="config file (default: ~/.config/afin-pull/config.json)")
    p.add_argument("--open", dest="open_after", action="store_true",
                   help="reveal the destination folder in Finder when done")
    return p


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv)

    if sys.platform != "darwin":
        raise Bail(
            "this only runs on macOS -- it reads WhatsApp and Messages data\n"
            "  stored on your Mac. Run it there, not in a cloud/Linux session."
        )

    cfg = load_config(args.config)
    sender = args.sender or cfg.get("from") or "AFIN"
    source = args.source or cfg.get("source") or "auto"
    prefix = args.prefix or cfg.get("prefix") or re.sub(r"\W+", "", sender).upper() or "MSG"
    min_bytes = args.min_bytes if args.min_bytes is not None else cfg.get("min_bytes", 50_000)
    include_mine = args.include_mine or cfg.get("include_mine", False)

    # ---- list mode
    if args.list_chats:
        chats, _, notes = gather(source, sender, want_list=True)
        for note in notes:
            log(f"note: {note}")
        if not chats:
            raise Bail("no threads found in either app")
        log("\nRecent threads (newest first):\n")
        for chat in sorted(chats, key=lambda c: c["last_ts"], reverse=True)[:50]:
            when = (datetime.fromtimestamp(chat["last_ts"]).strftime("%Y-%m-%d")
                    if chat["last_ts"] else "   --   ")
            tag = "WhatsApp" if chat["source"] == "whatsapp" else "Messages"
            handles = ", ".join(chat["handles"])
            label = chat["label"] or handles
            extra = f"  [{handles}]" if handles and handles != label else ""
            print(f"  {when}  {tag:9} {label}{extra}")
        return 0

    chats, attachments, notes = gather(source, sender, want_list=False)
    for note in notes:
        log(f"note: {note}")

    if not chats:
        raise Bail(
            f"no thread matched {sender!r}.\n"
            "  Run with --list-chats to see what's there, then pass the exact\n"
            "  name or number, e.g. --from '+447700900123'."
        )
    log(f"Thread: {'; '.join(c['label'] for c in chats)}")

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
                "  Pass it explicitly:  --dest '~/Pictures/Afie Edit'"
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
    else:
        since_ts = state["last_run"] or parse_since("30d")
    log(f"Window: since {datetime.fromtimestamp(since_ts):%Y-%m-%d %H:%M}"
        if since_ts else "Window: entire thread")

    # ---- select
    seen_guids = set(state["copied_guids"])
    seen_hashes = set(state["copied_hashes"])
    candidates, skipped, missing = [], [], []

    for att in attachments:
        if since_ts and att["ts"] < since_ts:
            continue
        if att["from_me"] and not include_mine:
            continue
        keep, reason = is_photo(att, min_bytes)
        if not keep:
            skipped.append((att, reason))
        elif att["guid"] in seen_guids:
            skipped.append((att, "already pulled"))
        elif not att["path"] or not att["path"].exists():
            missing.append(att)
        else:
            candidates.append(att)

    if missing:
        log(f"\n{len(missing)} photo(s) are not downloaded to this Mac:")
        for att in missing[:10]:
            log(f"  - {att['name']}")
        if len(missing) > 10:
            log(f"  ... and {len(missing) - 10} more")
        log("  Open the chat and scroll to them so they download, then re-run.")

    if not candidates:
        log("\nNothing new to pull.")
        if skipped:
            log(f"({len(skipped)} attachment(s) skipped, e.g. {skipped[0][1]})")
        return 0

    # ---- copy
    log(f"\n{len(candidates)} photo(s) to pull:\n")
    copied = total_bytes = 0
    for att in candidates:
        src = att["path"]
        digest = sha256_of(src)
        if digest in seen_hashes:
            log(f"  skip  {att['name']}  (duplicate of one already here)")
            continue

        stamp = datetime.fromtimestamp(att["ts"]).strftime("%Y-%m-%d_%H%M%S")
        safe = re.sub(r"[^\w.\-]+", "_", att["name"] or src.name)
        target = dest / f"{prefix}_{stamp}_{safe}"
        n = 2
        while target.exists():
            target = dest / f"{prefix}_{stamp}_{n}_{safe}"
            n += 1

        size = src.stat().st_size
        if args.dry_run:
            log(f"  would copy  {target.name}  ({human_bytes(size)})")
        else:
            shutil.copy2(src, target)
            log(f"  copied  {target.name}  ({human_bytes(size)})")
            seen_hashes.add(digest)
            seen_guids.add(att["guid"])
        copied += 1
        total_bytes += size

    if args.dry_run:
        log(f"\nDry run: {copied} photo(s), {human_bytes(total_bytes)}. Nothing written.")
        return 0

    state.update(copied_guids=sorted(seen_guids), copied_hashes=sorted(seen_hashes),
                 last_run=time.time())
    save_state(state_path, state)

    log(f"\nDone: {copied} photo(s), {human_bytes(total_bytes)} into {dest}")
    log("\nIn Lightroom Classic: File > Import Photos, point at that folder.")
    log("(Or set it as an Auto Import watched folder and they land by themselves.)")

    if args.open_after:
        subprocess.run(["open", "-R", str(dest)], check=False)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
