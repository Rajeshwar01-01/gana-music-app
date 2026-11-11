#!/usr/bin/env python3
"""AfroVibe's small SQLite-backed API and static HTML server.

Run with: python server.py
The API and page share one origin. SQLite keeps playlists durable between restarts.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("AFROVIBE_DB", ROOT / "data" / "afrovibe.sqlite3"))
PORT = int(os.environ.get("PORT", "8000"))
HOST = os.environ.get("HOST", "0.0.0.0")
MAX_BODY = 128_000
MAX_TRACKS = 100
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
PLAYLIST_ID = re.compile(r"^[A-Za-z0-9_-]{5,120}$")


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message


def connect_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def initialize_db() -> None:
    with connect_db() as db:
        db.executescript(
            """
            CREATE TABLE IF NOT EXISTS playlists (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                owner_token_hash TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                playlist_id TEXT NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
                position INTEGER NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                PRIMARY KEY (playlist_id, position)
            );
            """
        )


def parse_youtube_url(value: object) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("Each track must have a YouTube URL.")
    parsed = urlsplit(value.strip())
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or host not in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "music.youtube.com",
        "youtu.be",
    }:
        raise ValueError("Only YouTube video or playlist links are accepted.")

    query = parse_qs(parsed.query)
    video_id = (query.get("v") or [""])[0]
    list_id = (query.get("list") or [""])[0]
    if host == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]

    if not video_id:
        match = re.match(r"^/(?:shorts|embed|live)/([^/]+)", parsed.path)
        if match:
            video_id = match.group(1)

    if video_id and not VIDEO_ID.fullmatch(video_id):
        raise ValueError("That YouTube video link is invalid.")
    if list_id and not PLAYLIST_ID.fullmatch(list_id):
        raise ValueError("That YouTube playlist link is invalid.")
    if not video_id and not list_id:
        raise ValueError("The YouTube link needs a video or playlist ID.")

    if video_id:
        suffix = "&list=" + list_id if list_id else ""
        return "https://www.youtube.com/watch?v=" + video_id + suffix
    return "https://www.youtube.com/playlist?list=" + list_id


def normalize_playlist(payload: object) -> tuple[str, list[dict[str, str]]]:
    if not isinstance(payload, dict):
        raise ValueError("Send a JSON object.")
    name = payload.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Playlist name is required.")
    name = name.strip()[:48]

    raw_tracks = payload.get("tracks")
    if not isinstance(raw_tracks, list) or len(raw_tracks) > MAX_TRACKS:
        raise ValueError("A playlist can contain up to 100 YouTube links.")
    tracks: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw_tracks:
        if isinstance(item, str):
            url, title = item, "YouTube track"
        elif isinstance(item, dict):
            url = item.get("url")
            title = item.get("title", "YouTube track")
        else:
            raise ValueError("A track entry is invalid.")
        normalized = parse_youtube_url(url)
        if normalized in seen:
            continue
        if not isinstance(title, str):
            title = "YouTube track"
        title = " ".join(title.split())[:160] or "YouTube track"
        tracks.append({"url": normalized, "title": title})
        seen.add(normalized)
    if not tracks:
        raise ValueError("Add at least one YouTube link.")
    return name, tracks


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class Handler(BaseHTTPRequestHandler):
    server_version = "AfroVibeAPI/1.0"

    def send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ApiError(400, "Invalid request length.") from exc
        if length < 1 or length > MAX_BODY:
            raise ApiError(413, "Request body is empty or too large.")
        try:
            value = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ApiError(400, "Request body must be valid JSON.") from exc
        if not isinstance(value, dict):
            raise ApiError(400, "Send a JSON object.")
        return value

    def send_playlist(self, playlist_id: str) -> None:
        with connect_db() as db:
            row = db.execute(
                "SELECT id, name, updated_at FROM playlists WHERE id = ?",
                (playlist_id,),
            ).fetchone()
            if row is None:
                raise ApiError(404, "Playlist not found.")
            tracks = db.execute(
                "SELECT url, title FROM playlist_tracks WHERE playlist_id = ? ORDER BY position",
                (playlist_id,),
            ).fetchall()
        self.send_json(
            200,
            {
                "id": row["id"],
                "name": row["name"],
                "updatedAt": row["updated_at"],
                "tracks": [dict(track) for track in tracks],
            },
        )

    def owner_token_matches(self, db: sqlite3.Connection, playlist_id: str) -> bool:
        supplied = self.headers.get("X-Owner-Token", "")
        row = db.execute(
            "SELECT owner_token_hash FROM playlists WHERE id = ?",
            (playlist_id,),
        ).fetchone()
        return bool(
            row
            and supplied
            and hmac.compare_digest(row["owner_token_hash"], token_hash(supplied))
        )

    def request_is_same_origin(self) -> bool:
        origin = self.headers.get("Origin")
        if not origin:
            return True
        return urlsplit(origin).netloc.lower() == self.headers.get("Host", "").lower()

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/api/health":
            self.send_json(200, {"ok": True, "service": "afrovibe-api", "version": 1})
            return
        if path.startswith("/api/playlists/"):
            playlist_id = path.removeprefix("/api/playlists/")
            try:
                uuid.UUID(playlist_id)
            except ValueError:
                self.send_json(400, {"error": "Invalid playlist ID."})
                return
            try:
                self.send_playlist(playlist_id)
            except ApiError as exc:
                self.send_json(exc.status, {"error": exc.message})
            return
        if path not in ("/", "/index.html"):
            self.send_json(404, {"error": "Not found."})
            return
        page = ROOT / "index.html"
        if not page.is_file():
            self.send_json(404, {"error": "index.html is missing."})
            return
        body = page.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if not self.request_is_same_origin():
            self.send_json(403, {"error": "Cross-origin writes are not allowed."})
            return
        if urlsplit(self.path).path != "/api/playlists":
            self.send_json(404, {"error": "Not found."})
            return
        try:
            name, tracks = normalize_playlist(self.read_json())
        except ApiError as exc:
            self.send_json(exc.status, {"error": exc.message})
            return
        except ValueError as exc:
            self.send_json(400, {"error": str(exc)})
            return

        playlist_id = str(uuid.uuid4())
        owner_token = secrets.token_urlsafe(32)
        updated_at = now_iso()
        with connect_db() as db:
            db.execute(
                "INSERT INTO playlists(id, name, owner_token_hash, updated_at) VALUES (?, ?, ?, ?)",
                (playlist_id, name, token_hash(owner_token), updated_at),
            )
            db.executemany(
                "INSERT INTO playlist_tracks(playlist_id, position, url, title) VALUES (?, ?, ?, ?)",
                [(playlist_id, i, track["url"], track["title"]) for i, track in enumerate(tracks)],
            )
        self.send_json(
            201,
            {
                "id": playlist_id,
                "name": name,
                "updatedAt": updated_at,
                "ownerToken": owner_token,
            },
        )

    def do_PUT(self) -> None:
        if not self.request_is_same_origin():
            self.send_json(403, {"error": "Cross-origin writes are not allowed."})
            return
        playlist_id = urlsplit(self.path).path.removeprefix("/api/playlists/")
        try:
            uuid.UUID(playlist_id)
        except ValueError:
            self.send_json(400, {"error": "Invalid playlist ID."})
            return
        try:
            name, tracks = normalize_playlist(self.read_json())
        except ApiError as exc:
            self.send_json(exc.status, {"error": exc.message})
            return
        except ValueError as exc:
            self.send_json(400, {"error": str(exc)})
            return

        updated_at = now_iso()
        with connect_db() as db:
            if not self.owner_token_matches(db, playlist_id):
                self.send_json(403, {"error": "Only the playlist owner can update it."})
                return
            db.execute(
                "UPDATE playlists SET name = ?, updated_at = ? WHERE id = ?",
                (name, updated_at, playlist_id),
            )
            db.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
            db.executemany(
                "INSERT INTO playlist_tracks(playlist_id, position, url, title) VALUES (?, ?, ?, ?)",
                [(playlist_id, i, track["url"], track["title"]) for i, track in enumerate(tracks)],
            )
        self.send_json(200, {"id": playlist_id, "name": name, "updatedAt": updated_at})

    def do_DELETE(self) -> None:
        if not self.request_is_same_origin():
            self.send_json(403, {"error": "Cross-origin writes are not allowed."})
            return
        playlist_id = urlsplit(self.path).path.removeprefix("/api/playlists/")
        try:
            uuid.UUID(playlist_id)
        except ValueError:
            self.send_json(400, {"error": "Invalid playlist ID."})
            return
        with connect_db() as db:
            if not self.owner_token_matches(db, playlist_id):
                self.send_json(403, {"error": "Only the playlist owner can delete it."})
                return
            db.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
        self.send_json(200, {"ok": True})

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.log_date_time_string()} {format % args}")


if __name__ == "__main__":
    initialize_db()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"AfroVibe is available at http://localhost:{PORT}/")
    print(f"SQLite database: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping AfroVibe.")
    finally:
        server.server_close()
