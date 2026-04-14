"""Real engine adapter: executes an external CLI (default: internal engine_cli.py)."""

import asyncio
import shlex
import shutil
import sys
import uuid
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from app.config import settings
from .base import EngineAdapter


class RealEngineAdapter(EngineAdapter):
    name = "real"

    def __init__(self):
        # Fallback: internes MusicGen-CLI, sonst engine_cli.py falls gesetzt
        cli_path = Path(__file__).parent.parent.parent.parent / "engine_musicgen.py"
        self.cli_path = cli_path
        default_cmd = f"\"{sys.executable}\" \"{cli_path}\""
        self.command = settings.ENGINE_REAL_COMMAND or default_cmd

    def diagnostics(self) -> dict:
        cmd_parts = shlex.split(self.command)
        executable = cmd_parts[0] if cmd_parts else ""
        script_path = Path(cmd_parts[1]) if len(cmd_parts) > 1 and cmd_parts[1].endswith(".py") else self.cli_path
        executable_ok = Path(executable).exists() or bool(shutil.which(executable))
        script_ok = script_path.exists()
        ready = executable_ok and script_ok
        return {
            "name": self.name,
            "mode": "real",
            "ready": ready,
            "details": {
                "command": self.command,
                "executable": executable,
                "executable_ok": executable_ok,
                "script": str(script_path),
                "script_ok": script_ok,
            },
        }

    async def generate_track_audio(self, payload: Dict[str, Any]) -> str:
        return await self._run_external_engine(payload, kind="track")

    async def generate_beat_audio(self, payload: Dict[str, Any]) -> str:
        return await self._run_external_engine(payload, kind="beat")

    async def _run_external_engine(self, payload: Dict[str, Any], kind: str) -> str:
        # Wir erzeugen immer WAV, sicher abspielbar
        output_filename = f"{kind}_{uuid.uuid4().hex[:8]}.wav"
        output_path = settings.OUTPUTS_DIR / output_filename
        duration = max(5, min(int(payload.get("duration", 30)), 60))
        debug_path = settings.DATA_DIR / "engine_debug.log"
        debug_path.parent.mkdir(parents=True, exist_ok=True)

        cmd_parts = shlex.split(self.command)
        executable = cmd_parts[0] if cmd_parts else ""
        if not executable or not (Path(executable).exists() or shutil.which(executable)):
            raise RuntimeError(f"Engine-Kommando nicht gefunden: {executable or self.command}")
        cmd_parts += [
            "--type", kind,
            "--output", str(output_path),
            "--duration", str(duration),
        ]

        # Mapping der wichtigsten Felder
        if payload.get("title"):
            cmd_parts.extend(["--title", payload["title"]])
        if payload.get("genre"):
            cmd_parts.extend(["--genre", payload["genre"]])
        if payload.get("mood"):
            cmd_parts.extend(["--mood", payload["mood"]])
        if payload.get("tempo"):
            cmd_parts.extend(["--tempo", str(int(payload["tempo"]))])
        if payload.get("energy"):
            cmd_parts.extend(["--energy", str(int(payload["energy"]))])
        if payload.get("preset_id"):
            cmd_parts.extend(["--preset", payload["preset_id"]])
        if payload.get("lyrics"):
            cmd_parts.extend(["--lyrics", payload["lyrics"][:200]])
        if payload.get("negative_prompts"):
            negatives = ",".join(payload.get("negative_prompts"))
            cmd_parts.extend(["--negative", negatives[:200]])

        cmd_display = " ".join(shlex.quote(p) for p in cmd_parts)

        with open(debug_path, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now().isoformat()} | start | cmd={cmd_display} | payload={payload}\n")

        try:
            proc = await asyncio.to_thread(
                subprocess.run,
                cmd_parts,
                shell=False,
                capture_output=True,
                text=True,
                timeout=settings.ENGINE_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Engine timeout nach {settings.ENGINE_TIMEOUT}s | cmd={cmd_display}")

        stdout_text = (proc.stdout or "").strip()
        stderr_text = (proc.stderr or "").strip()

        debug_entry = (
            f"{datetime.now().isoformat()} | cmd={cmd_display} | rc={proc.returncode}\n"
            f"stdout: {stdout_text}\n"
            f"stderr: {stderr_text}\n\n"
        )
        with open(debug_path, "a", encoding="utf-8") as fh:
            fh.write(debug_entry)

        if proc.returncode != 0:
            err_text = stderr_text or stdout_text or "Unbekannter Fehler"
            snippet = (stdout_text[:200] + "...") if len(stdout_text) > 200 else stdout_text
            raise RuntimeError(f"Engine exit {proc.returncode}: {err_text} | stdout={snippet} | cmd={cmd_display}")

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(f"Engine meldete Erfolg, aber keine Ausgabedatei gefunden | cmd={cmd_display}")

        return str(output_path)
