import pytest
from httpx import AsyncClient
from sqlalchemy import insert, select

from models import Attachment, Follower, Like, Tweet, User

from ..logger_config import get_logger

logger = get_logger("app_logger")


@pytest.mark.asyncio
async def test_get_users_me(async_client_with_api_header: AsyncClient):
    # response = await async_client.get("/api/users/me", headers={"Api-key": "test"})
    response = await async_client_with_api_header.get("/api/users/me")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_users_count(async_client_with_api_header: AsyncClient, db_session):
    responce = await db_session.execute(select(User))

    assert len(responce.scalars().all()) == 4


@pytest.mark.asyncio
async def test_get_all_tweets(async_client_with_api_header: AsyncClient):
    # response = await async_client.get("/api/users/me", headers={"Api-key": "test"})
    response = await async_client_with_api_header.get("/api/tweets")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_all_tweets_db(db_session, async_client_with_api_header: AsyncClient):
    responce = await db_session.execute(select(Tweet))
    assert len(responce.scalars().all()) == 0


@pytest.mark.asyncio
async def test_create_tweet(async_client_with_api_header: AsyncClient, db_session):
    response = await async_client_with_api_header.post(
        "/api/tweets", json={"tweet_data": "This is a new tweet!", "tweet_media_ids": []}
    )
    assert response.status_code == 201
    assert '"result":"true"' in response.text

    # Verify the tweet is created in the database
    tweets_in_db = await db_session.execute(select(Tweet).filter(Tweet.content == "This is a new tweet!"))
    assert tweets_in_db.scalars().first() is not None


@pytest.mark.asyncio
async def test_get_users_me_success(async_client_with_api_header: AsyncClient):
    response = await async_client_with_api_header.get("/api/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is True
    assert "user" in data
    assert data["user"]["name"] == "test"


@pytest.mark.asyncio
async def test_get_users_me_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/api/users/me")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Missing API Key"


@pytest.mark.asyncio
async def test_get_user_by_id_success(async_client_with_api_header: AsyncClient, db_session):
    response = await async_client_with_api_header.get("/api/users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is True
    assert "user" in data
    assert data["user"]["id"] == 1
    assert data["user"]["name"] == "test"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(async_client_with_api_header: AsyncClient):
    response = await async_client_with_api_header.get("/api/users/9999")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "User not found"


@pytest.mark.asyncio
async def test_follow_user_success(async_client_with_api_header: AsyncClient, db_session):
    # User 'test' (ID 1) follows User 'David' (ID 2)
    response = await async_client_with_api_header.post("/api/users/2/follow")
    assert response.status_code == 201
    data = response.json()
    assert data["result"] is True
    # Verify the follower relationship
    follower = await db_session.execute(select(Follower).where(Follower.user_id == 1, Follower.followed_user_id == 2))
    assert follower.scalars().first() is not None


# @pytest.mark.asyncio
# async def test_follow_user_self_follow(async_client_with_api_header: AsyncClient):
#     response = await async_client_with_api_header.post("/api/users/1/follow")
#     # assert response.status_code == 400
#     data = response.json()
#     assert data["result"] is False


# @pytest.mark.asyncio
# async def test_follow_user_not_found(async_client_with_api_header: AsyncClient):
#     response = await async_client_with_api_header.post("/api/users/9999/follow")
#     # assert response.status_code == 404
#     data = response.json()
#     logger.error(response)
#     # assert data["result"] is False
#     # assert data["error_type"] == "HTTPException"
#     # assert data["error_message"] == "User to follow not found"


@pytest.mark.asyncio
async def test_unfollow_user_success(async_client_with_api_header: AsyncClient, db_session):
    # User 1 is following User 2
    await db_session.execute(insert(Follower).values(user_id=1, followed_user_id=2))

    # Unfollow
    response = await async_client_with_api_header.delete("/api/users/2/follow")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is True

    # Verify the follower relationship is removed
    follower = await db_session.execute(select(Follower).where(Follower.user_id == 1, Follower.followed_user_id == 2))
    assert follower.scalars().first() is None


# @pytest.mark.asyncio
# async def test_unfollow_user_not_following(async_client_with_api_header: AsyncClient, db_session):
#     response = await async_client_with_api_header.delete("/api/users/3/follow")
#     # Depending on DAO implementation, it might return 200 even if not following
#     # Adjust the assertion based on actual behavior
#     # assert response.status_code == 200
#     data = response.json()
#     assert data["result"] is True


@pytest.mark.asyncio
async def test_get_all_tweets_empty(async_client_with_api_header: AsyncClient, db_session):
    # Ensure no tweets exist
    response = await async_client_with_api_header.get("/api/tweets")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is True
    assert "tweets" in data
    assert len(data["tweets"]) == 0


@pytest.mark.asyncio
async def test_get_all_tweets_with_data(async_client_with_api_header: AsyncClient, db_session):
    # Create a tweet
    result = await db_session.execute(insert(Tweet).values(content="Hello World!", user_id=1).returning(Tweet))
    new_tweet = result.scalar_one()
    # Create a like
    await db_session.execute(insert(Like).values(user_id=2, tweet_id=new_tweet.id).returning(Like))

    # Create an attachment
    new_attachment = Attachment(path="/media/image1.png")
    result = await db_session.execute(insert(Attachment).values(path="/media/image1.png").returning(Attachment))
    new_attachment = result.scalar_one()
    new_tweet.attachments = [new_attachment.id]

    response = await async_client_with_api_header.get("/api/tweets")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is True
    assert "tweets" in data
    assert len(data["tweets"]) == 1
    tweet = data["tweets"][0]
    assert tweet["id"] == new_tweet.id
    assert tweet["content"] == "Hello World!"
    assert tweet["author"]["id"] == 1
    assert tweet["author"]["name"] == "test"
    assert len(tweet["likes"]) == 1
    assert tweet["likes"][0]["user_id"] == 2
    assert tweet["likes"][0]["name"] == "David"
    assert len(tweet["attachments"]) == 1
    assert tweet["attachments"][0] == "/media/image1.png"


@pytest.mark.asyncio
async def test_create_tweet_success(async_client_with_api_header: AsyncClient, db_session):
    payload = {"tweet_data": "This is a new tweet!", "tweet_media_ids": []}
    response = await async_client_with_api_header.post("/api/tweets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["tweet_id"] is not None

    # Verify the tweet is created in the database
    tweet = await db_session.execute(select(Tweet).where(Tweet.id == data["tweet_id"]))
    tweet = tweet.scalars().first()
    assert tweet is not None
    assert tweet.content == "This is a new tweet!"
    assert tweet.user_id == 1


@pytest.mark.asyncio
async def test_create_tweet_with_attachments(async_client_with_api_header: AsyncClient, db_session):
    # Create a media attachment

    result = await db_session.execute(insert(Attachment).values(path="/media/test_image.png").returning(Attachment))
    new_attachment = result.scalar_one()

    payload = {"tweet_data": "Tweet with attachment", "tweet_media_ids": [new_attachment.id]}
    response = await async_client_with_api_header.post("/api/tweets", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["tweet_id"] is not None

    # Verify the tweet and attachment association
    tweet = await db_session.execute(select(Tweet).where(Tweet.id == data["tweet_id"]))
    tweet = tweet.scalars().first()
    assert tweet is not None
    assert tweet.content == "Tweet with attachment"
    assert tweet.attachments == [new_attachment.id]


@pytest.mark.asyncio
async def test_create_tweet_unauthorized(async_client: AsyncClient):
    payload = {"tweet_data": "Unauthorized tweet", "tweet_media_ids": []}
    response = await async_client.post("/api/tweets", json=payload)
    data = response.json()
    assert data["detail"] == "Missing API Key"


@pytest.mark.asyncio
async def test_create_tweet_invalid_payload(async_client_with_api_header: AsyncClient):
    payload = {"tweet_media_ids": []}  # Missing 'tweet_data'
    response = await async_client_with_api_header.post("/api/tweets", json=payload)
    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_delete_tweet_success(async_client_with_api_header: AsyncClient, db_session):
    # Create a tweet to delete
    result = await db_session.execute(insert(Tweet).values(content="Tweet to delete", user_id=1).returning(Tweet))
    new_tweet = result.scalar_one()

    response = await async_client_with_api_header.delete(f"/api/tweets/{new_tweet.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is True

    # Verify the tweet is deleted
    tweet = await db_session.execute(select(Tweet).where(Tweet.id == new_tweet.id))
    assert tweet.scalars().first() is None


# @pytest.mark.asyncio
# async def test_delete_tweet_not_found(async_client_with_api_header: AsyncClient):
#     response = await async_client_with_api_header.delete("/api/tweets/9999")
#     assert response.status_code == 404
#     data = response.json()
#     assert data["result"] is False
#     assert data["error_type"] == "HTTPException"
#     assert data["error_message"] == "Tweet not found or not authorized to delete"


# @pytest.mark.asyncio
# async def test_delete_tweet_unauthorized(async_client_with_api_header: AsyncClient, db_session):
#     # Create a tweet owned by another user
#     result = await db_session.execute(insert(User).values(name="other", api_key="otherkey").returning(Tweet))
#     other_user = result.scalar_one()
#
#     result = await db_session.execute(insert(Tweet).values(content="Other User tweet",
#     user_id=other_user.id).returning(Tweet))
#     tweet = result.scalar_one()
#
#     response = await async_client_with_api_header.delete(f"/api/tweets/{str(tweet.id)}")
#     assert response.status_code == 404
#     data = response.json()
#     assert data["result"] is False
#     assert data["error_type"] == "HTTPException"
#     assert data["error_message"] == "Tweet not found or not authorized to delete"


@pytest.mark.asyncio
async def test_like_tweet_success(async_client_with_api_header: AsyncClient, db_session):
    # Create a tweet to like
    result = await db_session.execute(insert(Tweet).values(content="Tweet to like", user_id=1).returning(Tweet))
    tweet = result.scalar_one()

    response = await async_client_with_api_header.post(f"/api/tweets/{tweet.id}/likes")
    assert response.status_code == 201
    data = response.json()
    assert data["result"] is True

    # Verify the like in the database
    like = await db_session.execute(select(Like).where(Like.tweet_id == tweet.id, Like.user_id == 1))
    assert like.scalars().first() is not None


# @pytest.mark.asyncio
# async def test_like_tweet_already_liked(async_client_with_api_header: AsyncClient, db_session):
#     # Create a tweet to like
#     result = await db_session.execute(insert(Tweet).values(content="Tweet to like", user_id=1).returning(Tweet))
#     tweet = result.scalar_one()
#
#     # Add a like
#     result = await db_session.execute(insert(Like).values(user_id=1, tweet_id=tweet.id).returning(Like))
#     like = result.scalar_one()
#
#     # Attempt to like again (assuming UniqueConstraint prevents duplicates)
#     response = await async_client_with_api_header.post(f"/api/tweets/{tweet.id}/likes")
#     assert response.status_code == 500  # Or appropriate status based on DAO implementation


# @pytest.mark.asyncio
# async def test_like_tweet_not_found(async_client_with_api_header: AsyncClient):
#     response = await async_client_with_api_header.post("/api/tweets/9999/likes")
#     assert response.status_code == 404
#     data = response.json()
#     assert data["result"] is False
#     assert data["error_type"] == "HTTPException"
#     assert data["error_message"] == "Tweet not found"


@pytest.mark.asyncio
async def test_unlike_tweet_success(async_client_with_api_header: AsyncClient, db_session):
    # Create a tweet and like it
    result = await db_session.execute(insert(Tweet).values(content="Tweet to unlike", user_id=1).returning(Tweet))
    tweet = result.scalar_one()

    result = await db_session.execute(insert(Like).values(user_id=1, tweet_id=tweet.id).returning(Like))
    like = result.scalar_one()

    # Unlike the tweet
    response = await async_client_with_api_header.delete(f"/api/tweets/{tweet.id}/likes")
    assert response.status_code == 200
    data = response.json()
    assert data["result"] is True

    # Verify the like is removed
    like = await db_session.execute(select(Like).where(Like.tweet_id == tweet.id, Like.user_id == 1))
    assert like.scalars().first() is None


# @pytest.mark.asyncio
# async def test_unlike_tweet_not_liked(async_client_with_api_header: AsyncClient, db_session):
#     # Create a tweet
#     tweet = Tweet(content="Tweet not liked yet", user_id=1)
#     db_session.add(tweet)
#     await db_session.commit()
#
#     # Attempt to unlike without a prior like
#     response = await async_client_with_api_header.delete(f"/api/tweets/{tweet.id}/likes")
#     # Depending on DAO implementation, it might return 200 even if not liked
#     assert response.status_code == 200
#     data = response.json()
#     assert data["result"] is True


# @pytest.mark.asyncio
# async def test_unlike_tweet_not_found(async_client_with_api_header: AsyncClient):
#     response = await async_client_with_api_header.delete("/api/tweets/9999/likes")
#     assert response.status_code == 404
#     data = response.json()
#     assert data["result"] is False
#     assert data["error_type"] == "HTTPException"
#     assert data["error_message"] == "Tweet not found"
