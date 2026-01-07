# Design Document: Google Sheet Crawler

## Overview

Tính năng Google Sheet Crawler cho phép hệ thống tự động crawl dữ liệu từ Google Sheets của khách hàng. Hệ thống sử dụng kiến trúc queue-based với rate limiting theo cơ chế Token Bucket để tuân thủ Google Sheets API quotas.

### Key Design Decisions

1. **Queue-based Architecture**: Cloud Scheduler trigger → API response ngay → Background task enqueue → Worker process với rate limiting
2. **Token Bucket Rate Limiter**: Mirror chính xác Google's rate limits (300 req/min, 100 req/100s)
3. **Incremental Sync**: Chỉ sync rows mới dựa trên last_synced_row
4. **Service Account Authentication**: Một service account chung, khách hàng share sheet cho email này

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Google Cloud Scheduler                              │
│   POST /api/v1/internal/trigger-sync (every 5 min)                      │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP POST
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                              │
│                                                                          │
│   Internal API (/internal/trigger-sync)                                 │
│   ├── Verify API Key                                                    │
│   ├── Return 202 Accepted immediately                                   │
│   └── BackgroundTask: enqueue all enabled connections                   │
│                                                                          │
│   Public API (/sheet-connections/*)                                     │
│   ├── CRUD operations (JWT auth)                                        │
│   ├── Manual sync trigger                                               │
│   └── Data retrieval                                                    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Redis Queue                                      │
│   Queue: sheet_sync_tasks                                               │
│   Task: {connection_id, user_id, queued_at, retry_count}               │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Sync Worker Process                              │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │              Token Bucket Rate Limiter                          │   │
│   │                                                                  │   │
│   │   Bucket 1: read_per_minute (300 capacity, 5 tokens/sec)       │   │
│   │   Bucket 2: requests_per_100s (100 capacity, 1 token/sec)      │   │
│   │                                                                  │   │
│   │   await rate_limiter.acquire(tokens=2)                         │   │
│   │   # Blocks if insufficient tokens, waits for refill            │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │              Crawler Service                                    │   │
│   │   ├── Fetch data from Google Sheet                             │   │
│   │   ├── Apply column mapping                                      │   │
│   │   ├── Save to MongoDB                                          │   │
│   │   ├── Update sync state                                        │   │
│   │   └── Notify via WebSocket                                     │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MongoDB Collections                              │
│                                                                          │
│   sheet_connections    - Connection configurations                      │
│   sheet_sync_states    - Sync state tracking                           │
│   sheet_raw_data       - Crawled data storage                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. API Layer

#### Internal Router (`app/api/v1/internal/router.py`)

```python
@router.post("/trigger-sync")
async def trigger_sync(
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_internal_api_key)
) -> dict:
    """
    Cloud Scheduler endpoint.
    Returns immediately, enqueues in background.
    """
    background_tasks.add_task(enqueue_all_connections)
    return {"status": "accepted", "timestamp": datetime.now(timezone.utc).isoformat()}
```

#### Sheet Crawler Router (`app/api/v1/sheet_crawler/router.py`)

```python
# Service Account Info
GET  /service-account -> ServiceAccountInfoResponse

# Connection CRUD
POST   /sheet-connections -> ConnectionResponse
GET    /sheet-connections -> list[ConnectionResponse]
GET    /sheet-connections/{id} -> ConnectionResponse
PUT    /sheet-connections/{id} -> ConnectionResponse
DELETE /sheet-connections/{id} -> None

# Sync Operations
POST /sheet-connections/{id}/sync -> SyncTriggerResponse
GET  /sheet-connections/{id}/sync-status -> SyncStatusResponse

# Data Operations
GET /sheet-connections/{id}/preview -> SheetPreviewResponse
GET /sheet-connections/{id}/data -> SheetDataResponse
```

### 2. Service Layer

#### Crawler Service (`app/services/business/sheet_crawler/crawler_service.py`)

```python
class SheetCrawlerService:
    def __init__(
        self,
        sheet_client: GoogleSheetClient,
        connection_repo: SheetConnectionRepository,
        sync_state_repo: SheetSyncStateRepository,
        data_repo: SheetDataRepository,
        socket_gateway: SocketGateway
    ):
        pass
    
    async def sync_sheet(self, connection_id: str) -> SyncResult:
        """
        Sync a single sheet connection.
        1. Get connection and sync state
        2. Notify sync started via WebSocket
        3. Fetch new rows from Google Sheet
        4. Apply column mapping
        5. Save to database
        6. Update sync state
        7. Notify completion/failure via WebSocket
        """
        pass
    
    async def preview_sheet(self, connection_id: str, rows: int) -> SheetPreviewResult:
        """Fetch preview data from sheet."""
        pass
```

#### Column Mapper (`app/services/business/sheet_crawler/column_mapper.py`)

```python
class ColumnMapper:
    def map_row(
        self,
        row: list[str],
        headers: list[str],
        mappings: list[ColumnMapping]
    ) -> dict:
        """
        Map a row of data using column mappings.
        Supports both column letters (A, B) and header names.
        """
        pass
    
    def convert_type(self, value: str, data_type: str) -> Any:
        """
        Convert string value to specified type.
        Returns original string if conversion fails.
        """
        pass
```

### 3. Infrastructure Layer

#### Google Sheet Client (`app/infrastructure/google_sheets/client.py`)

```python
class GoogleSheetClient:
    async def get_sheet_values(
        self,
        sheet_id: str,
        sheet_name: str,
        start_row: int = 1
    ) -> list[list[str]]:
        """Fetch values from sheet starting at row."""
        pass
    
    async def get_sheet_metadata(self, sheet_id: str) -> dict:
        """Get sheet title and available tabs."""
        pass
    
    async def check_access(self, sheet_id: str) -> bool:
        """Check if service account can access sheet."""
        pass
```

#### Token Bucket Rate Limiter (`app/infrastructure/google_sheets/rate_limiter.py`)

```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.monotonic()
    
    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens, blocking if insufficient.
        Refills tokens based on elapsed time.
        """
        pass


class GoogleSheetsRateLimiter:
    def __init__(self):
        # 300 requests per minute = 5 per second
        self.read_per_minute = TokenBucket(capacity=300, refill_rate=5.0)
        # 100 requests per 100 seconds = 1 per second
        self.requests_per_100s = TokenBucket(capacity=100, refill_rate=1.0)
        self.safety_factor = 0.8
    
    async def acquire(self, request_count: int = 1) -> None:
        """
        Acquire tokens from all buckets.
        Blocks until all buckets have sufficient tokens.
        """
        pass
```

### 4. Worker Layer

#### Sync Worker (`app/workers/sheet_sync_worker.py`)

```python
class SheetSyncWorker:
    REQUESTS_PER_SYNC = 2  # Each sync makes ~2 API requests
    MAX_RETRIES = 3
    
    def __init__(self):
        self.queue = RedisQueue()
        self.rate_limiter = GoogleSheetsRateLimiter()
        self.running = False
    
    async def start(self):
        """
        Main worker loop:
        1. Dequeue task
        2. Acquire rate limit tokens (blocks if needed)
        3. Process task
        4. Handle failures with retry
        """
        pass
    
    async def process_task(self, task: dict) -> None:
        """Process a single sync task."""
        pass
```

### 5. Repository Layer

#### Sheet Connection Repository (`app/repo/sheet_connection_repo.py`)

```python
class SheetConnectionRepository:
    async def create(self, user_id: str, data: CreateConnectionRequest) -> SheetConnection
    async def find_by_id(self, connection_id: str) -> Optional[SheetConnection]
    async def find_by_user_id(self, user_id: str) -> list[SheetConnection]
    async def find_all_enabled(self) -> list[SheetConnection]
    async def update(self, connection_id: str, data: UpdateConnectionRequest) -> SheetConnection
    async def delete(self, connection_id: str) -> None
```

#### Sheet Sync State Repository (`app/repo/sheet_sync_state_repo.py`)

```python
class SheetSyncStateRepository:
    async def find_by_connection_id(self, connection_id: str) -> Optional[SheetSyncState]
    async def update_state(
        self,
        connection_id: str,
        last_synced_row: int,
        status: SyncStatus,
        total_rows_synced: int,
        error_message: Optional[str] = None
    ) -> SheetSyncState
    async def delete_by_connection_id(self, connection_id: str) -> None
```

#### Sheet Data Repository (`app/repo/sheet_data_repo.py`)

```python
class SheetDataRepository:
    async def upsert(
        self,
        connection_id: str,
        row_number: int,
        data: dict,
        raw_data: dict
    ) -> SheetRawData
    async def find_by_connection_id(
        self,
        connection_id: str,
        page: int,
        page_size: int
    ) -> tuple[list[SheetRawData], int]
    async def delete_by_connection_id(self, connection_id: str) -> int
```

## Data Models

### Domain Models (`app/domain/models/sheet_connection.py`)

```python
class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    SUCCESS = "success"
    FAILED = "failed"


class ColumnMapping(BaseModel):
    system_field: str      # e.g., "product_name"
    sheet_column: str      # e.g., "A" or "Product Name"
    data_type: str = "string"  # string, number, integer, date
    required: bool = False


class SheetConnection(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    sheet_id: str
    sheet_name: str = "Sheet1"
    column_mappings: list[ColumnMapping]
    header_row: int = 1
    data_start_row: int = 2
    sync_enabled: bool = True
    created_at: datetime
    updated_at: datetime


class SheetSyncState(BaseModel):
    id: str = Field(alias="_id")
    connection_id: str
    last_synced_row: int = 0
    last_sync_time: Optional[datetime] = None
    status: SyncStatus = SyncStatus.PENDING
    error_message: Optional[str] = None
    total_rows_synced: int = 0
    created_at: datetime
    updated_at: datetime


class SheetRawData(BaseModel):
    id: str = Field(alias="_id")
    connection_id: str
    row_number: int
    data: dict          # Mapped data
    raw_data: dict      # Original row
    synced_at: datetime
```

### API Schemas (`app/domain/schemas/sheet_crawler.py`)

```python
# Request Schemas
class CreateConnectionRequest(BaseModel):
    sheet_id: str
    sheet_name: str = "Sheet1"
    column_mappings: list[ColumnMapping]
    header_row: int = Field(default=1, ge=1)
    data_start_row: int = Field(default=2, ge=1)


class UpdateConnectionRequest(BaseModel):
    sheet_name: Optional[str] = None
    column_mappings: Optional[list[ColumnMapping]] = None
    sync_enabled: Optional[bool] = None


# Response Schemas
class ConnectionResponse(BaseModel):
    id: str
    sheet_id: str
    sheet_name: str
    column_mappings: list[ColumnMapping]
    sync_enabled: bool
    created_at: datetime
    updated_at: datetime


class SyncStatusResponse(BaseModel):
    connection_id: str
    status: SyncStatus
    last_synced_row: int
    last_sync_time: Optional[datetime]
    total_rows_synced: int
    error_message: Optional[str]


class SheetPreviewResponse(BaseModel):
    headers: list[str]
    rows: list[dict]
    total_rows: int


class SheetDataResponse(BaseModel):
    data: list[dict]
    total: int
    page: int
    page_size: int


class ServiceAccountInfoResponse(BaseModel):
    email: str
    instructions: str
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Connection Creation Round Trip

*For any* valid CreateConnectionRequest, creating a connection and then retrieving it by ID should return an equivalent connection with all fields preserved.

**Validates: Requirements 2.1, 2.4**

### Property 2: User Connection Isolation

*For any* user, listing connections should return only connections where user_id matches that user, and the count should equal the number of connections created by that user.

**Validates: Requirements 2.3, 2.5**

### Property 3: Connection Update Preservation

*For any* connection and valid UpdateConnectionRequest, updating the connection should result in the updated fields being changed while other fields remain unchanged.

**Validates: Requirements 2.6**

### Property 4: Cascade Delete Completeness

*For any* connection with associated sync state and raw data, deleting the connection should result in zero documents remaining for that connection_id in all three collections.

**Validates: Requirements 2.7**

### Property 5: Column Mapping Flexibility

*For any* column mapping with sheet_column as either a letter (A-Z) or a header name, the mapper should correctly identify the column index and extract the value.

**Validates: Requirements 3.1**

### Property 6: Type Conversion with Fallback

*For any* value and target data_type, conversion should either produce a value of the correct type or return the original string value (never throw an exception).

**Validates: Requirements 3.3, 3.4**

### Property 7: Preview Row Limit

*For any* preview request with rows parameter N, the response should contain at most min(N, 50) data rows.

**Validates: Requirements 4.2**

### Property 8: Sync Task Enqueue

*For any* manual sync trigger or scheduled trigger, the corresponding connection_id should be added to the Redis queue.

**Validates: Requirements 5.1, 6.2**

### Property 9: WebSocket Notification Completeness

*For any* sync operation (success or failure), exactly one terminal WebSocket event should be emitted (either "sheet:sync:completed" or "sheet:sync:failed").

**Validates: Requirements 5.3, 5.4, 5.5, 12.1, 12.2, 12.3**

### Property 10: Incremental Sync Correctness

*For any* sync operation where last_synced_row is N, the sync should only process rows with row_number > N, and after completion last_synced_row should equal the highest processed row number.

**Validates: Requirements 7.1, 7.3**

### Property 11: Token Bucket Refill Rate

*For any* Token Bucket with capacity C and refill_rate R, after consuming all tokens and waiting time T seconds, available tokens should be min(C, R * T).

**Validates: Requirements 8.1, 8.2, 8.4**

### Property 12: Token Bucket Blocking Behavior

*For any* acquire request for N tokens when available tokens < N, the acquire should block until sufficient tokens are available through refill.

**Validates: Requirements 8.3**

### Property 13: Worker Retry Limit

*For any* failed task with retry_count < 3, the task should be re-queued with retry_count + 1. For retry_count >= 3, the task should not be re-queued.

**Validates: Requirements 9.3, 9.4**

### Property 14: Pagination Correctness

*For any* data retrieval with page P and page_size S, the response should contain at most S records, and records should be from offset (P-1)*S.

**Validates: Requirements 10.1, 10.2, 10.3**

### Property 15: Data Upsert Idempotency

*For any* row synced multiple times with the same row_number, there should be exactly one document in sheet_raw_data for that (connection_id, row_number) pair.

**Validates: Requirements 14.3**

## Error Handling

### API Errors

| Error | HTTP Status | Response |
|-------|-------------|----------|
| Sheet not accessible | 400 | `{"detail": "Cannot access sheet. Please share with {email}"}` |
| Connection not found | 404 | `{"detail": "Connection not found"}` |
| Invalid API key | 401 | `{"detail": "Invalid API key"}` |
| Validation error | 422 | Pydantic validation errors |

### Sync Errors

| Error | Handling |
|-------|----------|
| Sheet inaccessible | Update sync state with error, notify via WebSocket |
| Rate limit exceeded | Token bucket handles waiting, no error |
| Network error | Retry up to 3 times, then fail |
| Invalid data format | Log warning, skip row, continue sync |

### Worker Errors

| Error | Handling |
|-------|----------|
| Task processing failure | Re-queue with retry_count + 1 (max 3) |
| MongoDB connection lost | Reconnect and retry |
| Redis connection lost | Exit worker, supervisor restarts |

## Testing Strategy

### Unit Tests

Unit tests verify specific examples and edge cases:

- Column mapper with various column formats (A, B, "Product Name")
- Type conversion for each data type
- Token bucket token calculation
- Pagination offset calculation

### Property-Based Tests

Property-based tests verify universal properties across all inputs using the `hypothesis` library (already in requirements.txt):

- Each property from the Correctness Properties section should have a corresponding property test
- Minimum 100 iterations per property test
- Tests should be tagged with: `# Feature: google-sheet-crawler, Property N: {property_text}`

### Integration Tests

- API endpoint tests with test database
- Worker processing with mock Google Sheets client
- WebSocket notification delivery

### Test Configuration

```python
# pytest configuration for property tests
from hypothesis import settings, Phase

settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=10)
```

## Configuration

### Environment Variables

```python
# app/config/settings.py additions

# Internal API
INTERNAL_API_KEY: str  # API key for Cloud Scheduler

# Google Sheets
GOOGLE_SERVICE_ACCOUNT_JSON: str  # Service account credentials JSON
GOOGLE_SERVICE_ACCOUNT_EMAIL: str  # Email to display to users

# Sheet Crawler
SHEET_SYNC_QUEUE_NAME: str = "sheet_sync_tasks"

# Redis (existing)
REDIS_URL: str = "redis://localhost:6379"
```

### Dependencies

```
# requirements.txt additions
gspread
gspread-asyncio
google-auth
python-dateutil
```

## Folder Structure

```
app/
├── api/v1/
│   ├── internal/
│   │   ├── __init__.py
│   │   └── router.py              # Internal API (Cloud Scheduler)
│   └── sheet_crawler/
│       ├── __init__.py
│       └── router.py              # Public API
│
├── domain/
│   ├── models/
│   │   └── sheet_connection.py    # Domain models
│   └── schemas/
│       └── sheet_crawler.py       # API schemas
│
├── repo/
│   ├── sheet_connection_repo.py
│   ├── sheet_sync_state_repo.py
│   └── sheet_data_repo.py
│
├── services/
│   └── business/
│       └── sheet_crawler/
│           ├── __init__.py
│           ├── crawler_service.py
│           └── column_mapper.py
│
├── infrastructure/
│   └── google_sheets/
│       ├── __init__.py
│       ├── client.py              # Google Sheets client
│       └── rate_limiter.py        # Token Bucket implementation
│
├── workers/
│   └── sheet_sync_worker.py       # Worker process
│
└── common/
    ├── repo.py                    # Add sheet repos
    └── service.py                 # Add sheet services
```
