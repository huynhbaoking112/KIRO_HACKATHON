"""Chat API endpoints for sending messages and receiving AI responses.

Provides REST endpoints for:
- Sending messages to AI agent
- Triggering background processing for agent responses
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.deps import get_current_active_user
from app.common.service import get_chat_service
from app.domain.models.user import User
from app.domain.schemas.chat import SendMessageRequest, SendMessageResponse
from app.services.ai.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    chat_service: ChatService = Depends(get_chat_service),
) -> SendMessageResponse:
    """Send a message and trigger async agent processing.

    If conversation_id is not provided, creates a new conversation.
    The user message is saved immediately, and agent processing
    runs in the background with responses streamed via Socket.IO.

    Args:
        request: SendMessageRequest with content and optional conversation_id
        background_tasks: FastAPI BackgroundTasks for async processing
        current_user: Authenticated user from JWT token
        chat_service: ChatService dependency

    Returns:
        SendMessageResponse with user_message_id and conversation_id

    Raises:
        HTTPException: 404 if conversation_id is invalid or not found

    Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
    """
    user_id = current_user.id

    # Validate conversation exists if conversation_id is provided
    if request.conversation_id is not None:
        conversation = await chat_service.conversation_service.get_conversation(
            request.conversation_id
        )
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        # Verify user owns the conversation
        if conversation.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )

    # Save user message and get/create conversation
    user_message_id, conversation_id = await chat_service.send_message(
        user_id=user_id,
        content=request.content,
        conversation_id=request.conversation_id,
    )

    # Add background task to process agent response
    background_tasks.add_task(
        chat_service.process_agent_response,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    return SendMessageResponse(
        user_message_id=user_message_id,
        conversation_id=conversation_id,
    )
