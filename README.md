# AfroVibe

AfroVibe is a browser-based music player with a Gen Z neon theme, an original Highlife-inspired demo loop, local audio, YouTube embeds, and editable playlists.

**Live app:** https://rajeshwar01-01.github.io/gana-music-app/

## Music library

- Paste a YouTube video link or public playlist link to add it to your library.
- Playback runs in YouTube's official embedded player. Videos that block embedding, are private, or are unavailable in your region may not play here. Open those on YouTube instead.
- Add local audio files you own or have permission to use. Audio stays in this browser on this device.
- Search and filter the library, like tracks, and use the player controls to play, pause, skip, seek, and adjust volume.
- The included Accra After Hours demo is generated in the browser with Web Audio; it is not a commercial recording.

AfroVibe does not download YouTube audio or provide a commercial streaming catalog. YouTube playback is provided by the embedded player and follows YouTube's own availability and playback rules.

## Playlists

Create, rename, and delete playlists. Use the **+** button next to a library track to add it to the selected playlist. Export a playlist as JSON and share that file; another person can import it in AfroVibe.

Shared playlist files contain YouTube video or playlist links, not audio. Local audio and the original demo are not transferred. Playlists and saved YouTube links are kept in browser storage on the current device; there is no account, server, or automatic cross-device sync.

## Run or publish

Open `index.html` in a modern browser. To publish with GitHub Pages, choose **Settings → Pages → Deploy from a branch → main → /(root)**. The site is static HTML and needs no build step.
