# Requirements Document

## Introduction

Tính năng Sheet Analytics API cung cấp các endpoint để lấy dữ liệu analytics từ các Google Sheets đã được sync về hệ thống. API hỗ trợ các loại visualizations khác nhau cho từng sheet type (Orders, Order Items, Customers, Products) với caching để tối ưu performance.

## Glossary

- **Sheet_Type**: Loại sheet được sync (orders, order_items, customers, products), xác định các metrics và visualizations có sẵn
- **Analytics_Service**: Service xử lý logic tính toán metrics và aggregations từ dữ liệu đã sync
- **Summary_Metrics**: Các số liệu tổng hợp như total_count, total_amount, avg_amount
- **Time_Series**: Dữ liệu được group theo thời gian (day/week/month/year) cho charts
- **Distribution**: Phân bố dữ liệu theo một field cụ thể (platform, order_status)
- **Top_N**: Danh sách N items có giá trị cao nhất theo một metric
- **Cache_Manager**: Component quản lý Redis cache cho analytics data
- **Granularity**: Mức độ chi tiết của time series (day, week, month, year)

## Requirements

### Requirement 1: Sheet Type Detection

**User Story:** As a user, I want the system to automatically detect my sheet type based on sheet name, so that I get appropriate analytics without extra configuration.

#### Acceptance Criteria

1. WHEN a connection has sheet_name matching "Orders" (case-insensitive), THE System SHALL treat it as orders type
2. WHEN a connection has sheet_name matching "Order_Items" (case-insensitive), THE System SHALL treat it as order_items type
3. WHEN a connection has sheet_name matching "Customers" (case-insensitive), THE System SHALL treat it as customers type
4. WHEN a connection has sheet_name matching "Products" (case-insensitive), THE System SHALL treat it as products type
5. WHEN a user requests analytics for a connection, THE System SHALL return metrics appropriate for the detected sheet type
6. WHEN sheet_name does not match any known type, THE System SHALL default to orders type

### Requirement 2: Summary Metrics

**User Story:** As a user, I want to see summary metrics for my synced data, so that I can quickly understand the overall status.

#### Acceptance Criteria

1. WHEN a user requests summary for an orders sheet, THE Analytics_Service SHALL return total_count, total_amount, and avg_amount
2. WHEN a user requests summary for an order_items sheet, THE Analytics_Service SHALL return total_quantity, total_line_total, and unique_products
3. WHEN a user requests summary for a customers sheet, THE Analytics_Service SHALL return total_count
4. WHEN a user requests summary for a products sheet, THE Analytics_Service SHALL return total_count
5. WHEN a user specifies date_from and date_to for orders sheet, THE Analytics_Service SHALL filter data by order_date before calculating metrics
6. WHEN a connection has no synced data, THE Analytics_Service SHALL return zero values for all metrics

### Requirement 3: Time Series Data

**User Story:** As a user, I want to see my data aggregated over time, so that I can visualize trends in charts.

#### Acceptance Criteria

1. WHEN a user requests time-series for an orders sheet, THE Analytics_Service SHALL return data grouped by the specified granularity
2. THE Analytics_Service SHALL support granularity values: day, week, month, year
3. WHEN granularity is not specified, THE Analytics_Service SHALL default to "day"
4. WHEN a user specifies metrics as "count", THE Analytics_Service SHALL return only count per period
5. WHEN a user specifies metrics as "amount", THE Analytics_Service SHALL return only total_amount per period
6. WHEN a user specifies metrics as "both" or does not specify, THE Analytics_Service SHALL return both count and total_amount per period
7. WHEN a user requests time-series for a non-orders sheet, THE System SHALL return a 400 error indicating time-series is not supported
8. THE Analytics_Service SHALL require date_from and date_to parameters for time-series requests

### Requirement 4: Distribution Data

**User Story:** As a user, I want to see the distribution of my data by specific fields, so that I can create pie charts and understand proportions.

#### Acceptance Criteria

1. WHEN a user requests distribution by platform for orders sheet, THE Analytics_Service SHALL return count and percentage for each platform value
2. WHEN a user requests distribution by order_status for orders sheet, THE Analytics_Service SHALL return count and percentage for each status value
3. WHEN a user requests distribution for a non-orders sheet, THE System SHALL return a 400 error indicating distribution is not supported
4. WHEN a user specifies date_from and date_to, THE Analytics_Service SHALL filter data before calculating distribution
5. THE Analytics_Service SHALL calculate percentage as (count / total) * 100 rounded to 1 decimal place

### Requirement 5: Top N Data

**User Story:** As a user, I want to see the top items by a specific metric, so that I can identify best performers.

#### Acceptance Criteria

1. WHEN a user requests top by platform for orders sheet, THE Analytics_Service SHALL return top N platforms by the specified metric
2. WHEN a user requests top by product_name for order_items sheet, THE Analytics_Service SHALL return top N products by the specified metric
3. WHEN metric is "count", THE Analytics_Service SHALL sort by count descending
4. WHEN metric is "amount" for orders, THE Analytics_Service SHALL sort by total_amount descending
5. WHEN metric is "quantity" for order_items, THE Analytics_Service SHALL sort by total quantity descending
6. WHEN limit is not specified, THE Analytics_Service SHALL default to 10
7. THE Analytics_Service SHALL accept limit values from 1 to 50
8. WHEN a user requests top for customers or products sheet, THE System SHALL return a 400 error indicating top is not supported

### Requirement 6: Enhanced Data Retrieval

**User Story:** As a user, I want to search, filter, and sort my synced data, so that I can find specific records easily.

#### Acceptance Criteria

1. WHEN a user provides a search parameter, THE Analytics_Service SHALL search across searchable fields for that sheet type
2. FOR orders sheet, THE Analytics_Service SHALL search in order_id, platform, order_status, customer_id fields
3. FOR order_items sheet, THE Analytics_Service SHALL search in order_item_id, order_id, product_id, product_name fields
4. FOR customers sheet, THE Analytics_Service SHALL search in customer_id, customer_name, phone fields
5. FOR products sheet, THE Analytics_Service SHALL search in product_id, product_name fields
6. WHEN a user provides sort_by and sort_order, THE Analytics_Service SHALL sort results accordingly
7. WHEN sort_order is not specified, THE Analytics_Service SHALL default to "desc"
8. WHEN a user provides date_from and date_to for orders sheet, THE Analytics_Service SHALL filter by order_date
9. THE Analytics_Service SHALL return paginated results with total count and total_pages

### Requirement 7: Caching

**User Story:** As a system operator, I want analytics results to be cached, so that repeated requests are fast and don't overload the database.

#### Acceptance Criteria

1. THE Cache_Manager SHALL cache analytics results in Redis with a TTL of 5 minutes
2. THE Cache_Manager SHALL use cache key pattern: analytics:{connection_id}:{endpoint}:{params_hash}
3. WHEN a sync completes for a connection, THE Cache_Manager SHALL invalidate all cache entries for that connection
4. WHEN cache hit occurs, THE Analytics_Service SHALL return cached data without querying database
5. WHEN cache miss occurs, THE Analytics_Service SHALL query database, compute results, cache them, and return

### Requirement 8: Access Control

**User Story:** As a user, I want my analytics data to be private, so that other users cannot see my data.

#### Acceptance Criteria

1. WHEN a user requests analytics for a connection, THE System SHALL verify the user owns that connection
2. WHEN a user requests analytics for a connection they don't own, THE System SHALL return a 404 error
3. WHEN a user requests analytics for a non-existent connection, THE System SHALL return a 404 error

### Requirement 9: Error Handling

**User Story:** As a user, I want clear error messages when something goes wrong, so that I can understand and fix the issue.

#### Acceptance Criteria

1. WHEN date_from is greater than date_to, THE System SHALL return a 400 error with message "Invalid date range"
2. WHEN an unsupported field is requested for distribution or top, THE System SHALL return a 400 error with message "Field not supported for this sheet type"
3. WHEN an invalid granularity is provided, THE System SHALL return a 400 error with message "Invalid granularity"
4. WHEN validation fails for query parameters, THE System SHALL return a 422 error with details
