from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class Base(BaseModel):
    created_at: datetime
    updated_at: datetime


# -------------------------------------USER--------------------------------------- #
class BaseUser(Base):
    id: int
    name: str = Field(max_length=50)
    api_key: str = Field(max_length=255)

    Config: ConfigDict = {"orm_model": True}

    # class Config:
    #     orm_model = True


class UserPydantic(BaseModel):
    id: int
    name: str


# -------------------------------------Like--------------------------------------- #
class LikeBase(Base):
    id: int
    user_id: int
    tweet_id: int

    Config: ConfigDict = {"orm_model": True}

    # class Config:
    #     orm_model = True


# -------------------------------------Follower--------------------------------------- #
class FollowerBase(Base):
    id: int
    user_id: int
    followed_user_id: int

    Config: ConfigDict = {"orm_model": True}

    # class Config:
    #     orm_model = True


# -------------------------------------TWEET--------------------------------------- #
class BaseTweet(Base):
    # model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    user_id: int
    attachments: List[int] | None

    # class Config:
    #     orm_model = True
    #     from_attributes = True

    Config: ConfigDict = {"orm_model": True, "from_attributes": True}


class TweetPayloadIn(BaseModel):
    content: str = Field(..., alias="tweet_data")
    # attachments: Optional[List[int]] = Field(default=[], alias="tweet_media_ids")
    attachments: Union[List[int], List] = Field(None, alias="tweet_media_ids")


class TweetPayloadOut(BaseModel):
    content: str
    attachments: Optional[List[int]] = Field(default=None)


# -------------------------------------ATTACHMENT--------------------------------------- #
class AttachmentBase(Base):
    id: int
    path: str

    # class Config:
    #     orm_model = True
    Config: ConfigDict = {"orm_model": True}


# -------------------------------------RESPONSE--------------------------------------- #
class LikeShort(BaseModel):
    user_id: int
    name: str


class BaseShort(BaseModel):
    id: int
    name: str


class TweetFull(BaseModel):
    id: int
    content: str
    attachments: Union[List[str], List] = Field(default=[])
    author: BaseShort
    likes: Union[List[LikeShort], List] = Field(default=[])


class UserFull(BaseModel):
    id: int
    name: str
    following: Union[List[LikeShort], List] = Field(default=[])
    followers: Union[List[LikeShort], List] = Field(default=[])


class BaseResponse(BaseModel):
    result: bool


class ErrorResponse(BaseResponse):
    error_type: str
    error_message: str


class TweetGetResponse(BaseResponse):
    tweets: Union[List[TweetFull], List] = Field(default=[])


class TweetPostResponse(BaseResponse):
    tweet_id: int


class UserGetResponse(BaseResponse):
    user: UserFull


class MediaPostResponse(BaseResponse):
    media_id: int
