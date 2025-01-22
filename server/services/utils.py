import os
import uuid
from functools import wraps
from pathlib import Path

from aiofile import async_open
from fastapi.exceptions import HTTPException

# from server.
from logger_config import get_logger
from models import User

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_DIR = BASE_DIR / os.getenv("MEDIA_DIR")

logger = get_logger("app_logger.services")


def logger_decorator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        logger.debug(f"Calling function '{func.__name__}' with args={args}, kwargs={kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Function '{func.__name__}' finished successfully")
            return result
        except Exception as exc:
            logger.error(f"Function '{func.__name__}' failed with {type(exc)}: {str(exc)}")
            raise exc

    return wrapper


class FileHandleService:
    def __init__(self, content: bytes, filename: str):
        self.content = content
        self.filename = filename

    async def save(self):
        """Save file to MEDIA_DIR"""
        unique_filename = self._gen_unique_filename()
        out_file_path = str(MEDIA_DIR / unique_filename)
        logger.error(f"{out_file_path}")
        await self._write_file(self.content, out_file_path, unique_filename)
        return unique_filename, out_file_path

    async def delete(self, filepath: str):
        """Delete file if tweet is deleted for optimal memory consumption"""
        file_path = Path(filepath)
        if file_path.exists():
            file_path.unlink()

    async def _write_file(self, content: bytes, filepath, unique_filename):
        try:
            async with async_open(filepath, "wb") as out_file:
                logger.debug(f"Uploading {self.filename}")
                await out_file.write(content)
                logger.debug(f"The file uploaded as {unique_filename}")
        except Exception as exc:
            raise HTTPException(
                status_code=500, detail=dict(result=False, error=f"{exc.__class__.__name__}: {str(exc)}")
            )

    def _gen_unique_filename(self):
        return f"{uuid.uuid4()}_{self.filename}"


def get_user_response_data(user: User):
    response = {"result": "true", "user": {"id": user.id, "name": user.name}}

    followers = [{"id": user_follower.id, "name": user_follower.name} for user_follower in user.followers] or None
    following = [{"id": followed_user.id, "name": followed_user.name} for followed_user in user.following] or None

    if followers:
        response["user"]["followers"] = followers

    if following:
        response["user"]["following"] = following

    return response
