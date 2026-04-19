// Micks Musikkiste V2 — Frontend-Logik
// Keine V1-Preset-Logik, kein Mode-Switch-Hack.
// Genre ist ein Formularfeld, nicht Navigationspunkt.

"use strict";

// ---------------------------------------------------------------------------
// Konstanten
// ---------------------------------------------------------------------------
const API_BASE = window.location.origin;
const POLL_INTERVAL_MS = 3000;

// ---------------------------------------------------------------------------
// Zustand
// ---------------------------------------------------------------------------
const state = {
    genres: [],           // [{id, name, substyles:[], bpm_default, bpm_range}]
    profiles: [],         // [{id, name, ...}]
    activeEngine: null,   // string
    activeProfile: null,  // string
    activeJob: null,      // job-Objekt nach Generierung
    lastRequest: null,    // Beat- oder Track-Request zum Neuerstellen
    lastType: null,       // "beat" | "track"
    pollTimer: null,
    allProjects: [],
    filteredProjects: [],
    dialogResolve: null,
};

// ---------------------------------------------------------------------------
// Hilfsfunktionen
// ---------------------------------------------------------------------------
const byId = (id) => document.getElementById(id);

function esc(text) {
    return String(text ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function fmtDuration(seconds) {
    if (!Number.isFinite(Number(seconds))) return "–";
    const s = Number(seconds);
    const m = Math.floor(s / 60);
    const r = s % 60;
    return m > 0 ? `${m}:${String(r).padStart(2, "0")} min` : `${r} Sek.`;
}

function fmtDate(value) {
    if (!value) return "–";
    const d = new Date(value);
    return `${d.toLocaleDateString("de-DE")} ${d.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })}`;
}

function showToast(msg, isError = false) {
    const t = document.createElement("div");
    t.className = `toast ${isError ? "toast-error" : "toast-success"}`;
    t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), isError ? 5000 : 3000);
}

// ---------------------------------------------------------------------------
// API-Modul
// ---------------------------------------------------------------------------
const api = {
    async _req(path, opts = {}) {
        const resp = await fetch(`${API_BASE}${path}`, {
            headers: { "Content-Type": "application/json", ...opts.headers },
            ...opts,
        });
        const isJson = resp.headers.get("content-type")?.includes("application/json");
        const data = isJson ? await resp.json() : null;
        if (!resp.ok) {
            const msg = data?.error?.message || data?.detail || data?.message || `HTTP ${resp.status}`;
            throw new Error(msg);
        }
        return data;
    },

    genres: () => api._req("/api/v2/genres"),
    engineStatus: () => api._req("/api/v2/engine/status"),
    config: () => api._req("/api/v2/config"),
    profiles: () => api._req("/api/v2/profiles"),
    job: (id) => api._req(`/api/v2/jobs/${id}`),
    beat: (body) => api._req("/api/v2/beat/generate", { method: "POST", body: JSON.stringify(body) }),
    track: (body) => api._req("/api/v2/track/generate", { method: "POST", body: JSON.stringify(body) }),
    projects: () => api._req("/api/v2/projects"),
    saveProject: (body) => api._req("/api/v2/projects", { method: "POST", body: JSON.stringify(body) }),
    switchEngine: (engine) => api._req("/api/engine/mode", { method: "POST", body: JSON.stringify({ mode: engine }) }),
    switchProfile: (id) => api._req("/api/engine/profile", { method: "POST", body: JSON.stringify({ profile_id: id }) }),
};

// ---------------------------------------------------------------------------
// Navigation
// ---------------------------------------------------------------------------
function navigateTo(page) {
    document.querySelectorAll(".page").forEach((s) => s.classList.remove("active"));
    const target = byId(`page-${page}`);
    if (target) target.classList.add("active");

    document.querySelectorAll(".nav-btn").forEach((b) => {
        b.classList.toggle("active", b.dataset.page === page);
    });

    window.scrollTo({ top: 0, behavior: "smooth" });
}

function setupNavigation() {
    document.querySelectorAll(".nav-btn[data-page]").forEach((btn) => {
        btn.addEventListener("click", () => navigateTo(btn.dataset.page));
    });

    // Start-Cards auf dem Dashboard
    document.querySelectorAll(".start-card[data-page]").forEach((card) => {
        card.addEventListener("click", () => navigateTo(card.dataset.page));
    });

    // Dashboard-Tiles
    document.querySelectorAll(".dash-tile[data-page]").forEach((tile) => {
        tile.addEventListener("click", () => navigateTo(tile.dataset.page));
    });
}

// ---------------------------------------------------------------------------
// Genres + Substyle
// ---------------------------------------------------------------------------
async function loadGenres() {
    try {
        const resp = await api.genres();
        const genreList = resp?.data ?? resp ?? [];
        state.genres = Array.isArray(genreList) ? genreList : [];
    } catch (e) {
        console.warn("Genre-Load fehlgeschlagen:", e);
        state.genres = [];
    }
    populateGenreDropdowns();
}

function populateGenreDropdowns() {
    ["beatGenre", "trackGenre", "genreFilter"].forEach((id) => {
        const sel = byId(id);
        if (!sel) return;
        const isFilter = id === "genreFilter";
        // Erste Option behalten
        const defaultOption = sel.options[0];
        sel.innerHTML = "";
        sel.appendChild(defaultOption);
        state.genres.forEach((g) => {
            const opt = document.createElement("option");
            opt.value = g.id;
            opt.textContent = g.name;
            sel.appendChild(opt);
        });
    });
}

function populateSubstyleDropdown(genreId, selectId = "trackSubstyle") {
    const sel = byId(selectId);
    if (!sel) return;
    sel.innerHTML = '<option value="">– kein Substil –</option>';
    const genre = state.genres.find((g) => g.id === genreId);
    if (!genre?.substyles?.length) return;
    genre.substyles.forEach((sub) => {
        const opt = document.createElement("option");
        const label = typeof sub === "string" ? sub : (sub.id || sub);
        opt.value = label;
        opt.textContent = label;
        sel.appendChild(opt);
    });
}

// ---------------------------------------------------------------------------
// Engine-Status + Engine-Pill
// ---------------------------------------------------------------------------
async function loadEngineStatus() {
    try {
        const resp = await api.engineStatus();
        const d = resp?.data ?? {};
        state.activeEngine = d.engine || d.active_engine || "–";
        state.activeProfile = d.active_profile || "–";
        renderEnginePill(d);
        renderStatusPage(d);
    } catch (e) {
        byId("enginePill").textContent = "Engine: offline";
        byId("enginePill").className = "engine-pill engine-pill-error";
        console.warn("Engine-Status fehlgeschlagen:", e);
    }
}

function renderEnginePill(d) {
    const pill = byId("enginePill");
    const engine = d.engine || d.active_engine || "–";
    const ready = d.ready === true;
    pill.textContent = `${engine}${ready ? "" : " ⚠"}`;
    pill.className = `engine-pill ${ready ? "engine-pill-ok" : "engine-pill-warn"}`;
    pill.title = ready ? "Engine bereit" : "Engine nicht ready (Mock oder Setup fehlt)";
}

function renderStatusPage(d) {
    const engine = d.engine || d.active_engine || "–";
    const ready = d.ready === true;
    byId("statusActiveEngine").textContent = engine;
    byId("statusReady").textContent = ready ? "✓ bereit" : "⚠ nicht bereit";
    byId("statusReady").className = ready ? "status-ok" : "status-warn";
    byId("statusTransport").textContent = d.transport || d.details?.transport || "–";
    byId("statusWorker").textContent = d.worker_running !== undefined
        ? (d.worker_running ? "läuft" : "gestoppt")
        : "–";

    // Detail-Block
    const det = byId("engineDetails");
    if (d.activation_instructions) {
        det.innerHTML = `<div class="hint-block hint-warn"><strong>Aktivierung nötig:</strong><br>${esc(d.activation_instructions)}</div>`;
    } else {
        det.innerHTML = "";
    }

    // Engine-Buttons highlighten
    document.querySelectorAll(".engine-mode-btn").forEach((b) => b.classList.remove("active"));
    const activeBtn = document.querySelector(`.engine-mode-btn[onclick*="'${engine}'"]`);
    if (activeBtn) activeBtn.classList.add("active");
}

// ---------------------------------------------------------------------------
// Profile
// ---------------------------------------------------------------------------
async function loadProfiles() {
    try {
        const resp = await api.profiles();
        const d = resp?.data ?? {};
        state.profiles = d.profiles ?? [];
        state.activeProfile = d.active_profile || state.activeProfile;
        populateProfileDropdowns();
        renderProfileList();
    } catch (e) {
        console.warn("Profiles-Load fehlgeschlagen:", e);
    }
}

function populateProfileDropdowns() {
    ["beatProfile", "trackProfile"].forEach((id) => {
        const sel = byId(id);
        if (!sel) return;
        const defaultOpt = sel.options[0];
        sel.innerHTML = "";
        sel.appendChild(defaultOpt);
        state.profiles.forEach((p) => {
            const opt = document.createElement("option");
            opt.value = p.id;
            opt.textContent = p.name || p.id;
            if (p.id === state.activeProfile) opt.selected = true;
            sel.appendChild(opt);
        });
    });
}

function renderProfileList() {
    const list = byId("profileList");
    if (!list) return;
    if (!state.profiles.length) {
        list.innerHTML = '<p class="placeholder">Keine Profile in data/profiles/ gefunden.</p>';
        return;
    }
    list.innerHTML = state.profiles.map((p) => `
        <div class="profile-item ${p.id === state.activeProfile ? "profile-item-active" : ""}"
             data-profile-id="${esc(p.id)}">
            <strong>${esc(p.name || p.id)}</strong>
            ${p.description ? `<small>${esc(p.description)}</small>` : ""}
            <button class="btn btn-sm btn-secondary" onclick="switchProfile('${esc(p.id)}')">
                ${p.id === state.activeProfile ? "Aktiv" : "Aktivieren"}
            </button>
        </div>
    `).join("");
}

// ---------------------------------------------------------------------------
// Engine-Formular-Dropdowns befüllen
// ---------------------------------------------------------------------------
function populateEngineDropdowns() {
    const engines = [
        { value: "ace", label: "ACE (ComfyUI)" },
        { value: "musicgen", label: "MusicGen (nicht ready)" },
        { value: "mock", label: "Mock (Test)" },
    ];
    ["beatEngine", "trackEngine"].forEach((id) => {
        const sel = byId(id);
        if (!sel) return;
        const defaultOpt = sel.options[0];
        sel.innerHTML = "";
        sel.appendChild(defaultOpt);
        engines.forEach((e) => {
            const opt = document.createElement("option");
            opt.value = e.value;
            opt.textContent = e.label;
            if (e.value === state.activeEngine) opt.selected = true;
            sel.appendChild(opt);
        });
    });
}

// ---------------------------------------------------------------------------
// Slider-Labels
// ---------------------------------------------------------------------------
function setupSliders() {
    const pairs = [
        ["beatEnergy", "beatEnergyVal"],
        ["beatDarkness", "beatDarknessVal"],
        ["beatMelody", "beatMelodyVal"],
        ["trackEnergy", "trackEnergyVal"],
        ["trackCreativity", "trackCreativityVal"],
        ["trackMelody", "trackMelodyVal"],
        ["trackVocal", "trackVocalVal"],
    ];
    pairs.forEach(([rangeId, labelId]) => {
        const range = byId(rangeId);
        const label = byId(labelId);
        if (!range || !label) return;
        range.addEventListener("input", () => {
            label.textContent = range.value;
        });
    });
}

// ---------------------------------------------------------------------------
// Beat-Generierung
// ---------------------------------------------------------------------------
function setupBeatForm() {
    const form = byId("beatForm");
    if (!form) return;

    byId("beatGenre")?.addEventListener("change", () => {
        // Beat hat keinen Substyle
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const genre = byId("beatGenre").value;
        const prompt = byId("beatPrompt").value.trim();
        if (!genre || !prompt) {
            showToast("Bitte Genre und Prompt ausfüllen.", true);
            return;
        }

        const genreObj = state.genres.find((g) => g.id === genre);
        const defaultBpm = genreObj?.bpm_default ?? 125;

        const bpmRaw = byId("beatBpm").value;
        const seedRaw = byId("beatSeed").value;

        const body = {
            title: byId("beatTitle").value.trim() || `Beat – ${genre}`,
            genre,
            prompt,
            negative_prompt: byId("beatNegative").value.trim() || undefined,
            bpm: bpmRaw ? Number(bpmRaw) : defaultBpm,
            duration: Number(byId("beatDuration").value),
            energy: Number(byId("beatEnergy").value),
            darkness: Number(byId("beatDarkness").value),
            melody: Number(byId("beatMelody").value),
        };

        const engineVal = byId("beatEngine")?.value;
        if (engineVal) body.engine = engineVal;
        const profileVal = byId("beatProfile")?.value;
        if (profileVal) body.profile = profileVal;
        if (seedRaw !== "") body.seed = Number(seedRaw);

        // Leere optionale Felder entfernen
        Object.keys(body).forEach((k) => body[k] === undefined && delete body[k]);

        state.lastRequest = body;
        state.lastType = "beat";

        await startGeneration("beat", body);
    });
}

// ---------------------------------------------------------------------------
// Track-Generierung
// ---------------------------------------------------------------------------
function setupTrackForm() {
    const form = byId("trackForm");
    if (!form) return;

    byId("trackGenre")?.addEventListener("change", () => {
        populateSubstyleDropdown(byId("trackGenre").value);
        // BPM-Default setzen
        const genre = state.genres.find((g) => g.id === byId("trackGenre").value);
        if (genre?.bpm_default && !byId("trackBpm").value) {
            byId("trackBpm").placeholder = `z. B. ${genre.bpm_default}`;
        }
    });

    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const genre = byId("trackGenre").value;
        const prompt = byId("trackPrompt").value.trim();
        if (!genre || !prompt) {
            showToast("Bitte Genre und Prompt ausfüllen.", true);
            return;
        }

        const genreObj = state.genres.find((g) => g.id === genre);
        const defaultBpm = genreObj?.bpm_default ?? 125;
        const bpmRaw = byId("trackBpm").value;
        const seedRaw = byId("trackSeed").value;

        const body = {
            title: byId("trackTitle").value.trim() || `Track – ${genre}`,
            genre,
            prompt,
            negative_prompt: byId("trackNegative").value.trim() || undefined,
            substyle: byId("trackSubstyle").value || undefined,
            text_idea: byId("trackTextIdea").value.trim() || undefined,
            bpm: bpmRaw ? Number(bpmRaw) : defaultBpm,
            duration: Number(byId("trackDuration").value),
            energy: Number(byId("trackEnergy").value),
            creativity: Number(byId("trackCreativity").value),
            melody: Number(byId("trackMelody").value),
            vocal_strength: Number(byId("trackVocal").value),
        };

        const engineVal = byId("trackEngine")?.value;
        if (engineVal) body.engine = engineVal;
        const profileVal = byId("trackProfile")?.value;
        if (profileVal) body.profile = profileVal;
        if (seedRaw !== "") body.seed = Number(seedRaw);

        Object.keys(body).forEach((k) => body[k] === undefined && delete body[k]);

        state.lastRequest = body;
        state.lastType = "track";

        await startGeneration("track", body);
    });
}

// ---------------------------------------------------------------------------
// Generierung starten + Job-Polling
// ---------------------------------------------------------------------------
async function startGeneration(type, body) {
    navigateTo("result");
    showResultRunning("Generierung gestartet…");

    try {
        const resp = type === "beat"
            ? await api.beat(body)
            : await api.track(body);

        const jobId = resp?.data?.job_id ?? resp?.job_id;
        if (!jobId) throw new Error("Keine job_id in der Antwort");

        startPolling(jobId, body);
    } catch (err) {
        showResultError(err.message);
    }
}

function startPolling(jobId, originalBody) {
    stopPolling();
    state.pollTimer = setInterval(async () => {
        try {
            const resp = await api.job(jobId);
            const job = resp?.data ?? resp ?? {};
            handleJobUpdate(job, originalBody);
        } catch (err) {
            // Netzwerkfehler beim Polling → kurz warten, nicht sofort abbrechen
            console.warn("Polling-Fehler:", err);
        }
    }, POLL_INTERVAL_MS);
}

function stopPolling() {
    if (state.pollTimer) {
        clearInterval(state.pollTimer);
        state.pollTimer = null;
    }
}

function handleJobUpdate(job, originalBody) {
    const status = job.status || "unknown";
    const pct = Math.round((job.progress ?? 0) * 100);

    if (status === "completed") {
        stopPolling();
        state.activeJob = job;
        showResultCompleted(job, originalBody);
    } else if (status === "failed") {
        stopPolling();
        showResultError(job.error || "Generierung fehlgeschlagen.");
    } else {
        // queued / running
        const msg = status === "queued" ? "In der Warteschlange…" : `Generierung läuft… ${pct > 0 ? pct + "%" : ""}`;
        showResultRunning(msg, pct);
    }
}

// ---------------------------------------------------------------------------
// Ergebnis-Seite rendern
// ---------------------------------------------------------------------------
function showResultRunning(msg, pct = 0) {
    byId("resultStatusBanner").style.display = "flex";
    byId("resultStatusBanner").className = "result-status-banner status-running";
    byId("resultStatusDot").textContent = "●";
    byId("resultStatusMsg").textContent = msg;
    byId("resultErrorBanner").style.display = "none";
    byId("resultProgressWrap").style.display = pct > 0 ? "flex" : "none";
    if (pct > 0) {
        byId("resultProgressFill").style.width = `${pct}%`;
        byId("resultProgressText").textContent = `${pct}%`;
    }
    // Aktionen sperren
    ["btnSave", "btnExport", "btnRegenerate"].forEach((id) => {
        const b = byId(id);
        if (b) b.disabled = true;
    });
}

function showResultError(msg) {
    byId("resultStatusBanner").style.display = "none";
    byId("resultErrorBanner").style.display = "block";
    byId("resultErrorText").textContent = msg;
    byId("resultProgressWrap").style.display = "none";
}

function showResultCompleted(job, originalBody) {
    byId("resultStatusBanner").style.display = "flex";
    byId("resultStatusBanner").className = "result-status-banner status-completed";
    byId("resultStatusMsg").textContent = "Fertig";
    byId("resultProgressWrap").style.display = "none";
    setTimeout(() => { byId("resultStatusBanner").style.display = "none"; }, 1500);

    byId("resultErrorBanner").style.display = "none";

    const title = job.title || originalBody?.title || "Ergebnis";
    byId("resultTitle").textContent = esc(title);

    const type = state.lastType === "beat" ? "Beat" : "Track";
    const genre = originalBody?.genre || job.genre || "–";
    const engine = job.engine_used || state.activeEngine || "–";
    byId("resultType").textContent = type;
    byId("resultGenre").textContent = genre;
    byId("resultEngine").textContent = engine;
    byId("resultDurationChip").textContent = fmtDuration(originalBody?.duration);

    // Details
    byId("detailType").textContent = type;
    byId("detailGenre").textContent = genre;
    byId("detailSubstyle").textContent = originalBody?.substyle || "–";
    byId("detailDuration").textContent = fmtDuration(originalBody?.duration);
    byId("detailBpm").textContent = originalBody?.bpm ?? "–";
    byId("detailEngine").textContent = engine;
    byId("detailProfile").textContent = originalBody?.profile || state.activeProfile || "–";
    byId("detailPrompt").textContent = originalBody?.prompt || "–";

    // Audio
    const audioUrl = job.output_url || job.audio_url;
    const isMock = engine === "mock";
    byId("mockBanner").style.display = isMock ? "block" : "none";
    if (audioUrl) {
        const player = byId("audioPlayer");
        player.src = audioUrl.startsWith("http") ? audioUrl : `${API_BASE}${audioUrl}`;
        player.load();
    }

    // Aktionen freischalten
    ["btnSave", "btnExport", "btnRegenerate"].forEach((id) => {
        const b = byId(id);
        if (b) b.disabled = false;
    });
}

// ---------------------------------------------------------------------------
// Ergebnis-Aktionen
// ---------------------------------------------------------------------------
function setupResultActions() {
    byId("btnBack")?.addEventListener("click", () => {
        stopPolling();
        navigateTo(state.lastType === "beat" ? "beat" : "track");
    });

    byId("btnRegenerate")?.addEventListener("click", async () => {
        if (!state.lastRequest || !state.lastType) return;
        await startGeneration(state.lastType, state.lastRequest);
    });

    byId("btnSave")?.addEventListener("click", async () => {
        if (!state.activeJob) return;
        const name = await promptForName("Projekt speichern", "Projektname", state.activeJob.title || "Mein Projekt");
        if (!name) return;
        try {
            await api.saveProject({
                title: name,
                job_id: state.activeJob.id || state.activeJob.job_id,
                type: state.lastType,
                genre: state.lastRequest?.genre,
                output_url: state.activeJob.output_url,
                metadata: state.lastRequest,
            });
            showToast("Projekt gespeichert.");
        } catch (err) {
            showToast(`Fehler beim Speichern: ${err.message}`, true);
        }
    });

    byId("btnExport")?.addEventListener("click", () => {
        const url = state.activeJob?.output_url;
        if (!url) return;
        const absUrl = url.startsWith("http") ? url : `${API_BASE}${url}`;
        const a = document.createElement("a");
        a.href = absUrl;
        a.download = `${state.activeJob?.title || "export"}.wav`.replace(/\s+/g, "_");
        document.body.appendChild(a);
        a.click();
        a.remove();
    });
}

// ---------------------------------------------------------------------------
// Engine switchen (Status-Seite)
// ---------------------------------------------------------------------------
window.switchEngine = async function (engine) {
    const note = byId("engineSwitchNote");
    try {
        await api.switchEngine(engine);
        showToast(`Engine auf „${engine}" umgestellt.`);
        await loadEngineStatus();
        populateEngineDropdowns();
    } catch (err) {
        if (note) {
            note.style.display = "block";
            note.textContent = `Fehler: ${err.message}`;
        }
        showToast(`Umschalten fehlgeschlagen: ${err.message}`, true);
    }
};

window.switchProfile = async function (profileId) {
    try {
        await api.switchProfile(profileId);
        state.activeProfile = profileId;
        showToast(`Profil „${profileId}" aktiviert.`);
        renderProfileList();
        populateProfileDropdowns();
    } catch (err) {
        showToast(`Profil-Wechsel fehlgeschlagen: ${err.message}`, true);
    }
};

// ---------------------------------------------------------------------------
// Projekte laden
// ---------------------------------------------------------------------------
async function loadProjects() {
    try {
        const resp = await api.projects();
        const list = resp?.data ?? resp?.projects ?? [];
        state.allProjects = Array.isArray(list) ? list : [];
    } catch (e) {
        state.allProjects = [];
    }
    renderProjects();
    renderDashboardRecent();
}

function renderDashboardRecent() {
    const el = byId("dashRecentList");
    if (!el) return;
    const recent = [...state.allProjects]
        .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
        .slice(0, 5);
    if (!recent.length) {
        el.innerHTML = '<p class="placeholder">Noch keine Projekte</p>';
        return;
    }
    el.innerHTML = recent.map((p) => `
        <div class="recent-item">
            <span class="recent-title">${esc(p.title || p.name || "Ohne Titel")}</span>
            <span class="recent-meta">${esc(p.type || "–")} · ${esc(p.genre || "–")} · ${fmtDate(p.created_at)}</span>
        </div>
    `).join("");
}

function renderProjects() {
    const el = byId("projectsList");
    if (!el) return;
    const search = byId("projectSearch")?.value.toLowerCase() ?? "";
    const filterType = document.querySelector(".filter-btn.active")?.dataset.filter ?? "all";
    const filterGenre = byId("genreFilter")?.value ?? "";
    const sortMode = byId("sortFilter")?.value ?? "newest";

    let list = [...state.allProjects];

    if (search) list = list.filter((p) => (p.title || "").toLowerCase().includes(search));
    if (filterType !== "all") list = list.filter((p) => p.type === filterType);
    if (filterGenre) list = list.filter((p) => p.genre === filterGenre);

    list.sort((a, b) => {
        if (sortMode === "oldest") return new Date(a.created_at || 0) - new Date(b.created_at || 0);
        if (sortMode === "name") return (a.title || "").localeCompare(b.title || "");
        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
    });

    state.filteredProjects = list;

    if (!list.length) {
        el.innerHTML = '<p class="placeholder">Keine Projekte gefunden.</p>';
        return;
    }

    el.innerHTML = list.map((p) => `
        <div class="project-card">
            <div class="project-card-main">
                <strong class="project-title">${esc(p.title || p.name || "Ohne Titel")}</strong>
                <div class="project-meta">
                    <span class="meta-chip">${esc(p.type || "–")}</span>
                    <span class="meta-chip meta-chip-genre">${esc(p.genre || "–")}</span>
                    <span class="project-date">${fmtDate(p.created_at)}</span>
                </div>
            </div>
            ${(p.output_url || p.audio_url) ? `
            <div class="project-card-actions">
                <audio controls src="${esc((p.output_url || p.audio_url).startsWith("http") ? (p.output_url || p.audio_url) : API_BASE + (p.output_url || p.audio_url))}" class="audio-player audio-player-small"></audio>
            </div>` : ""}
        </div>
    `).join("");
}

function setupProjectFilters() {
    byId("projectSearch")?.addEventListener("input", renderProjects);
    byId("genreFilter")?.addEventListener("change", renderProjects);
    byId("sortFilter")?.addEventListener("change", renderProjects);
    document.querySelectorAll(".filter-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
            btn.classList.add("active");
            renderProjects();
        });
    });
}

// ---------------------------------------------------------------------------
// Name-Dialog
// ---------------------------------------------------------------------------
function setupNameDialog() {
    const dialog = byId("nameDialog");
    if (!dialog) return;
    const form = byId("nameDialogForm");
    const cancelBtn = byId("nameDialogCancel");

    const close = (value) => {
        const resolve = state.dialogResolve;
        state.dialogResolve = null;
        if (dialog.open) dialog.close();
        resolve?.(value);
    };

    form.addEventListener("submit", (e) => {
        e.preventDefault();
        close(byId("nameDialogField").value.trim() || null);
    });
    cancelBtn.addEventListener("click", () => close(null));
    dialog.addEventListener("cancel", (e) => { e.preventDefault(); close(null); });
    dialog.addEventListener("click", (e) => {
        const r = dialog.getBoundingClientRect();
        if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) {
            close(null);
        }
    });
}

function promptForName(title, label, defaultVal = "") {
    const dialog = byId("nameDialog");
    if (!dialog) return Promise.resolve(window.prompt(label, defaultVal));

    if (state.dialogResolve) { state.dialogResolve(null); state.dialogResolve = null; }

    byId("nameDialogTitle").textContent = title;
    byId("nameDialogLabel").textContent = label;
    byId("nameDialogField").value = defaultVal;

    return new Promise((resolve) => {
        state.dialogResolve = resolve;
        dialog.showModal();
        requestAnimationFrame(() => {
            const f = byId("nameDialogField");
            f.focus();
            f.select();
        });
    });
}

// ---------------------------------------------------------------------------
// DOMContentLoaded — Initialisierung
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", async () => {
    setupNavigation();
    setupSliders();
    setupBeatForm();
    setupTrackForm();
    setupResultActions();
    setupProjectFilters();
    setupNameDialog();

    // Parallel laden
    await Promise.allSettled([
        loadGenres(),
        loadEngineStatus(),
        loadProfiles(),
        loadProjects(),
    ]);

    // Engine-Dropdowns erst nach Status befüllen
    populateEngineDropdowns();
});
