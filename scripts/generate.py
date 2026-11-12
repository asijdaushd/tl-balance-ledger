"""Phase 3 + 4: merge per-patch JSON, group by weapon, emit self-contained HTML."""
import os, re, json, glob, html, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse import ROOT, WEAPONS

OUT = os.path.join(ROOT, "output")
os.makedirs(OUT, exist_ok=True)

TYPES = [("buff", "Buff"), ("nerf", "Nerf"), ("rework", "Rework"),
         ("bugfix", "Bug fix"), ("new", "New"), ("other", "Other")]


def slug(w):
    return re.sub(r"[^a-z0-9]+", "-", w.lower()).strip("-")


def e(s):
    return html.escape(s or "", quote=True)


CSS = """
:root{
  --bg:#12141a; --panel:#1a1d25; --panel2:#20242e; --line:#2c313d;
  --fg:#e6e8ee; --muted:#98a0b3; --accent:#7aa2f7;
  --buff:#3fb950; --nerf:#f85149; --rework:#d29922; --bugfix:#8b949e; --new:#58a6ff; --other:#6e7681;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:15px/1.55 ui-sans-serif,system-ui,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent)}
.wrap{max-width:1000px;margin:0 auto;padding:28px 20px 80px}
header h1{margin:0 0 6px;font-size:28px;letter-spacing:.3px}
h2{font-size:19px;margin:0 0 10px}
.sum{color:var(--muted);font-size:14px;margin-bottom:18px}
.sum b{color:var(--fg)}
.bar{position:sticky;top:0;z-index:5;background:rgba(18,20,26,.94);
  backdrop-filter:blur(6px);border-bottom:1px solid var(--line);
  padding:10px 0;margin-bottom:22px;display:flex;flex-wrap:wrap;gap:10px;align-items:center}
select{background:var(--panel2);color:var(--fg);border:1px solid var(--line);
  border-radius:6px;padding:6px 9px;font-size:13px;max-width:100%}
.filters{display:flex;flex-wrap:wrap;gap:6px}
.filters button{background:var(--panel2);color:var(--muted);border:1px solid var(--line);
  border-radius:999px;padding:4px 11px;font-size:12px;cursor:pointer;font-weight:600}
.filters button.on{color:#0d1117}
.filters button.on[data-t=buff]{background:var(--buff);border-color:var(--buff)}
.filters button.on[data-t=nerf]{background:var(--nerf);border-color:var(--nerf)}
.filters button.on[data-t=rework]{background:var(--rework);border-color:var(--rework)}
.filters button.on[data-t=bugfix]{background:var(--bugfix);border-color:var(--bugfix)}
.filters button.on[data-t=new]{background:var(--new);border-color:var(--new)}
.filters button.on[data-t=other]{background:var(--other);border-color:var(--other)}
.tl{position:relative;padding-left:26px}
.tl:before{content:"";position:absolute;left:7px;top:6px;bottom:6px;width:2px;background:var(--line)}
.patch{position:relative;margin:0 0 26px}
.patch:before{content:"";position:absolute;left:-23px;top:12px;width:12px;height:12px;
  border-radius:50%;background:var(--accent);border:3px solid var(--bg)}
.phead{display:flex;flex-wrap:wrap;gap:10px;align-items:baseline;margin-bottom:8px}
.pdate{font-variant-numeric:tabular-nums;color:var(--muted);font-size:13px}
.ptitle{font-size:17px;font-weight:700}
.plink{font-size:12px}
.chg{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--other);
  border-radius:7px;padding:10px 13px;margin:7px 0}
.chg[data-t=buff]{border-left-color:var(--buff)}
.chg[data-t=nerf]{border-left-color:var(--nerf)}
.chg[data-t=rework]{border-left-color:var(--rework)}
.chg[data-t=bugfix]{border-left-color:var(--bugfix)}
.chg[data-t=new]{border-left-color:var(--new)}
.tag{display:inline-block;font-size:10.5px;font-weight:800;letter-spacing:.6px;
  text-transform:uppercase;padding:2px 7px;border-radius:4px;color:#0d1117;margin-right:8px;
  vertical-align:1px}
.tag.buff{background:var(--buff)}.tag.nerf{background:var(--nerf)}
.tag.rework{background:var(--rework)}.tag.bugfix{background:var(--bugfix)}
.tag.new{background:var(--new)}.tag.other{background:var(--other)}
.ctx{color:var(--muted);font-size:13px;font-style:italic;margin:0 0 5px;
  border-left:2px solid var(--line);padding-left:8px}
.txt{margin:0}
.subs{margin:6px 0 0 14px;padding:0;list-style:none}
.subs li{color:var(--muted);font-size:13.5px;margin:3px 0;position:relative;padding-left:12px}
.subs li:before{content:"\\2013";position:absolute;left:0}
.ba{margin-top:5px;font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums}
.ba b{color:var(--fg)}
.meta{font-size:11.5px;color:var(--other);margin-top:5px}
footer{margin-top:50px;border-top:1px solid var(--line);padding-top:14px;
  color:var(--muted);font-size:12.5px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th,td{text-align:left;padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:12px;margin:20px 0 34px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:14px 16px;
  text-decoration:none;color:inherit;display:block}
.card:hover{border-color:var(--accent)}
.card h3{margin:0 0 4px;font-size:16px}
.card p{margin:0 0 6px;color:var(--muted);font-size:12.5px}
.pill{display:inline-block;background:var(--panel2);border:1px solid var(--line);
  border-radius:999px;padding:1px 8px;font-size:11px;color:var(--muted);margin:2px 3px 0 0}
.scroll{overflow-x:auto}
"""

JS = """
(function(){
  var active={buff:1,nerf:1,rework:1,bugfix:1,new:1,other:1};
  function apply(){
    document.querySelectorAll('.chg').forEach(function(c){
      c.style.display = active[c.dataset.t] ? '' : 'none';
    });
    document.querySelectorAll('.patch').forEach(function(p){
      var any=[].some.call(p.querySelectorAll('.chg'),function(c){return c.style.display!=='none';});
      p.style.display = any ? '' : 'none';
    });
  }
  document.querySelectorAll('.filters button').forEach(function(b){
    b.addEventListener('click',function(){
      active[b.dataset.t]=!active[b.dataset.t];
      b.classList.toggle('on',!!active[b.dataset.t]);
      apply();
    });
  });
  var sel=document.getElementById('jump');
  if(sel) sel.addEventListener('change',function(){
    var el=document.getElementById(sel.value);
    if(el) el.scrollIntoView({behavior:'smooth',block:'start'});
  });
  apply();
})();
"""


def page(title, body):
    return ('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + e(title) + '</title><style>' + CSS + '</style></head><body>'
            '<div class="wrap">' + body + '</div></body></html>')


def render_change(c):
    t = c["change_type"]
    out = ['<div class="chg" data-t="' + t + '">']
    if c.get("context_line"):
        out.append('<p class="ctx">' + e(c["context_line"]) + '</p>')
    out.append('<p class="txt"><span class="tag ' + t + '">' + t + '</span>' + e(c["change_text"]) + '</p>')
    if c.get("sub_lines"):
        out.append('<ul class="subs">' + "".join('<li>' + e(s) + '</li>' for s in c["sub_lines"]) + '</ul>')
    if c.get("before_value"):
        out.append('<div class="ba">before <b>' + e(c["before_value"]) +
                   '</b> &rarr; after <b>' + e(c["after_value"]) + '</b></div>')
    meta = []
    if c.get("section"):
        meta.append("section: " + c["section"])
    if c.get("skill_or_mechanic_name"):
        meta.append("skill/mechanic: " + c["skill_or_mechanic_name"])
    if c.get("type_confidence") == "low":
        meta.append("tag confidence: low")
    if meta:
        out.append('<div class="meta">' + e(" · ".join(meta)) + '</div>')
    out.append('</div>')
    return "".join(out)


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "data", "patches", "*.json")))
    patches = [json.load(open(f, encoding="utf-8")) for f in files]
    patches.sort(key=lambda p: p["patch_date"])

    by_weapon = collections.defaultdict(list)
    for p in patches:
        for c in p["changes"]:
            by_weapon[c["weapon"]].append(c)
    for w in by_weapon:
        by_weapon[w].sort(key=lambda c: c["patch_date"])
    json.dump({w: by_weapon[w] for w in sorted(by_weapon)},
              open(os.path.join(ROOT, "data", "by_weapon.json"), "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)

    order = [w for w in WEAPONS if w in by_weapon] + sorted(set(by_weapon) - set(WEAPONS))
    stats = {}

    for w in order:
        cs = by_weapon[w]
        groups = collections.OrderedDict()
        for c in cs:
            groups.setdefault((c["patch_date"], c["patch_title"], c["source_url"]), []).append(c)
        counts = collections.Counter(c["change_type"] for c in cs)
        stats[w] = {"patches": len(groups), "changes": len(cs),
                    "first": cs[0]["patch_date"], "last": cs[-1]["patch_date"], "counts": counts}

        nav = "".join('<option value="p' + str(i) + '">' + e(d) + " — " + e(t) + '</option>'
                      for i, (d, t, _u) in enumerate(groups))
        filt = "".join('<button class="on" data-t="' + k + '">' + lbl +
                       ' <span style="opacity:.75">' + str(counts.get(k, 0)) + '</span></button>'
                       for k, lbl in TYPES)
        tl = []
        for i, ((d, t, u), cs2) in enumerate(groups.items()):
            tl.append('<section class="patch" id="p' + str(i) + '"><div class="phead">'
                      '<span class="pdate">' + e(d) + '</span>'
                      '<span class="ptitle">' + e(t) + '</span>'
                      '<a class="plink" href="' + e(u) + '" target="_blank" rel="noopener">source &#8599;</a></div>')
            tl += [render_change(c) for c in cs2]
            tl.append('</section>')

        body = ('<header><h1>' + e(w) + ' &mdash; balance history</h1>'
                '<div class="sum"><b>' + str(len(groups)) + '</b> patches &middot; <b>' +
                str(len(cs)) + '</b> recorded changes &middot; first <b>' + e(cs[0]["patch_date"]) +
                '</b> &middot; last <b>' + e(cs[-1]["patch_date"]) + '</b> &middot; oldest first</div></header>'
                '<div class="bar"><select id="jump"><option value="">Jump to patch&hellip;</option>' + nav + '</select>'
                '<div class="filters">' + filt + '</div></div>'
                '<div class="tl">' + "".join(tl) + '</div>'
                '<footer>Source: official Throne and Liberty patch notes (playthroneandliberty.com). '
                'Change text is quoted verbatim; the buff / nerf / rework / bugfix tag is inferred, not official. '
                '<a href="index.html">&larr; all weapons</a></footer>'
                '<script>' + JS + '</script>')
        open(os.path.join(OUT, slug(w) + ".html"), "w", encoding="utf-8").write(
            page(w + " — T&L balance history", body))

    processed = [p for p in patches if p["n_changes"]]
    skipped = [p for p in patches if not p["n_changes"]]
    excluded = json.load(open(os.path.join(ROOT, "data", "excluded.json"), encoding="utf-8"))

    cards = "".join(
        '<a class="card" href="' + slug(w) + '.html"><h3>' + e(w) + '</h3><p>' +
        str(stats[w]["changes"]) + ' changes across ' + str(stats[w]["patches"]) + ' patches<br>' +
        e(stats[w]["first"]) + ' &rarr; ' + e(stats[w]["last"]) + '</p>' +
        "".join('<span class="pill">' + k + ' ' + str(stats[w]["counts"].get(k, 0)) + '</span>'
                for k, _l in TYPES if stats[w]["counts"].get(k)) + '</a>'
        for w in order)

    rows = "".join(
        '<tr><td>' + e(p["patch_date"]) + '</td><td>' + e(p["patch_title"]) + '</td><td>' +
        str(p["n_changes"]) + '</td><td>' +
        e(", ".join(sorted({c["weapon"] for c in p["changes"]}))) + '</td><td><a href="' +
        e(p["source_url"]) + '" target="_blank" rel="noopener">link</a></td></tr>' for p in processed)
    srows = "".join(
        '<tr><td>' + e(p["patch_date"]) + '</td><td>' + e(p["patch_title"]) + '</td><td><a href="' +
        e(p["source_url"]) + '" target="_blank" rel="noopener">link</a></td></tr>' for p in skipped)
    erows = "".join(
        '<tr><td>' + e(x["date"]) + '</td><td>' + e(x["title"]) + '</td><td>' + e(x["reason"]) +
        '</td><td><a href="' + e(x["url"]) + '" target="_blank" rel="noopener">link</a></td></tr>'
        for x in excluded)

    total = sum(s["changes"] for s in stats.values())
    body = ('<header><h1>Throne and Liberty &mdash; weapon balance history</h1>'
            '<div class="sum">Every weapon change in the official patch notes from global launch '
            '(1 Oct 2024) to ' + e(patches[-1]["patch_date"]) + ' &middot; <b>' + str(len(processed)) +
            '</b> patches with weapon changes &middot; <b>' + str(total) +
            '</b> recorded changes &middot; <b>' + str(len(order)) + '</b> weapons</div></header>'
            '<div class="grid">' + cards + '</div>'
            '<h2>Patches with weapon changes (' + str(len(processed)) + ')</h2>'
            '<div class="scroll"><table><tr><th>Date</th><th>Patch</th><th>Changes</th>'
            '<th>Weapons</th><th>Source</th></tr>' + rows + '</table></div>'
            '<h2 style="margin-top:34px">Patch notes read, no weapon changes found (' + str(len(skipped)) + ')</h2>'
            '<div class="scroll"><table><tr><th>Date</th><th>Patch</th><th>Source</th></tr>' + srows + '</table></div>'
            '<h2 style="margin-top:34px">Articles excluded (' + str(len(excluded)) + ')</h2>'
            '<div class="scroll"><table><tr><th>Date</th><th>Article</th><th>Reason</th><th>Source</th></tr>' +
            erows + '</table></div>'
            '<footer>Built from playthroneandliberty.com/en-gb news articles plus the three '
            '/game/releases expansion pages. Weapon names normalised: Dagger(s)&rarr;Dagger, '
            'Crossbow(s)&rarr;Crossbow, Wand / Wand and Tome&rarr;Wand and Tome. '
            'Change text is verbatim from the notes; change-type tags are inferred.</footer>')
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(
        page("T&L weapon balance history", body))

    print("weapons:", len(order), " total changes:", total)
    for w in order:
        s = stats[w]
        print("  %-18s %4d changes / %2d patches  %s -> %s" % (w, s["changes"], s["patches"], s["first"], s["last"]))


if __name__ == "__main__":
    main()
