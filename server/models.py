from typing import List

from sqlalchemy import (
    VARCHAR,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Sequence,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Like(Base):
    id: Mapped[int] = mapped_column(Sequence("like_id_seq"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweet.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="liked_tweets")
    tweet: Mapped["Tweet"] = relationship(back_populates="liked_by")

    __table_args__ = (UniqueConstraint("user_id", "tweet_id", name=None),)


class Follower(Base):
    # https://docs.sqlalchemy.org/en/20/orm/join_conditions.html#self-referential-many-to-many-relationship
    id: Mapped[int] = mapped_column(Sequence("follower_id_seq"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    followed_user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    followed_user: Mapped["User"] = relationship("User", foreign_keys=[followed_user_id])

    __table_args__ = (
        UniqueConstraint("user_id", "followed_user_id", name=None),
        CheckConstraint("user_id != followed_user_id", name="check_user_not_follow_self"),
    )


class User(Base):
    id: Mapped[int] = mapped_column(Sequence("user_id_seq"), primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(50), nullable=False)
    api_key: Mapped[str] = mapped_column(VARCHAR(255), nullable=False, unique=True)
    # One-to-many relationship: one User to many Tweets
    tweets: Mapped[List["Tweet"]] = relationship(back_populates="user", cascade="all, delete")
    # Many-to-many relationship
    liked_tweets: Mapped[List["Like"]] = relationship(back_populates="user", cascade="all, delete")

    # Self-referential-many-to-many-relationship see link at table Follower
    following: Mapped[List["User"]] = relationship(
        "User",
        secondary="follower",
        primaryjoin=id == Follower.user_id,
        secondaryjoin=id == Follower.followed_user_id,
        back_populates="followers",
        viewonly=True,
        cascade="all, delete",
    )

    followers: Mapped[List["User"]] = relationship(
        "User",
        secondary="follower",
        primaryjoin=id == Follower.followed_user_id,
        secondaryjoin=id == Follower.user_id,
        back_populates="following",
        viewonly=True,
        cascade="all, delete",
    )

    __table_args__ = (
        Index(None, "id"),
        Index(None, "api_key"),
    )


class Tweet(Base):
    id: Mapped[int] = mapped_column(Sequence("tweet_id_seq"), primary_key=True)
    content: Mapped[str] = mapped_column(String, nullable=False)
    # One to many relationship means that parent(User) can have many child(Tweet)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    attachments = mapped_column(ARRAY(Integer), nullable=True)
    # Many-to-one relationship: each Tweet has one User
    user: Mapped["User"] = relationship(back_populates="tweets")
    # Many-to-many relationship
    liked_by: Mapped[List["Like"]] = relationship(back_populates="tweet", cascade="all, delete")

    __table_args__ = (Index("gix_tweet_content_ru", text("to_tsvector('russian', content)"), postgresql_using="gin"),)


class Attachment(Base):
    id: Mapped[int] = mapped_column(Sequence("attachment_id_seq"), primary_key=True)
    path: Mapped[str]

    __table_args__ = (Index(None, "id"),)
