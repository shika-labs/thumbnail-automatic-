"""Simple Streamlit app for rendering reusable thumbnails without coding."""

from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Dict, Iterable

import streamlit as st
from PIL import Image

from thumbnail_automatic import ThumbnailTemplate, load_config


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "config" / "sample_thumbnail.json"


def deep_copy_config(config: Dict) -> Dict:
    """Create a copy of the configuration safe to mutate in the UI."""

    return json.loads(json.dumps(config))


def iter_text_blocks(config: Dict) -> Iterable[Dict]:
    """Yield each text block from the configuration."""

    blocks = config.get("blocks", [])
    for block in blocks:
        if isinstance(block, dict):
            yield block


def render_thumbnail(config: Dict) -> Image.Image:
    """Render a thumbnail using the shared template class."""

    template = ThumbnailTemplate(config)
    return template.render()


def main() -> None:
    st.set_page_config(page_title="Thumbnail Generator", page_icon="🖼️")
    st.title("Tạo thumbnail mà không cần biết code")
    st.write(
        "Điền nội dung mong muốn ở bên trái, tải ảnh nhân vật (nếu có) rồi tải về file PNG"
        " được tạo tự động."
    )

    with st.sidebar:
        st.header("Cấu hình")
        st.caption(
            "Bạn có thể dùng mẫu có sẵn hoặc tải file JSON tùy chỉnh nếu đã có template riêng."
        )

        uploaded_config_file = st.file_uploader("Tải file cấu hình JSON", type="json")

        if uploaded_config_file is not None:
            try:
                loaded_config = json.load(uploaded_config_file)
            except json.JSONDecodeError as exc:
                st.error(f"Không đọc được file JSON: {exc}")
                st.stop()
        else:
            loaded_config = load_config(DEFAULT_CONFIG_PATH)

        uploaded_photo = st.file_uploader(
            "Chọn ảnh nhân vật (JPG/PNG)",
            type=["jpg", "jpeg", "png", "webp"],
        )

    config = deep_copy_config(loaded_config)
    config.setdefault("_base_dir", str(BASE_DIR))

    st.subheader("Nội dung chữ")
    st.caption("Chỉnh sửa từng phần, bấm Enter để xuống dòng.")

    for idx, block in enumerate(iter_text_blocks(config)):
        default_text = str(block.get("text", ""))
        label = block.get("id") or f"Khối chữ {idx + 1}"
        multiline = "\n" in default_text or len(default_text) > 40
        if multiline:
            updated_text = st.text_area(label, default_text, height=120)
        else:
            updated_text = st.text_input(label, default_text)
        block["text"] = updated_text

    if uploaded_photo is not None:
        try:
            photo_image = Image.open(uploaded_photo).convert("RGB")
        except Exception as exc:  # pragma: no cover - display error in UI only
            st.error(f"Không đọc được ảnh đã tải lên: {exc}")
            st.stop()
        config.setdefault("photo", {})["_image"] = photo_image

    thumbnail = render_thumbnail(config)

    st.subheader("Kết quả")
    st.image(thumbnail, caption="Xem thử thumbnail", use_column_width=True)

    buffer = io.BytesIO()
    thumbnail.save(buffer, format="PNG")
    buffer.seek(0)
    suggested_name = Path(config.get("output_path", "thumbnail.png")).name

    st.download_button(
        "Tải về ảnh PNG",
        buffer.getvalue(),
        file_name=suggested_name,
        mime="image/png",
    )


if __name__ == "__main__":
    main()
