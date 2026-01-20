"""Group message service for admin-managed group chats."""

from app.common.exceptions import NotFoundError
from app.domain.models.group_message import GroupMessage
from app.common.event_socket import GroupChatEvents
from app.repo.group_member_repo import GroupMemberRepository
from app.repo.group_message_repo import GroupMessageRepository
from app.socket_gateway import gateway


class GroupMessageService:
    """Service for sending and retrieving group messages."""

    def __init__(
        self,
        group_message_repo: GroupMessageRepository,
        group_member_repo: GroupMemberRepository,
    ):
        """Initialize GroupMessageService with repositories.

        Args:
            group_message_repo: Repository for group message operations
            group_member_repo: Repository for group membership checks
        """
        self.group_message_repo = group_message_repo
        self.group_member_repo = group_member_repo

    async def send_message(
        self,
        user_id: str,
        group_id: str,
        content: str,
        client_msg_id: str | None = None,
    ) -> GroupMessage:
        """Send a message to a group after membership validation."""
        is_member = await self.group_member_repo.is_active_member(group_id, user_id)
        if not is_member:
            raise NotFoundError()

        message = await self.group_message_repo.create_message(
            group_id=group_id,
            sender_id=user_id,
            content=content,
            client_msg_id=client_msg_id,
        )

        await gateway.emit_to_room(
            room=f"group:{group_id}",
            event=GroupChatEvents.MESSAGE_CREATED,
            data={
                "id": message.id,
                "group_id": message.group_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            },
        )

        return message

    async def list_messages(
        self,
        user_id: str,
        group_id: str,
        cursor: str | None = None,
        limit: int = 50,
    ) -> tuple[list[GroupMessage], str | None]:
        """List messages for a group with membership validation."""
        is_member = await self.group_member_repo.is_active_member(group_id, user_id)
        if not is_member:
            raise NotFoundError()

        return await self.group_message_repo.list_messages(
            group_id=group_id,
            cursor=cursor,
            limit=limit,
        )
