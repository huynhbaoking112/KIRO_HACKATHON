# Design Document: Sheet Analytics API

## Overview

Tính năng Sheet Analytics API mở rộng hệ thống Google Sheet Crawler hiện có bằng cách thêm các endpoint analytics để hỗ trợ dashboard visualizations. API sử dụng kiến trúc layered với caching để tối ưu performance.

### Key Design Decisions

1. **Hybrid API Pattern**: Pre-defined endpoints cho common metrics + flexible data endpoint với search/filter
2. **Redis Caching**: Cache aggregated results với TTL 5 phút, invalidate khi sync hoàn thành
3. **Sheet Type Aware**: Mỗi sheet type có metrics và capabilities riêng
4. **MongoDB Aggregation Pipeline**: Sử dụng aggregation framework cho performance

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Frontend Dashboard                               │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                   │
│   │ Summary │  │  Time   │  │  Dist   │  │  Top N  │                   │
│   │  Cards  │  │ Series  │  │ Charts  │  │ Charts  │                   │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘                   │
└────────┼────────────┼────────────┼────────────┼─────────────────────────┘
         │            │            │            │
         ▼            ▼            ▼            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                              │
│                                                                          │
│   Analytics Router (/api/v1/analytics/{connection_id}/*)                │
│   ├── GET /summary                                                      │
│   ├── GET /time-series                                                  │
│   ├── GET /distribution/{field}                                         │
│   ├── GET /top/{field}                                                  │
│   └── GET /data                                                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Analytics Service                                │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Cache Manager                                 │   │
│   │   Check Redis → Hit? Return cached                              │   │
│   │                → Miss? Query → Compute → Cache → Return         │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                              │                                           │
│                              ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │              Sheet Type Strategy                                 │   │
│   │   ├── OrdersAnalytics                                           │   │
│   │   ├── OrderItemsAnalytics                                       │   │
│   │   ├── CustomersAnalytics                                        │   │
│   │   └── ProductsAnalytics                                         │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Data Layer                                       │
│                                                                          │
│   ┌─────────────────┐              ┌─────────────────┐                  │
│   │     Redis       │              │     MongoDB     │                  │
│   │   (Cache)       │              │  (sheet_raw_    │                  │
│   │                 │              │   data)         │                  │
│   └─────────────────┘              └─────────────────┘                  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### 1. API Layer

#### Analytics Router (`app/api/v1/analytics/router.py`)

```python
router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/{connection_id}/summary")
async def get_summary(
    connection_id: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
) -> SummaryResponse:
    """Get summary metrics for a connection."""
    pass

@router.get("/{connection_id}/time-series")
async def get_time_series(
    connection_id: str,
    date_from: date,
    date_to: date,
    granularity: Granularity = Granularity.DAY,
    metrics: TimeSeriesMetrics = TimeSeriesMetrics.BOTH,
    current_user: User = Depends(get_current_active_user),
) -> TimeSeriesResponse:
    """Get time series data for orders sheet."""
    pass

@router.get("/{connection_id}/distribution/{field}")
async def get_distribution(
    connection_id: str,
    field: DistributionField,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user: User = Depends(get_current_active_user),
) -> DistributionResponse:
    """Get distribution data for a field."""
    pass

@router.get("/{connection_id}/top/{field}")
async def get_top(
    connection_id: str,
    field: str,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: int = Query(default=10, ge=1, le=50),
    metric: TopMetric = TopMetric.AMOUNT,
    current_user: User = Depends(get_current_active_user),
) -> TopResponse:
    """Get top N items by field."""
    pass

@router.get("/{connection_id}/data")
async def get_data(
    connection_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: SortOrder = SortOrder.DESC,
    current_user: User = Depends(get_current_active_user),
) -> DataResponse:
    """Get paginated data with search and filter."""
    pass
```

### 2. Service Layer

#### Analytics Service (`app/services/business/analytics/analytics_service.py`)

```python
class AnalyticsService:
    def __init__(
        self,
        connection_repo: SheetConnectionRepository,
        data_repo: SheetDataRepository,
        cache_manager: AnalyticsCacheManager,
    ):
        self.connection_repo = connection_repo
        self.data_repo = data_repo
        self.cache_manager = cache_manager
        self.strategies = {
            SheetType.ORDERS: OrdersAnalyticsStrategy(),
            SheetType.ORDER_ITEMS: OrderItemsAnalyticsStrategy(),
            SheetType.CUSTOMERS: CustomersAnalyticsStrategy(),
            SheetType.PRODUCTS: ProductsAnalyticsStrategy(),
        }
    
    async def get_summary(
        self,
        connection_id: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> dict:
        """Get summary metrics using appropriate strategy."""
        pass
    
    async def get_time_series(
        self,
        connection_id: str,
        date_from: date,
        date_to: date,
        granularity: Granularity,
        metrics: TimeSeriesMetrics,
    ) -> dict:
        """Get time series data (orders only)."""
        pass
    
    async def get_distribution(
        self,
        connection_id: str,
        field: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> dict:
        """Get distribution data (orders only)."""
        pass
    
    async def get_top(
        self,
        connection_id: str,
        field: str,
        limit: int,
        metric: str,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> dict:
        """Get top N items."""
        pass
    
    async def get_data(
        self,
        connection_id: str,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> dict:
        """Get paginated data with search/filter."""
        pass
```

#### Analytics Strategy (`app/services/business/analytics/strategies.py`)

```python
class BaseAnalyticsStrategy(ABC):
    """Base class for sheet type specific analytics."""
    
    @abstractmethod
    def get_summary_pipeline(
        self,
        connection_id: str,
        date_from: Optional[date],
        date_to: Optional[date],
    ) -> list[dict]:
        """Return MongoDB aggregation pipeline for summary."""
        pass
    
    @abstractmethod
    def get_searchable_fields(self) -> list[str]:
        """Return list of fields that can be searched."""
        pass
    
    @abstractmethod
    def get_sortable_fields(self) -> list[str]:
        """Return list of fields that can be sorted."""
        pass
    
    def supports_time_series(self) -> bool:
        return False
    
    def supports_distribution(self) -> bool:
        return False
    
    def get_distribution_fields(self) -> list[str]:
        return []
    
    def supports_top(self) -> bool:
        return False
    
    def get_top_fields(self) -> list[str]:
        return []


class OrdersAnalyticsStrategy(BaseAnalyticsStrategy):
    """Analytics strategy for orders sheet."""
    
    def get_summary_pipeline(self, connection_id, date_from, date_to):
        match_stage = {"connection_id": connection_id}
        if date_from or date_to:
            match_stage["data.order_date"] = {}
            if date_from:
                match_stage["data.order_date"]["$gte"] = date_from.isoformat()
            if date_to:
                match_stage["data.order_date"]["$lte"] = date_to.isoformat()
        
        return [
            {"$match": match_stage},
            {"$group": {
                "_id": None,
                "total_count": {"$sum": 1},
                "total_amount": {"$sum": {"$toDouble": "$data.total_amount"}},
                "avg_amount": {"$avg": {"$toDouble": "$data.total_amount"}},
            }}
        ]
    
    def get_searchable_fields(self):
        return ["order_id", "platform", "order_status", "customer_id"]
    
    def get_sortable_fields(self):
        return ["order_id", "platform", "order_status", "order_date", "subtotal", "total_amount"]
    
    def supports_time_series(self):
        return True
    
    def supports_distribution(self):
        return True
    
    def get_distribution_fields(self):
        return ["platform", "order_status"]
    
    def supports_top(self):
        return True
    
    def get_top_fields(self):
        return ["platform"]


class OrderItemsAnalyticsStrategy(BaseAnalyticsStrategy):
    """Analytics strategy for order_items sheet."""
    
    def get_summary_pipeline(self, connection_id, date_from, date_to):
        return [
            {"$match": {"connection_id": connection_id}},
            {"$group": {
                "_id": None,
                "total_quantity": {"$sum": {"$toDouble": "$data.quantity"}},
                "total_line_total": {"$sum": {"$toDouble": "$data.line_total"}},
                "unique_products": {"$addToSet": "$data.product_id"},
            }},
            {"$project": {
                "total_quantity": 1,
                "total_line_total": 1,
                "unique_products": {"$size": "$unique_products"},
            }}
        ]
    
    def get_searchable_fields(self):
        return ["order_item_id", "order_id", "product_id", "product_name"]
    
    def get_sortable_fields(self):
        return ["order_item_id", "order_id", "product_id", "product_name", "quantity", "unit_price", "final_price", "line_total"]
    
    def supports_top(self):
        return True
    
    def get_top_fields(self):
        return ["product_name"]


class CustomersAnalyticsStrategy(BaseAnalyticsStrategy):
    """Analytics strategy for customers sheet."""
    
    def get_summary_pipeline(self, connection_id, date_from, date_to):
        return [
            {"$match": {"connection_id": connection_id}},
            {"$count": "total_count"}
        ]
    
    def get_searchable_fields(self):
        return ["customer_id", "customer_name", "phone"]
    
    def get_sortable_fields(self):
        return ["customer_id", "customer_name", "phone"]


class ProductsAnalyticsStrategy(BaseAnalyticsStrategy):
    """Analytics strategy for products sheet."""
    
    def get_summary_pipeline(self, connection_id, date_from, date_to):
        return [
            {"$match": {"connection_id": connection_id}},
            {"$count": "total_count"}
        ]
    
    def get_searchable_fields(self):
        return ["product_id", "product_name"]
    
    def get_sortable_fields(self):
        return ["product_id", "product_name"]
```

### 3. Cache Layer

#### Cache Manager (`app/services/business/analytics/cache_manager.py`)

```python
class AnalyticsCacheManager:
    """Manages Redis caching for analytics data."""
    
    CACHE_TTL = 300  # 5 minutes
    KEY_PREFIX = "analytics"
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    def _build_key(
        self,
        connection_id: str,
        endpoint: str,
        params: dict,
    ) -> str:
        """Build cache key from connection_id, endpoint, and params."""
        params_hash = hashlib.md5(
            json.dumps(params, sort_keys=True).encode()
        ).hexdigest()[:8]
        return f"{self.KEY_PREFIX}:{connection_id}:{endpoint}:{params_hash}"
    
    async def get(
        self,
        connection_id: str,
        endpoint: str,
        params: dict,
    ) -> Optional[dict]:
        """Get cached data if exists."""
        key = self._build_key(connection_id, endpoint, params)
        data = await self.redis.get(key)
        if data:
            return json.loads(data)
        return None
    
    async def set(
        self,
        connection_id: str,
        endpoint: str,
        params: dict,
        data: dict,
    ) -> None:
        """Cache data with TTL."""
        key = self._build_key(connection_id, endpoint, params)
        await self.redis.setex(key, self.CACHE_TTL, json.dumps(data))
    
    async def invalidate(self, connection_id: str) -> int:
        """Invalidate all cache entries for a connection."""
        pattern = f"{self.KEY_PREFIX}:{connection_id}:*"
        keys = await self.redis.keys(pattern)
        if keys:
            return await self.redis.delete(*keys)
        return 0
```

### 4. Repository Layer

#### Analytics Repository (`app/repo/analytics_repo.py`)

```python
class AnalyticsRepository:
    """Repository for analytics aggregation queries."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.sheet_raw_data
    
    async def aggregate(self, pipeline: list[dict]) -> list[dict]:
        """Execute aggregation pipeline."""
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)
    
    async def find_with_search(
        self,
        connection_id: str,
        search: Optional[str],
        search_fields: list[str],
        date_field: Optional[str],
        date_from: Optional[date],
        date_to: Optional[date],
        sort_by: Optional[str],
        sort_order: int,
        skip: int,
        limit: int,
    ) -> tuple[list[dict], int]:
        """Find documents with search, filter, and pagination."""
        query = {"connection_id": connection_id}
        
        # Add search condition
        if search and search_fields:
            search_conditions = [
                {f"data.{field}": {"$regex": search, "$options": "i"}}
                for field in search_fields
            ]
            query["$or"] = search_conditions
        
        # Add date filter
        if date_field and (date_from or date_to):
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from.isoformat()
            if date_to:
                date_query["$lte"] = date_to.isoformat()
            query[f"data.{date_field}"] = date_query
        
        # Get total count
        total = await self.collection.count_documents(query)
        
        # Build sort
        sort_field = f"data.{sort_by}" if sort_by else "row_number"
        
        # Get paginated results
        cursor = (
            self.collection.find(query)
            .sort(sort_field, sort_order)
            .skip(skip)
            .limit(limit)
        )
        
        results = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            results.append(doc)
        
        return results, total
```

## Data Models

### Sheet Type Detection

Sheet type is automatically detected from `sheet_name` field (case-insensitive matching):

| sheet_name | Detected Type |
|------------|---------------|
| "Orders" | orders |
| "Order_Items" | order_items |
| "Customers" | customers |
| "Products" | products |
| Other | orders (default) |

#### Sheet Type Detector (`app/services/business/analytics/sheet_type_detector.py`)

```python
class SheetType(str, Enum):
    """Type of sheet being synced."""
    ORDERS = "orders"
    ORDER_ITEMS = "order_items"
    CUSTOMERS = "customers"
    PRODUCTS = "products"


def detect_sheet_type(sheet_name: str) -> SheetType:
    """Detect sheet type from sheet name (case-insensitive)."""
    name_lower = sheet_name.lower().strip()
    
    if name_lower == "orders":
        return SheetType.ORDERS
    elif name_lower == "order_items":
        return SheetType.ORDER_ITEMS
    elif name_lower == "customers":
        return SheetType.CUSTOMERS
    elif name_lower == "products":
        return SheetType.PRODUCTS
    else:
        return SheetType.ORDERS  # Default
```

### Analytics Schemas (`app/domain/schemas/analytics.py`)

```python
from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Granularity(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class TimeSeriesMetrics(str, Enum):
    COUNT = "count"
    AMOUNT = "amount"
    BOTH = "both"


class TopMetric(str, Enum):
    COUNT = "count"
    AMOUNT = "amount"
    QUANTITY = "quantity"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


# Summary Response - varies by sheet type
class OrdersSummaryResponse(BaseModel):
    total_count: int
    total_amount: float
    avg_amount: float


class OrderItemsSummaryResponse(BaseModel):
    total_quantity: int
    total_line_total: float
    unique_products: int


class SimpleSummaryResponse(BaseModel):
    total_count: int


# Time Series Response
class TimeSeriesDataPoint(BaseModel):
    date: str
    count: Optional[int] = None
    total_amount: Optional[float] = None


class TimeSeriesResponse(BaseModel):
    granularity: Granularity
    data: list[TimeSeriesDataPoint]


# Distribution Response
class DistributionDataPoint(BaseModel):
    value: str
    count: int
    percentage: float


class DistributionResponse(BaseModel):
    field: str
    data: list[DistributionDataPoint]


# Top Response
class TopDataPoint(BaseModel):
    value: str
    count: int
    total_amount: Optional[float] = None
    total_quantity: Optional[int] = None


class TopResponse(BaseModel):
    field: str
    metric: str
    data: list[TopDataPoint]


# Data Response
class DataResponse(BaseModel):
    data: list[dict]
    total: int
    page: int
    page_size: int
    total_pages: int
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Sheet Type Metrics Consistency

*For any* connection with a specific sheet_type, requesting summary should return exactly the fields defined for that sheet type (orders: total_count, total_amount, avg_amount; order_items: total_quantity, total_line_total, unique_products; customers/products: total_count).

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 2: Date Filter Correctness

*For any* orders connection with date_from and date_to parameters, all data included in summary/time-series/distribution calculations should have order_date within the specified range.

**Validates: Requirements 2.5, 3.1, 4.4, 6.8**

### Property 3: Time Series Granularity Grouping

*For any* time-series request with granularity G, each data point's date should represent the start of a period of granularity G, and no two data points should have the same date.

**Validates: Requirements 3.1, 3.2**

### Property 4: Time Series Metrics Selection

*For any* time-series request with metrics parameter M, the response should contain only the fields specified by M (count only, amount only, or both).

**Validates: Requirements 3.4, 3.5, 3.6**

### Property 5: Distribution Percentage Sum

*For any* distribution response, the sum of all percentages should equal 100.0 (within floating point tolerance of 0.1).

**Validates: Requirements 4.5**

### Property 6: Top N Ordering

*For any* top N response sorted by metric M, each item's value for M should be greater than or equal to the next item's value for M.

**Validates: Requirements 5.3, 5.4, 5.5**

### Property 7: Top N Limit Compliance

*For any* top N request with limit L, the response should contain at most L items.

**Validates: Requirements 5.1, 5.2, 5.7**

### Property 8: Search Result Relevance

*For any* data request with search parameter S, all returned items should contain S (case-insensitive) in at least one of the searchable fields for that sheet type.

**Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5**

### Property 9: Sort Order Correctness

*For any* data request with sort_by field F and sort_order O, the results should be sorted by F in order O.

**Validates: Requirements 6.6**

### Property 10: Pagination Correctness

*For any* data request with page P and page_size S, total_pages should equal ceil(total / S), and the number of returned items should be min(S, total - (P-1)*S).

**Validates: Requirements 6.9**

### Property 11: Cache Key Uniqueness

*For any* two requests with different parameters, the cache keys should be different.

**Validates: Requirements 7.2**

### Property 12: Cache Invalidation Completeness

*For any* connection after sync completion, all cache entries for that connection should be deleted.

**Validates: Requirements 7.3**

### Property 13: Access Control Enforcement

*For any* analytics request, the user should only receive data for connections they own.

**Validates: Requirements 8.1, 8.2**

### Property 14: Date Range Validation

*For any* request where date_from > date_to, the system should return a 400 error.

**Validates: Requirements 9.1**

### Property 15: Sheet Type Feature Restriction

*For any* non-orders sheet, requesting time-series or distribution should return a 400 error. For customers/products sheets, requesting top should return a 400 error.

**Validates: Requirements 3.7, 4.3, 5.8**

## Error Handling

### API Errors

| Error | HTTP Status | Response |
|-------|-------------|----------|
| Invalid date range | 400 | `{"detail": "Invalid date range: date_from must be before date_to"}` |
| Field not supported | 400 | `{"detail": "Field '{field}' not supported for sheet type '{type}'"}` |
| Feature not supported | 400 | `{"detail": "Time series not supported for sheet type '{type}'"}` |
| Connection not found | 404 | `{"detail": "Connection not found"}` |
| Validation error | 422 | Pydantic validation errors |

### Cache Errors

| Error | Handling |
|-------|----------|
| Redis connection lost | Log warning, bypass cache, query database directly |
| Cache serialization error | Log error, bypass cache |

## Testing Strategy

### Unit Tests

Unit tests verify specific examples and edge cases:

- Summary calculation for each sheet type
- Date filtering logic
- Granularity grouping (day/week/month/year)
- Percentage calculation rounding
- Cache key generation
- Search query building

### Property-Based Tests

Property-based tests verify universal properties across all inputs using the `hypothesis` library:

- Each property from the Correctness Properties section should have a corresponding property test
- Minimum 100 iterations per property test
- Tests should be tagged with: `# Feature: sheet-analytics-api, Property N: {property_text}`

### Integration Tests

- API endpoint tests with test database
- Cache hit/miss scenarios
- Access control verification
- End-to-end analytics flow

### Test Configuration

```python
# pytest configuration for property tests
from hypothesis import settings, Phase

settings.register_profile("ci", max_examples=100)
settings.register_profile("dev", max_examples=10)
```

## Configuration

### Environment Variables

No new environment variables required. Uses existing:
- `REDIS_URL` - For caching
- `MONGODB_URL` - For data queries

### Dependencies

No new dependencies required. Uses existing:
- `redis` - For caching
- `motor` - For MongoDB async operations

## Folder Structure

```
app/
├── api/v1/
│   └── analytics/
│       ├── __init__.py
│       └── router.py              # Analytics API endpoints
│
├── domain/
│   └── schemas/
│       ├── sheet_crawler.py       # Update: Add SheetType enum
│       └── analytics.py           # NEW: Analytics schemas
│
├── repo/
│   └── analytics_repo.py          # NEW: Analytics aggregation queries
│
├── services/
│   └── business/
│       └── analytics/
│           ├── __init__.py
│           ├── analytics_service.py   # Main analytics service
│           ├── strategies.py          # Sheet type strategies
│           └── cache_manager.py       # Redis cache manager
│
└── common/
    ├── repo.py                    # Add get_analytics_repo
    └── service.py                 # Add get_analytics_service
```

## API Endpoints Summary

### Base URL: `/api/v1/analytics/{connection_id}`

| Endpoint | Method | Description | Sheet Types |
|----------|--------|-------------|-------------|
| `/summary` | GET | Summary metrics | All |
| `/time-series` | GET | Time-based aggregation | Orders only |
| `/distribution/{field}` | GET | Field value distribution | Orders only |
| `/top/{field}` | GET | Top N by field | Orders, Order Items |
| `/data` | GET | Paginated raw data with search/filter | All |

### Query Parameters Reference

| Parameter | Type | Endpoints | Description |
|-----------|------|-----------|-------------|
| `date_from` | date | All (orders only) | Start date filter |
| `date_to` | date | All (orders only) | End date filter |
| `granularity` | enum | time-series | day/week/month/year |
| `metrics` | enum | time-series | count/amount/both |
| `limit` | int | top | 1-50, default 10 |
| `metric` | enum | top | count/amount/quantity |
| `page` | int | data | Page number, default 1 |
| `page_size` | int | data | 1-100, default 20 |
| `search` | string | data | Search query |
| `sort_by` | string | data | Sort field |
| `sort_order` | enum | data | asc/desc |
