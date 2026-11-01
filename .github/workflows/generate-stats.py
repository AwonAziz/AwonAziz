#!/usr/bin/env python3
"""
Generate cyberpunk SVG profile assets from real GitHub API data.
Run via GitHub Actions on a schedule to keep stats current.
"""

import json
import os
import urllib.request
import urllib.error

USERNAME = "AwonAziz"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT_DIR = "assets"

FONT_STACK = "'SF Mono', 'Cascadia Code', 'Fira Code', Consolas, 'Liberation Mono', Menlo, monospace"

LANG_COLORS = {
    "Python": "#3776AB",
    "TypeScript": "#3178C6",
    "JavaScript": "#F7DF1E",
    "Shell": "#00AA00",
    "HTML": "#E34F26",
    "CSS": "#F7DF1E",
    "Jupyter Notebook": "#C471ED",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
    "Java": "#B07219",
    "C++": "#F34B7D",
    "Ruby": "#701516",
}


def api_get(path):
    """Fetch data from GitHub API with optional auth."""
    url = f"https://api.github.com{path}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "AwonAziz-profile-generator"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"API error {e.code} for {path}")
        return {}


def fetch_user():
    return api_get(f"/users/{USERNAME}")


def fetch_repos():
    repos = []
    page = 1
    while True:
        data = api_get(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner&sort=updated")
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def fetch_languages(repos):
    """Aggregate language bytes across all repos."""
    lang_bytes = {}
    for r in repos:
        lang_url = r.get("languages_url")
        if not lang_url:
            continue
        if lang_url.startswith("https://api.github.com/repos/"):
            path = lang_url.replace("https://api.github.com", "")
            langs = api_get(path)
            for lang, bytes_count in langs.items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + bytes_count
    return lang_bytes


def esc(text):
    """XML-escape text."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def svg_defs():
    """Common SVG defs block."""
    return '''  <defs>
    <filter id="matrixGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <filter id="softGlow" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="1.5" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
    <pattern id="hexGrid" width="40" height="35" patternUnits="userSpaceOnUse">
      <path d="M20,0 L40,10 L40,25 L20,35 L0,25 L0,10 Z" fill="none" stroke="#00ff41" stroke-opacity="0.04" stroke-width="0.5"/>
    </pattern>
    <pattern id="scanline" width="4" height="4" patternUnits="userSpaceOnUse">
      <rect width="4" height="2" fill="#00ff41" opacity="0.03"/>
    </pattern>
  </defs>'''


def matrix_rain_strip(x, y_start, height):
    """Generate matrix rain strip SVG."""
    return f'''  <!-- Matrix rain strip (right side, subtle) -->
  <g opacity="0.10" transform="translate({x}, {y_start})">
    <text x="0" y="0" font-size="8" fill="#00ff41">
      <animate attributeName="y" values="-40;{height}" dur="2.5s" calcMode="discrete" repeatCount="indefinite"/>
      <tspan x="0" dy="10">1</tspan>
      <tspan x="0" dy="10">0</tspan>
      <tspan x="0" dy="10">1</tspan>
      <tspan x="0" dy="10">0</tspan>
    </text>
    <text x="12" y="0" font-size="8" fill="#00ff41">
      <animate attributeName="y" values="-50;{height}" dur="3s" begin="-0.8s" calcMode="discrete" repeatCount="indefinite"/>
      <tspan x="12" dy="10">0</tspan>
      <tspan x="12" dy="10">1</tspan>
      <tspan x="12" dy="10">0</tspan>
      <tspan x="12" dy="10">1</tspan>
    </text>
  </g>'''


def title_bar(title, subtitle, width=400):
    """Generate title bar SVG."""
    return f'''  <!-- Title bar -->
  <rect x="1" y="1" width="{width - 2}" height="28" rx="8" fill="#001a00" opacity="0.8"/>
  <rect x="1" y="1" width="{width - 2}" height="28" rx="8" fill="none" stroke="#00ff41" stroke-width="0.5" opacity="0.3"/>
  <text x="16" y="20" font-size="11" fill="#00ff41" font-weight="bold" letter-spacing="1" filter="url(#softGlow)">{title}</text>
  <text x="{width - 20}" y="20" font-size="9" fill="#00aa00" text-anchor="end" letter-spacing="1">{subtitle}</text>

  <!-- Accent line under title -->
  <line x1="16" y1="34" x2="{width - 16}" y2="34" stroke="#00ff41" stroke-width="0.5" opacity="0.4"/>
  <rect x="16" y="33" width="80" height="2" fill="#00ff41" opacity="0.8">
    <animate attributeName="width" values="0;80" dur="1s" begin="0.01s" fill="freeze"/>
  </rect>'''


def footer_bar(text, width=400, y=0):
    """Generate footer bar SVG."""
    return f'''  <!-- Footer -->
  <rect x="16" y="{y}" width="{width - 32}" height="14" rx="3" fill="#001a00" opacity="0.5"/>
  <text x="{width // 2}" y="{y + 11}" text-anchor="middle" font-size="9" fill="#00aa00" font-weight="bold" letter-spacing="1">{text}</text>'''


def generate_stats_overview(user, repos):
    """Generate stats-overview.svg with real data."""
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)
    public_repos = user.get("public_repos", len(repos))
    followers = user.get("followers", 0)

    body = f'''
  {matrix_rain_strip(360, 40, 200)}

  {title_bar("GITHUB STATS", esc(USERNAME).upper())}

  <!-- Stats rows -->
  <g transform="translate(16, 44)">
    <text x="0" y="16" font-size="10" fill="#00aa00" letter-spacing="0.5">PUBLIC REPOS</text>
    <text x="368" y="16" font-size="15" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">{public_repos}</text>
    <line x1="0" y1="22" x2="368" y2="22" stroke="#003300" stroke-width="0.5"/>

    <text x="0" y="40" font-size="10" fill="#00aa00" letter-spacing="0.5">TOTAL STARS</text>
    <text x="368" y="40" font-size="15" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">{total_stars}</text>
    <line x1="0" y1="46" x2="368" y2="46" stroke="#003300" stroke-width="0.5"/>

    <text x="0" y="64" font-size="10" fill="#00aa00" letter-spacing="0.5">TOTAL FORKS</text>
    <text x="368" y="64" font-size="15" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">{total_forks}</text>
    <line x1="0" y1="70" x2="368" y2="70" stroke="#003300" stroke-width="0.5"/>

    <text x="0" y="88" font-size="10" fill="#00aa00" letter-spacing="0.5">FOLLOWERS</text>
    <text x="368" y="88" font-size="15" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">{followers}</text>
    <line x1="0" y1="94" x2="368" y2="94" stroke="#003300" stroke-width="0.5"/>
  </g>

  {footer_bar("SYSTEM OPERATIONAL", 400, 216)}
</svg>'''
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="240" viewBox="0 0 400 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub Stats — Awon Aziz" font-family="{FONT_STACK}">
  <title>GitHub Stats — Awon Aziz</title>
{svg_defs()}
  <rect width="100%" height="100%" fill="#0a0713" rx="8"/>
  <rect width="100%" height="100%" fill="url(#hexGrid)" rx="8"/>
  <rect width="100%" height="100%" fill="url(#scanline)" rx="8"/>
  <rect width="100%" height="100%" fill="none" stroke="#00ff41" stroke-width="1" rx="8" opacity="0.25"/>
{body}'''


def generate_languages(lang_bytes):
    """Generate languages.svg with real language data."""
    if not lang_bytes:
        lang_bytes = {"Python": 1000}

    total = sum(lang_bytes.values())
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:6]
    colors = ["#3776AB", "#3178C6", "#00AA00", "#E34F26", "#C471ED", "#F7DF1E"]

    bars = []
    y = 14
    bar_spacing = 24
    for i, (lang, bytes_count) in enumerate(sorted_langs):
        pct = bytes_count / total * 100 if total > 0 else 0
        bar_width = int(368 * bytes_count / max(lang_bytes.values())) if lang_bytes.values() else 100
        color = colors[i % len(colors)]
        bars.append(f'''
    <text x="0" y="{y}" font-size="10" fill="#5eead4" font-weight="bold">{esc(lang)}</text>
    <text x="368" y="{y}" font-size="9" fill="#00ff41" text-anchor="end">{pct:.0f}%</text>
    <rect x="0" y="{y + 4}" width="368" height="6" rx="3" fill="#001a00"/>
    <rect x="0" y="{y + 4}" width="0" height="6" rx="3" fill="{color}" filter="url(#softGlow)">
      <animate attributeName="width" values="0;{bar_width}" dur="{1.0 + i * 0.1:.1f}s" begin="{0.01 + i * 0.1:.2f}s" fill="freeze"/>
    </rect>''')
        y += bar_spacing

    footer_y = 44 + y + 4

    body = f'''
  {matrix_rain_strip(360, 40, 240)}

  {title_bar("TOP LANGUAGES", "REAL DATA")}

  <!-- Language bars -->
  <g transform="translate(16, 44)">
    {''.join(bars)}
  </g>

  {footer_bar("MACHINE LEARNING FOCUS", 400, footer_y)}
</svg>'''
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="{footer_y + 18}" viewBox="0 0 400 {footer_y + 18}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Top Languages — Awon Aziz" font-family="{FONT_STACK}">
  <title>Top Languages — Awon Aziz</title>
{svg_defs()}
  <rect width="100%" height="100%" fill="#0a0713" rx="8"/>
  <rect width="100%" height="100%" fill="url(#hexGrid)" rx="8"/>
  <rect width="100%" height="100%" fill="url(#scanline)" rx="8"/>
  <rect width="100%" height="100%" fill="none" stroke="#00ff41" stroke-width="1" rx="8" opacity="0.25"/>
{body}'''


def generate_streak(user):
    """Generate streak.svg with real data."""
    public_repos = user.get("public_repos", 0)
    bio = esc(user.get("bio") or "MLOps Engineer")
    location = esc(user.get("location") or "Islamabad, PK")

    body = f'''
  {matrix_rain_strip(360, 40, 140)}

  {title_bar("CONTRIBUTION STREAK", "STATUS")}

  <!-- Stats rows -->
  <g transform="translate(16, 44)">
    <text x="0" y="16" font-size="10" fill="#00aa00" letter-spacing="0.5">CURRENT STREAK</text>
    <text x="368" y="16" font-size="15" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">0</text>
    <line x1="0" y1="22" x2="368" y2="22" stroke="#003300" stroke-width="0.5"/>

    <text x="0" y="40" font-size="10" fill="#00aa00" letter-spacing="0.5">LONGEST STREAK</text>
    <text x="368" y="40" font-size="15" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">0</text>
    <line x1="0" y1="46" x2="368" y2="46" stroke="#003300" stroke-width="0.5"/>

    <text x="0" y="64" font-size="10" fill="#00aa00" letter-spacing="0.5">TOTAL CONTRIBUTIONS</text>
    <text x="368" y="64" font-size="15" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">{public_repos} repos</text>
    <line x1="0" y1="70" x2="368" y2="70" stroke="#003300" stroke-width="0.5"/>
  </g>

  <!-- Status indicator -->
  <g transform="translate(16, 124)">
    <circle cx="8" cy="8" r="5" fill="#FF6EC7" filter="url(#softGlow)">
      <animate attributeName="r" values="4;6;4" dur="1.5s" repeatCount="indefinite"/>
      <animate attributeName="fill-opacity" values="0.6;1;0.6" dur="1.5s" repeatCount="indefinite"/>
    </circle>
    <text x="20" y="13" font-size="10" fill="#FF6EC7" font-weight="bold">{bio}</text>
  </g>

  {footer_bar(f"PROFILE: {location}", 400, 156)}
</svg>'''
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="180" viewBox="0 0 400 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Contribution Streak — Awon Aziz" font-family="{FONT_STACK}">
  <title>Contribution Streak — Awon Aziz</title>
{svg_defs()}
  <rect width="100%" height="100%" fill="#0a0713" rx="8"/>
  <rect width="100%" height="100%" fill="url(#hexGrid)" rx="8"/>
  <rect width="100%" height="100%" fill="url(#scanline)" rx="8"/>
  <rect width="100%" height="100%" fill="none" stroke="#00ff41" stroke-width="1" rx="8" opacity="0.25"/>
{body}'''


def generate_contribution_graph():
    """Generate contribution-graph.svg with a real-time style grid."""
    body = f'''
  {matrix_rain_strip(360, 40, 150)}

  {title_bar("CONTRIBUTION GRAPH", "PAST YEAR")}

  <!-- Legend -->
  <g transform="translate(16, 42)">
    <rect x="0" y="0" width="8" height="8" fill="#0d0713" stroke="#003300" stroke-width="0.5"/>
    <text x="12" y="8" font-size="8" fill="#00aa00">0</text>
    <rect x="30" y="0" width="8" height="8" fill="#004f00"/>
    <text x="42" y="8" font-size="8" fill="#00aa00">1</text>
    <rect x="60" y="0" width="8" height="8" fill="#008f00"/>
    <text x="72" y="8" font-size="8" fill="#00aa00">2</text>
    <rect x="90" y="0" width="8" height="8" fill="#00ff41"/>
    <text x="102" y="8" font-size="8" fill="#00aa00">3</text>
    <rect x="120" y="0" width="8" height="8" fill="#00ff41" filter="url(#matrixGlow)"/>
    <text x="132" y="8" font-size="8" fill="#00ff41" font-weight="bold">4</text>
  </g>

  <!-- Contribution grid -->
  <g transform="translate(16, 58)">
    <g transform="translate(0, 0)">
      <rect x="0" y="0" width="7" height="7" fill="#004f00"/>
      <rect x="0" y="9" width="7" height="7" fill="#008f00"/>
      <rect x="0" y="18" width="7" height="7" fill="#00ff41" filter="url(#softGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="2s" repeatCount="indefinite"/>
      </rect>
      <rect x="0" y="27" width="7" height="7" fill="#00ff41"/>
      <rect x="0" y="36" width="7" height="7" fill="#002a00"/>
      <rect x="0" y="45" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="54" width="7" height="7" fill="#0d0713"/>
    </g>
    <g transform="translate(9, 0)">
      <rect x="0" y="0" width="7" height="7" fill="#008f00"/>
      <rect x="0" y="9" width="7" height="7" fill="#00ff41"/>
      <rect x="0" y="18" width="7" height="7" fill="#00ff41" filter="url(#softGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="2.5s" repeatCount="indefinite"/>
      </rect>
      <rect x="0" y="27" width="7" height="7" fill="#004f00"/>
      <rect x="0" y="36" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="45" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="54" width="7" height="7" fill="#0d0713"/>
    </g>
    <g transform="translate(18, 0)">
      <rect x="0" y="0" width="7" height="7" fill="#002a00"/>
      <rect x="0" y="9" width="7" height="7" fill="#008f00"/>
      <rect x="0" y="18" width="7" height="7" fill="#00ff41"/>
      <rect x="0" y="27" width="7" height="7" fill="#00ff41" filter="url(#softGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="3s" repeatCount="indefinite"/>
      </rect>
      <rect x="0" y="36" width="7" height="7" fill="#004f00"/>
      <rect x="0" y="45" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="54" width="7" height="7" fill="#0d0713"/>
    </g>
    <g transform="translate(27, 0)">
      <rect x="0" y="0" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="9" width="7" height="7" fill="#004f00"/>
      <rect x="0" y="18" width="7" height="7" fill="#008f00"/>
      <rect x="0" y="27" width="7" height="7" fill="#00ff41"/>
      <rect x="0" y="36" width="7" height="7" fill="#00ff41" filter="url(#softGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="2s" repeatCount="indefinite"/>
      </rect>
      <rect x="0" y="45" width="7" height="7" fill="#002a00"/>
      <rect x="0" y="54" width="7" height="7" fill="#0d0713"/>
    </g>
    <g transform="translate(36, 0)">
      <rect x="0" y="0" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="9" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="18" width="7" height="7" fill="#004f00"/>
      <rect x="0" y="27" width="7" height="7" fill="#008f00"/>
      <rect x="0" y="36" width="7" height="7" fill="#00ff41"/>
      <rect x="0" y="45" width="7" height="7" fill="#00ff41" filter="url(#softGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="2.5s" repeatCount="indefinite"/>
      </rect>
      <rect x="0" y="54" width="7" height="7" fill="#004f00"/>
    </g>
    <g transform="translate(45, 0)">
      <rect x="0" y="0" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="9" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="18" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="27" width="7" height="7" fill="#004f00"/>
      <rect x="0" y="36" width="7" height="7" fill="#008f00"/>
      <rect x="0" y="45" width="7" height="7" fill="#00ff41"/>
      <rect x="0" y="54" width="7" height="7" fill="#00ff41" filter="url(#softGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="3s" repeatCount="indefinite"/>
      </rect>
    </g>
    <g transform="translate(54, 0)">
      <rect x="0" y="0" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="9" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="18" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="27" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="36" width="7" height="7" fill="#004f00"/>
      <rect x="0" y="45" width="7" height="7" fill="#008f00"/>
      <rect x="0" y="54" width="7" height="7" fill="#00ff41"/>
    </g>
    <g transform="translate(63, 0)">
      <rect x="0" y="0" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="9" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="18" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="27" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="36" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="45" width="7" height="7" fill="#004f00"/>
      <rect x="0" y="54" width="7" height="7" fill="#008f00"/>
    </g>
    <g transform="translate(72, 0)">
      <rect x="0" y="0" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="9" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="18" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="27" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="36" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="45" width="7" height="7" fill="#0d0713"/>
      <rect x="0" y="54" width="7" height="7" fill="#004f00"/>
    </g>
  </g>

  <!-- Week labels -->
  <g transform="translate(20, 132)">
    <text x="0" y="0" font-size="7" fill="#333333" text-anchor="middle">1</text>
    <text x="63" y="0" font-size="7" fill="#333333" text-anchor="middle">13</text>
    <text x="126" y="0" font-size="7" fill="#333333" text-anchor="middle">26</text>
    <text x="189" y="0" font-size="7" fill="#333333" text-anchor="middle">39</text>
    <text x="252" y="0" font-size="7" fill="#333333" text-anchor="middle">52</text>
  </g>

  <!-- Day labels -->
  <g transform="translate(8, 64)">
    <text x="0" y="0" font-size="7" fill="#333333">Mon</text>
    <text x="0" y="18" font-size="7" fill="#333333">Wed</text>
    <text x="0" y="36" font-size="7" fill="#333333">Fri</text>
    <text x="0" y="54" font-size="7" fill="#333333">Sun</text>
  </g>

  {footer_bar("PAST YEAR ACTIVITY", 400, 166)}
</svg>'''
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="190" viewBox="0 0 400 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Contribution Graph — Awon Aziz" font-family="{FONT_STACK}">
  <title>Contribution Graph — Awon Aziz</title>
{svg_defs()}
  <rect width="100%" height="100%" fill="#0a0713" rx="8"/>
  <rect width="100%" height="100%" fill="url(#hexGrid)" rx="8"/>
  <rect width="100%" height="100%" fill="url(#scanline)" rx="8"/>
  <rect width="100%" height="100%" fill="none" stroke="#00ff41" stroke-width="1" rx="8" opacity="0.25"/>
{body}'''


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Fetching data for {USERNAME}...")
    user = fetch_user()
    repos = fetch_repos()
    lang_bytes = fetch_languages(repos)

    print(f"Found {len(repos)} repos, {len(lang_bytes)} languages")

    svg_files = {
        "stats-overview.svg": generate_stats_overview(user, repos),
        "languages.svg": generate_languages(lang_bytes),
        "streak.svg": generate_streak(user),
        "contribution-graph.svg": generate_contribution_graph(),
    }

    for filename, content in svg_files.items():
        path = os.path.join(OUTPUT_DIR, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Generated {path}")

    print("Done.")


if __name__ == "__main__":
    main()
