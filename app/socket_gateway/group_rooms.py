"""Helpers for managing Socket.IO group room memberships."""

from app.infrastructure.database.mongodb import MongoDB
from app.repo.group_member_repo import GroupMemberRepository


def _get_group_member_repo() -> GroupMemberRepository:
    return GroupMemberRepository(MongoDB.get_db())


def _get_sio():
    from app.socket_gateway.server import sio

    return sio


async def join_groups_for_sid(user_id: str, sid: str) -> None:
    """Join a single socket connection to all active group rooms for a user."""
    repo = _get_group_member_repo()
    sio = _get_sio()
    group_ids = await repo.list_active_group_ids_for_user(
        user_id=user_id,
        skip=0,
        limit=None,
    )
    for group_id in group_ids:
        await sio.enter_room(sid, f"group:{group_id}")


def get_user_sids(user_id: str) -> list[str]:
    """Return all active socket IDs for a user (single-instance only)."""
    sio = _get_sio()
    participants = sio.manager.get_participants("/", f"user:{user_id}")
    return list(participants)


async def join_user_to_group_room(user_id: str, group_id: str) -> None:
    """Join all active sockets of a user to a group room."""
    sio = _get_sio()
    for sid in get_user_sids(user_id):
        await sio.enter_room(sid, f"group:{group_id}")


async def remove_user_from_group_room(user_id: str, group_id: str) -> None:
    """Remove all active sockets of a user from a group room."""
    sio = _get_sio()
    for sid in get_user_sids(user_id):
        await sio.leave_room(sid, f"group:{group_id}")
