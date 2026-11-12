"""Phase 2: extract weapon balance changes from cached patch pages -> data/patches/*.json"""
import re, os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse import ROOT, blocks, weapon_heading, is_pseudo_heading, BULLET_RE, canon
from classify import classify, values

PATCH_DIR = os.path.join(ROOT, "data", "patches")
os.makedirs(PATCH_DIR, exist_ok=True)

NOT_PATCH = {
    "confidential-technical-test", "early-access-packs-available-now", "launch-release-notes",
    "early-access-preload", "autumn-2024-content-roadmap", "launch-prep-activity-times",
    "spear-deep-dive", "tico-holiday-letter-2024", "wilds-of-talandre-announcement",
    "summer-in-solisium", "the-frozen-divide-announcement",
}
# expansion notes that live on /game/releases/<slug> instead of in the news article
RELEASE_PAGES = [
    ("call-of-the-spear-1-10-0", "The Call of the Spear (1.10.0) Release Notes", "2024-12-04"),
    ("wilds-of-talandre",        "Wilds of Talandre Release Notes",              "2025-03-05"),
    ("solisiums-awakening",      "Solisium's Awakening Release Notes",           "2025-09-17"),
]

SKILLNAME = re.compile(r"^\s*((?:Skill Core|Passive|Mastery|Specialization)?\s*:?\s*[^:]{2,90}?)\s*:\s+(.+)$", re.S)
LEADIN = re.compile(r"^(Skill Core|Passive Skill|Passive|Mastery|Weapon Mastery|Specialization)\s*:\s*", re.I)

def skill_name(text):
    """Leading 'Name: rest' -> Name. Handles 'Skill Core: Flash: ...' (two colons)."""
    t = text.strip()
    prefix = ""
    m = LEADIN.match(t)
    if m:
        prefix = m.group(0).strip() + " "
        t = t[m.end():]
    m = SKILLNAME.match(t)
    if not m:
        return None
    name = m.group(1).strip()
    if len(name) > 90 or name.count(" ") > 12 or name.endswith((".", "!", "?")):
        return None
    return (prefix + name).strip()

BARE_W = re.compile(r"^\s*(" + "|".join([
    "greatsword", r"sword\s*(?:and|&|/)\s*shield", "daggers?", "crossbows?", "longbow",
    "staff", r"wand\s*(?:and|&)\s*tome", "wand", "spear", "orb", "gauntlets?"]) + r")\s*:?\s*$", re.I)

ACTION = re.compile(r"(?i)^(fixed|corrected|resolved|added|new|increas|decreas|reduc|chang|adjust|"
                    r"remov|updat|improv|now|expand|extend|lower|rais|renam|replac|modif)")

def strip_names(text):
    """Drop the leading 'Skill Name:' (and 'Skill Name: Spec Name:') label chain."""
    rest = text.strip()
    for _ in range(3):
        m = re.match(r"^([^:.]{2,70}):\s+(?=\S)", rest)
        if not m or ACTION.match(m.group(1).strip()) or len(m.group(1).split()) > 8:
            break
        rest = rest[m.end():]
    return rest or text


def extract(path, scope, meta):
    bs = blocks(path, scope)
    sec_w = None          # weapon set by a heading / pseudo-heading
    sec_name = None       # nearest non-weapon heading, for context
    list_w = None         # weapon set by a bare "Dagger:" list label
    list_d = -1
    entries = []
    last = None
    lead_in, lead_d = None, -1
    last_prose = None
    plab_w, plab_s = None, None

    for kind, depth, text in bs:
        if kind.startswith("h") or (kind == "p" and is_pseudo_heading(kind, text)):
            w = weapon_heading(kind, text)
            sec_w, list_w, list_d, last = w, None, -1, None
            lead_in, lead_d, last_prose = None, -1, None
            plab_w, plab_s = None, None
            if not w:
                sec_name = text
            continue
        if kind not in ("li", "p"):
            continue

        # a bare "Dagger:" bullet labels the nested bullets beneath it
        m = BARE_W.match(text)
        if kind == "li" and m and canon(m.group(1)):
            list_w, list_d, last = canon(m.group(1)), depth, None
            continue
        if list_w is not None and depth <= list_d:
            list_w, list_d = None, -1
        if lead_in is not None and depth <= lead_d:
            lead_in, lead_d = None, -1
        if kind == "li" and text.rstrip().endswith(":") and not BULLET_RE.match(text):
            lead_in, lead_d, last = text, depth, None
            continue

        # a <p> like "Staff: Elemental Awakening" labels the <li> lines that follow
        if kind == "p":
            pm = BULLET_RE.match(text)
            if pm and canon(pm.group(1)) and "." not in pm.group(2) and len(pm.group(2)) <= 80:
                plab_w, plab_s, last = canon(pm.group(1)), pm.group(2).strip(), None
                last_prose = text
                continue
            plab_w, plab_s = None, None

        weapon, body, base = None, text, 0
        if list_w is not None and depth > list_d:
            weapon, base = list_w, list_d + 1
        elif sec_w and kind == "li":
            weapon, base = sec_w, 0
        else:
            mm = BULLET_RE.match(text)
            if mm and canon(mm.group(1)):
                weapon, body, base = canon(mm.group(1)), mm.group(2).strip(), depth
            elif plab_w and kind == "li":
                weapon, base = plab_w, depth
            else:
                if kind == "p" or depth == 0:
                    last_prose = text
                last = None
                continue

        if depth > base and last is not None and last["weapon"] == weapon:
            last["sub_lines"].append(text)
            continue

        ctx = lead_in if (lead_in is not None and depth > lead_d) else None
        label_like = len(body) <= 80 and "." not in body
        if ctx is None and label_like:
            ctx = last_prose or sec_name
        if plab_w == weapon and plab_s and ctx is None:
            ctx = plab_s
        sn = skill_name(body) or (plab_s if plab_w == weapon else None)
        rest = strip_names(body)
        if sn is None and ctx and len(body) <= 80 and "." not in body:
            sn = body.strip()
        basis = (ctx + " " + rest) if ctx else rest
        ct, conf = classify(basis)
        before, after = values(basis)
        e = {
            "patch_date": meta["date"], "patch_title": meta["title"], "source_url": meta["url"],
            "weapon": weapon, "section": sec_name, "context_line": ctx,
            "skill_or_mechanic_name": sn,
            "change_type": ct, "type_confidence": conf,
            "before_value": before, "after_value": after,
            "change_text": text, "sub_lines": [],
        }
        entries.append(e)
        last = e
    return entries

def main():
    arts = json.load(open(os.path.join(ROOT, "data", "articles.json"), encoding="utf-8"))
    by_slug = {a["slug"]: a for a in arts}
    jobs = []
    for a in arts:
        if a["tag"] != "Update" or a["slug"] in NOT_PATCH:
            continue
        jobs.append((os.path.join(ROOT, "cache", "articles", a["slug"] + ".html"), "article",
                     {"date": a["date"], "title": a["title"].replace("�", " ").strip(), "url": a["url"], "slug": a["slug"]}))
    for slug, title, date in RELEASE_PAGES:
        jobs.append((os.path.join(ROOT, "cache", "releases", slug + ".html"), "main",
                     {"date": date, "title": title,
                      "url": "https://www.playthroneandliberty.com/en-gb/game/releases/" + slug,
                      "slug": "release-" + slug}))

    manifest, empty = [], []
    for path, scope, meta in sorted(jobs, key=lambda j: j[2]["date"]):
        ents = extract(path, scope, meta)
        out = {"patch_date": meta["date"], "patch_title": meta["title"], "source_url": meta["url"],
               "slug": meta["slug"], "n_changes": len(ents), "changes": ents}
        json.dump(out, open(os.path.join(PATCH_DIR, f"{meta['date']}_{meta['slug']}.json"), "w",
                            encoding="utf-8"), indent=1, ensure_ascii=False)
        manifest.append({"date": meta["date"], "slug": meta["slug"], "title": meta["title"],
                         "url": meta["url"], "n_changes": len(ents),
                         "weapons": sorted({e["weapon"] for e in ents})})
        if not ents:
            empty.append(meta["slug"])
        print(f"{meta['date']}  {meta['slug'][:34]:34}  {len(ents):4d}  " +
              ",".join(sorted({e['weapon'] for e in ents}))[:60])
    json.dump(manifest, open(os.path.join(ROOT, "data", "manifest.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print("\npatches:", len(manifest), " total changes:", sum(m["n_changes"] for m in manifest),
          " no weapon content:", len(empty))
    print("empty:", ", ".join(empty))

if __name__ == "__main__":
    main()
