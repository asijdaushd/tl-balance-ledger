"""Shared parsing helpers: turn a cached T&L page into an ordered list of content blocks."""
import re, os
from bs4 import BeautifulSoup

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

WEAPON_ALTS = (r"greatsword|sword\s*(?:and|&|/)\s*shield|daggers?|crossbows?|"
               r"longbow|staff|wand\s*(?:and|&)\s*tome|wand|spear|orb|gauntlets?")
SUFFIX = r"(?:\s*(?:changes?|balance(?:\s*changes?)?|adjustments?|skills?|updates?|skill\s*changes?))?"
HEAD_RE   = re.compile(r"^\s*(" + WEAPON_ALTS + r")" + SUFFIX + r"\s*[:\-–]?\s*$", re.I)
BULLET_RE = re.compile(r"^\s*(?:skills?\s*[-–]\s*)?(" + WEAPON_ALTS + r")\s*[:\-–]\s*(.+)$", re.I | re.S)

CANON = [
    (r"sword\s*(?:and|&|/)\s*shield", "Sword and Shield"),
    (r"greatsword", "Greatsword"),
    (r"daggers?", "Dagger"),
    (r"crossbows?", "Crossbow"),
    (r"longbow", "Longbow"),
    (r"staff", "Staff"),
    (r"wand\s*(?:and|&)\s*tome", "Wand and Tome"),
    (r"wand", "Wand and Tome"),          # folded per user
    (r"spear", "Spear"),
    (r"orb", "Orb"),
    (r"gauntlets?", "Gauntlets"),
]
WEAPONS = ["Sword and Shield", "Greatsword", "Dagger", "Crossbow", "Longbow",
           "Staff", "Wand and Tome", "Spear", "Orb", "Gauntlets"]

def canon(name):
    n = re.sub(r"\s+", " ", name.strip().lower())
    for pat, out in CANON:
        if re.fullmatch(pat, n):
            return out
    return None

def norm(s):
    s = s.replace("\xa0", " ").replace("​", "").replace("’", "'")
    return re.sub(r"\s+", " ", s).strip()

SKIP_TXT = re.compile(r"^\d+ ?KB$|^$")

def blocks(path, scope="article"):
    """Ordered [(kind, depth, text)] for headings / list items / paragraphs.

    A nested <ul> inside an <li> is NOT folded into the parent's text: the parent
    keeps only its own direct text and children are emitted after it with depth+1.
    """
    html = open(path, encoding="utf-8", errors="replace").read()
    soup = BeautifulSoup(html, "lxml")
    root = soup.find("article") if scope == "article" else soup.find("main")
    if root is None:
        root = soup.find("main") or soup.body
    out = []

    def own_text(tag):
        parts = []
        for c in tag.children:
            if getattr(c, "name", None) in ("ul", "ol"):
                continue
            parts.append(c.get_text(" ") if hasattr(c, "get_text") else str(c))
        return norm(" ".join(parts))

    def walk(tag, depth):
        for c in tag.children:
            n = getattr(c, "name", None)
            if n is None:
                continue
            if re.fullmatch(r"h[1-6]", n or ""):
                t = norm(c.get_text(" "))
                if not SKIP_TXT.match(t):
                    out.append((n, depth, t))
            elif n == "li":
                t = own_text(c)
                if not SKIP_TXT.match(t):
                    out.append(("li", depth, t))
                for sub in c.find_all(["ul", "ol"], recursive=False):
                    walk(sub, depth + 1)
            elif n == "p":
                t = norm(c.get_text(" "))
                if not SKIP_TXT.match(t):
                    out.append(("p", depth, t))
            elif n in ("ul", "ol"):
                walk(c, depth)
            else:
                walk(c, depth)

    walk(root, 0)
    return out

def weapon_heading(kind, text):
    """Return canonical weapon if this block acts as a weapon section header."""
    m = HEAD_RE.match(text)
    if not m:
        return None
    if kind.startswith("h") or (kind == "p" and len(text) <= 32):
        return canon(m.group(1))
    return None

def is_pseudo_heading(kind, text):
    """A short <p> with no terminal punctuation used as a section label."""
    if kind.startswith("h"):
        return True
    if kind != "p":
        return False
    return len(text) <= 48 and not text.endswith((".", "!", "?")) and ":" not in text
