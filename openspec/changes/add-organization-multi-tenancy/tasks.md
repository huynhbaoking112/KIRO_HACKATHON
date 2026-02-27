## 1. Domain Models

- [x] 1.1 Create Organization model in `app/domain/models/organization.py` with fields: id, name, slug, description, is_active, created_by, created_at, updated_at
- [x] 1.2 Create OrganizationRole enum (ADMIN, USER) in `app/domain/models/organization.py`
- [x] 1.3 Create OrganizationMember model in `app/domain/models/organization.py` with fields: id, user_id, organization_id, role, added_by, is_active, created_at, updated_at
- [x] 1.4 Update UserRole enum in `app/domain/models/user.py`: rename ADMIN to SUPER_ADMIN
- [x] 1.5 Add organization_id field (Optional) to Conversation model in `app/domain/models/conversation.py`
- [x] 1.6 Add organization_id field (Optional) to SheetConnection model in `app/domain/models/sheet_connection.py`
- [x] 1.7 Export new models in `app/domain/models/__init__.py`

## 2. Schemas

- [x] 2.1 Create organization schemas in `app/domain/schemas/organization.py`: CreateOrganizationRequest, UpdateOrganizationRequest, OrganizationResponse, OrganizationDetailResponse
- [x] 2.2 Create membership schemas in `app/domain/schemas/organization.py`: AddMemberRequest, UpdateMemberRoleRequest, OrganizationMemberResponse, UserOrganizationResponse
- [x] 2.3 Create user management schemas in `app/domain/schemas/auth.py`: CreateUserRequest, CreateUserResponse, ChangePasswordRequest, ResetPasswordRequest
- [x] 2.4 Remove RegisterRequest schema from `app/domain/schemas/auth.py`
- [x] 2.5 Update auth schemas to use SUPER_ADMIN in role references

## 3. Repositories

- [ ] 3.1 Create OrganizationRepository in `app/repo/organization_repo.py` with methods: create, find_by_id, find_by_slug, list_all, update, deactivate
- [ ] 3.2 Create OrganizationMemberRepository in `app/repo/organization_member_repo.py` with methods: create, find_by_user_and_org, list_by_organization, list_by_user, update_role, remove
- [ ] 3.3 Add list_all method to UserRepository in `app/repo/user_repo.py`
- [ ] 3.4 Add update_password method to UserRepository in `app/repo/user_repo.py`
- [ ] 3.5 Add update_is_active method to UserRepository in `app/repo/user_repo.py`
- [ ] 3.6 Update ConversationRepository to support organization_id filtering
- [ ] 3.7 Update SheetConnectionRepository to support organization_id filtering

## 4. Database Indexes

- [ ] 4.1 Add organization indexes in `app/infrastructure/database/mongodb.py`: slug (unique), is_active
- [ ] 4.2 Add organization_members indexes: (user_id, organization_id) unique, organization_id, user_id
- [ ] 4.3 Update conversations index to include organization_id
- [ ] 4.4 Update sheet_connections index to include organization_id

## 5. Services

- [ ] 5.1 Create OrganizationService in `app/services/organization/organization_service.py` with methods: create_organization, get_organization, list_organizations, update_organization, deactivate_organization
- [ ] 5.2 Add membership methods to OrganizationService: add_member, remove_member, change_member_role, get_organization_members, get_user_organizations
- [ ] 5.3 Add permission helper methods: _check_can_manage_members, _check_is_member
- [ ] 5.4 Create UserService in `app/services/user/user_service.py` with methods: create_user, list_users, get_user, deactivate_user, reset_password
- [ ] 5.5 Remove register_user method from AuthService in `app/services/auth/auth_service.py`
- [ ] 5.6 Add change_password method to AuthService

## 6. Dependencies

- [ ] 6.1 Add get_org_repo dependency factory in `app/common/repo.py`
- [ ] 6.2 Add get_member_repo dependency factory in `app/common/repo.py`
- [ ] 6.3 Add get_org_service dependency factory in `app/common/service.py`
- [ ] 6.4 Add get_user_service dependency factory in `app/common/service.py`
- [ ] 6.5 Create get_current_organization_context dependency in `app/api/deps.py` that validates X-Organization-ID header
- [ ] 6.6 Create require_org_admin dependency in `app/api/deps.py`
- [ ] 6.7 Update require_admin to require_super_admin in `app/api/deps.py`

## 7. Organization API Endpoints

- [ ] 7.1 Create organization router in `app/api/v1/organizations/routes.py`
- [ ] 7.2 Implement POST /api/v1/organizations - create organization (Super Admin only)
- [ ] 7.3 Implement GET /api/v1/organizations - list organizations (Super Admin only)
- [ ] 7.4 Implement GET /api/v1/organizations/{org_id} - get organization details
- [ ] 7.5 Implement PATCH /api/v1/organizations/{org_id} - update organization (Super Admin only)
- [ ] 7.6 Implement DELETE /api/v1/organizations/{org_id} - deactivate organization (Super Admin only)

## 8. Membership API Endpoints

- [ ] 8.1 Implement POST /api/v1/organizations/{org_id}/members - add member
- [ ] 8.2 Implement GET /api/v1/organizations/{org_id}/members - list members
- [ ] 8.3 Implement PATCH /api/v1/organizations/{org_id}/members/{user_id} - change role
- [ ] 8.4 Implement DELETE /api/v1/organizations/{org_id}/members/{user_id} - remove member

## 9. User Management API Endpoints

- [ ] 9.1 Create user management router in `app/api/v1/users/routes.py`
- [ ] 9.2 Implement POST /api/v1/users - create user (Admin only)
- [ ] 9.3 Implement GET /api/v1/users - list users (scoped by permission)
- [ ] 9.4 Implement GET /api/v1/users/me - get current user profile
- [ ] 9.5 Implement GET /api/v1/users/me/organizations - list user's organizations
- [ ] 9.6 Implement GET /api/v1/users/{user_id} - get user details
- [ ] 9.7 Implement PATCH /api/v1/users/{user_id} - update user (deactivate)
- [ ] 9.8 Implement POST /api/v1/users/{user_id}/reset-password - reset password

## 10. Auth Updates

- [ ] 10.1 Remove /api/v1/auth/register endpoint from `app/api/v1/auth/routes.py`
- [ ] 10.2 Implement POST /api/v1/auth/change-password endpoint
- [ ] 10.3 Update JWT token generation to use SUPER_ADMIN role

## 11. Router Registration

- [ ] 11.1 Register organizations router in `app/api/v1/router.py`
- [ ] 11.2 Register users router in `app/api/v1/router.py`

## 12. Update Existing Endpoints

- [ ] 12.1 Update conversation endpoints to require X-Organization-ID header
- [ ] 12.2 Update sheet connection endpoints to require X-Organization-ID header
- [ ] 12.3 Update conversation creation to include organization_id
- [ ] 12.4 Update sheet connection creation to include organization_id

## 13. Exceptions

- [ ] 13.1 Add OrganizationNotFoundError to `app/common/exceptions.py`
- [ ] 13.2 Add AlreadyMemberError to `app/common/exceptions.py`
- [ ] 13.3 Add NotMemberError to `app/common/exceptions.py`
- [ ] 13.4 Add PermissionDeniedError to `app/common/exceptions.py` (if not exists)

## 14. Testing

- [ ] 14.1 Write unit tests for Organization model
- [ ] 14.2 Write unit tests for OrganizationMember model
- [ ] 14.3 Write unit tests for OrganizationRepository
- [ ] 14.4 Write unit tests for OrganizationMemberRepository
- [ ] 14.5 Write unit tests for OrganizationService
- [ ] 14.6 Write unit tests for UserService
- [ ] 14.7 Write integration tests for organization endpoints
- [ ] 14.8 Write integration tests for membership endpoints
- [ ] 14.9 Write integration tests for user management endpoints
- [ ] 14.10 Write integration tests for permission checks (Super Admin, Org Admin, User)
