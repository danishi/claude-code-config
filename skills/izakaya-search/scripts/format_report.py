#!/usr/bin/env python3
"""Format restaurant data into a Markdown comparison report.

Takes collected restaurant data as JSON and generates a formatted
Markdown comparison report with composite ratings and fake review detection.

Usage:
    python format_report.py -i restaurants.json -o report.md
    echo '{"restaurants": [...]}' | python format_report.py -o report.md
    python format_report.py -i data.json --top 3
"""

import argparse
import json
import sys
from typing import Any

# Rating source weights for composite score calculation
WEIGHTS = {
    "google": 0.45,
    "tabelog": 0.35,
    "hotpepper": 0.20,
}

# Fake review penalty cap
MAX_PENALTY = 0.8


def calculate_composite(ratings: dict[str, dict[str, Any]]) -> tuple[float, int]:
    """Calculate weighted composite score from available ratings.

    If a source is missing, its weight is redistributed proportionally
    to the remaining sources. Google Maps scores may be adjusted for
    suspected fake reviews.

    Returns:
        Tuple of (composite_score, total_review_count).
    """
    available = {}
    total_reviews = 0

    for source, weight in WEIGHTS.items():
        if source in ratings and ratings[source].get("score") is not None:
            available[source] = weight
            total_reviews += ratings[source].get("count", 0)

    if not available:
        return 0.0, 0

    weight_sum = sum(available.values())
    composite = 0.0
    for source, weight in available.items():
        normalized_weight = weight / weight_sum
        score = ratings[source].get("adjusted_score", ratings[source]["score"])
        composite += score * normalized_weight

    return round(composite, 2), total_reviews


def format_markdown(restaurants: list[dict], search_params: dict | None) -> str:
    """Generate a Markdown comparison report."""
    lines = []

    lines.append("# 居酒屋・飲食店 検索結果レポート")
    lines.append("")

    # Search parameters summary
    if search_params:
        lines.append("## 検索条件")
        lines.append("")

        param_labels = {
            "area": "エリア",
            "party_size": "人数",
            "budget_min": "予算下限",
            "budget_max": "予算上限",
            "preferences": "こだわり条件",
        }

        for key, label in param_labels.items():
            if key in search_params:
                value = search_params[key]
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                if key in ("budget_min", "budget_max") and isinstance(value, (int, float)):
                    value = f"{value:,.0f}円"
                if key == "party_size":
                    value = f"{value}名"
                lines.append(f"- **{label}:** {value}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Restaurant entries
    for rank, r in enumerate(restaurants, 1):
        composite, total_reviews = calculate_composite(r.get("ratings", {}))

        lines.append(f"## {rank}. {r['name']}")
        lines.append("")
        lines.append(f"**総合評価: {composite}/5.00** ({total_reviews}件の口コミ)")
        lines.append("")

        # Ratings table
        lines.append("| サイト | 評価 | 口コミ数 | 備考 |")
        lines.append("|---|---|---|---|")

        source_names = {
            "google": "Google Maps",
            "tabelog": "食べログ",
            "hotpepper": "ホットペッパー",
        }

        ratings = r.get("ratings", {})
        for source_key, display_name in source_names.items():
            if source_key in ratings:
                info = ratings[source_key]
                score = info.get("score", "-")
                count = info.get("count", "-")
                note = ""
                if source_key == "google" and info.get("adjusted_score") is not None:
                    adj = info["adjusted_score"]
                    note = f"⚠ 調整済 ({score} → {adj})"
                    score = adj
                lines.append(f"| {display_name} | {score}/5.0 | {count} | {note} |")
            else:
                lines.append(f"| {display_name} | - | - | |")
        lines.append("")

        # Basic info
        if r.get("genre"):
            lines.append(f"- **ジャンル:** {r['genre']}")

        area_parts = []
        if r.get("area"):
            area_parts.append(r["area"])
        if r.get("nearest_station"):
            station = r["nearest_station"]
            walk = r.get("walk_minutes", "")
            walk_str = f" 徒歩{walk}分" if walk else ""
            area_parts.append(f"{station}{walk_str}")
        if area_parts:
            lines.append(f"- **アクセス:** {' / '.join(area_parts)}")

        if r.get("budget_min") is not None or r.get("budget_max") is not None:
            bmin = f"{r['budget_min']:,.0f}" if r.get("budget_min") is not None else "?"
            bmax = f"{r['budget_max']:,.0f}" if r.get("budget_max") is not None else "?"
            lines.append(f"- **予算:** {bmin}-{bmax}円/人")

        if r.get("hours"):
            lines.append(f"- **営業時間:** {r['hours']}")

        if r.get("holidays"):
            lines.append(f"- **定休日:** {r['holidays']}")

        if r.get("seats"):
            seat_str = f"{r['seats']}席"
            if r.get("room_types"):
                seat_str += f" ({', '.join(r['room_types'])})"
            lines.append(f"- **席数:** {seat_str}")

        if r.get("features"):
            lines.append(f"- **特徴:** {', '.join(r['features'])}")

        lines.append("")

        # Courses
        courses = r.get("courses", [])
        if courses:
            lines.append("### おすすめコース")
            lines.append("")
            lines.append("| コース名 | 料金 | 時間 | 内容 |")
            lines.append("|---|---|---|---|")
            for c in courses:
                price = f"{c['price']:,.0f}円" if c.get("price") else "-"
                lines.append(f"| {c.get('name', '-')} | {price} | "
                              f"{c.get('duration', '-')} | {c.get('includes', '-')} |")
            lines.append("")

        # Links
        urls = r.get("urls", {})
        phone = r.get("phone")
        if urls or phone:
            lines.append("### リンク")
            lines.append("")
            if urls.get("tabelog"):
                lines.append(f"- [食べログ]({urls['tabelog']})")
            if urls.get("hotpepper"):
                lines.append(f"- [ホットペッパー]({urls['hotpepper']})")
            if urls.get("google_maps"):
                lines.append(f"- [Google Maps]({urls['google_maps']})")
            if urls.get("reservation_tabelog"):
                lines.append(f"- [食べログで予約]({urls['reservation_tabelog']})")
            if urls.get("reservation_hotpepper"):
                lines.append(f"- [ホットペッパーで予約]({urls['reservation_hotpepper']})")
            if phone:
                lines.append(f"- [電話で予約](tel:{phone}) (`{phone}`)")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def sort_restaurants(restaurants: list[dict], sort_field: str) -> list[dict]:
    """Sort restaurants by the specified field (descending)."""
    def sort_key(r: dict) -> float:
        if sort_field == "composite":
            score, _ = calculate_composite(r.get("ratings", {}))
            return score
        elif sort_field in ("tabelog", "google", "hotpepper"):
            return r.get("ratings", {}).get(sort_field, {}).get("score", 0)
        elif sort_field == "budget":
            return -(r.get("budget_min", 0) or 0)
        return 0

    return sorted(restaurants, key=sort_key, reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Format restaurant data into a Markdown comparison report."
    )
    parser.add_argument(
        "-i", "--input",
        help="Input JSON file with restaurant data (default: stdin)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of top restaurants to include (default: 5)",
    )
    parser.add_argument(
        "--sort",
        choices=["composite", "tabelog", "google", "budget"],
        default="composite",
        help="Sort by field (default: composite)",
    )
    args = parser.parse_args()

    # Read input
    if args.input:
        with open(args.input, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    restaurants = data.get("restaurants", [])
    search_params = data.get("search_params")

    # Sort and limit
    restaurants = sort_restaurants(restaurants, args.sort)
    restaurants = restaurants[: args.top]

    # Format output
    output = format_markdown(restaurants, search_params)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
