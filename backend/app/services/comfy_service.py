"""Local ComfyUI startup/reachability helper for ACE mode."""

import asyncio
import os
import shlex
import socket
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from app.config import settings
from app.logging_config import logger

_comfy_state: dict[str, Any] = {
    "url": settings.COMFYUI_URL,
    "reachable": False,
    "autostart_enabled": settings.COMFYUI_AUTOSTART,
    "autostart_attempted": False,
    "autostart_started": False,
    "exe_path": settings.COMFYUI_EXE,
    "server_root": settings.COMFYUI_SERVER_ROOT,
    "server_python": settings.COMFYUI_SERVER_PYTHON,
    "launch_mode": None,
    "launch_command": None,
    "launch_cwd": None,
    "ace_assets": None,
    "last_error": None,
}


def _is_reachable(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=2.0):
            return True
    except OSError:
        return False


def get_comfy_state() -> dict[str, Any]:
    state = dict(_comfy_state)
    state["reachable"] = _is_reachable(settings.COMFYUI_URL)
    state["url"] = settings.COMFYUI_URL
    state["exe_path"] = settings.COMFYUI_EXE
    state["server_root"] = settings.COMFYUI_SERVER_ROOT
    state["server_python"] = settings.COMFYUI_SERVER_PYTHON
    state["autostart_enabled"] = settings.COMFYUI_AUTOSTART
    return state


def _extract_option(command: str, option: str) -> str | None:
    parts = shlex.split(command)
    for idx, part in enumerate(parts):
        if part == option and idx + 1 < len(parts):
            return parts[idx + 1]
    return None


def _parse_host_port(url: str) -> tuple[str, int]:
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return host, port


def _resolve_launch_target() -> tuple[str, list[str], Path]:
    host, port = _parse_host_port(settings.COMFYUI_URL)
    server_root = Path(settings.COMFYUI_SERVER_ROOT).expanduser()
    server_python = Path(settings.COMFYUI_SERVER_PYTHON).expanduser()
    main_py = server_root / "main.py"
    desktop_exe = Path(settings.COMFYUI_EXE).expanduser()

    if server_root.exists() and server_python.exists() and main_py.exists():
        return (
            "embedded-python",
            [
                str(server_python),
                "-s",
                "main.py",
                "--listen",
                host,
                "--port",
                str(port),
                "--windows-standalone-build",
            ],
            server_root,
        )

    if desktop_exe.exists():
        return ("desktop-exe", [str(desktop_exe)], desktop_exe.parent)

    raise FileNotFoundError(
        f"ComfyUI launch target missing: python={server_python} main={main_py} exe={desktop_exe}"
    )


def _create_windows_junction(link_path: Path, target_path: Path) -> None:
    proc = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link_path), str(target_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            proc.stderr.strip()
            or proc.stdout.strip()
            or f"mklink failed: {proc.returncode}"
        )


def _ensure_dir_link(link_path: Path, target_path: Path) -> dict[str, Any]:
    status: dict[str, Any] = {
        "link": str(link_path),
        "target": str(target_path),
        "exists": False,
        "ok": False,
        "action": "missing_target",
    }
    if not target_path.exists():
        return status

    status["exists"] = True
    if link_path.exists():
        try:
            resolved = link_path.resolve()
        except OSError:
            resolved = link_path
        if resolved == target_path.resolve():
            status["ok"] = True
            status["action"] = "already_linked"
            return status
        status["action"] = "occupied"
        return status

    link_path.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        _create_windows_junction(link_path, target_path)
    else:
        os.symlink(str(target_path), str(link_path), target_is_directory=True)
    status["ok"] = True
    status["action"] = "linked"
    return status


def _ensure_ace_assets() -> dict[str, Any] | None:
    workflow_path = _extract_option(settings.ACE_STEP_COMMAND, "--workflow")
    if not workflow_path:
        return None

    workflow = Path(workflow_path).expanduser()
    vendor_root = (
        workflow.parent.parent
        if workflow.parent.name == "workflows"
        else workflow.parent
    )
    custom_target = vendor_root / "custom_nodes" / "ComfyUI_ACE-Step"
    model_target = vendor_root / "models" / "TTS" / "ACE-Step-v1-3.5B"
    server_root = Path(settings.COMFYUI_SERVER_ROOT).expanduser()

    assets = {
        "vendor_root": str(vendor_root),
        "custom_node": _ensure_dir_link(
            server_root / "custom_nodes" / "ComfyUI_ACE-Step", custom_target
        ),
        "model_dir": _ensure_dir_link(
            server_root / "models" / "TTS" / "ACE-Step-v1-3.5B", model_target
        ),
    }
    return assets


def _launch_comfy_process(command: list[str], cwd: Path) -> subprocess.Popen:
    kwargs: dict[str, Any] = {
        "cwd": str(cwd),
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
    }
    if os.name == "nt":
        kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
    return subprocess.Popen(command, **kwargs)


async def ensure_comfy_available() -> dict[str, Any]:
    """Ensure ComfyUI is reachable for ACE mode, optionally autostarting it."""
    _comfy_state.update(
        {
            "url": settings.COMFYUI_URL,
            "exe_path": settings.COMFYUI_EXE,
            "server_root": settings.COMFYUI_SERVER_ROOT,
            "server_python": settings.COMFYUI_SERVER_PYTHON,
            "autostart_enabled": settings.COMFYUI_AUTOSTART,
            "launch_mode": None,
            "launch_command": None,
            "launch_cwd": None,
            "ace_assets": None,
            "last_error": None,
        }
    )

    if _is_reachable(settings.COMFYUI_URL):
        _comfy_state["reachable"] = True
        logger.info("comfy_already_running", url=settings.COMFYUI_URL)
        return get_comfy_state()

    _comfy_state["reachable"] = False
    if not settings.COMFYUI_AUTOSTART:
        _comfy_state["last_error"] = "autostart_disabled"
        logger.warning("comfy_not_running_autostart_disabled", url=settings.COMFYUI_URL)
        return get_comfy_state()

    try:
        launch_mode, command, cwd = _resolve_launch_target()
    except FileNotFoundError as exc:
        _comfy_state["autostart_attempted"] = True
        _comfy_state["last_error"] = str(exc)
        logger.error(
            "comfy_autostart_target_missing",
            exe_path=settings.COMFYUI_EXE,
            server_python=settings.COMFYUI_SERVER_PYTHON,
            server_root=settings.COMFYUI_SERVER_ROOT,
            url=settings.COMFYUI_URL,
        )
        return get_comfy_state()

    _comfy_state["autostart_attempted"] = True
    try:
        _comfy_state["ace_assets"] = _ensure_ace_assets()
    except Exception as exc:
        _comfy_state["ace_assets"] = {"error": str(exc)}
        logger.warning("comfy_ace_assets_prepare_failed", error=str(exc))
    _comfy_state["launch_mode"] = launch_mode
    _comfy_state["launch_command"] = command
    _comfy_state["launch_cwd"] = str(cwd)
    logger.info(
        "comfy_autostart_begin",
        launch_mode=launch_mode,
        command=command,
        cwd=str(cwd),
        url=settings.COMFYUI_URL,
    )

    try:
        proc = await asyncio.to_thread(_launch_comfy_process, command, cwd)
        _comfy_state["autostart_started"] = True
        logger.info(
            "comfy_autostart_spawned",
            pid=proc.pid,
            launch_mode=launch_mode,
            cwd=str(cwd),
        )
    except Exception as exc:
        _comfy_state["last_error"] = str(exc)
        logger.exception(
            "comfy_autostart_spawn_failed",
            launch_mode=launch_mode,
            cwd=str(cwd),
            command=command,
        )
        return get_comfy_state()

    deadline = asyncio.get_running_loop().time() + max(
        5, settings.COMFYUI_START_TIMEOUT
    )
    while asyncio.get_running_loop().time() < deadline:
        if _is_reachable(settings.COMFYUI_URL):
            _comfy_state["reachable"] = True
            _comfy_state["last_error"] = None
            logger.info("comfy_autostart_ready", url=settings.COMFYUI_URL)
            return get_comfy_state()

        if proc.poll() is not None:
            _comfy_state["last_error"] = f"comfy_process_exited:{proc.returncode}"
            logger.error(
                "comfy_autostart_exited_early",
                returncode=proc.returncode,
                launch_mode=launch_mode,
                command=command,
                cwd=str(cwd),
                url=settings.COMFYUI_URL,
            )
            return get_comfy_state()

        await asyncio.sleep(1.0)

    _comfy_state["last_error"] = f"comfy_start_timeout:{settings.COMFYUI_START_TIMEOUT}"
    logger.error(
        "comfy_autostart_timeout",
        launch_mode=launch_mode,
        command=command,
        cwd=str(cwd),
        timeout_seconds=settings.COMFYUI_START_TIMEOUT,
        url=settings.COMFYUI_URL,
    )
    return get_comfy_state()
