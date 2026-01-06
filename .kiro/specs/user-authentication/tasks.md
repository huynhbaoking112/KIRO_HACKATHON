# Implementation Plan: User Authentication

## Overview

Implementation plan cho hệ thống User Authentication theo pattern Controller → Service → Repository. Sử dụng JWT cho authentication và bcrypt cho password hashing với MongoDB làm database.

## Tasks

- [x] 1. Setup Infrastructure Layer
  - [x] 1.1 Implement MongoDB connection client
    - Tạo `app/infrastructure/database/mongodb.py` với async connection
    - Implement connect, disconnect, get_db methods
    - Update `app/main.py` lifespan để connect/disconnect MongoDB
    - _Requirements: 1.6_

  - [x] 1.2 Implement Password Security Utils
    - Tạo `app/infrastructure/security/__init__.py`
    - Tạo `app/infrastructure/security/password.py` với hash_password, verify_password
    - Sử dụng passlib với bcrypt scheme
    - _Requirements: 1.5, 6.1, 6.2, 6.3_

  - [ ]* 1.3 Write property tests for Password Utils
    - **Property 1: Password Hash Round-Trip**
    - **Property 2: Password Hash Uniqueness**
    - **Validates: Requirements 1.5, 6.1, 6.2, 6.3**

  - [x] 1.4 Implement JWT Security Utils
    - Tạo `app/infrastructure/security/jwt.py` với create_access_token, decode_access_token
    - Sử dụng python-jose với HS256 algorithm
    - Token expiration 3 days
    - _Requirements: 2.5, 2.6, 3.1, 3.2, 3.5_

  - [ ]* 1.5 Write property tests for JWT Utils
    - **Property 6: JWT Token Round-Trip**
    - **Property 7: JWT Token Expiration**
    - **Validates: Requirements 2.5, 2.6, 3.5**

  - [x] 1.6 Update Settings với JWT và MongoDB config
    - Thêm MONGODB_URI, MONGODB_DB_NAME
    - Thêm JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_DAYS
    - Update `.env.example`
    - _Requirements: 2.6, 3.1_

- [ ] 2. Checkpoint - Ensure infrastructure tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Setup Domain Layer
  - [x] 3.1 Create User Model và Enums
    - Tạo `app/domain/models/user.py` với User model, UserRole enum
    - Fields: id, email, hashed_password, role, is_active, created_at, updated_at
    - _Requirements: 1.6, 5.1_

  - [x] 3.2 Create Auth Schemas
    - Tạo `app/domain/schemas/auth.py`
    - RegisterRequest, LoginRequest, TokenResponse, TokenPayload, UserResponse
    - Email validation, password min_length=8
    - _Requirements: 1.3, 1.4, 4.4_

  - [ ]* 3.3 Write property tests for Schema Validation
    - **Property 10: Email Validation**
    - **Property 11: Password Length Validation**
    - **Validates: Requirements 1.3, 1.4**

- [ ] 4. Setup Repository Layer
  - [ ] 4.1 Create User Repository
    - Tạo `app/repo/__init__.py`
    - Tạo `app/repo/user_repo.py` với UserRepository class
    - Implement create, find_by_email, find_by_id methods
    - _Requirements: 1.6_

- [ ] 5. Setup Service Layer
  - [ ] 5.1 Create Custom Exceptions
    - Update `app/common/exceptions.py`
    - Thêm AuthenticationError, InvalidTokenError, EmailAlreadyExistsError, InactiveUserError, PermissionDeniedError
    - _Requirements: 1.2, 2.2, 2.3, 2.4, 3.3, 3.4_

  - [ ] 5.2 Implement Auth Service
    - Tạo `app/services/auth/__init__.py`
    - Tạo `app/services/auth/auth_service.py` với AuthService class
    - Implement register_user, authenticate_user, create_access_token, verify_token
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 5.3 Write property tests for Auth Service
    - **Property 3: Registration Creates Valid User**
    - **Property 4: Duplicate Email Rejection**
    - **Property 5: Invalid Credentials Rejection**
    - **Validates: Requirements 1.1, 1.2, 2.2, 2.3**

  - [ ] 5.4 Implement User Service
    - Update `app/services/business/user_service.py` với UserService class
    - Implement get_user_by_id method
    - _Requirements: 4.1_

- [ ] 6. Checkpoint - Ensure service tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Setup API Layer
  - [ ] 7.1 Create Auth Dependencies
    - Update `app/api/deps.py`
    - Implement get_current_user, get_current_active_user, require_admin dependencies
    - Setup OAuth2PasswordBearer
    - _Requirements: 4.2, 4.3, 5.2, 5.3, 5.4_

  - [ ] 7.2 Create Auth Routes
    - Tạo `app/api/v1/auth/__init__.py`
    - Tạo `app/api/v1/auth/routes.py`
    - Implement POST /auth/register, POST /auth/login
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4_

  - [ ] 7.3 Update User Routes
    - Update `app/api/v1/business/users.py`
    - Implement GET /users/me với get_current_active_user dependency
    - _Requirements: 4.1, 4.4_

  - [ ] 7.4 Update API Router
    - Update `app/api/v1/router.py` để include auth routes
    - _Requirements: 1.1, 2.1_

  - [ ]* 7.5 Write property tests for API endpoints
    - **Property 8: Profile Excludes Password**
    - **Property 9: Role-Based Access Control**
    - **Validates: Requirements 4.4, 5.2, 5.3**

- [ ] 8. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Dependencies đã được thêm vào requirements.txt: python-jose[cryptography], passlib[bcrypt], motor
