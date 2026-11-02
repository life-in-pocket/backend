import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.dependencies import get_db
from app.database import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db(engine):
    sesion_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with sesion_maker() as session:
        yield session

@pytest_asyncio.fixture
async def client(db, monkeypatch):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.user.service.send_email", _fake_send)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:        yield ac

    app.dependency_overrides.clear()

async def _fake_send(**kwargs):
    return None


