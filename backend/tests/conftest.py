import asyncio
import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

# Cross-platform Python executable (works on Windows and Linux/CI)
_PYTHON_EXE = sys.executable

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import settings
from app.database import async_session_factory, close_db

TEST_PREFIX = "pytest-mm-"


async def cleanup_test_artifacts():
    async with async_session_factory() as session:
        await session.execute(
            text("""
                UPDATE projects
                SET last_job_id = NULL
                WHERE name LIKE :prefix
                   OR last_job_id IN (
                       SELECT id FROM jobs WHERE title LIKE :prefix
                   )
                """),
            {"prefix": f"{TEST_PREFIX}%"},
        )
        await session.execute(
            text("DELETE FROM projects WHERE name LIKE :prefix"),
            {"prefix": f"{TEST_PREFIX}%"},
        )
        await session.execute(
            text("DELETE FROM jobs WHERE title LIKE :prefix"),
            {"prefix": f"{TEST_PREFIX}%"},
        )
        await session.commit()

    for pattern in (f"{TEST_PREFIX}*",):
        for path in settings.OUTPUTS_DIR.glob(pattern):
            if path.is_file():
                path.unlink(missing_ok=True)
    for pattern in (f"{TEST_PREFIX}*",):
        for path in settings.EXPORTS_DIR.glob(pattern):
            if path.is_file():
                path.unlink(missing_ok=True)


def cleanup_test_artifacts_sync():
    async def _cleanup():
        await close_db()
        await cleanup_test_artifacts()
        await close_db()

    asyncio.run(_cleanup())


@pytest.fixture()
def server():
    cleanup_test_artifacts_sync()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        test_port = sock.getsockname()[1]
    test_base_url = f"http://127.0.0.1:{test_port}"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_ROOT)
    env["ENGINE_MODE"] = "mock"
    env["ENGINE_MOCK_DELAY"] = "1"
    env["SERVER_PORT"] = str(test_port)

    process = subprocess.Popen(
        [
            _PYTHON_EXE,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(test_port),
        ],
        cwd=str(BACKEND_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + 20
    last_error = None
    while time.time() < deadline:
        try:
            response = httpx.get(f"{test_base_url}/health", timeout=2.0)
            if response.status_code == 200:
                yield {"process": process, "base_url": test_base_url}
                break
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
    else:
        process.terminate()
        cleanup_test_artifacts_sync()
        raise RuntimeError(f"Testserver konnte nicht gestartet werden: {last_error}")

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


@pytest.fixture()
def client(server):
    with httpx.Client(base_url=server["base_url"], timeout=20.0) as http_client:
        yield http_client


@pytest_asyncio.fixture()
async def db_session():
    await cleanup_test_artifacts()
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture()
def test_token():
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
