"""Service factory functions with singleton pattern."""

from functools import lru_cache

from app.common.repo import (
    get_sheet_connection_repo,
    get_sheet_data_repo,
    get_sheet_sync_state_repo,
    get_user_repo,
)
from app.infrastructure.google_sheets.client import GoogleSheetClient
from app.infrastructure.redis.client import RedisClient
from app.infrastructure.redis.redis_queue import RedisQueue
from app.services.auth.auth_service import AuthService
from app.services.business.sheet_crawler.crawler_service import SheetCrawlerService


@lru_cache
def get_redis_queue() -> RedisQueue:
    """Get singleton RedisQueue instance.

    Returns:
        RedisQueue instance with Redis client
    """
    client = RedisClient.get_client()
    return RedisQueue(client)


@lru_cache
def get_auth_service() -> AuthService:
    """Get singleton AuthService instance.

    Returns:
        AuthService instance with UserRepository
    """
    user_repo = get_user_repo()
    return AuthService(user_repo)


@lru_cache
def get_google_sheet_client() -> GoogleSheetClient:
    """Get singleton GoogleSheetClient instance.

    Returns:
        GoogleSheetClient instance for Google Sheets API access
    """
    return GoogleSheetClient()


@lru_cache
def get_crawler_service() -> SheetCrawlerService:
    """Get singleton SheetCrawlerService instance.

    Returns:
        SheetCrawlerService instance with all dependencies
    """
    return SheetCrawlerService(
        sheet_client=get_google_sheet_client(),
        connection_repo=get_sheet_connection_repo(),
        sync_state_repo=get_sheet_sync_state_repo(),
        data_repo=get_sheet_data_repo(),
    )
