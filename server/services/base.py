from typing import Generic, TypeVar

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import Base
from services.utils import logger_decorator

T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    """«Data Access Object» (объект доступа к данным)"""

    model: type[T]
    lazy = selectinload

    @classmethod
    @logger_decorator
    async def find_all_lazy(cls, session: AsyncSession, options: list, filters: dict | None = None):
        filters = filters or dict()
        load_options = [cls.lazy(option) for option in options]
        try:
            query = select(cls.model).filter_by(**filters).options(*load_options)
            result = await session.execute(query)
            records = result.scalars().all()
            return records
        except SQLAlchemyError as e:
            raise e

    @classmethod
    @logger_decorator
    async def find_one_or_none_lazy(cls, session: AsyncSession, options: list, filters: dict | None = None):
        filters = filters or dict()
        load_options = [cls.lazy(option) for option in options]
        try:
            query = select(cls.model).filter_by(**filters).options(*load_options)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            return record
        except SQLAlchemyError as e:
            raise e

    @classmethod
    @logger_decorator
    async def find_one_or_none(cls, session: AsyncSession, filters: dict | None = None):
        filters = filters or dict()

        try:
            query = select(cls.model).filter_by(**filters)
            result = await session.execute(query)
            record = result.scalar_one_or_none()
            return record
        except SQLAlchemyError as e:
            raise e

    @classmethod
    @logger_decorator
    async def add(cls, session: AsyncSession, **kwargs):
        try:
            query = insert(cls.model).values(**kwargs).returning(cls.model)
            result = await session.execute(query)
            record = result.scalar_one()
            return record
        except SQLAlchemyError as e:
            raise e

    @classmethod
    @logger_decorator
    async def delete(cls, session: AsyncSession, **kwargs):
        try:
            query = delete(cls.model).returning(cls.model)

            for key, value in kwargs.items():
                column = getattr(cls.model, key)
                query = query.where(column == value)

            result = await session.execute(query)
            record = result.scalar_one()
            return record
        except SQLAlchemyError as e:
            raise e


# class GetUser:
#     user_model = User
#
#     @classmethod
#     async def _get_user_by_id(cls, session: AsyncSession, api_key: str):
#         user = await session.scalar(select(cls.user_model).filter(cls.user_model.api_key == api_key))
#         return user
