import re, os, json, time, urllib.request, html

ROOT = os.path.join(os.path.dirname(__file__), "..")
CACHE = os.path.join(ROOT, "cache", "articles")
os.makedirs(CACHE, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"}
arts = json.load(open(os.path.join(ROOT, "data", "articles.json"), encoding="utf-8"))

def get(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 2000:
        return open(path, encoding="utf-8", errors="replace").read()
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                t = r.read().decode("utf-8", "replace")
            break
        except Exception as e:
            print("  retry", e); time.sleep(4)
    else:
        return None
    open(path, "w", encoding="utf-8").write(t)
    time.sleep(1.0)
    return t

BAL = re.compile(r"(?i)(class balance|combat balance|weapon skill|skill balance|weapon balance|balance adjust|skill adjust|weapon changes|combat changes|balance changes)")
for i, a in enumerate(arts, 1):
    h = get(a["url"], os.path.join(CACHE, a["slug"] + ".html"))
    if h is None:
        a["date"] = None; print(i, a["slug"], "FETCH FAIL"); continue
    m = re.search(r'articlePane-date">\s*<span>([^<]+)</span>', h)
    d = m.group(1).strip() if m else None
    if d and re.match(r"\d\d/\d\d/\d{4}", d):
        dd, mm, yy = d.split("/"); a["date"] = f"{yy}-{mm}-{dd}"
    else:
        a["date"] = d
    t = re.search(r'articlePane-tag">\s*(.*?)\s*</h4>', h, re.S)
    a["tag"] = html.unescape(t.group(1)).strip() if t else a.get("category")
    heads = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<h[23][^>]*>(.*?)</h[23]>", h, re.S)]
    a["headings"] = [html.unescape(x) for x in heads if x]
    a["balance_hit"] = sorted(set(x.lower() for x in BAL.findall(h)))
    if i % 20 == 0: print("...", i)

arts.sort(key=lambda x: (x["date"] or "0000"), reverse=True)
json.dump(arts, open(os.path.join(ROOT, "data", "articles.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("done", len(arts), "no-date:", sum(1 for a in arts if not a["date"]))
