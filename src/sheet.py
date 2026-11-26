"""Builds contact-sheet frames: one per shot, with the time it appears in the film.
Writes assets/<project>/cs/NN.jpg and src/sheets.json."""
import subprocess, re, json, os
from PIL import Image, ImageChops, ImageStat
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, 'assets')

def scenes(src, lo, hi):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-ss', str(lo), '-to', str(hi), '-i', src, '-vf',
                        "select='gt(scene,0.3)',showinfo", '-an', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return [lo + float(x) for x in re.findall(r'pts_time:([\d.]+)', r)]

def pick(src, lo, hi, n):
    ts = [lo + 0.4] + [t + 0.4 for t in scenes(src, lo, hi) if lo + 0.3 < t < hi - 0.6]
    out = []
    for t in sorted(ts):
        if not out or t - out[-1] > 0.8:
            out.append(t)
    while len(out) < n:
        g, i = max([(out[k + 1] - out[k], k) for k in range(len(out) - 1)] + [(hi - out[-1], len(out) - 1)])
        out.insert(i + 1, out[i] + g / 2)
    if len(out) > n:
        step = len(out) / n
        out = [out[int(k * step)] for k in range(n)]
    return out

# project: list of (film file, film index on the page, start, end, frame count, crop)
PLAN = {
    'nongfu': [('film.mp4', 0, 0.2, 25.6, 16, '')],
    'shell': [('film1.mp4', 0, 0.5, 27.5, 6, ''), ('film2.mp4', 1, 0.5, 42.5, 6, '')],
    'pub': [('frogprince.mp4', 'frog', 25, 585, 16, 'crop=1280:532:0:94'), ('tuas.mp4', 'tuas', 3, 232, 12, ''),
            ('flashmob.mp4', 'flash', 2.0, 48.0, 16, 'crop=1600:670:0:115')],
    'nlb': [('film.mp4', 0, 3.0, 36.0, 16, '')],
    'canon': [('film.mp4', 0, 1.0, 24.0, 16, '')],
}
out = {}
for pid, srcs in PLAN.items():
    d = os.path.join(A, pid, 'cs'); os.makedirs(d, exist_ok=True)
    for f in os.listdir(d): os.remove(os.path.join(d, f))
    frames, k, prev = [], 0, None
    for film, idx, lo, hi, n, crop in srcs:
        src = os.path.join(A, pid, film)
        for t in pick(src, lo, hi, n + 3):
            name = f'{k:02d}'
            fp = os.path.join(d, name + '.jpg')
            vf = (crop + ',' if crop else '') + 'scale=480:-2'
            subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-ss', f'{t:.2f}', '-i', src, '-frames:v', '1', '-vf', vf, '-q:v', '4', fp], check=True)
            small = Image.open(fp).convert('L').resize((32, 18))
            if prev is not None and ImageStat.Stat(ImageChops.difference(small, prev)).mean[0] < (1.2 if pid == 'nlb' else 14):
                os.remove(fp); continue  # too close to the frame before it
            prev = small
            frames.append({'img': f'cs/{name}', 'film': idx, 't': round(t, 2)})
            k += 1
            if sum(1 for f in frames if f['film'] == idx) >= n: break
    out[pid] = frames
    print(pid, len(frames))
json.dump(out, open(os.path.join(ROOT, 'src', 'sheets.json'), 'w'), indent=1)
