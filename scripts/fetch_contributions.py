"""
fetch_contributions.py
Pulls the public contribution calendar HTML fragment GitHub serves at
/users/<username>/contributions (the same one the profile page uses)
— no GraphQL API, no personal access token needed.

Usage:
    python scripts/fetch_contributions.py [username]
Output:
    data/contributions.json
"""
import json
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DEFAULT_USERNAME = "sujalshindesource"
URL_TMPL = "https://github.com/users/{username}/contributions"


def fetch(username: str) -> dict:
    resp = requests.get(
        URL_TMPL.format(username=username),
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
        timeout=20,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    days = []
    for td in soup.select("td.ContributionCalendar-day"):
        date = td.get("data-date")
        level = td.get("data-level")
        if date is None or level is None:
            continue
        days.append({"date": date, "level": int(level)})

    # Fallback selector for markup variants (older <rect> based calendar)
    if not days:
        for rect in soup.select("rect.ContributionCalendar-day"):
            date = rect.get("data-date")
            level = rect.get("data-level")
            if date is None or level is None:
                continue
            days.append({"date": date, "level": int(level)})

    days.sort(key=lambda d: d["date"])

    total = 0
    counts_tag = soup.select_one(".js-yearly-contributions h2")
    if counts_tag:
        digits = "".join(ch for ch in counts_tag.get_text() if ch.isdigit())
        if digits:
            total = int(digits)

    streak = longest = 0
    current_streak = 0
    best_day = {"date": None, "level": 0}
    monthly = {}
    today = datetime.utcnow().date()

    for d in days:
        lvl = d["level"]
        if lvl > best_day["level"]:
            best_day = {"date": d["date"], "level": lvl}
        month_key = d["date"][:7]
        monthly[month_key] = monthly.get(month_key, 0) + (1 if lvl > 0 else 0)

        if lvl > 0:
            current_streak += 1
            longest = max(longest, current_streak)
        else:
            current_streak = 0

    # Trailing streak counted from the most recent day backwards
    trailing = 0
    for d in reversed(days):
        if datetime.strptime(d["date"], "%Y-%m-%d").date() > today:
            continue
        if d["level"] > 0:
            trailing += 1
        else:
            break
    streak = trailing

    return {
        "username": username,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "total_contributions": total,
        "current_streak": streak,
        "longest_streak": longest,
        "best_day": best_day,
        "monthly": monthly,
        "days": days,
    }


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_USERNAME
    data = fetch(username)
    out_path = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2))
    print(f"Wrote {out_path}: {len(data['days'])} days, "
          f"{data['total_contributions']} total contributions, "
          f"streak {data['current_streak']}")
