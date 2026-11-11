# AfroVibe

A browser-based music app with a neon theme, an original Highlife-inspired demo loop, local audio, YouTube embeds, and editable playlists.

**Public frontend:** https://rajeshwar01-01.github.io/gana-music-app/

## Frontend

The app is a single HTML page. It supports local audio, likes, search and filters, YouTube video and playlist embeds, and local playlists. Export a playlist as JSON to pass YouTube links to another user.

YouTube playback uses the official embedded player. The app does not download YouTube audio. Some videos may be private, unavailable in your region, or disallow embedding. Import music and links you have permission to use.

## Backend: SQLite playlist API

`server.py` uses only the Python standard library. It serves `index.html` and a SQLite-backed API from the same origin.

Run it locally:

```sh
python server.py
```

Open http://localhost:8000/. The database is created at `data/afrovibe.sqlite3`. Set `PORT`, `HOST`, and `AFROVIBE_DB` to choose the listen address, port, or persistent database path. For a public host, bind to `0.0.0.0` and put the app behind HTTPS.

### Online playlist sharing

When served by `server.py`, **Share online** publishes the selected playlist and copies a share link. The API stores YouTube links and titles, never audio. Anyone with the share URL can view or import a copy. Only the creator's browser, which keeps the private owner token, can update the original playlist. Importing a link makes a separate copy another user can edit and publish.

The backend and page should be hosted together over HTTPS with persistent disk to enable online sharing. GitHub Pages can serve the static frontend, but cannot run this API; its public page therefore supports local playlists and JSON import/export until a backend host is configured. Deploy `server.py` on a Python host that preserves the SQLite file between restarts, and point users to that host's URL.

Local audio stays in the current browser and is never included in shared links or JSON playlists.
