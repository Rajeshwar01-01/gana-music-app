(() => {
  "use strict";

  const form = document.getElementById("spotifyForm");
  const input = document.getElementById("spotifyUrl");
  const entriesNode = document.getElementById("spotifyEntries");
  const status = document.getElementById("spotifyStatus");
  const featuredNode = document.getElementById("spotifyFeatured");
  if (!form || !input || !entriesNode || !status || !featuredNode) return;

  const storageKey = "afrovibe-spotify-links";
  const supportedTypes = new Set(["track", "album", "playlist"]);
  const spotifyId = /^[A-Za-z0-9]{22}$/;
  const featuredLinks = [
    { title: "Ghana Highlife Party", creator: "Spotify", url: "https://open.spotify.com/playlist/37i9dQZF1DXc5TIUNEibWO?utm_source=openai&utm_medium=chatgpt&go=1&nap_web=1&request_id=a50e9505-b4aa-4bb1-b4e6-6b6e3b141064" },
    { title: "Ghana Party", creator: "Spotify", url: "https://open.spotify.com/playlist/37i9dQZF1DX7t977T5F4kQ?utm_source=openai&utm_medium=chatgpt&go=1&nap_web=1&request_id=a50e9505-b4aa-4bb1-b4e6-6b6e3b141064" },
    { title: 'Raanjhan (From "Do Patti")', sourceLabel: 'From your Spotify playlist "5" · Sachet-Parampara, Parampara Tandon, Kausar Munir', url: "https://open.spotify.com/track/4vHRQnzGcKEtqsLH70tAms?utm_source=openai&utm_medium=chatgpt&go=1&nap_web=1&request_id=82a93682-9b54-4cc5-bb19-c181e597201b" },
    { title: "Roz Mala Visrun Me", sourceLabel: 'From your Spotify playlist "5" · Bela Shende, Harshavardhan Wavare', url: "https://open.spotify.com/track/0d30F80EiIm4W55EzIIDYa?utm_source=openai&utm_medium=chatgpt&go=1&nap_web=1&request_id=82a93682-9b54-4cc5-bb19-c181e597201b" },
    { title: "I Guess", sourceLabel: 'From your Spotify playlist "My playlist #1" · KR$NA, Kabu Beats', url: "https://open.spotify.com/track/0OxG3hlJNNzXcSrNVXEu8f?utm_source=openai&utm_medium=chatgpt&go=1&nap_web=1&request_id=3b866b84-67ba-4a28-b784-5a0d6cfb3151" },
    { title: "Victory Anthem", sourceLabel: 'From your Spotify playlist "My playlist #1" · Khushi TDT, Lash curry, Audiocrackerr · Explicit', url: "https://open.spotify.com/track/1UEbsf5kGEIcSMiWexOkrZ?utm_source=openai&utm_medium=chatgpt&go=1&nap_web=1&request_id=3b866b84-67ba-4a28-b784-5a0d6cfb3151" }
  ];

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

  function addToAfroVibe(url, title) {
    window.dispatchEvent(new CustomEvent("afrovibe:spotify-link-added", { detail: { url, title } }));
  }

  function renderFeatured() {
    featuredNode.replaceChildren();
    featuredLinks.forEach(item => {
      const entry = parseSpotifyLink(item.url);
      if (!entry) return;
      const card = document.createElement("article");
      card.className = "spotify-entry";
      card.dataset.spotifyUrl = entry.url;
      const title = document.createElement("h5");
      title.className = "spotify-entry-title";
      title.textContent = item.title;
      const source = document.createElement("span");
      source.className = "spotify-entry-source";
      source.textContent = item.sourceLabel || ("Curated by " + item.creator);
      const frame = document.createElement("iframe");
      frame.src = "https://open.spotify.com/embed/" + entry.type + "/" + entry.id + "?utm_source=generator";
      frame.title = "Spotify " + entry.type + ": " + item.title;
      frame.height = entry.type === "track" ? "152" : "352";
      frame.loading = "lazy";
      frame.setAttribute("allow", "autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture");
      frame.setAttribute("allowfullscreen", "");
      frame.setAttribute("frameborder", "0");
      const link = document.createElement("a");
      link.className = "spotify-open";
      link.href = item.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "Open on Spotify";
      const add = document.createElement("button");
      add.type = "button";
      add.className = "btn small";
      add.textContent = "＋ Add to playlist";
      add.addEventListener("click", () => addToAfroVibe(item.url, item.title));
      const actions = document.createElement("div");
      actions.className = "spotify-entry-actions";
      actions.append(add);
      card.append(title, source, frame, link, actions);
      featuredNode.append(card);
    });
  }

  function renderEntries() {
    entriesNode.replaceChildren();
    entries.forEach(entry => {
      const card = document.createElement("article");
      card.className = "spotify-entry";
      card.dataset.spotifyUrl = entry.url;

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

      const add = document.createElement("button");
      add.type = "button";
      add.className = "btn small";
      add.textContent = "＋ Add to playlist";
      add.addEventListener("click", () => addToAfroVibe(entry.url, "Spotify " + entry.type));
      actions.append(add, remove);
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

  window.addEventListener("afrovibe:spotify-focus", event => {
    const entry = parseSpotifyLink(event.detail?.url || "");
    if (!entry) return;
    const card = [...document.querySelectorAll("[data-spotify-url]")].find(node => node.dataset.spotifyUrl === entry.url);
    card?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  });

  renderFeatured();
  renderEntries();
})();

