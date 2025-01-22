from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Attachment, Follower, Like, Tweet, User
from services.base import BaseDAO
from services.utils import logger_decorator


class UserDAO(BaseDAO[User]):
    model = User


class FollowerDAO(BaseDAO[Follower]):
    model = Follower


class LikeDAO(BaseDAO[User]):
    model = Like


class TweetDAO(BaseDAO[Tweet]):
    model = Tweet


class AttachmentDAO(BaseDAO[User]):
    model = Attachment

    @classmethod
    @logger_decorator
    async def find_attachments_path_by_tweet_id(cls, session: AsyncSession, tweet_ids: List[int]):
        query = select(cls.model.path).where(cls.model.id.in_(tweet_ids))
        result = await session.execute(query)
        records = (result.scalars().all(),)
        return records
