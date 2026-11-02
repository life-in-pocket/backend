import fakeredis.aioredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.main import app
from app.dependencies import get_db
from app.database import Base
from app.user.model import User  # noqa: F401  (реєструє таблицю в Base.metadata)
from app.user import routes as user_routes
from app.core import redis as redis_module

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
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(autouse=True)
async def fake_redis(monkeypatch):
    fake = fakeredis.aioredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis_module, "redis_client", fake)
    monkeypatch.setattr(user_routes, "redis_client", fake)
    yield fake
    await fake.flushall()
    await fake.aclose()


async def _fake_send(**kwargs):
    return None


@pytest_asyncio.fixture
async def client(db, monkeypatch):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr("app.user.service.send_email", _fake_send)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()