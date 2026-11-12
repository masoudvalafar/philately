#!/usr/bin/env python3
"""Build the philately site from data/censors.json.

Usage (inside the repo's redesign/ folder):
  python3 build.py
This regenerates the live site at the repository root.
Options: --images DIR (default ../images), --out DIR (default the repository root).
Scans are read as <id>_front.jpg and <id>_back.jpg. With Pillow installed,
web-sized copies and detail crops are written to <out>/img/.
"""
import argparse, html, json, os, re, shutil
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--images", default=os.path.join(HERE, "..", "images"))
ap.add_argument("--out", default=os.path.join(HERE, ".."))
args = ap.parse_args()

OUT = os.path.abspath(args.out)
IMG_SRC = os.path.abspath(args.images)
DATA = json.load(open(os.path.join(HERE, "data", "censors.json"), encoding="utf-8"))

try:
    from PIL import Image
    HAVE_PIL = True
except ImportError:
    HAVE_PIL = False

esc = html.escape
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
START, END = 1909, 1926          # timeline span, in years
EVENTS = [(1911.9, "1911: Majles closed"), (1914.6, "1914: war begins"),
          (1915.6, "1915: Bushire occupied"), (1918.1, "1918: Dunsterforce"),
          (1921.15, "1921: the coup"), (1925.8, "1925: Qajars deposed")]
TOWN_FA = {
    "Tehran": "تهران", "Tabriz": "تبریز", "Qazvin": "قزوین", "Hamadan": "همدان", "Isfahan": "اصفهان", "Bandar Abbas": "بندرعباس",
    "Shiraz": "شیراز", "Bushire": "بوشهر", "Rasht": "رشت", "Senneh": "سنه", "Kermanshah": "کرمانشاه",
    "Meched": "مشهد", "Neishabur": "نیشابور", "Yezd": "یزد", "Qom": "قم", "Sultanabad": "سلطان‌آباد",
    "Kazerun": "کازرون", "Behbahan": "بهبهان", "Ram Hormoz": "رامهرمز", "Zanjan": "زنجان",
    "Mianeh": "میانه", "Barforush": "بارفروش", "Arak": "اراک", "London": "لندن",
}


# ---------------------------------------------------------------- dates
def parse(s):
    if not s:
        return None
    y, m, d = (int(x) for x in s.split("-"))
    return date(y, m, d)


def frac(s):
    d = parse(s)
    return d.year + (d.timetuple().tm_yday - 1) / 365.0


def long_date(s):
    d = parse(s)
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}" if d else ""


def short_date(s):
    d = parse(s)
    return f"{d.day} {MONTHS[d.month - 1][:3]} {d.year}" if d else ""


def pct(y):
    return (y - START) / (END - START) * 100


# ---------------------------------------------------------------- model
covers = DATA["covers"]
marks = DATA["marks"]
strikes = [dict(cp=a, ink=b, cover=c, src=d) for a, b, c, d in DATA["strikes"]]
# A source with no strikes (e.g. "Not yet attributed" once everything is attributed) is not shown.
sources = [s for s in DATA["sources"] if any(x["src"] == s["id"] for x in strikes)]
src_by_id = {s["id"]: s for s in sources}


def ordered_unique(xs):
    out = []
    for x in xs:
        if x not in out:
            out.append(x)
    return out


def cover_key(cid):
    """Sort key and timeline position for an item: (year fraction or None)."""
    c = covers.get(cid, {})
    for k in ("sent", "received"):
        if c.get(k):
            return frac(c[k])
    if c.get("year"):
        return int(c["year"]) + 0.5
    return None


def sort_covers(cids):
    return sorted(cids, key=lambda c: (cover_key(c) is None, cover_key(c) or 0, c))


def cover_when(cid, short=True):
    c = covers.get(cid, {})
    f = short_date if short else long_date
    if c.get("sent"):
        return f(c["sent"])
    if c.get("received"):
        return ("received " if not short else "rec. ") + f(c["received"])
    return c.get("year") or "Undated"


def route(cid):
    c = covers.get(cid, {})
    a, b = c.get("from"), c.get("to")
    if a and b:
        return f"{a} to {b}"
    if a:
        return f"From {a}"
    if b:
        return f"To {b}"
    return c.get("kind", "Item")


def route_fa(cid):
    c = covers.get(cid, {})
    a, b = TOWN_FA.get(c.get("from", "")), TOWN_FA.get(c.get("to", ""))
    if a and b:
        return f"{a} به {b}"
    if a:
        return f"از {a}"
    return ""


FA_RUN = re.compile(r"([\u0600-\u06FF\u200c][\u0600-\u06FF\u200c\s]*[\u0600-\u06FF\u200c]|[\u0600-\u06FF])")


def rich(text):
    """Escape text and isolate Persian runs so they read correctly inside English."""
    return FA_RUN.sub(lambda m: f'<bdi lang="fa" dir="rtl">{m.group(0)}</bdi>', esc(text))


def mark_name(cp):
    return marks.get(cp, {}).get("name", cp)


def mark_slug(cp):
    return cp.lower()


src_covers = {s["id"]: sort_covers(ordered_unique(x["cover"] for x in strikes if x["src"] == s["id"])) for s in sources}
cover_srcs = {}
for x in strikes:
    cover_srcs.setdefault(x["cover"], [])
    if x["src"] not in cover_srcs[x["cover"]]:
        cover_srcs[x["cover"]].append(x["src"])
mark_covers = {}
for x in strikes:
    mark_covers.setdefault(x["cp"], [])
    if x["cover"] not in mark_covers[x["cp"]]:
        mark_covers[x["cp"]].append(x["cover"])


def cp_sort(cp):
    m = re.match(r"CP-(\d+)", cp)
    return (0, int(m.group(1))) if m else (1, cp)


def segments(sid):
    ys = sorted(y for y in (cover_key(c) for c in src_covers[sid]) if y is not None)
    segs = []
    for y in ys:
        if segs and y - segs[-1][1] < 1.25:
            segs[-1][1] = y
        else:
            segs.append([y, y])
    return [(a, max(b, a + 0.15)) for a, b in segs]


def span_text(sid):
    ys = [cover_key(c) for c in src_covers[sid] if cover_key(c) is not None]
    if not ys:
        return ""
    a, b = int(min(ys)), int(max(ys))
    return str(a) if a == b else f"{a}–{b}"


def inks(cp, sid=None):
    return ", ".join(sorted({x["ink"] for x in strikes if x["cp"] == cp and x["ink"] and (sid is None or x["src"] == sid)}))


# ---------------------------------------------------------------- images
_cache = {}


def scan(cid, side):
    """{'m': (path, w, h), 'l': (...)} relative to OUT, or None."""
    key = (cid, side)
    if key in _cache:
        return _cache[key]
    name = f"{cid}_{side}.jpg"
    src = os.path.join(IMG_SRC, name)
    if not os.path.exists(src):
        _cache[key] = None
        return None
    if not HAVE_PIL:
        rel = os.path.relpath(src, OUT).replace(os.sep, "/")
        _cache[key] = {"m": (rel, None, None), "l": (rel, None, None)}
        return _cache[key]
    out = {}
    rel_src = os.path.relpath(src, OUT).replace(os.sep, "/")
    for size, width in (("m", 900),):
        dst = os.path.join(OUT, "img", size, name)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            im = Image.open(src).convert("RGB")
            if im.width > width:
                im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
            im.save(dst, quality=84, optimize=True, progressive=True)
        with Image.open(dst) as im:
            out[size] = (f"img/{size}/{name}", im.width, im.height)
    out["l"] = (rel_src, None, None)   # zoom shows the original scan
    _cache[key] = out
    return out


def crop(cid, side, box, n):
    """Detail crop from the original scan; box is (x0, y0, x1, y1) as fractions."""
    if not HAVE_PIL:
        return None
    src = os.path.join(IMG_SRC, f"{cid}_{side}.jpg")
    if not os.path.exists(src):
        return None
    rel = f"img/crop/{cid}-{n}.jpg"
    dst = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    im = Image.open(src).convert("RGB")
    W, H = im.size
    c = im.crop((round(box[0] * W), round(box[1] * H), round(box[2] * W), round(box[3] * H)))
    s = 640 / max(c.size)
    if s < 1:
        c = c.resize((round(c.width * s), round(c.height * s)), Image.LANCZOS)
    c.save(dst, quality=88)
    return rel


# ---------------------------------------------------------------- layout
NAV = [("Home", "index.html"), ("Education", "education.html"), ("Rates", "rate.html"),
       ("Censors", "censors.html"), ("Forgeries", "forgery.html"),
       ("Collection", "collection.html"), ("Resources", "resources.html")]


def page(title, body, root, active, description=""):
    links = []
    for name, href in NAV:
        url = root + href
        cur = ' aria-current="page"' if name == active else ""
        links.append(f'<a href="{url}"{cur}>{name}</a>')
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="stylesheet" href="{root}assets/site.css">
<script>document.documentElement.classList.add("js")</script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="masthead">
  <div class="wrap masthead__inner">
    <a class="wordmark" href="{root}index.html"><span>Persian Postal History</span><span class="wordmark__fa" lang="fa" dir="rtl">تاریخ پستی ایران</span></a>
    <nav class="nav" aria-label="Main">{''.join(links)}</nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="footer">
  <div class="wrap">
    <p>Ahmad Shah era postal history, 1909–1925, from the collection of Masoud Valafar.</p>
    <p>Corrections and additions are welcome: <a href="mailto:masoudvalafar@gmail.com">masoudvalafar@gmail.com</a></p>
  </div>
</footer>
<dialog class="zoom" aria-label="Enlarged scan">
  <form method="dialog"><button class="zoom__close">Close</button></form>
  <div class="zoom__stage fit"><img alt=""></div>
</dialog>
<script src="{root}assets/site.js" defer></script>
</body>
</html>
"""


def write(rel, content):
    path = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def card(cid, root, sid):
    im = scan(cid, "front")
    pic = (f'<img src="{root}{im["m"][0]}" alt="" loading="lazy">' if im
           else '<span class="card__empty">Scan to be added</span>')
    return (f'<a class="card" id="card-{sid}-{cid}" data-cover="{cid}" href="{root}covers/{cid}.html?from={sid}">'
            f'<span class="card__img">{pic}</span>'
            f'<span class="card__title">{esc(route(cid))}</span>'
            f'<span class="card__meta">{esc(cover_when(cid))}, item {cid}</span></a>')


def timeline(root, active=None, only=None, marker=None, compact=False):
    """Bars per source. only: limit to these source ids. marker: year fraction to mark."""
    rows = []
    for s in sources:
        if only is not None and s["id"] not in only:
            continue
        segs = segments(s["id"])
        bars = "".join(
            f'<span class="bar" style="left:{max(pct(a), 0):.2f}%;width:{max(min(pct(b), 100) - max(pct(a), 0), 0.9):.2f}%;background:{s["color"]}"></span>'
            for a, b in segs) or '<span class="bar__none">No dated covers yet</span>'
        n = len(src_covers[s["id"]])
        cur = ' aria-current="true"' if s["id"] == active else ""
        rows.append(f'<a class="tl__row" href="{root}censors.html#{s["id"]}" data-source="{s["id"]}"{cur}>'
                    f'<span class="tl__label"><span class="tl__name">{esc(s["name"])}</span><span class="tl__count">{n}</span></span>'
                    f'<span class="tl__track">{bars}</span></a>')
    years = "".join(f"<span>{y}</span>" for y in range(START, END))
    ycols = f' style="grid-template-columns:repeat({END - START},minmax(0,1fr))"'
    events = "" if compact else "".join(
        f'<span class="tl__event" style="left:{pct(y):.2f}%">{esc(t)}</span>' for y, t in EVENTS)
    mark = (f'<span class="tl__marker" style="left:{pct(marker):.2f}%"></span>' if marker else "")
    return f"""<div class="tl{' tl--compact' if compact else ''}">
  {'' if compact else f'<div class="tl__head"><span></span><span class="tl__events">{events}</span></div>'}
  <div class="tl__rows">{''.join(rows)}<div class="tl__markerlane"><span></span><span class="tl__markertrack">{mark}</span></div></div>
  <div class="tl__axis"><span></span><span class="tl__years"{ycols}>{years}</span></div>
</div>"""


# ---------------------------------------------------------------- document pages
ITEMS = json.load(open(os.path.join(HERE, "data", "items.json"), encoding="utf-8"))
# Persiphila stamp numbers per cover, from the "stamps persiphila" column of the Inventory sheet.
STAMPS = json.load(open(os.path.join(HERE, "data", "stamps.json"), encoding="utf-8"))
DOCS = [
    ("education", "Reading a cover", "What you will find on a typical cover of the Ahmad Shah era, and the other markings to look for."),
    ("rate", "Postal rates", "A study of the rates of postal items during the Ahmad Shah era, 1909–1925, each shown on a cover that paid it."),
    ("forgery", "Forgeries", "How to approach counterfeit covers, a short list of checks, and examples."),
    ("collection", "Collection", "Notable items from the collection: stamps of every issue on cover, and mixed frankings."),
    ("resources", "Resources", "Books, catalogues and societies for the postal history of Iran."),
]
_img_cache = {}


def asset(name):
    """A non-scan image from the images folder (detail shots). Returns (medium, large) paths or None."""
    if name in _img_cache:
        return _img_cache[name]
    src = os.path.join(IMG_SRC, name)
    if not os.path.exists(src):
        _img_cache[name] = None
        return None
    if not HAVE_PIL:
        rel = os.path.relpath(src, OUT).replace(os.sep, "/")
        _img_cache[name] = (rel, rel)
        return _img_cache[name]
    out = []
    base = os.path.splitext(name)[0] + ".jpg"
    for size, width in (("m", 900),):
        dst = os.path.join(OUT, "img", size, base)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
            im = Image.open(src)
            if im.mode in ("RGBA", "LA", "P"):
                bg = Image.new("RGB", im.size, "white")
                im = im.convert("RGBA")
                bg.paste(im, mask=im.split()[-1])
                im = bg
            im = im.convert("RGB")
            if im.width > width:
                im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
            im.save(dst, quality=84, optimize=True, progressive=True)
        out.append(f"img/{size}/{base}")
    out.append(os.path.relpath(src, OUT).replace(os.sep, "/"))
    _img_cache[name] = tuple(out)
    return _img_cache[name]


MISSING_SCANS = set()


def item_card(key, root, show_stamps=False):
    it = ITEMS.get(key)
    if not it:
        return f"<!-- unknown item {esc(key)} -->"
    cid = it.get("id", "")
    figs = []
    for side, label in (("front", "Front"), ("back", "Back")):
        im = scan(cid, side) if cid else None
        if im:
            m, l = im["m"], im["l"]
            dims = f' width="{m[1]}" height="{m[2]}"' if m[1] else ""
            figs.append(f'<a class="scan__link" href="{root}{l[0]}" data-zoom><img src="{root}{m[0]}" alt="{label} of item {cid}"{dims} loading="lazy"></a>')
    if show_stamps and not figs:
        # On the Collection page an item waits for its scan before it is shown.
        MISSING_SCANS.add(cid)
        return f"<!-- item {esc(key)} ({esc(cid)}) has no scan yet -->"
    scans = f'<div class="item__scans item__scans--{len(figs)}">{"".join(figs)}</div>' if figs else ""
    title = it.get("title") or (f"Item {cid}" if cid.isdigit() else "")
    link = (f'<a class="item__link" href="{root}covers/{cid}.html?from={cover_srcs[cid][0]}">See this cover in Censors</a>'
            if cid in cover_srcs else "")
    desc = f'<p>{rich(it["description"])}</p>' if it.get("description") else ""
    # Only real inventory numbers are shown; internal ids like "forge1" are not.
    meta = f'<p class="item__id">Item {cid}</p>' if cid.isdigit() and title != f"Item {cid}" else ""
    title_html = f'<p class="item__title">{esc(title)}</p>' if title else ""
    st = STAMPS.get(cid) if show_stamps else None
    stamps = f'<p class="item__id">Stamps: {esc(", ".join(st))}</p>' if st else ""
    return (f'<article class="item" id="item-{esc(key)}">{scans}<div class="item__body">'
            f'{title_html}{meta}{stamps}{desc}{link}</div></article>')


def build_doc(name, title, lead):
    root = ""
    src = open(os.path.join(HERE, "content", f"{name}.html"), encoding="utf-8").read()
    src = re.sub(r"^<!--.*?-->\n?", "", src, flags=re.S)
    src = re.sub(r'(?:<x-item key="[^"]+"></x-item>\s*)+',
                 lambda m: '<div class="items">' + "".join(item_card(k, root, name == "collection") for k in re.findall(r'key="([^"]+)"', m.group(0))) + "</div>",
                 src)

    def detail(m):
        a = asset(m.group(1))
        if not a:
            return '<span class="detail__missing">Image not found</span>'
        return f'<a class="scan__link" href="{root}{a[1]}" data-zoom><img src="{root}{a[0]}" alt="" loading="lazy"></a>'
    src = re.sub(r'<img alt="" src="([^"]+)"/>', detail, src)

    # contents: h2 and h3 headings, linked to their section (or given an id)
    toc, used = [], set()

    def head(m):
        lvl, text = m.group(2), m.group(3)
        sid = m.group(1)
        if not sid:
            sid = re.sub(r"[^a-z0-9]+", "-", re.sub(r"<[^>]+>", "", text).lower()).strip("-") or "part"
            while sid in used:
                sid += "-x"
            used.add(sid)
            out = f'<h{lvl} id="{sid}">{text}</h{lvl}>'
        else:
            out = f'<h{lvl}>{text}</h{lvl}>'
        if lvl in ("2", "3"):
            toc.append((int(lvl), sid, re.sub(r"<[^>]+>", "", text)))
        return out
    src = re.sub(r'(?:<section class="sec" id="([^"]+)">\s*)?<h([2-6])>(.*?)</h\2>',
                 lambda m: (f'<section class="sec" id="{m.group(1)}">\n' if m.group(1) else "") + head(m), src)
    toc_html = ""
    if len(toc) >= 4:
        lis = "".join(f'<li class="toc__l{l}"><a href="#{i}">{esc(html.unescape(t))}</a></li>' for l, i, t in toc)
        toc_html = (f'<nav class="toc" aria-label="On this page"><details open><summary>On this page</summary>'
                    f'<ol>{lis}</ol></details></nav>')
    body = f"""
<section class="wrap pagehead">
  <h1 class="display">{esc(title)}</h1>
  <p class="lead">{esc(lead)}</p>
</section>
<div class="wrap doc{' doc--toc' if toc_html else ''}">
  {toc_html}
  <article class="doc__body">{src}</article>
</div>"""
    write(f"{name}.html", page(f"{title} · Persian Postal History", body, root, title_nav(name), lead))


def title_nav(name):
    return {"education": "Education", "rate": "Rates", "forgery": "Forgeries",
            "collection": "Collection", "resources": "Resources"}[name]


# ---------------------------------------------------------------- pages
def build_home():
    feat = "40229"
    im = scan(feat, "front")
    total = len(cover_srcs)
    sections = [
        ("Education", "education.html", "What you will find on a typical cover of the era: addresses, manuscript dates, postmarks, postbox, postage due and registration marks."),
        ("Rates", "rate.html", "Postal rates for letters, registration, receipts and foreign mail, each shown on a cover that paid it."),
        ("Censors", "censors.html", f"Who read the mail, and when: {total} censored items from nine sources, from the first Persian controls of 1910 to Reza Khan’s army."),
        ("Forgeries", "forgery.html", "Common and less common forgeries, and how to tell them apart."),
        ("Collection", "collection.html", "Notable items: the many ways to make up a rate, charity stamps, mixed frankings and more."),
        ("Resources", "resources.html", "Books, catalogues and societies for the postal history of Iran."),
    ]
    idx = "".join(f'<li><a href="{h}"><span class="index__name">{n}</span><span class="index__text">{t}</span></a></li>'
                  for n, h, t in sections)
    hero_img = (f'<a class="scan__link" href="{im["l"][0]}" data-zoom><img src="{im["m"][0]}" alt="Cover from Hamadan to Isfahan, 1917" fetchpriority="high"></a>'
                if im else "")
    body = f"""
<section class="wrap hero">
  <div>
    <h1 class="display">Persia’s mail in the reign of Ahmad Shah, 1909–1925</h1>
    <p class="fa-sub" lang="fa" dir="rtl">تاریخ پستی ایران در دوران احمدشاه قاجار</p>
    <p class="lead">Revolution, foreign occupation and famine all left their marks on the post. This site studies them through covers: where each letter went, what it cost, who stamped it and who read it on the way.</p>
  </div>
  <figure class="hero__cover sheet">{hero_img}
    <figcaption>Hamadan to Isfahan, 26 April 1917, read by three censors on one journey. <a href="covers/{feat}.html?from=persian">See the cover</a></figcaption>
  </figure>
</section>
<section class="wrap band">
  <h2 class="h2">On this site</h2>
  <ul class="index">{idx}</ul>
</section>
<section class="wrap band prose">
  <h2 class="h2">An ongoing study</h2>
  <p>I am Masoud Valafar, and I collect the postal history of Iran from 1909 to 1925, the reign of Ahmad Shah. The period was one of constant upheaval, and the post shows it: stamps ran out and were revalued by hand, routes bent around war zones, and letters were opened by one authority after another.</p>
  <p>This site is a work in progress. If you can correct a reading, date a mark or add an example, please write to me at <a href="mailto:masoudvalafar@gmail.com">masoudvalafar@gmail.com</a>.</p>
</section>"""
    write("index.html", page("Persian Postal History, 1909–1925", body, "", "Home",
                             "The postal history of Iran in the Ahmad Shah era, 1909–1925."))


def build_censors():
    root = ""
    ref = DATA["reference"]
    secs = []
    for s in sources:
        sid = s["id"]
        cps = sorted({x["cp"] for x in strikes if x["src"] == sid}, key=cp_sort)
        groups = []
        for cp in cps:
            cids = sort_covers(ordered_unique(x["cover"] for x in strikes if x["src"] == sid and x["cp"] == cp))
            ys = [cover_key(c) for c in cids if cover_key(c) is not None]
            yr = ""
            if ys:
                a, b = int(min(ys)), int(max(ys))
                yr = str(a) if a == b else f"{a}–{b}"
            note = ", ".join(v for v in (marks.get(cp, {}).get("place", ""), yr, inks(cp, sid)) if v)
            groups.append(f"""
  <div class="mgroup" id="{sid}-{mark_slug(cp)}">
    <div class="mgroup__head">
      <a class="mgroup__cp" href="censors/{mark_slug(cp)}.html">{esc(mark_name(cp))}</a>
      <p>{esc(note)}</p>
    </div>
    <div class="cards">{''.join(card(c, root, sid) for c in cids)}</div>
  </div>""")
        n = len(src_covers[sid])
        summary = f'{n} {"cover" if n == 1 else "covers"}, {len(cps)} {"mark" if len(cps) == 1 else "marks"}' + (f", {span_text(sid)}" if span_text(sid) else "")
        prov = '<p class="note">Attribution provisional.</p>' if s.get("provisional") else ""
        secs.append(f"""
<section class="source" id="{sid}" data-source="{sid}" aria-labelledby="h-{sid}">
  <div class="source__head">
    <h2 class="h1" id="h-{sid}">{esc(s['name'])}</h2>
    <p class="source__summary">{summary}</p>
  </div>
  {"".join(f'<p class="source__text">{rich(para)}</p>' for para in s['text'].split(chr(10) + chr(10)))}{prov}
  {''.join(groups)}
</section>""")
    body = f"""
<section class="wrap pagehead">
  <h1 class="display">Who read the mail, and when</h1>
  <p class="fa-sub" lang="fa" dir="rtl">مهرهای سانسور و ممیزی</p>
  <p class="lead">Each bar shows when one source’s censor marks appear on covers in this collection. Select a source to see its covers, grouped by mark, then select a cover to see everything it shows.</p>
  <p class="note">All CP numbers are from {esc(ref['author'])}’s catalogue, <a href="{ref['url']}"><cite>{esc(ref['title'])}</cite></a>.</p>
</section>
<section class="wrap" aria-label="Timeline by source">
  <div class="sheet tl-sheet">{timeline(root)}</div>
</section>
<div class="wrap sources">{''.join(secs)}</div>"""
    write("censors.html", page("Censor and control marks · Persian Postal History", body, root, "Censors",
                               "Who read Persian mail, and when, 1910–1925."))


def build_covers():
    root = "../"
    for cid, sids in cover_srcs.items():
        c = covers.get(cid, {})
        front, back = scan(cid, "front"), scan(cid, "back")
        feats = c.get("features", [])
        # numbered features, front first
        numbered = [dict(f, n=i + 1) for i, f in enumerate(sorted(feats, key=lambda f: f["side"] != "front"))]

        def figure(side, im, label):
            if not im:
                return ""
            spots = "".join(
                f'<a class="spot{" spot--censor" if f.get("censor") else ""}" href="#f{f["n"]}" '
                f'style="left:{f["x"] * 100:.1f}%;top:{f["y"] * 100:.1f}%" aria-label="Note {f["n"]}: {esc(f["title"])}">{f["n"]}</a>'
                for f in numbered if f["side"] == side)
            m, l = im["m"], im["l"]
            dims = f' width="{m[1]}" height="{m[2]}"' if m[1] else ""
            cap = label + (". Numbers match the notes below; censor marks are numbered in rust." if spots and side == "front" else ".")
            return (f'<figure class="sheet scanfig"><div class="scanfig__frame">'
                    f'<a class="scan__link" href="{root}{l[0]}" data-zoom><img src="{root}{m[0]}" alt="{label} of item {cid}"{dims}></a>'
                    f'{spots}</div><figcaption>{cap}</figcaption></figure>')

        scans = figure("front", front, "Front") + figure("back", back, "Back")
        if not scans:
            scans = '<div class="sheet noscan">Scans of this item are still to be added.</div>'

        # per-source navigation blocks
        navs, bottoms = [], []
        marker = cover_key(cid)
        for i, sid in enumerate(sids):
            s = src_by_id[sid]
            lst = src_covers[sid]
            k = lst.index(cid)
            prev_c = lst[k - 1] if k > 0 else None
            next_c = lst[k + 1] if k < len(lst) - 1 else None
            hidden = "" if i == 0 else " hidden"
            others = [o for o in sids if o != sid]
            also = (" Also read by " + ", ".join(
                f'<a href="{cid}.html?from={o}">{esc(src_by_id[o]["name"])}</a>' for o in others) + ".") if others else ""

            def pn(x, label, cls):
                if not x:
                    return f'<span class="pn {cls}"></span>'
                return (f'<a class="pn {cls}" href="{x}.html?from={sid}"><span class="pn__label">{label} in {esc(s["name"])}</span>'
                        f'<span class="pn__title">{esc(route(x))}, {esc(cover_when(x))}</span></a>')

            back_href = f"{root}censors.html?seen={cid}#{sid}"
            navs.append(f"""
<div class="ctx" data-source="{sid}"{hidden}>
  <div class="ctx__top">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="{root}censors.html">Censors</a><span>/</span><a href="{back_href}">{esc(s['name'])}</a><span>/</span><span aria-current="page">{esc(route(cid))}</span></nav>
    <p class="ctx__pos">Cover {k + 1} of {len(lst)} from {esc(s['name'])}.{also}</p>
  </div>
  <div class="ctx__row">
    {pn(prev_c, 'Previous', 'pn--prev')}
    <div class="ctx__strip">{timeline(root, active=sid, only=sids, marker=marker, compact=True)}</div>
    {pn(next_c, 'Next', 'pn--next')}
  </div>
</div>""")
            bottoms.append(f"""
<nav class="bottomnav" data-source="{sid}" aria-label="Covers from {esc(s['name'])}"{hidden}>
  {f'<a href="{prev_c}.html?from={sid}">Previous: {esc(route(prev_c))}</a>' if prev_c else '<span></span>'}
  <a class="bottomnav__back" href="{back_href}">Back to all {esc(s['name'])} covers</a>
  {f'<a href="{next_c}.html?from={sid}">Next: {esc(route(next_c))}</a>' if next_c else '<span></span>'}
</nav>""")

        # journey
        cps = ordered_unique(x["cp"] for x in strikes if x["cover"] == cid)
        parts = []
        for sid in sids:
            sc = ordered_unique(x["cp"] for x in strikes if x["cover"] == cid and x["src"] == sid)
            links = [f'<a href="{root}censors/{mark_slug(cp)}.html">{esc(mark_name(cp))}</a>' for cp in sc]
            joined = links[0] if len(links) == 1 else ", ".join(links[:-1]) + " and " + links[-1]
            parts.append(f'{joined} ({esc(src_by_id[sid]["name"])}{", provisional" if src_by_id[sid].get("provisional") else ""})')
        censored = "; ".join(parts)
        steps = []
        if c.get("from") or c.get("sent"):
            steps.append(("", f'{esc(c.get("from", "Posted"))}{", " + long_date(c["sent"]) if c.get("sent") else ""}', "Posted"))
        if c.get("via"):
            steps.append(("", f'Via {esc(c["via"])}', "In transit"))
        steps.append(("censor", "Read by censors", censored))
        if c.get("to") or c.get("received"):
            days = ""
            if c.get("sent") and c.get("received"):
                days = f', {(parse(c["received"]) - parse(c["sent"])).days} days later'
            steps.append(("", f'{esc(c.get("to", "Received"))}{", " + long_date(c["received"]) if c.get("received") else ""}',
                          "Received" + days if c.get("received") else "Destination"))
        journey = "".join(f'<li class="{cls}"><strong>{t}</strong><span>{d}</span></li>' for cls, t, d in steps)

        details = [("Item", f'{cid}, {esc(c.get("kind", "item").lower())}'), ("Rate", esc(c.get("rate", ""))),
                   ("Franking", esc(c.get("stamps", ""))),
                   ("Sources", ", ".join(f'<a href="{root}censors.html#{s}">{esc(src_by_id[s]["name"])}</a>' for s in sids))]
        dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in details if v)

        notes = ""
        if numbered:
            items = []
            for f in numbered:
                cr = crop(cid, f["side"], f["box"], f["n"])
                pic = f'<img src="{root}{cr}" alt="Detail: {esc(f["title"])}" loading="lazy">' if cr else ""
                items.append(f'<article class="note-card{" note-card--censor" if f.get("censor") else ""}" id="f{f["n"]}">'
                             f'{pic}<h3><span class="num">{f["n"]}</span>{esc(f["title"])}</h3><p>{rich(f["text"])}</p></article>')
            notes = f'<section class="shows" aria-label="What this cover shows"><h2 class="h1">What this cover shows</h2><div class="shows__grid">{"".join(items)}</div></section>'

        context = f'<section class="context"><h2 class="h3">{esc(c["context_title"])}</h2><p>{esc(c["context"])}</p></section>' if c.get("context") else ""
        fa = route_fa(cid)
        body = f"""
<div class="ctxbar"><div class="wrap">{''.join(navs)}</div></div>
<div class="wrap coverpage">
  <div class="coverpage__head">
    <div>
      <h1 class="display">{esc(route(cid))}</h1>
      {f'<p class="fa-sub" lang="fa" dir="rtl">{fa}</p>' if fa else ''}
    </div>
    {f'<p class="coverpage__summary">{rich(c["text"])}</p>' if c.get("text") else ''}
  </div>
  <div class="coverpage__main">
    <div class="coverpage__scans">{scans}</div>
    <aside class="coverpage__side">
      <section class="sheet panel"><h2 class="h3">The journey</h2><ol class="journey">{journey}</ol></section>
      <section class="sheet panel"><h2 class="h3">Details</h2><dl class="facts">{dl}</dl></section>
      {context}
    </aside>
  </div>
  {notes}
  {''.join(bottoms)}
</div>"""
        write(f"covers/{cid}.html", page(f"{route(cid)} ({cid}) · Persian Postal History", body, root, "Censors",
                                         f"{route(cid)}, item {cid}, with its censor marks."))


def build_marks():
    root = "../"
    allcps = sorted(mark_covers, key=cp_sort)
    for i, cp in enumerate(allcps):
        sids = ordered_unique(x["src"] for x in strikes if x["cp"] == cp)
        cids = sort_covers(mark_covers[cp])
        ys = [cover_key(c) for c in cids if cover_key(c) is not None]
        rows = [("Applied by", ", ".join(f'<a href="{root}censors.html#{s}">{esc(src_by_id[s]["name"])}</a>' for s in sids)),
                ("Reads", esc(marks.get(cp, {}).get("meaning", ""))), ("Ink", esc(inks(cp))),
                ("Seen", f"{int(min(ys))}–{int(max(ys))}" if ys and int(min(ys)) != int(max(ys)) else (str(int(ys[0])) if ys else "")),
                ("Covers", str(len(cids))),
                ("Catalogue", f'{esc(cp)} in {esc(DATA["reference"]["author"])}, <a href="{DATA["reference"]["url"]}"><cite>{esc(DATA["reference"]["title"])}</cite></a>' if cp.startswith("CP-") else "")]
        dl = "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows if v)
        prev_l = f'<a href="{mark_slug(allcps[i - 1])}.html">Previous mark: {esc(mark_name(allcps[i - 1]))}</a>' if i else "<span></span>"
        next_l = f'<a href="{mark_slug(allcps[i + 1])}.html">Next mark: {esc(mark_name(allcps[i + 1]))}</a>' if i < len(allcps) - 1 else "<span></span>"
        mtext = marks.get(cp, {}).get("text", "")
        mark_text = ('<section class="context">' + "".join(f"<p>{rich(p)}</p>" for p in mtext.split(chr(10) + chr(10))) + "</section>") if mtext else ""
        body = f"""
<div class="wrap">
  <nav class="crumbs crumbs--page" aria-label="Breadcrumb"><a href="{root}censors.html">Censors</a><span>/</span><a href="{root}censors.html#{sids[0]}">{esc(src_by_id[sids[0]]['name'])}</a><span>/</span><span aria-current="page">{esc(mark_name(cp))}</span></nav>
  <section class="markhead"><h1 class="markhead__cp">{esc(mark_name(cp))}</h1><dl class="facts">{dl}</dl></section>{mark_text}
  <div class="cards cards--wide">{''.join(card(c, root, sids[0]) for c in cids)}</div>
  <nav class="bottomnav">{prev_l}<span></span>{next_l}</nav>
</div>"""
        write(f"censors/{mark_slug(cp)}.html", page(f"{mark_name(cp)} · Censor marks · Persian Postal History", body, root,
                                                    "Censors", f"{mark_name(cp)}, a censor mark on Persian mail."))


def copy_assets():
    src = os.path.join(HERE, "assets")
    dst = os.path.join(OUT, "assets")
    if os.path.abspath(src) != os.path.abspath(dst):
        shutil.copytree(src, dst, dirs_exist_ok=True)


build_home()
for _n, _t, _l in DOCS:
    build_doc(_n, _t, _l)
build_censors()
build_covers()
build_marks()
copy_assets()
print(f"Built {len(DOCS) + 1} pages, the timeline, {len(cover_srcs)} cover pages and {len(mark_covers)} mark pages into {OUT}"
      + ("" if HAVE_PIL else " (Pillow not installed: linking original scans, no detail crops)"))
if MISSING_SCANS:
    print("Collection items waiting for scans in images/: " + ", ".join(sorted(MISSING_SCANS)))
