# Design Document: User Authentication

## Overview

Hệ thống User Authentication được thiết kế theo kiến trúc **Controller → Service → Repository** pattern, sử dụng JWT cho stateless authentication và bcrypt cho password hashing. Hệ thống hỗ trợ đăng ký, đăng nhập, và phân quyền role-based (user/admin).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Controller Layer (API)                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  app/api/v1/auth/routes.py                          │    │
│  │  - POST /auth/register                              │    │
│  │  - POST /auth/login                                 │    │
│  └──────────────────────────┬──────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  app/api/v1/business/users.py                       │    │
│  │  - GET /users/me                                    │    │
│  └──────────────────────────┬──────────────────────────┘    │
└─────────────────────────────┼───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  app/services/auth/auth_service.py                  │    │
│  │  - register_user(email, password) → User            │    │
│  │  - authenticate_user(email, password) → Token       │    │
│  │  - verify_token(token) → TokenPayload               │    │
│  └──────────────────────────┬──────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  app/services/business/user_service.py              │    │
│  │  - get_user_by_id(id) → User                        │    │
│  └──────────────────────────┬──────────────────────────┘    │
└─────────────────────────────┼───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Repository Layer                          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  app/repo/user_repo.py                              │    │
│  │  - create(user_data) → User                         │    │
│  │  - find_by_email(email) → User | None               │    │
│  │  - find_by_id(id) → User | None                     │    │
│  └──────────────────────────┬──────────────────────────┘    │
└─────────────────────────────┼───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Infrastructure Layer                        │
│  ┌──────────────────┐  ┌─────────────────────────────────┐  │
│  │  MongoDB Client  │  │  Security Utils                 │  │
│  │  (motor async)   │  │  - hash_password()              │  │
│  │                  │  │  - verify_password()            │  │
│  │                  │  │  - create_access_token()        │  │
│  │                  │  │  - decode_access_token()        │  │
│  └──────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. API Layer (Controllers)

#### Auth Routes (`app/api/v1/auth/routes.py`)

```python
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(request: RegisterRequest, auth_service: AuthService = Depends()):
    """Register a new user with email and password."""
    pass

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, auth_service: AuthService = Depends()):
    """Login and receive JWT access token."""
    pass
```

#### User Routes (`app/api/v1/business/users.py`)

```python
router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current authenticated user's profile."""
    pass
```

### 2. Service Layer

#### Auth Service (`app/services/auth/auth_service.py`)

```python
class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def register_user(self, email: str, password: str) -> User:
        """Register a new user. Raises ValueError if email exists."""
        pass
    
    async def authenticate_user(self, email: str, password: str) -> str:
        """Authenticate user and return JWT token. Raises AuthenticationError on failure."""
        pass
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token for user."""
        pass
    
    def verify_token(self, token: str) -> TokenPayload:
        """Verify and decode JWT token. Raises InvalidTokenError on failure."""
        pass
```

#### User Service (`app/services/business/user_service.py`)

```python
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
    
    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        pass
```

### 3. Repository Layer

#### User Repository (`app/repo/user_repo.py`)

```python
class UserRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.users
    
    async def create(self, user_data: UserCreate) -> User:
        """Create a new user in database."""
        pass
    
    async def find_by_email(self, email: str) -> User | None:
        """Find user by email."""
        pass
    
    async def find_by_id(self, user_id: str) -> User | None:
        """Find user by ID."""
        pass
```

### 4. Infrastructure Layer

#### Security - Password (`app/infrastructure/security/password.py`)

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

#### Security - JWT (`app/infrastructure/security/jwt.py`)

```python
from jose import jwt, JWTError
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=3)) -> str:
    """Create JWT access token with expiration."""
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")

def decode_access_token(token: str) -> dict:
    """Decode and verify JWT token. Raises JWTError on failure."""
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
```

#### MongoDB Client (`app/infrastructure/database/mongodb.py`)

```python
from motor.motor_asyncio import AsyncIOMotorClient

class MongoDB:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect(cls, uri: str, db_name: str):
        """Connect to MongoDB."""
        cls.client = AsyncIOMotorClient(uri)
        cls.db = cls.client[db_name]
    
    @classmethod
    async def disconnect(cls):
        """Disconnect from MongoDB."""
        if cls.client:
            cls.client.close()
    
    @classmethod
    def get_db(cls):
        """Get database instance."""
        return cls.db
```

### 5. Dependencies (`app/api/deps.py`)

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token."""
    pass

async def get_current_active_user(user: User = Depends(get_current_user)) -> User:
    """Get current active user. Raises HTTPException if inactive."""
    pass

async def require_admin(user: User = Depends(get_current_active_user)) -> User:
    """Require admin role. Raises HTTPException if not admin."""
    pass
```

## Data Models

### User Model (`app/domain/models/user.py`)

```python
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class User(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    hashed_password: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
```

### Auth Schemas (`app/domain/schemas/auth.py`)

```python
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: str  # user_id
    email: str
    role: str
    exp: int
    iat: int

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    # Note: hashed_password is NOT included
```

### MongoDB Document Structure

```json
{
    "_id": "ObjectId",
    "email": "user@example.com",
    "hashed_password": "$2b$12$...",
    "role": "user",
    "is_active": true,
    "created_at": "ISODate",
    "updated_at": "ISODate"
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Password Hash Round-Trip

*For any* valid password string, hashing it and then verifying the original password against the hash SHALL return true, and verifying any different password SHALL return false.

**Validates: Requirements 1.5, 6.1, 6.3**

### Property 2: Password Hash Uniqueness

*For any* password, hashing it multiple times SHALL produce different hash values (due to unique salt generation).

**Validates: Requirements 6.2**

### Property 3: Registration Creates Valid User

*For any* valid email and password (≥8 chars), registration SHALL create a user with:
- The provided email
- A bcrypt-hashed password (not plain text)
- Role set to "user"
- is_active set to true

**Validates: Requirements 1.1, 1.5, 1.6**

### Property 4: Duplicate Email Rejection

*For any* registered email, attempting to register again with the same email SHALL be rejected with "Email already registered" error.

**Validates: Requirements 1.2**

### Property 5: Invalid Credentials Rejection

*For any* login attempt with non-existent email OR incorrect password, the system SHALL reject with "Invalid email or password" error (same message for both cases to prevent email enumeration).

**Validates: Requirements 2.2, 2.3**

### Property 6: JWT Token Round-Trip

*For any* valid user, creating an access token and then decoding it SHALL return the same user_id, email, and role.

**Validates: Requirements 2.5, 3.5**

### Property 7: JWT Token Expiration

*For any* generated access token, the expiration time (exp claim) SHALL be approximately 3 days (259200 seconds) from the issued time (iat claim).

**Validates: Requirements 2.6**

### Property 8: Profile Excludes Password

*For any* user profile response, the response SHALL NOT contain the hashed_password field.

**Validates: Requirements 4.4**

### Property 9: Role-Based Access Control

*For any* admin-only endpoint:
- Users with role "admin" SHALL be allowed access
- Users with role "user" SHALL receive 403 Forbidden

**Validates: Requirements 5.2, 5.3**

### Property 10: Email Validation

*For any* string that is not a valid email format, registration SHALL be rejected with a validation error.

**Validates: Requirements 1.3**

### Property 11: Password Length Validation

*For any* password shorter than 8 characters, registration SHALL be rejected with a validation error.

**Validates: Requirements 1.4**

## Error Handling

### Custom Exceptions (`app/common/exceptions.py`)

```python
class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass

class InvalidTokenError(Exception):
    """Raised when JWT token is invalid or expired."""
    pass

class EmailAlreadyExistsError(Exception):
    """Raised when email is already registered."""
    pass

class UserNotFoundError(Exception):
    """Raised when user is not found."""
    pass

class InactiveUserError(Exception):
    """Raised when user account is inactive."""
    pass

class PermissionDeniedError(Exception):
    """Raised when user lacks required permissions."""
    pass
```

### HTTP Error Responses

| Exception | HTTP Status | Response |
|-----------|-------------|----------|
| AuthenticationError | 401 | `{"detail": "Invalid email or password"}` |
| InvalidTokenError | 401 | `{"detail": "Invalid token"}` or `{"detail": "Token has expired"}` |
| EmailAlreadyExistsError | 400 | `{"detail": "Email already registered"}` |
| InactiveUserError | 401 | `{"detail": "Account is inactive"}` |
| PermissionDeniedError | 403 | `{"detail": "Permission denied"}` |
| ValidationError | 422 | Pydantic validation error details |

## Testing Strategy

### Unit Tests

Unit tests sẽ test các component riêng lẻ:

1. **Password Utils Tests**
   - Test hash_password returns bcrypt hash
   - Test verify_password with correct/incorrect passwords

2. **JWT Utils Tests**
   - Test create_access_token includes required claims
   - Test decode_access_token with valid/invalid/expired tokens

3. **Repository Tests** (with mock database)
   - Test create user
   - Test find_by_email
   - Test find_by_id

4. **Service Tests** (with mock repository)
   - Test register_user success/failure cases
   - Test authenticate_user success/failure cases

### Property-Based Tests

Property-based tests sử dụng `hypothesis` library để test các correctness properties:

- **Minimum 100 iterations** per property test
- Each test references design document property
- Tag format: **Feature: user-authentication, Property N: {property_text}**

### Integration Tests

Integration tests sẽ test full flow qua API:

1. Register → Login → Get Profile flow
2. Role-based access control flow
3. Error handling scenarios

## Configuration

### Settings (`app/config/settings.py`)

```python
class Settings(BaseSettings):
    # Existing settings...
    
    # MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "ai_service"
    
    # JWT
    JWT_SECRET_KEY: str  # Required, no default for security
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_DAYS: int = 3
```

### Environment Variables (`.env.example`)

```
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=ai_service

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=3
```

## Dependencies

Thêm vào `requirements.txt`:

```
python-jose[cryptography]
passlib[bcrypt]
motor
```
