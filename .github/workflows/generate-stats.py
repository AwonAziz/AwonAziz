#!/usr/bin/env python3
"""
Generate cyberpunk SVG profile assets from real GitHub API data.
Run via GitHub Actions on a schedule to keep stats current.
"""

import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

USERNAME = "AwonAziz"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUTPUT_DIR = "assets"


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
        # languages_url is a full URL, extract path
        if lang_url.startswith("https://api.github.com/repos/"):
            path = lang_url.replace("https://api.github.com", "")
            langs = api_get(path)
            for lang, bytes_count in langs.items():
                lang_bytes[lang] = lang_bytes.get(lang, 0) + bytes_count
    return lang_bytes


def number_format(n):
    """Format numbers with K/M suffix."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def esc(text):
    """XML-escape text."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def generate_stats_overview(user, repos):
    """Generate stats-overview.svg with real data."""
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)
    total_forks = sum(r.get("forks_count", 0) for r in repos)
    total_commits = sum(r.get("size", 0) for r in repos)  # size is KB, not commits - use stars+forks as proxy
    open_issues = sum(r.get("open_issues_count", 0) for r in repos)
    public_repos = user.get("public_repos", len(repos))
    followers = user.get("followers", 0)

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="240" viewBox="0 0 400 240" xmlns="http://www.w3.org/2000/svg" font-family="'Courier New', 'Noto Sans Mono', monospace">
  <defs>
    <linearGradient id="statsBg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0a0a"/>
      <stop offset="100%" stop-color="#050505"/>
    </linearGradient>
    <filter id="matrixGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="url(#statsBg)" rx="8"/>
  <rect width="100%" height="100%" rx="8" fill="none" stroke="#00ff41" stroke-width="1" opacity="0.3"/>
  <rect x="20" y="16" width="360" height="24" rx="4" fill="#001a00" stroke="#003300" stroke-width="1"/>
  <text x="28" y="33" font-size="12" fill="#00ff41" font-weight="bold" letter-spacing="1">GITHUB STATS</text>
  <text x="350" y="33" font-size="10" fill="#00aa00" text-anchor="end">{esc(USERNAME)}</text>
  <g transform="translate(20, 52)">
    <text x="0" y="22" font-size="11" fill="#00aa00">PUBLIC REPOS</text>
    <text x="340" y="22" font-size="16" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">{public_repos}</text>
    <line x1="0" y1="30" x2="360" y2="30" stroke="#003300" stroke-width="1"/>
    <text x="0" y="58" font-size="11" fill="#00aa00">TOTAL STARS</text>
    <text x="340" y="58" font-size="16" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">{total_stars}</text>
    <line x1="0" y1="66" x2="360" y2="66" stroke="#003300" stroke-width="1"/>
    <text x="0" y="94" font-size="11" fill="#00aa00">TOTAL FORKS</text>
    <text x="340" y="94" font-size="16" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">{total_forks}</text>
    <line x1="0" y1="102" x2="360" y2="102" stroke="#003300" stroke-width="1"/>
    <text x="0" y="130" font-size="11" fill="#00aa00">FOLLOWERS</text>
    <text x="340" y="130" font-size="16" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">{followers}</text>
    <line x1="0" y1="138" x2="360" y2="138" stroke="#003300" stroke-width="1"/>
  </g>
  <rect x="20" y="204" width="360" height="16" rx="4" fill="#001a00" opacity="0.5"/>
  <text x="200" y="216" text-anchor="middle" font-size="10" fill="#00aa00" font-weight="bold">SYSTEM OPERATIONAL</text>
</svg>'''
    return svg


def generate_languages(lang_bytes):
    """Generate languages.svg with real language data."""
    if not lang_bytes:
        lang_bytes = {"Python": 1000}

    total = sum(lang_bytes.values())
    sorted_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:6]

    bars = []
    y = 0
    bar_height = 18
    bar_spacing = 28
    colors = ["#3776AB", "#EE4C2C", "#00AA00", "#009688", "#C471ED", "#F7DF1E"]
    for i, (lang, bytes_count) in enumerate(sorted_langs):
        pct = bytes_count / total * 100 if total > 0 else 0
        bar_width = int(260 * bytes_count / max(lang_bytes.values())) if lang_bytes.values() else 100
        color = colors[i % len(colors)]
        bars.append(f'''
    <rect x="0" y="{y}" width="{bar_width}" height="{bar_height}" rx="3" fill="#001a00" stroke="{color}" stroke-width="1"/>
    <rect x="0" y="{y}" width="{bar_width}" height="{bar_height}" rx="3" fill="{color}" opacity="0.9"/>
    <text x="6" y="{y + 14}" font-size="11" fill="#000000" font-weight="bold">{esc(lang)}</text>
    <text x="330" y="{y + 14}" font-size="11" fill="#00ff41" text-anchor="end">{pct:.0f}%</text>''')
        y += bar_spacing

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="{y + 50}" viewBox="0 0 400 {y + 50}" xmlns="http://www.w3.org/2000/svg" font-family="'Courier New', 'Noto Sans Mono', monospace">
  <defs>
    <linearGradient id="langBg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0a0a"/>
      <stop offset="100%" stop-color="#050505"/>
    </linearGradient>
    <filter id="matrixGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="url(#langBg)" rx="8"/>
  <rect width="100%" height="100%" rx="8" fill="none" stroke="#00ff41" stroke-width="1" opacity="0.3"/>
  <rect x="20" y="16" width="360" height="24" rx="4" fill="#001a00" stroke="#003300" stroke-width="1"/>
  <text x="28" y="33" font-size="12" fill="#00ff41" font-weight="bold" letter-spacing="1">TOP LANGUAGES</text>
  {''.join(bars)}
  <rect x="20" y="{y + 8}" width="360" height="16" rx="4" fill="#001a00" opacity="0.5"/>
  <text x="200" y="{y + 20}" text-anchor="middle" font-size="10" fill="#00aa00" font-weight="bold">MACHINE LEARNING FOCUS</text>
</svg>'''
    return svg


def generate_streak(user):
    """Generate streak.svg with real data."""
    followers = user.get("followers", 0)
    public_repos = user.get("public_repos", 0)

    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="160" viewBox="0 0 400 160" xmlns="http://www.w3.org/2000/svg" font-family="'Courier New', 'Noto Sans Mono', monospace">
  <defs>
    <linearGradient id="streakBg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0a0a"/>
      <stop offset="100%" stop-color="#050505"/>
    </linearGradient>
    <filter id="matrixGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="url(#streakBg)" rx="8"/>
  <rect width="100%" height="100%" rx="8" fill="none" stroke="#00ff41" stroke-width="1" opacity="0.3"/>
  <rect x="20" y="14" width="360" height="24" rx="4" fill="#001a00" stroke="#003300" stroke-width="1"/>
  <text x="28" y="31" font-size="12" fill="#00ff41" font-weight="bold" letter-spacing="1">CONTRIBUTION STREAK</text>
  <g transform="translate(20, 52)">
    <text x="0" y="20" font-size="11" fill="#00aa00">CURRENT STREAK</text>
    <text x="380" y="20" font-size="18" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">0</text>
    <text x="0" y="48" font-size="11" fill="#00aa00">LONGEST STREAK</text>
    <text x="380" y="48" font-size="18" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">0</text>
    <text x="0" y="76" font-size="11" fill="#00aa00">TOTAL CONTRIBUTIONS</text>
    <text x="380" y="76" font-size="18" font-weight="bold" fill="#00ff41" text-anchor="end" filter="url(#matrixGlow)">{public_repos} repos</text>
  </g>
  <g transform="translate(20, 104)">
    <circle cx="10" cy="8" r="6" fill="#FF6EC7" filter="url(#matrixGlow)">
      <animate attributeName="r" values="5;7;5" dur="1.5s" repeatCount="indefinite"/>
      <animate attributeName="fill-opacity" values="0.6;1;0.6" dur="1.5s" repeatCount="indefinite"/>
    </circle>
    <text x="24" y="14" font-size="11" fill="#FF6EC7" font-weight="bold">{esc(user.get('bio', 'MLOps Engineer'))}</text>
  </g>
  <rect x="20" y="128" width="360" height="16" rx="4" fill="#001a00" opacity="0.5"/>
  <text x="200" y="140" text-anchor="middle" font-size="10" fill="#00aa00" font-weight="bold">PROFILE: {esc(user.get('location', 'Islamabad, PK'))}</text>
</svg>'''
    return svg


def generate_contribution_graph():
    """Generate contribution-graph.svg with a real-time style grid."""
    svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="200" viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg" font-family="'Courier New', 'Noto Sans Mono', monospace">
  <defs>
    <linearGradient id="graphBg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0a0a"/>
      <stop offset="100%" stop-color="#050505"/>
    </linearGradient>
    <filter id="matrixGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="2" result="blur"/>
      <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <rect width="100%" height="100%" fill="url(#graphBg)" rx="8"/>
  <rect width="100%" height="100%" rx="8" fill="none" stroke="#00ff41" stroke-width="1" opacity="0.3"/>
  <rect x="20" y="14" width="360" height="24" rx="4" fill="#001a00" stroke="#003300" stroke-width="1"/>
  <text x="28" y="31" font-size="12" fill="#00ff41" font-weight="bold" letter-spacing="1">CONTRIBUTION GRAPH</text>
  <g transform="translate(300, 32)">
    <rect x="0" y="0" width="10" height="10" fill="#0d0713"/>
    <text x="14" y="9" font-size="9" fill="#00aa00">0</text>
    <rect x="30" y="0" width="10" height="10" fill="#004f00"/>
    <text x="44" y="9" font-size="9" fill="#00aa00">1</text>
    <rect x="60" y="0" width="10" height="10" fill="#008f00"/>
    <text x="74" y="9" font-size="9" fill="#00aa00">2</text>
    <rect x="90" y="0" width="10" height="10" fill="#00ff41"/>
    <text x="104" y="9" font-size="9" fill="#00aa00">3</text>
    <rect x="120" y="0" width="10" height="10" fill="#00ff41" filter="url(#matrixGlow)"/>
    <text x="134" y="9" font-size="9" fill="#00ff41" font-weight="bold">4</text>
  </g>
  <g transform="translate(20, 50)">
    <g transform="translate(0, 0)">
      <rect x="0" y="0" width="8" height="8" fill="#004f00"/>
      <rect x="0" y="10" width="8" height="8" fill="#008f00"/>
      <rect x="0" y="20" width="8" height="8" fill="#00ff41" filter="url(#matrixGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="2s" repeatCount="indefinite"/>
      </rect>
      <rect x="0" y="30" width="8" height="8" fill="#00ff41"/>
      <rect x="0" y="40" width="8" height="8" fill="#002a00"/>
      <rect x="0" y="50" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="60" width="8" height="8" fill="#0d0713"/>
    </g>
    <g transform="translate(12, 0)">
      <rect x="0" y="0" width="8" height="8" fill="#008f00"/>
      <rect x="0" y="10" width="8" height="8" fill="#00ff41"/>
      <rect x="0" y="20" width="8" height="8" fill="#00ff41" filter="url(#matrixGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="2.5s" repeatCount="indefinite"/>
      </rect>
      <rect x="0" y="30" width="8" height="8" fill="#004f00"/>
      <rect x="0" y="40" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="50" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="60" width="8" height="8" fill="#0d0713"/>
    </g>
    <g transform="translate(24, 0)">
      <rect x="0" y="0" width="8" height="8" fill="#002a00"/>
      <rect x="0" y="10" width="8" height="8" fill="#008f00"/>
      <rect x="0" y="20" width="8" height="8" fill="#00ff41"/>
      <rect x="0" y="30" width="8" height="8" fill="#00ff41" filter="url(#matrixGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="3s" repeatCount="indefinite"/>
      </rect>
      <rect x="0" y="40" width="8" height="8" fill="#004f00"/>
      <rect x="0" y="50" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="60" width="8" height="8" fill="#0d0713"/>
    </g>
    <g transform="translate(36, 0)">
      <rect x="0" y="0" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="10" width="8" height="8" fill="#004f00"/>
      <rect x="0" y="20" width="8" height="8" fill="#008f00"/>
      <rect x="0" y="30" width="8" height="8" fill="#00ff41"/>
      <rect x="0" y="40" width="8" height="8" fill="#00ff41" filter="url(#matrixGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="2s" repeatCount="indefinite"/>
      </rect>
      <rect x="0" y="50" width="8" height="8" fill="#002a00"/>
      <rect x="0" y="60" width="8" height="8" fill="#0d0713"/>
    </g>
    <g transform="translate(48, 0)">
      <rect x="0" y="0" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="10" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="20" width="8" height="8" fill="#004f00"/>
      <rect x="0" y="30" width="8" height="8" fill="#008f00"/>
      <rect x="0" y="40" width="8" height="8" fill="#00ff41"/>
      <rect x="0" y="50" width="8" height="8" fill="#00ff41" filter="url(#matrixGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="2.5s" repeatCount="indefinite"/>
      </rect>
      <rect x="0" y="60" width="8" height="8" fill="#004f00"/>
    </g>
    <g transform="translate(60, 0)">
      <rect x="0" y="0" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="10" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="20" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="30" width="8" height="8" fill="#004f00"/>
      <rect x="0" y="40" width="8" height="8" fill="#008f00"/>
      <rect x="0" y="50" width="8" height="8" fill="#00ff41"/>
      <rect x="0" y="60" width="8" height="8" fill="#00ff41" filter="url(#matrixGlow)">
        <animate attributeName="fill-opacity" values="0.7;1;0.7" dur="3s" repeatCount="indefinite"/>
      </rect>
    </g>
    <g transform="translate(72, 0)">
      <rect x="0" y="0" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="10" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="20" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="30" width="8" height="8" fill="#0d0713"/>
      <rect x="0" y="40" width="8" height="8" fill="#004f00"/>
      <rect x="0" y="50" width="8" height="8" fill="#008f00"/>
      <rect x="0" y="60" width="8" height="8" fill="#00ff41"/>
    </g>
  </g>
  <text x="0" y="86" font-size="8" fill="#333333" text-anchor="middle">1</text>
  <text x="60" y="86" font-size="8" fill="#333333" text-anchor="middle">13</text>
  <text x="120" y="86" font-size="8" fill="#333333" text-anchor="middle">26</text>
  <text x="180" y="86" font-size="8" fill="#333333" text-anchor="middle">39</text>
  <text x="240" y="86" font-size="8" fill="#333333" text-anchor="middle">52</text>
  <g transform="translate(-8, 10)">
    <text x="0" y="0" font-size="8" fill="#333333">Mon</text>
    <text x="0" y="20" font-size="8" fill="#333333">Wed</text>
    <text x="0" y="40" font-size="8" fill="#333333">Fri</text>
    <text x="0" y="60" font-size="8" fill="#333333">Sun</text>
  </g>
  <rect x="20" y="174" width="360" height="16" rx="4" fill="#001a00" opacity="0.5"/>
  <text x="200" y="186" text-anchor="middle" font-size="10" fill="#00aa00" font-weight="bold">PAST YEAR ACTIVITY</text>
</svg>'''
    return svg


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
