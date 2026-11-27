(() => {
  "use strict";

  const REPO_API = "https://api.github.com/repos/nnqrt/news/contents/legacy";
  const CACHE_KEY = "osint_archive_gh_legacy_v1";
  const CACHE_TTL_MS = 3 * 60 * 1000;

  function getBasePrefix() {
    const p = window.location.pathname.replace(/\\/g, "/");
    return /\/legacy(\/|$)/.test(p) ? "../" : "";
  }

  function formatIdToLabel(id) {
    if (!/^\d{12}$/.test(id)) return id;
    return `${id.slice(0, 4)}-${id.slice(4, 6)}-${id.slice(6, 8)} ${id.slice(8, 10)}:${id.slice(10, 12)} KST`;
  }

  function getCurrentFileInfo() {
    const p = window.location.pathname.replace(/\\/g, "/");
    const m = p.match(/index_(\d{12})\.html$/i);
    if (m) return { id: m[1], isLegacy: true, isHub: false };
    if (/\/legacy(\/|\/index\.html)?$/i.test(p)) return { id: null, isLegacy: true, isHub: true };
    return { id: null, isLegacy: false, isHub: false, isRootIndex: true };
  }

  async function fetchManifest(base) {
    try {
      const res = await fetch(`${base}legacy/editions.json?v=${Date.now()}`, { cache: "no-cache" });
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data.editions) ? data.editions : [];
    } catch {
      return [];
    }
  }

  async function fetchGitHubLegacyAdditions() {
    try {
      const raw = sessionStorage.getItem(CACHE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Date.now() - parsed.ts < CACHE_TTL_MS && Array.isArray(parsed.items)) {
          return parsed.items;
        }
      }
    } catch {
      // Ignore storage errors
    }

    try {
      const res = await fetch(REPO_API, {
        headers: { Accept: "application/vnd.github+json" },
        cache: "no-cache",
      });
      if (!res.ok) return [];
      const files = await res.json();
      if (!Array.isArray(files)) return [];
      const items = files
        .filter((f) => typeof f.name === "string" && /^index_\d{12}\.html$/i.test(f.name))
        .map((f) => {
          const id = f.name.match(/\d{12}/)[0];
          return {
            id,
            label: formatIdToLabel(id),
            path: `legacy/${f.name}`,
            title: `한반도 OSINT — ${formatIdToLabel(id)}`,
            headline: "",
            format: "auto",
          };
        });
      try {
        sessionStorage.setItem(CACHE_KEY, JSON.stringify({ ts: Date.now(), items }));
      } catch {
        // Ignore storage errors
      }
      return items;
    } catch {
      return [];
    }
  }

  function mergeEditions(manifestList, ghList) {
    const byId = new Map();
    for (const item of manifestList) {
      if (!item || !item.path) continue;
      const key = item.id || item.path;
      const existing = byId.get(key);
      if (!existing || item.path === "index.html") {
        byId.set(key, item);
      }
    }
    for (const item of ghList) {
      if (!item || !item.path) continue;
      const key = item.id || item.path;
      if (!byId.has(key)) {
        byId.set(key, item);
      }
    }
    const list = Array.from(byId.values());
    list.sort((a, b) => {
      if (a.id !== b.id) return b.id.localeCompare(a.id);
      return a.path === "index.html" ? -1 : 1;
    });
    return list;
  }

  async function loadEditions() {
    const base = getBasePrefix();
    const [manifestList, ghList] = await Promise.all([
      fetchManifest(base),
      fetchGitHubLegacyAdditions(),
    ]);
    return mergeEditions(manifestList, ghList);
  }

  function resolveHref(base, itemPath) {
    return `${base}${itemPath}`;
  }

  function buildSelectElement(editions, base, currentInfo, extraClass) {
    const select = document.createElement("select");
    select.id = "editionArchiveSelect";
    select.className = extraClass;
    select.setAttribute("aria-label", "과거 시점 기사 판본 선택");

    const currentPath = currentInfo.isRootIndex
      ? "index.html"
      : currentInfo.id
        ? `legacy/index_${currentInfo.id}.html`
        : "";

    for (const ed of editions) {
      const opt = document.createElement("option");
      opt.value = resolveHref(base, ed.path);
      const tag = ed.isCurrent ? " [현재 메인]" : "";
      opt.textContent = `📅 ${ed.label}${tag}`;
      if (ed.path === currentPath || (currentInfo.id && ed.id === currentInfo.id)) {
        opt.selected = true;
      }
      select.appendChild(opt);
    }

    select.addEventListener("change", (e) => {
      const target = e.target.value;
      if (target) window.location.href = target;
    });
    return select;
  }

  function injectBarStyles() {
    if (document.getElementById("osint-archive-bar-style")) return;
    const style = document.createElement("style");
    style.id = "osint-archive-bar-style";
    style.textContent = `
      .osint-archive-link {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-family: var(--font-ui, 'Noto Sans KR', sans-serif);
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border: 1px solid var(--hair, #CBD5E1);
        border-radius: 4px;
        background: var(--surface, #F8FAFC);
        color: var(--ink, #111827);
        text-decoration: none;
        white-space: nowrap;
        transition: opacity 0.15s ease;
      }
      .osint-archive-link:hover { opacity: 0.8; }
      .osint-v1-bar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 10px;
        padding: 10px 14px;
        margin: -36px 0 28px;
        border: 1px solid #CBD5E1;
        border-left: 4px solid #1E3A8A;
        background: #F8FAFC;
        font-family: 'IBM Plex Sans', 'Noto Sans KR', sans-serif;
        font-size: 13px;
        color: #0F172A;
      }
      .osint-v1-bar-left {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 700;
      }
      .osint-v1-bar-right {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px;
      }
      .osint-v1-select {
        font-family: inherit;
        font-size: 12.5px;
        font-weight: 600;
        padding: 4px 8px;
        border: 1px solid #CBD5E1;
        background: #FFFFFF;
        color: #0F172A;
      }
      @media (max-width: 680px) {
        .osint-v1-bar { margin-top: -24px; }
      }
    `;
    document.head.appendChild(style);
  }

  async function mountArchiveNavigation() {
    const info = getCurrentFileInfo();
    if (info.isHub) return;

    const base = getBasePrefix();
    const editions = await loadEditions();
    if (!editions.length) return;

    injectBarStyles();

    const datelineActions = document.querySelector(".dateline-actions");
    if (datelineActions) {
      if (document.getElementById("editionArchiveSelect")) return;

      const select = buildSelectElement(editions, base, info, "bgm-select");
      datelineActions.appendChild(select);

      if (info.isLegacy) {
        const homeLink = document.createElement("a");
        homeLink.className = "osint-archive-link";
        homeLink.href = `${base}index.html`;
        homeLink.textContent = "← 최신판";
        datelineActions.appendChild(homeLink);
      }

      const hubLink = document.createElement("a");
      hubLink.className = "osint-archive-link";
      hubLink.href = `${base}legacy/index.html`;
      hubLink.textContent = "아카이브";
      datelineActions.appendChild(hubLink);
      return;
    }

    // Fallback for v1 briefings without .dateline-actions
    if (document.getElementById("osintV1ArchiveBar")) return;
    const bar = document.createElement("nav");
    bar.id = "osintV1ArchiveBar";
    bar.className = "osint-v1-bar";
    bar.setAttribute("aria-label", "과거 시점 기사 탐색");

    const left = document.createElement("div");
    left.className = "osint-v1-bar-left";
    left.textContent = "한반도 OSINT 아카이브 · 시점 선택";

    const right = document.createElement("div");
    right.className = "osint-v1-bar-right";

    const select = buildSelectElement(editions, base, info, "osint-v1-select");
    const homeLink = document.createElement("a");
    homeLink.className = "osint-archive-link";
    homeLink.href = `${base}index.html`;
    homeLink.textContent = "← 최신판";

    const hubLink = document.createElement("a");
    hubLink.className = "osint-archive-link";
    hubLink.href = `${base}legacy/index.html`;
    hubLink.textContent = "전체 목록";

    right.appendChild(select);
    right.appendChild(homeLink);
    right.appendChild(hubLink);

    bar.appendChild(left);
    bar.appendChild(right);
    document.body.insertBefore(bar, document.body.firstChild);
  }

  window.OSINTArchive = {
    loadEditions,
    getBasePrefix,
    formatIdToLabel,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mountArchiveNavigation);
  } else {
    mountArchiveNavigation();
  }
})();
