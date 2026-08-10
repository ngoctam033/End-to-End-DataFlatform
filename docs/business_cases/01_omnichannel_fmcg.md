# Business Case: Omnichannel D2C FMCG

Tài liệu này mô tả chi tiết bài toán kinh doanh (Business Case) mà hệ thống Data Platform này hướng tới giải quyết. Lĩnh vực được chọn là sự kết hợp của 3 domain lớn: **Thương mại điện tử & Bán lẻ đa kênh**, **Logistics & Chuỗi cung ứng**, và **FMCG (Hàng tiêu dùng nhanh)**.

---

## 1. Bối cảnh Kinh Doanh (Business Context)

Doanh nghiệp giả định là một công ty sản xuất và phân phối các mặt hàng FMCG (ví dụ: Nước giải khát, Thực phẩm đóng gói, Sữa...). Công ty vận hành theo mô hình **Omnichannel D2C (Direct-to-Consumer)**, phân phối qua 3 kênh chính:
* **Kênh Bán buôn (Wholesale - B2B):** Phân phối số lượng lớn cho các đại lý, siêu thị.
* **Kênh Bán lẻ Vật lý (Retail POS):** Các cửa hàng trưng bày và bán trực tiếp của công ty.
* **Kênh E-commerce (D2C):** Bán trực tiếp cho người tiêu dùng qua Website riêng, Shopee, TikTok Shop.

**Đặc thù "Nỗi đau" (Pain Points):**
* Hàng FMCG có vòng đời ngắn, phải quản lý khắt khe Hạn sử dụng (Expiration dates / Lot numbers).
* Việc bán hàng đa kênh khiến dữ liệu khách hàng và doanh thu bị phân mảnh. Không biết khách hàng VIP offline có đang mua hàng trên Shopee hay không.
* Áp lực về Logistics rất lớn: Vừa phải gom hàng giao sỉ cho đại lý, vừa phải xé lẻ hàng để đóng gói giao nhanh cho khách E-commerce, đồng thời phải đảm bảo các cửa hàng POS không bị thiếu hàng (Out-of-stock).

---

## 2. Giải Pháp Dữ Liệu (Data Strategy)

Hệ thống Data Platform sẽ kết nối trực tiếp với **Odoo ERP** - nơi vận hành toàn bộ các giao dịch cốt lõi của công ty.

### A. Nguồn Dữ Liệu (Data Sources từ Odoo)
* **Sales & CRM:** Bảng `sale_order`, `sale_order_line` (Đơn hàng online/bán buôn), `pos_order` (Đơn hàng POS), `res_partner` (Khách hàng).
* **Inventory & FMCG:** Bảng `product_template`, `product_product` (Danh mục hàng hóa), `stock_lot` (Quản lý lô date).
* **Logistics:** Bảng `stock_picking`, `stock_move` (Lệnh xuất nhập, điều chuyển kho).

### B. Các Data Models trọng tâm (dbt Transformations)
Data Pipeline sẽ làm sạch và biến đổi dữ liệu thô thành 3 mô hình chính (Star-schema):

1. **Omnichannel Sales Model:**
   * **Mục tiêu:** Hợp nhất doanh thu toàn kênh. Tính toán RFM (Recency, Frequency, Monetary) để xác định chân dung khách hàng. Phân tích giỏ hàng (Market Basket Analysis).
2. **FMCG Inventory Health Model:**
   * **Mục tiêu:** Theo dõi lượng hàng tồn, đối chiếu với tốc độ bán (Sales Velocity) để dự báo ngày hết hàng (Days of Inventory). Cảnh báo tự động các lô hàng sắp hết hạn sử dụng.
3. **Logistics Fulfillment Model:**
   * **Mục tiêu:** Đo lường hiệu suất kho bãi. Tính toán Lead time (thời gian từ lúc khách lên đơn đến khi đóng gói và giao cho đơn vị vận chuyển). Tỷ lệ giao hàng đúng hạn (OTD).

---

## 3. Đầu ra (BI Dashboards)
Các mô hình trên sẽ phục vụ cho các Dashboard quản trị chiến lược trên **Metabase**:
* **Executive Dashboard:** Tổng quan doanh thu Đa kênh, Top sản phẩm bán chạy/chậm.
* **Supply Chain Dashboard:** Cảnh báo đỏ hàng hóa cận date, báo cáo tỷ lệ lấp đầy đơn hàng, phát hiện các điểm "thắt cổ chai" trong khâu vận hành kho bãi.

---

## 4. Các Bài Toán Phân Tích Nâng Cao (Advanced Analytics)

Để nâng tầm dự án lên mức độ Senior/Lead Data Engineer, hệ thống sẽ mở rộng xử lý các bài toán phân tích chuyên sâu sau:

### A. Market Basket Analysis (Phân tích rổ hàng & Gợi ý bán chéo)
* **Bài toán:** Sử dụng dữ liệu chi tiết của đơn hàng (`sale_order_line` và `pos_order_line`) để tìm ra quy luật kết hợp sản phẩm (Ví dụ: Khách mua bia thường mua thêm đồ nhắm).
* **Giá trị:** Tham mưu cho team Business tạo ra các "Combo" trên E-commerce để tăng giá trị trung bình trên mỗi đơn hàng (AOV), hoặc tối ưu hóa việc trưng bày sản phẩm tại cửa hàng bán lẻ.

### B. Customer Churn Prediction (Dự báo khách hàng rời bỏ)
* **Bài toán:** Tính toán **Purchase Cycle (Chu kỳ mua hàng)** của từng khách hàng. Nếu một khách hàng (có lịch sử mua hàng 20 ngày/lần) mà đã 45 ngày không phát sinh giao dịch mới, hệ thống tự động gán nhãn "Nguy cơ rời bỏ" (At-risk).
* **Giá trị:** Cung cấp danh sách khách hàng "At-risk" cho team Marketing để gửi mã giảm giá kịp thời qua SMS/Email nhằm giữ chân khách hàng (Retention).

### C. Failed Delivery & Return Analytics (Phân tích Hàng Hoàn / Bom hàng)
* **Bài toán:** Phân tích dữ liệu vận đơn (`stock_picking` với trạng thái `returned` / `cancelled`) để tìm ra quy luật: Hàng hoàn thường xảy ra ở Đơn vị vận chuyển nào? Ở Tỉnh thành nào? Do sản phẩm đóng gói kém hay do tệp khách hàng mua COD.
* **Giá trị:** Giúp team Logistics đánh giá đối tác vận chuyển (SLA) và team Sale có chính sách hạn chế hình thức thanh toán COD ở những khu vực có tỷ lệ "Bom hàng" cao, tránh lãng phí chi phí logistics và hư hỏng hàng hóa lưu kho.

### D. Dự báo đứt hàng theo mùa vụ (Seasonality Out-of-Stock)
* **Bài toán:** Kết hợp dữ liệu lịch sử bán hàng theo thời gian (Time-series data) để dự báo nhu cầu. Nếu tốc độ bán (Sales velocity) tăng vọt, hệ thống tự động tính toán lại mức Tồn kho an toàn (Safety Stock).
* **Giá trị:** Ngăn chặn việc cửa hàng hết sạch hàng đúng vào lúc nhu cầu khách hàng cao nhất.
