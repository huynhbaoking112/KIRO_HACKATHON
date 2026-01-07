# Implementation Plan: Google Sheet Crawler

## Overview

Implementation plan cho tính năng Google Sheet Crawler với queue-based architecture và Token Bucket rate limiting. Tasks được sắp xếp theo thứ tự dependencies: Domain Models → Infrastructure → Repository → Service → API → Worker.

## Tasks

- [x] 1. Setup Domain Models và Schemas
  - [x] 1.1 Create domain models for sheet connection
    - Create `app/domain/models/sheet_connection.py`
    - Define `SyncStatus` enum, `ColumnMapping`, `SheetConnection`, `SheetSyncState`, `SheetRawData` models
    - _Requirements: 2.1, 7.3, 14.2_
  - [x] 1.2 Create API schemas for sheet crawler
    - Create `app/domain/schemas/sheet_crawler.py`
    - Define request schemas: `CreateConnectionRequest`, `UpdateConnectionRequest`
    - Define response schemas: `ConnectionResponse`, `SyncStatusResponse`, `SheetPreviewResponse`, `SheetDataResponse`, `ServiceAccountInfoResponse`
    - _Requirements: 1.1, 1.2, 2.1, 10.1, 11.1_

- [x] 2. Setup Configuration
  - [x] 2.1 Add new settings to config
    - Update `app/config/settings.py` with Google Sheets and internal API settings
    - Add: `INTERNAL_API_KEY`, `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_SERVICE_ACCOUNT_EMAIL`, `SHEET_SYNC_QUEUE_NAME`, `REDIS_URL`
    - _Requirements: 6.3, 13.1_
  - [x] 2.2 Update requirements.txt
    - Add: `gspread`, `gspread-asyncio`, `google-auth`, `python-dateutil`
    - _Requirements: 13.1_

- [x] 3. Implement Infrastructure Layer
  - [x] 3.1 Implement Token Bucket Rate Limiter
    - Create `app/infrastructure/google_sheets/__init__.py`
    - Create `app/infrastructure/google_sheets/rate_limiter.py`
    - Implement `TokenBucket` class with capacity, refill_rate, acquire method
    - Implement `GoogleSheetsRateLimiter` with two buckets (300/min, 100/100s)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - [ ]* 3.2 Write property tests for Token Bucket
    - **Property 11: Token Bucket Refill Rate**
    - **Property 12: Token Bucket Blocking Behavior**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**
  - [x] 3.3 Implement Google Sheet Client
    - Create `app/infrastructure/google_sheets/client.py`
    - Implement `GoogleSheetClient` with service account authentication
    - Implement `get_sheet_values`, `get_sheet_metadata`, `check_access` methods
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [x] 4. Implement Repository Layer
  - [x] 4.1 Implement Sheet Connection Repository
    - Create `app/repo/sheet_connection_repo.py`
    - Implement CRUD operations: `create`, `find_by_id`, `find_by_user_id`, `find_all_enabled`, `update`, `delete`
    - _Requirements: 2.1, 2.3, 2.4, 2.6, 2.7, 6.2_
  - [x] 4.2 Implement Sheet Sync State Repository
    - Create `app/repo/sheet_sync_state_repo.py`
    - Implement `find_by_connection_id`, `update_state`, `delete_by_connection_id`
    - _Requirements: 7.3, 7.4, 11.1_
  - [x] 4.3 Implement Sheet Data Repository
    - Create `app/repo/sheet_data_repo.py`
    - Implement `upsert`, `find_by_connection_id` (with pagination), `delete_by_connection_id`
    - _Requirements: 10.1, 10.2, 14.1, 14.3_
  - [ ]* 4.4 Write property tests for repositories
    - **Property 1: Connection Creation Round Trip**
    - **Property 2: User Connection Isolation**
    - **Property 4: Cascade Delete Completeness**
    - **Property 14: Pagination Correctness**
    - **Property 15: Data Upsert Idempotency**
    - **Validates: Requirements 2.1, 2.3, 2.4, 2.7, 10.1, 10.2, 14.3**
  - [x] 4.5 Update common/repo.py with factory functions
    - Add `get_sheet_connection_repo`, `get_sheet_sync_state_repo`, `get_sheet_data_repo`
    - _Requirements: 2.1_

- [ ] 5. Implement Service Layer
  - [ ] 5.1 Implement Column Mapper
    - Create `app/services/business/sheet_crawler/__init__.py`
    - Create `app/services/business/sheet_crawler/column_mapper.py`
    - Implement `ColumnMapper` with `map_row` and `convert_type` methods
    - Support both column letters (A, B) and header names
    - _Requirements: 3.1, 3.3, 3.4_
  - [ ]* 5.2 Write property tests for Column Mapper
    - **Property 5: Column Mapping Flexibility**
    - **Property 6: Type Conversion with Fallback**
    - **Validates: Requirements 3.1, 3.3, 3.4**
  - [ ] 5.3 Implement Crawler Service
    - Create `app/services/business/sheet_crawler/crawler_service.py`
    - Implement `SheetCrawlerService` with `sync_sheet`, `preview_sheet` methods
    - Integrate with GoogleSheetClient, repositories, and SocketGateway
    - Implement incremental sync logic (start from last_synced_row + 1)
    - _Requirements: 4.1, 5.3, 5.4, 5.5, 7.1, 7.2, 7.3, 7.4, 12.1, 12.2, 12.3_
  - [ ]* 5.4 Write property tests for Crawler Service
    - **Property 9: WebSocket Notification Completeness**
    - **Property 10: Incremental Sync Correctness**
    - **Validates: Requirements 5.3, 5.4, 5.5, 7.1, 7.3, 12.1, 12.2, 12.3**
  - [ ] 5.5 Update common/service.py with factory functions
    - Add `get_crawler_service`, `get_google_sheet_client`
    - _Requirements: 5.1_

- [ ] 6. Checkpoint - Core Logic Complete
  - Ensure all unit tests pass
  - Verify domain models, infrastructure, repositories, and services are working
  - Ask the user if questions arise

- [ ] 7. Implement API Layer
  - [ ] 7.1 Implement Internal API Router
    - Create `app/api/v1/internal/__init__.py`
    - Create `app/api/v1/internal/router.py`
    - Implement `verify_internal_api_key` dependency
    - Implement `POST /trigger-sync` endpoint with BackgroundTasks
    - _Requirements: 6.1, 6.2, 6.3_
  - [ ] 7.2 Implement Sheet Crawler Public API Router
    - Create `app/api/v1/sheet_crawler/__init__.py`
    - Create `app/api/v1/sheet_crawler/router.py`
    - Implement `GET /service-account` endpoint
    - Implement CRUD endpoints for connections
    - Implement `POST /{id}/sync`, `GET /{id}/sync-status` endpoints
    - Implement `GET /{id}/preview`, `GET /{id}/data` endpoints
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 4.1, 4.2, 4.3, 5.1, 5.2, 10.1, 10.2, 10.3, 11.1, 11.2, 11.3_
  - [ ]* 7.3 Write property tests for API endpoints
    - **Property 3: Connection Update Preservation**
    - **Property 7: Preview Row Limit**
    - **Property 8: Sync Task Enqueue**
    - **Validates: Requirements 2.6, 4.2, 5.1, 6.2**
  - [ ] 7.4 Register routers in main application
    - Update `app/api/v1/router.py` to include internal and sheet_crawler routers
    - _Requirements: 1.1, 2.1_

- [ ] 8. Implement Worker
  - [ ] 8.1 Implement Sheet Sync Worker
    - Create `app/workers/sheet_sync_worker.py`
    - Implement `SheetSyncWorker` class with main loop
    - Integrate with Redis queue and rate limiter
    - Implement retry logic (max 3 retries)
    - _Requirements: 9.1, 9.2, 9.3, 9.4_
  - [ ]* 8.2 Write property tests for Worker
    - **Property 13: Worker Retry Limit**
    - **Validates: Requirements 9.3, 9.4**

- [ ] 9. Final Checkpoint
  - Ensure all tests pass
  - Verify end-to-end flow: API → Queue → Worker → Database → WebSocket
  - Ask the user if questions arise

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Worker should be run as a separate process: `python -m app.workers.sheet_sync_worker`
