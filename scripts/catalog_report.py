#!/usr/bin/env python3
"""Print a transparent inventory summary for the SniffleShop source."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", default="source.json")
    parser.add_argument("--stale-days", type=int, default=365)
    args = parser.parse_args()

    source = json.loads(Path(args.source).read_text(encoding="utf-8"))
    apps = source.get("apps", [])
    versions = [(app, version) for app in apps for version in app.get("versions", [])]
    categories = Counter(app.get("category", "(uncategorized)") for app in apps)
    missing_min_os = sorted(app["name"] for app, version in versions if not version.get("minOSVersion"))
    now = datetime.now(timezone.utc)
    stale = []
    for app, version in versions:
        raw_date = version.get("date")
        if not raw_date:
            continue
        try:
            parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue  # The validator reports malformed dates.
        age = (now - parsed.astimezone(timezone.utc)).days
        if age > args.stale_days:
            stale.append((app["name"], version.get("version", "?"), raw_date, age))

    print(f'{source.get("name", "Source")}: {len(apps)} apps, {len(versions)} IPA builds')
    print("Categories:")
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count}")
    print(f"Builds without minOSVersion: {len(missing_min_os)}")
    for name in missing_min_os:
        print(f"  - {name}")
    print(f"Builds older than {args.stale_days} days: {len(stale)}")
    for name, version, released, age in sorted(stale, key=lambda row: row[3], reverse=True):
        print(f"  - {name} {version}: {released} ({age} days old)")
    print("Age is a review signal, not proof that a release is broken or unsupported.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
