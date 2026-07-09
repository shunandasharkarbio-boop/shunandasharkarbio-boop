import urllib.request
import json
import re
import math
from datetime import datetime

# ==========================================================
# CONFIGURATION & OVERRIDES
# ==========================================================
OVERRIDE_STATS = {
    "public_repos": 24,
    "commits": "1.2K+",
    "stars": 89,
    "followers": 42,
    "following": 36
}

OVERRIDE_LANGUAGES = [
    ("Python",     60.0, "#4ade80"),
    ("R",          15.0, "#3b82f6"),
    ("Jupyter",    10.0, "#f97316"),
    ("JavaScript",  8.0, "#facc15"),
    ("Other",       7.0, "#a8a29e")
]

# Set False to use real GitHub contribution data
FORCE_LUSH_GARDEN = False

# ==========================================================
# DATA FETCHING
# ==========================================================
def fetch_url(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as r:
            return r.read().decode('utf-8')
    except Exception as e:
        print(f"  Warning: {e}")
        return None

def get_real_data(username):
    stats = {}
    raw = fetch_url(f"https://api.github.com/users/{username}")
    if raw:
        d = json.loads(raw)
        stats['public_repos'] = d.get('public_repos', 0)
        stats['followers']    = d.get('followers', 0)
        stats['following']    = d.get('following', 0)
    else:
        stats = {'public_repos': 16, 'followers': 2, 'following': 1}

    repos_raw = fetch_url(f"https://api.github.com/users/{username}/repos?per_page=100")
    langs, stars = {}, 0
    if repos_raw:
        for repo in json.loads(repos_raw):
            if not repo.get('fork'):
                stars += repo.get('stargazers_count', 0)
                lang = repo.get('language')
                if lang:
                    langs[lang] = langs.get(lang, 0) + 1
    stats['stars'] = stars

    lang_colors = {
        "Python": "#4ade80", "HTML": "#e34c26", "CSS": "#563d7c",
        "JavaScript": "#f1e05a", "R": "#198ce7",
        "Jupyter Notebook": "#da5b0b", "Shell": "#89e051"
    }
    total = sum(langs.values()) or 1
    lang_list = []
    for lang, cnt in sorted(langs.items(), key=lambda x: x[1], reverse=True)[:4]:
        lang_list.append((lang, round(cnt/total*100, 1), lang_colors.get(lang, "#a8a29e")))
    spent = sum(x[1] for x in lang_list)
    if spent < 100:
        lang_list.append(("Other", round(100-spent, 1), "#a8a29e"))
    stats['languages'] = lang_list

    commits_raw = fetch_url(f"https://api.github.com/search/commits?q=author:{username}")
    commits = 466
    if commits_raw:
        try:
            commits = json.loads(commits_raw).get('total_count', 466)
        except Exception:
            pass
    stats['commits'] = commits

    contributions_html = fetch_url(f"https://github.com/users/{username}/contributions")
    contributions = []
    if contributions_html:
        for date, level in re.findall(r'data-date="(\d{4}-\d{2}-\d{2})".*?data-level="(\d+)"', contributions_html):
            contributions.append({'date': date, 'level': int(level)})
        contributions.sort(key=lambda x: x['date'])

    return stats, contributions


# ==========================================================
# SVG GENERATION  — matches reference image exactly
# ==========================================================
def generate_svg(username, stats, contributions):
    # Build 53×7 contribution grid
    grid = [[0]*7 for _ in range(53)]
    if contributions:
        start = datetime.strptime(contributions[0]['date'], "%Y-%m-%d")
        for day in contributions:
            dt = datetime.strptime(day['date'], "%Y-%m-%d")
            diff = (dt - start).days
            w, d = diff//7, diff%7
            if w < 53:
                grid[w][d] = day['level']

    if FORCE_LUSH_GARDEN:
        import random
        random.seed(42)
        grid = [[random.choice([0,0,1,1,2,3,4]) for _ in range(7)] for _ in range(53)]

    # Canvas
    W, H = 900, 320

    defs  = []
    style = []
    els   = []

    # ── Gradients & Filters ────────────────────────────────
    defs.append("""
    <linearGradient id="bgG" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="#010d05"/>
      <stop offset="100%" stop-color="#031808"/>
    </linearGradient>
    <linearGradient id="stemG" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%"   stop-color="#6ee7b7"/>
      <stop offset="100%" stop-color="#166534"/>
    </linearGradient>
    <radialGradient id="leftFade" cx="0%" cy="50%" r="30%">
      <stop offset="0%"   stop-color="#010d05"/>
      <stop offset="100%" stop-color="#010d05" stop-opacity="0"/>
    </radialGradient>
    <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="3" result="b"/>
      <feComposite in="SourceGraphic" in2="b" operator="over"/>
    </filter>
    <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="1.5" result="b"/>
      <feComposite in="SourceGraphic" in2="b" operator="over"/>
    </filter>
    <filter id="shadow">
      <feDropShadow dx="0" dy="3" stdDeviation="5"
                    flood-color="#000" flood-opacity="0.6"/>
    </filter>
    <clipPath id="leftClip">
      <rect x="0" y="0" width="625" height="320"/>
    </clipPath>
    <clipPath id="rightClip">
      <rect x="630" y="0" width="270" height="320"/>
    </clipPath>
    """)

    # ── CSS Animations ─────────────────────────────────────
    style.append("""
    text {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
      fill: #d1fae5;
    }
    .ttl  { font-size:10px; font-weight:700; letter-spacing:1.8px; fill:#6ee7b7; }
    .mon  { font-size:8.5px; fill:#4ade80; opacity:0.7; }
    .slabel { font-size:11.5px; fill:#a7f3d0; }
    .sval   { font-size:11.5px; fill:#6ee7b7; font-weight:700;
              font-family: 'Fira Code', Consolas, monospace; }
    .llabel { font-size:10.5px; fill:#a7f3d0; }
    .lpct   { font-size:10px; fill:#6ee7b7;
              font-family: 'Fira Code', Consolas, monospace; }
    .quote  { font-style:italic; font-size:11px; fill:#4ade80; opacity:0.65;
              font-family: Georgia, serif; }
    .banner { font-style:italic; font-size:11.5px; fill:#86efac; }
    .firefly { animation: ff 4s infinite ease-in-out; }
    @keyframes ff {
      0%,100% { opacity:0.15; r:1.5px; }
      50%      { opacity:0.95; r:2.5px; }
    }
    .sway {
      transform-box: fill-box;
      transform-origin: bottom center;
      animation: sway 5s infinite ease-in-out alternate;
    }
    @keyframes sway {
      0%   { transform: rotate(-4deg); }
      100% { transform: rotate(4deg);  }
    }
    .pop {
      transform-box: fill-box;
      transform-origin: center bottom;
      opacity: 0;
      animation: pop 0.7s cubic-bezier(.34,1.56,.64,1) forwards;
    }
    @keyframes pop {
      to { opacity:1; transform: scale(1); }
      from { transform: scale(0); }
    }
    .grow {
      stroke-dasharray: 300;
      stroke-dashoffset: 300;
      animation: grow 1.4s ease forwards;
    }
    @keyframes grow { to { stroke-dashoffset: 0; } }
    """)

    # ── Background ─────────────────────────────────────────
    els.append(f'<rect width="{W}" height="{H}" rx="14" fill="url(#bgG)"/>')

    # Subtle edge vignette on left side
    els.append(f'<rect x="0" y="0" width="80" height="{H}" rx="0" fill="url(#leftFade)"/>')

    # ── Top banner ─────────────────────────────────────────
    els.append(
        f'<text x="16" y="20" class="banner">'
        f'🌿 A scientist in the making.  •  A nature lover at heart.  •  A dreamer forever.  🌿'
        f'</text>'
    )

    # ── LEFT PANEL: Contribution Garden ────────────────────
    # card bg
    els.append('<rect x="8" y="30" width="612" height="278" rx="11" '
               'fill="#020e06" fill-opacity="0.75" stroke="#14532d" stroke-width="1.2" '
               'filter="url(#shadow)"/>')

    # title
    els.append('<text x="22" y="52" class="ttl">🌿 CONTRIBUTION GARDEN  ·</text>')

    # Month labels — 12 labels across 53 weeks
    month_labels = ["Jul","Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul"]
    label_cols   = [0, 4, 9, 13, 18, 22, 26, 31, 35, 39, 44, 48, 52]
    grid_x = 16
    step   = 11.0   # cell + gap
    cell   = 8.5

    for lbl, lc in zip(month_labels, label_cols):
        lx = grid_x + lc * step
        els.append(f'<text x="{lx:.1f}" y="68" class="mon">· {lbl}</text>')

    # Contribution cells
    grid_y = 74
    soil_y = 248

    colors = {
        0: "#0b2215",   # empty
        1: "#14532d",   # light
        2: "#166534",   # medium-low
        3: "#15803d",   # medium-high
        4: "#22c55e"    # bright
    }

    for col in range(53):
        for row in range(7):
            lvl   = grid[col][row]
            color = colors[lvl]
            cx    = grid_x + col * step
            cy    = grid_y + row * step
            # slightly rounded squares like reference
            els.append(
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{cell}" height="{cell}" '
                f'rx="2" fill="{color}" opacity="0.9"/>'
            )

    # Soil / ground line
    els.append(f'<line x1="8" y1="{soil_y}" x2="618" y2="{soil_y}" '
               f'stroke="#14532d" stroke-width="1" stroke-dasharray="3 3" opacity="0.6"/>')

    # ── Flowers & Stems ─────────────────────────────────────
    flower_palettes = [
        ("#a78bfa", "#e2e8f0"),   # violet / white centre
        ("#93c5fd", "#fde68a"),   # blue / yellow centre
        ("#f9a8d4", "#fde68a"),   # pink / yellow centre
        ("#fb923c", "#fde68a"),   # orange / yellow centre
        ("#ffffff", "#fbbf24"),   # white / amber centre
        ("#fdba74", "#86efac"),   # peach / green centre
    ]

    for col in range(53):
        week_sum = sum(grid[col])
        cx = grid_x + col * step + cell / 2
        delay = col * 0.018

        if week_sum <= 0:
            # sparse grass blades on empty weeks
            if col % 5 == 0:
                els.append(
                    f'<path class="grow" style="animation-delay:{delay:.2f}s" '
                    f'd="M {cx:.1f} {soil_y} Q {cx-2:.1f} {soil_y-10} {cx-3:.1f} {soil_y-14}" '
                    f'stroke="#166534" stroke-width="1.2" fill="none" opacity="0.5"/>'
                )
            continue

        # stem height
        stem_h = min(20 + week_sum * 5.5, 155)
        tip_y  = soil_y - stem_h
        wg     = math.sin(col * 0.9) * 10
        tip_x  = cx + wg

        # curved stem
        els.append(
            f'<path class="grow" style="animation-delay:{delay:.2f}s" '
            f'd="M {cx:.1f} {soil_y} Q {cx+wg*0.4:.1f} {soil_y-stem_h*0.55:.1f} {tip_x:.1f} {tip_y:.1f}" '
            f'stroke="url(#stemG)" stroke-width="1.4" fill="none" opacity="0.9"/>'
        )

        # leaves
        if stem_h > 40:
            ly1 = soil_y - stem_h * 0.38
            lx1 = cx + wg * 0.15
            els.append(
                f'<path class="pop" style="animation-delay:{delay+0.25:.2f}s" '
                f'd="M {lx1:.1f} {ly1:.1f} C {lx1-9:.1f} {ly1-4:.1f} {lx1-11:.1f} {ly1+4:.1f} {lx1:.1f} {ly1:.1f}" '
                f'fill="#4ade80" opacity="0.75"/>'
            )
        if stem_h > 80:
            ly2 = soil_y - stem_h * 0.65
            lx2 = cx + wg * 0.45
            els.append(
                f'<path class="pop" style="animation-delay:{delay+0.4:.2f}s" '
                f'd="M {lx2:.1f} {ly2:.1f} C {lx2+9:.1f} {ly2-4:.1f} {lx2+11:.1f} {ly2+4:.1f} {lx2:.1f} {ly2:.1f}" '
                f'fill="#4ade80" opacity="0.75"/>'
            )

        # flower at tip
        fc, cc = flower_palettes[col % len(flower_palettes)]
        fl_delay = delay + 0.55

        if week_sum >= 8:
            # Full bloom: 5 petals + centre
            els.append(
                f'<g class="sway pop" style="animation-delay:{fl_delay:.2f}s" '
                f'transform="translate({tip_x:.1f},{tip_y:.1f})">'
            )
            for p in range(5):
                ang = p / 5 * 2 * math.pi - math.pi / 2
                px  = math.cos(ang) * 5.5
                py  = math.sin(ang) * 5.5
                els.append(f'<ellipse cx="{px:.2f}" cy="{py:.2f}" rx="3.8" ry="3.2" fill="{fc}" opacity="0.92"/>')
            els.append(f'<circle cx="0" cy="0" r="2.8" fill="{cc}"/>')
            els.append('</g>')

        elif week_sum >= 4:
            # Bud
            els.append(
                f'<g class="pop" style="animation-delay:{fl_delay:.2f}s" '
                f'transform="translate({tip_x:.1f},{tip_y:.1f})">'
                f'<ellipse cx="0" cy="-4" rx="3" ry="5" fill="{fc}" opacity="0.85"/>'
                f'<ellipse cx="-3" cy="-2" rx="2.5" ry="4" fill="{fc}" opacity="0.7"/>'
                f'<ellipse cx="3" cy="-2" rx="2.5" ry="4" fill="{fc}" opacity="0.7"/>'
                f'</g>'
            )
        else:
            # Tiny sprout
            els.append(
                f'<path class="pop" style="animation-delay:{fl_delay:.2f}s" '
                f'd="M {tip_x:.1f} {tip_y:.1f} C {tip_x-4:.1f} {tip_y-6:.1f} {tip_x} {tip_y-10:.1f} {tip_x:.1f} {tip_y:.1f} '
                f'C {tip_x+4:.1f} {tip_y-6:.1f} {tip_x} {tip_y-10:.1f} {tip_x:.1f} {tip_y:.1f}" '
                f'fill="#86efac" opacity="0.85"/>'
            )

    # Fireflies / sparkles
    ff_pts = [(80,170),(200,145),(350,200),(500,155),(440,90),(150,105),(560,120),(290,80)]
    for i,(fx,fy) in enumerate(ff_pts):
        els.append(
            f'<circle cx="{fx}" cy="{fy}" r="2" fill="#fde68a" '
            f'filter="url(#glow)" class="firefly" style="animation-delay:{i*0.6:.1f}s"/>'
        )

    # Butterfly (simple SVG path near top-right of garden)
    bx, by = 540, 97
    els.append(
        f'<g transform="translate({bx},{by})" opacity="0.7">'
        f'<path d="M0,0 C-8,-10 -18,-8 -12,0 C-8,4 -4,2 0,0" fill="#d946ef" opacity="0.75"/>'
        f'<path d="M0,0 C8,-10 18,-8 12,0 C8,4 4,2 0,0" fill="#c026d3" opacity="0.75"/>'
        f'<path d="M0,0 C-6,5 -12,10 -8,14 C-4,10 -2,5 0,0" fill="#d946ef" opacity="0.6"/>'
        f'<path d="M0,0 C6,5 12,10 8,14 C4,10 2,5 0,0" fill="#c026d3" opacity="0.6"/>'
        f'<line x1="0" y1="-2" x2="-4" y2="-8" stroke="#1a1a1a" stroke-width="0.7"/>'
        f'<line x1="0" y1="-2" x2="4" y2="-8" stroke="#1a1a1a" stroke-width="0.7"/>'
        f'</g>'
    )

    # Quote
    els.append('<text x="312" y="288" class="quote" text-anchor="middle">'
               '"Small commits, big changes."</text>')

    # ── RIGHT PANEL ────────────────────────────────────────
    rp_x = 628  # left edge of right panel

    # Divider line
    els.append(f'<line x1="{rp_x-2}" y1="30" x2="{rp_x-2}" y2="295" '
               f'stroke="#14532d" stroke-width="1" opacity="0.5"/>')

    # ── LAB STATS card ─────────────────────────────────────
    els.append(f'<rect x="{rp_x}" y="30" width="262" height="126" rx="10" '
               f'fill="#020e06" fill-opacity="0.75" stroke="#14532d" stroke-width="1.2" filter="url(#shadow)"/>')
    els.append(f'<text x="{rp_x+14}" y="52" class="ttl">LAB STATS</text>')

    stat_rows = [
        ("📁", "Repositories", str(stats["public_repos"])),
        ("🌿", "Commits",      str(stats["commits"])),
        ("⭐", "Stars",        str(stats["stars"])),
        ("👥", "Followers",    str(stats["followers"])),
        ("🤝", "Following",    str(stats["following"])),
    ]
    for i, (ico, lbl, val) in enumerate(stat_rows):
        ry = 68 + i * 18
        els.append(f'<text x="{rp_x+14}" y="{ry}" class="slabel">{ico}  {lbl}</text>')
        els.append(f'<text x="{rp_x+258}" y="{ry}" class="sval" text-anchor="end">{val}</text>')

    # ── LANGUAGES card ─────────────────────────────────────
    lc_y = 165
    els.append(f'<rect x="{rp_x}" y="{lc_y}" width="262" height="130" rx="10" '
               f'fill="#020e06" fill-opacity="0.75" stroke="#14532d" stroke-width="1.2" filter="url(#shadow)"/>')
    els.append(f'<text x="{rp_x+14}" y="{lc_y+22}" class="ttl">LANGUAGES</text>')

    # Donut chart
    dcx = rp_x + 50
    dcy = lc_y + 75
    r   = 30
    circ = 2 * math.pi * r
    acc  = 0.0
    for lang, pct, color in stats["languages"]:
        dash = (pct / 100) * circ
        gap  = circ - dash
        off  = -(acc / 100) * circ
        els.append(
            f'<circle cx="{dcx}" cy="{dcy}" r="{r}" fill="none" stroke="{color}" '
            f'stroke-width="11" stroke-dasharray="{dash:.2f} {gap:.2f}" '
            f'stroke-dashoffset="{off:.2f}" transform="rotate(-90 {dcx} {dcy})" '
            f'filter="url(#softGlow)"/>'
        )
        acc += pct

    # Donut inner ring underlay
    els.append(f'<circle cx="{dcx}" cy="{dcy}" r="21" fill="#010d05"/>')

    # Legend
    leg_x = rp_x + 96
    leg_y = lc_y + 42
    leg_sp = 17
    for i, (lang, pct, color) in enumerate(stats["languages"][:5]):
        ly = leg_y + i * leg_sp
        els.append(f'<rect x="{leg_x}" y="{ly-8}" width="7" height="7" rx="1.5" fill="{color}"/>')
        els.append(f'<text x="{leg_x+11}" y="{ly}" class="llabel">{lang}</text>')
        els.append(f'<text x="{rp_x+256}" y="{ly}" class="lpct" text-anchor="end">{pct}%</text>')

    # ── Compile SVG ────────────────────────────────────────
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {W} {H}" width="100%" height="{H}">
  <defs>{chr(10).join(defs)}</defs>
  <style>{chr(10).join(style)}</style>
  {chr(10).join(els)}
</svg>"""
    return svg


# ==========================================================
# MAIN
# ==========================================================
def main():
    username = "shunandasharkarbio-boop"
    print("Collecting GitHub data...")
    real_stats, contributions = get_real_data(username)

    final = {}
    if OVERRIDE_STATS:
        final.update(OVERRIDE_STATS)
    else:
        for k in ("public_repos","commits","stars","followers","following"):
            final[k] = real_stats[k]

    final["languages"] = OVERRIDE_LANGUAGES if OVERRIDE_LANGUAGES else real_stats["languages"]

    print("Generating garden SVG...")
    svg = generate_svg(username, final, contributions)

    with open("garden.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    print("Done! Saved to garden.svg")

if __name__ == "__main__":
    main()
