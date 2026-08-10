#!/usr/bin/env python3
"""Turn queued carousel artwork into compact 9:16 Instagram Reels."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "content-plan.json"
CATALOG_PATH = ROOT / "trending-western-audio.json"
FPS = 30
SLIDE_SECONDS = 1.65


def source_file(relative: str) -> Path:
    direct = ROOT / relative
    return direct if direct.exists() else ROOT / "public" / relative


def output_file(relative: str) -> Path:
    direct_parent = ROOT / Path(relative).parent
    return direct_parent / "reel.mp4" if direct_parent.exists() else ROOT / "public" / Path(relative).parent / "reel.mp4"


def compose_vertical(source: Path, target: Path) -> None:
    with Image.open(source) as opened:
        image = opened.convert("RGB")
    background = Image.new("RGB", (1080, 1920), (3, 8, 12))

    max_w, max_h = 1000, 1420
    scale = min(max_w / image.width, max_h / image.height)
    foreground = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    shadow = Image.new("RGBA", (foreground.width + 38, foreground.height + 38), (0, 0, 0, 0))
    shadow_layer = Image.new("RGBA", foreground.size, (0, 0, 0, 155))
    shadow.alpha_composite(shadow_layer, (19, 22))
    x = (1080 - foreground.width) // 2
    y = (1920 - foreground.height) // 2
    composed = background.convert("RGBA")
    composed.alpha_composite(shadow, (x - 19, y - 19))
    composed.alpha_composite(foreground.convert("RGBA"), (x, y))
    composed.convert("RGB").save(target, quality=90, subsampling=0)


def render_reel(item: dict, force: bool = False) -> tuple[int, str, int]:
    sources = item.get("source_assets") or item.get("assets") or [item["asset"]]
    output = output_file(sources[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    newest_source = max(source_file(relative).stat().st_mtime for relative in sources)
    if (
        output.exists()
        and output.stat().st_size > 100_000
        and output.stat().st_mtime >= newest_source
        and not force
    ):
        return item["id"], str(output.relative_to(ROOT / "public") if "public" in output.parts else output.relative_to(ROOT)), output.stat().st_size

    with tempfile.TemporaryDirectory(prefix=f"reel-{item['id']:03d}-") as temp_dir:
        temp = Path(temp_dir)
        frames = []
        for index, relative in enumerate(sources):
            frame = temp / f"frame-{index:02d}.jpg"
            compose_vertical(source_file(relative), frame)
            frames.append(frame)

        concat_file = temp / "frames.txt"
        concat_lines = []
        for frame in frames:
            concat_lines += [f"file '{frame}'", f"duration {SLIDE_SECONDS}"]
        concat_lines.append(f"file '{frames[-1]}'")
        concat_file.write_text("\n".join(concat_lines) + "\n")
        total = len(frames) * SLIDE_SECONDS
        temp_output = temp / "reel.mp4"
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-vf", f"fps={FPS},format=yuv420p",
            "-map", "0:v", "-map", "1:a",
            "-c:v", "h264_videotoolbox", "-profile:v", "high", "-b:v", "1000k",
            "-maxrate", "1800k", "-bufsize", "3600k", "-realtime", "true", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "64k", "-shortest", "-movflags", "+faststart",
            str(temp_output),
        ]
        subprocess.run(command, check=True)
        shutil.move(temp_output, output)

    relative_output = str(output.relative_to(ROOT / "public") if "public" in output.parts else output.relative_to(ROOT))
    return item["id"], relative_output, output.stat().st_size


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--only", type=int, help="Render one queue ID")
    parser.add_argument("--workers", type=int, default=max(1, min(3, (os.cpu_count() or 4) // 2)))
    args = parser.parse_args()

    plan = json.loads(PLAN_PATH.read_text())
    catalog = json.loads(CATALOG_PATH.read_text())
    tracks = catalog["tracks"]
    candidates = [track["key"] for track in tracks]
    targets = []
    for item in plan:
        is_source_carousel = item.get("post_type") == "carousel" or item.get("source_post_type") == "carousel"
        if not is_source_carousel or item.get("status") == "published":
            continue
        if args.only and item["id"] != args.only:
            continue
        if item.get("post_type") == "carousel":
            item["source_post_type"] = "carousel"
            item["source_assets"] = list(item.get("assets") or [item["asset"]])
        item["post_type"] = "reel"
        item["reel_asset"] = str(Path(item["source_assets"][0]).parent / "reel.mp4")
        item["reel_spec"] = {
            "width": 1080,
            "height": 1920,
            "fps": FPS,
            "source": "existing carousel artwork",
            "slides": len(item["source_assets"]),
            "transition": "beat-paced hard cuts",
        }
        preferred = candidates[(int(item["id"]) - 1) % len(candidates)]
        item["audio"] = {
            "requested": True,
            "selection": "trending_western",
            "graph_api_attachment": True,
            "audio_type": "music",
            "catalog_verified_at": catalog["verified_at"],
            "western_audio_key": preferred,
            "western_candidates": candidates,
            "language_exclusions": ["Indonesian"],
            "audio_volume": 100,
            "video_volume": 0,
            "selection_timing": "publish_time",
        }
        targets.append(item)

    if not targets:
        print("No queued carousel Reels need rendering.")
        return

    results = {}
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(render_reel, item, args.force): item for item in targets}
        for future in as_completed(futures):
            item_id, relative, size = future.result()
            results[item_id] = (relative, size)
            print(f"Rendered reel {item_id:03d}: {relative} ({size / 1024:.0f} KiB)")

    for item in targets:
        relative, _ = results[item["id"]]
        item["reel_asset"] = relative
    PLAN_PATH.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    print(f"Converted {len(targets)} queued carousels to Reels.")


if __name__ == "__main__":
    main()
