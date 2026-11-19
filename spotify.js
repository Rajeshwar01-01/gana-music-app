(() => {
  "use strict";

  const form = document.getElementById("spotifyForm");
  const input = document.getElementById("spotifyUrl");
  const entriesNode = document.getElementById("spotifyEntries");
  const status = document.getElementById("spotifyStatus");
  if (!form || !input || !entriesNode || !status) return;

  const storageKey = "afrovibe-spotify-links";
  const supportedTypes = new Set(["track", "album", "playlist"]);
  const spotifyId = /^[A-Za-z0-9]{22}$/;

  function parseSpotifyLink(value) {
    try {
      const url = new URL(value.trim());
      if (url.protocol !== "https:" || url.hostname.toLowerCase() !== "open.spotify.com") return null;
      const parts = url.pathname.split("/").filter(Boolean);
      if (parts[0] === "embed") parts.shift();
      const [type, id] = parts;
      if (!supportedTypes.has(type) || !spotifyId.test(id || "")) return null;
      return {
        type,
        id,
        url: "https://open.spotify.com/" + type + "/" + id
      };
    } catch (_) {
      return null;
    }
  }

  function readEntries() {
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || "[]");
      if (!Array.isArray(saved)) return [];
      return saved.map(item => parseSpotifyLink(item?.url || "")).filter(Boolean);
    } catch (_) {
      return [];
    }
  }

  let entries = readEntries();

  function saveEntries() {
    try {
      localStorage.setItem(storageKey, JSON.stringify(entries));
      return true;
    } catch (_) {
      status.textContent = "Browser storage is full. Remove a Spotify link and try again.";
      return false;
    }
  }

  function renderEntries() {
    entriesNode.replaceChildren();
    entries.forEach(entry => {
      const card = document.createElement("article");
      card.className = "spotify-entry";

      const frame = document.createElement("iframe");
      frame.src = "https://open.spotify.com/embed/" + entry.type + "/" + entry.id + "?utm_source=generator";
      frame.title = "Spotify " + entry.type + " player";
      frame.height = entry.type === "track" ? "152" : "352";
      frame.loading = "lazy";
      frame.setAttribute("allow", "autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture");
      frame.setAttribute("allowfullscreen", "");
      frame.setAttribute("frameborder", "0");

      const actions = document.createElement("div");
      actions.className = "spotify-entry-actions";
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "btn small";
      remove.textContent = "Remove";
      remove.setAttribute("aria-label", "Remove Spotify " + entry.type + " link");
      remove.addEventListener("click", () => {
        entries = entries.filter(item => item.url !== entry.url);
        if (saveEntries()) {
          renderEntries();
          status.textContent = "Spotify link removed from this browser.";
        }
      });

      actions.append(remove);
      card.append(frame, actions);
      entriesNode.append(card);
    });
  }

  form.addEventListener("submit", event => {
    event.preventDefault();
    const entry = parseSpotifyLink(input.value);
    if (!entry) {
      status.textContent = "Paste a Spotify track, album, or playlist link from open.spotify.com.";
      return;
    }
    if (entries.some(item => item.url === entry.url)) {
      status.textContent = "That Spotify link is already in this browser.";
      return;
    }
    entries.push(entry);
    if (saveEntries()) {
      input.value = "";
      renderEntries();
      status.textContent = "Added an official Spotify player. Press play in the player to listen.";
    }
  });

  renderEntries();
})();

