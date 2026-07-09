import urllib.request
import json
import re
import math
from datetime import datetime

# ==========================================================
# CONFIGURATION & OVERRIDES
# Set to None to use actual live GitHub data.
# Set to values to show custom showcase stats.
# ==========================================================
OVERRIDE_STATS = {
    "public_repos": 24,
    "commits": "1.2K+",
    "stars": 89,
    "followers": 42,
    "following": 36
}

OVERRIDE_LANGUAGES = [
    ("Python", 60.0, "#4ade80"),
    ("R", 15.0, "#3b82f6"),
    ("Jupyter", 10.0, "#f97316"),
    ("JavaScript", 8.0, "#facc15"),
    ("Other", 7.0, "#a8a29e")
]

# Set to False to use actual contribution grid data.
# Set to True to generate a lush, fully blooming demo garden.
FORCE_LUSH_GARDEN = True 

# ==========================================================
# DATA FETCHING UTILITIES
# ==========================================================
def fetch_url(url):
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_real_data(username):
    user_stats = {}
    
    # 1. Fetch user general stats
    user_data_raw = fetch_url(f"https://api.github.com/users/{username}")
    if user_data_raw:
        user_data = json.loads(user_data_raw)
        user_stats['public_repos'] = user_data.get('public_repos', 0)
        user_stats['followers'] = user_data.get('followers', 0)
        user_stats['following'] = user_data.get('following', 0)
    else:
        user_stats = {'public_repos': 16, 'followers': 2, 'following': 1}
        
    # 2. Fetch repos to calculate languages and stars
    repos_data_raw = fetch_url(f"https://api.github.com/users/{username}/repos?per_page=100")
    languages = {}
    stars = 0
    if repos_data_raw:
        repos_data = json.loads(repos_data_raw)
        for repo in repos_data:
            if not repo.get('fork', False):
                stars += repo.get('stargazers_count', 0)
                lang = repo.get('language')
                if lang:
                    languages[lang] = languages.get(lang, 0) + 1
    
    user_stats['stars'] = stars
    
    # Languages color mapping
    lang_colors = {
        "Python": "#4ade80",
        "HTML": "#e34c26",
        "CSS": "#563d7c",
        "JavaScript": "#f1e05a",
        "R": "#198ce7",
        "Jupyter Notebook": "#da5b0b",
        "Shell": "#89e051"
    }
    
    total_langs = sum(languages.values()) if languages else 1
    languages_pct = []
    for lang, count in sorted(languages.items(), key=lambda x: x[1], reverse=True)[:4]:
        pct = round((count / total_langs) * 100, 1)
        color = lang_colors.get(lang, "#a8a29e")
        languages_pct.append((lang, pct, color))
        
    # Add "Other" if there's remaining percentage
    spent_pct = sum(x[1] for x in languages_pct)
    if spent_pct < 100:
        languages_pct.append(("Other", round(100 - spent_pct, 1), "#a8a29e"))
        
    user_stats['languages'] = languages_pct
    
    # 3. Fetch total commits (a quick estimation from search API)
    commits_search_raw = fetch_url(f"https://api.github.com/search/commits?q=author:{username}")
    commits = 0
    if commits_search_raw:
        try:
            commits_data = json.loads(commits_search_raw)
            commits = commits_data.get('total_count', 0)
        except Exception:
            pass
    if commits == 0:
         commits = 466 # fallback estimate
    user_stats['commits'] = commits
    
    # 4. Fetch contribution grid HTML
    contributions_html = fetch_url(f"https://github.com/users/{username}/contributions")
    contributions = []
    if contributions_html:
        pattern = r'data-date="(\d{4}-\d{2}-\d{2})".*?data-level="(\d+)"'
        matches = re.findall(pattern, contributions_html)
        for date, level in matches:
            contributions.append({'date': date, 'level': int(level)})
        contributions.sort(key=lambda x: x['date'])
        
    return user_stats, contributions

# ==========================================================
# SVG GENERATION
# ==========================================================
def generate_svg(username, stats, contributions):
    # Setup standard 53x7 grid
    grid = [[0 for _ in range(7)] for _ in range(53)]
    
    if contributions:
        # Group days into weeks
        start_date = datetime.strptime(contributions[0]['date'], "%Y-%m-%d")
        for day in contributions:
            dt = datetime.strptime(day['date'], "%Y-%m-%d")
            days_diff = (dt - start_date).days
            week_idx = days_diff // 7
            day_idx = days_diff % 7
            if week_idx < 53:
                grid[week_idx][day_idx] = day['level']
                
    if FORCE_LUSH_GARDEN:
        # Generate some beautiful dummy contribution levels for a lush garden demo
        import random
        random.seed(42)
        grid = [[random.choice([0,0,1,1,2,3,4]) for _ in range(7)] for _ in range(53)]

    # Card layout configs
    width = 950
    height = 330
    
    # SVG Elements lists
    defs = []
    styles = []
    elements = []
    
    # Defs: Gradients, Glow filters
    defs.append("""
    <linearGradient id="bg-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#020f07" />
        <stop offset="100%" stop-color="#041f0f" />
    </linearGradient>
    <linearGradient id="stem-gradient" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stop-color="#81c784" />
        <stop offset="100%" stop-color="#2e7d32" />
    </linearGradient>
    <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="2.5" result="blur" />
        <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    <filter id="card-glow" x="-10%" y="-10%" width="120%" height="120%">
        <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.5"/>
    </filter>
    """)
    
    # Stylesheet
    styles.append("""
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;600&family=Inter:wght@400;600;700&family=Playfair+Display:ital,wght@1,500;1,600&display=swap');
    text {
        font-family: 'Inter', sans-serif;
        fill: #e2e8f0;
    }
    .title {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.5px;
        fill: #81c784;
    }
    .marquee {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 13px;
        fill: #a8e6cf;
    }
    .stat-label {
        font-size: 12px;
        fill: #94a3b8;
    }
    .stat-val {
        font-family: 'Fira Code', monospace;
        font-size: 12px;
        font-weight: 600;
        fill: #4ade80;
        text-anchor: end;
    }
    .lang-label {
        font-size: 11px;
        fill: #cbd5e1;
    }
    .lang-pct {
        font-family: 'Fira Code', monospace;
        font-size: 10px;
        fill: #94a3b8;
    }
    .quote {
        font-family: 'Playfair Display', serif;
        font-style: italic;
        font-size: 12px;
        fill: #6b7280;
        text-anchor: middle;
    }
    .firefly {
        animation: pulse 3s infinite ease-in-out;
    }
    @keyframes pulse {
        0%, 100% { opacity: 0.2; transform: scale(0.8); }
        50% { opacity: 0.9; transform: scale(1.2); }
    }
    """)
    
    # Main outer rectangle
    elements.append('<rect x="0" y="0" width="950" height="330" rx="16" fill="url(#bg-gradient)" stroke="#113e21" stroke-width="2"/>')
    
    # Top Marquee / Tagline
    elements.append('<text x="35" y="30" class="marquee">🌱 A scientist in the making.  🌲 A nature lover at heart.  🌿 A dreamer forever.</text>')
    
    # Cards layout (Glassmorphism borders & shadows)
    # 1. Left Card: Contribution Garden
    elements.append('<rect x="20" y="48" width="670" height="262" rx="12" fill="#03150b" fill-opacity="0.65" stroke="#164e2d" stroke-width="1.2" filter="url(#card-glow)"/>')
    elements.append('<text x="50" y="74" class="title">🌿 CONTRIBUTION GARDEN</text>')
    
    # 2. Right Top Card: Lab Stats
    elements.append('<rect x="710" y="48" width="220" height="124" rx="12" fill="#03150b" fill-opacity="0.65" stroke="#164e2d" stroke-width="1.2" filter="url(#card-glow)"/>')
    elements.append('<text x="730" y="74" class="title">🔬 LAB STATS</text>')
    
    # 3. Right Bottom Card: Languages
    elements.append('<rect x="710" y="186" width="220" height="124" rx="12" fill="#03150b" fill-opacity="0.65" stroke="#164e2d" stroke-width="1.2" filter="url(#card-glow)"/>')
    elements.append('<text x="730" y="210" class="title">💻 LANGUAGES</text>')
    
    # ==========================================================
    # RENDER GRID & THE GARDEN (Trellis & Stems)
    # ==========================================================
    # Grid offset: x starting at 50, y starting at 95
    grid_x = 50
    grid_y = 92
    cell_size = 9
    spacing = 3.2
    step = cell_size + spacing # 12.2
    
    # Contribution Colors (Forest/Garden theme)
    colors = {
        0: "#06180d", # Invisible background/soil
        1: "#0f361d", # Light sprout green
        2: "#1c5d33", # Medium leaf green
        3: "#2e8b4e", # Rich plant green
        4: "#4ade80"  # Blooming bright neon green
    }
    
    # Draw contribution grid cells (trellis)
    for col in range(53):
        for row in range(7):
            level = grid[col][row]
            color = colors[level]
            cx = grid_x + col * step
            cy = grid_y + row * step
            elements.append(f'<rect x="{cx}" y="{cy}" width="{cell_size}" height="{cell_size}" rx="2" fill="{color}"/>')
            
    # Ground soil line
    soil_y = 265
    elements.append(f'<line x1="35" y1="{soil_y}" x2="675" y2="{soil_y}" stroke="#143d22" stroke-width="1.5" stroke-dasharray="4 2"/>')
    
    # Flower color palette choices
    # Petals color, Center color
    flower_styles = [
        ("#b39ddb", "#ffd54f"),  # Purple Daisy
        ("#f48fb1", "#fff59d"),  # Pink Cosmos
        ("#81d4fa", "#ffca28"),  # Blue Bell
        ("#ffb74d", "#d4e157"),  # Orange Lily
        ("#ffffff", "#ffd54f"),  # White Camomile
    ]
    
    # Draw Stems, Vines and Flowers growing up
    for col in range(53):
        week_total = sum(grid[col])
        col_x = grid_x + col * step + (cell_size / 2)
        
        if week_total > 0:
            # Stem height proportional to commits
            # Min height: 25px, Max height: 160px
            stem_h = min(25 + week_total * 5.0, 160)
            target_y = soil_y - stem_h
            
            # Curved Bezier path for organic growth
            wiggle = math.sin(col) * 12
            target_x = col_x + wiggle
            
            # Draw stem path
            elements.append(
                f'<path d="M {col_x} {soil_y} Q {col_x + wiggle*0.5} {soil_y - stem_h*0.5} {target_x} {target_y}" '
                f'stroke="url(#stem-gradient)" stroke-width="1.5" fill="none" opacity="0.85"/>'
            )
            
            # Draw leaves
            if stem_h > 45:
                # Leaf 1 (Left, 40% height)
                ly1 = soil_y - stem_h * 0.4
                lx1 = col_x + wiggle * 0.16
                elements.append(f'<path d="M {lx1} {ly1} C {lx1-6} {ly1-3} {lx1-8} {ly1+2} {lx1} {ly1}" fill="#4ade80" opacity="0.8"/>')
                
                # Leaf 2 (Right, 70% height)
                ly2 = soil_y - stem_h * 0.7
                lx2 = col_x + wiggle * 0.49
                elements.append(f'<path d="M {lx2} {ly2} C {lx2+6} {ly2-3} {lx2+8} {ly2+2} {lx2} {ly2}" fill="#4ade80" opacity="0.8"/>')
            
            # Bloom flower at top based on contributions
            if week_total >= 8:
                # High commits = Beautiful blooming flower!
                # Choose color style deterministically based on week number
                flower_color, center_color = flower_styles[col % len(flower_styles)]
                
                elements.append(f'<g transform="translate({target_x}, {target_y})">')
                # 5 circles as petals
                elements.append(f'  <circle cx="0" cy="-4.5" r="3.5" fill="{flower_color}"/>')
                elements.append(f'  <circle cx="4.2" cy="-1.4" r="3.5" fill="{flower_color}"/>')
                elements.append(f'  <circle cx="2.6" cy="3.6" r="3.5" fill="{flower_color}"/>')
                elements.append(f'  <circle cx="-2.6" cy="3.6" r="3.5" fill="{flower_color}"/>')
                elements.append(f'  <circle cx="-4.2" cy="-1.4" r="3.5" fill="{flower_color}"/>')
                # Yellow flower center
                elements.append(f'  <circle cx="0" cy="0" r="2.2" fill="{center_color}"/>')
                elements.append('</g>')
            elif week_total >= 3:
                # Medium commits = A flower bud
                elements.append(
                    f'<path d="M {target_x} {target_y} C {target_x-4} {target_y-6} {target_x} {target_y-10} {target_x} {target_y-10} '
                    f'C {target_x} {target_y-10} {target_x+4} {target_y-6} {target_x} {target_y}" fill="#f48fb1"/>'
                )
            else:
                # Low commits = Small green sprout/leaves
                elements.append(
                    f'<path d="M {target_x} {target_y} C {target_x-3} {target_y-3} {target_x-4} {target_y} {target_x} {target_y} '
                    f'C {target_x+3} {target_y-3} {target_x+4} {target_y} {target_x} {target_y}" fill="#81c784"/>'
                )
        else:
            # 25% chance of grass for non-commit weeks to keep ground lush
            if col % 4 == 0:
                elements.append(
                    f'<path d="M {col_x} {soil_y} Q {col_x-2} {soil_y-6} {col_x-4} {soil_y-9} Q {col_x-1} {soil_y-4} {col_x} {soil_y} Z" fill="#1b5e3a"/>'
                )
                
    # Add a couple of glowing fireflies/particles
    firefly_coords = [(120, 210), (280, 180), (450, 220), (580, 160), (320, 80), (80, 110)]
    for i, (fx, fy) in enumerate(firefly_coords):
        elements.append(
            f'<circle cx="{fx}" cy="{fy}" r="2" fill="#ffd54f" filter="url(#glow)" class="firefly" '
            f'style="animation-delay: {i*0.5}s; opacity: 0.75;"/>'
        )
        
    # Quote at bottom of left card
    elements.append('<text x="355" y="292" class="quote">"Small commits, big changes."</text>')
    
    # ==========================================================
    # RIGHT TOP CARD: LAB STATS
    # ==========================================================
    stat_y_start = 100
    stat_spacing = 20
    
    # Stats fields configuration
    stats_list = [
        ("Repositories", stats["public_repos"], "📁"),
        ("Commits", stats["commits"], "🌿"),
        ("Stars", stats["stars"], "⭐"),
        ("Followers", stats["followers"], "👥"),
        ("Following", stats["following"], "🤝")
    ]
    
    for i, (label, val, icon) in enumerate(stats_list):
        curr_y = stat_y_start + i * stat_spacing
        elements.append(f'<text x="732" y="{curr_y}" class="stat-label">{icon}  {label}</text>')
        elements.append(f'<text x="910" y="{curr_y}" class="stat-val">{val}</text>')
        
    # ==========================================================
    # RIGHT BOTTOM CARD: LANGUAGES
    # ==========================================================
    # Donut center: cx = 770, cy = 245
    # Radius = 24
    donut_cx = 770
    donut_cy = 248
    donut_r = 24
    donut_circumference = 2 * math.pi * donut_r # ~150.8
    
    # Background circle underlay
    elements.append(f'<circle cx="{donut_cx}" cy="{donut_cy}" r="{donut_r}" fill="none" stroke="#051c0f" stroke-width="8"/>')
    
    # Draw segments
    accumulated_pct = 0
    for lang, pct, color in stats["languages"]:
        dash_len = (pct / 100) * donut_circumference
        gap_len = donut_circumference - dash_len
        offset = - (accumulated_pct / 100) * donut_circumference
        
        elements.append(
            f'<circle cx="{donut_cx}" cy="{donut_cy}" r="{donut_r}" fill="none" stroke="{color}" stroke-width="8" '
            f'stroke-dasharray="{dash_len:.2f} {gap_len:.2f}" stroke-dashoffset="{offset:.2f}" '
            f'transform="rotate(-90 {donut_cx} {donut_cy})"/>'
        )
        accumulated_pct += pct
        
    # Draw Legend on the right of the donut
    legend_x = 818
    legend_y_start = 216
    legend_spacing = 16
    
    for i, (lang, pct, color) in enumerate(stats["languages"][:5]):
        curr_y = legend_y_start + i * legend_spacing
        # Dot/square
        elements.append(f'<rect x="{legend_x}" y="{curr_y - 8}" width="7" height="7" rx="1.5" fill="{color}"/>')
        # Label
        elements.append(f'<text x="{legend_x + 13}" y="{curr_y - 1}" class="lang-label">{lang}</text>')
        # Pct
        elements.append(f'<text x="912" y="{curr_y - 1}" class="lang-pct" text-anchor="end">{pct}%</text>')

    # Compile the SVG
    svg_out = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="100%" height="{height}">
    <defs>
    {chr(10).join(defs)}
    </defs>
    <style>
    {chr(10).join(styles)}
    </style>
    {chr(10).join(elements)}
</svg>
"""
    return svg_out

def main():
    username = "shunandasharkarbio-boop"
    
    # 1. Gather stats (Check configs first)
    print("Collecting GitHub Statistics...")
    real_stats, contributions = get_real_data(username)
    
    # Mixin overrides
    final_stats = {}
    
    # Repos, commits, stars, followers, following
    if OVERRIDE_STATS:
        for k, v in OVERRIDE_STATS.items():
            final_stats[k] = v
    else:
        final_stats["public_repos"] = real_stats["public_repos"]
        final_stats["commits"] = real_stats["commits"]
        final_stats["stars"] = real_stats["stars"]
        final_stats["followers"] = real_stats["followers"]
        final_stats["following"] = real_stats["following"]
        
    # Languages
    if OVERRIDE_LANGUAGES:
        final_stats["languages"] = OVERRIDE_LANGUAGES
    else:
        final_stats["languages"] = real_stats["languages"]
        
    # 2. Build the SVG file
    print("Generating your custom Garden SVG...")
    svg_code = generate_svg(username, final_stats, contributions)
    
    # 3. Write out the SVG
    output_path = "garden.svg"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_code)
        
    print(f"Success! Saved garden visualization to '{output_path}'")

if __name__ == "__main__":
    main()
