# Requirements Document

## Introduction

Tính năng Google Sheet Crawler cho phép hệ thống tự động crawl dữ liệu từ Google Sheets của khách hàng để hỗ trợ phân tích dữ liệu bán hàng. Khách hàng sẽ share Google Sheet của họ cho service account của hệ thống, cấu hình column mapping, và hệ thống sẽ tự động sync dữ liệu định kỳ mỗi 5 phút hoặc theo yêu cầu manual.

## Glossary

- **Sheet_Connection**: Cấu hình kết nối giữa hệ thống và một Google Sheet của khách hàng, bao gồm sheet ID, column mapping, và sync settings
- **Column_Mapping**: Ánh xạ giữa các cột trong Google Sheet của khách hàng với các field chuẩn của hệ thống
- **Sync_State**: Trạng thái đồng bộ của một connection, bao gồm last synced row, status, và error information
- **Sheet_Raw_Data**: Dữ liệu thô được crawl từ Google Sheet và lưu vào database
- **Rate_Limiter**: Bộ điều khiển tốc độ request theo cơ chế Token Bucket để tuân thủ Google Sheets API quotas
- **Crawler_Service**: Service xử lý logic crawl dữ liệu từ Google Sheet
- **Google_Sheet_Client**: Client wrapper cho gspread library để tương tác với Google Sheets API
- **Sync_Worker**: Worker process xử lý các sync tasks từ message queue
- **Service_Account**: Google Cloud service account dùng để authenticate với Google Sheets API

## Requirements

### Requirement 1: Service Account Information

**User Story:** As a user, I want to get the service account email, so that I can share my Google Sheet with the system.

#### Acceptance Criteria

1. WHEN a user requests service account information, THE System SHALL return the service account email address
2. WHEN a user requests service account information, THE System SHALL return instructions on how to share the sheet

### Requirement 2: Sheet Connection Management

**User Story:** As a user, I want to create and manage connections to my Google Sheets, so that the system can crawl my sales data.

#### Acceptance Criteria

1. WHEN a user creates a new connection with valid sheet ID and column mappings, THE System SHALL create a Sheet_Connection record and return the connection details
2. WHEN a user creates a connection with a sheet that the service account cannot access, THE System SHALL return an error indicating the sheet is not accessible
3. WHEN a user lists their connections, THE System SHALL return all Sheet_Connection records belonging to that user
4. WHEN a user requests a specific connection by ID, THE System SHALL return the connection details if it belongs to the user
5. WHEN a user requests a connection that does not exist or belongs to another user, THE System SHALL return a not found error
6. WHEN a user updates a connection's column mappings or sync settings, THE System SHALL update the Sheet_Connection record and return the updated details
7. WHEN a user deletes a connection, THE System SHALL remove the Sheet_Connection, associated Sync_State, and all Sheet_Raw_Data records

### Requirement 3: Column Mapping Configuration

**User Story:** As a user, I want to configure column mappings, so that my sheet columns are correctly mapped to system fields.

#### Acceptance Criteria

1. WHEN a user specifies column mappings, THE System SHALL accept both column letters (A, B, C) and column header names as sheet_column values
2. WHEN a user specifies a required column that is missing in the sheet, THE System SHALL return a validation error during sync
3. WHEN a user specifies data types for columns, THE System SHALL convert values to the specified type (string, number, integer, date) during sync
4. IF a value cannot be converted to the specified data type, THEN THE System SHALL store the original string value

### Requirement 4: Sheet Preview

**User Story:** As a user, I want to preview my sheet data before syncing, so that I can verify the column mapping is correct.

#### Acceptance Criteria

1. WHEN a user requests a preview of a connection, THE System SHALL fetch and return the header row and first N data rows from the Google Sheet
2. WHEN a user specifies the number of preview rows, THE System SHALL return that many rows (up to a maximum of 50)
3. WHEN the sheet is not accessible during preview, THE System SHALL return an error with a descriptive message

### Requirement 5: Manual Sync Trigger

**User Story:** As a user, I want to manually trigger a sync, so that I can get the latest data immediately without waiting for the scheduled sync.

#### Acceptance Criteria

1. WHEN a user triggers a manual sync, THE System SHALL enqueue a sync task for that connection
2. WHEN a user triggers a manual sync, THE System SHALL return immediately with an accepted status
3. WHEN a sync task is processed, THE System SHALL notify the user via WebSocket when sync starts
4. WHEN a sync task completes successfully, THE System SHALL notify the user via WebSocket with the number of rows synced
5. WHEN a sync task fails, THE System SHALL notify the user via WebSocket with the error message

### Requirement 6: Scheduled Sync via Cloud Scheduler

**User Story:** As a system operator, I want the system to automatically sync all enabled connections every 5 minutes, so that user data stays up to date.

#### Acceptance Criteria

1. WHEN Cloud Scheduler calls the internal trigger endpoint, THE System SHALL return an accepted response immediately
2. WHEN Cloud Scheduler calls the internal trigger endpoint, THE System SHALL enqueue sync tasks for all enabled connections in a background task
3. WHEN the internal endpoint is called without a valid API key, THE System SHALL return an unauthorized error

### Requirement 7: Incremental Sync

**User Story:** As a user, I want the system to only sync new rows, so that syncing is efficient and doesn't duplicate data.

#### Acceptance Criteria

1. WHEN syncing a sheet, THE Crawler_Service SHALL start from the row after the last synced row
2. WHEN syncing a sheet for the first time, THE Crawler_Service SHALL start from the configured data_start_row
3. WHEN new rows are synced, THE Sync_State SHALL be updated with the new last_synced_row
4. WHEN syncing completes, THE Sync_State SHALL record the sync timestamp and status

### Requirement 8: Rate Limiting with Token Bucket

**User Story:** As a system operator, I want the system to respect Google Sheets API rate limits, so that we don't get blocked by Google.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL implement a Token Bucket algorithm with capacity matching Google's read request limit (300 requests per minute)
2. THE Rate_Limiter SHALL implement a second Token Bucket for the per-100-seconds limit (100 requests per 100 seconds)
3. WHEN a worker needs to make API requests, THE Rate_Limiter SHALL block until sufficient tokens are available
4. WHEN tokens are consumed, THE Rate_Limiter SHALL refill tokens at the configured rate over time
5. THE Rate_Limiter SHALL apply a safety factor (80%) to stay within limits

### Requirement 9: Worker Task Processing

**User Story:** As a system operator, I want sync tasks to be processed reliably from a queue, so that the system can handle load and recover from failures.

#### Acceptance Criteria

1. THE Sync_Worker SHALL continuously dequeue tasks from the Redis queue
2. WHEN a task is dequeued, THE Sync_Worker SHALL acquire rate limit tokens before processing
3. WHEN a task fails, THE Sync_Worker SHALL re-queue the task with an incremented retry count (up to 3 retries)
4. WHEN a task exceeds the maximum retry count, THE Sync_Worker SHALL mark the sync as failed and notify the user

### Requirement 10: Synced Data Retrieval

**User Story:** As a user, I want to retrieve my synced data, so that I can use it for analysis.

#### Acceptance Criteria

1. WHEN a user requests synced data, THE System SHALL return paginated Sheet_Raw_Data records for that connection
2. WHEN a user specifies page and page_size parameters, THE System SHALL return the corresponding page of results
3. THE System SHALL return both the mapped data and the total count of records

### Requirement 11: Sync Status Monitoring

**User Story:** As a user, I want to check the sync status of my connections, so that I know if syncing is working correctly.

#### Acceptance Criteria

1. WHEN a user requests sync status, THE System SHALL return the current Sync_State including status, last_synced_row, last_sync_time, and any error message
2. WHEN a sync is in progress, THE System SHALL show status as "syncing"
3. WHEN a sync has failed, THE System SHALL show the error message from the last attempt

### Requirement 12: WebSocket Notifications

**User Story:** As a user, I want to receive real-time notifications about sync progress, so that I know when my data is ready.

#### Acceptance Criteria

1. WHEN a sync starts, THE System SHALL emit a "sheet:sync:started" event to the user's WebSocket room
2. WHEN a sync completes successfully, THE System SHALL emit a "sheet:sync:completed" event with rows_synced and total_rows
3. WHEN a sync fails, THE System SHALL emit a "sheet:sync:failed" event with the error message

### Requirement 13: Google Sheet Client

**User Story:** As a developer, I want a reliable client for Google Sheets API, so that I can fetch data from customer sheets.

#### Acceptance Criteria

1. THE Google_Sheet_Client SHALL authenticate using the configured service account credentials
2. THE Google_Sheet_Client SHALL support fetching all values from a specified sheet tab
3. THE Google_Sheet_Client SHALL support fetching sheet metadata (title, available sheets)
4. THE Google_Sheet_Client SHALL support checking if the service account has access to a sheet
5. WHEN API errors occur, THE Google_Sheet_Client SHALL propagate the error with a descriptive message

### Requirement 14: Data Persistence

**User Story:** As a user, I want my synced data to be stored permanently, so that I can access historical data for analysis.

#### Acceptance Criteria

1. WHEN data is synced, THE System SHALL store each row as a Sheet_Raw_Data document in MongoDB
2. THE Sheet_Raw_Data document SHALL include the connection_id, row_number, mapped data, raw data, and sync timestamp
3. WHEN a row is synced again (same row_number), THE System SHALL update the existing document (upsert)
4. THE System SHALL NOT delete synced data unless the connection is deleted
