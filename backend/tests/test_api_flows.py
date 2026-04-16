import time
from pathlib import Path

from conftest import TEST_PREFIX


def wait_for_job_completion(client, job_id, timeout=60):
    deadline = time.time() + timeout
    last_payload = None
    while time.time() < deadline:
        response = client.get(f"/api/jobs/{job_id}")
        assert response.status_code == 200
        last_payload = response.json()["data"]
        if last_payload["status"] in {"completed", "failed", "cancelled"}:
            return last_payload
        time.sleep(0.5)
    raise AssertionError(
        f"Job {job_id} wurde nicht rechtzeitig abgeschlossen: {last_payload}"
    )


def test_health_and_frontend_shell(client):
    health = client.get("/health")
    assert health.status_code == 200
    payload = health.json()
    assert payload["status"] == "ok"
    assert payload["engine_type"] == "mock"
    assert "X-Request-ID" in health.headers

    diagnostics = client.get("/api/diagnostics")
    assert diagnostics.status_code == 200
    diagnostics_payload = diagnostics.json()
    assert diagnostics_payload["engine"]["ready"] is True
    assert diagnostics_payload["engine"]["mode"] == "mock"
    assert diagnostics_payload["database"]["ok"] is True
    assert "app.log" in diagnostics_payload["logs"]["app_log"]

    root = client.get("/")
    assert root.status_code == 200
    assert "Micks Musikkiste" in root.text

    script = client.get("/static/js/app.js")
    assert script.status_code == 200
    assert "handleExport" in script.text
    assert "currentProjectId" in script.text


def test_mock_job_project_roundtrip_and_export(client, test_token):
    track_title = f"{TEST_PREFIX}{test_token}-track"
    project_name = f"{TEST_PREFIX}{test_token}-project"
    export_name = f"{TEST_PREFIX}{test_token}-export"

    job_response = client.post(
        "/api/track/generate",
        json={
            "title": track_title,
            "genre": "Techno",
            "mood": "dark",
            "language": "de",
            "duration": 45,
            "lyrics": "testen",
            "negative_prompts": ["rauschen"],
            "energy": 6,
            "tempo": 130,
            "creativity": 5,
            "catchiness": 4,
            "vocal_strength": 3,
            "preset_id": "techno_dark",
        },
    )
    assert job_response.status_code == 200
    job_id = job_response.json()["data"]["job_id"]

    job = wait_for_job_completion(client, job_id)
    assert job["status"] == "completed"
    assert Path(job["result_file"]).exists()
    assert job["metadata"]["title"] == track_title

    project_response = client.post(
        "/api/projects",
        json={
            "name": project_name,
            "project_type": "track",
            "genre": "Techno",
            "mood": "dark",
            "duration": job["metadata"]["duration"],
            "output_file": job["result_file"],
            "preset_used": job["preset_used"],
            "lyrics": job["metadata"]["lyrics"],
            "negative_prompts": job["metadata"]["negative_prompts"],
            "parameters": job["metadata"],
            "metadata": {**job["metadata"], "source_job_id": job["id"]},
        },
    )
    assert project_response.status_code == 200
    project = project_response.json()["data"]
    assert project["last_job_id"] == job["id"]
    assert project["audio_url"].startswith("/outputs/")

    list_response = client.get("/api/projects/search", params={"q": TEST_PREFIX})
    assert list_response.status_code == 200
    assert list_response.json()["data"]["total"] >= 1

    export_response = client.post(
        f"/api/projects/{project['id']}/export",
        params={"export_name": export_name},
    )
    assert export_response.status_code == 200
    export_data = export_response.json()["data"]
    assert export_data["public_url"].startswith("/exports/")
    export_file = Path(export_data["path"])
    assert export_file.exists()

    loaded_project = client.get(f"/api/projects/{project['id']}")
    assert loaded_project.status_code == 200
    loaded_data = loaded_project.json()["data"]
    assert loaded_data["last_export_at"] is not None
    assert len(loaded_data["exports"]) == 1


def test_export_non_completed_job_returns_400(client, test_token):
    response = client.post(
        "/api/export/not-a-real-job",
        params={"export_name": f"{TEST_PREFIX}{test_token}-bad"},
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "job_not_completed"
    assert payload["error"]["message"] == "Job nicht abgeschlossen"
    assert payload["error"]["request_id"]
