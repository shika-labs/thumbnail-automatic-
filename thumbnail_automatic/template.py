"""Utilities for rendering reusable YouTube-style thumbnails."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

from PIL import Image, ImageDraw, ImageFont

Color = Union[str, Tuple[int, int, int]]
PaddingValue = Union[int, Sequence[int]]


def load_config(path: Union[str, Path]) -> Dict:
    """Load a JSON configuration file and attach its base directory."""

    resolved_path = Path(path).expanduser().resolve()
    with resolved_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    data.setdefault("_base_dir", str(resolved_path.parent))
    return data


class ThumbnailTemplate:
    """Render a text-focused thumbnail based on a JSON configuration."""

    def __init__(self, config: Dict):
        self.config = config
        base_dir = config.get("_base_dir")
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        canvas = config.get("canvas", {})
        self.width = int(canvas.get("width", 1280))
        self.height = int(canvas.get("height", 720))
        self.background_color: Color = canvas.get("background_color", "#101010")
        self.image = Image.new("RGB", (self.width, self.height), color=self.background_color)
        self.draw = ImageDraw.Draw(self.image)
        self._stroke_supported = self._detect_stroke_support()
        self.photo_box: Optional[Tuple[int, int, int, int]] = None
        self.photo_anchor: Optional[str] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def render(self) -> Image.Image:
        """Render the thumbnail according to the config and return the PIL image."""
        self._draw_photo()
        self._draw_text_column()
        return self.image

    def save(self, output_path: Union[str, Path]) -> None:
        """Render and save the thumbnail image."""
        self.render()
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.image.save(output_path)

    # ------------------------------------------------------------------
    # Rendering helpers
    # ------------------------------------------------------------------
    def _draw_photo(self) -> None:
        photo_cfg = self.config.get("photo")
        if not photo_cfg:
            return

        anchor = photo_cfg.get("anchor", "right")
        padding = int(photo_cfg.get("padding", 40))
        width_value = photo_cfg.get("width")
        desired_width = int(width_value) if width_value is not None else None
        height_value = photo_cfg.get("height")
        desired_height = int(height_value) if height_value is not None else None
        corner_radius = int(photo_cfg.get("corner_radius", 12))

        override_image = photo_cfg.get("_image")

        if isinstance(override_image, Image.Image):
            photo = override_image.convert("RGB")
        else:
            path_value = photo_cfg.get("path", "")
            path = Path(path_value).expanduser()
            if not path.is_absolute():
                path = self.base_dir / path
            if path.exists():
                with Image.open(path) as raw:
                    photo = raw.convert("RGB")
            else:
                placeholder_label = photo_cfg.get(
                    "placeholder_label",
                    "Thêm ảnh vào\nassets/subject.jpg",
                )
                photo = self._build_photo_placeholder(
                    padding=padding,
                    desired_width=desired_width,
                    desired_height=desired_height,
                    label=placeholder_label,
                )
                corner_radius = max(corner_radius, 0)

        if desired_width and desired_height:
            size = (int(desired_width), int(desired_height))
        elif desired_width:
            ratio = desired_width / photo.width
            size = (int(desired_width), int(photo.height * ratio))
        else:
            target_height = desired_height or (self.height - padding * 2)
            ratio = target_height / photo.height
            size = (int(photo.width * ratio), int(target_height))

        photo = photo.resize(size, Image.LANCZOS)

        if corner_radius > 0:
            mask = Image.new("L", photo.size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([(0, 0), (photo.size[0], photo.size[1])], radius=corner_radius, fill=255)
        else:
            mask = None

        x: int
        y: int
        if anchor == "left":
            x = padding
        else:
            x = self.width - padding - photo.size[0]
        y = max(padding, (self.height - photo.size[1]) // 2)

        if mask:
            self.image.paste(photo, (x, y), mask)
        else:
            self.image.paste(photo, (x, y))

        self.photo_box = (x, y, x + photo.size[0], y + photo.size[1])
        self.photo_anchor = anchor

    def _build_photo_placeholder(
        self,
        padding: int,
        desired_width: Optional[int],
        desired_height: Optional[int],
        label: str,
    ) -> Image.Image:
        """Create a simple instructional image when the real portrait is missing."""

        available_height = max(80, self.height - padding * 2)
        height = int(desired_height or available_height)
        width = int(desired_width or min(self.width // 2, height * 3 // 2))

        placeholder = Image.new("RGB", (max(width, 200), max(height, 200)), color="#2c2c2c")
        overlay = ImageDraw.Draw(placeholder)
        border_color = "#4a4a4a"
        overlay.rectangle(
            [(0, 0), (placeholder.size[0] - 1, placeholder.size[1] - 1)],
            outline=border_color,
            width=6,
        )

        icon_size = min(placeholder.size) // 4
        icon_margin = icon_size // 2
        icon_box = [
            icon_margin,
            icon_margin,
            icon_margin + icon_size,
            icon_margin + icon_size,
        ]
        overlay.rectangle(icon_box, outline="#888888", width=6)
        overlay.line(
            [(icon_box[0], icon_box[3]), (icon_box[2], icon_box[1])],
            fill="#888888",
            width=6,
        )

        font = self._load_font(None, max(24, min(40, placeholder.size[0] // 12)))
        lines = label.split("\n")
        text_height = self._measure_text_height(font, lines, line_spacing=6)
        start_y = (placeholder.size[1] - text_height) // 2 + icon_size // 2
        for idx, line in enumerate(lines):
            line_width = self._text_line_width(font, line, stroke_width=0)
            text_x = max(20, (placeholder.size[0] - line_width) // 2)
            text_y = start_y + idx * (self._line_height(font) + 6)
            overlay.text((text_x, text_y), line, fill="#dddddd", font=font)

        return placeholder

    # ------------------------------------------------------------------
    def _draw_text_column(self) -> None:
        column_cfg = self.config.get("text_column", {})
        x = int(column_cfg.get("x", 60))
        y = int(column_cfg.get("y", 60))
        gap = int(column_cfg.get("gap", 28))
        right_padding = int(column_cfg.get("right_padding", 60))
        photo_gap = int(column_cfg.get("photo_gap", 24))

        max_width_value = column_cfg.get("max_width")
        max_width = int(max_width_value) if max_width_value is not None else None
        if max_width is None:
            max_width = self.width - x - right_padding
            if self.photo_box and self.photo_anchor == "right":
                max_width = min(max_width, self.photo_box[0] - x - photo_gap)

        if self.photo_box and self.photo_anchor == "left":
            start_x = self.photo_box[2] + photo_gap
            x = max(x, start_x)
            if max_width is None:
                max_width = self.width - x - right_padding

        accent_cfg = column_cfg.get("accent")
        if accent_cfg and accent_cfg.get("enabled", True):
            accent_width = int(accent_cfg.get("width", 28))
            accent_offset = int(accent_cfg.get("offset", 20))
            accent_color = accent_cfg.get("fill", "#d70000")
            accent_top = y
            accent_bottom = self.height - int(accent_cfg.get("bottom_padding", 60))
            accent_x0 = x - accent_offset - accent_width
            accent_x1 = accent_x0 + accent_width
            self.draw.rectangle([(accent_x0, accent_top), (accent_x1, accent_bottom)], fill=accent_color)

        blocks = self.config.get("blocks", [])
        for block in blocks:
            text = str(block.get("text", ""))
            if not text:
                continue
            font_size = int(block.get("font_size", 72))
            font = self._load_font(block.get("font_path"), font_size)
            stroke_width = int(block.get("stroke_width", 0))
            stroke_fill = block.get("stroke_fill", "#000000")
            line_spacing = int(block.get("line_spacing", 4))
            block_max_value = block.get("max_width")
            block_max_width = int(block_max_value) if block_max_value is not None else max_width

            lines = self._wrap_text(text, font, block_max_width, stroke_width)
            if not lines or not any(line.strip() for line in lines):
                continue

            text_height = self._measure_text_height(font, lines, line_spacing)
            background_fill = block.get("background_fill")
            background_padding = self._parse_padding(block.get("background_padding", 20)) if background_fill else (0, 0, 0, 0)
            background_radius = int(block.get("background_radius", 18))
            align = block.get("align", "left")

            block_x = x
            block_y = y
            content_x = block_x
            text_container_width = block_max_width

            if background_fill:
                box_width = max(self._text_line_width(font, line, stroke_width) for line in lines)
                box_width = min(box_width, block_max_width)
                padded_width = box_width + background_padding[1] + background_padding[3]
                padded_height = text_height + background_padding[0] + background_padding[2]
                background_box = [
                    block_x,
                    block_y,
                    block_x + padded_width,
                    block_y + padded_height,
                ]
                self.draw.rounded_rectangle(background_box, radius=background_radius, fill=background_fill)
                content_x += background_padding[3]
                block_y += background_padding[0]
                text_container_width = box_width
            for idx, line in enumerate(lines):
                line_y = block_y + idx * (self._line_height(font) + line_spacing)
                if align == "center":
                    container_width = min(text_container_width, block_max_width)
                    line_width = min(self._text_line_width(font, line, stroke_width), container_width)
                    text_x = content_x + max(0, (container_width - line_width) / 2)
                else:
                    text_x = content_x
                self._draw_text(
                    position=(text_x, line_y),
                    text=line,
                    font=font,
                    fill=block.get("fill", "#ffffff"),
                    stroke_width=stroke_width,
                    stroke_fill=stroke_fill,
                )

            total_height = text_height + background_padding[0] + background_padding[2]
            y += total_height + gap

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _detect_stroke_support(self) -> bool:
        """Check whether the current Pillow build supports stroke arguments."""

        test_image = Image.new("RGB", (10, 10))
        tester = ImageDraw.Draw(test_image)
        font = ImageFont.load_default()
        try:
            tester.text((0, 0), "x", font=font, stroke_width=1, stroke_fill="#000000")
        except TypeError:
            return False
        else:
            return True

    def _draw_text(
        self,
        position: Tuple[float, float],
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: Color,
        stroke_width: int,
        stroke_fill: Color,
    ) -> None:
        """Draw text with optional stroke, compatible with older Pillow versions."""

        if stroke_width <= 0:
            self.draw.text(position, text, fill=fill, font=font)
            return

        if self._stroke_supported:
            try:
                self.draw.text(
                    position,
                    text,
                    fill=fill,
                    font=font,
                    stroke_width=stroke_width,
                    stroke_fill=stroke_fill,
                )
                return
            except TypeError:
                self._stroke_supported = False

        x, y = position
        for dx in range(-stroke_width, stroke_width + 1):
            for dy in range(-stroke_width, stroke_width + 1):
                if dx == 0 and dy == 0:
                    continue
                self.draw.text((x + dx, y + dy), text, font=font, fill=stroke_fill)
        self.draw.text(position, text, fill=fill, font=font)

    def _load_font(self, font_path: Optional[str], font_size: int) -> ImageFont.FreeTypeFont:
        if font_path:
            path = Path(font_path).expanduser()
            if not path.is_absolute():
                path = self.base_dir / path
            if path.exists():
                return ImageFont.truetype(str(path), font_size)
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except OSError:
            return ImageFont.load_default()

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int, stroke_width: int) -> List[str]:
        lines: List[str] = []
        current = ""
        for ch in text:
            if ch == "\n":
                lines.append(current)
                current = ""
                continue
            candidate = current + ch
            width = self._text_line_width(font, candidate, stroke_width)
            if width <= max_width or not current:
                current = candidate
            else:
                lines.append(current)
                current = "" if ch.isspace() else ch
        lines.append(current)
        if lines and lines[-1] == "":
            lines.pop()
        return lines or [""]

    def _text_line_width(self, font: ImageFont.FreeTypeFont, text: str, stroke_width: int) -> int:
        if not text:
            return 0
        bbox = font.getbbox(text)
        width = bbox[2] - bbox[0]
        if stroke_width > 0:
            width += stroke_width * 2
        return int(width)

    def _line_height(self, font: ImageFont.FreeTypeFont) -> int:
        ascent, descent = font.getmetrics()
        return ascent + descent

    def _measure_text_height(self, font: ImageFont.FreeTypeFont, lines: Sequence[str], line_spacing: int) -> int:
        if not lines:
            return 0
        line_height = self._line_height(font)
        return line_height * len(lines) + line_spacing * max(0, len(lines) - 1)

    def _parse_padding(self, value: PaddingValue) -> Tuple[int, int, int, int]:
        if isinstance(value, int):
            return (value, value, value, value)
        values = list(value)
        if len(values) == 2:
            top = bottom = int(values[0])
            left = right = int(values[1])
            return (top, right, bottom, left)
        if len(values) == 4:
            top, right, bottom, left = (int(v) for v in values)
            return (top, right, bottom, left)
        raise ValueError("padding must be an int, [vertical, horizontal], or [top, right, bottom, left]")
