#!/usr/bin/env python3
"""Download chapter images from Wikimedia Commons (gently), then build sprite sheets.
Usage: fetch_images.py 1 2 3 ...   (chapter numbers)
- type map/doc  -> img/<key>.jpg at width<=1000 (kept as separate file)
- others        -> packed into sp/chNN.jpg (480px column), im['sp']=[y,w,h]
"""
import json, os, subprocess, sys, time, io
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, 'tools', 'raw'); os.makedirs(RAW, exist_ok=True)
os.makedirs(os.path.join(ROOT, 'img'), exist_ok=True); os.makedirs(os.path.join(ROOT, 'sp'), exist_ok=True)
UA = 'OnnuriWorldHistory/1.0 (personal study app; cyc04392@gmail.com)'
SLEEP = 3

def fetch(commons, width, out):
    import hashlib, urllib.parse
    name = commons[5:].replace(' ', '_')
    h = hashlib.md5(name.encode('utf-8')).hexdigest()
    enc = urllib.parse.quote(name)
    ext = name.rsplit('.', 1)[-1].lower()
    thumb = f'https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[:2]}/{enc}/{width}px-{enc}' + ('.png' if ext in ('svg','tif','tiff','pdf') else '')
    orig = f'https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{enc}'
    redirect = f'https://commons.wikimedia.org/wiki/Special:Redirect/file/{enc}?width={width}'
    for url in (thumb, orig, redirect):
        for attempt in range(6):
            r = subprocess.run(['curl', '-sS', '-L', '-m', '60', '-A', UA, '-o', out, '-w', '%{http_code}', url], capture_output=True, text=True)
            code = r.stdout.strip()
            print(f'  {name[:36]} {url.split("/")[2][:6]} -> {code}', flush=True)
            if code == '200' and os.path.exists(out) and os.path.getsize(out) > 500:
                try:
                    Image.open(out).verify(); time.sleep(0.6); return True
                except Exception: pass
            if code in ('404', '400'): break
            time.sleep(25 if code == '429' else 4)
    return False

def process(no):
    p = os.path.join(ROOT, 'data', f'ch{no:02d}.json')
    d = json.load(open(p, encoding='utf-8'))
    col = 480; items = []; missing = []; failed = []
    for key, im in d['images'].items():
        wide = im['type'] in ('map', 'doc')
        raw = os.path.join(RAW, key + '.bin')
        if not os.path.exists(raw):
            ok = fetch(im['commons'], 960 if wide else 500, raw); time.sleep(SLEEP)
            if not ok:
                missing.append(key);
                if os.path.exists(raw): os.remove(raw)
                continue
        try:
            img = Image.open(raw); img = ImageOps.exif_transpose(img)
            if img.mode in ('RGBA', 'LA', 'P'):
                bg = Image.new('RGB', img.size, (255, 255, 255)); bg.paste(img.convert('RGBA'), mask=img.convert('RGBA').split()[-1]); img = bg
            else: img = img.convert('RGB')
        except Exception as e:
            missing.append(key); continue
        if wide:
            if img.width > 1000: img = img.resize((1000, round(img.height * 1000 / img.width)), Image.LANCZOS)
            img.save(os.path.join(ROOT, 'img', key + '.jpg'), 'JPEG', quality=82, optimize=True)
            im.pop('sp', None)
        else:
            img = img.resize((col, max(1, round(img.height * col / img.width))), Image.LANCZOS)
            if img.height > 700: img = img.crop((0, 0, col, 700))
            items.append((key, img))
    if items:
        H = sum(i.height for _, i in items) + 2 * (len(items) - 1)
        sheet = Image.new('RGB', (col, H), (255, 255, 255)); y = 0
        for key, img in items:
            sheet.paste(img, (0, y)); d['images'][key]['sp'] = [y, col, img.height]; y += img.height + 2
        sheet.save(os.path.join(ROOT, 'sp', f'ch{no:02d}.jpg'), 'JPEG', quality=80, optimize=True)
    for k in failed:
        im = d['images'][k]; im.pop('sp', None); im['file'] = k + '.jpg'
    for k in missing:
        print(f'ch{no:02d}: 이미지 없음 → 제거: {k} ({d["images"][k]["commons"]})')
        del d['images'][k]
        for q in d['q']: q['img'] = [x for x in q.get('img', []) if x != k]
        for g in d['g'].values(): g['img'] = [x for x in g.get('img', []) if x != k]
        for e in d['exam']: e['img'] = [x for x in e.get('img', []) if x != k]
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    print(f'ch{no:02d}: sprite {len(items)} · wide {len(d["images"]) - len(items)} · missing {len(missing)}', flush=True)

for a in sys.argv[1:]: process(int(a))
print('DONE')
