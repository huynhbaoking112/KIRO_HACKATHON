"""Group chat endpoints for admin-managed group chat."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_current_active_user, require_admin
from app.common.exceptions import NotFoundError
from app.common.service import get_group_message_service, get_group_service
from app.domain.models.user import User
from app.domain.schemas.group_chat import (
    AddGroupMemberRequest,
    CreateGroupRequest,
    GroupListResponse,
    GroupMemberResponse,
    GroupMessageListResponse,
    GroupMessageResponse,
    GroupResponse,
    SendGroupMessageRequest,
)
from app.services.business.group_message_service import GroupMessageService
from app.services.business.group_service import GroupService

router = APIRouter(prefix="/groups", tags=["groups"])


def _map_not_found(error: NotFoundError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=error.message,
    )


@router.post("", response_model=GroupResponse)
async def create_group(
    request: CreateGroupRequest,
    current_user: User = Depends(require_admin),
    group_service: GroupService = Depends(get_group_service),
) -> GroupResponse:
    """Create a new group (admin only)."""
    group = await group_service.create_group(
        admin_id=current_user.id,
        name=request.name,
    )
    return GroupResponse(
        id=group.id,
        name=group.name,
        created_by_admin_id=group.created_by_admin_id,
        created_at=group.created_at,
    )


@router.post("/{group_id}/members", response_model=GroupMemberResponse)
async def add_group_member(
    group_id: str,
    request: AddGroupMemberRequest,
    current_user: User = Depends(require_admin),
    group_service: GroupService = Depends(get_group_service),
) -> GroupMemberResponse:
    """Add a user to a group (admin only)."""
    try:
        member = await group_service.add_member(
            admin_id=current_user.id,
            group_id=group_id,
            user_id=request.user_id,
        )
    except NotFoundError as exc:
        raise _map_not_found(exc) from exc

    return GroupMemberResponse(
        group_id=member.group_id,
        user_id=member.user_id,
        joined_at=member.joined_at,
        removed_at=member.removed_at,
    )


@router.delete("/{group_id}/members/{user_id}", response_model=GroupMemberResponse)
async def remove_group_member(
    group_id: str,
    user_id: str,
    current_user: User = Depends(require_admin),
    group_service: GroupService = Depends(get_group_service),
) -> GroupMemberResponse:
    """Remove a user from a group (admin only)."""
    try:
        member = await group_service.remove_member(
            admin_id=current_user.id,
            group_id=group_id,
            user_id=user_id,
        )
    except NotFoundError as exc:
        raise _map_not_found(exc) from exc

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    return GroupMemberResponse(
        group_id=member.group_id,
        user_id=member.user_id,
        joined_at=member.joined_at,
        removed_at=member.removed_at,
    )


@router.get("", response_model=GroupListResponse)
async def list_groups(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    group_service: GroupService = Depends(get_group_service),
) -> GroupListResponse:
    """List groups for current user."""
    groups, total = await group_service.list_user_groups(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return GroupListResponse(
        items=[
            GroupResponse(
                id=group.id,
                name=group.name,
                created_by_admin_id=group.created_by_admin_id,
                created_at=group.created_at,
            )
            for group in groups
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{group_id}/messages", response_model=GroupMessageListResponse)
async def list_group_messages(
    group_id: str,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    message_service: GroupMessageService = Depends(get_group_message_service),
) -> GroupMessageListResponse:
    """List group messages for a group the user belongs to."""
    try:
        messages, next_cursor = await message_service.list_messages(
            user_id=current_user.id,
            group_id=group_id,
            cursor=cursor,
            limit=limit,
        )
    except NotFoundError as exc:
        raise _map_not_found(exc) from exc

    return GroupMessageListResponse(
        group_id=group_id,
        items=[
            GroupMessageResponse(
                id=msg.id,
                group_id=msg.group_id,
                sender_id=msg.sender_id,
                content=msg.content,
                created_at=msg.created_at,
            )
            for msg in messages
        ],
        next_cursor=next_cursor,
    )


@router.post("/{group_id}/messages", response_model=GroupMessageResponse)
async def send_group_message(
    group_id: str,
    request: SendGroupMessageRequest,
    current_user: User = Depends(get_current_active_user),
    message_service: GroupMessageService = Depends(get_group_message_service),
) -> GroupMessageResponse:
    """Send a message to a group the user belongs to."""
    try:
        message = await message_service.send_message(
            user_id=current_user.id,
            group_id=group_id,
            content=request.content,
            client_msg_id=request.client_msg_id,
        )
    except NotFoundError as exc:
        raise _map_not_found(exc) from exc

    return GroupMessageResponse(
        id=message.id,
        group_id=message.group_id,
        sender_id=message.sender_id,
        content=message.content,
        created_at=message.created_at,
    )
