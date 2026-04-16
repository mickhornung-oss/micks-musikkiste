"""ACE-Step 1.5 engine adapter.

This adapter shells out to an external ACE-Step CLI/runner.
Expected contract: the command must create a WAV file at the requested --output path.
No silent fallback – if the command fails or produces no file, the job fails.
"""

import asyncio
import shlex
import socket
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from urllib.parse import urlparse

from app.config import settings
from app.services.comfy_service import get_comfy_state

from .base import EngineAdapter


class AceEngineAdapter(EngineAdapter):
    name = "ace-step-1.5"

    def __init__(self):
        self.command = settings.ACE_STEP_COMMAND
        self.max_duration = settings.ACE_STEP_MAX_DURATION

    def diagnostics(self) -> dict:
        workflow_path = self._extract_option("--workflow")
        comfy_url = self._extract_option("--comfy-url") or settings.COMFYUI_URL
        comfy_state = get_comfy_state()
        workflow_ok = bool(workflow_path and Path(workflow_path).exists())
        comfy_reachable = self._is_comfy_reachable(comfy_url)
        ready = bool(self.command) and workflow_ok and comfy_reachable
        return {
            "name": self.name,
            "mode": "ace",
            "ready": ready,
            "details": {
                "command": self.command,
                "workflow_path": workflow_path,
                "workflow_ok": workflow_ok,
                "comfy_url": comfy_url,
                "comfy_reachable": comfy_reachable,
                "comfy_autostart": comfy_state,
            },
        }

    async def generate_track_audio(self, payload: Dict[str, Any]) -> str:
        return await self._run_ace(payload, kind="track")

    async def generate_beat_audio(self, payload: Dict[str, Any]) -> str:
        # ACE-Step has no dedicated beat mode; reuse track path.
        return await self._run_ace(payload, kind="beat")

    async def _run_ace(self, payload: Dict[str, Any], kind: str) -> str:
        self._validate_runtime_requirements()
        output_filename = f"{kind}_{uuid.uuid4().hex[:8]}.mp3"
        output_path = settings.OUTPUTS_DIR / output_filename

        duration = int(payload.get("duration", 30))
        duration = max(5, min(duration, self.max_duration))

        tags = self._build_tags(payload, kind)
        negative_prompts = self._normalize_list(payload.get("negative_prompts"))
        lyrics_text = str(payload.get("lyrics") or "").strip()
        instrumental_preferred = bool(payload.get("instrumental_preferred"))
        if kind == "beat":
            instrumental_preferred = True
        elif lyrics_text:
            instrumental_preferred = False
        if int(payload.get("vocal_strength") or 0) <= 2 and not lyrics_text:
            instrumental_preferred = True

        cmd_parts = shlex.split(self.command)
        cmd_parts += [
            "--output",
            str(output_path),
            "--duration",
            str(duration),
            "--tags",
            ",".join(tags) if tags else "music",
        ]
        if lyrics_text:
            cmd_parts += ["--lyrics", lyrics_text[:5000]]
        if payload.get("title"):
            cmd_parts += ["--title", payload["title"][:200]]
        if negative_prompts:
            cmd_parts += ["--negative-prompts", ",".join(negative_prompts)]
        if instrumental_preferred:
            cmd_parts += ["--instrumental"]

        cmd_display = " ".join(shlex.quote(p) for p in cmd_parts)
        debug_path = settings.DATA_DIR / "engine_debug_ace.log"
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        with open(debug_path, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().isoformat()} | start | cmd={cmd_display}\n")

        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                cmd_parts,
                capture_output=True,
                text=True,
                timeout=settings.ENGINE_TIMEOUT,
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"ACE-Step timeout nach {settings.ENGINE_TIMEOUT}s | cmd={cmd_display}"
            )

        with open(debug_path, "a", encoding="utf-8") as fh:
            fh.write(
                f"{datetime.now().isoformat()} | rc={proc.returncode}\n"
                f"stdout: {proc.stdout[:2000]}\n"
                f"stderr: {proc.stderr[:2000]}\n\n"
            )

        if proc.returncode != 0:
            raise RuntimeError(
                f"ACE-Step exit {proc.returncode}: {proc.stderr or proc.stdout}"
            )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(
                "ACE-Step meldete Erfolg, aber keine Audiodatei gefunden"
            )

        return str(output_path)

    @staticmethod
    def _normalize_list(value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            raw_values = value.split(",")
        elif isinstance(value, (list, tuple, set)):
            raw_values = value
        else:
            raw_values = [value]

        normalized = []
        for item in raw_values:
            text = str(item).strip()
            if text and text not in normalized:
                normalized.append(text)
        return normalized

    def _build_tags(self, payload: Dict[str, Any], kind: str) -> list[str]:
        tags: list[str] = []
        for value in (
            payload.get("genre"),
            payload.get("mood"),
            payload.get("style_description"),
        ):
            if value:
                tags.append(str(value).strip())

        tags.extend(self._normalize_list(payload.get("preset_tags")))

        if payload.get("drum_kit_hint"):
            tags.append(f"drum kit:{payload['drum_kit_hint']}")
        if payload.get("preset_id"):
            tags.append(f"preset:{payload['preset_id']}")
        if payload.get("energy"):
            tags.append(f"energy:{payload['energy']}")
        if payload.get("tempo"):
            tags.append(f"tempo:{payload['tempo']} bpm")
        if payload.get("heaviness"):
            tags.append(f"heaviness:{payload['heaviness']}/10")
        if payload.get("melody_amount") is not None:
            tags.append(f"melody:{payload['melody_amount']}/10")
        if payload.get("creativity"):
            tags.append(f"creativity:{payload['creativity']}/10")
        if payload.get("catchiness"):
            tags.append(f"catchiness:{payload['catchiness']}/10")

        if kind == "beat":
            tags.extend(["instrumental beat", "no vocals", "loop-friendly groove"])
        elif int(payload.get("vocal_strength") or 0) <= 2:
            tags.extend(["mostly instrumental", "minimal vocals"])

        unique_tags = []
        for tag in tags:
            text = str(tag).strip()
            if text and text not in unique_tags:
                unique_tags.append(text)
        return unique_tags

    def _validate_runtime_requirements(self):
        if not self.command.strip():
            raise RuntimeError(
                "ACE-Step-Kommando ist leer. Bitte ACE_STEP_COMMAND setzen oder ENGINE_MODE=mock verwenden."
            )

        workflow_path = self._extract_option("--workflow")
        if not workflow_path or not Path(workflow_path).exists():
            raise RuntimeError(
                f"ACE-Workflow nicht gefunden: {workflow_path or 'nicht gesetzt'}. "
                "Bitte Workflow-Pfad prüfen oder ENGINE_MODE=mock verwenden."
            )

        comfy_url = self._extract_option("--comfy-url") or settings.COMFYUI_URL
        if not self._is_comfy_reachable(comfy_url):
            raise RuntimeError(
                f"ComfyUI unter {comfy_url} nicht erreichbar. "
                "Bitte ComfyUI starten oder ENGINE_MODE=mock verwenden."
            )

    def _extract_option(self, option: str) -> str | None:
        cmd_parts = shlex.split(self.command)
        for index, part in enumerate(cmd_parts):
            if part == option and index + 1 < len(cmd_parts):
                return cmd_parts[index + 1]
        return None

    @staticmethod
    def _is_comfy_reachable(comfy_url: str) -> bool:
        try:
            parsed = urlparse(comfy_url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            with socket.create_connection((host, port), timeout=2.0):
                return True
        except OSError:
            return False
