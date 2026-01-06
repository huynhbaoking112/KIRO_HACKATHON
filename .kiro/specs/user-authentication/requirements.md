# Requirements Document

## Introduction

Hệ thống xác thực người dùng (User Authentication) cho phép người dùng đăng ký tài khoản mới và đăng nhập vào hệ thống sử dụng email và password. Hệ thống sử dụng JWT (JSON Web Token) để quản lý phiên đăng nhập với thời hạn 3 ngày, hỗ trợ đăng nhập đa thiết bị, và phân quyền theo role (user/admin).

## Glossary

- **User**: Người dùng của hệ thống, có thể đăng ký và đăng nhập
- **Auth_Service**: Service xử lý logic xác thực (đăng ký, đăng nhập)
- **User_Repository**: Repository thực hiện các thao tác với database cho User
- **JWT**: JSON Web Token - token xác thực stateless
- **Access_Token**: JWT token được cấp sau khi đăng nhập thành công
- **Role**: Vai trò của user trong hệ thống (user hoặc admin)
- **Password_Hasher**: Component hash và verify password sử dụng bcrypt

## Requirements

### Requirement 1: User Registration

**User Story:** As a new user, I want to register an account with email and password, so that I can access the system.

#### Acceptance Criteria

1. WHEN a user submits registration with valid email and password, THE Auth_Service SHALL create a new user account with role "user" and return user information
2. WHEN a user submits registration with an email that already exists, THE Auth_Service SHALL reject the registration and return an error message "Email already registered"
3. WHEN a user submits registration with invalid email format, THE Auth_Service SHALL reject the registration and return a validation error
4. WHEN a user submits registration with password shorter than 8 characters, THE Auth_Service SHALL reject the registration and return a validation error
5. WHEN storing user password, THE Password_Hasher SHALL hash the password using bcrypt before saving to database
6. THE User_Repository SHALL store user data with fields: email, hashed_password, role, is_active, created_at, updated_at

### Requirement 2: User Login

**User Story:** As a registered user, I want to login with my email and password, so that I can receive an access token to use the system.

#### Acceptance Criteria

1. WHEN a user submits login with correct email and password, THE Auth_Service SHALL return a valid JWT access token
2. WHEN a user submits login with incorrect email, THE Auth_Service SHALL reject the login and return error "Invalid email or password"
3. WHEN a user submits login with incorrect password, THE Auth_Service SHALL reject the login and return error "Invalid email or password"
4. WHEN a user submits login with inactive account, THE Auth_Service SHALL reject the login and return error "Account is inactive"
5. WHEN generating access token, THE Auth_Service SHALL include user_id, email, role in the token payload
6. WHEN generating access token, THE Auth_Service SHALL set token expiration to 3 days from creation time

### Requirement 3: JWT Token Management

**User Story:** As a system, I want to create and verify JWT tokens, so that I can authenticate users on protected endpoints.

#### Acceptance Criteria

1. WHEN creating a JWT token, THE Auth_Service SHALL sign the token using HS256 algorithm with a secret key
2. WHEN verifying a JWT token, THE Auth_Service SHALL validate the signature and expiration time
3. IF a JWT token has expired, THEN THE Auth_Service SHALL reject the token and return error "Token has expired"
4. IF a JWT token has invalid signature, THEN THE Auth_Service SHALL reject the token and return error "Invalid token"
5. WHEN decoding a valid JWT token, THE Auth_Service SHALL return the user information from token payload

### Requirement 4: Get Current User

**User Story:** As an authenticated user, I want to retrieve my profile information, so that I can see my account details.

#### Acceptance Criteria

1. WHEN an authenticated user requests their profile, THE User_Service SHALL return user information (id, email, role, is_active, created_at)
2. WHEN a request is made without access token, THE System SHALL reject the request with 401 Unauthorized
3. WHEN a request is made with invalid access token, THE System SHALL reject the request with 401 Unauthorized
4. THE System SHALL NOT return the hashed_password in user profile response

### Requirement 5: Role-Based Access Control

**User Story:** As a system administrator, I want to restrict certain endpoints to admin users only, so that I can protect sensitive operations.

#### Acceptance Criteria

1. THE System SHALL support two roles: "user" and "admin"
2. WHEN a non-admin user accesses an admin-only endpoint, THE System SHALL reject the request with 403 Forbidden
3. WHEN an admin user accesses an admin-only endpoint, THE System SHALL allow the request to proceed
4. THE Auth_Service SHALL provide a dependency function to check admin role

### Requirement 6: Password Security

**User Story:** As a security-conscious system, I want to securely hash and verify passwords, so that user credentials are protected.

#### Acceptance Criteria

1. THE Password_Hasher SHALL use bcrypt algorithm for password hashing
2. WHEN hashing a password, THE Password_Hasher SHALL generate a unique salt for each password
3. WHEN verifying a password, THE Password_Hasher SHALL compare the provided password against the stored hash
4. THE System SHALL NOT store plain-text passwords in the database
