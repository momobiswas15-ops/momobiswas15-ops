#!/usr/bin/env python3
"""Generate a repository-hosted SVG timeline from GitHub's public events API."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import urllib.request
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "momobiswas15-ops")
OUTPUT = Path(os.environ.get("OUTPUT", "assets/profile-activity.svg"))
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def api(path: str):
    request = urllib.request.Request(f"https://api.github.com{path}")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if TOKEN:
        request.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(x: int, y: int, value: str, size: int, color: str, weight: int = 400) -> str:
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="{size}px" font-weight="{weight}">{esc(value)}</text>'


def event_summary(event: dict) -> tuple[str, str]:
    event_type = event.get("type", "")
    repo = event.get("repo", {}).get("name", "public repository")
    payload = event.get("payload", {})
    if event_type == "PushEvent":
        count = len(payload.get("commits", [])) or int(payload.get("size", 1))
        return "Pushed code", f"{count} commit{'s' if count != 1 else ''} to {repo}"
    if event_type == "PullRequestEvent":
        action = payload.get("action", "updated")
        return f"{action.title()} pull request", repo
    if event_type == "IssuesEvent":
        action = payload.get("action", "updated")
        return f"{action.title()} issue", repo
    if event_type == "CreateEvent":
        ref_type = payload.get("ref_type", "repository")
        return f"Created {ref_type}", repo
    if event_type == "WatchEvent":
        return "Starred repository", repo
    if event_type == "ForkEvent":
        return "Forked repository", repo
    if event_type == "ReleaseEvent":
        return "Published release", repo
    return "Public GitHub activity", repo


def relative_date(value: str) -> str:
    try:
        when = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return when.strftime("%d %b %Y")
    except (TypeError, ValueError):
        return "recently"


def main() -> None:
    raw_events = api(f"/users/{USERNAME}/events/public?per_page=30")
    supported = {"PushEvent", "PullRequestEvent", "IssuesEvent", "CreateEvent", "WatchEvent", "ForkEvent", "ReleaseEvent"}
    events = [event for event in raw_events if event.get("type") in supported][:5]

    svg = [
        '<svg width="1100" height="390" viewBox="0 0 1100 390" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">',
        '<title id="title">Recent public GitHub activity</title>',
        '<desc id="desc">A repository-hosted timeline of recent public GitHub events for Md Mubaswir Biswas.</desc>',
        '<defs><linearGradient id="bg" x1="0" y1="0" x2="1100" y2="390" gradientUnits="userSpaceOnUse"><stop stop-color="#07111F"/><stop offset="1" stop-color="#111B3A"/></linearGradient><linearGradient id="line" x1="0" y1="0" x2="1100" y2="0"><stop stop-color="#22D3EE"/><stop offset="1" stop-color="#818CF8"/></linearGradient><pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" stroke="#93C5FD" stroke-opacity="0.06"/></pattern></defs>',
        '<rect width="1100" height="390" rx="22" fill="url(#bg)"/><rect width="1100" height="390" rx="22" fill="url(#grid)"/>',
        '<path d="M66 150V330" stroke="url(#line)" stroke-width="3" stroke-linecap="round"/>',
        text(48, 48, "RECENT PUBLIC ACTIVITY", 14, "#67E8F9", 700),
        text(48, 84, "A small log of what is moving on GitHub.", 25, "#F8FAFC", 700),
        text(48, 112, "Refreshed automatically from public GitHub events.", 15, "#94A3B8"),
    ]

    if not events:
        svg.extend([text(92, 196, "No recent public events to display yet.", 16, "#CBD5E1", 600), text(92, 224, "The timeline will fill automatically as public activity appears.", 13, "#94A3B8")])
    else:
        for index, event in enumerate(events):
            y = 154 + index * 37
            title, detail = event_summary(event)
            date = relative_date(event.get("created_at", ""))
            svg.append(f'<circle cx="66" cy="{y - 5}" r="6" fill="#22D3EE" stroke="#A5F3FC" stroke-width="2"/>')
            svg.append(text(92, y, title, 15, "#F8FAFC", 700))
            svg.append(text(300, y, detail, 13, "#CBD5E1"))
            svg.append(text(930, y, date, 12, "#94A3B8"))

    updated = dt.datetime.now(dt.timezone.utc).strftime("%d %b %Y · %H:%M UTC")
    svg.extend([text(48, 365, f"Updated automatically · {updated}", 12, "#64748B"), text(1052, 365, f"github.com/{USERNAME}", 12, "#64748B", 400), "</svg>"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(svg) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
