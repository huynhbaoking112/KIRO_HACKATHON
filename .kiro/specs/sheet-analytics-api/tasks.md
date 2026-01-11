# Implementation Plan: Sheet Analytics API

## Overview

Implementation plan cho tính năng Sheet Analytics API với caching và strategy pattern. Tasks được sắp xếp theo thứ tự dependencies: Schemas → Repository → Service → API → Integration.

## Tasks

- [x] 1. Create Analytics Schemas
  - [x] 1.1 Create analytics schemas
    - Create `app/domain/schemas/analytics.py`
    - Define `SheetType` enum with values: orders, order_items, customers, products
    - Define enums: `Granularity`, `TimeSeriesMetrics`, `TopMetric`, `SortOrder`
    - Define response schemas: `OrdersSummaryResponse`, `OrderItemsSummaryResponse`, `SimpleSummaryResponse`
    - Define `TimeSeriesResponse`, `DistributionResponse`, `TopResponse`, `DataResponse`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 4.1, 5.1, 6.9_

- [x] 2. Implement Repository Layer
  - [x] 2.1 Create analytics repository
    - Create `app/repo/analytics_repo.py`
    - Implement `AnalyticsRepository` class with `aggregate` method
    - Implement `find_with_search` method for paginated search/filter
    - _Requirements: 2.1, 6.1, 6.6_
  - [x] 2.2 Update common/repo.py
    - Add `get_analytics_repo` factory function
    - _Requirements: 2.1_

- [x] 3. Implement Service Layer
  - [x] 3.1 Create sheet type detector
    - Create `app/services/analytics/__init__.py`
    - Create `app/services/analytics/sheet_type_detector.py`
    - Implement `detect_sheet_type(sheet_name: str) -> SheetType` function
    - Match sheet_name case-insensitively to detect type
    - Default to "orders" if no match
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_
  - [x] 3.2 Create cache manager
    - Create `app/services/analytics/cache_manager.py`
    - Implement `AnalyticsCacheManager` with `get`, `set`, `invalidate` methods
    - Implement cache key building with params hash
    - _Requirements: 7.1, 7.2, 7.3_
  - [ ]* 3.3 Write property tests for cache manager
    - **Property 11: Cache Key Uniqueness**
    - **Property 12: Cache Invalidation Completeness**
    - **Validates: Requirements 7.2, 7.3**
  - [x] 3.4 Create analytics strategies
    - Create `app/services/analytics/strategies.py`
    - Implement `BaseAnalyticsStrategy` abstract class
    - Implement `OrdersAnalyticsStrategy` with summary, time-series, distribution, top pipelines
    - Implement `OrderItemsAnalyticsStrategy` with summary, top pipelines
    - Implement `CustomersAnalyticsStrategy` with summary pipeline
    - Implement `ProductsAnalyticsStrategy` with summary pipeline
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 4.1, 5.1, 5.2_
  - [ ]* 3.5 Write property tests for strategies
    - **Property 1: Sheet Type Metrics Consistency**
    - **Property 5: Distribution Percentage Sum**
    - **Property 6: Top N Ordering**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 4.5, 5.3, 5.4, 5.5**
  - [x] 3.6 Create analytics service
    - Create `app/services/analytics/analytics_service.py`
    - Implement `AnalyticsService` class
    - Use `detect_sheet_type` to determine sheet type from connection's sheet_name
    - Implement `get_summary` method with caching
    - Implement `get_time_series` method with caching
    - Implement `get_distribution` method with caching
    - Implement `get_top` method with caching
    - Implement `get_data` method with search/filter/sort
    - _Requirements: 1.5, 2.1, 2.5, 3.1, 4.1, 5.1, 6.1, 6.6, 7.4, 7.5_
  - [ ]* 3.7 Write property tests for analytics service
    - **Property 2: Date Filter Correctness**
    - **Property 3: Time Series Granularity Grouping**
    - **Property 4: Time Series Metrics Selection**
    - **Property 7: Top N Limit Compliance**
    - **Property 8: Search Result Relevance**
    - **Property 9: Sort Order Correctness**
    - **Property 10: Pagination Correctness**
    - **Validates: Requirements 2.5, 3.1, 3.4, 3.5, 3.6, 5.7, 6.1, 6.6, 6.9**
  - [x] 3.8 Update common/service.py
    - Add `get_analytics_service` factory function
    - Add `get_analytics_cache_manager` factory function
    - _Requirements: 2.1_

- [ ] 4. Checkpoint - Core Logic Complete
  - Ensure all unit tests pass
  - Verify strategies return correct metrics for each sheet type
  - Ask the user if questions arise

- [x] 5. Implement API Layer
  - [x] 5.1 Create analytics router
    - Create `app/api/v1/analytics/__init__.py`
    - Create `app/api/v1/analytics/router.py`
    - Implement `GET /{connection_id}/summary` endpoint
    - Implement `GET /{connection_id}/time-series` endpoint
    - Implement `GET /{connection_id}/distribution/{field}` endpoint
    - Implement `GET /{connection_id}/top/{field}` endpoint
    - Implement `GET /{connection_id}/data` endpoint
    - Add access control verification for all endpoints
    - _Requirements: 2.1, 3.1, 4.1, 5.1, 6.1, 8.1, 8.2, 8.3_
  - [ ]* 5.2 Write property tests for API endpoints
    - **Property 13: Access Control Enforcement**
    - **Property 14: Date Range Validation**
    - **Property 15: Sheet Type Feature Restriction**
    - **Validates: Requirements 8.1, 8.2, 9.1, 3.7, 4.3, 5.8**
  - [x] 5.3 Register analytics router
    - Update `app/api/v1/router.py` to include analytics router
    - _Requirements: 2.1_

- [ ] 6. Integrate Cache Invalidation
  - [ ] 6.1 Update crawler service for cache invalidation
    - Update `app/services/sheet_crawler/crawler_service.py`
    - Call `cache_manager.invalidate(connection_id)` after successful sync
    - _Requirements: 7.3_

- [ ] 7. Final Checkpoint
  - Ensure all tests pass
  - Verify end-to-end flow: Create connection → Sync → Analytics API (auto-detect sheet type from sheet_name)
  - Test caching behavior (hit/miss/invalidation)
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Cache invalidation is critical - must be called after every successful sync
- Sheet type is auto-detected from sheet_name (case-insensitive): Orders, Order_Items, Customers, Products
- No changes needed to existing SheetConnection model or CreateConnectionRequest
