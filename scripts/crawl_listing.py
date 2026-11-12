import re, os, time, json, urllib.request, html

BASE = "https://www.playthroneandliberty.com"
LOC = "/en-gb"
CACHE = os.path.join(os.path.dirname(__file__), "..", "cache", "listing")
os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}

def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return open(path, encoding="utf-8", errors="replace").read()
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        t = r.read().decode("utf-8", "replace")
    open(path, "w", encoding="utf-8").write(t)
    time.sleep(1.2)
    return t

CARD = re.compile(
    r'href="(/en-gb/news/articles/[^"]+)"'          # 1 url
    r'.*?aria-label="([^"]*)"'                      # 2 title
    r'.*?slotLink-info-subheading[^>]*>\s*(.*?)\s*</h4>'  # 3 category
    , re.S)

def parse(h):
    out = []
    for m in CARD.finditer(h):
        url, title, cat = m.group(1), html.unescape(m.group(2)), html.unescape(m.group(3))
        out.append({"url": BASE + url, "slug": url.rsplit("/", 1)[-1], "title": title, "category": cat})
    return out

all_items, seen, page = [], set(), 1
while page <= 60:
    url = f"{BASE}{LOC}/news" + (f"?page={page}" if page > 1 else "")
    h = fetch(url, os.path.join(CACHE, f"page{page:02d}.html"))
    items = parse(h)
    new = [i for i in items if i["slug"] not in seen]
    print(f"page {page}: {len(items)} cards, {len(new)} new")
    if not new:
        break
    for i in new:
        seen.add(i["slug"]); all_items.append(i)
    page += 1

json.dump(all_items, open(os.path.join(os.path.dirname(__file__), "..", "data", "articles.json"), "w", encoding="utf-8"), indent=1)
print("TOTAL", len(all_items))
