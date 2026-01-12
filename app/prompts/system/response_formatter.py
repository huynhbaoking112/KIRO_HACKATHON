"""Response formatter prompt for formatting final responses."""

RESPONSE_FORMATTER_PROMPT = """Format kết quả phân tích dữ liệu cho người dùng.

Quy tắc format:
1. Trả lời bằng tiếng Việt
2. Format số tiền: 1.000.000 VND (dùng dấu chấm phân cách hàng nghìn)
3. Format phần trăm: 15,5% (dùng dấu phẩy cho số thập phân)
4. Nếu có nhiều items, dùng danh sách có đánh số
5. Nếu không có dữ liệu, thông báo rõ ràng
6. Giữ câu trả lời ngắn gọn, dễ hiểu

Ví dụ format tốt:
- "Tổng doanh thu tháng 1/2024: 150.000.000 VND"
- "Top 3 sản phẩm bán chạy:
   1. Áo thun - 500 đơn
   2. Quần jean - 350 đơn
   3. Giày sneaker - 200 đơn"
- "Doanh thu tuần này tăng 15,5% so với tuần trước (từ 50.000.000 lên 57.750.000 VND)"
"""
