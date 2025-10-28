# Thumbnail Automatic

Generate reusable YouTube-style thumbnails from a JSON configuration. The template is inspired by bold Japanese thumbnails where the text can be swapped in quickly for new videos.

## Requirements

- Python 3.10+
- [Pillow](https://python-pillow.org/) (install with `pip install -r requirements.txt`)
- [Streamlit](https://streamlit.io/) để chạy giao diện web cục bộ.
- Japanese fonts. The sample configuration references the free [Noto Sans JP](https://fonts.google.com/noto/specimen/Noto+Sans+JP) family. Download the `Bold` and `Black` weights and place the `.otf` files inside the `fonts/` directory.

## Project structure

```
.
├── assets/                 # Put your subject photos here (not tracked in git)
├── config/                 # JSON templates that define text, colors, and layout
├── fonts/                  # Custom fonts used by the templates
├── output/                 # Generated thumbnails
├── app.py                  # Streamlit app cho người không rành code
├── generate_thumbnail.py   # CLI for rendering thumbnails
└── thumbnail_automatic/    # Rendering library
```

## Quick start

1. Install dependencies and download fonts:

   ```bash
   pip install -r requirements.txt
   # Download NotoSansJP-Bold.otf and NotoSansJP-Black.otf into the fonts/ folder
   ```

2. Copy your portrait or product photo into `assets/subject.jpg` (or update the path in the config file).

3. Render the example thumbnail:

   ```bash
   python generate_thumbnail.py
   ```

   or, if you want to pick a different template file manually:

   ```bash
   python generate_thumbnail.py config/sample_thumbnail.json
   ```

   The rendered image will be saved to `output/sample_thumbnail.png`. If the portrait photo
   is missing the script automatically draws a grey placeholder telling you where to put
   your own picture (`assets/subject.jpg`).

## Tôi không rành về code, dùng sao?

### Cách 1: mở app web (dễ nhất)

#### Bản cực kỳ chi tiết cho người mới

1. **Cài Python (nếu chưa có):**
   - Tải bản mới nhất từ [python.org/downloads](https://www.python.org/downloads/) và chạy file cài đặt.
   - Trong quá trình cài trên Windows nhớ tick vào ô **"Add Python to PATH"** trước khi bấm Install.
   - Sau khi cài, mở Command Prompt (Windows) hoặc Terminal (macOS) rồi gõ `python --version`. Nếu thấy hiện `Python 3.x.x` là đã xong.
2. **Tải dự án về máy:** bạn có thể dùng nút Download ZIP trên GitHub rồi giải nén, hoặc dùng `git clone ...` nếu quen Git.
3. **Mở thư mục dự án:**
   - Windows: mở thư mục vừa giải nén, giữ Shift + bấm chuột phải vào vùng trống, chọn *Open PowerShell window here* hoặc *Open in Terminal*.
   - macOS: mở ứng dụng Terminal, gõ `cd` rồi kéo thả thư mục dự án vào cửa sổ Terminal để tự điền đường dẫn, sau đó Enter.
4. **Cài thư viện cần thiết:**
   ```bash
   pip install -r requirements.txt
   ```
   Lần đầu chạy có thể mất vài phút để tải thư viện.
5. **Chạy ứng dụng web:**
   ```bash
   streamlit run app.py
   ```
   Sau vài giây, Streamlit sẽ in ra dòng `Local URL: http://localhost:8501`. Nếu trình duyệt không tự mở, hãy copy đường link này và dán vào Chrome/Edge.
6. **Sử dụng app:**
   - Điền nội dung chữ vào các ô trong bảng bên trái.
   - (Không bắt buộc) Bấm nút tải ảnh để chọn ảnh nhân vật/sản phẩm.
   - Ảnh xem trước được cập nhật ngay bên phải.
   - Khi hài lòng, bấm **"Tải về ảnh PNG"** để lưu ảnh vào máy.

> Mẹo: nếu Streamlit hỏi muốn mở firewall hay không (Windows), chọn Allow để app hoạt động.

### Cách 2: chạy bằng terminal (không cần trình duyệt)

> Các bước này dành cho người mới bắt đầu, bạn chỉ cần copy lệnh và dán vào cửa sổ lệnh.

1. Mở thư mục dự án, gõ `python generate_thumbnail.py --interactive` và bấm Enter.
2. Chương trình sẽ lần lượt hỏi bạn phần chữ muốn thay. Nhập nội dung mới (hoặc bấm Enter để giữ nguyên).
3. Sau khi hoàn thành, terminal sẽ báo đường dẫn file kết quả. Mở file PNG trong thư mục `output/` để xem.

Bạn có thể chạy lại câu lệnh bất cứ lúc nào để tạo thumbnail mới mà không phải chỉnh sửa file JSON.

## Updating the text quickly

Each text block inside the configuration file has an optional `id` field. Use the `--interactive`
flag for a friendly prompt, or the `--text` override flag to swap the copy without editing JSON:

```bash
python generate_thumbnail.py --interactive

# Hoặc dùng câu lệnh ngắn khi bạn đã quen:
python generate_thumbnail.py config/sample_thumbnail.json \
  --text headline="70代でも遅くない" \
  --text guest="山田 太郎"
```

You can add more blocks with their own fonts, sizes, and colors. The fields supported by each block are:

| Field | Description |
| ----- | ----------- |
| `id` | Unique identifier for CLI overrides. |
| `text` | Text content. Supports manual line breaks with `\n`. |
| `font_path` | Path to a `.ttf`/`.otf` font file. Falls back to DejaVu Sans if missing. |
| `font_size` | Font size in points. |
| `fill` | Text color (hex or RGB tuple). |
| `stroke_width` / `stroke_fill` | Outline thickness and color for extra contrast. |
| `background_fill` | Optional rounded rectangle behind the text. |
| `background_padding` | Padding around the text inside the background box. Accepts a single value, `[vertical, horizontal]`, or `[top, right, bottom, left]`. |
| `background_radius` | Corner radius for the background box. |
| `line_spacing` | Extra pixels between wrapped lines. |
| `max_width` | Maximum width in pixels before the text wraps to a new line. |
| `align` | `left` or `center` alignment inside its container. |

## Customizing the layout

- Adjust the `text_column` section to move the text stack, spacing, and accent bar.
- Change the `photo` settings to control padding, rounded corners, and where the portrait sits.
- Duplicate the JSON file to create new templates. Only the copy and the CLI overrides change between videos, so you can keep a consistent design.

## Automation tips

Integrate the script with your workflow by combining it with a shell script or task runner. For example, this snippet renders two language variants using the same layout:

```bash
python generate_thumbnail.py config/sample_thumbnail.json --output output/video-ja.png --text headline="50代から人生が\n崩壊する習慣"
python generate_thumbnail.py config/sample_thumbnail.json --output output/video-en.png --text headline="Habits that ruin\nyour 50s"
```

The output directory is ignored by git so you can commit only the reusable template files.
