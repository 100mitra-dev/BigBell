/* BigBell Creator Search — vanilla JS front-end (no framework). */
const $ = (id) => document.getElementById(id);
const state = {
  q: "", niche: "", language: "", region: "", tier: "",
  platform: "", status: "", sort_by: "followers",
  min_followers: 0, min_engagement: 0, verified_only: false,
  source: "all", page: 1, page_size: 24,
};

const fmt = (n) => n >= 1e6 ? (n / 1e6).toFixed(1) + "M"
  : n >= 1e3 ? (n / 1e3).toFixed(1).replace(/\.0$/, "") + "K" : String(n);

async function api(path, opts) {
  const res = await fetch(path, opts);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

function initials(name) {
  return name.split(/\s+/).slice(0, 2).map((w) => w[0] || "").join("").toUpperCase();
}

function collectParams() {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(state)) {
    if (v === "" || v === false || v === null) continue;
    p.set(k, v);
  }
  return p.toString();
}

async function loadFacets() {
  const f = await api("/api/v1/creators/facets");
  fillSelect($("fNiche"), f.niches);
  fillSelect($("fLang"), f.languages);
  fillSelect($("fRegion"), f.regions);
  fillSelect($("fPlatform"), f.platforms);
}

function fillSelect(sel, obj) {
  const cur = sel.value;
  const first = sel.options[0].textContent;
  sel.innerHTML = "";
  sel.appendChild(new Option(first, ""));
  for (const k of Object.keys(obj || {})) sel.appendChild(new Option(`${k} (${obj[k]})`, k));
  sel.value = cur;
}

async function loadStatus() {
  try {
    const s = await api("/api/v1/discovery/status");
    const pill = $("statusPill");
    const n = s.cached_creators ?? "?";
    const meta = s.meta?.configured ? "Meta ✓" : "Meta mock";
    const mod = s.sources?.modash?.configured ? "Modash ✓" : "Modash mock";
    pill.textContent = `● DB ${n} · ${meta} · ${mod}`;
    pill.classList.add("live");
  } catch { /* pill keeps connecting state */ }
}

function cardHTML(c) {
  const plats = Object.entries(c.followers_by_platform || {})
    .map(([p, n]) => `<div class="stat"><b>${fmt(n)}</b><i>${p}</i></div>`).join("");
  const handles = Object.entries(c.handles || {})
    .map(([p, h]) => `<div><b style="text-transform:capitalize">${p}</b> · <code>${h}</code></div>`).join("");
  return `
    <article class="card" data-id="${c.id}">
      <div class="card-top">
        <div class="avatar">${initials(c.name)}</div>
        <div>
          <h3>${c.name}</h3>
          <div class="sub">${c.display_region || "—"} · ${(c.languages || []).join(" · ")}</div>
          <div class="badges">
            <span class="badge tier-${c.tier}">${c.tier}</span>
            <span class="badge src-${c.source || "local"}">${c.source || "local"}</span>
            ${c.verified || c.verified_count ? `<span class="badge src-modash">verified</span>` : ""}
          </div>
        </div>
      </div>
      <div class="niches">${(c.niches || []).map((n) => `<span>${n}</span>`).join("")}</div>
      <div class="handles">${handles}</div>
      <div class="stats">
        <div class="stat"><b>${fmt(c.total_followers || 0)}</b><i>followers</i></div>
        <div class="stat"><b>${(c.engagement_rate ?? 0).toFixed(1)}%</b><i>engagement</i></div>
        <div class="stat"><b>${(c.content_quality_score ?? 0).toFixed(1)}</b><i>quality</i></div>
      </div>
      ${plats ? `<div class="stats">${plats}</div>` : ""}
      <div class="bar"><span style="width:${Math.min(100, (c.engagement_rate || 0) * 12)}%"></span></div>
    </article>`;
}

let lastItems = [];
async function search() {
  const grid = $("grid");
  grid.classList.toggle("list", $("listView").classList.contains("on"));
  try {
    const r = await api("/api/v1/creators/search?" + collectParams());
    lastItems = r.items;
    $("error").hidden = true;
    $("empty").hidden = r.items.length > 0;
    grid.innerHTML = r.items.map(cardHTML).join("");
    $("resultMeta").textContent =
      `${r.total} creator${r.total === 1 ? "" : "s"} · page ${r.page}/${r.total_pages} · source: ${r.source}`;
    $("pageInfo").textContent = `Page ${r.page} of ${r.total_pages}`;
    $("prevBtn").disabled = r.page <= 1;
    $("nextBtn").disabled = r.page >= r.total_pages;
    renderChips();
  } catch (e) {
    $("error").hidden = false;
  }
}

function renderChips() {
  const chips = [];
  const labels = { q: "Search", niche: "Niche", language: "Language", region: "Region", tier: "Tier", platform: "Platform", status: "Status" };
  for (const [k, label] of Object.entries(labels)) {
    if (state[k]) chips.push(`<button data-clear="${k}">${label}: ${state[k]} ✕</button>`);
  }
  if (state.min_followers) chips.push(`<button data-clear="min_followers">≥ ${fmt(state.min_followers)} followers ✕</button>`);
  if (state.min_engagement) chips.push(`<button data-clear="min_engagement">≥ ${state.min_engagement}% eng. ✕</button>`);
  if (state.verified_only) chips.push(`<button data-clear="verified_only">Verified ✕</button>`);
  $("activeChips").innerHTML = chips.join("");
}

function bind() {
  let t;
  $("q").addEventListener("input", (e) => {
    clearTimeout(t);
    t = setTimeout(() => { state.q = e.target.value.trim(); state.page = 1; search(); }, 250);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== $("q")) { e.preventDefault(); $("q").focus(); }
  });
  const map = [["fNiche", "niche"], ["fLang", "language"], ["fRegion", "region"], ["fTier", "tier"], ["fPlatform", "platform"], ["fStatus", "status"], ["fSort", "sort_by"]];
  for (const [id, key] of map) {
    $(id).addEventListener("change", (e) => { state[key] = e.target.value; state.page = 1; search(); });
  }
  $("fMinF").addEventListener("input", (e) => {
    state.min_followers = +e.target.value; $("oFollowers").textContent = fmt(state.min_followers);
    state.page = 1; search();
  });
  $("fMinE").addEventListener("input", (e) => {
    state.min_engagement = +e.target.value; $("oEng").textContent = state.min_engagement + "%";
    state.page = 1; search();
  });
  $("fVerified").addEventListener("change", (e) => { state.verified_only = e.target.checked; state.page = 1; search(); });
  document.querySelectorAll(".seg button").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll(".seg button").forEach((x) => x.classList.remove("on"));
    b.classList.add("on");
    state.source = b.dataset.source; state.page = 1; search();
  }));
  $("clearBtn").addEventListener("click", () => {
    Object.assign(state, { q: "", niche: "", language: "", region: "", tier: "", platform: "", status: "", sort_by: "followers", min_followers: 0, min_engagement: 0, verified_only: false, page: 1 });
    $("q").value = ""; $("fNiche").value = ""; $("fLang").value = ""; $("fRegion").value = "";
    $("fTier").value = ""; $("fPlatform").value = ""; $("fStatus").value = ""; $("fSort").value = "followers";
    $("fMinF").value = 0; $("oFollowers").textContent = "0";
    $("fMinE").value = 0; $("oEng").textContent = "0%"; $("fVerified").checked = false;
    search();
  });
  $("activeChips").addEventListener("click", (e) => {
    const k = e.target.dataset?.clear;
    if (k) { $("clearBtn").click(); }
  });
  $("gridView").addEventListener("click", () => {
    $("grid").classList.remove("list");
    document.querySelectorAll(".viewbtn").forEach(b => b.classList.toggle("on", b.id === "gridView"));
  });
  $("listView").addEventListener("click", () => {
    $("grid").classList.add("list");
    document.querySelectorAll(".viewbtn").forEach(b => b.classList.toggle("on", b.id === "listView"));
  });
  $("prevBtn").addEventListener("click", () => { if (state.page > 1) { state.page--; search(); } });
  $("nextBtn").addEventListener("click", () => { state.page++; search(); });
  $("retryBtn").addEventListener("click", search);
  $("grid").addEventListener("click", (e) => {
    const card = e.target.closest(".card");
    if (card) openDetail(card.dataset.id);
  });
  function download(filename, text, type) {
    const blob = new Blob([text], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  }
  $("csvBtn").addEventListener("click", () => {
    const rows = [["id", "name", "niche", "language", "region", "followers", "engagement", "tier", "source"]];
    for (const c of lastItems) rows.push([c.id, c.name, (c.niches || []).join(" | "), (c.languages || []).join(" | "), c.display_region || "", c.total_followers || 0, c.engagement_rate || 0, c.tier || "", c.source || "local"]);
    download("bigbell-creators.csv", rows.map(r => r.map(v => `"${String(v).replace(/"/g, '""')}"`).join(",")).join("\n"), "text/csv;charset=utf-8");
  });
  $("jsonBtn").addEventListener("click", () => download("bigbell-creators.json", JSON.stringify(lastItems, null, 2), "application/json"));
  $("syncBtn").addEventListener("click", async () => {
    $("syncBtn").disabled = true; $("syncBtn").textContent = "Syncing…";
    try { await api("/api/v1/discovery/sync", { method: "POST" }); await loadStatus(); await search(); }
    finally { $("syncBtn").disabled = false; $("syncBtn").textContent = "Sync DB"; }
  });
  $("keysBtn").addEventListener("click", () => $("keysModal").showModal());
  $("kSave").addEventListener("click", async (e) => {
    e.preventDefault();
    const body = {
      meta_marketplace_key: $("kMeta").value || undefined,
      modash_key: $("kModash").value || undefined,
      meta_api_base_url: $("kBase").value || undefined,
    };
    try {
      const r = await api("/api/v1/discovery/config", {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
      });
      $("kMsg").textContent = "Saved: " + (r.applied.join(", ") || "nothing changed");
      await loadStatus();
    } catch { $("kMsg").textContent = "Save failed — is the API running?"; }
  });
}

function openDetail(id) {
  const c = lastItems.find((x) => x.id === id);
  if (!c) return;
  const dlg = $("detail");
  dlg.innerHTML = `
    <div class="d-head">
      <div class="avatar">${initials(c.name)}</div>
      <div><h3 style="margin:0">${c.name}</h3>
      <div class="sub">${c.display_region || "—"} · ${(c.languages || []).join(" · ")}</div></div>
      <button class="btn ghost d-close" onclick="this.closest('dialog').close()">Close</button>
    </div>
    <div class="d-body">
      ${c.bio ? `<p class="meta">${c.bio}</p>` : ""}
      <h4>Niches · Languages · Regions</h4>
      <div class="niches">${[...(c.niches || []), ...(c.languages || []), c.display_region].filter(Boolean).map((n) => `<span>${n}</span>`).join("")}</div>
      <h4>Handles &amp; audience</h4>
      <div class="handles">${Object.entries(c.handles || {}).map(([p, h]) => `<div><b style="text-transform:capitalize">${p}</b> · <code>${h}</code> · ${fmt((c.followers_by_platform || {})[p] || 0)}</div>`).join("")}</div>
      <h4>Performance</h4>
      <div class="d-grid">
        <div class="d-cell"><b>${fmt(c.total_followers || 0)}</b><i>total followers / subs</i></div>
        <div class="d-cell"><b>${(c.engagement_rate ?? 0).toFixed(1)}%</b><i>engagement rate</i></div>
        <div class="d-cell"><b>${(c.content_quality_score ?? 0).toFixed(1)} / 10</b><i>content quality</i></div>
        <div class="d-cell"><b>${c.total_campaigns_completed ?? 0}</b><i>campaigns · ₹${fmt(c.total_earnings || 0)}</i></div>
      </div>
      <h4>Status</h4>
      <p class="meta">${c.status} · tier ${c.tier} · source ${c.source || "local"} · ${(c.suggested_tags || []).join(", ")}</p>
    </div>`;
  dlg.showModal();
  dlg.addEventListener("click", (e) => { if (e.target === dlg) dlg.close(); }, { once: true });
}

/* ---- view tabs ---- */
document.querySelectorAll(".viewtabs button").forEach((b) => b.addEventListener("click", () => {
  document.querySelectorAll(".viewtabs button").forEach((x) => x.classList.toggle("on", x === b));
  const v = b.dataset.view;
  document.querySelector("main.layout").hidden = v !== "search";
  $("campaignsView").hidden = v !== "campaigns";
  $("messagesView").hidden = v !== "messages";
  if (v === "campaigns") loadCampaigns();
}));

/* ---- campaigns ---- */
async function loadCampaigns() {
  const list = $("campaignList");
  try {
    const camps = await api("/api/v1/campaigns/");
    list.innerHTML = camps.map((c) => `
      <article class="camp" data-id="${c.id}">
        <div class="brand">${c.brand} · ${c.status}</div>
        <h3>${c.title}</h3>
        <p>${(c.description || "").slice(0, 140)}</p>
        <div class="meta">₹${fmt(c.budget || 0)} · ${(c.target_niches || []).join(", ")} · due ${c.deadline || "—"}</div>
      </article>`).join("") || `<div class="empty"><h3>No campaigns yet</h3></div>`;
  } catch { list.innerHTML = `<div class="empty"><h3>Couldn’t load campaigns</h3></div>`; }
}
$("campaignList").addEventListener("click", async (e) => {
  const el = e.target.closest(".camp");
  if (!el) return;
  const det = $("campaignDetail");
  try {
    const r = await api(`/api/v1/campaigns/${el.dataset.id}/matches?limit=8`);
    det.hidden = false;
    det.innerHTML = `<h3 style="font-family:var(--font-d)">Top matches — ${r.campaign.title}</h3>` +
      r.items.map((c) => `<div class="matchrow" data-id="${c.id}"><b>${c.match_score}</b><span>${c.name}</span><span class="muted">${(c.niches || []).slice(0, 2).join(", ")} · ${fmt(c.total_followers || 0)}</span></div>`).join("");
    det.querySelectorAll(".matchrow").forEach((row) => row.addEventListener("click", () => {
      lastItems = r.items;
      openDetail(row.dataset.id);
    }));
    det.scrollIntoView({ behavior: "smooth", block: "nearest" });
  } catch { det.hidden = false; det.innerHTML = `<div class="empty"><h3>Couldn’t load matches</h3></div>`; }
});

/* ---- messages (FAQ helpdesk) ---- */
$("chatForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = $("chatInput");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  const log = $("chatLog");
  log.insertAdjacentHTML("beforeend", `<div class="msg me">${text}</div>`);
  log.scrollTop = log.scrollHeight;
  try {
    const r = await api("/api/v1/faq/ask?question=" + encodeURIComponent(text));
    const src = (r.sources || []).slice(0, 2).map((s) => s.question || s.id || "").filter(Boolean).join(" · ");
    log.insertAdjacentHTML("beforeend", `<div class="msg bot">${r.answer}${src ? `<span class="src">Sources: ${src} · confidence ${r.confidence || "—"}</span>` : ""}</div>`);
  } catch { log.insertAdjacentHTML("beforeend", `<div class="msg bot">The helpdesk is unreachable — is the API running?</div>`); }
  log.scrollTop = log.scrollHeight;
});

(async function init() {
  bind();
  try { await loadFacets(); } catch { /* search shows error state */ }
  await loadStatus();
  await search();
})();
