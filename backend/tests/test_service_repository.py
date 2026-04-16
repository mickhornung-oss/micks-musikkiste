from datetime import timedelta
from pathlib import Path

import pytest
from app.errors import InvalidStateError
from app.models.db_models import Job, JobStatus, Project, ProjectType, utc_now_naive
from app.repositories import JobRepository, ProjectRepository
from app.services.engines.ace import AceEngineAdapter
from app.services.music_service import MusicGenerationService
from app.services.project_service import ProjectService
from conftest import TEST_PREFIX


@pytest.mark.asyncio
async def test_music_service_marks_missing_result_file_as_failed(
    db_session, test_token
):
    job = Job(
        id=f"{TEST_PREFIX}{test_token}-missing-job",
        type="track",
        title=f"{TEST_PREFIX}{test_token}-missing-result",
        status=JobStatus.COMPLETED.value,
        progress=100,
        result_file=str(
            Path("data/outputs") / f"{TEST_PREFIX}{test_token}-missing.wav"
        ),
        metadata_json={"title": f"{TEST_PREFIX}{test_token}-missing-result"},
        engine="mock",
    )
    repo = JobRepository(db_session)
    await repo.create(job)
    await db_session.commit()

    service = MusicGenerationService(db_session)
    payload = await service.get_job_status(job.id)

    assert payload["status"] == JobStatus.FAILED.value
    assert payload["error"] == "Ergebnisdatei nicht vorhanden"


@pytest.mark.asyncio
async def test_project_service_rejects_invalid_project_type(db_session, test_token):
    service = ProjectService(db_session)

    with pytest.raises(InvalidStateError) as exc:
        await service.create_project(
            name=f"{TEST_PREFIX}{test_token}-invalid",
            project_type="mixtape",
            genre="Techno",
            mood="dark",
            duration=120,
            parameters={},
        )

    assert exc.value.code == "invalid_project_type"


@pytest.mark.asyncio
async def test_project_repository_add_export_updates_metadata(db_session, test_token):
    project = Project(
        id=f"{TEST_PREFIX}{test_token}-project-export",
        name=f"{TEST_PREFIX}{test_token}-project-export",
        type=ProjectType.TRACK.value,
        genre="Techno",
        mood="dark",
        duration=120,
        output_file=str(Path("data/outputs") / "demo_track_001.mp3"),
        parameters={"tempo": 128},
        metadata_json={"title": f"{TEST_PREFIX}{test_token}-project-export"},
        negative_prompts=[],
        exports=[],
        last_export_at=None,
    )
    repo = ProjectRepository(db_session)
    await repo.create(project)
    await db_session.commit()

    updated = await repo.add_export(
        project.id,
        f"{TEST_PREFIX}{test_token}-export.mp3",
        str(Path("data/exports") / f"{TEST_PREFIX}{test_token}-export.mp3"),
    )
    await db_session.commit()

    assert updated is not None
    assert updated.last_export_at is not None
    assert len(updated.exports) == 1
    assert updated.exports[0]["filename"] == f"{TEST_PREFIX}{test_token}-export.mp3"


@pytest.mark.asyncio
async def test_job_repository_status_counts(db_session, test_token):
    repo = JobRepository(db_session)
    queued = Job(
        id=f"{TEST_PREFIX}{test_token}-queued-job",
        type="track",
        title=f"{TEST_PREFIX}{test_token}-queued-title",
        status=JobStatus.QUEUED.value,
        progress=0,
        metadata_json={},
        engine="mock",
    )
    failed = Job(
        id=f"{TEST_PREFIX}{test_token}-failed-job",
        type="beat",
        title=f"{TEST_PREFIX}{test_token}-failed-title",
        status=JobStatus.FAILED.value,
        progress=0,
        error="kaputt",
        metadata_json={},
        engine="mock",
    )
    await repo.create(queued)
    await repo.create(failed)
    await db_session.commit()

    counts = await repo.get_status_counts()

    assert counts["queued"] >= 1
    assert counts["failed"] >= 1


def test_ace_engine_diagnostics_reports_missing_comfy(monkeypatch):
    monkeypatch.setattr(
        "app.services.engines.ace.settings.ACE_STEP_COMMAND",
        'python ../scripts/ace_comfy_wrapper.py --workflow "C:/Users/mickh/Desktop/Py Mick/vendor/ComfyUI/workflows/ACE-gen-lora.json" --comfy-url http://127.0.0.1:65530',
    )
    adapter = AceEngineAdapter()

    diagnostics = adapter.diagnostics()

    assert diagnostics["mode"] == "ace"
    assert diagnostics["details"]["workflow_ok"] is True
    assert diagnostics["details"]["comfy_reachable"] is False
    assert diagnostics["ready"] is False


@pytest.mark.asyncio
async def test_job_repository_recover_stuck_jobs_requeues_running_job(
    db_session, test_token
):
    repo = JobRepository(db_session)
    job = Job(
        id=f"{TEST_PREFIX}{test_token}-recover-job",
        type="track",
        title=f"{TEST_PREFIX}{test_token}-recover-title",
        status=JobStatus.RUNNING.value,
        progress=10,
        metadata_json={},
        engine="mock",
        attempt_count=1,
        max_attempts=3,
        claimed_at=utc_now_naive() - timedelta(minutes=20),
        heartbeat_at=utc_now_naive() - timedelta(minutes=20),
        worker_id="worker-old",
    )
    await repo.create(job)
    await db_session.commit()

    result = await repo.recover_stuck_jobs()
    await db_session.commit()
    recovered = await repo.get_by_id(job.id)

    assert result["recovered"] >= 1
    assert recovered is not None
    assert recovered.status == JobStatus.QUEUED.value
    assert recovered.worker_id is None
    assert recovered.heartbeat_at is None
    assert recovered.scheduled_at is not None


@pytest.mark.asyncio
async def test_job_repository_release_stale_jobs_marks_terminal_job_failed(
    db_session, test_token
):
    repo = JobRepository(db_session)
    job = Job(
        id=f"{TEST_PREFIX}{test_token}-stale-job",
        type="beat",
        title=f"{TEST_PREFIX}{test_token}-stale-title",
        status=JobStatus.RUNNING.value,
        progress=10,
        metadata_json={},
        engine="mock",
        attempt_count=3,
        max_attempts=3,
        claimed_at=utc_now_naive() - timedelta(minutes=20),
        heartbeat_at=utc_now_naive() - timedelta(minutes=20),
        worker_id="worker-old",
    )
    await repo.create(job)
    await db_session.commit()

    released = await repo.release_stale_jobs(timeout_seconds=60, current_job_id=None)
    await db_session.commit()
    failed = await repo.get_by_id(job.id)

    assert released == 0
    assert failed is not None
    assert failed.status == JobStatus.FAILED.value
    assert failed.worker_id is None
    assert failed.finished_at is not None
