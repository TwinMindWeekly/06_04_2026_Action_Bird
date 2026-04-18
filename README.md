# 🚀 Action Bird - Flappy Bird Hardcore Edition

**Action Bird** là một phiên bản nâng cấp mạnh mẽ từ trò chơi Flappy Bird cổ điển, kết hợp với các yếu tố hành động, hệ thống kỹ năng và cơ chế RPG đơn giản. Trò chơi mang lại cảm giác kịch tính hơn với Laser, Chế độ khổng lồ và hệ thống Shop đa dạng.

![Action Bird Logo](assets/images/banner.png)

## ✨ Tính năng nổi bật

- **🔥 Kỹ năng Hành động:**
  - **Laser Shot (F):** Bắn tia laser để phá hủy ống chướng ngại vật ngay lập tức.
  - **Giant Mode:** Biến chim thành khổng lồ, bất tử và có khả năng húc đổ mọi vật cản.
  - **Ghost Mode:** Xuyên thấu qua mọi chướng ngại vật trong một khoảng thời gian.
- **📈 Hệ thống Kỹ năng & Combo:**
  - **Near Miss:** Nhận điểm thưởng khi bay cực sát ống mà không chạm.
  - **Destruction Combo:** Phá hủy liên tiếp các ống để tăng hệ số nhân điểm (X2, X3...).
- **🛒 Shop & Economy:**
  - Thu thập **Credits (HS)** qua mỗi ván chơi để mua Skin và nâng cấp.
  - Hệ thống Skin đa dạng (Red Bird, Original...) với hiệu ứng Blending chuyên nghiệp.
- **📊 Lưu trữ & Thành tựu:**
  - Tự động lưu High Score, Credits và Skins vào file `settings.json`.
  - Hệ thống Thành tựu (Achievements) theo dõi tiến trình phá hủy ống và sử dụng kỹ năng.

## 🛠️ Hướng dẫn cài đặt

### Yêu cầu hệ thống
- Python 3.8 trở lên.
- Thư viện Pygame.

### Các bước cài đặt
1. Tải toàn bộ mã nguồn về máy hoặc dùng lệnh:
   ```bash
   git clone https://github.com/TwinMindWeekly/Action-Bird.git
   ```
2. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
3. Chạy trò chơi:
   ```bash
   python FB.py
   ```

## 🎮 Cách chơi

- **Chuột (Mouse):** Điều hướng chính trong Menu, Shop và Settings.
- **SPACE:** Nhảy (Flap).
- **F:** Bắn Laser (khi có đủ điều kiện).
- **PLAY:** Nhấn nút PLAY tại sảnh để bắt đầu.
- **RETRY:** Nhấn nút RETRY sau khi thua để chơi lại nhanh.

## 📂 Thu thập tài nguyên (Assets)

Dự án được cấu trúc khoa học để dễ bảo trì:
- `assets/images/`: Chứa các file ảnh (`FB2.png`, `BG2.png`, `FB_red.png`).
- `assets/sounds/`: Chứa âm nhạc và hiệu ứng âm thanh (`music.mp3`, `wing.wav`).

## 🎯 Lộ trình phát triển (Roadmap)

- [ ] **Hệ thống Boss:** Cứ mỗi 50 điểm sẽ xuất hiện một Boss cản đường.
- [ ] **Multiplayer:** Chế độ đối kháng 2 người chơi qua mạng hoặc local.
- [ ] **Aura & Tails:** Thêm hiệu ứng hào quang và đuôi khi bay đạt tốc độ cao.
- [ ] **Chướng ngại vật động:** Thêm các loài chim khác bay ngược chiều hoặc bom rơi.

## 🤝 Đóng góp

Mọi ý đóng góp đều được hoan nghênh! Vui lòng đọc tệp [CONTRIBUTING.md](CONTRIBUTING.md) để biết thêm chi tiết về cách gửi Pull Request.

---
© 2024 **Action Bird Team** - Một dự án thuộc [TwinMindWeekly](https://github.com/TwinMindWeekly).
