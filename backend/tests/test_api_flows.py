import time
from pathlib import Path

from conftest import TEST_PREFIX


# ---------------------------------------------------------------------------
# Hilfsfunktion: Job pollen bis completed/failed
# ---------------------------------------------------------------------------
def wait_for_v2_job(client, job_id, timeout=60):
    """Pollt GET /api/v2/jobs/{job_id} bis Status terminal ist."""
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        resp = client.get(f"/api/v2/jobs/{job_id}")
        assert resp.status_code == 200, f"job-poll HTTP {resp.status_code}: {resp.text}"
        last = resp.json()["data"]
        if last["status"] in {"completed", "failed", "cancelled"}:
            return last
        time.sleep(0.5)
    raise AssertionError(f"Job {job_id} nicht abgeschlossen in {timeout}s: {last}")


# ---------------------------------------------------------------------------
# Test: Health / Diagnostics / Frontend-Shell (V2)
# ---------------------------------------------------------------------------
def test_health_and_frontend_shell(client):
    # Health
    health = client.get("/health")
    assert health.status_code == 200
    payload = health.json()
    assert payload["status"] == "ok"
    assert payload["engine_type"] == "mock"
    assert "X-Request-ID" in health.headers

    # Diagnostics
    diag = client.get("/api/diagnostics")
    assert diag.status_code == 200
    dp = diag.json()
    assert dp["engine"]["ready"] is True
    assert dp["engine"]["mode"] == "mock"
    assert dp["database"]["ok"] is True

    # Root gibt HTML zurück
    root = client.get("/")
    assert root.status_code == 200
    assert "Micks Musikkiste" in root.text

    # app.js enthält V2-Bezeichner
    script = client.get("/static/js/app.js")
    assert script.status_code == 200
    assert "api.beat" in script.text or "startGeneration" in script.text
    assert "output_url" in script.text
    # V1-Bezeichner dürfen nicht mehr vorkommen
    assert "handleExport" not in script.text
    assert "currentProjectId" not in script.text


# ---------------------------------------------------------------------------
# Test: V2-Endpunkte vorhanden
# ---------------------------------------------------------------------------
def test_v2_endpoints_exist(client):
    assert client.get("/api/v2/genres").status_code == 200
    assert client.get("/api/v2/profiles").status_code == 200
    assert client.get("/api/v2/engine/status").status_code == 200
    assert client.get("/api/v2/config").status_code == 200
    assert client.get("/api/v2/projects").status_code == 200


# ---------------------------------------------------------------------------
# Test: Genre/Substyle-Daten korrekt
# ---------------------------------------------------------------------------
def test_v2_genres_structure(client):
    resp = client.get("/api/v2/genres")
    assert resp.status_code == 200
    data = resp.json()["data"]
    genres = data["genres"]
    assert len(genres) >= 1
    for g in genres:
        assert "id" in g
        assert "label" in g
        assert isinstance(g.get("substyles"), list)
    # Substyle-Daten für hiphop vorhanden
    hip = next((g for g in genres if g["id"] == "hiphop"), None)
    assert hip is not None
    assert len(hip["substyles"]) > 0


# ---------------------------------------------------------------------------
# Test: Beat V2 Ende-zu-Ende (Mock)
# ---------------------------------------------------------------------------
def test_v2_beat_e2e_mock(client, test_token):
    title = f"{TEST_PREFIX}{test_token}-beat-e2e"

    # Beat generieren
    resp = client.post(
        "/api/v2/beat/generate",
        json={
            "title": title,
            "genre": "techno",
            "prompt": "dark industrial kick hypnotic groove",
            "negative_prompt": "vocals bright melody",
            "bpm": 130,
            "duration": 20,
            "energy": 8,
            "darkness": 7,
            "melody": 2,
            "engine": "mock",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    job_id = data["job_id"]
    assert data["status"] == "queued"
    assert data["engine_used"] == "mock"
    assert job_id

    # Job pollen
    job = wait_for_v2_job(client, job_id)
    assert job["status"] == "completed", f"Job failed: {job.get('error')}"
    assert job["output_url"] is not None and job["output_url"].startswith("/outputs/")
    assert Path(job["result_file"]).exists()
    assert Path(job["result_file"]).stat().st_size > 0

    # Audio-Datei über HTTP erreichbar
    audio_resp = client.get(job["output_url"])
    assert audio_resp.status_code == 200
    assert "audio" in audio_resp.headers.get("content-type", "")

    # Metadaten-Integrität
    meta = job["metadata"]
    assert meta["genre"] == "techno"
    assert meta["prompt"] == "dark industrial kick hypnotic groove"
    assert meta.get("_v2") is True
    # text_idea darf nicht im Beat vorkommen
    assert "text_idea" not in meta or meta.get("text_idea") is None


# ---------------------------------------------------------------------------
# Test: Full Track V2 Ende-zu-Ende mit text_idea-Trennung (Mock)
# ---------------------------------------------------------------------------
def test_v2_track_e2e_mock_with_text_idea(client, test_token):
    title = f"{TEST_PREFIX}{test_token}-track-e2e"

    resp = client.post(
        "/api/v2/track/generate",
        json={
            "title": title,
            "genre": "hiphop",
            "substyle": "boombap",
            "prompt": "boom bap groove sampled soul jazz piano",
            "negative_prompt": "harsh distortion noise",
            "text_idea": "Stadtleben, Regen, Nachtfahrt, Melancholie",
            "bpm": 90,
            "duration": 25,
            "energy": 6,
            "creativity": 7,
            "melody": 5,
            "vocal_strength": 4,
            "engine": "mock",
        },
    )
    assert resp.status_code == 200, resp.text
    job_id = resp.json()["data"]["job_id"]

    job = wait_for_v2_job(client, job_id)
    assert job["status"] == "completed"
    assert job["output_url"].startswith("/outputs/")

    meta = job["metadata"]
    # Felder-Integrität
    assert meta["genre"] == "hiphop"
    assert meta["substyle"] == "boombap"
    assert meta["prompt"] == "boom bap groove sampled soul jazz piano"

    # text_idea muss als Metadaten gespeichert sein, NICHT als lyrics
    assert meta["text_idea"] == "Stadtleben, Regen, Nachtfahrt, Melancholie"
    assert "lyrics" not in meta  # text_idea wird niemals als lyrics weitergegeben
    assert isinstance(meta.get("text_theme_tags"), list)
    assert len(meta["text_theme_tags"]) <= 3  # max. 3 Stichworte

    # text_theme_tags enthalten keine vollständigen Sätze (kein Songtext)
    for tag in meta["text_theme_tags"]:
        assert len(tag.split()) == 1, f"Tag '{tag}' ist kein Stichwort"


# ---------------------------------------------------------------------------
# Test: Projekt speichern + Projektliste (V2)
# ---------------------------------------------------------------------------
def test_v2_project_save_and_list(client, test_token):
    title = f"{TEST_PREFIX}{test_token}-proj-beat"

    # Beat erzeugen
    resp = client.post(
        "/api/v2/beat/generate",
        json={"title": title, "genre": "techno", "prompt": "minimal techno", "bpm": 128, "duration": 15, "engine": "mock"},
    )
    job_id = resp.json()["data"]["job_id"]
    job = wait_for_v2_job(client, job_id)
    assert job["status"] == "completed"

    # Speichern via V2
    save_resp = client.post(
        "/api/v2/projects",
        json={
            "title": f"{TEST_PREFIX}{test_token}-projekt",
            "type": "beat",
            "genre": "techno",
            "output_url": job["output_url"],
            "job_id": job_id,
            "metadata": {"prompt": "minimal techno", "bpm": 128, "duration": 15},
        },
    )
    assert save_resp.status_code == 200, save_resp.text
    project = save_resp.json()["data"]
    assert project["id"]

    # Projektliste via V2
    list_resp = client.get("/api/v2/projects")
    assert list_resp.status_code == 200
    projects = list_resp.json()["data"]["projects"]
    titles = [p["title"] for p in projects]
    assert any(TEST_PREFIX in t for t in titles)

    # V2-Felder vorhanden
    for p in projects:
        assert "title" in p
        assert "type" in p
        assert "genre" in p


# ---------------------------------------------------------------------------
# Test: Export nach Speichern (V1-Export-Endpunkt)
# ---------------------------------------------------------------------------
def test_v2_project_export(client, test_token):
    title = f"{TEST_PREFIX}{test_token}-export-beat"

    # Beat erzeugen + speichern
    resp = client.post(
        "/api/v2/beat/generate",
        json={"title": title, "genre": "techno", "prompt": "export test kick", "bpm": 128, "duration": 15, "engine": "mock"},
    )
    job_id = resp.json()["data"]["job_id"]
    job = wait_for_v2_job(client, job_id)

    save_resp = client.post(
        "/api/v2/projects",
        json={
            "title": title,
            "type": "beat",
            "genre": "techno",
            "output_url": job["output_url"],
            "job_id": job_id,
            "metadata": {"duration": 15},
        },
    )
    assert save_resp.status_code == 200
    project_id = save_resp.json()["data"]["id"]

    # Export
    export_resp = client.post(
        f"/api/projects/{project_id}/export",
        params={"export_name": f"{TEST_PREFIX}{test_token}-dl"},
    )
    assert export_resp.status_code == 200
    export_data = export_resp.json()["data"]
    assert export_data["public_url"].startswith("/exports/")
    assert Path(export_data["path"]).exists()


# ---------------------------------------------------------------------------
# Test: Engine-/Profil-Status (V2)
# ---------------------------------------------------------------------------
def test_v2_engine_status_honest(client):
    resp = client.get("/api/v2/engine/status")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["active_engine"] == "mock"
    assert data["ready"] is True  # Mock ist immer ready
    assert data["worker_running"] is True


def test_v2_profiles_available(client):
    resp = client.get("/api/v2/profiles")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert isinstance(data["profiles"], list)
    assert len(data["profiles"]) >= 1
    assert data["active_profile"] is not None


# ---------------------------------------------------------------------------
# Test: Fehlerzustand — ungültiges Genre wird nicht hart geblockt
# ---------------------------------------------------------------------------
def test_v2_beat_unknown_genre_accepted_with_warning(client, test_token):
    """V2 warnt bei unbekanntem Genre, bricht aber nicht ab."""
    resp = client.post(
        "/api/v2/beat/generate",
        json={
            "title": f"{TEST_PREFIX}{test_token}-bad-genre",
            "genre": "sonstwas",
            "prompt": "test",
            "bpm": 120,
            "duration": 10,
            "engine": "mock",
        },
    )
    # Soll durchgehen (nur Warnung, kein 400)
    assert resp.status_code == 200
    job_id = resp.json()["data"]["job_id"]
    job = wait_for_v2_job(client, job_id)
    assert job["status"] == "completed"

