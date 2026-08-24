#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess
from collections import Counter
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parent.parent
plan=json.loads((ROOT/'content-plan.json').read_text())
errors=[]; image_dims=Counter(); video_specs=Counter(); bytes_total=0
for item in plan:
    for rel in item['assets']:
        p=ROOT/'public'/rel
        if not p.exists(): errors.append(f'missing {rel}'); continue
        bytes_total += p.stat().st_size
        try:
            with Image.open(p) as im:
                im.verify(); dims=im.size
            expected=(1080,1920) if item['post_type']=='reel' else (1080,1350)
            if dims != expected: errors.append(f'bad dimensions {rel}: {dims} != {expected}')
            image_dims[str(dims)] += 1
        except Exception as e: errors.append(f'image decode {rel}: {e}')
    if item['post_type']=='reel':
        rel=item['reel_asset']; p=ROOT/'public'/rel
        if not p.exists(): errors.append(f'missing {rel}'); continue
        bytes_total += p.stat().st_size
        try:
            out=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height,r_frame_rate,duration','-show_entries','format=duration,size','-of','json',str(p)],text=True)
            data=json.loads(out); s=data['streams'][0]; spec=(s['codec_name'],s['width'],s['height'],s['r_frame_rate'],round(float(data['format']['duration']),2))
            video_specs[str(spec)] += 1
            if s['codec_name']!='h264' or (s['width'],s['height'])!=(1080,1920) or float(data['format']['duration']) < 5.8:
                errors.append(f'bad reel spec {rel}: {spec}')
        except Exception as e: errors.append(f'video decode {rel}: {e}')
formats=Counter(x['post_type'] for x in plan)
report={
    'status':'pass' if not errors else 'fail',
    'posts':len(plan),
    'date_start':plan[0]['date'] if plan else None,
    'date_end':plan[-1]['date'] if plan else None,
    'formats':dict(formats),
    'image_dimensions':dict(image_dims),
    'video_specs':dict(video_specs),
    'unique_titles':len({x['title'].casefold() for x in plan}),
    'unique_captions':len({x['final_caption'].casefold() for x in plan}),
    'all_approved':all(x['approval_status']=='approved' for x in plan),
    'all_queued_or_published':all(x['status'] in {'queued_auto','published'} for x in plan),
    'old_asset_paths_remaining':sum(any('arga-tirta-100d' in a for a in x['assets']) for x in plan),
    'public_media_bytes':bytes_total,
    'errors':errors,
}
(ROOT/'campaign-v2/reports/qc-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(1 if errors else 0)
