"""
Pytest configuration — provides isolated async DB fixtures.
"""
import os
import sys
import pytest
import pytest_asyncio
from pathlib import Path

# Ensure backend is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Configure test environment before any tests run."""
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_nyayasetu.db"
    os.environ["UPLOAD_DIR"] = "./test_uploads"
    yield
    # Cleanup DB and uploads after full session
    import shutil
    for path in ["./test_nyayasetu.db", "./test_uploads"]:
        p = Path(path)
        if p.is_dir():
            shutil.rmtree(str(p))
        elif p.exists():
            p.unlink()


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    """
    Reset the test database before each test to ensure isolation.
    Drops and recreates all tables.
    """
    from database import Base, engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
