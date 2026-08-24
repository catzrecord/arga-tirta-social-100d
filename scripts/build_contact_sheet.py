#!/usr/bin/env python3
"""Build a compact visual overview of all 184 campaign days."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
POSTS = ROOT / "public" / "posts" / "arga-tirta-6m-v2"
OUTPUT = ROOT / "campaign-v2" / "reports" / "feed-contact-sheet-final.jpg"


def first_visual(day: Path) -> Path:
    for name in ("slide-01.jpg", "post.jpg", "poster.jpg"):
        candidate = day / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No cover image in {day}")


def main() -> None:
    days = sorted(path for path in POSTS.glob("day-*") if path.is_dir())
    if len(days) != 184:
        raise SystemExit(f"Expected 184 days, found {len(days)}")

    columns = 14
    thumb_w, thumb_h = 108, 150
    label_h = 20
    rows = (len(days) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_w, rows * (thumb_h + label_h)), "#081d32")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()

    for index, day in enumerate(days):
        source = Image.open(first_visual(day)).convert("RGB")
        source.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x = (index % columns) * thumb_w
        y = (index // columns) * (thumb_h + label_h)
        tile = Image.new("RGB", (thumb_w, thumb_h), "#dff6ff")
        tile.paste(source, ((thumb_w - source.width) // 2, (thumb_h - source.height) // 2))
        sheet.paste(tile, (x, y))
        label = f"D{index + 1:03d}"
        draw.text((x + 5, y + thumb_h + 4), label, fill="#ffffff", font=font)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUTPUT, quality=90, optimize=True, progressive=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
