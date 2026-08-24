#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
CALENDAR = ROOT / "planning/pak-tirto-6-months/calendar-daily.json"
PUBLIC_ROOT = ROOT / "public/posts/arga-tirta-6m-v2"
CAMPAIGN = ROOT / "campaign-v2"
MASTER_DIR = CAMPAIGN / "masters"
FONT_DIR = CAMPAIGN / "fonts"
WEEK1 = ROOT / "production/week-01-2026-08-24"
BEBAS = FONT_DIR / "BebasNeue-Regular.ttf"
MONTSERRAT = FONT_DIR / "Montserrat-Variable.ttf"

BLUE = (0, 91, 211)
CYAN = (15, 156, 229)
DEEP = (0, 48, 120)
INK = (8, 40, 78)
WHITE = (255, 255, 255)
VERSION = "arga-tirta-6m-v2-20260824"
AUDIO_KEYS = ["respect", "sweetly", "summer-inside", "sometimes", "young-beautiful", "end-of-august", "august", "love-story"]

MASTER_SAFE = {
    1: (245, 78, 470, "light"),
    2: (80, 82, 650, "light"),
    3: (480, 78, 535, "sky"),
    4: (58, 74, 535, "light"),
    5: (125, 66, 820, "sky"),
    6: (470, 60, 545, "light"),
    7: (520, 215, 515, "card"),
}

POINTS = {
    "edukasi": [
        ("LIHAT KONDISINYA", "Mulai dari kondisi nyata, bukan asumsi atau jumlah alat."),
        ("CATAT PERUBAHANNYA", "Angka dan catatan membantu keputusan tetap konsisten."),
        ("SUSUN LANGKAHNYA", "Urutan yang jelas membuat pekerjaan lebih mudah diulang."),
    ],
    "maintenance": [
        ("DENGARKAN GEJALANYA", "Perubahan suara, tekanan, dan aliran layak diperhatikan."),
        ("PERIKSA BERURUTAN", "Cek sumber masalah sebelum memilih komponen pengganti."),
        ("JADWALKAN SERVICE", "Perawatan terencana membantu operasional tetap berjalan."),
    ],
    "produk_layanan": [
        ("COCOKKAN KEBUTUHAN", "Produk dan kapasitas mengikuti kondisi serta target usaha."),
        ("HITUNG PEMAKAIAN", "Stok yang sehat mengikuti ritme operasional harian."),
        ("KONSULTASIKAN DULU", "Detail kecil menentukan kemudahan pemakaian berikutnya."),
    ],
    "brand_humor": [
        ("KELIHATAN SEPELE", "Pak Tirto tahu detail kecil sering menjadi pekerjaan besar."),
        ("PAK UDIN PUNYA CARA", "Santai boleh, urutan teknis tetap harus tepat."),
        ("BU YATI SUDAH CATAT", "Kalau sudah masuk buku Bu Yati, semua jadi lebih jelas."),
    ],
    "conversion_proof": [
        ("BACA LOKASINYA", "Ukuran, utilitas, dan alur kerja menentukan rancangan awal."),
        ("SUSUN SISTEMNYA", "Desain dibuat agar siap dipakai dan mudah dirawat."),
        ("LANJUT KONSULTASI", "Kirim foto atau ukuran lokasi untuk pembacaan awal."),
    ],
    "community": [
        ("PILIH TIMMU", "Setiap depot punya kebiasaan dan tantangan yang berbeda."),
        ("CERITAKAN KONDISINYA", "Jawabanmu membantu kami membuat konten yang lebih berguna."),
        ("LANJUT DI KOMENTAR", "Bagikan pengalaman sederhana dari tempat usahamu."),
    ],
}


def mfont(size: int, variation: str):
    font = ImageFont.truetype(str(MONTSERRAT), size)
    font.set_variation_by_name(variation)
    return font


def bfont(size: int):
    return ImageFont.truetype(str(BEBAS), size)


def fit_bebas(draw, text, max_width, max_height, start=95, minimum=38):
    words = text.split()
    for size in range(start, minimum - 1, -1):
        font = bfont(size)
        for line_count in (1, 2, 3):
            lines, current = [], ""
            for word in words:
                test = f"{current} {word}".strip()
                if draw.textbbox((0, 0), test, font=font)[2] <= max_width or not current:
                    current = test
                else:
                    lines.append(current)
                    current = word
            if current:
                lines.append(current)
            if len(lines) <= line_count:
                bbox = draw.multiline_textbbox((0, 0), "\n".join(lines), font=font, spacing=-5)
                if bbox[3] - bbox[1] <= max_height:
                    return font, lines
    return bfont(minimum), [text]


def wrapped(draw, text, font, max_width, max_lines=5):
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:max_lines]


def cover_crop(im, size, x_bias=0.0, y_bias=0.0):
    tw, th = size
    target = tw / th
    w, h = im.size
    if w / h < target:
        crop_h = w / target
        space = h - crop_h
        y0 = space / 2 + y_bias * space / 2
        y0 = max(0, min(space, y0))
        box = (0, int(round(y0)), w, int(round(y0 + crop_h)))
    else:
        crop_w = h * target
        space = w - crop_w
        x0 = space / 2 + x_bias * space / 2
        x0 = max(0, min(space, x0))
        box = (int(round(x0)), 0, int(round(x0 + crop_w)), h)
    return im.crop(box).resize(size, Image.Resampling.LANCZOS)


def short_headline(row):
    source = row.get("national_day_hook") or row["hook"]
    clean = source.replace("—", " ").replace(":", " ").replace("?", "").replace("!", "").replace(".", "")
    words = clean.split()
    if len(words) > 6:
        words = words[:6]
    return " ".join(words).upper()


def choose_master(row):
    cast = row["featured_cast"]
    text = f"{row['weekly_theme']} {row['hook']}".lower()
    if row.get("national_day"):
        return 2
    if "Pak Tirto + Bu Yati + Pak Udin" in cast:
        return 6
    if "Bu Yati + Pak Udin" in cast:
        return 7
    if "Pak Tirto + Bu Yati" in cast:
        return 4
    if "Pak Tirto + Pak Udin" in cast:
        return 5 if row["week"] % 2 else 3
    if cast == "Bu Yati":
        return 4 if row["week"] % 2 else 7
    if cast == "Pak Udin":
        return 3 if row["week"] % 2 else 5
    if any(key in text for key in ("survei", "ruang", "instalasi", "timeline", "desain")):
        return 6
    if any(key in text for key in ("pipa", "service", "filter", "troubleshooting", "sparepart")):
        return 5
    return 1 if row["week"] % 2 else 2


def add_grade(im, variant):
    grades = [
        (1.02, 1.08, 1.04, (0, 92, 215, 18)),
        (1.05, 1.12, 1.02, (0, 180, 235, 12)),
        (.98, 1.16, 1.08, (0, 48, 120, 22)),
        (1.07, 1.04, 1.06, (255, 176, 65, 10)),
    ]
    brightness, contrast, color, tint = grades[variant % len(grades)]
    im = ImageEnhance.Brightness(im).enhance(brightness)
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(color)
    ov = Image.new("RGBA", im.size, tint)
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def glow_motif(im, row, variant):
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    d = ImageDraw.Draw(ov)
    w, h = im.size
    pillar = row["pillar"]
    seed = row["id"]
    if pillar in ("maintenance", "edukasi"):
        pts = [(int(w * .04), int(h * (.72 - .04 * (variant % 3)))), (int(w * .34), int(h * .58)), (int(w * .63), int(h * .66)), (int(w * .96), int(h * .48))]
        gd.line(pts, fill=(0, 184, 255, 190), width=16, joint="curve")
        d.line(pts, fill=(110, 225, 255, 220), width=3, joint="curve")
    elif pillar == "produk_layanan":
        for i in range(5):
            x = 80 + i * 78 + (seed % 3) * 12
            y = 1080 - i * 22
            gd.ellipse((x - 42, y - 42, x + 42, y + 42), outline=(0, 160, 255, 180), width=14)
            d.ellipse((x - 42, y - 42, x + 42, y + 42), outline=(160, 235, 255, 210), width=3)
    elif pillar == "conversion_proof":
        for x in range(80, 1050, 95):
            gd.line((x, 760, x, 1320), fill=(0, 164, 255, 100), width=8)
        for y in range(770, 1330, 95):
            gd.line((60, y, 1040, y), fill=(0, 164, 255, 100), width=8)
    elif pillar == "community":
        gd.arc((90, 770, 990, 1460), 190, 350, fill=(0, 180, 255, 180), width=18)
        d.arc((90, 770, 990, 1460), 190, 350, fill=(170, 240, 255, 220), width=3)
    else:
        x = 90 + (variant % 4) * 170
        gd.rounded_rectangle((x, 820, x + 370, 1100), radius=48, outline=(0, 174, 255, 150), width=18)
        d.rounded_rectangle((x, 820, x + 370, 1100), radius=48, outline=(150, 235, 255, 210), width=3)
    glow = glow.filter(ImageFilter.GaussianBlur(13))
    ov = Image.alpha_composite(glow, ov)
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")


def brand(draw, x, y, tone):
    color = WHITE if tone == "white" else DEEP
    font = mfont(25, "ExtraBold")
    draw.text((x, y), "ARGA\nTIRTA", font=font, fill=color, spacing=-5)
    draw.text((x, y + 61), "WATER SYSTEM", font=mfont(9, "SemiBold"), fill=color)
    draw.rounded_rectangle((x, y + 80, x + 150, y + 86), radius=3, fill=color)


def compose_cover(row, size=(1080, 1350), reel=False):
    master_id = choose_master(row)
    im = Image.open(MASTER_DIR / f"day-{master_id:02d}-digital-imaging-v2.png").convert("RGB")
    variant = row["id"] - 1
    flip = (row["week"] + row["id"]) % 3 == 0
    if flip:
        im = ImageOps.mirror(im)
    x_bias = (-.55, -.2, 0, .25, .55)[variant % 5]
    y_bias = (-.35, -.12, .05, .22)[variant % 4]
    im = cover_crop(im, size, x_bias, y_bias)
    im = add_grade(im, variant)
    im = glow_motif(im, row, variant)

    scale = size[0] / 1080
    sx, sy, sw, tone = MASTER_SAFE[master_id]
    if flip:
        sx = 1080 - sx - sw
    if reel:
        sy = max(230, sy + 120)
    x, y, width = int(sx * scale), int(sy * scale), int(sw * scale)
    headline = short_headline(row)
    eyebrow = (row.get("national_day") or row["series_name"]).upper()
    if len(eyebrow) > 34:
        eyebrow = eyebrow[:34].rstrip() + "…"
    subline = row["weekly_theme"].upper()

    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    mode = (variant + master_id) % 5
    if tone == "sky":
        small_color, sub_color = WHITE, WHITE
    else:
        small_color, sub_color = DEEP, DEEP

    if tone == "card" or mode == 1:
        d.rounded_rectangle((x - 24, y - 24, x + width + 22, y + int(250 * scale)), radius=int(26 * scale), fill=(250, 253, 255, 238))
        small_color = sub_color = DEEP
    elif mode == 3:
        panel_x0 = max(0, x - 30)
        d.polygon([(panel_x0, 0), (x + width + 35, 0), (x + width - 10, im.size[1]), (max(0, x - 75), im.size[1])], fill=(0, 48, 120, 220))
        small_color = sub_color = WHITE
    elif mode == 4:
        d.rounded_rectangle((x - 18, y - 16, x + width + 18, y + int(210 * scale)), radius=int(22 * scale), fill=(0, 39, 102, 145))
        small_color = sub_color = WHITE

    d.text((x, y), eyebrow, font=mfont(max(16, int(23 * scale)), "ExtraBold"), fill=small_color)
    pill_y = y + int(38 * scale)
    max_h = int(118 * scale)
    main_font, lines = fit_bebas(d, headline, width - int(38 * scale), max_h, start=int(78 * scale), minimum=int(38 * scale))
    line_text = "\n".join(lines)
    bbox = d.multiline_textbbox((0, 0), line_text, font=main_font, spacing=-5)
    text_h = bbox[3] - bbox[1]
    pill_h = max(int(82 * scale), text_h + int(18 * scale))
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x + 5, pill_y + 8, x + width + 5, pill_y + pill_h + 8), radius=int(18 * scale), fill=(0, 25, 80, 95))
    shadow = shadow.filter(ImageFilter.GaussianBlur(max(4, int(8 * scale))))
    ov = Image.alpha_composite(ov, shadow)
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle((x, pill_y, x + width, pill_y + pill_h), radius=int(18 * scale), fill=BLUE)
    tx = x + int(20 * scale)
    ty = pill_y + int(1 * scale)
    d.multiline_text((tx, ty), line_text, font=main_font, fill=WHITE, spacing=-5)
    d.text((x + int(5 * scale), pill_y + pill_h + int(13 * scale)), subline[:44], font=mfont(max(13, int(17 * scale)), "SemiBold"), fill=sub_color)

    date_text = row["date"].replace("-", "·")
    d.rounded_rectangle((int(38 * scale), im.size[1] - int(58 * scale), int(225 * scale), im.size[1] - int(24 * scale)), radius=int(17 * scale), fill=(255, 255, 255, 225))
    d.text((int(58 * scale), im.size[1] - int(52 * scale)), date_text, font=mfont(max(11, int(13 * scale)), "ExtraBold"), fill=DEEP)
    if row["format"] == "carousel":
        d.rounded_rectangle((im.size[0] - int(145 * scale), im.size[1] - int(58 * scale), im.size[0] - int(30 * scale), im.size[1] - int(24 * scale)), radius=int(17 * scale), fill=(255, 255, 255, 225))
        d.text((im.size[0] - int(124 * scale), im.size[1] - int(52 * scale)), "GESER  →", font=mfont(max(11, int(13 * scale)), "ExtraBold"), fill=DEEP)
    bx = im.size[0] - int(190 * scale)
    by = int(42 * scale) if not reel else int(120 * scale)
    brand(d, bx, by, "white" if tone == "sky" or mode in (3, 4) else "blue")
    return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"), master_id, mode


def carousel_slide(row, point, slide_no, layout):
    base, master_id, _ = compose_cover(row)
    title, body = point
    if layout == 0:
        im = ImageEnhance.Brightness(base).enhance(.76)
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        for yy in range(620, 1350):
            alpha = int(35 + (yy - 620) / 730 * 195)
            d.rectangle((0, yy, 1080, yy + 1), fill=(0, 42, 108, alpha))
        d.rounded_rectangle((58, 660, 230, 704), radius=22, fill=(255, 255, 255, 235))
        d.text((82, 669), f"LANGKAH {slide_no - 1}", font=mfont(16, "ExtraBold"), fill=DEEP)
        d.text((58, 735), title, font=bfont(78), fill=WHITE)
        yy = 840
        for line in wrapped(d, body, mfont(26, "SemiBold"), 900):
            d.text((62, yy), line, font=mfont(26, "SemiBold"), fill=WHITE)
            yy += 40
        brand(d, 855, 54, "white")
        d.rounded_rectangle((910, 1270, 1035, 1310), radius=20, fill=(255, 255, 255, 230))
        d.text((934, 1278), f"{slide_no}/4 →", font=mfont(14, "ExtraBold"), fill=DEEP)
        return Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    if layout == 1:
        panel_left = row["id"] % 2 == 0
        photo = cover_crop(base, (650, 1350), x_bias=.35 if panel_left else -.35)
        im = Image.new("RGB", (1080, 1350), DEEP)
        if panel_left:
            im.paste(photo, (430, 0)); px, tx = 0, 55
            seam = [(390, 0), (455, 0), (430, 1350), (365, 1350)]
        else:
            im.paste(photo, (0, 0)); px, tx = 650, 700
            seam = [(625, 0), (690, 0), (715, 1350), (650, 1350)]
        d = ImageDraw.Draw(im)
        d.polygon(seam, fill=CYAN)
        d.rounded_rectangle((tx, 90, tx + 175, 132), radius=21, fill=WHITE)
        d.text((tx + 23, 97), f"LANGKAH {slide_no - 1}", font=mfont(16, "ExtraBold"), fill=DEEP)
        title_font, title_lines = fit_bebas(d, title, 320, 260, start=78, minimum=44)
        d.multiline_text((tx, 190), "\n".join(title_lines), font=title_font, fill=WHITE, spacing=-5)
        yy = 425
        for line in wrapped(d, body, mfont(24, "SemiBold"), 300):
            d.text((tx, yy), line, font=mfont(24, "SemiBold"), fill=(226, 244, 255))
            yy += 38
        brand(d, tx, 1155, "white")
        d.rounded_rectangle((tx + 230, 1260, tx + 350, 1300), radius=20, fill=WHITE)
        d.text((tx + 252, 1268), f"{slide_no}/4", font=mfont(14, "ExtraBold"), fill=DEEP)
        return im

    bg = ImageEnhance.Brightness(base).enhance(.56).filter(ImageFilter.GaussianBlur(2))
    ov = Image.new("RGBA", bg.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle((86, 238, 994, 1100), radius=38, fill=(250, 253, 255, 244))
    d.text((140, 330), title, font=bfont(82), fill=DEEP)
    yy = 500
    for line in wrapped(d, body, mfont(27, "SemiBold"), 760):
        d.text((145, yy), line, font=mfont(27, "SemiBold"), fill=INK)
        yy += 43
    cta = row.get("national_day_cta") or row["cta"]
    cta_short = " ".join(cta.replace(".", "").split()[:7]).upper()
    d.rounded_rectangle((145, 750, 780, 846), radius=48, fill=BLUE)
    cta_font, cta_lines = fit_bebas(d, cta_short, 570, 62, start=38, minimum=25)
    d.multiline_text((185, 770), "\n".join(cta_lines[:1]), font=cta_font, fill=WHITE)
    d.text((145, 960), "ARGA TIRTA • WATER SYSTEM", font=mfont(18, "ExtraBold"), fill=DEEP)
    d.rounded_rectangle((850, 1015, 950, 1055), radius=20, fill=BLUE)
    d.text((874, 1023), f"{slide_no}/4", font=mfont(14, "ExtraBold"), fill=WHITE)
    return Image.alpha_composite(bg.convert("RGBA"), ov).convert("RGB")


def caption_for(row):
    hook = row.get("national_day_hook") or row["hook"]
    cta = row.get("national_day_cta") or row["cta"]
    if row.get("national_day"):
        body = f"Pada {row['national_day']}, keluarga Arga Tirta mengingat kembali pentingnya kebiasaan baik, kerja yang rapi, dan manfaat yang terus diteruskan."
    elif "Bu Yati" in row["featured_cast"]:
        body = f"Bu Yati melihat {row['weekly_theme'].lower()} dari sisi yang paling terasa setiap hari: stok, waktu kerja, kenyamanan pelanggan, dan keputusan yang praktis."
    elif "Pak Udin" in row["featured_cast"]:
        body = f"Pak Udin boleh terlihat santai, tetapi urusan {row['weekly_theme'].lower()} tetap dimulai dari melihat gejala, mencatat perubahan, lalu bekerja sesuai urutan."
    else:
        body = f"Pak Tirto percaya {row['weekly_theme'].lower()} perlu dibangun dari kondisi nyata, alur yang jelas, dan sistem yang mudah diperiksa kembali."
    return f"{hook}\n\n{body}\n\n{cta}\n\n#ArgaTirta #DepotAirMinum #IsiUlang #WaterSystem #UsahaAirMinum"


def render_reel(poster, output):
    cmd = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-loop", "1", "-i", str(poster),
        "-vf", "scale=1134:2016,crop=1080:1920:x='27+12*sin(t*0.9)':y='42+14*(t/6)',fade=t=in:st=0:d=0.2,fade=t=out:st=5.35:d=0.55,format=yuv420p",
        "-t", "6", "-r", "24", "-c:v", "h264_videotoolbox", "-b:v", "1800k", "-maxrate", "2200k", "-bufsize", "4000k", "-movflags", "+faststart", "-an", str(output),
    ]
    subprocess.run(cmd, check=True)


def week1_asset(row, day_dir):
    day = row["id"]
    if day in (1, 3, 6):
        for slide in range(1, 5):
            src = WEEK1 / "carousels" / f"day-{day:02d}-slide-{slide:02d}-final-v2.jpg"
            shutil.copy2(src, day_dir / f"slide-{slide:02d}.jpg")
        return True
    if day in (2, 4):
        shutil.copy2(WEEK1 / "final" / f"day-{day:02d}-cover-final-v2.jpg", day_dir / "post.jpg")
        return True
    if day in (5, 7):
        shutil.copy2(WEEK1 / "final" / f"day-{day:02d}-reel-cover-9x16-final-v2.jpg", day_dir / "poster.jpg")
        return True
    return False


def main():
    rows = json.loads(CALENDAR.read_text(encoding="utf-8"))
    assert len(rows) == 184
    formats = Counter(r["format"] for r in rows)
    assert formats == {"carousel": 79, "single": 53, "reel": 52}, formats
    if PUBLIC_ROOT.exists():
        shutil.rmtree(PUBLIC_ROOT)
    PUBLIC_ROOT.mkdir(parents=True)

    plan = []
    source_hashes = {}
    render_manifest = []
    for index, row in enumerate(rows, start=1):
        day_dir = PUBLIC_ROOT / f"day-{index:03d}"
        day_dir.mkdir()
        used_week1 = week1_asset(row, day_dir)
        if not used_week1:
            if row["format"] == "carousel":
                cover, master_id, layout = compose_cover(row)
                cover.save(day_dir / "slide-01.jpg", quality=90, subsampling=0, optimize=True)
                pts = POINTS[row["pillar"]]
                carousel_slide(row, pts[0], 2, 0).save(day_dir / "slide-02.jpg", quality=89, subsampling=0, optimize=True)
                carousel_slide(row, pts[1], 3, 1).save(day_dir / "slide-03.jpg", quality=89, subsampling=0, optimize=True)
                carousel_slide(row, pts[2], 4, 2).save(day_dir / "slide-04.jpg", quality=89, subsampling=0, optimize=True)
            elif row["format"] == "single":
                cover, master_id, layout = compose_cover(row)
                cover.save(day_dir / "post.jpg", quality=90, subsampling=0, optimize=True)
            else:
                cover, master_id, layout = compose_cover(row, size=(1080, 1920), reel=True)
                cover.save(day_dir / "poster.jpg", quality=90, subsampling=0, optimize=True)
        else:
            master_id, layout = choose_master(row), "week1-approved"

        if row["format"] == "carousel":
            assets = [f"posts/arga-tirta-6m-v2/day-{index:03d}/slide-{n:02d}.jpg" for n in range(1, 5)]
            reel_asset = None
        elif row["format"] == "single":
            assets = [f"posts/arga-tirta-6m-v2/day-{index:03d}/post.jpg"]
            reel_asset = None
        else:
            assets = [f"posts/arga-tirta-6m-v2/day-{index:03d}/poster.jpg"]
            reel_asset = f"posts/arga-tirta-6m-v2/day-{index:03d}/reel.mp4"
            render_reel(ROOT / "public" / assets[0], ROOT / "public" / reel_asset)

        item = {
            "id": 1000 + index,
            "campaign_day": index,
            "date": row["date"],
            "time_wib": row["time_wib"],
            "title": row.get("national_day_hook") or row["hook"],
            "content_theme": row["pillar"],
            "weekly_theme": row["weekly_theme"],
            "post_type": row["format"],
            "slide_count": len(assets),
            "asset": assets[0],
            "assets": assets,
            "slides": [{"index": n + 1, "asset": asset} for n, asset in enumerate(assets)],
            "reel_asset": reel_asset,
            "final_caption": caption_for(row),
            "status": "queued_auto",
            "approval_required": True,
            "approval_status": "approved",
            "approved_from_user_instruction": "2026-08-24",
            "visual_revision": "digital-imaging-cast-shadow-v2",
            "asset_version": VERSION,
            "visual_system": "arga-tirta-family-business-digital-imaging-v2",
            "featured_cast": row["featured_cast"],
            "supporting_cast": row["supporting_cast"],
            "camera_shot": row["camera_shot"],
            "camera_lens": row["camera_lens"],
            "camera_angle": row["camera_angle"],
            "national_day": row.get("national_day", ""),
            "ai_generated": True,
            "master_source": f"campaign-v2/masters/day-{master_id:02d}-digital-imaging-v2.png",
            "layout_variant": layout,
        }
        if row["format"] == "reel":
            key = AUDIO_KEYS[(index - 1) % len(AUDIO_KEYS)]
            item["audio"] = {
                "selection": "trending_western",
                "western_audio_key": key,
                "western_candidates": [k for k in AUDIO_KEYS if k != key],
                "graph_api_attachment": True,
                "audio_volume": 100,
                "video_volume": 0,
            }
        plan.append(item)
        render_manifest.append({"campaign_day": index, "date": row["date"], "format": row["format"], "assets": assets, "reel_asset": reel_asset, "master": master_id, "layout": layout})

    (ROOT / "content-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "public/content-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (CAMPAIGN / "render-manifest.json").write_text(json.dumps(render_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    asset_files = sorted(p for p in PUBLIC_ROOT.rglob("*") if p.is_file())
    for p in asset_files:
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if digest in source_hashes:
            raise RuntimeError(f"Exact duplicate: {p} and {source_hashes[digest]}")
        source_hashes[digest] = str(p)
    report = {
        "campaign": "arga-tirta-6m-v2",
        "period": [rows[0]["date"], rows[-1]["date"]],
        "posts": len(plan),
        "formats": dict(sorted(formats.items())),
        "asset_files": len(asset_files),
        "unique_asset_hashes": len(source_hashes),
        "approval": "approved",
        "status": "queued_auto",
        "visual_revision": "digital-imaging-cast-shadow-v2",
    }
    (CAMPAIGN / "reports/generation-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
