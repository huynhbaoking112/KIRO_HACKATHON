"""Group service for admin-managed group chat operations."""

from app.common.event_socket import GroupChatEvents
from app.common.exceptions import NotFoundError
from app.domain.models.group import Group
from app.domain.models.group_member import GroupMember
from app.repo.group_member_repo import GroupMemberRepository
from app.repo.group_repo import GroupRepository
from app.socket_gateway import gateway
from app.socket_gateway.group_rooms import (
    join_user_to_group_room,
    remove_user_from_group_room,
)


class GroupService:
    """Service for managing groups and memberships."""

    def __init__(
        self,
        group_repo: GroupRepository,
        group_member_repo: GroupMemberRepository,
    ):
        """Initialize GroupService with repositories.

        Args:
            group_repo: Repository for group operations
            group_member_repo: Repository for membership operations
        """
        self.group_repo = group_repo
        self.group_member_repo = group_member_repo

    async def create_group(self, admin_id: str, name: str) -> Group:
        """Create a new group and auto-add creator as member."""
        group = await self.group_repo.create(name=name, created_by_admin_id=admin_id)
        member = await self.group_member_repo.upsert_active_member(
            group_id=group.id,
            user_id=admin_id,
            admin_id=admin_id,
        )
        await join_user_to_group_room(user_id=admin_id, group_id=group.id)
        await gateway.emit_to_user(
            user_id=admin_id,
            event=GroupChatEvents.MEMBER_ADDED,
            data={
                "group_id": group.id,
                "added_at": member.joined_at.isoformat(),
            },
        )
        return group

    async def add_member(
        self, admin_id: str, group_id: str, user_id: str
    ) -> GroupMember:
        """Add a user to a group (idempotent)."""
        group = await self.group_repo.get_by_id(group_id)
        if group is None:
            raise NotFoundError()
        member = await self.group_member_repo.upsert_active_member(
            group_id=group_id,
            user_id=user_id,
            admin_id=admin_id,
        )
        await join_user_to_group_room(user_id=user_id, group_id=group_id)
        await gateway.emit_to_user(
            user_id=user_id,
            event=GroupChatEvents.MEMBER_ADDED,
            data={
                "group_id": group_id,
                "added_at": member.joined_at.isoformat(),
            },
        )
        return member

    async def remove_member(
        self, admin_id: str, group_id: str, user_id: str
    ) -> GroupMember | None:
        """Remove a user from a group (idempotent)."""
        group = await self.group_repo.get_by_id(group_id)
        if group is None:
            raise NotFoundError()
        member = await self.group_member_repo.set_removed(
            group_id=group_id,
            user_id=user_id,
            admin_id=admin_id,
        )
        if member is None:
            return None

        await remove_user_from_group_room(user_id=user_id, group_id=group_id)
        removed_at = member.removed_at
        await gateway.emit_to_user(
            user_id=user_id,
            event=GroupChatEvents.MEMBER_REMOVED,
            data={
                "group_id": group_id,
                "removed_at": removed_at.isoformat() if removed_at else None,
            },
        )
        return member

    async def list_user_groups(
        self, user_id: str, skip: int = 0, limit: int = 20
    ) -> tuple[list[Group], int]:
        """List groups for a user with pagination.

        Returns:
            Tuple of (groups, total)
        """
        memberships = await self.group_member_repo.list_groups_for_user(
            user_id=user_id,
            skip=skip,
            limit=limit,
        )
        group_ids = [member.group_id for member in memberships]
        groups = await self.group_repo.get_by_ids(group_ids)
        group_map = {group.id: group for group in groups}
        ordered_groups = [
            group_map[group_id]
            for group_id in group_ids
            if group_id in group_map
        ]
        total = await self.group_member_repo.count_active_groups_for_user(user_id)
        return ordered_groups, total

    async def ensure_member_or_404(self, user_id: str, group_id: str) -> None:
        """Ensure the user is an active member of the group."""
        is_member = await self.group_member_repo.is_active_member(group_id, user_id)
        if not is_member:
            raise NotFoundError()
