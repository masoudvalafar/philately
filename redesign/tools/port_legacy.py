"""One-time port of the legacy pages into content/*.html fragments and data/items.json."""
import json, re, sys
from bs4 import BeautifulSoup, NavigableString, Tag

SRC = sys.argv[1]
OUT = sys.argv[2]

# ---- items.js -> items.json
js = open(f"{SRC}/items.js", encoding="utf-8").read()
items = {}
for m in re.finditer(r'"([^"]*)"\s*:\s*\{(.*?)\n\s*\},', js, re.S):
    key, body = m.group(1), m.group(2)
    if not key:
        continue
    rec = {}
    for f in re.finditer(r"(\w+)\s*:\s*(['\"`])((?:\\.|(?!\2).)*?)\2", body, re.S):
        val = f.group(3)
        val = re.sub(r"\\\s*\n\s*", " ", val)          # line continuations
        val = val.replace("\\'", "'").replace('\\"', '"')
        rec[f.group(1)] = re.sub(r"\s+", " ", val).strip()
    items[key] = rec
json.dump(items, open(f"{OUT}/data/items.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("items:", len(items))

def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:60] or "section"

used_ids = set()
def uid(t):
    s = slug(t); base = s; n = 2
    while s in used_ids:
        s = f"{base}-{n}"; n += 1
    used_ids.add(s); return s

def port(name, skip_titles=()):
    used_ids.clear()
    soup = BeautifulSoup(open(f"{SRC}/{name}.html", encoding="utf-8").read(), "html.parser")
    main = soup.select_one("div.main-content")
    title = None
    # scripts -> x-item placeholders
    for sc in main.find_all("script"):
        keys = re.findall(r'addItem\(items\["([^"]+)"\]', sc.string or "")
        frag = "".join(f'<x-item key="{k}"></x-item>' for k in keys)
        sc.replace_with(BeautifulSoup(frag, "html.parser"))
    hmap = {"h2": 1, "h3": 2, "h4": 3, "h5": 4}

    def walk(container, default, plain_level):
        """default: level for collapsibles before any plain heading; plain_level: level for plain headings."""
        last_plain = None
        children = list(container.children)
        i = 0
        while i < len(children):
            ch = children[i]
            if isinstance(ch, Tag) and ch.name in ("h3", "h4", "h5") and not ch.has_attr("data-gen"):
                lvl = plain_level if container is not main else (2 if ch.name == "h3" else 3)
                ch.name = f"h{min(6, lvl)}"
                last_plain = lvl
            if isinstance(ch, Tag) and ch.name == "button" and "collapsible" in (ch.get("class") or []):
                j = i + 1
                while j < len(children) and not (isinstance(children[j], Tag) and children[j].name == "div"):
                    j += 1
                div = children[j] if j < len(children) else None
                text = ch.get_text(" ", strip=True)
                lvl = min(6, (last_plain + 1) if last_plain else default)
                sec = soup.new_tag("section", attrs={"class": "sec", "id": uid(text)})
                h = soup.new_tag(f"h{lvl}", attrs={"data-gen": "1"}); h.string = text
                sec.append(h)
                if div is not None:
                    for c in list(div.contents):
                        sec.append(c.extract())
                    div.decompose()
                    walk(sec, min(6, lvl + 1), min(6, lvl + 1))
                    if not sec.get_text(strip=True).replace(text, "") and not sec.find("x-item") and not sec.find("img"):
                        p = soup.new_tag("p", attrs={"class": "empty"}); p.string = "No example in the collection yet."
                        sec.append(p)
                if text in skip_titles:
                    sec.clear()
                    sec.append(h)
                    sec.append(BeautifulSoup(skip_titles[text], "html.parser"))
                ch.replace_with(sec)
                children = list(container.children)
                i = children.index(sec) + 1
                continue
            i += 1

    # page title: a leading h2, if any
    first_h2 = main.find("h2")
    if first_h2 and first_h2.parent is main:
        title = first_h2.get_text(" ", strip=True); first_h2.decompose()
    walk(main, 2, 2)

    # clean attributes, inline styles, ids from old divs
    for t in main.find_all(True):
        if t.name == "img":
            src = t.get("src", "").replace("./images/", "")
            t.attrs = {"src": src, "alt": ""}
        elif t.name == "a":
            href = t.get("href", "")
            href = {"./rate.html": "rate.html", "./education.html": "education.html", "./forgery.html": "forgery.html",
                    "./collection.html": "collection.html", "./resources.html": "resources.html"}.get(href, href)
            t.attrs = {"href": href}
        elif t.name == "section":
            t.attrs = {"class": "sec", "id": t.get("id")}
        elif t.name == "figure":
            t.attrs = {"class": "detail"}
        elif t.name == "div" and "details" in (t.get("class") or []):
            t.attrs = {"class": "details"}
        elif t.name == "x-item":
            t.attrs = {"key": t.get("key")}
        elif t.name == "p" and "empty" in (t.get("class") or []):
            t.attrs = {"class": "empty"}
        else:
            t.attrs = {}
    # unwrap list items that only hold an item placeholder
    for li in main.find_all("li"):
        if li.find("x-item") and not li.get_text(strip=True):
            li.unwrap()
    for lst in main.find_all(["ol", "ul"]):
        if not lst.find("li"):
            lst.unwrap()
    from bs4 import Comment
    for c in main.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    # an image followed by a paragraph becomes a captioned detail figure
    for img in main.find_all("img"):
        fig = soup.new_tag("figure", attrs={"class": "detail"})
        nxt = img.find_next_sibling()
        img.replace_with(fig)
        fig.append(img)
        if nxt is not None and nxt.name == "p" and fig.find_next_sibling() is nxt:
            cap = soup.new_tag("figcaption")
            for c in list(nxt.contents):
                cap.append(c.extract())
            nxt.decompose()
            fig.append(cap)
    # group runs of figures
    for fig in main.find_all("figure", class_="detail"):
        if fig.parent and fig.parent.name == "div":
            continue
        grid = soup.new_tag("div", attrs={"class": "details"})
        fig.insert_before(grid)
        run = [fig]
        sib = fig.find_next_sibling()
        while sib is not None and sib.name == "figure":
            run.append(sib)
            sib = sib.find_next_sibling()
        for f in run:
            grid.append(f.extract())
    for t in main.find_all(string=True):
        if t.parent.name not in ("pre", "code"):
            t.replace_with(re.sub(r"\s+", " ", t))
    html = main.decode_contents()
    html = re.sub(r"\s*(</?(?:section|h[1-6]|p|ul|ol|li|figure|figcaption|div)\b[^>]*>)\s*", r"\n\1", html)
    html = re.sub(r"(<(?:p|li|figcaption|h[1-6])\b[^>]*>)\n", r"\1", html)
    html = re.sub(r"\n(</(?:p|li|figcaption|h[1-6])>)", r"\1", html)
    html = re.sub(r"\n\s*\n+", "\n", html).strip()
    open(f"{OUT}/content/{name}.html", "w", encoding="utf-8").write(
        (f"<!-- title: {title} -->\n" if title else "") + html + "\n")
    print(name, "sections:", html.count('<section'), "items:", html.count("<x-item"))

port("education")
port("rate")
port("forgery")
port("resources")
port("collection", skip_titles={"Censor and Control Marks":
    '<p>Censored covers now have their own section, with a timeline of who read the mail and a page for every cover. <a href="censors.html">Go to censor and control marks</a>.</p>'})
