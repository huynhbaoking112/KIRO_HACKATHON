# Group Chat (Admin-managed) — Requirements

## Summary
Build a group chat feature where **system admins** can create and manage group membership, and **users** can chat inside groups they belong to.

## Goals
- Admin can **create** a group chat.
- Admin can **add/remove** any user to/from any group chat.
- Users can **list** groups they belong to, **send messages**, **read message history**, and **receive real-time messages** in those groups.
- The system enforces **authorization** so removed users cannot access the group anymore.

## Non-goals (MVP)
- No user self-leave.
- No attachments, reactions, typing indicators, read receipts, search, pinning, mentions, threads.
- No multi-instance / horizontal scaling requirements (single Socket.IO server instance).

## Actors & Roles
- **Admin**: a user with global role `admin` (system-wide). There is **no per-group admin role**.
- **User**: a normal authenticated user with role `user`.

## Definitions
- **Group**: a chat container with an ID and name.
- **Member**: a user who is currently in the group (membership is active).
- **Removed member**: a user previously in the group but currently not a member.

## Assumptions / Decisions (confirmed)
- Admin is global (system admin).
- When an admin creates a group, the creator is **auto-added as a member**.
- Users cannot self-remove/leave.
- Messages are broadcast via Socket.IO to a **group room** `group:{group_id}`.
- On socket connect, the server joins the user to all group rooms they are a member of.
- When an admin removes a user from a group, the server removes **all active sockets** of that user from the group room.

## User Stories & Acceptance Criteria

### R1 — Admin creates a group
**As an admin**, I can create a group with a name so that users can chat in it.

Acceptance criteria:
- Only `admin` can create a group.
- A group has at least: `id`, `name`, `created_by_admin_id`, `created_at`.
- The creator admin is auto-added as an active member of the group.
- Response returns the created group object.

### R2 — Admin adds a user to a group
**As an admin**, I can add a user to a group so they can participate.

Acceptance criteria:
- Only `admin` can add members.
- Adding is idempotent: adding an already-active member succeeds without duplication.
- If the user is currently connected via Socket.IO, they are joined to `group:{group_id}` immediately (all of their active connections).
- The added user receives a real-time notification on their personal room `user:{user_id}` that they were added (payload includes `group_id`).

### R3 — Admin removes a user from a group
**As an admin**, I can remove a user from a group so they lose access.

Acceptance criteria:
- Only `admin` can remove members.
- Removal is idempotent: removing a non-member or already-removed member succeeds without error.
- All active sockets for that user are removed from `group:{group_id}` immediately.
- The removed user receives a real-time notification on `user:{user_id}` that they were removed (payload includes `group_id`).
- After removal, the user cannot:
  - list the group in “my groups”
  - fetch message history
  - send messages
  - receive future broadcasts from `group:{group_id}`

### R4 — User lists groups they belong to
**As a user**, I can list the groups I’m currently a member of.

Acceptance criteria:
- Only authenticated users can list their groups.
- Returns only active memberships.
- Pagination is supported (either skip/limit or cursor); API specifies limit bounds.

### R5 — User sends a message to a group
**As a user**, I can send a message to a group so others can see it.

Acceptance criteria:
- Only authenticated users who are active members can send.
- Server validates membership at send-time (do not rely solely on room membership).
- Message is persisted before broadcast.
- A `group:message:created` event is emitted to room `group:{group_id}` with message payload.
- If message submission is retried, the API supports optional idempotency via `client_msg_id` (recommended).

### R6 — User reads message history in a group
**As a user**, I can fetch message history for a group I belong to.

Acceptance criteria:
- Only authenticated active members can read.
- Results are paginated (cursor-based recommended for large groups).
- Messages include at least: `id`, `group_id`, `sender_id`, `content`, `created_at`.

### R7 — User receives real-time group messages
**As a user**, I receive messages in real time for groups I belong to.

Acceptance criteria:
- On Socket.IO connect, after auth, the server joins the socket to all `group:{group_id}` rooms the user is a current member of.
- When the server emits `group:message:created` to a group room, all connected members in that room receive it.
- When the user is removed by admin, they must stop receiving messages for that group immediately.

## Authorization & Error Handling Requirements
- Authentication:
  - All endpoints require JWT auth.
- Authorization:
  - Admin endpoints require role `admin`.
  - User group/message endpoints require active membership.
- Errors:
  - `401 Unauthorized` for invalid/missing token
  - `403 Forbidden` for role violations (non-admin calling admin endpoints)
  - `404 Not Found` when group does not exist OR group exists but user is not a member (avoid leaking existence)

## Data Consistency Requirements
- Membership updates are atomic from the perspective of authorization:
  - After successful remove, subsequent send/history calls must be rejected.
- Message ordering:
  - Messages must be returned in a deterministic order (by `created_at`, then `id` tiebreaker).

## Non-functional Requirements (MVP)
- Performance:
  - “Connect → join all rooms” must be efficient; membership queries must be indexed by `user_id`.
  - Message history must be paginated; limit defaults and max enforced.
- Reliability:
  - Socket emits should not block core persistence path (persist first, then emit).
- Auditability (recommended):
  - Log admin membership changes with `admin_id`, `group_id`, `user_id`, action, timestamp.

## Open Questions (none blocking)
- Should admins be able to list members/messages of any group via admin endpoints (beyond being a member)? (Optional)

---
## Approval Gate
Please review these requirements. If you approve, I will produce:
1) `design.md` (architecture, data model details, APIs, socket events, correctness properties)
2) `tasks.md` (implementation plan with breakdown and test strategy)

