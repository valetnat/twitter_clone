import os
import sys
from typing import AsyncGenerator


import pytest_asyncio
from fastapi.exceptions import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)

from database import Base, get_session
from models import User

from ..logger_config import get_logger
from ..main import app as _app


logger = get_logger("app_logger")

test_db_url = os.getenv("DATABASE_TEST_URL")

engine = create_async_engine(test_db_url, isolation_level="READ COMMITTED", echo=False)
AsyncSession = async_sessionmaker(engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_database():
    """
    Setup and tears down the test database data for every single tests (due to scope function)
    It is assumed that the test database already exists.
    """
    async with engine.begin() as conn:
        # Startup logic: Drop and create all tables at startup
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession() as session:
        async with session.begin():
            session.add_all(
                [
                    User(name="test", api_key="test"),
                    User(name="David", api_key="david"),
                    User(name="Patric", api_key="patric"),
                    User(name="Christian", api_key="christian"),
                ]
            )

    yield  # Run the tests

    async with engine.begin() as conn:
        # Drop all tables after tests
        await conn.run_sync(Base.metadata.drop_all)
        # pass

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Provides a clean database session for each test.
    """

    async with AsyncSession() as session:
        async with session.begin():
            try:
                yield session
                await session.commit()
            except Exception as exc:
                await session.rollback()
                raise HTTPException(
                    status_code=500,
                    detail=dict(result=False, error_type=f"{exc.__class__.__name__}", error_message=f"{str(exc)}"),
                )
            finally:
                await session.close()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Provides an async HTTP client for testing the FastAPI app.
    Overrides the app's session dependency with the test session.
    """

    # Dependency override for the session
    async def override_get_session():
        yield db_session

    _app.dependency_overrides[get_session] = override_get_session

    # Create the async client
    async with AsyncClient(transport=ASGITransport(app=_app), base_url="http://test") as ac:
        yield ac

    _app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client_with_api_header(async_client: AsyncSession, db_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Fixture that returns a TestClient with api-user headers.
    """

    headers = {"Api-Key": "test"}
    # Modify the client to automatically include the headers in each request
    async_client.headers.update(headers)

    yield async_client

    async_client.headers.clear()
