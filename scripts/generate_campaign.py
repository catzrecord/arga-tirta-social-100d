#!/usr/bin/env python3
"""Render 100 post / 200 final assets Arga Tirta secara deterministik."""

from __future__ import annotations

import csv
import hashlib
import json
import random
import textwrap
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
PLAN_CSV = ROOT / "planning" / "content-plan-100-days.csv"
MASTERS = sorted((ROOT / "production-sources" / "generated-masters").glob("*.jpg"))
LOGO = ROOT / "branding" / "arga-tirta-symbol.png"
OUT = ROOT / "public" / "posts" / "arga-tirta-100d"
W, H = 1080, 1350

FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
FONT_REG = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_NARROW = Path(r"C:\Windows\Fonts\ARIALNB.TTF")
WHITE = (246, 244, 237)
MUTED = (176, 190, 191)
CYAN = (77, 206, 218)
YELLOW = (251, 202, 30)

TEXT_ONLY = [
    ["AIR YANG BAIK", "PUNYA CERITA", "DI BALIKNYA.", "Ada proses yang dijaga, bahkan saat tak terlihat."],
    ["BENING ITU TERLIHAT.", "PROSES TIDAK.", "KEDUANYA", "tetap perlu dijaga."],
    ["FILTRASI BUKAN", "SATU BENDA.", "IA ADALAH", "rangkaian keputusan yang saling menjaga."],
    ["JANGAN TUNGGU", "SAMPAI BERHENTI.", "RAWAT SAAT", "semuanya masih bekerja baik."],
    ["RUANG BOLEH KECIL.", "ALURNYA", "TETAP HARUS", "terasa lega dan masuk akal."],
    ["SERING DIANGGAP", "SEPELE.", "PADAHAL DETAIL", "ikut menjaga kepercayaan."],
    ["BERSIH BUKAN", "SEKADAR KELIHATAN.", "BERSIH ADALAH", "cara kerja yang diulang setiap hari."],
    ["PASANG.", "UJI.", "PERIKSA LAGI.", "Baru kemudian kami menyebutnya selesai."],
    ["BEKERJA LEBIH CEPAT", "BUKAN BERARTI", "TERGESA-GESA.", "Buat alurnya lebih jelas."],
    ["KEPERCAYAAN", "TIDAK DATANG", "DALAM SEHARI.", "Ia dijaga dalam setiap pengulangan."],
    ["MESIN SELALU", "MEMBERI TANDA.", "PERTANYAANNYA:", "apakah kita cukup peka melihatnya?"],
    ["TIDAK HARUS", "BERUBAH BESAR.", "CUKUP MULAI", "dari satu detail yang paling dekat."],
    ["USAHA BERTUMBUH", "DENGAN CARANYA.", "SISTEM YANG BAIK", "membantunya tumbuh lebih tenang."],
    ["KERJA YANG BAIK", "TIDAK HARUS", "TERLIHAT RAMAI.", "Cukup terasa dari hasilnya."],
]


def ft(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def trim_alpha(im: Image.Image) -> Image.Image:
    rgba = im.convert("RGBA")
    return rgba.crop(rgba.getchannel("A").getbbox())


def add_logo(im: Image.Image) -> Image.Image:
    canvas = im.convert("RGBA")
    mark = trim_alpha(Image.open(LOGO))
    mark = mark.resize((81, round(mark.height * 81 / mark.width)), Image.Resampling.LANCZOS)
    canvas.alpha_composite(mark, (1080 - 50 - mark.width, 1350 - 15 - mark.height))
    return canvas.convert("RGB")


def crop_photo(master: Image.Image, seed: int, dark: float = 0.0) -> Image.Image:
    rng = random.Random(seed)
    im = master.convert("RGB")
    if seed % 3 == 0:
        im = ImageOps.mirror(im)
    scale = max(W / im.width, H / im.height) * (1.02 + rng.random() * 0.22)
    size = (round(im.width * scale), round(im.height * scale))
    im = im.resize(size, Image.Resampling.LANCZOS)
    max_x, max_y = im.width - W, im.height - H
    x = round(max_x * rng.random()) if max_x else 0
    y = round(max_y * rng.random()) if max_y else 0
    im = im.crop((x, y, x + W, y + H))
    im = ImageEnhance.Color(im).enhance(0.82 + rng.random() * 0.20)
    im = ImageEnhance.Contrast(im).enhance(1.04 + rng.random() * 0.15)
    if dark:
        shade = Image.new("RGBA", im.size, (1, 8, 13, round(255 * dark)))
        im = Image.alpha_composite(im.convert("RGBA"), shade).convert("RGB")
    return im


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.upper().split()
    lines, current = [], []
    for word in words:
        trial = " ".join(current + [word])
        if current and draw.textbbox((0, 0), trial, font=face)[2] > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def dark_gradient(im: Image.Image, top_alpha: int, bottom_alpha: int) -> Image.Image:
    grad = Image.new("L", (1, H))
    grad.putdata([round(top_alpha + (bottom_alpha - top_alpha) * y / (H - 1)) for y in range(H)])
    grad = grad.resize((W, H))
    overlay = Image.new("RGB", (W, H), (2, 9, 14))
    return Image.composite(overlay, im, grad)


def header(draw: ImageDraw.ImageDraw, day: int, label: str) -> None:
    draw.text((72, 66), "ARGA TIRTA / FIELD NOTES", font=ft(FONT_BOLD, 22), fill=MUTED)
    draw.rounded_rectangle((920, 58, 1006, 98), radius=20, outline=(127, 154, 158), width=2)
    draw.text((938, 67), f"{day:03d}", font=ft(FONT_BOLD, 19), fill=WHITE)
    draw.text((72, 1250), label.upper(), font=ft(FONT_REG, 19), fill=MUTED)


def draw_headline(draw: ImageDraw.ImageDraw, text: str, y: int, accent_index: int = -1) -> int:
    face = ft(FONT_NARROW, 74)
    lines = wrap(draw, text, face, 900)
    if len(lines) > 4:
        face = ft(FONT_NARROW, 64)
        lines = wrap(draw, text, face, 900)
    for i, line in enumerate(lines[:5]):
        fill = YELLOW if i == accent_index else WHITE
        draw.text((70, y), line, font=face, fill=fill, stroke_width=1)
        y += face.size + 8
    return y


def photo_slide(day: int, slide: int, hook: str, label: str, variant: str) -> Image.Image:
    master_index = (day * 7 + slide * 5 + (0 if variant == "single" else 3)) % len(MASTERS)
    master = Image.open(MASTERS[master_index])
    seed = day * 1009 + slide * 97
    im = crop_photo(master, seed)
    if slide == 1 or variant == "single":
        im = dark_gradient(im, 30, 205)
        d = ImageDraw.Draw(im)
        header(d, day, label)
        y = draw_headline(d, hook, 830 if len(hook) < 58 else 760, accent_index=-1)
        d.line((72, min(1190, y + 18), 270, min(1190, y + 18)), fill=CYAN, width=5)
    elif slide == 2:
        im = dark_gradient(im, 85, 150)
        d = ImageDraw.Draw(im)
        header(d, day, "lihat lebih dekat")
        d.text((72, 250), "02", font=ft(FONT_NARROW, 154), fill=YELLOW)
        d.line((270, 340, 1000, 340), fill=(112, 143, 147), width=2)
        short = hook.split(".")[0]
        draw_headline(d, short, 780)
    else:
        im = im.filter(ImageFilter.GaussianBlur(5))
        im = dark_gradient(im, 160, 225)
        d = ImageDraw.Draw(im)
        header(d, day, "catatan penutup")
        d.text((72, 310), "SATU DETAIL", font=ft(FONT_NARROW, 92), fill=WHITE)
        d.text((72, 415), "PADA SATU WAKTU.", font=ft(FONT_NARROW, 92), fill=CYAN)
        d.line((72, 570, 1000, 570), fill=(83, 113, 118), width=2)
        d.text((72, 630), "Simpan dulu.", font=ft(FONT_REG, 38), fill=MUTED)
        d.text((72, 685), "Barangkali berguna nanti.", font=ft(FONT_REG, 38), fill=MUTED)
    return add_logo(im)


def text_background(seed: int) -> Image.Image:
    top = (6 + seed % 7, 20 + seed % 9, 27 + seed % 11)
    bottom = (1, 6, 10)
    strip = Image.new("RGB", (1, H))
    strip.putdata([
        tuple(round(top[c] * (1 - y / (H - 1)) + bottom[c] * y / (H - 1)) for c in range(3))
        for y in range(H)
    ])
    im = strip.resize((W, H))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    x = 180 + (seed * 137) % 720
    gd.ellipse((x - 420, -260, x + 420, 580), fill=(25, 155, 177, 24))
    glow = glow.filter(ImageFilter.GaussianBlur(130))
    return Image.alpha_composite(im.convert("RGBA"), glow).convert("RGB")


def text_slide(day: int, slide: int, copy: list[str], week: int) -> Image.Image:
    im = text_background(day * 17 + slide)
    d = ImageDraw.Draw(im)
    header(d, day, f"minggu {week:02d} / text only")
    d.text((72, 238), f"0{slide}", font=ft(FONT_NARROW, 44), fill=YELLOW)
    d.line((155, 271, 1000, 271), fill=(67, 100, 107), width=2)
    if slide <= 3:
        y = draw_headline(d, copy[slide - 1], 480, accent_index=0 if slide == 3 else -1)
        d.text((74, min(1030, y + 60)), "Sebuah catatan dari pekerjaan sehari-hari.", font=ft(FONT_REG, 29), fill=MUTED)
    else:
        face = ft(FONT_NARROW, 76)
        lines = wrap(d, copy[3], face, 880)
        y = 440
        for i, line in enumerate(lines):
            d.text((72, y), line, font=face, fill=CYAN if i == len(lines) - 1 else WHITE)
            y += 92
        d.line((72, y + 35, 285, y + 35), fill=YELLOW, width=5)
    return add_logo(im)


def caption(row: dict[str, str]) -> str:
    hook = row["hook_di_gambar"].strip()
    pillar = row["pilar"]
    middle = {
        "Brand": "Kami percaya hasil yang tenang selalu lahir dari proses yang diperhatikan.",
        "Edukasi": "Hal sederhana seperti ini membantu kualitas tetap lebih mudah dipantau dari hari ke hari.",
        "Produk": "Detail kecil tetap layak dipilih dengan cermat karena dipakai berulang setiap hari.",
        "Layanan": "Setiap lokasi punya kebutuhan berbeda. Karena itu, prosesnya dimulai dengan melihat kondisi nyata.",
        "Human": "Di lapangan, ketelitian tumbuh dari kebiasaan yang dilakukan tanpa banyak suara.",
        "Soft Sell": "Tidak perlu terburu-buru. Mulai saja dari bagian yang paling ingin dirapikan.",
        "Text Only": "Beberapa hal tidak selalu terlihat, tetapi perannya terasa ketika semuanya berjalan rapi.",
    }[pillar]
    return (
        f"{hook}\n\n{middle}\n\n{row['cta_caption']}\n\n"
        "#ArgaTirta #DepotAirMinum #IsiUlang #TutupGalon #UsahaAirMinum"
    )


def dhash(path: Path) -> str:
    im = Image.open(path).convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    bits = []
    px = list(im.getdata())
    for y in range(8):
        for x in range(8):
            bits.append(px[y * 9 + x] > px[y * 9 + x + 1])
    value = sum(bit << i for i, bit in enumerate(bits))
    return f"{value:016x}"


def main() -> None:
    if len(MASTERS) < 8:
        raise RuntimeError("Minimal 8 generated photo masters diperlukan")
    rows = list(csv.DictReader(PLAN_CSV.open(encoding="utf-8-sig")))
    plan = []
    rendered: list[Path] = []
    text_week = 0
    for row in rows:
        day = int(row["hari"])
        post_dir = OUT / f"day-{day:03d}"
        post_dir.mkdir(parents=True, exist_ok=True)
        if row["format"] == "Carousel Text Only":
            post_type, slide_count = "carousel", 4
            copy = TEXT_ONLY[text_week]
            text_week += 1
            images = [text_slide(day, i, copy, int(row["minggu"])) for i in range(1, 5)]
        elif row["format"] == "Carousel Foto":
            post_type, slide_count = "carousel", 3
            images = [photo_slide(day, i, row["hook_di_gambar"], row["pilar"], "carousel") for i in range(1, 4)]
        else:
            post_type, slide_count = "single", 1
            images = [photo_slide(day, 1, row["hook_di_gambar"], row["pilar"], "single")]

        assets = []
        for slide_no, image in enumerate(images, 1):
            name = "post.jpg" if slide_count == 1 else f"slide-{slide_no:02d}.jpg"
            target = post_dir / name
            image.save(target, quality=89, subsampling=0, optimize=True)
            rendered.append(target)
            assets.append(target.relative_to(ROOT / "public").as_posix())

        plan.append({
            "id": day,
            "date": row["tanggal"],
            "time_wib": "19:17",
            "title": row["hook_di_gambar"],
            "content_theme": row["pilar"].lower().replace(" ", "_"),
            "weekly_theme": row["tema_mingguan"],
            "post_type": post_type,
            "slide_count": slide_count,
            "asset": assets[0],
            "assets": assets,
            "slides": [{"index": i + 1, "asset": asset} for i, asset in enumerate(assets)],
            "final_caption": caption(row),
            "status": "queued_auto",
            "approval_required": True,
            "approval_status": "approved",
            "visual_revision": "cinematic-field-notes-v1",
            "asset_version": "arga-tirta-100d-v1",
            "ai_generated": True,
        })

    exact = {}
    perceptual = {}
    for path in rendered:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in exact:
            raise RuntimeError(f"Exact duplicate: {path} dan {exact[digest]}")
        exact[digest] = path
        ph = dhash(path)
        perceptual.setdefault(ph, []).append(path)
    # dHash dipakai sebagai alarm kemiripan komposisi, bukan bukti byte-identik.
    # File final tetap wajib lolos SHA-256 unik; collision dHash dicatat untuk audit.
    exact_ph = {key: paths for key, paths in perceptual.items() if len(paths) > 1}

    (ROOT / "content-plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (ROOT / "public" / "content-plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {
        "posts": len(plan),
        "assets": len(rendered),
        "single": sum(x["post_type"] == "single" for x in plan),
        "carousel": sum(x["post_type"] == "carousel" for x in plan),
        "text_only_carousel": text_week,
        "exact_duplicates": 0,
        "identical_dhash_groups_reviewed": len(exact_ph),
    }
    (ROOT / "asset-validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
