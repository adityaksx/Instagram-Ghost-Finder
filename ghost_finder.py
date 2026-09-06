#!/usr/bin/env python3
"""
Instagram Ghost Finder — HTML Report Generator
===============================================
Parses your Instagram data export and generates a beautiful
interactive HTML report showing followers, mutuals, and ghosts.

Usage:
    python ghost_finder.py
    python ghost_finder.py --followers followers_1.json --following following.json
    python ghost_finder.py --output report.html
"""

import json
import argparse
import os
import sys
from datetime import datetime


# ── Parsers ────────────────────────────────────────────────────────────────

def load_followers(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for item in data:
        for entry in item.get("string_list_data", []):
            u = entry.get("value", "").strip()
            if u:
                out[u.lower()] = {
                    "username": u,
                    "href": entry.get("href", f"https://www.instagram.com/{u}"),
                    "timestamp": entry.get("timestamp", 0),
                }
    return out


def load_following(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    out = {}
    for item in data.get("relationships_following", []):
        u = item.get("title", "").strip()
        if u:
            ts = (item.get("string_list_data") or [{}])[0].get("timestamp", 0)
            out[u.lower()] = {
                "username": u,
                "href": f"https://www.instagram.com/{u}",
                "timestamp": ts,
            }
    return out


def fmt_date(ts):
    if not ts:
        return ""
    return datetime.fromtimestamp(ts).strftime("%d %b %Y")


# ── HTML generator ──────────────────────────────────────────────────────────

def build_html(followers: dict, following: dict, output_path: str):
    follower_set  = set(followers.keys())
    following_set = set(following.keys())

    ghosts_keys  = following_set - follower_set          # you follow, they don't
    mutual_keys  = following_set & follower_set           # both follow each other
    fans_keys    = follower_set - following_set           # they follow, you don't

    def make_list(keys, source_dict, sort_ts=True):
        items = [source_dict[k] for k in keys if k in source_dict]
        if sort_ts:
            items.sort(key=lambda x: x["timestamp"], reverse=True)
        else:
            items.sort(key=lambda x: x["username"].lower())
        return items

    ghosts  = make_list(ghosts_keys,  following)
    mutuals = make_list(mutual_keys,  following)
    fans    = make_list(fans_keys,    followers)

    def js_array(lst):
        rows = []
        for u in lst:
            rows.append(
                f'{{"u":{json.dumps(u["username"])},"h":{json.dumps(u["href"])},"d":{json.dumps(fmt_date(u["timestamp"]))}}}'
            )
        return "[" + ",".join(rows) + "]"

    generated = datetime.now().strftime("%d %b %Y, %I:%M %p")

    html = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Instagram Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300..700&family=Syne:wght@700;800&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#0d0d0f;--surface:#141417;--surface2:#1b1b1f;--surface3:#222228;
  --border:rgba(255,255,255,0.07);--border-hover:rgba(255,255,255,0.15);
  --text:#eeedf5;--muted:#7e7d8f;--faint:#3e3d4a;
  --purple:#a855f7;--purple-dim:rgba(168,85,247,0.15);--purple-glow:rgba(168,85,247,0.08);
  --pink:#ec4899;--green:#34d399;--yellow:#fbbf24;--blue:#60a5fa;
  --radius-sm:6px;--radius-md:10px;--radius-lg:16px;--radius-xl:22px;
  --font-display:'Syne',sans-serif;--font-body:'Inter',sans-serif;
}}
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{-webkit-font-smoothing:antialiased;scroll-behavior:smooth}}
body{{min-height:100dvh;font-family:var(--font-body);font-size:15px;
  color:var(--text);background:var(--bg);line-height:1.6;}}

/* ambient glow */
body::before{{content:'';position:fixed;top:-300px;left:50%;transform:translateX(-50%);
  width:900px;height:600px;
  background:radial-gradient(ellipse,rgba(168,85,247,0.07) 0%,transparent 70%);
  pointer-events:none;z-index:0}}

.wrap{{max-width:1100px;margin:0 auto;padding:0 20px;position:relative;z-index:1}}

/* ── Header ── */
header{{padding:36px 0 28px;border-bottom:1px solid var(--border)}}
.hrow{{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}}
.logo{{display:flex;align-items:center;gap:12px}}
.logo-icon{{width:42px;height:42px;border-radius:12px;
  background:linear-gradient(135deg,var(--purple),var(--pink));
  display:flex;align-items:center;justify-content:center;flex-shrink:0}}
.logo-icon svg{{width:22px;height:22px;color:#fff}}
.logo-text h1{{font-family:var(--font-display);font-size:21px;font-weight:800;
  letter-spacing:-0.3px;line-height:1.1}}
.logo-text p{{font-size:12px;color:var(--muted);margin-top:2px}}
.gen-date{{font-size:12px;color:var(--faint)}}

/* ── Stats ── */
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:14px;padding:28px 0 24px}}
.stat{{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-lg);padding:18px 20px;position:relative;overflow:hidden;
  transition:border-color .2s,transform .2s}}
.stat:hover{{border-color:var(--border-hover);transform:translateY(-2px)}}
.stat.hi{{border-color:rgba(168,85,247,.3);
  background:linear-gradient(135deg,rgba(168,85,247,.07),var(--surface))}}
.stat.hi::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--purple),var(--pink))}}
.stat-lbl{{font-size:11px;color:var(--muted);text-transform:uppercase;
  letter-spacing:.6px;margin-bottom:4px}}
.stat-val{{font-family:var(--font-display);font-size:34px;font-weight:800;line-height:1}}
.c-purple{{color:var(--purple)}} .c-green{{color:var(--green)}}
.c-yellow{{color:var(--yellow)}} .c-blue{{color:var(--blue)}}

/* ── Tabs ── */
.tabs{{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0 20px}}
.tab{{padding:9px 18px;border-radius:var(--radius-md);border:1px solid var(--border);
  background:var(--surface);font-size:13px;font-weight:600;color:var(--muted);
  cursor:pointer;transition:all .18s;user-select:none}}
.tab:hover{{border-color:var(--border-hover);color:var(--text)}}
.tab.active{{background:var(--purple-dim);border-color:rgba(168,85,247,.4);color:var(--purple)}}
.tab .cnt{{display:inline-block;background:rgba(255,255,255,.06);
  border-radius:999px;padding:1px 8px;font-size:11px;margin-left:6px;
  font-weight:700;color:var(--muted)}}
.tab.active .cnt{{background:rgba(168,85,247,.2);color:var(--purple)}}

/* ── Controls ── */
.controls{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}}
.search-wrap{{flex:1;min-width:200px;position:relative}}
.search-wrap svg{{position:absolute;left:11px;top:50%;transform:translateY(-50%);
  color:var(--faint);width:15px;height:15px;pointer-events:none}}
.search-input{{width:100%;background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-md);padding:9px 12px 9px 34px;color:var(--text);
  font-size:13px;outline:none;transition:border-color .18s;font-family:var(--font-body)}}
.search-input:focus{{border-color:rgba(168,85,247,.5)}}
.search-input::placeholder{{color:var(--faint)}}
.sort-sel{{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-md);padding:9px 14px;color:var(--text);
  font-size:13px;outline:none;cursor:pointer;font-family:var(--font-body);
  transition:border-color .18s}}
.sort-sel:focus{{border-color:rgba(168,85,247,.5)}}
.res-label{{font-size:12px;color:var(--muted);margin-bottom:14px}}
.res-label span{{color:var(--purple);font-weight:600}}

/* ── Grid ── */
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}}

/* ── Card ── */
.card{{background:var(--surface);border:1px solid var(--border);
  border-radius:var(--radius-lg);padding:16px;
  display:flex;flex-direction:column;align-items:center;gap:10px;
  text-decoration:none;color:inherit;
  transition:border-color .18s,background .18s,transform .18s;
  text-align:center}}
.card:hover{{border-color:rgba(168,85,247,.4);background:var(--surface2);
  transform:translateY(-2px)}}

/* pfp */
.pfp{{width:54px;height:54px;border-radius:50%;position:relative;flex-shrink:0}}
.pfp-img{{width:54px;height:54px;border-radius:50%;object-fit:cover;
  display:block;border:2px solid var(--border)}}
.pfp-fallback{{width:54px;height:54px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-family:var(--font-display);font-size:20px;font-weight:800;
  color:#fff;border:2px solid transparent}}
.pfp-ring{{position:absolute;inset:-3px;border-radius:50%;
  background:linear-gradient(135deg,var(--purple),var(--pink));
  z-index:-1;opacity:0;transition:opacity .18s}}
.card:hover .pfp-ring{{opacity:1}}

.card-uname{{font-size:13px;font-weight:600;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  width:100%;max-width:160px}}
.card-date{{font-size:11px;color:var(--muted)}}
.card-link{{font-size:11px;color:var(--faint);
  display:flex;align-items:center;gap:4px;transition:color .15s}}
.card:hover .card-link{{color:var(--purple)}}
.card-link svg{{width:11px;height:11px}}

/* badge on ghost cards */
.ghost-badge{{position:absolute;top:10px;right:10px;
  background:rgba(168,85,247,.18);color:var(--purple);
  border-radius:999px;font-size:10px;font-weight:700;
  padding:2px 7px;border:1px solid rgba(168,85,247,.3)}}

/* section hidden */
.section{{display:none}}.section.active{{display:block}}

/* empty */
.empty{{text-align:center;padding:60px 20px;color:var(--muted);display:none}}
.empty.show{{display:block}}
.empty-icon{{font-size:44px;margin-bottom:12px}}
.empty h3{{font-size:16px;color:var(--text);margin-bottom:6px}}

footer{{margin-top:60px;padding:28px 0;border-top:1px solid var(--border);
  text-align:center;font-size:12px;color:var(--faint)}}

@media(max-width:600px){{
  .stats{{grid-template-columns:repeat(2,1fr)}}
  .grid{{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}}
}}
</style>
</head>
<body>

<header>
<div class="wrap">
  <div class="hrow">
    <div class="logo">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
          <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
          <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
        </svg>
      </div>
      <div class="logo-text">
        <h1>Instagram Report</h1>
        <p>Followers · Mutuals · Ghosts</p>
      </div>
    </div>
    <div class="gen-date">Generated {generated}</div>
  </div>
</div>
</header>

<main>
<div class="wrap">

  <div class="stats">
    <div class="stat">
      <div class="stat-lbl">Following</div>
      <div class="stat-val">{len(following)}</div>
    </div>
    <div class="stat">
      <div class="stat-lbl">Followers</div>
      <div class="stat-val c-blue">{len(followers)}</div>
    </div>
    <div class="stat">
      <div class="stat-lbl">Mutuals</div>
      <div class="stat-val c-green">{len(mutuals)}</div>
    </div>
    <div class="stat">
      <div class="stat-lbl">Fans (not following)</div>
      <div class="stat-val c-yellow">{len(fans)}</div>
    </div>
    <div class="stat hi">
      <div class="stat-lbl">👻 Not Following Back</div>
      <div class="stat-val c-purple">{len(ghosts)}</div>
    </div>
  </div>

  <div class="tabs">
    <div class="tab active" data-tab="ghosts">👻 Not Following Back <span class="cnt">{len(ghosts)}</span></div>
    <div class="tab" data-tab="mutuals">🤝 Mutuals <span class="cnt">{len(mutuals)}</span></div>
    <div class="tab" data-tab="fans">🙋 Fans <span class="cnt">{len(fans)}</span></div>
  </div>

  <!-- Ghosts -->
  <div class="section active" id="sec-ghosts">
    <div class="controls">
      <div class="search-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input class="search-input" id="gs-search" placeholder="Search…" autocomplete="off">
      </div>
      <select class="sort-sel" id="gs-sort">
        <option value="newest">Newest First</option>
        <option value="oldest">Oldest First</option>
        <option value="az">A → Z</option>
        <option value="za">Z → A</option>
      </select>
    </div>
    <div class="res-label">Showing <span id="gs-count">{len(ghosts)}</span> accounts</div>
    <div class="grid" id="gs-grid"></div>
    <div class="empty" id="gs-empty"><div class="empty-icon">🔍</div><h3>No results</h3><p>Try a different search</p></div>
  </div>

  <!-- Mutuals -->
  <div class="section" id="sec-mutuals">
    <div class="controls">
      <div class="search-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input class="search-input" id="mu-search" placeholder="Search…" autocomplete="off">
      </div>
      <select class="sort-sel" id="mu-sort">
        <option value="newest">Newest First</option>
        <option value="oldest">Oldest First</option>
        <option value="az">A → Z</option>
        <option value="za">Z → A</option>
      </select>
    </div>
    <div class="res-label">Showing <span id="mu-count">{len(mutuals)}</span> accounts</div>
    <div class="grid" id="mu-grid"></div>
    <div class="empty" id="mu-empty"><div class="empty-icon">🔍</div><h3>No results</h3><p>Try a different search</p></div>
  </div>

  <!-- Fans -->
  <div class="section" id="sec-fans">
    <div class="controls">
      <div class="search-wrap">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input class="search-input" id="fa-search" placeholder="Search…" autocomplete="off">
      </div>
      <select class="sort-sel" id="fa-sort">
        <option value="newest">Newest First</option>
        <option value="oldest">Oldest First</option>
        <option value="az">A → Z</option>
        <option value="za">Z → A</option>
      </select>
    </div>
    <div class="res-label">Showing <span id="fa-count">{len(fans)}</span> accounts</div>
    <div class="grid" id="fa-grid"></div>
    <div class="empty" id="fa-empty"><div class="empty-icon">🔍</div><h3>No results</h3><p>Try a different search</p></div>
  </div>

</div>
</main>

<footer><div class="wrap">Data from Instagram export &middot; {generated}</div></footer>

<script>
const GHOSTS  = {js_array(ghosts)};
const MUTUALS = {js_array(mutuals)};
const FANS    = {js_array(fans)};

// Deterministic gradient per username
function hue(s){{let h=0;for(let i=0;i<s.length;i++)h=(h*31+s.charCodeAt(i))%360;return h}}
function gradient(u){{const h=hue(u);return`linear-gradient(135deg,hsl(${{h}},65%,48%),hsl(${{(h+50)%360}},72%,58%))`}}

// PFP: try to load real IG pic via unavatar, fallback to initials
function pfpHtml(u){{
  const g = gradient(u);
  const initial = u.charAt(0).toUpperCase();
  const avatarUrl = `https://unavatar.io/instagram/${{u}}?fallback=false`;
  return `
    <div class="pfp">
      <div class="pfp-ring"></div>
      <img class="pfp-img" src="${{avatarUrl}}"
           onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
           alt="@${{u}}" loading="lazy" width="54" height="54">
      <div class="pfp-fallback" style="background:${{g}};display:none">${{initial}}</div>
    </div>`;
}}

function renderGrid(data, gridId, countId, emptyId){{
  const grid  = document.getElementById(gridId);
  const cnt   = document.getElementById(countId);
  const empty = document.getElementById(emptyId);
  cnt.textContent = data.length;
  if(!data.length){{ grid.innerHTML=''; empty.classList.add('show'); return; }}
  empty.classList.remove('show');
  const isGhost = gridId==='gs-grid';
  grid.innerHTML = data.map(x=>`
    <a class="card" href="${{x.h}}" target="_blank" rel="noopener noreferrer" style="position:relative">
      ${{isGhost?'<span class="ghost-badge">ghost</span>':''}}
      ${{pfpHtml(x.u)}}
      <div class="card-uname" title="@${{x.u}}">@${{x.u}}</div>
      ${{x.d?`<div class="card-date">${{x.d}}</div>`:''}}
      <div class="card-link">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
          <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
        </svg>Open profile
      </div>
    </a>`).join('');
}}

function filterSort(data, query, sort){{
  let d = query ? data.filter(x=>x.u.toLowerCase().includes(query)) : [...data];
  if(sort==='newest') d.sort((a,b)=>((b.ts||0)-(a.ts||0)));
  else if(sort==='oldest') d.sort((a,b)=>((a.ts||0)-(b.ts||0)));
  else if(sort==='az') d.sort((a,b)=>a.u.localeCompare(b.u));
  else if(sort==='za') d.sort((a,b)=>b.u.localeCompare(a.u));
  return d;
}}

function setup(data, searchId, sortId, gridId, countId, emptyId){{
  const render = ()=>renderGrid(
    filterSort(data,document.getElementById(searchId).value.toLowerCase().trim(),
               document.getElementById(sortId).value),
    gridId,countId,emptyId);
  document.getElementById(searchId).addEventListener('input', render);
  document.getElementById(sortId).addEventListener('change', render);
  render();
}}

setup(GHOSTS, 'gs-search','gs-sort','gs-grid','gs-count','gs-empty');
setup(MUTUALS,'mu-search','mu-sort','mu-grid','mu-count','mu-empty');
setup(FANS,   'fa-search','fa-sort','fa-grid','fa-count','fa-empty');

// Tabs
document.querySelectorAll('.tab').forEach(tab=>{{
  tab.addEventListener('click',()=>{{
    document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
    document.querySelectorAll('.section').forEach(s=>s.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('sec-'+tab.dataset.tab).classList.add('active');
  }});
}});
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  ✅  Report saved → \033[1;36m{output_path}\033[0m")
    print(f"  👥  Following      : \033[1m{len(following)}\033[0m")
    print(f"  📥  Followers      : \033[1;32m{len(followers)}\033[0m")
    print(f"  🤝  Mutuals        : \033[1;33m{len(mutuals)}\033[0m")
    print(f"  👻  Not following  : \033[1;35m{len(ghosts)}\033[0m")
    print(f"\n  Open \033[1;36m{output_path}\033[0m in any browser.\n")


# ── Entry point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate an Instagram HTML report from your data export."
    )
    parser.add_argument("--followers", default="followers_1.json",
                        help="Path to followers_1.json (default: followers_1.json)")
    parser.add_argument("--following", default="following.json",
                        help="Path to following.json  (default: following.json)")
    parser.add_argument("--output",   default="instagram_report.html",
                        help="Output HTML file        (default: instagram_report.html)")
    args = parser.parse_args()

    for label, path in [("Followers", args.followers), ("Following", args.following)]:
        if not os.path.isfile(path):
            print(f"\033[1;31m  ✗ {label} file not found: {path}\033[0m")
            print(f"    Put the file in the same folder or pass --{label.lower()} <path>\n")
            sys.exit(1)

    print(f"\n  Loading {args.followers} …")
    followers = load_followers(args.followers)
    print(f"  Loading {args.following} …")
    following = load_following(args.following)

    build_html(followers, following, args.output)


if __name__ == "__main__":
    main()
