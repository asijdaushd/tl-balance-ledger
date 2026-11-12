"""Build one self-contained HTML page containing every weapon's balance history."""
import os, re, json, glob, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse import ROOT, WEAPONS

OUT = os.path.join(ROOT, "output", "solisium-balance-ledger.html")

TYPES = ["buff", "nerf", "rework", "bugfix", "new", "other"]
LABEL = {"buff": "Buff", "nerf": "Nerf", "rework": "Rework",
         "bugfix": "Bug fix", "new": "New", "other": "Other"}


def main():
    patches = [json.load(open(f, encoding="utf-8"))
               for f in sorted(glob.glob(os.path.join(ROOT, "data", "patches", "*.json")))]
    patches.sort(key=lambda p: p["patch_date"])
    excluded = json.load(open(os.path.join(ROOT, "data", "excluded.json"), encoding="utf-8"))

    by_weapon = collections.defaultdict(list)
    for p in patches:
        for c in p["changes"]:
            by_weapon[c["weapon"]].append(c)
    order = [w for w in WEAPONS if w in by_weapon] + sorted(set(by_weapon) - set(WEAPONS))

    weapons = []
    for w in order:
        cs = sorted(by_weapon[w], key=lambda c: c["patch_date"])
        groups = collections.OrderedDict()
        for c in cs:
            groups.setdefault((c["patch_date"], c["patch_title"], c["source_url"]), []).append(c)
        counts = collections.Counter(c["change_type"] for c in cs)
        weapons.append({
            "name": w,
            "id": re.sub(r"[^a-z0-9]+", "-", w.lower()).strip("-"),
            "changes": len(cs),
            "patches": len(groups),
            "first": cs[0]["patch_date"],
            "last": cs[-1]["patch_date"],
            "counts": {t: counts.get(t, 0) for t in TYPES},
            "groups": [{
                "date": d, "title": t, "url": u,
                "items": [{
                    "t": c["change_type"],
                    "lo": c.get("type_confidence") == "low",
                    "ctx": c.get("context_line"),
                    "txt": c["change_text"],
                    "sub": c.get("sub_lines") or [],
                    "b": c.get("before_value"), "a": c.get("after_value"),
                    "sec": c.get("section"), "sk": c.get("skill_or_mechanic_name"),
                } for c in cs2],
            } for (d, t, u), cs2 in groups.items()],
        })

    data = {
        "weapons": weapons,
        "processed": [{"date": p["patch_date"], "title": p["patch_title"], "url": p["source_url"],
                       "n": p["n_changes"],
                       "w": sorted({c["weapon"] for c in p["changes"]})}
                      for p in patches if p["n_changes"]],
        "silent": [{"date": p["patch_date"], "title": p["patch_title"], "url": p["source_url"]}
                   for p in patches if not p["n_changes"]],
        "excluded": excluded,
        "totals": {"changes": sum(w["changes"] for w in weapons),
                   "patches": sum(1 for p in patches if p["n_changes"]),
                   "read": len(patches),
                   "last": patches[-1]["patch_date"]},
    }

    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.replace("__DATA__", payload)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    print("wrote", OUT, round(os.path.getsize(OUT) / 1024), "KB")


TEMPLATE = r"""<title>Solisium Balance Ledger</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Zilla+Slab:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<style>
:root{
  --ground:#eceef2;
  --surface:#fbfcfd;
  --surface-2:#f2f4f7;
  --line:#d3d8e0;
  --line-soft:#e2e6ec;
  --ink:#161a21;
  --ink-2:#454d5a;
  --ink-3:#6d7684;
  --accent:#a9552a;
  --accent-ink:#8c451f;
  --buff:#1f7a45;
  --nerf:#b02a24;
  --rework:#94661a;
  --bugfix:#5c6674;
  --new:#2a5ba8;
  --other:#8a929e;
  --chip-ink:#ffffff;
  --shadow:0 1px 2px rgba(20,26,36,.06), 0 8px 24px -18px rgba(20,26,36,.5);
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --ground:#0f1319;
    --surface:#161b23;
    --surface-2:#1c222c;
    --line:#2b323d;
    --line-soft:#232935;
    --ink:#e7eaef;
    --ink-2:#aeb6c2;
    --ink-3:#7c8695;
    --accent:#d5854c;
    --accent-ink:#e9a271;
    --buff:#4bbd76;
    --nerf:#f2665c;
    --rework:#d9a441;
    --bugfix:#8d97a6;
    --new:#6aa6ff;
    --other:#7b8492;
    --chip-ink:#0f1319;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 30px -22px #000;
  }
}
:root[data-theme="dark"]{
  --ground:#0f1319;
  --surface:#161b23;
  --surface-2:#1c222c;
  --line:#2b323d;
  --line-soft:#232935;
  --ink:#e7eaef;
  --ink-2:#aeb6c2;
  --ink-3:#7c8695;
  --accent:#d5854c;
  --accent-ink:#e9a271;
  --buff:#4bbd76;
  --nerf:#f2665c;
  --rework:#d9a441;
  --bugfix:#8d97a6;
  --new:#6aa6ff;
  --other:#7b8492;
  --chip-ink:#0f1319;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 10px 30px -22px #000;
}

*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0;
  background:var(--ground);
  color:var(--ink);
  font-family:"IBM Plex Sans",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  font-size:15px;
  line-height:1.55;
}
h1,h2,h3{font-family:"Zilla Slab",Georgia,"Times New Roman",serif;font-weight:600;text-wrap:balance;margin:0}
a{color:var(--accent-ink);text-decoration-thickness:1px;text-underline-offset:2px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}
.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-variant-numeric:tabular-nums}

/* ---------- masthead ---------- */
.masthead{
  border-bottom:1px solid var(--line);
  background:var(--surface);
}
.mast-in{max-width:1320px;margin:0 auto;padding:22px 24px 18px;
  display:flex;flex-wrap:wrap;gap:18px 28px;align-items:flex-end;justify-content:space-between}
.brand h1{font-size:27px;letter-spacing:-.01em;line-height:1.15}
.brand .kicker{
  font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.16em;
  text-transform:uppercase;color:var(--accent-ink);margin-bottom:6px;display:block;
}
.brand p{margin:6px 0 0;color:var(--ink-3);font-size:13.5px;max-width:62ch}
.readout{display:flex;gap:26px;flex-wrap:wrap}
.readout div{min-width:74px}
.readout b{display:block;font-family:"IBM Plex Mono",monospace;font-size:23px;font-weight:600;
  line-height:1.1;font-variant-numeric:tabular-nums}
.readout span{font-size:10.5px;letter-spacing:.13em;text-transform:uppercase;color:var(--ink-3)}

/* ---------- shell ---------- */
.shell{max-width:1320px;margin:0 auto;padding:0 24px 90px;display:grid;
  grid-template-columns:250px minmax(0,1fr);gap:34px;align-items:start}
@media (max-width:900px){.shell{grid-template-columns:minmax(0,1fr);gap:18px;padding-bottom:60px}}

/* ---------- rail ---------- */
.rail{position:sticky;top:16px;padding-top:24px}
@media (max-width:900px){
  .rail{position:static;padding-top:16px;overflow-x:auto;scrollbar-width:thin}
  .rail-list{display:flex;flex-direction:row;gap:8px;min-width:min-content;padding-bottom:4px}
  .rail-btn{min-width:172px}
  .rail h2{margin-bottom:8px}
}
.rail h2{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink-3);
  font-family:"IBM Plex Mono",monospace;font-weight:500;margin:0 0 10px 2px}
.rail-list{display:flex;flex-direction:column;gap:3px;list-style:none;margin:0 0 20px;padding:0}
.rail-btn{
  width:100%;text-align:left;background:transparent;border:1px solid transparent;
  border-radius:7px;padding:8px 10px;cursor:pointer;color:var(--ink-2);
  font:inherit;display:block;transition:background .12s,border-color .12s,color .12s;
}
.rail-btn:hover{background:var(--surface-2);color:var(--ink)}
.rail-btn[aria-current="true"]{background:var(--surface);border-color:var(--line);color:var(--ink);
  box-shadow:var(--shadow)}
.rail-btn .rb-top{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.rail-btn .rb-name{font-weight:500;font-size:14px}
.rail-btn .rb-n{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink-3);
  font-variant-numeric:tabular-nums}
.spark{display:flex;height:4px;border-radius:2px;overflow:hidden;margin-top:7px;background:var(--line-soft)}
.spark i{display:block;height:100%}

/* ---------- panes ---------- */
.pane{padding-top:24px;min-width:0}
.pane[hidden]{display:none}
.pane-head{margin-bottom:18px}
.pane-head h2{font-size:24px;letter-spacing:-.01em}
.pane-sub{color:var(--ink-3);font-size:13px;margin-top:5px;display:flex;flex-wrap:wrap;gap:4px 14px}
.pane-sub b{color:var(--ink-2);font-weight:600}

/* controls */
.controls{
  position:sticky;top:0;z-index:9;background:var(--ground);
  padding:12px 0 12px;margin-bottom:6px;
  border-bottom:1px solid var(--line-soft);
  display:flex;flex-wrap:wrap;gap:9px;align-items:center;
}
.field{position:relative;flex:1 1 210px;min-width:170px;max-width:330px}
input[type=search],select{
  width:100%;background:var(--surface);color:var(--ink);border:1px solid var(--line);
  border-radius:7px;padding:7px 10px;font:inherit;font-size:13px;
}
input[type=search]::placeholder{color:var(--ink-3)}
select{max-width:290px;flex:0 1 290px;font-family:"IBM Plex Mono",monospace;font-size:12px}
.filters{display:flex;flex-wrap:wrap;gap:5px}
.fbtn{
  font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.05em;font-weight:500;
  background:var(--surface);color:var(--ink-3);border:1px solid var(--line);
  border-radius:999px;padding:4px 10px;cursor:pointer;display:inline-flex;gap:6px;align-items:center;
}
.fbtn .dot{width:7px;height:7px;border-radius:2px;background:currentColor;opacity:.45}
.fbtn[aria-pressed="true"]{color:var(--chip-ink);border-color:transparent}
.fbtn[aria-pressed="true"] .dot{opacity:1;background:var(--chip-ink)}
.fbtn[data-t=buff][aria-pressed="true"]{background:var(--buff)}
.fbtn[data-t=nerf][aria-pressed="true"]{background:var(--nerf)}
.fbtn[data-t=rework][aria-pressed="true"]{background:var(--rework)}
.fbtn[data-t=bugfix][aria-pressed="true"]{background:var(--bugfix)}
.fbtn[data-t=new][aria-pressed="true"]{background:var(--new)}
.fbtn[data-t=other][aria-pressed="true"]{background:var(--other)}
.fbtn:not([aria-pressed="true"]) .dot{background:var(--ink-3)}

/* timeline */
.tl{position:relative;padding-left:23px;margin-top:14px}
.tl::before{content:"";position:absolute;left:5px;top:10px;bottom:8px;width:1px;background:var(--line)}
.patch{position:relative;margin-bottom:26px;scroll-margin-top:78px}
.patch::before{content:"";position:absolute;left:-22px;top:9px;width:9px;height:9px;border-radius:50%;
  background:var(--accent);box-shadow:0 0 0 3px var(--ground)}
.phead{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 12px;margin-bottom:9px}
.phead .pdate{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink-3);
  font-variant-numeric:tabular-nums}
.phead h3{font-size:17.5px}
.phead a{font-size:11.5px;font-family:"IBM Plex Mono",monospace}

.chg{
  background:var(--surface);border:1px solid var(--line-soft);border-left:2px solid var(--other);
  border-radius:0 8px 8px 0;padding:11px 14px;margin-bottom:7px;box-shadow:var(--shadow);
}
.chg[data-t=buff]{border-left-color:var(--buff)}
.chg[data-t=nerf]{border-left-color:var(--nerf)}
.chg[data-t=rework]{border-left-color:var(--rework)}
.chg[data-t=bugfix]{border-left-color:var(--bugfix)}
.chg[data-t=new]{border-left-color:var(--new)}
.chg[hidden]{display:none}
.tag{
  font-family:"IBM Plex Mono",monospace;font-size:10px;font-weight:600;letter-spacing:.09em;
  text-transform:uppercase;padding:2px 6px;border-radius:3px;color:var(--chip-ink);
  margin-right:8px;white-space:nowrap;
}
.tag.buff{background:var(--buff)}.tag.nerf{background:var(--nerf)}
.tag.rework{background:var(--rework)}.tag.bugfix{background:var(--bugfix)}
.tag.new{background:var(--new)}.tag.other{background:var(--other)}
.ctx{margin:0 0 7px;padding-left:9px;border-left:2px solid var(--line);
  color:var(--ink-3);font-size:12.5px;font-style:italic;max-width:78ch}
.txt{margin:0;max-width:78ch}
.subs{list-style:none;margin:7px 0 0;padding:0 0 0 15px;display:flex;flex-direction:column;gap:3px}
.subs li{position:relative;color:var(--ink-2);font-size:13.5px;padding-left:12px;max-width:76ch}
.subs li::before{content:"";position:absolute;left:0;top:.65em;width:6px;height:1px;background:var(--ink-3)}
.ba{margin-top:7px;display:inline-flex;gap:8px;align-items:center;
  font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink-3);
  background:var(--surface-2);border:1px solid var(--line-soft);border-radius:5px;padding:2px 8px}
.ba b{color:var(--ink);font-weight:600}
.meta{margin-top:7px;font-size:11px;color:var(--ink-3);
  font-family:"IBM Plex Mono",monospace;display:flex;flex-wrap:wrap;gap:4px 12px}
.meta .warn{color:var(--rework)}

/* overview */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:11px;margin:6px 0 34px}
.card{
  background:var(--surface);border:1px solid var(--line);border-radius:9px;padding:14px 15px;
  text-align:left;cursor:pointer;font:inherit;color:inherit;box-shadow:var(--shadow);
  transition:border-color .12s,transform .12s;
}
.card:hover{border-color:var(--accent);transform:translateY(-1px)}
.card h3{font-size:16.5px;margin-bottom:2px}
.card .cnum{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--ink-3);
  font-variant-numeric:tabular-nums;display:block;margin-bottom:9px}
.sec{margin:0 0 30px}
.sec > h3{font-size:18px;margin-bottom:3px}
.sec > p{margin:0 0 12px;color:var(--ink-3);font-size:13px;max-width:74ch}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:9px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13px;min-width:520px}
th,td{text-align:left;padding:7px 12px;border-bottom:1px solid var(--line-soft);vertical-align:top}
tr:last-child td{border-bottom:0}
th{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ink-3);font-weight:500;background:var(--surface-2);position:sticky;top:0}
td.n,td.d{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums;white-space:nowrap}
td.w{color:var(--ink-3);font-size:12.5px}

.note{
  border:1px solid var(--line);border-left:2px solid var(--accent);background:var(--surface);
  border-radius:0 9px 9px 0;padding:13px 16px;margin:0 0 30px;box-shadow:var(--shadow);
}
.note h3{font-size:15px;margin-bottom:5px}
.note p{margin:0 0 7px;font-size:13.5px;color:var(--ink-2);max-width:76ch}
.note p:last-child{margin-bottom:0}
.empty{color:var(--ink-3);font-size:14px;padding:26px 0;text-align:center;
  font-family:"IBM Plex Mono",monospace}
footer{border-top:1px solid var(--line);margin-top:16px;padding-top:14px;color:var(--ink-3);font-size:12px;
  max-width:80ch}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
</style>

<header class="masthead">
  <div class="mast-in">
    <div class="brand">
      <span class="kicker">Throne and Liberty &middot; Weapon balance archive</span>
      <h1>Solisium Balance Ledger</h1>
      <p>Every weapon change in the official patch notes, from global launch on 1 October 2024 onward. Change text is quoted verbatim from the notes.</p>
    </div>
    <div class="readout">
      <div><b id="rd-changes">&mdash;</b><span>Changes</span></div>
      <div><b id="rd-patches">&mdash;</b><span>Patches</span></div>
      <div><b id="rd-weapons">&mdash;</b><span>Weapons</span></div>
      <div><b id="rd-last">&mdash;</b><span>Latest</span></div>
    </div>
  </div>
</header>

<div class="shell">
  <nav class="rail" aria-label="Weapons">
    <h2>Index</h2>
    <ul class="rail-list" id="rail"></ul>
  </nav>
  <main class="pane-wrap">
    <section class="pane" id="pane-overview"></section>
    <section class="pane" id="pane-weapon" hidden></section>
  </main>
</div>

<script type="application/json" id="ledger">__DATA__</script>
<script>
(function(){
  "use strict";
  var D = JSON.parse(document.getElementById("ledger").textContent);
  var TYPES = ["buff","nerf","rework","bugfix","new","other"];
  var LABEL = {buff:"Buff",nerf:"Nerf",rework:"Rework",bugfix:"Bug fix",new:"New",other:"Other"};
  var esc = function(s){
    return String(s == null ? "" : s).replace(/[&<>"]/g, function(c){
      return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];
    });
  };
  var byId = {};
  D.weapons.forEach(function(w){ byId[w.id] = w; });

  document.getElementById("rd-changes").textContent = D.totals.changes;
  document.getElementById("rd-patches").textContent = D.totals.patches;
  document.getElementById("rd-weapons").textContent = D.weapons.length;
  document.getElementById("rd-last").textContent = D.totals.last;

  /* ---------- rail ---------- */
  var rail = document.getElementById("rail");
  var railHTML = '<li><button class="rail-btn" data-view="overview">' +
    '<span class="rb-top"><span class="rb-name">Overview</span>' +
    '<span class="rb-n">' + D.totals.patches + ' patches</span></span></button></li>';
  D.weapons.forEach(function(w){
    var bar = TYPES.map(function(t){
      var pct = w.counts[t] / w.changes * 100;
      return pct ? '<i style="width:' + pct.toFixed(2) + '%;background:var(--' + t + ')"></i>' : "";
    }).join("");
    railHTML += '<li><button class="rail-btn" data-view="' + w.id + '">' +
      '<span class="rb-top"><span class="rb-name">' + esc(w.name) + '</span>' +
      '<span class="rb-n">' + w.changes + '</span></span>' +
      '<span class="spark" aria-hidden="true">' + bar + '</span></button></li>';
  });
  rail.innerHTML = railHTML;

  /* ---------- overview ---------- */
  function tableRows(list, kind){
    return list.map(function(p){
      if (kind === "processed")
        return '<tr><td class="d">' + esc(p.date) + '</td><td>' + esc(p.title) + '</td>' +
          '<td class="n">' + p.n + '</td><td class="w">' + esc(p.w.join(", ")) + '</td>' +
          '<td><a href="' + esc(p.url) + '" target="_blank" rel="noopener">notes</a></td></tr>';
      if (kind === "silent")
        return '<tr><td class="d">' + esc(p.date) + '</td><td>' + esc(p.title) + '</td>' +
          '<td><a href="' + esc(p.url) + '" target="_blank" rel="noopener">notes</a></td></tr>';
      return '<tr><td class="d">' + esc(p.date) + '</td><td>' + esc(p.title) + '</td>' +
        '<td class="w">' + esc(p.reason) + '</td>' +
        '<td><a href="' + esc(p.url) + '" target="_blank" rel="noopener">article</a></td></tr>';
    }).join("");
  }

  document.getElementById("pane-overview").innerHTML =
    '<div class="pane-head"><h2>Overview</h2><div class="pane-sub">' +
      '<span><b>' + D.totals.read + '</b> patch-note articles read</span>' +
      '<span><b>' + D.totals.patches + '</b> carried weapon changes</span>' +
      '<span><b>' + D.totals.changes + '</b> individual changes recorded</span>' +
    '</div></div>' +
    '<div class="grid">' + D.weapons.map(function(w){
      return '<button class="card" data-view="' + w.id + '"><h3>' + esc(w.name) + '</h3>' +
        '<span class="cnum">' + w.changes + ' changes &middot; ' + w.patches + ' patches<br>' +
        esc(w.first) + ' &rarr; ' + esc(w.last) + '</span>' +
        '<span class="spark">' + TYPES.map(function(t){
          var pct = w.counts[t] / w.changes * 100;
          return pct ? '<i style="width:' + pct.toFixed(2) + '%;background:var(--' + t + ')"></i>' : "";
        }).join("") + '</span></button>';
    }).join("") + '</div>' +
    '<div class="note"><h3>How to read this</h3>' +
      '<p>The wording of every change is copied verbatim from the patch notes &mdash; numbers and skill names are untouched. Where the change was stated in a lead-in line above a list, that line appears in italics above the entry.</p>' +
      '<p>The buff / nerf / rework / bug&nbsp;fix label is <em>inferred</em>, not official &mdash; Amazon Games does not tag its notes. Entries the classifier was unsure about are labelled <em>Other</em> or carry a &ldquo;low confidence&rdquo; note. Before and after values appear only where the notes literally wrote them.</p>' +
      '<p>Weapon names are normalised across eras: Daggers&rarr;Dagger, Crossbows&rarr;Crossbow, Wand&rarr;Wand and Tome.</p></div>' +
    '<div class="sec"><h3>Patches carrying weapon changes</h3>' +
      '<p>' + D.processed.length + ' of the ' + D.totals.read + ' patch-note articles read.</p>' +
      '<div class="scroll"><table><thead><tr><th>Date</th><th>Patch</th><th>Changes</th><th>Weapons</th><th>Source</th></tr></thead>' +
      '<tbody>' + tableRows(D.processed, "processed") + '</tbody></table></div></div>' +
    '<div class="sec"><h3>Patch notes read, no weapon changes found</h3>' +
      '<p>Logged rather than dropped, so the coverage gap is visible.</p>' +
      '<div class="scroll"><table><thead><tr><th>Date</th><th>Patch</th><th>Source</th></tr></thead>' +
      '<tbody>' + tableRows(D.silent, "silent") + '</tbody></table></div></div>' +
    '<div class="sec"><h3>Articles excluded</h3>' +
      '<p>Announcements, dev letters and event posts &mdash; not patch notes.</p>' +
      '<div class="scroll"><table><thead><tr><th>Date</th><th>Article</th><th>Reason</th><th>Source</th></tr></thead>' +
      '<tbody>' + tableRows(D.excluded, "excluded") + '</tbody></table></div></div>' +
    '<footer>Sourced from playthroneandliberty.com news articles plus the three /game/releases expansion pages, which hold the real notes for Call of the Spear, Wilds of Talandre and Solisium&rsquo;s Awakening.</footer>';

  /* ---------- weapon pane ---------- */
  var pane = document.getElementById("pane-weapon");
  var current = null;

  function renderWeapon(w){
    current = w;
    var jump = w.groups.map(function(g,i){
      return '<option value="pt' + i + '">' + esc(g.date) + "  " + esc(g.title) + '</option>';
    }).join("");
    var filters = TYPES.map(function(t){
      return '<button class="fbtn" data-t="' + t + '" aria-pressed="true">' +
        '<span class="dot"></span>' + LABEL[t] + " " + w.counts[t] + '</button>';
    }).join("");
    var body = w.groups.map(function(g,i){
      return '<article class="patch" id="pt' + i + '"><div class="phead">' +
        '<span class="pdate">' + esc(g.date) + '</span><h3>' + esc(g.title) + '</h3>' +
        '<a href="' + esc(g.url) + '" target="_blank" rel="noopener">source &#8599;</a></div>' +
        g.items.map(function(c){
          var s = '<div class="chg" data-t="' + c.t + '">';
          if (c.ctx) s += '<p class="ctx">' + esc(c.ctx) + '</p>';
          s += '<p class="txt"><span class="tag ' + c.t + '">' + c.t + '</span>' + esc(c.txt) + '</p>';
          if (c.sub && c.sub.length)
            s += '<ul class="subs">' + c.sub.map(function(x){ return '<li>' + esc(x) + '</li>'; }).join("") + '</ul>';
          if (c.b) s += '<div class="ba">' + esc(c.b) + ' <span>&rarr;</span> <b>' + esc(c.a) + '</b></div>';
          var meta = [];
          if (c.sk) meta.push('<span>' + esc(c.sk) + '</span>');
          if (c.sec) meta.push('<span>in &ldquo;' + esc(c.sec) + '&rdquo;</span>');
          if (c.lo) meta.push('<span class="warn">label uncertain</span>');
          if (meta.length) s += '<div class="meta">' + meta.join("") + '</div>';
          return s + '</div>';
        }).join("") + '</article>';
    }).join("");

    pane.innerHTML =
      '<div class="pane-head"><h2>' + esc(w.name) + '</h2><div class="pane-sub">' +
        '<span><b>' + w.changes + '</b> changes</span><span><b>' + w.patches + '</b> patches</span>' +
        '<span>first <b>' + esc(w.first) + '</b></span><span>latest <b>' + esc(w.last) + '</b></span>' +
        '<span>oldest first</span></div></div>' +
      '<div class="controls">' +
        '<div class="field"><input type="search" id="q" placeholder="Search skills or wording…" autocomplete="off"></div>' +
        '<select id="jump"><option value="">Jump to patch…</option>' + jump + '</select>' +
        '<div class="filters">' + filters + '</div>' +
      '</div>' +
      '<div class="tl" id="tl">' + body + '</div>' +
      '<p class="empty" id="none" hidden>Nothing matches those filters.</p>' +
      '<footer>Change text verbatim from the official notes; buff / nerf / rework / bug fix labels are inferred.</footer>';

    wire();
    apply();
  }

  var active = {}, query = "";
  TYPES.forEach(function(t){ active[t] = true; });

  function apply(){
    var q = query.trim().toLowerCase(), shown = 0;
    pane.querySelectorAll(".patch").forEach(function(p){
      var any = false;
      p.querySelectorAll(".chg").forEach(function(c){
        var ok = active[c.dataset.t] && (!q || c.textContent.toLowerCase().indexOf(q) !== -1);
        c.hidden = !ok;
        if (ok) { any = true; shown++; }
      });
      p.hidden = !any;
    });
    document.getElementById("none").hidden = shown > 0;
  }

  function wire(){
    pane.querySelectorAll(".fbtn").forEach(function(b){
      b.setAttribute("aria-pressed", String(active[b.dataset.t]));
      b.addEventListener("click", function(){
        active[b.dataset.t] = !active[b.dataset.t];
        b.setAttribute("aria-pressed", String(active[b.dataset.t]));
        apply();
      });
    });
    var q = document.getElementById("q");
    q.value = query;
    q.addEventListener("input", function(){ query = q.value; apply(); });
    document.getElementById("jump").addEventListener("change", function(e){
      var el = e.target.value && document.getElementById(e.target.value);
      if (el) el.scrollIntoView({behavior:"smooth", block:"start"});
    });
  }

  /* ---------- routing ---------- */
  function show(view, push){
    var isW = !!byId[view];
    document.getElementById("pane-overview").hidden = isW;
    pane.hidden = !isW;
    if (isW && (!current || current.id !== view)) renderWeapon(byId[view]);
    rail.querySelectorAll(".rail-btn").forEach(function(b){
      b.setAttribute("aria-current", String(b.dataset.view === (isW ? view : "overview")));
    });
    if (push) history.replaceState(null, "", isW ? "#" + view : "#overview");
    window.scrollTo({top:0, behavior: push ? "smooth" : "auto"});
  }

  document.addEventListener("click", function(e){
    var b = e.target.closest("[data-view]");
    if (b) show(b.dataset.view, true);
  });
  window.addEventListener("hashchange", function(){ show(location.hash.slice(1) || "overview", false); });
  show(location.hash.slice(1) || "overview", false);
})();
</script>
"""

if __name__ == "__main__":
    main()
