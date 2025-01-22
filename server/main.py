import logging.config
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Optional, Union

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Security,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import delete

from database import AsyncSession, engine, get_session
from logger_config import dict_config, get_logger
from models import Tweet, User
from schemas import (
    BaseResponse,
    ErrorResponse,
    MediaPostResponse,
    TweetFull,
    TweetGetResponse,
    TweetPayloadIn,
    TweetPostResponse,
    UserGetResponse,
)
from services.service import AttachmentDAO, FollowerDAO, LikeDAO, TweetDAO, UserDAO
from services.utils import FileHandleService, get_user_response_data


logging.config.dictConfig(dict_config)
logger = get_logger("app_logger")

api_key_header = APIKeyHeader(name="Api-Key", auto_error=False)


# Dependency to get current user based on API Key
async def get_current_user(
    api_key: Optional[str] = Security(api_key_header), session: AsyncSession = Depends(get_session)
) -> User:
    if not api_key:
        logger.warning("Missing Api-Key in request headers.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API Key")

    user = await UserDAO.find_one_or_none_lazy(
        session=session,
        filters={"api_key": api_key},
        options=[User.following, User.followers, User.liked_tweets, User.tweets],
    )

    if not user:
        logger.warning("Unauthorized access attempt with invalid Api-Key.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API Key")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / os.getenv("MEDIA_DIR")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning("Start up")

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

    yield
    async with AsyncSession() as session:
        async with session.begin():
            await session.execute(delete(User))
    await engine.dispose()


app = FastAPI(lifespan=lifespan, debug=False)


@app.middleware("http")
async def add_headers_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    logger.info(
        f"{request.method} {request.url.path} completed in {process_time:.4f}s with status {response.status_code}"
    )
    return response


@app.get(
    "/api/users/me",
    response_model=UserGetResponse,
    responses={
        500: {"model": ErrorResponse}
    },
    summary="Retrieve a user's information by user ID.",
)
async def get_auth_user(request: Request, cur_user: CurrentUserDep):
    logger.info(f"Function <{get_auth_user.__name__}> gets Api-Key: {request.headers.get('Api-key')}")

    response = get_user_response_data(cur_user)

    logger.info(f"Function <{get_auth_user.__name__}> return: {response}")
    return UserGetResponse(**response)


@app.get("/api/users/{user_id}", responses={200: {"model": UserGetResponse}, 500: {"model": ErrorResponse}})
async def get_user(user_id: int, session: SessionDep):
    user = await UserDAO.find_one_or_none_lazy(
        session=session,
        filters={"id": user_id},
        options=[User.following, User.followers, User.liked_tweets, User.tweets],
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    response = get_user_response_data(user)
    return UserGetResponse(**response)


@app.delete(
    "/api/users/{user_id}/follow",
    responses={201: {"model": BaseResponse}, 500: {"model": ErrorResponse}},
    summary="Follow a user by user ID.",
)
@app.post(
    "/api/users/{user_id}/follow",
    responses={201: {"model": BaseResponse}, 500: {"model": ErrorResponse}},
    summary="Unfollow a user by user ID.",
)
async def follow(user_id: int, session: SessionDep, cur_user: CurrentUserDep, request: Request):
    if request.method == "DELETE":
        await FollowerDAO.delete(session=session, user_id=cur_user.id, followed_user_id=user_id)
        return JSONResponse({"result": True}, status_code=200)

    await FollowerDAO.add(session=session, user_id=cur_user.id, followed_user_id=user_id)
    return JSONResponse({"result": True}, 201)


@app.get("/api/tweets", responses={200: {"model": TweetGetResponse}, 500: {"model": ErrorResponse}})
async def get_all_tweets(session: SessionDep):
    response = {"result": True}

    tweets = await TweetDAO.find_all_lazy(session=session, options=[Tweet.user, Tweet.liked_by])
    for tweet in tweets:
        response.setdefault("tweets", [])
        tweet_dict = {
            "id": tweet.id,
            "content": tweet.content,
            "author": {"id": tweet.user_id, "name": tweet.user.name},
        }
        likes = []
        for user_like in tweet.liked_by:
            user = await UserDAO.find_one_or_none_lazy(session=session, filters={"id": user_like.user_id}, options=[])
            likes.append({"user_id": user_like.user_id, "name": user.name})
        if len(likes) > 0:
            tweet_dict["likes"] = likes

        if tweet.attachments:
            paths = await AttachmentDAO.find_attachments_path_by_tweet_id(session, tweet_ids=tweet.attachments)
            tweet_dict["attachments"] = [path for path in paths[0]]

        response["tweets"].append(TweetFull(**tweet_dict))

    return JSONResponse(TweetGetResponse(**response).model_dump(), status_code=200)


@app.post("/api/tweets", responses={201: {"model": TweetPostResponse}, 500: {"model": ErrorResponse}})
async def add_tweet(
    payload: TweetPayloadIn, request: Request, session: SessionDep, cur_user: CurrentUserDep
) -> JSONResponse:
    logger.info(f"Function <{get_auth_user.__name__}> gets Api-Key: {request.headers.get('Api-key')}")

    payload = payload.model_dump()
    if not payload["attachments"]:
        payload.pop("attachments")
    new_tweet = await TweetDAO.add(session, user_id=cur_user.id, **payload)

    return JSONResponse({"result": "true", "tweet_id": new_tweet.id}, 201)


@app.post(
    "/api/medias",
    responses={201: {"model": MediaPostResponse}, 500: {"model": ErrorResponse}},
    description=f"Save attached tweet file into path=:{MEDIA_DIR}",
)
async def create_media_file(session: SessionDep, file: Union[UploadFile, None] = None) -> JSONResponse:
    """
    Save a media file from user twit
    """
    if file:
        logger.info(f"Function <{create_media_file.__name__}> gets {file}")
        content = await file.read()
        fileservice = FileHandleService(content=content, filename=file.filename)
        unique_filename, out_file_path = await fileservice.save()

        try:
            new_attachment = await AttachmentDAO.add(session, path=str(out_file_path))

            logger.info(
                f"Function <{create_media_file.__name__}> return:"
                + str({"result": "true", "media_id": new_attachment.id})
            )
            return JSONResponse({"result": "true", "media_id": new_attachment.id}, 201)

        except SQLAlchemyError:
            await fileservice.delete(filepath=out_file_path)
            logger.debug(f"The file {unique_filename} was deleted due to error on the db side")
            raise


@app.delete("/api/tweets/{tweet_id}", responses={200: {"model": BaseResponse}, 500: {"model": ErrorResponse}})
async def del_tweet(tweet_id: int, session: SessionDep, cur_user: CurrentUserDep, request: Request):
    logger.info(
        f"Function <{del_tweet.__name__}> gets: api-Key: {request.headers.get('Api-key')}, tweet_id: {tweet_id}"
    )

    await TweetDAO.delete(session, id=tweet_id, user_id=cur_user.id)

    return JSONResponse({"result": True}, status_code=200)


@app.delete("/api/tweets/{tweet_id}/likes", responses={200: {"model": BaseResponse}, 500: {"model": ErrorResponse}})
@app.post("/api/tweets/{tweet_id}/likes", responses={201: {"model": BaseResponse}, 500: {"model": ErrorResponse}})
async def like(tweet_id: int, session: SessionDep, cur_user: CurrentUserDep, request: Request) -> JSONResponse:
    if request.method == "DELETE":
        await LikeDAO.delete(session, tweet_id=tweet_id, user_id=cur_user.id)
        return JSONResponse({"result": True}, status_code=200)

    await LikeDAO.add(session, tweet_id=tweet_id, user_id=cur_user.id)

    return JSONResponse({"result": True}, 201)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)
