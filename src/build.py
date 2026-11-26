"""Builds the site from content.json, style.css and app.js.

  python3 src/build.py            writes index.html (the real site, for GitHub Pages)
  python3 src/build.py --preview  writes preview.html (films open in a new tab, for the Claude preview link)
"""
import json, sys, os
from html import escape as e
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')
PREVIEW = '--preview' in sys.argv

c = json.load(open(os.path.join(SRC, 'content.json'), encoding='utf-8'))
css = open(os.path.join(SRC, 'style.css'), encoding='utf-8').read()
js = open(os.path.join(SRC, 'app.js'), encoding='utf-8').read()

P = c['projects']
me = c['person']
TITLE = f"{me['name']}, {me['role']}, {me['city']}"


# ---------- assets ----------
def size(path):
    w, h = Image.open(os.path.join(ROOT, path)).size
    return (path, w, h)

def ref(pid, r):
    """A poster or image reference: "03" means assets/<project>/03.jpg, "folder/03" means assets/folder/03.jpg."""
    return size(f"assets/{r}.jpg" if '/' in r else f"assets/{pid}/{r}.jpg")

def numbered(pid):
    d = os.path.join(ROOT, 'assets', pid)
    return [size(f'assets/{pid}/{f}') for f in sorted(os.listdir(d))
            if f.endswith('.jpg') and f[0].isdigit()]

def loops(p):
    out = []
    for n in p.get('loop', []):
        _, w, h = size(f"assets/{p['id']}/{n}.jpg")
        out.append((f"assets/{p['id']}/{n}.mp4", f"assets/{p['id']}/{n}.jpg", w, h))
    return out

def video(mp4, jpg, w, h, eager=False, cls=''):
    c_ = f' class="{cls}"' if cls else ''
    src = f'src="{mp4}" autoplay preload="auto"' if eager else f'data-src="{mp4}" preload="none"'
    return f'<video{c_} {src} poster="{jpg}" width="{w}" height="{h}" muted loop playsinline aria-hidden="true"></video>'

def img(s, w, h, alt='', lazy=True):
    return f'<img src="{s}" alt="{e(alt)}"{" loading=" + chr(34) + "lazy" + chr(34) if lazy else ""} width="{w}" height="{h}">'


# ---------- building blocks ----------
def film_urls(f):
    if f['type'] == 'yt':
        return (f"https://www.youtube.com/watch?v={f['id']}",
                f"https://www.youtube-nocookie.com/embed/{f['id']}?autoplay=1&rel=0")
    u = f"https://www-ccv.adobe.io/v1/player/ccv/{f['id']}/embed?bgcolor=%23191919&lazyLoading=true&api_key=BehancePro2View"
    return (u, u)

PLAY = '<span class="play" aria-hidden="true"><svg width="15" height="17" viewBox="0 0 14 16"><path d="M0 0l14 8-14 8z" fill="currentColor"/></svg></span>'

def film(pid, f, name, key):
    s, w, h = ref(pid, f['poster'])
    label = f.get('label', '')
    cap = f'<figcaption>{e(label)}</figcaption>' if label else ''
    if f['type'] == 'post':
        # a short silent loop shown as a post, like a GIF
        src = f"assets/{pid}/{f['src']}.mp4"
        return (f'<figure class="film-wrap"><div class="film post"><video src="{src}" poster="{s}" muted loop playsinline autoplay '
                f'preload="metadata" aria-hidden="true"></video></div>{cap}</figure>')
    if f['type'] == 'file':
        # our own file: plays in place, and the contact sheet can start it at any moment
        src = f"assets/{pid}/{f['src']}.mp4"
        return (f'<figure class="film-wrap"><div class="film" role="button" tabindex="0" data-video="{src}" data-key="{e(key)}" '
                f'aria-label="Play {e(label or name)}">{img(s, w, h)}{PLAY}</div>{cap}</figure>')
    watch, embed = film_urls(f)
    return (f'<figure class="film-wrap"><a class="film" href="{e(watch)}" target="_blank" rel="noopener" '
            f'data-embed="{e(embed)}" aria-label="Play {e(label or name)}">{img(s, w, h)}{PLAY}</a>{cap}</figure>')

def films_block(pid, films, name, shape=''):
    if not films:
        return ''
    cls = 'films' + (' tall' if shape == 'tall' else '') + (' many' if len(films) > 1 and shape != 'tall' else '')
    return f'<div class="{cls}">' + ''.join(film(pid, f, name, f.get('key', f'{pid}:{k}')) for k, f in enumerate(films)) + '</div>'

SHEETS = json.load(open(os.path.join(SRC, 'sheets.json'), encoding='utf-8'))

def sheet(pid, which):
    """Contact sheet: one frame per shot. Each frame starts its film at that moment."""
    fr = [x for x in SHEETS.get(pid, []) if (isinstance(x['film'], int) if which == 'main' else x['film'] == which)]
    if not fr:
        return ''
    cells = ''
    for x in fr:
        s, w, h = size(f"assets/{pid}/{x['img']}.jpg")
        key = x['film'] if isinstance(x['film'], str) else f"{pid}:{x['film']}"
        m, sec = divmod(int(x['t']), 60)
        cells += (f'<button class="cs-f" data-key="{key}" data-t="{x["t"]}" aria-label="Play from {m}:{sec:02d}" '
                  f'style="aspect-ratio:{w}/{h}"><img src="{s}" alt="" loading="lazy" width="{w}" height="{h}"></button>')
    _, w0, h0 = size(f"assets/{pid}/{fr[0]['img']}.jpg")
    tall = h0 > w0
    return f'<div class="sheet{" tall" if tall else ""}">{cells}</div>'

def reel(imgs):
    """Images at their own shape. Wide ones get a row each; runs of upright ones share a row."""
    rows, buf = [], []
    def flush():
        if not buf:
            return
        n = len(buf)
        cls = {1: 'row lone', 2: 'row n2', 3: 'row n3', 4: 'row n4'}[n]
        rows.append(f'<div class="{cls}">' + ''.join(f'<figure>{img(s, w, h)}</figure>' for s, w, h in buf) + '</div>')
        buf.clear()
    for s, w, h in imgs:
        if w / h >= 1.25:
            flush()
            rows.append(f'<div class="row"><figure>{img(s, w, h)}</figure></div>')
        else:
            buf.append((s, w, h))
            if len(buf) == 4:
                flush()
    flush()
    return f'<div class="reel">{"".join(rows)}</div>' if rows else ''

def credits_block(p):
    cr = p.get('credits') or []
    if not cr:
        return ''
    rows = ''.join(f'<dt>{e(r)}</dt><dd>{e(n)}</dd>' for r, n in cr)
    return f'<dl class="credits">{rows}</dl>'

def words(t):
    return ' '.join(f'<span class="w"><span>{e(x)}</span></span>' for x in t.split())


# ---------- index ----------
stage, items = [], []
for i, p in enumerate(P):
    lp = loops(p)
    tri = p.get('heroLayout') == 'tri'
    cls = ' '.join(x for x in ['on' if i == 0 else '', 'tri' if tri else ''] if x)
    media = ''.join(video(m, j, w, h, eager=(i == 0 and k == 0)) for k, (m, j, w, h) in enumerate(lp[:3] if tri else lp[:1]))
    if not media:
        s, w, h = numbered(p['id'])[0]
        media = f'<img src="{s}" alt="" width="{w}" height="{h}">'
    stage.append(f'<figure{" class=" + chr(34) + cls + chr(34) if cls else ""}>{media}</figure>')
    light = ' data-light' if p.get('theme') == 'light' else ''
    cls_li = '' if p.get('featured') else ' class="other"'
    items.append(f'<li{light}{cls_li}><a href="#{p["id"]}">{e(p["client"])}</a></li>')

index = f'''
<div class="stage" aria-hidden="true">{''.join(stage)}</div>
<main class="view index" id="v-work" data-title="{e(TITLE)}" style="--n:{len(P)}">
  <h1 class="intro">{e(me['intro'])}</h1>
  <nav aria-label="Selected work"><ol class="list">{''.join(items)}</ol></nav>
</main>'''


# ---------- projects ----------
projects = []
for i, p in enumerate(P):
    pid = p['id']
    lp = loops(p)
    tri = p.get('heroLayout') == 'tri'
    hero = ''.join(video(m, j, w, h, cls='on' if k == 0 else '') for k, (m, j, w, h) in enumerate(lp))
    if not hero:
        s, w, h = numbered(pid)[0]
        hero = f'<img class="on" src="{s}" alt="" width="{w}" height="{h}">'

    used = {ref(pid, f['poster'])[0] for f in p['films']}
    rest = [x for x in numbered(pid) if x[0] not in used]
    if not lp:
        rest = rest[1:]

    parts = ''
    for part in p.get('parts', []):
        pimgs = [ref(pid, r) for r in part.get('images', [])]
        awards = ''
        if part.get('awards'):
            awards = '<ul class="awards">' + ''.join(f'<li>{e(a)}</li>' for a in part['awards']) + '</ul>'
        parts += f'''
    <section class="chapter">
      <header class="ch-head"><h3>{e(part['title'])}</h3><span class="yr">{e(part['year'])}</span></header>
      <p class="ch-text">{e(part['text'])}</p>
      {films_block(pid, part['films'], part['title'])}
      {''.join(sheet(pid, f['key']) for f in part['films'] if f.get('key'))}
      {reel(pimgs)}
      {awards}
    </section>'''

    nxt = P[(i + 1) % len(P)]
    nl = loops(nxt)
    nimg = (nl[0][1], nl[0][2], nl[0][3]) if nl else numbered(nxt['id'])[0]

    projects.append(f'''
<article class="view project{' light' if p.get('theme') == 'light' else ''}" id="v-{pid}" hidden data-title="{e(p['title'] + ', ' + p['client'] + ' | ' + me['name'])}">
  <header class="p-hero">
    <div class="p-frames{' tri' if tri else ''}">{hero}</div>
    <div class="p-title"><div class="inner">
      <h2>{words(p['title'])}</h2>
      <p class="sub">{e(p['sub'])}</p>
    </div></div>
  </header>
  <div class="wrap"><div class="inner">
    <p class="lead">{e(p['line'])}</p>
    {films_block(pid, p['films'], p['title'], p.get('filmShape', ''))}
    {sheet(pid, 'main')}
    {reel(rest)}
    <p class="body">{e(p['body'])}</p>
    {parts}
    {credits_block(p)}
  </div></div>
  <a class="next" href="#{nxt['id']}">
    <img src="{nimg[0]}" alt="" loading="lazy" width="{nimg[1]}" height="{nimg[2]}">
    <span class="next-in"><span class="small">Next</span><strong>{e(nxt['client'])}</strong></span>
  </a>
</article>''')


# ---------- info ----------
jobs = ''.join(f'<li><span class="when">{e(a)}</span><span>{e(b)}</span></li>' for a, b in c['experience'])
about = ''.join(f'<p>{e(x)}</p>' for x in c['about'][1:])
info = f'''
<main class="view info" id="v-info" hidden data-title="Info | {e(me['name'])}">
  <div class="wrap"><div class="inner">
    <p class="lead">{e(c['about'][0])}</p>
    <div class="info-grid">
      <div class="about">{about}<p class="small">{e(c['education'])}</p></div>
      <ul class="jobs">{jobs}</ul>
    </div>
    <section class="contact" id="contact">
      <a class="big" href="mailto:{e(me['email'])}">{e(me['email'])}</a>
      <a class="small link" href="{e(me['linkedin'])}" target="_blank" rel="noopener">LinkedIn</a>
    </section>
  </div></div>
</main>'''

ld = json.dumps({
    "@context": "https://schema.org", "@type": "Person", "name": me['name'], "jobTitle": me['role'],
    "address": {"@type": "PostalAddress", "addressLocality": me['city'], "addressCountry": "SG"},
    "description": me['summary'], "email": me['email'], "sameAs": [me['linkedin']],
    "alumniOf": ["Glasgow School of Art", "Nanyang Polytechnic"],
}, ensure_ascii=False)

header = '''
<header class="top">
  <a class="mark" href="#work">Kuo Jinn</a>
  <nav class="nav" aria-label="Main"><a href="#work">Work</a><a href="#info">Info</a></nav>
</header>'''

fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@300..600&display=swap">')
libs = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>'
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js"></script>'
        '<script src="https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js"></script>')
body = header + index + ''.join(projects) + info + libs + f'<script>{js}</script>'

if PREVIEW:
    out = (f'<title>Kuo Jinn Portfolio</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n<meta name="kj-preview" content="1">\n'
           f'{fonts}\n<style>{css}</style>\n{body}')
    path = os.path.join(ROOT, 'preview.html')
else:
    desc = e(me['summary'])
    out = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(TITLE)}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{e(TITLE)}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="assets/nongfu/h0.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b0b0a">
<link rel="icon" href="data:,">
{fonts}
<style>{css}</style>
<script type="application/ld+json">{ld}</script>
</head>
<body>
{body}
</body>
</html>'''
    path = os.path.join(ROOT, 'index.html')

for bad in ('\u2014',):
    assert bad not in out, 'em dash found in output'
open(path, 'w', encoding='utf-8').write(out)
print('wrote', path, len(out) // 1024, 'KB')
