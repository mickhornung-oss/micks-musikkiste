const API_BASE = window.location.origin;

const state = {
    currentJob: null,
    currentJobId: null,
    currentProjectId: null,
    trackPresets: [],
    beatPresets: [],
    allProjects: [],
    filteredProjects: [],
    selectedMode: null,
};

const MODE_CONFIGS = {
    techno_beat: {
        page: "beat",
        navLabel: "Techno Beat",
        toast: "Techno Beat ist bereit.",
        beatPreset: "beat_techno_club",
        beatTitle: "Techno Beat",
        beatMood: "groovy",
        beatDuration: "45",
        beatPageTitle: "Techno Beat",
        beatPageIntro: "Druckvoller Club-Groove mit klarem Kick-Fokus und ohne Vocal-Chaos.",
    },
    hiphop_beat: {
        page: "beat",
        navLabel: "Hip-Hop Beat",
        toast: "Hip-Hop Beat ist bereit.",
        beatPreset: "beat_hiphop_trap",
        beatTitle: "Hip-Hop Beat",
        beatMood: "laid back",
        beatDuration: "45",
        beatPageTitle: "Hip-Hop Beat",
        beatPageIntro: "Head-nod Groove mit 808-Fokus, klarer Rhythmik und sofort brauchbarem Hip-Hop-Start.",
    },
    full_track: {
        page: "track",
        navLabel: "Voller Track",
        toast: "Voller Track ist bereit.",
        trackPreset: "techno_melodic",
        trackTitle: "Full Track",
        trackMood: "energetic",
        trackDuration: "60",
    },
};

const dialogState = {
    resolve: null,
};

const byId = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", async () => {
    setupNavigation();
    setupEventListeners();
    setupTextInputDialog();
    setupSliderUpdates();
    resetResultUI();
    await loadPresets();
    await loadProjects();
    await loadSystemStatus();
});

function formatDateTime(value) {
    if (!value) return "-";
    const date = new Date(value);
    return `${date.toLocaleDateString("de-DE")} ${date.toLocaleTimeString("de-DE", { hour: "2-digit", minute: "2-digit" })}`;
}

function formatDuration(seconds) {
    if (!Number.isFinite(seconds)) return "-";
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${String(secs).padStart(2, "0")} min`;
}

function escapeHtml(text) {
    return String(text || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function buildAbsoluteUrl(path) {
    if (!path) return "";
    return path.startsWith("http") ? path : `${API_BASE}${path}`;
}

function triggerDownload(url, filename) {
    const link = document.createElement("a");
    link.href = url;
    link.download = filename || "export";
    document.body.appendChild(link);
    link.click();
    link.remove();
}

function buildSlug(value, fallback = "micks-export") {
    const slug = String(value || "")
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9\s_-]/g, "")
        .replace(/\s+/g, "_");
    return slug || fallback;
}

function setupTextInputDialog() {
    const dialog = byId("textInputDialog");
    if (!dialog) return;

    const form = byId("textInputDialogForm");
    const input = byId("textInputField");
    const cancelButton = byId("textInputCancel");

    const closeDialog = (value) => {
        const resolve = dialogState.resolve;
        dialogState.resolve = null;
        if (dialog.open) {
            dialog.close();
        }
        resolve?.(value);
    };

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        closeDialog(input.value.trim() || null);
    });

    cancelButton.addEventListener("click", () => closeDialog(null));

    dialog.addEventListener("cancel", (event) => {
        event.preventDefault();
        closeDialog(null);
    });

    dialog.addEventListener("click", (event) => {
        const rect = dialog.getBoundingClientRect();
        const clickedBackdrop =
            event.clientX < rect.left ||
            event.clientX > rect.right ||
            event.clientY < rect.top ||
            event.clientY > rect.bottom;
        if (clickedBackdrop) {
            closeDialog(null);
        }
    });
}

async function promptForText({ title, description, label, defaultValue = "", confirmLabel = "Speichern" }) {
    const dialog = byId("textInputDialog");
    const input = byId("textInputField");
    if (!dialog || !input) {
        return window.prompt(title, defaultValue);
    }

    if (dialogState.resolve) {
        dialogState.resolve(null);
        dialogState.resolve = null;
    }

    byId("textInputDialogTitle").textContent = title;
    byId("textInputDialogDescription").textContent = description;
    byId("textInputDialogLabel").textContent = label;
    byId("textInputConfirm").textContent = confirmLabel;
    input.value = defaultValue;

    return new Promise((resolve) => {
        dialogState.resolve = resolve;
        dialog.showModal();
        window.requestAnimationFrame(() => {
            input.focus();
            input.select();
        });
    });
}

function showToast(message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `toast ${type === "error" ? "toast-error" : "toast-success"}`;
    toast.textContent = type === "error" ? `Warnung: ${message}` : message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), type === "error" ? 4500 : 3000);
}

function showMessage(message) {
    showToast(message, "success");
}

function showError(message) {
    showToast(message, "error");
    byId("progress").style.display = "none";
    byId("errorMessage").style.display = "block";
    byId("errorText").textContent = message;
}

async function apiRequest(path, options = {}) {
    const response = await fetch(`${API_BASE}${path}`, options);
    const isJson = response.headers.get("content-type")?.includes("application/json");
    const data = isJson ? await response.json() : null;
    if (!response.ok) {
        throw new Error(data?.error?.message || data?.detail || data?.message || `Request fehlgeschlagen: ${response.status}`);
    }
    return data;
}

function resetResultState() {
    state.currentJob = null;
    state.currentJobId = null;
    state.currentProjectId = null;
}

function clearAudioPlayer() {
    const player = byId("audioPlayer");
    player.pause();
    player.removeAttribute("src");
    player.load();
}

function toggleResultActions(disabled) {
    ["playBtn", "stopBtn", "exportBtn", "saveBtn", "varyBtn", "regenerateBtn"].forEach((id) => {
        const button = byId(id);
        if (button) button.disabled = disabled;
    });
}

function setResultPlaceholders() {
    byId("resultTitle").textContent = "Warte auf Generierung...";
    byId("resultType").textContent = "Track";
    byId("resultGenre").textContent = "Genre";
    byId("resultPreset").style.display = "none";
    byId("resultCreated").textContent = "Eben erstellt";
    byId("resultDetailsType").textContent = "Track";
    byId("resultDetailsGenre").textContent = "-";
    byId("resultDetailsDuration").textContent = "-";
    byId("resultDetailsMood").textContent = "-";
    byId("resultDetailsPreset").textContent = "Keines";
    byId("resultDetailsTempo").textContent = "-";
    toggleResultActions(true);
}

function updateProgress(value) {
    byId("progressFill").style.width = `${value}%`;
    byId("progressText").textContent = `${value}%`;
}

function updateResultStatus(status, text) {
    const banner = byId("resultStatus");
    banner.style.display = "block";
    banner.className = `result-status-banner status-${status}`;
    byId("resultStatusMsg").textContent = text;
    if (status === "completed") {
        setTimeout(() => {
            banner.style.display = "none";
        }, 1500);
    }
}

function resetResultUI() {
    byId("progress").style.display = "none";
    byId("errorMessage").style.display = "none";
    updateProgress(0);
    clearAudioPlayer();
    setResultPlaceholders();
    updateResultStatus("idle", "Bereit für deinen nächsten Track oder Beat.");
}

function showProgress() {
    byId("progress").style.display = "block";
    byId("errorMessage").style.display = "none";
    updateProgress(0);
    clearAudioPlayer();
    setResultPlaceholders();
}

function getPresetLabel(presetId, type) {
    if (!presetId) return null;
    const presets = type === "beat" ? state.beatPresets : state.trackPresets;
    return presets.find((preset) => preset.id === presetId)?.name || presetId;
}

function setupNavigation() {
    document.querySelectorAll(".nav-btn").forEach((button) => {
        button.addEventListener("click", () => {
            if (button.dataset.mode) {
                activateMode(button.dataset.mode);
                return;
            }
            navigateToPage(button.dataset.page);
        });
    });
    document.querySelectorAll(".action-card").forEach((card) => {
        card.addEventListener("click", () => {
            if (card.dataset.mode) {
                activateMode(card.dataset.mode);
                return;
            }
            navigateToPage(card.dataset.page);
        });
    });
}

function navigateToPage(pageName) {
    document.querySelectorAll(".page").forEach((page) => page.classList.remove("active"));
    byId(`page-${pageName}`)?.classList.add("active");
    document.querySelectorAll(".nav-btn").forEach((button) => {
        button.classList.toggle("active", button.dataset.page === pageName && !button.dataset.mode);
    });
    if (pageName === "beat" || pageName === "track") {
        syncModeChrome();
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
}

function setActiveModeUI(mode) {
    document.querySelectorAll(".nav-btn[data-mode]").forEach((button) => {
        button.classList.toggle("active", button.dataset.mode === mode);
    });
    document.querySelectorAll(".mode-chip[data-mode]").forEach((button) => {
        button.classList.toggle("active", button.dataset.mode === mode);
    });
}

function syncModeChrome() {
    if (state.selectedMode === "techno_beat" || state.selectedMode === "hiphop_beat") {
        const config = MODE_CONFIGS[state.selectedMode];
        byId("beatPageTitle").textContent = config.beatPageTitle;
        byId("beatPageIntro").textContent = config.beatPageIntro;
        setActiveModeUI(state.selectedMode);
        return;
    }
    if (state.selectedMode === "full_track") {
        setActiveModeUI("full_track");
    }
}

function activateMode(mode, { silent = false, preservePage = false, markActive = true } = {}) {
    const config = MODE_CONFIGS[mode];
    if (!config) return;
    const previousMode = state.selectedMode;
    state.selectedMode = mode;

    if (mode === "techno_beat" || mode === "hiphop_beat") {
        byId("beatPageTitle").textContent = config.beatPageTitle;
        byId("beatPageIntro").textContent = config.beatPageIntro;
        byId("beatTitle").value = byId("beatTitle").value && previousMode === mode ? byId("beatTitle").value : config.beatTitle;
        byId("beatPreset").value = config.beatPreset;
        applyBeatPreset(config.beatPreset);
        byId("beatMood").value = config.beatMood;
        byId("beatDuration").value = config.beatDuration;
    }

    if (mode === "full_track") {
        byId("trackTitle").value = byId("trackTitle").value && previousMode === mode ? byId("trackTitle").value : config.trackTitle;
        byId("trackPreset").value = config.trackPreset;
        applyTrackPreset(config.trackPreset);
        byId("trackMood").value = config.trackMood;
        byId("trackDuration").value = config.trackDuration;
    }

    if (!preservePage) {
        navigateToPage(config.page);
    } else if (markActive) {
        setActiveModeUI(mode);
    }

    if (markActive) {
        setActiveModeUI(mode);
    }
    if (!silent) showMessage(config.toast);
}

function setupEventListeners() {
    byId("trackForm").addEventListener("submit", handleTrackGeneration);
    byId("beatForm").addEventListener("submit", handleBeatGeneration);
    byId("trackForm").addEventListener("reset", () => window.setTimeout(() => activateMode("full_track"), 0));
    byId("beatForm").addEventListener("reset", () => window.setTimeout(() => activateMode(state.selectedMode === "hiphop_beat" ? "hiphop_beat" : "techno_beat"), 0));
    byId("playBtn").addEventListener("click", () => byId("audioPlayer").play());
    byId("stopBtn").addEventListener("click", () => byId("audioPlayer").pause());
    byId("varyBtn").addEventListener("click", handleVariation);
    byId("regenerateBtn").addEventListener("click", handleRegenerate);
    byId("saveBtn").addEventListener("click", handleSaveProject);
    byId("exportBtn").addEventListener("click", handleExport);
    byId("deleteBtn").addEventListener("click", handleDeleteResult);
    byId("backBtn").addEventListener("click", handleBackToEditor);
    byId("trackPreset").addEventListener("change", (event) => applyTrackPreset(event.target.value));
    byId("beatPreset").addEventListener("change", (event) => applyBeatPreset(event.target.value));
    document.querySelectorAll(".mode-chip[data-mode]").forEach((button) => {
        button.addEventListener("click", () => activateMode(button.dataset.mode));
    });

    ["projectSearch", "genreFilter", "presetFilter", "sortFilter"].forEach((id) => {
        byId(id)?.addEventListener("input", applyFilters);
        byId(id)?.addEventListener("change", applyFilters);
    });

    document.querySelectorAll(".filter-btn").forEach((button) => {
        button.addEventListener("click", () => {
            document.querySelectorAll(".filter-btn").forEach((candidate) => candidate.classList.remove("active"));
            button.classList.add("active");
            applyFilters();
        });
    });

}

function setupSliderUpdates() {
    [
        ["trackEnergy", "energyValue"],
        ["trackTempo", "tempoValue"],
        ["trackCreativity", "creativityValue"],
        ["trackCatchiness", "catchinessValue"],
        ["trackVocal", "vocalValue"],
        ["beatTempo", "beatTempoValue"],
        ["beatHeaviness", "heavinessValue"],
        ["beatMelody", "melodyValue"],
        ["beatEnergy", "beatEnergyValue"],
    ].forEach(([inputId, labelId]) => {
        const input = byId(inputId);
        const label = byId(labelId);
        if (!input || !label) return;
        label.textContent = input.value;
        input.addEventListener("input", () => {
            label.textContent = input.value;
        });
    });
}

async function loadPresets() {
    const [trackData, beatData] = await Promise.all([
        apiRequest("/api/presets/track"),
        apiRequest("/api/presets/beat"),
    ]);
    state.trackPresets = trackData.data?.presets || [];
    state.beatPresets = beatData.data?.presets || [];
    populatePresetFilter();
    activateMode("techno_beat", { silent: true, preservePage: true, markActive: false });
    activateMode("full_track", { silent: true, preservePage: true, markActive: false });
    state.selectedMode = null;
}

function populatePresetFilter() {
    const select = byId("presetFilter");
    const presets = [...state.trackPresets, ...state.beatPresets];
    const uniqueIds = [...new Map(presets.map((preset) => [preset.id, preset.name])).entries()];
    select.innerHTML = `
        <option value="">Alle Presets</option>
        <option value="with">Nur mit Preset</option>
        <option value="without">Ohne Preset</option>
    `;
    uniqueIds.forEach(([id, name]) => {
        const option = document.createElement("option");
        option.value = id;
        option.textContent = name;
        select.appendChild(option);
    });
}

function pickClosestOptionValue(selectId, desiredValue) {
    const select = byId(selectId);
    const numericDesired = Number.parseInt(desiredValue, 10);
    const options = [...select.options]
        .map((option) => Number.parseInt(option.value, 10))
        .filter((value) => Number.isFinite(value));

    if (!options.length || !Number.isFinite(numericDesired)) {
        return select.value;
    }

    return String(options.reduce((closest, current) => {
        return Math.abs(current - numericDesired) < Math.abs(closest - numericDesired) ? current : closest;
    }, options[0]));
}

function applyTrackPreset(presetId) {
    const preset = state.trackPresets.find((item) => item.id === presetId);
    byId("presetHint").style.display = preset ? "block" : "none";
    if (!preset?.values) return;
    if (preset.category === "techno") byId("trackGenre").value = "Techno";
    if (preset.category === "hiphop") byId("trackGenre").value = "Hip-Hop";
    byId("trackEnergy").value = preset.values.energy;
    byId("trackTempo").value = preset.values.tempo;
    byId("trackCreativity").value = preset.values.creativity;
    byId("trackCatchiness").value = preset.values.catchiness;
    byId("trackVocal").value = preset.values.vocal_strength || 5;
    byId("trackMood").value = preset.default_mood || byId("trackMood").value;
    byId("trackLanguage").value = preset.recommended_language || byId("trackLanguage").value;
    byId("trackDuration").value = pickClosestOptionValue("trackDuration", preset.recommended_duration || byId("trackDuration").value);
    byId("trackNegative").value = (preset.negative_prompts || []).join(", ");
    byId("presetHint").textContent = preset.description || "Preset-Werte werden direkt für den Erstlauf gesetzt.";
    setupSliderUpdates();
}

function applyBeatPreset(presetId) {
    const preset = state.beatPresets.find((item) => item.id === presetId);
    byId("beatPresetHint").style.display = preset ? "block" : "none";
    if (!preset?.values) return;
    if (preset.category === "techno") byId("beatGenre").value = "Techno";
    if (preset.category === "hiphop") byId("beatGenre").value = "Hip-Hop";
    byId("beatTempo").value = preset.values.tempo;
    byId("beatHeaviness").value = preset.values.heaviness;
    byId("beatMelody").value = preset.values.melody_amount;
    byId("beatEnergy").value = preset.values.energy;
    byId("beatMood").value = preset.default_mood || byId("beatMood").value;
    byId("beatDuration").value = pickClosestOptionValue("beatDuration", preset.recommended_duration || byId("beatDuration").value);
    byId("beatPresetHint").textContent = preset.description || "Preset-Werte werden direkt für Groove und Arrangement gesetzt.";
    setupSliderUpdates();
}

function buildTrackRequest() {
    return {
        title: byId("trackTitle").value,
        genre: byId("trackGenre").value,
        mood: byId("trackMood").value,
        language: byId("trackLanguage").value,
        duration: Number.parseInt(byId("trackDuration").value, 10),
        lyrics: byId("trackLyrics").value || null,
        negative_prompts: byId("trackNegative").value
            ? byId("trackNegative").value.split(",").map((item) => item.trim()).filter(Boolean)
            : [],
        energy: Number.parseInt(byId("trackEnergy").value, 10),
        tempo: Number.parseInt(byId("trackTempo").value, 10),
        creativity: Number.parseInt(byId("trackCreativity").value, 10),
        catchiness: Number.parseInt(byId("trackCatchiness").value, 10),
        vocal_strength: Number.parseInt(byId("trackVocal").value, 10),
        preset_id: byId("trackPreset").value || null,
    };
}

function buildBeatRequest() {
    return {
        title: byId("beatTitle").value,
        genre: byId("beatGenre").value,
        mood: byId("beatMood").value,
        duration: Number.parseInt(byId("beatDuration").value, 10),
        tempo: Number.parseInt(byId("beatTempo").value, 10),
        heaviness: Number.parseInt(byId("beatHeaviness").value, 10),
        melody_amount: Number.parseInt(byId("beatMelody").value, 10),
        energy: Number.parseInt(byId("beatEnergy").value, 10),
        preset_id: byId("beatPreset").value || null,
    };
}

async function handleTrackGeneration(event) {
    event.preventDefault();
    await submitGeneration("/api/track/generate", buildTrackRequest(), "track");
}

async function handleBeatGeneration(event) {
    event.preventDefault();
    await submitGeneration("/api/beat/generate", buildBeatRequest(), "beat");
}

async function submitGeneration(path, payload, type) {
    try {
        resetResultState();
        navigateToPage("result");
        showProgress();
        updateResultStatus("queued", `${type === "track" ? "Track" : "Beat"} steht in der Warteschlange...`);
        const data = await apiRequest(path, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        state.currentJobId = data.data.job_id;
        await monitorJob(state.currentJobId, type);
    } catch (error) {
        showError(error.message);
    }
}

async function monitorJob(jobId, type) {
    return new Promise((resolve) => {
        const interval = setInterval(async () => {
            try {
                const data = await apiRequest(`/api/jobs/${jobId}`);
                const job = data.data;
                updateProgress(job.progress || 0);

                if (job.status === "queued") {
                    updateResultStatus("queued", "In der Warteschlange...");
                    return;
                }
                if (job.status === "running" || job.status === "generating") {
                    updateResultStatus("running", `Wird generiert (${job.progress || 0}%)`);
                    return;
                }

                clearInterval(interval);
                if (job.status === "completed") {
                    state.currentJob = job;
                    state.currentJobId = job.id;
                    state.currentProjectId = null;
                    updateResultStatus("completed", "Fertig! Ergebnis bereit.");
                    showResult(job, type);
                    await loadProjects();
                    showMessage("Fertig generiert");
                } else {
                    showFailedResult(job);
                }
                resolve();
            } catch (error) {
                clearInterval(interval);
                updateResultStatus("failed", "Job-Überwachung fehlgeschlagen");
                showError(error.message);
                resolve();
            }
        }, 600);
    });
}

function buildAudioUrl(entity) {
    if (!entity) return "";
    if (entity.audio_url) return buildAbsoluteUrl(entity.audio_url);
    const filePath = entity.result_file || entity.output_file;
    if (!filePath) return "";
    const filename = filePath.split(/[/\\]/).pop();
    return `${API_BASE}/outputs/${filename}`;
}

function showResult(job, type) {
    byId("progress").style.display = "none";
    byId("errorMessage").style.display = "none";
    const player = byId("audioPlayer");
    player.src = buildAudioUrl(job);
    player.load();
    toggleResultActions(false);

    const metadata = job.metadata || {};
    const presetLabel = getPresetLabel(job.preset_used || metadata.preset_id, job.type);
    byId("resultTitle").textContent = metadata.title || job.title || "Unbenannt";
    byId("resultType").textContent = type === "beat" ? "Beat" : "Track";
    byId("resultGenre").textContent = metadata.genre || "-";
    byId("resultCreated").textContent = `Erstellt: ${formatDateTime(job.created_at)}`;
    byId("resultDetailsType").textContent = type === "beat" ? "Beat" : "Track";
    byId("resultDetailsGenre").textContent = metadata.genre || "-";
    byId("resultDetailsDuration").textContent = formatDuration(metadata.duration || 0);
    byId("resultDetailsMood").textContent = metadata.mood || "-";
    byId("resultDetailsPreset").textContent = presetLabel || "Keines";
    byId("resultDetailsTempo").textContent = metadata.tempo ? `${metadata.tempo} BPM` : "-";

    if (presetLabel) {
        byId("resultPreset").style.display = "inline-block";
        byId("resultPreset").textContent = presetLabel;
    } else {
        byId("resultPreset").style.display = "none";
    }
}

function showFailedResult(job) {
    state.currentJob = null;
    state.currentJobId = job?.id || null;
    state.currentProjectId = null;
    byId("progress").style.display = "none";
    byId("errorMessage").style.display = "block";
    byId("errorText").textContent = job?.error || "Generierung abgebrochen";
    toggleResultActions(true);
    clearAudioPlayer();
    updateResultStatus(job?.status || "failed", job?.error || "Generierung abgebrochen");
}

function handleDeleteResult() {
    resetResultState();
    resetResultUI();
    navigateToPage("dashboard");
}

function handleBackToEditor() {
    if (!state.currentJob) {
        navigateToPage("dashboard");
        return;
    }
    navigateToPage(state.currentJob.type === "beat" ? "beat" : "track");
}

async function handleVariation() {
    if (!state.currentJob) return;
    showMessage("Variation bleibt in diesem Block ein Mock-Platzhalter.");
}

async function handleRegenerate() {
    if (!state.currentJob) return;
    const project = projectFromCurrentJob();
    if (state.currentJob.type === "beat") {
        restoreBeatForm(project);
        navigateToPage("beat");
    } else {
        restoreTrackForm(project);
        navigateToPage("track");
    }
    showMessage("Einstellungen übernommen.");
}

function projectFromCurrentJob() {
    const metadata = state.currentJob?.metadata || {};
    return {
        id: state.currentProjectId,
        name: metadata.title || state.currentJob?.title,
        type: state.currentJob?.type,
        genre: metadata.genre,
        mood: metadata.mood,
        duration: metadata.duration,
        preset_used: state.currentJob?.preset_used || metadata.preset_id || null,
        lyrics: metadata.lyrics || null,
        negative_prompts: metadata.negative_prompts || [],
        parameters: metadata,
        metadata,
        output_file: state.currentJob?.result_file || null,
        audio_url: state.currentJob?.audio_url || null,
    };
}

async function handleSaveProject() {
    if (!state.currentJob) {
        showError("Kein Ergebnis zum Speichern vorhanden");
        return;
    }

    const projectName = await promptForText({
        title: "Projekt speichern",
        description: "Gib deinem gespeicherten Projekt einen klaren Namen.",
        label: "Projektname",
        defaultValue: state.currentJob.metadata?.title || state.currentJob.title || "Neues Projekt",
        confirmLabel: "Projekt speichern",
    });
    if (!projectName) return;

    const metadata = state.currentJob.metadata || {};
    const payload = {
        name: projectName,
        project_type: state.currentJob.type,
        genre: metadata.genre || "Techno",
        mood: metadata.mood || "neutral",
        duration: metadata.duration || 120,
        output_file: state.currentJob.result_file || null,
        preset_used: state.currentJob.preset_used || metadata.preset_id || null,
        lyrics: metadata.lyrics || null,
        negative_prompts: metadata.negative_prompts || [],
        parameters: metadata,
        metadata: { ...metadata, source_job_id: state.currentJob.id },
    };

    try {
        const data = await apiRequest("/api/projects", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        state.currentProjectId = data.data.id;
        await loadProjects();
        showMessage("Projekt gespeichert");
    } catch (error) {
        showError(error.message);
    }
}

async function handleExport() {
    if (!state.currentJob && !state.currentProjectId) {
        showError("Kein Ergebnis zum Exportieren vorhanden");
        return;
    }

    const exportName = await promptForText({
        title: "Export erstellen",
        description: "Lege den Dateinamen für den Export fest.",
        label: "Export-Name",
        defaultValue: buildSlug(state.currentJob?.metadata?.title || state.currentJob?.title || state.currentProjectId || "micks-export"),
        confirmLabel: "Exportieren",
    });
    if (!exportName) return;

    try {
        const path = state.currentProjectId
            ? `/api/projects/${state.currentProjectId}/export?export_name=${encodeURIComponent(exportName)}`
            : `/api/export/${state.currentJob.id}?export_name=${encodeURIComponent(exportName)}`;
        const data = await apiRequest(path, { method: "POST" });
        triggerDownload(buildAbsoluteUrl(data.data.public_url), data.data.filename);
        await loadProjects();
        showMessage("Export erstellt");
    } catch (error) {
        showError(error.message);
    }
}

async function loadProjects() {
    try {
        const data = await apiRequest("/api/projects");
        state.allProjects = data.data?.projects || [];
        applyFilters();
        renderRecentProjects();
    } catch (error) {
        state.allProjects = [];
        state.filteredProjects = [];
        renderProjectCards();
        renderRecentProjects();
        showError(error.message);
    }
}

function applyFilters() {
    const searchTerm = (byId("projectSearch")?.value || "").trim().toLowerCase();
    const typeFilter = document.querySelector(".filter-btn.active")?.dataset.filter || "all";
    const genreFilter = byId("genreFilter")?.value || "";
    const presetFilter = byId("presetFilter")?.value || "";
    const sortFilter = byId("sortFilter")?.value || "newest";

    state.filteredProjects = state.allProjects.filter((project) => {
        const haystack = [project.name, project.genre, project.mood].map((value) => String(value || "").toLowerCase());
        const matchesSearch = !searchTerm || haystack.some((value) => value.includes(searchTerm));
        const matchesType = typeFilter === "all" || project.type === typeFilter;
        const matchesGenre = !genreFilter || project.genre === genreFilter;
        const hasPreset = Boolean(project.preset_used);
        const matchesPreset =
            !presetFilter ||
            (presetFilter === "with" && hasPreset) ||
            (presetFilter === "without" && !hasPreset) ||
            project.preset_used === presetFilter;
        return matchesSearch && matchesType && matchesGenre && matchesPreset;
    });

    state.filteredProjects.sort((left, right) => {
        if (sortFilter === "oldest") return new Date(left.created_at) - new Date(right.created_at);
        if (sortFilter === "name") return left.name.localeCompare(right.name, "de");
        if (sortFilter === "export") return new Date(right.last_export_at || 0) - new Date(left.last_export_at || 0);
        return new Date(right.created_at) - new Date(left.created_at);
    });

    renderProjectCards();
}

function renderProjectCards() {
    const container = byId("projectsList");
    if (!container) return;
    if (!state.filteredProjects.length) {
        container.innerHTML = '<p class="placeholder">Keine Projekte gefunden.</p>';
        return;
    }

    container.innerHTML = state.filteredProjects.map((project) => {
        const presetLabel = getPresetLabel(project.preset_used, project.type) || project.preset_used || "";
        return `
            <div class="project-card" data-project-id="${project.id}">
                <div class="project-card-header">
                    <div class="project-card-title">${escapeHtml(project.name)}</div>
                    <div class="project-card-meta">
                        <span class="project-card-badge type-${escapeHtml(project.type)}">${project.type === "track" ? "Track" : "Beat"}</span>
                        <span class="project-card-badge">${escapeHtml(project.genre)}</span>
                        ${presetLabel ? `<span class="project-card-badge preset">${escapeHtml(presetLabel)}</span>` : ""}
                    </div>
                </div>
                <div class="project-card-info">
                    <div>${formatDateTime(project.created_at)}</div>
                    <div>${formatDuration(project.duration || 0)}</div>
                    <div>${escapeHtml(project.mood || "-")}</div>
                </div>
                <div class="project-card-actions">
                    <button type="button" class="project-card-btn primary" data-action="open" data-project-id="${project.id}" data-testid="project-open-btn">Öffnen</button>
                    <button type="button" class="project-card-btn secondary" data-action="play" data-project-id="${project.id}" data-testid="project-play-btn">Abspielen</button>
                    <button type="button" class="project-card-btn secondary" data-action="export" data-project-id="${project.id}" data-testid="project-export-btn">Export</button>
                    <button type="button" class="project-card-btn delete" data-action="delete" data-project-id="${project.id}" data-testid="project-delete-btn">Löschen</button>
                </div>
            </div>
        `;
    }).join("");
    attachActionButtonHandlers(container);
}

function renderRecentProjects() {
    const container = byId("recentProjects");
    if (!container) return;
    const recentProjects = [...state.allProjects]
        .sort((left, right) => new Date(right.created_at) - new Date(left.created_at))
        .slice(0, 3);

    if (!recentProjects.length) {
        container.innerHTML = '<p class="placeholder">Noch keine Projekte gespeichert.</p>';
        return;
    }

    container.innerHTML = recentProjects.map((project) => `
        <div class="project-item compact">
            <div>
                <div class="project-title">${escapeHtml(project.name)}</div>
                <div class="project-meta">${escapeHtml(project.type.toUpperCase())} · ${escapeHtml(project.genre)} · ${formatDateTime(project.created_at)}</div>
            </div>
            <div class="project-actions">
                <button type="button" class="btn btn-secondary" data-action="open" data-project-id="${project.id}" data-testid="recent-project-open-btn">Öffnen</button>
                <button type="button" class="btn btn-secondary" data-action="play" data-project-id="${project.id}" data-testid="recent-project-play-btn">Start</button>
            </div>
        </div>
    `).join("");
    attachActionButtonHandlers(container);
}

function attachActionButtonHandlers(container) {
    container.querySelectorAll("[data-action][data-project-id]").forEach((button) => {
        button.onclick = null;
        button.addEventListener("click", handleActionButtonClick);
    });
}

function handleActionButtonClick(event) {
    const actionButton = event.currentTarget;
    const { action, projectId } = actionButton.dataset;
    if (action === "open") {
        void openProject(projectId, event);
        return;
    }
    if (action === "play") {
        void playProjectAudio(projectId, event);
        return;
    }
    if (action === "export") {
        void exportProject(projectId, event);
        return;
    }
    if (action === "delete") {
        void deleteProject(projectId, event);
    }
}

function handleProjectListClick(event) {
    const actionButton = event.target.closest("[data-action][data-project-id]");
    if (!actionButton) return;
    handleActionButtonClick({ currentTarget: actionButton, target: actionButton, preventDefault: () => {}, stopPropagation: () => {} });
}

function handleRecentProjectsClick(event) {
    const actionButton = event.target.closest("[data-action][data-project-id]");
    if (!actionButton) return;
    handleActionButtonClick({ currentTarget: actionButton, target: actionButton, preventDefault: () => {}, stopPropagation: () => {} });
}

function normalizeProject(project) {
    return {
        ...project,
        parameters: project.parameters || {},
        metadata: project.metadata || {},
        negative_prompts: project.negative_prompts || [],
        exports: project.exports || [],
    };
}

function projectToJob(project) {
    const metadata = {
        ...project.parameters,
        ...project.metadata,
        title: project.metadata?.title || project.name,
        genre: project.genre,
        mood: project.mood,
        duration: project.parameters?.duration || project.duration,
        lyrics: project.lyrics || project.parameters?.lyrics || null,
        negative_prompts: project.negative_prompts || [],
        preset_id: project.preset_used || project.parameters?.preset_id || null,
    };
    return {
        id: project.last_job_id || project.id,
        type: project.type,
        title: project.name,
        status: "completed",
        progress: 100,
        result_file: project.output_file || null,
        output_file: project.output_file || null,
        audio_url: project.audio_url || project.download_url || null,
        created_at: project.created_at,
        preset_used: project.preset_used || null,
        metadata,
    };
}

async function openProject(projectId, event) {
    event?.stopPropagation();
    try {
        const data = await apiRequest(`/api/projects/${projectId}`);
        const project = normalizeProject(data.data);
        state.currentProjectId = project.id;
        state.currentJob = projectToJob(project);
        state.currentJobId = state.currentJob.id;

        if (project.type === "beat") {
            restoreBeatForm(project);
        } else {
            restoreTrackForm(project);
        }

        navigateToPage("result");
        showResult(state.currentJob, project.type);
        showMessage("Projekt geladen");
    } catch (error) {
        showError(error.message);
    }
}

function restoreTrackForm(project) {
    byId("trackTitle").value = project.name || project.metadata?.title || "";
    byId("trackGenre").value = project.genre || "";
    byId("trackMood").value = project.mood || "";
    byId("trackLanguage").value = project.parameters?.language || project.metadata?.language || "en";
    byId("trackDuration").value = pickClosestOptionValue("trackDuration", project.parameters?.duration || project.duration || 60);
    byId("trackLyrics").value = project.lyrics || project.parameters?.lyrics || "";
    byId("trackNegative").value = (project.negative_prompts || []).join(", ");
    byId("trackEnergy").value = project.parameters?.energy || 5;
    byId("trackTempo").value = project.parameters?.tempo || 120;
    byId("trackCreativity").value = project.parameters?.creativity || 5;
    byId("trackCatchiness").value = project.parameters?.catchiness || 5;
    byId("trackVocal").value = project.parameters?.vocal_strength || 5;
    byId("trackPreset").value = project.preset_used || "";
    applyTrackPreset(project.preset_used || "");
    state.selectedMode = "full_track";
    syncModeChrome();
    setupSliderUpdates();
}

function restoreBeatForm(project) {
    byId("beatTitle").value = project.name || "";
    byId("beatGenre").value = project.genre || "";
    byId("beatMood").value = project.mood || "";
    byId("beatDuration").value = pickClosestOptionValue("beatDuration", project.parameters?.duration || project.duration || 45);
    byId("beatTempo").value = project.parameters?.tempo || 120;
    byId("beatHeaviness").value = project.parameters?.heaviness || 5;
    byId("beatMelody").value = project.parameters?.melody_amount || 3;
    byId("beatEnergy").value = project.parameters?.energy || 6;
    byId("beatPreset").value = project.preset_used || "";
    applyBeatPreset(project.preset_used || "");
    state.selectedMode = project.preset_used === "beat_hiphop_boom" || project.preset_used === "beat_hiphop_trap"
        ? "hiphop_beat"
        : "techno_beat";
    syncModeChrome();
    setupSliderUpdates();
}

async function playProjectAudio(projectId, event) {
    event?.stopPropagation();
    try {
        const data = await apiRequest(`/api/projects/${projectId}`);
        const audioUrl = buildAudioUrl(data.data);
        if (!audioUrl) {
            showError("Keine Audiodatei verfügbar");
            return;
        }
        const audio = new Audio(audioUrl);
        await audio.play();
    } catch (error) {
        showError(error.message);
    }
}

async function deleteProject(projectId, event) {
    event?.stopPropagation();
    if (!window.confirm("Projekt wirklich löschen?")) return;
    try {
        await apiRequest(`/api/projects/${projectId}`, { method: "DELETE" });
        if (state.currentProjectId === projectId) {
            handleDeleteResult();
        }
        await loadProjects();
        showMessage("Projekt gelöscht");
    } catch (error) {
        showError(error.message);
    }
}

async function exportProject(projectId, event) {
    event?.stopPropagation();
    const project = state.allProjects.find((candidate) => candidate.id === projectId);
    const exportName = buildSlug(project?.name || "projekt-export", "projekt-export");
    try {
        const data = await apiRequest(`/api/projects/${projectId}/export?export_name=${encodeURIComponent(exportName)}`, {
            method: "POST",
        });
        triggerDownload(buildAbsoluteUrl(data.data.public_url), data.data.filename);
        await loadProjects();
        showMessage("Projekt exportiert");
    } catch (error) {
        showError(error.message);
    }
}

async function loadSystemStatus() {
    try {
        const data = await apiRequest("/health");
        const label = data.engine_name && data.engine_name !== data.engine_type
            ? `${data.engine_type} · ${data.engine_name}`
            : data.engine_type;
        byId("statusEngine").textContent = label || "-";
        byId("statusProjects").textContent = data.total_projects ?? "-";
        byId("statusOutputs").textContent = data.total_outputs ?? "-";
        byId("statusVersion").textContent = data.version || "-";
        byId("systemStatus").textContent = `• ${label || "unbekannt"}`;
    } catch (error) {
        console.error("Status laden fehlgeschlagen", error);
    }
}


