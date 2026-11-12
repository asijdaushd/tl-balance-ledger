import re

UP   = (r"(?:increase[sd]?|increasing|raise[sd]?|raising|improve[sd]?|improving|boost(?:s|ed|ing)?|"
        r"extend(?:s|ed|ing)?|expand(?:s|ed|ing)?|amplifie[sd]|amplified|buffed|strengthened|greater|higher|more)")
DOWN = (r"(?:decrease[sd]?|decreasing|reduce[sd]?|reducing|lower(?:s|ed|ing)?|shorten(?:s|ed|ing)?|"
        r"nerfed|remove[sd]?|removing|less|fewer|shorter|smaller)")
DIR  = re.compile(r"(?i)\b(" + UP + r"|" + DOWN + r")\b")
UP_ONLY = re.compile(r"(?i)^" + UP + r"$")

INVERTED = (r"cooldown|cost|costs|mana|stamina|charge time|cast time|casting time|time required|"
            r"activation requirement|requirement|penalt|recharge|delay|threshold")
GOOD = (r"damage|heal|healing|duration|range|radius|amount|value|stack|chance|rate|power|"
        r"defense|resistance|shield|speed|hit|effect|bonus|reward|potency|magnitude")

FIX = re.compile(r"(?i)\b(fixed|corrected|resolved|addressed an issue|an issue where|an issue causing|"
                 r"an issue that|an issue preventing|an issue allowing|now properly|now correctly|as intended)\b")
NEW = re.compile(r"(?i)(^\s*(added|new)\b|\badded (?:the |a |an )?new\b|\bhas been added\b|"
                 r"\bhave been added\b|\bnewly added\b|\bnew skill\b|\bnew effect\b|\bnew specialization\b)")
REWORK = re.compile(r"(?i)\b(renamed|reworked|redesigned|revamped|changed|adjusted|updated|replaced|"
                    r"converted|swapped|restructured|modified|reclassified|now applies|moved)\b")
TOOLTIP = re.compile(r"(?i)\b(tooltip|skill description|descriptions?|text update|notation|localiz|"
                     r"displayed|display\b|wording)")
NOLONGER = re.compile(r"(?i)\bno longer\b")
CANNOW = re.compile(r"(?i)\b(can now|now also|now stacks|now grants|now applies to)\b")


def _proper_noun(text, m):
    """A capitalized direction word mid-sentence belongs to a skill/spec name, not the verb."""
    if not m.group(1)[:1].isupper():
        return False
    if m.start() == 0:
        return False
    pre = text[max(0, m.start() - 2):m.start()]
    return not re.search(r"[.;:!?]\s$", pre)


def _direction(text):
    score = 0
    for m in DIR.finditer(text):
        if _proper_noun(text, m):
            continue
        word = m.group(1)
        tail = text[m.end(): m.end() + 90].lower()
        head = text[max(0, m.start() - 45): m.start()].lower()
        up = bool(UP_ONLY.match(word))
        if word.lower().startswith("remov"):
            up = False
        elif re.search(INVERTED, tail + " " + head) and not re.search(GOOD, tail[:40]):
            up = not up
        weight = 2 if m.start() == 0 else 1     # sentence-initial verb states the change
        score += weight if up else -weight
    return score


def classify(text):
    """Return (change_type, confidence)."""
    t = text.strip()
    if FIX.search(t):
        return "bugfix", "high" if re.match(r"(?i)^(fixed|corrected|resolved)", t) else "medium"
    if NEW.search(t):
        return "new", "high" if re.match(r"(?i)^added\b", t) else "medium"
    d = _direction(t)
    if d == 0 and NOLONGER.search(t) and not CANNOW.search(t):
        return "nerf", "medium"
    if d > 0:
        return "buff", "high" if d > 1 else "medium"
    if d < 0:
        return "nerf", "high" if d < -1 else "medium"
    if TOOLTIP.search(t):
        return "bugfix", "low"
    if REWORK.search(t):
        return "rework", "medium"
    if re.search(r"(?i)\bnow\b", t):
        return "rework", "low"
    return "other", "low"


NUM = r"[0-9][0-9,.]*\s*(?:%|s\b|sec\w*|m\b|meters?|points?|stacks?|times?)?"
FROM_TO = re.compile(r"(?i)\bfrom\s+(" + NUM + r")\s+to\s+(" + NUM + r")")
ARROW   = re.compile(r"(" + NUM + r")\s*(?:→|->)\s*(" + NUM + r")")


def values(text):
    m = FROM_TO.search(text) or ARROW.search(text)
    if not m:
        return None, None
    return m.group(1).strip().rstrip(".,"), m.group(2).strip().rstrip(".,")
