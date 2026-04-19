"""V2 API-Routes für Micks Musikkiste.

Klare Trennung von V1:
  - Eigener Router mit /api/v2/ Prefix
  - Saubere Request/Response-Verträge (BeatRequest, TrackRequest, GenerationStarted)
  - Prompt / Negativ-Prompt / Textidee strikt getrennt
  - Kein Preset-Merge, kein Genre-als-Navigation-Hack

Prompt-Logik (verbindlich):
  prompt        → direkte Musik-Beschreibung an die Engine (primär)
  negative_prompt → direkt als negative_prompts an Engine
  text_idea     → gespeichert als Metadaten, intern zu Themen-Tags aufbereitet,
                   NIEMALS direkt als Songtext/Lyrics an Engine weitergegeben
"""

import re
from typing import Optional

from app.config import settings
from app.database import get_db_session
from app.errors import NotFoundError
from app.logging_config import logger
from app.models import (
    BeatRequest,
    GenerationStarted,
    TrackRequest,
)
from app.services.engines import get_engine_diagnostics
from app.services.genre_service import get_all_genres, is_valid_genre
from app.services.music_service import MusicGenerationService
from app.services.project_service import ProjectService
from app.services.queue_worker import get_worker
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

v2_router = APIRouter(prefix="/api/v2", tags=["v2"])


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------

async def _get_music_service(
    session: AsyncSession = Depends(get_db_session),
) -> MusicGenerationService:
    return MusicGenerationService(session)


async def _get_project_service(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectService:
    return ProjectService(session)


# ---------------------------------------------------------------------------
# Interne Hilfsfunktionen
# ---------------------------------------------------------------------------

def _split_to_list(text: str) -> list[str]:
    """Konvertiert einen kommagetrennten String in eine bereinigte Liste."""
    if not text:
        return []
    return [p.strip() for p in text.split(",") if p.strip()]


def _extract_theme_tags(text_idea: str) -> list[str]:
    """Extrahiert max. 3 thematische Stichworte aus einer Textidee.

    WICHTIG: Das ist keine Lyrics-Konvertierung.
    Es werden nur grobe thematische Stichworte extrahiert, die als atmosphärische
    Hinweise in die Engine-Tags fließen – nicht als Songtext.
    Der ursprüngliche text_idea-Text wird NICHT an die Engine weitergegeben.
    """
    if not text_idea or not text_idea.strip():
        return []
    # Bereinige und extrahiere signifikante Wörter (max. 3)
    cleaned = re.sub(r"[^\w\s]", " ", text_idea.lower())
    words = [w for w in cleaned.split() if len(w) > 3]
    # Filtere Stoppwörter (rudimentär)
    stopwords = {"dass", "the", "and", "oder", "with", "that", "this", "für", "eine", "einen",
                 "über", "durch", "from", "into", "nach", "auch", "wird", "werden"}
    meaningful = [w for w in words if w not in stopwords]
    return meaningful[:3]  # max. 3 thematische Stichworte


def _build_beat_payload(request: BeatRequest, engine_used: str) -> dict:
    """Baut das interne Engine-Payload aus einem BeatRequest.

    prompt          → primäre Musikbeschreibung (direkt an Engine)
    negative_prompt → aufgeteilt und als negative_prompts Liste
    Kein text_idea, kein lyrics.
    """
    negative_list = _split_to_list(request.negative_prompt)

    return {
        "title": request.title,
        "genre": request.genre,
        "prompt": request.prompt,
        "negative_prompts": negative_list,
        "bpm": request.bpm,
        "duration": request.duration,
        "energy": request.energy,
        "darkness": request.darkness,
        "melody_amount": request.melody,
        "engine": engine_used,
        "profile": request.profile or settings.ENGINE_PROFILE,
        # Explizit keine text_idea, keine lyrics
        "_v2": True,
    }


def _build_track_payload(request: TrackRequest, engine_used: str) -> dict:
    """Baut das interne Engine-Payload aus einem TrackRequest.

    Strikte Feldregel:
      prompt        → direkt an Engine (Musik-Beschreibung)
      negative_prompt → als negative_prompts Liste
      text_idea     → NICHT an Engine als lyrics.
                      Wird als Metadaten gespeichert.
                      Nur max. 3 thematische Tags werden intern extrahiert.
    """
    negative_list = _split_to_list(request.negative_prompt)
    theme_tags = _extract_theme_tags(request.text_idea)

    return {
        "title": request.title,
        "genre": request.genre,
        "substyle": request.substyle,
        "prompt": request.prompt,
        "negative_prompts": negative_list,
        # text_idea: gespeichert in Metadaten, NIEMALS als lyrics an Engine
        "text_idea": request.text_idea,
        "text_theme_tags": theme_tags,   # max. 3 thematische Stichworte (kein Songtext)
        "bpm": request.bpm,
        "duration": request.duration,
        "energy": request.energy,
        "creativity": request.creativity,
        "melody_amount": request.melody,
        "vocal_strength": request.vocal_strength,
        "engine": engine_used,
        "profile": request.profile or settings.ENGINE_PROFILE,
        "_v2": True,
    }


def _resolve_engine(engine_override: Optional[str]) -> str:
    """Gibt die aktive Engine zurück (Override oder aktive Settings-Engine)."""
    if engine_override and engine_override in {"mock", "ace", "musicgen"}:
        return engine_override
    return settings.ENGINE_MODE or "mock"


# ---------------------------------------------------------------------------
# V2 Endpoints
# ---------------------------------------------------------------------------

@v2_router.post("/beat/generate", response_model=None)
async def v2_generate_beat(
    request: BeatRequest,
    music_service: MusicGenerationService = Depends(_get_music_service),
) -> dict:
    """Beat generieren (V2).

    Felder:
      - genre: techno | hiphop
      - prompt: freier Musikprompt (Pflicht, primäres Steuerinstrument)
      - negative_prompt: Ausschlüsse (optional)
      - bpm, duration, energy, darkness, melody: Steuerparameter
      - engine, profile: optionale Engine/Profil-Overrides
    """
    # Genre-Validierung (nicht hart blocken, aber warnen)
    if not is_valid_genre(request.genre):
        logger.warning("v2_beat_unknown_genre", genre=request.genre)

    engine_used = _resolve_engine(request.engine)
    payload = _build_beat_payload(request, engine_used)

    logger.info(
        "v2_beat_generate",
        title=request.title,
        genre=request.genre,
        engine=engine_used,
        prompt_length=len(request.prompt),
        has_negative=bool(request.negative_prompt),
    )

    job_id = await music_service.generate_beat(payload)

    return {
        "success": True,
        "message": "Beat-Generierung gestartet",
        "data": GenerationStarted(
            job_id=job_id,
            status="queued",
            title=request.title,
            engine_used=engine_used,
        ).model_dump(),
    }


@v2_router.post("/track/generate", response_model=None)
async def v2_generate_track(
    request: TrackRequest,
    music_service: MusicGenerationService = Depends(_get_music_service),
) -> dict:
    """Full Track generieren (V2).

    Felder:
      - genre: techno | hiphop
      - substyle: Substil (optional, z.B. melodic, dark, boombap)
      - prompt: freier Musikprompt (Pflicht, primäres Steuerinstrument)
      - negative_prompt: Ausschlüsse (optional)
      - text_idea: Themen-/Ideeninput (optional).
                   KEIN fertiger Songtext. Wird intern als Themen-Metadaten behandelt.
                   Wird NIEMALS 1:1 als Lyrics an die Engine weitergegeben.
      - bpm, duration, energy, creativity, melody, vocal_strength: Steuerparameter
      - engine, profile: optionale Engine/Profil-Overrides
    """
    if not is_valid_genre(request.genre):
        logger.warning("v2_track_unknown_genre", genre=request.genre)

    engine_used = _resolve_engine(request.engine)
    payload = _build_track_payload(request, engine_used)

    logger.info(
        "v2_track_generate",
        title=request.title,
        genre=request.genre,
        substyle=request.substyle,
        engine=engine_used,
        prompt_length=len(request.prompt),
        has_negative=bool(request.negative_prompt),
        has_text_idea=bool(request.text_idea),
    )

    job_id = await music_service.generate_track(payload)

    return {
        "success": True,
        "message": "Track-Generierung gestartet",
        "data": GenerationStarted(
            job_id=job_id,
            status="queued",
            title=request.title,
            engine_used=engine_used,
        ).model_dump(),
    }


@v2_router.get("/engine/status")
async def v2_engine_status() -> dict:
    """V2 Engine-Status mit vollständiger Readiness-Info für alle Engines."""
    diag = get_engine_diagnostics()
    worker = get_worker()
    worker_running = worker.get_status().get("running", False) if worker else False

    return {
        "success": True,
        "data": {
            "active_engine": settings.ENGINE_MODE,
            "active_profile": settings.ENGINE_PROFILE,
            "ready": diag.get("ready", False),
            "transport": diag.get("transport", "direct"),
            "details": diag.get("details", {}),
            "worker_running": worker_running,
        },
    }


@v2_router.get("/profiles")
async def v2_get_profiles() -> dict:
    """Gibt alle verfügbaren Engine-Profile zurück."""
    profiles_dir = settings.PROJECT_ROOT / "data" / "profiles"
    profiles = []
    if profiles_dir.exists():
        for p in sorted(profiles_dir.glob("*.json")):
            try:
                import json as _json
                profiles.append(_json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                pass
    return {
        "success": True,
        "data": {
            "profiles": profiles,
            "active_profile": settings.ENGINE_PROFILE,
        },
    }


@v2_router.get("/genres")
async def v2_get_genres() -> dict:
    """Gibt alle verfügbaren Genres und ihre Substile zurück."""
    return {
        "success": True,
        "data": {
            "genres": get_all_genres(),
        },
    }


@v2_router.get("/config")
async def v2_get_config() -> dict:
    """Gibt die V2-Produktkonfiguration zurück (für Frontend-Initialisierung)."""
    diag = get_engine_diagnostics()
    return {
        "success": True,
        "data": {
            "version": "2.0",
            "engine": {
                "active": settings.ENGINE_MODE,
                "profile": settings.ENGINE_PROFILE,
                "ready": diag.get("ready", False),
            },
            "genres": get_all_genres(),
            "limits": {
                "beat": {
                    "min_duration": 10,
                    "max_duration": 300,
                    "default_duration": 60,
                },
                "track": {
                    "min_duration": 10,
                    "max_duration": 600,
                    "default_duration": 180,
                },
                "bpm_min": 60,
                "bpm_max": 200,
            },
        },
    }


@v2_router.get("/jobs/{job_id}")
async def v2_get_job(
    job_id: str,
    music_service: MusicGenerationService = Depends(_get_music_service),
) -> dict:
    """Job-Status abfragen (V2, gleiche DB wie V1)."""
    job = await music_service.get_job_status(job_id)
    if not job:
        raise NotFoundError(
            "Job nicht gefunden", code="job_not_found", details={"job_id": job_id}
        )
    return {"success": True, "data": job}


@v2_router.post("/projects")
async def v2_save_project(
    body: dict,
    project_service: ProjectService = Depends(_get_project_service),
) -> dict:
    """Projekt speichern (V2).

    Erwartet V2-Felder:
      title, type (beat|track), genre, output_url, job_id, metadata (optional)
    """
    title = body.get("title") or "Ohne Titel"
    project_type = body.get("type", "beat")
    genre = body.get("genre", "")
    output_url = body.get("output_url", "")
    metadata = body.get("metadata") or {}

    # output_url in output_file (lokalen Pfad) konvertieren, soweit möglich
    output_file: Optional[str] = None
    if output_url:
        filename = output_url.lstrip("/").replace("outputs/", "").replace("exports/", "")
        from pathlib import Path as _Path
        candidate = settings.OUTPUTS_DIR / filename
        if candidate.exists():
            output_file = str(candidate)

    project = await project_service.create_project(
        name=title,
        project_type=project_type,
        genre=genre,
        mood=metadata.get("substyle") or "",
        duration=int(metadata.get("duration") or 0),
        parameters=metadata,
        output_file=output_file,
        metadata={
            "title": title,
            "job_id": body.get("job_id"),
            "output_url": output_url,
            **metadata,
        },
        last_job_id=body.get("job_id"),
    )
    return {"success": True, "message": "Projekt gespeichert", "data": project}


@v2_router.get("/projects")
async def v2_list_projects(
    project_service: ProjectService = Depends(_get_project_service),
) -> dict:
    """Projektliste (V2) — gibt V2-kompatible Felder zurück."""
    projects = await project_service.list_projects()
    v2_projects = []
    for p in projects:
        v2_projects.append({
            "id": p.get("id"),
            "title": p.get("name") or p.get("title") or "Ohne Titel",
            "type": p.get("type"),
            "genre": p.get("genre"),
            "output_url": p.get("audio_url") or p.get("output_url"),
            "created_at": p.get("created_at"),
            "metadata": p.get("metadata") or {},
        })
    return {"success": True, "data": {"total": len(v2_projects), "projects": v2_projects}}
