#!/usr/bin/env python3
"""Generate a reliable, repository-hosted SVG dashboard from GitHub's public API."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import urllib.request
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "momobiswas15-ops")
OUTPUT = Path(os.environ.get("OUTPUT", "assets/profile-stats.svg"))
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def api(path: str):
    request = urllib.request.Request(f"https://api.github.com{path}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        request.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def short_number(value: int) -> str:
    if value >= 1000:
        return f"{value / 1000:.1f}k"
    return str(value)


def text(x: int, y: int, value: str, size: int, color: str, weight: int = 400, anchor: str = "start") -> str:
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="{size}px" font-weight="{weight}" text-anchor="{anchor}">{esc(value)}</text>'


def main() -> None:
    user = api(f"/users/{USERNAME}")
    repos = api(f"/users/{USERNAME}/repos?per_page=100&sort=updated")

    stars = sum(int(repo.get("stargazers_count", 0)) for repo in repos)
    updated = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y · %H:%M UTC")

    metrics = [
        ("PUBLIC REPOS", short_number(int(user.get("public_repos", 0))), "visible projects"),
        ("STARS EARNED", short_number(stars), "across repositories"),
        ("FOLLOWERS", short_number(int(user.get("followers", 0))), "people following"),
        ("FOLLOWING", short_number(int(user.get("following", 0))), "developers followed"),
    ]

    colors = ["#22D3EE", "#818CF8", "#38BDF8", "#A78BFA"]
    svg = [
        '<svg width="1100" height="330" viewBox="0 0 1100 330" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">',
        '<title id="title">Live GitHub dashboard for Md Mubaswir Biswas</title>',
        '<desc id="desc">A repository-hosted dashboard showing public repositories, stars, followers, and developers followed.</desc>',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1100" y2="330" gradientUnits="userSpaceOnUse"><stop stop-color="#07111F"/><stop offset="1" stop-color="#102A43"/></linearGradient><linearGradient id="line" x1="0" y1="0" x2="1100" y2="0"><stop stop-color="#22D3EE"/><stop offset="1" stop-color="#818CF8"/></linearGradient><pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" stroke="#93C5FD" stroke-opacity="0.07"/></pattern></defs>',
        '<rect width="1100" height="330" rx="22" fill="url(#bg)"/><rect width="1100" height="330" rx="22" fill="url(#grid)"/>',
        '<path d="M0 285C190 250 320 305 470 266C650 219 745 93 1100 145" stroke="url(#line)" stroke-opacity="0.32" stroke-width="2"/>',
        text(48, 58, "LIVE GITHUB DASHBOARD", 14, "#67E8F9", 700),
        text(48, 95, "Public activity, kept simple.", 27, "#F8FAFC", 700),
        text(48, 124, "A fresh snapshot of the work visible on this profile.", 15, "#94A3B8", 400),
    ]

    card_x = [48, 302, 556, 810]
    for index, ((label, value, note), x) in enumerate(zip(metrics, card_x)):
        color = colors[index]
        svg.append(f'<rect x="{x}" y="168" width="226" height="94" rx="14" fill="#0B172A" fill-opacity="0.78" stroke="#334155" stroke-opacity="0.7"/>')
        svg.append(f'<rect x="{x}" y="168" width="226" height="4" rx="2" fill="{color}"/>')
        svg.append(text(x + 18, 194, label, 11, "#94A3B8", 700))
        svg.append(text(x + 18, 225, value, 25, "#F8FAFC", 700))
        svg.append(text(x + 18, 247, note, 11, "#CBD5E1", 400))

    svg.extend([
        text(48, 303, f"Updated automatically · {updated}", 12, "#64748B", 400),
        text(1052, 303, f"github.com/{USERNAME}", 12, "#64748B", 400, "end"),
        "</svg>",
    ])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(svg) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
