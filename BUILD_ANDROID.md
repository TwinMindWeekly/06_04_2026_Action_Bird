# Build Action Bird cho Android

Hướng dẫn đầy đủ để build file `.apk` từ source code Python/pygame của Action Bird, đã được kiểm chứng trên Windows 11 + WSL2 Ubuntu 24.04.

## TL;DR

```bash
# Trong WSL Ubuntu (chỉ làm 1 lần):
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip python3-venv \
  autoconf libtool pkg-config zlib1g-dev libncurses-dev libncursesw5-dev \
  libtinfo6 cmake libffi-dev libssl-dev build-essential ccache libltdl-dev
python3 -m venv ~/buildozer-venv
~/buildozer-venv/bin/pip install --upgrade pip wheel setuptools
~/buildozer-venv/bin/pip install buildozer 'cython==0.29.37'

# Mỗi lần build:
cd /path/to/project
bash tools/build_android.sh
```

APK sẽ ở `bin/actionbird-1.0-arm64-v8a_armeabi-v7a-debug.apk`.

---

## Tại sao phải làm phức tạp?

Build pygame cho Android không phải plug-and-play vì 3 vấn đề cộng hưởng:

1. **Buildozer không chạy native trên Windows** — phải dùng WSL2 hoặc Linux/macOS.
2. **pygame 2.1.0 (mặc định trong python-for-android) không tương thích Python 3.11** — sinh ra lỗi compile do CPython internal API thay đổi (`longintrepr.h`, `recursion_depth`, `PyCode_New` signature, `struct _frame`...).
3. **SDK license prompt treo build** — buildozer dùng `sdkmanager` cũ, tương tác kém với việc nhận license.

Repo này đã giải quyết cả 3:
- File `recipes/pygame/__init__.py` ghi đè recipe pygame, regenerate Cython output bằng Cython 0.29.37 ngay trong `prebuild_arch`.
- `tools/accept_sdk_licenses.sh` ghi sẵn các SHA hash license vào đúng vị trí.
- `tools/build_android.sh` activate venv và set PATH đúng trước khi gọi buildozer.

---

## Yêu cầu môi trường

| Thành phần | Phiên bản | Ghi chú |
|------------|-----------|---------|
| OS | Linux x86_64 hoặc WSL2 | macOS chưa kiểm chứng cho project này |
| Ubuntu | 22.04 / 24.04 | |
| Python | 3.10–3.12 | Buildozer venv |
| Java | OpenJDK 17 | bắt buộc cho Android Gradle Plugin |
| RAM | ≥ 4 GB | NDK toolchain ngốn RAM khi compile |
| Disk | ≥ 8 GB free | NDK + SDK + p4a build artifacts |
| Internet | tốt | lần đầu tải ~2 GB (NDK, SDK, p4a, Gradle deps) |

---

## Cài đặt lần đầu

### 1. (Windows) Cài WSL2 Ubuntu

PowerShell admin:

```powershell
wsl --install -d Ubuntu-24.04
```

Khởi động lại máy nếu Windows yêu cầu, rồi mở Ubuntu từ Start menu, đặt username/password.

### 2. Cài system packages

Trong terminal Ubuntu:

```bash
sudo apt update
sudo apt install -y \
  git zip unzip openjdk-17-jdk python3-pip python3-venv \
  autoconf libtool pkg-config zlib1g-dev libncurses-dev \
  libncursesw5-dev libtinfo6 cmake libffi-dev libssl-dev \
  build-essential ccache libltdl-dev ffmpeg
```

`ffmpeg` để convert `music.mp3` sang `.ogg` nếu cần (xem mục **Asset notes** bên dưới).

### 3. Tạo venv cho buildozer

```bash
python3 -m venv ~/buildozer-venv
~/buildozer-venv/bin/pip install --upgrade pip wheel setuptools
~/buildozer-venv/bin/pip install buildozer 'cython==0.29.37'
```

> ⚠️ Cython phải pin **0.29.37** — không dùng 3.x (quá strict cho pygame 2.1.0) và cũng không nên dùng 0.29.36 trở xuống (chưa hỗ trợ Python 3.11).

### 4. Verify

```bash
~/buildozer-venv/bin/buildozer --version   # Buildozer 1.5.0
~/buildozer-venv/bin/cython --version      # Cython version 0.29.37
java -version                              # OpenJDK 17
```

---

## Build APK

### Lần đầu (mất 30–60 phút)

```bash
# Clone repo về thư mục Linux native (KHÔNG build trên /mnt/d/... — quá chậm)
git clone <repo-url> ~/action-bird
cd ~/action-bird

# Bắt đầu build — sẽ tải Android SDK + NDK + python-for-android (~2 GB)
bash tools/build_android.sh
```

Quá trình build sẽ:
1. Tải Android NDK r25b (~1 GB)
2. Tải/cài Android SDK + platform tools + build-tools
3. **Treo ở SDK license prompt** — đây là vấn đề đã biết. Khi thấy `Accept? (y/N):`, bấm `Ctrl+C` để dừng, rồi chạy:
   ```bash
   bash tools/accept_sdk_licenses.sh
   bash tools/build_android.sh   # resume
   ```
4. Compile hostpython3 (Python cho Linux build host, ~5 phút)
5. Compile target Python3 + libffi + openssl + sqlite3 + jpeg + png cho **armeabi-v7a** (~5 phút)
6. Compile SDL2 + SDL2_image + SDL2_mixer + SDL2_ttf cho armeabi-v7a (~10 phút)
7. Compile pygame cho armeabi-v7a (recipe của repo này regenerate Cython trước khi compile)
8. Lặp lại bước 5–7 cho **arm64-v8a** (~15 phút)
9. Đóng gói APK qua Gradle (~2 phút)

Khi xong, APK ở `bin/actionbird-1.0-arm64-v8a_armeabi-v7a-debug.apk`.

### Lần sau (sau khi sửa code Python)

```bash
bash tools/build_android.sh
```

Khoảng **5–15 giây** vì mọi native artifact đã cached. Buildozer chỉ:
- Repackage Python source code
- Đóng gói APK mới qua Gradle

---

## Troubleshooting

### `Accept? (y/N):` treo lệnh build

Buildozer kẹt ở màn hình license của Android SDK. Workaround:

```bash
# Trong terminal khác (hoặc Ctrl+C dừng build cũ trước)
bash tools/accept_sdk_licenses.sh
bash tools/build_android.sh
```

### `clang: error: '...recursion_depth' in 'struct _ts'`

Có nghĩa pygame recipe của repo không được kích hoạt. Kiểm tra:

```bash
grep p4a.local_recipes buildozer.spec
# phải thấy: p4a.local_recipes = ./recipes
ls recipes/pygame/__init__.py
# phải tồn tại
```

Nếu đã có cả 2 mà vẫn lỗi, xoá build cache và build lại:

```bash
rm -rf .buildozer ~/.buildozer
bash tools/build_android.sh
```

### `cython: command not found` trong giữa build

Venv chưa được activate trước khi gọi buildozer. Dùng `tools/build_android.sh` (đã handle đúng) thay vì gọi `buildozer` trực tiếp.

### Build chậm kinh khủng

Đang build trên `/mnt/d/...` (Windows filesystem). WSL2 đọc/ghi file qua giao thức 9p chậm gấp 5–10× so với ext4 native. Copy project sang `~/action-bird` (Linux filesystem) rồi build:

```bash
cp -r /mnt/d/path/to/project ~/action-bird
cd ~/action-bird
bash tools/build_android.sh
```

### Hết RAM khi build

NDK toolchain compile multi-threaded, có thể ngốn 4-6GB. Set `WSL_MEMORY` trong `%USERPROFILE%\.wslconfig` nếu chạy WSL:

```ini
[wsl2]
memory=8GB
swap=4GB
```

Sau đó `wsl --shutdown` rồi mở lại Ubuntu.

### Google Play Protect chặn cài APK

Đây là **cảnh báo** của Play Protect, không phải lỗi build. APK debug không có production signature.

Trên màn hình cảnh báo, bấm **"Tiếp tục cài đặt"** (text link, không phải nút "Tôi hiểu" lớn). Hoặc tạm tắt Play Protect: Play Store → Avatar → Play Protect → Settings → tắt "Scan apps".

---

## Cấu hình build

### `buildozer.spec`

Các option quan trọng:

| Key | Giá trị | Lý do |
|-----|---------|-------|
| `requirements` | `python3,pygame` | Để recipe pygame của repo được dùng |
| `p4a.local_recipes` | `./recipes` | Kích hoạt custom pygame recipe |
| `android.archs` | `arm64-v8a, armeabi-v7a` | Đa số phone Android còn hỗ trợ |
| `android.api` | `33` | Android 13. Có thể tăng lên 34/35 cho store. |
| `android.minapi` | `21` | Android 5.0 — đủ cho 99% phone hiện tại |
| `orientation` | `portrait` | Game design dọc (400×600 logical) |
| `fullscreen` | `1` | Ẩn status bar Android |
| `source.include_exts` | `py,png,jpg,jpeg,wav,mp3,ogg,json,ttf,otf` | Bundled vào APK |
| `source.include_patterns` | `assets/*,assets/images/*,assets/sounds/*` | Đảm bảo cây thư mục assets được bao gồm |

### Asset notes

- **Music**: pygame trên Android không play tin cậy `.mp3`. Repo đã chứa `assets/sounds/music.ogg` (Vorbis q5). `asset_manager.py` ưu tiên `.ogg` trước.
  Nếu muốn convert lại từ mp3:
  ```bash
  ffmpeg -y -i assets/sounds/music.mp3 -c:a libvorbis -q:a 5 assets/sounds/music.ogg
  ```

- **Asset paths**: trên Android, `os.getcwd()` = thư mục writable storage, **không phải** nơi bundle code. `config.py` đã set `APP_DIR = os.path.dirname(os.path.abspath(__file__))` để các path tài nguyên đều là tuyệt đối.

- **Settings file**: `config.py` tự chuyển save path sang `app_storage_path()` khi chạy trên Android (có thể ghi được; thư mục bundle là read-only).

### Display & gameplay scaling

Game logic dùng resolution 400×600 (portrait 2:3). Phone tỉ lệ thường 9:18 hoặc 9:20 (cao hơn).

`main.py` detect screen size khi khởi động trên Android, tăng `config.HEIGHT` để khớp aspect ratio phone (giữ `WIDTH=400`):

```python
config.HEIGHT = int(config.WIDTH * sh / sw)   # ~889 cho 9:20
config.TUBE_GAP = int(config.TUBE_GAP * scale)   # scale gap pipe theo
```

`spawn_tubes` cũng dùng `h_min/h_max` tỷ lệ với HEIGHT để 2 ống trên-dưới luôn cân đối ngay cả trên phone cao.

`game.py` set display mode với `pygame.FULLSCREEN | pygame.SCALED` trên Android — pygame tự scale framebuffer logical lên kích thước thực, **không vỡ** pixel art.

---

## Cấu trúc thư mục

```
.
├── main.py                  # Entry point — override config.HEIGHT trên Android
├── game.py                  # Main loop, state machine, render
├── entities.py              # Bird, Tube, Item, Laser, Cloud
├── ui.py                    # Lobby, settings, shop, pause overlay
├── asset_manager.py         # Load image/sound, palette swap skin
├── config.py                # Constants, paths, colors, fonts
├── assets/
│   ├── images/              # BG2.png, FB2.png, ...
│   └── sounds/              # *.wav, music.ogg, music.mp3
├── recipes/
│   └── pygame/__init__.py   # Custom p4a recipe (Python 3.11 fix)
├── tools/
│   ├── build_android.sh     # Build wrapper (activate venv + set PATH)
│   └── accept_sdk_licenses.sh   # Pre-accept SDK licenses
├── buildozer.spec           # Buildozer/p4a config
└── BUILD_ANDROID.md         # File này
```

---

## Cài APK lên điện thoại

### Cách 1 — Copy file (đơn giản nhất)

1. Trên điện thoại: Settings → Apps → Special access → Install unknown apps → cho phép app file manager
2. Copy `.apk` qua điện thoại (USB, Drive, Telegram...)
3. Mở file → Install

### Cách 2 — adb từ Windows

```powershell
winget install Google.PlatformTools
adb devices                    # đảm bảo phone connected
adb install bin\actionbird-1.0-arm64-v8a_armeabi-v7a-debug.apk
```

### Cách 3 — adb từ WSL

WSL2 mặc định không thấy USB devices. Dùng `usbipd-win`:

```powershell
winget install usbipd
usbipd list                    # ghi nhớ BUSID của phone
usbipd bind --busid <BUSID>
usbipd attach --wsl --busid <BUSID>
```

Trong WSL:

```bash
~/.buildozer/android/platform/android-sdk/platform-tools/adb devices
~/.buildozer/android/platform/android-sdk/platform-tools/adb install \
    bin/actionbird-1.0-arm64-v8a_armeabi-v7a-debug.apk
```

---

## Debug app trên thiết bị

Xem log Python từ adb:

```bash
~/.buildozer/android/platform/android-sdk/platform-tools/adb logcat -s python -s SDL -s SDL2
```

Crash logs xuất hiện ở đó. Filter `python` để chỉ thấy stdout/stderr của Python.
