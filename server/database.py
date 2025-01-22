import os
from datetime import datetime

from fastapi.exceptions import HTTPException
from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

from logger_config import get_logger

logger = get_logger("app_logger")

db_url = os.getenv("DATABASE_URL")
# print(db_url)
# db_url = "postgresql+asyncpg://admin:admin@db:5432/twitter"
engine = create_async_engine(db_url, isolation_level="READ COMMITTED", echo=True)

AsyncSession = async_sessionmaker(engine, expire_on_commit=False)


# https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession
class Base(AsyncAttrs, DeclarativeBase):
    # https://docs.sqlalchemy.org/en/20/core/constraints.html#configuring-constraint-naming-conventions
    # https://alembic.sqlalchemy.org/en/latest/naming.html#the-importance-of-naming-constraints
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )

    # Base: абстрактный класс, от которого наследуются все модели.
    # Он используется для миграций и аккумулирует информацию обо всех моделях,
    # чтобы Alembic мог создавать миграции для синхронизации структуры базы данных с моделями на бэкенде.
    __abstract__ = True

    # @declared_attr.directive: определяет имя таблицы для модели на основе имени класса,
    # преобразуя его в нижний регистр
    # (например, класс User будет иметь таблицу user).
    # https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.declared_attr
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}"

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    def to_json(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def __repr__(self):
        return str(self)


async def get_session():
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
