# AfroVibe

A browser-based music app with a neon theme, an original Highlife-inspired demo loop, local audio, YouTube embeds, and editable playlists.

**GitHub Pages frontend:** https://rajeshwar01-01.github.io/gana-music-app/

## Frontend

The app is a single HTML page. It supports local audio, likes, search and filters, YouTube video and playlist embeds, and local playlists. Export a playlist as JSON to pass YouTube links to another user.

YouTube playback uses the official embedded player. The app does not download YouTube audio. Some videos may be private, unavailable in your region, or disallow embedding. Import music and links you have permission to use.

## Backend: SQLite playlist API

`server.py` uses only the Python standard library. It serves `index.html` and a SQLite-backed API from the same origin.

Run it locally:

```sh
python server.py
```

Then open http://localhost:8000/. The database is created at `data/afrovibe.sqlite3`. Set `PORT` and `AFROVIBE_DB` to choose a different port or a persistent database path.

### Online playlist sharing

When the page is served by `server.py`, **Share online** publishes the selected playlist and copies a share link. The API stores only YouTube links and names, never audio. Anyone with the share URL can view/import a copy. Only the creator's browser, which stores the private owner token, can update that shared playlist. Importing a link makes a separate copy that another user can edit and publish.

The API is intentionally same-origin. Host the HTML and Python server together over HTTPS with a persistent disk to enable online sharing for everyone. GitHub Pages serves the static frontend only, so its current public page continues to support local playlists and JSON export/import; it cannot run this API. The Vercel account connection currently has no access to the selected team, so no hosted API was deployed.

Local audio remains in the current browser and is never included in a shared link or JSON playlist.
