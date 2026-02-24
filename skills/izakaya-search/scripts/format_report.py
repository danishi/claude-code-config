#!/usr/bin/env python3
"""Format restaurant data into a comparison report.

Takes collected restaurant data as JSON and generates a formatted
Markdown, CSV, or JSON comparison report with composite ratings.

Usage:
    python format_report.py -i restaurants.json -o report.md
    echo '{"restaurants": [...]}' | python format_report.py -o report.md
    python format_report.py -i data.json --format csv --top 3
"""

import argparse
import csv
import io
import json
import sys
from typing import Any

# Rating source weights for composite score calculation
WEIGHTS = {
    "tabelog": 0.40,
    "google": 0.35,
    "hotpepper": 0.25,
}


def calculate_composite(ratings: dict[str, dict[str, Any]]) -> tuple[float, int]:
    """Calculate weighted composite score from available ratings.

    If a source is missing, its weight is redistributed proportionally
    to the remaining sources.

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
        composite += ratings[source]["score"] * normalized_weight

    return round(composite, 2), total_reviews


def format_markdown(restaurants: list[dict], search_params: dict | None, lang: str) -> str:
    """Generate a Markdown comparison report."""
    lines = []

    # Header
    if lang == "ja":
        lines.append("# 居酒屋・飲食店 検索結果レポート")
    else:
        lines.append("# Restaurant Search Results Report")

    lines.append("")

    # Search parameters summary
    if search_params:
        if lang == "ja":
            lines.append("## 検索条件")
        else:
            lines.append("## Search Criteria")
        lines.append("")

        param_labels_ja = {
            "area": "エリア",
            "party_size": "人数",
            "budget_min": "予算下限",
            "budget_max": "予算上限",
            "preferences": "こだわり条件",
        }
        param_labels_en = {
            "area": "Area",
            "party_size": "Party size",
            "budget_min": "Min budget",
            "budget_max": "Max budget",
            "preferences": "Preferences",
        }
        labels = param_labels_ja if lang == "ja" else param_labels_en

        for key, label in labels.items():
            if key in search_params:
                value = search_params[key]
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                if key in ("budget_min", "budget_max") and isinstance(value, (int, float)):
                    value = f"{value:,.0f} {'円' if lang == 'ja' else 'yen'}"
                if key == "party_size":
                    value = f"{value} {'名' if lang == 'ja' else 'people'}"
                lines.append(f"- **{label}:** {value}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Restaurant entries
    for rank, r in enumerate(restaurants, 1):
        composite, total_reviews = calculate_composite(r.get("ratings", {}))

        lines.append(f"## {rank}. {r['name']}")
        lines.append("")

        review_label = "件の口コミ" if lang == "ja" else " reviews"
        lines.append(f"**{'総合評価' if lang == 'ja' else 'Composite Rating'}: "
                      f"{composite}/5.00** ({total_reviews}{review_label})")
        lines.append("")

        # Ratings table
        source_label = "サイト" if lang == "ja" else "Source"
        rating_label = "評価" if lang == "ja" else "Rating"
        count_label = "口コミ数" if lang == "ja" else "Reviews"

        lines.append(f"| {source_label} | {rating_label} | {count_label} |")
        lines.append("|---|---|---|")

        source_names = {
            "tabelog": "食べログ" if lang == "ja" else "Tabelog",
            "google": "Google Maps",
            "hotpepper": "ホットペッパー" if lang == "ja" else "Hot Pepper",
        }

        ratings = r.get("ratings", {})
        for source_key, display_name in source_names.items():
            if source_key in ratings:
                score = ratings[source_key].get("score", "-")
                count = ratings[source_key].get("count", "-")
                lines.append(f"| {display_name} | {score}/5.0 | {count} |")
            else:
                lines.append(f"| {display_name} | - | - |")
        lines.append("")

        # Basic info
        info_items = []
        if r.get("genre"):
            info_items.append(f"- **{'ジャンル' if lang == 'ja' else 'Genre'}:** {r['genre']}")

        area_parts = []
        if r.get("area"):
            area_parts.append(r["area"])
        if r.get("nearest_station"):
            station = r["nearest_station"]
            walk = r.get("walk_minutes", "")
            walk_str = f" {'徒歩' if lang == 'ja' else ''}{walk}{'分' if lang == 'ja' else ' min walk'}" if walk else ""
            area_parts.append(f"{station}{walk_str}")
        if area_parts:
            info_items.append(f"- **{'アクセス' if lang == 'ja' else 'Location'}:** "
                              f"{' / '.join(area_parts)}")

        if r.get("budget_min") is not None or r.get("budget_max") is not None:
            bmin = f"{r['budget_min']:,.0f}" if r.get("budget_min") is not None else "?"
            bmax = f"{r['budget_max']:,.0f}" if r.get("budget_max") is not None else "?"
            yen = "円/人" if lang == "ja" else " yen/person"
            info_items.append(f"- **{'予算' if lang == 'ja' else 'Budget'}:** {bmin}-{bmax}{yen}")

        if r.get("hours"):
            info_items.append(f"- **{'営業時間' if lang == 'ja' else 'Hours'}:** {r['hours']}")

        if r.get("holidays"):
            info_items.append(f"- **{'定休日' if lang == 'ja' else 'Regular holiday'}:** {r['holidays']}")

        if r.get("seats"):
            seat_str = f"{r['seats']}{'席' if lang == 'ja' else ' seats'}"
            if r.get("room_types"):
                seat_str += f" ({', '.join(r['room_types'])})"
            info_items.append(f"- **{'席数' if lang == 'ja' else 'Seats'}:** {seat_str}")

        if r.get("features"):
            info_items.append(f"- **{'特徴' if lang == 'ja' else 'Features'}:** "
                              f"{', '.join(r['features'])}")

        lines.extend(info_items)
        lines.append("")

        # Courses
        courses = r.get("courses", [])
        if courses:
            lines.append(f"### {'おすすめコース' if lang == 'ja' else 'Recommended Courses'}")
            lines.append("")

            c_name = "コース名" if lang == "ja" else "Course"
            c_price = "料金" if lang == "ja" else "Price"
            c_dur = "時間" if lang == "ja" else "Duration"
            c_inc = "内容" if lang == "ja" else "Includes"

            lines.append(f"| {c_name} | {c_price} | {c_dur} | {c_inc} |")
            lines.append("|---|---|---|---|")
            for c in courses:
                price = f"{c['price']:,.0f}{'円' if lang == 'ja' else ' yen'}" if c.get("price") else "-"
                lines.append(f"| {c.get('name', '-')} | {price} | "
                              f"{c.get('duration', '-')} | {c.get('includes', '-')} |")
            lines.append("")

        # Links
        urls = r.get("urls", {})
        phone = r.get("phone")
        if urls or phone:
            lines.append(f"### {'リンク' if lang == 'ja' else 'Quick Links'}")
            lines.append("")
            if urls.get("tabelog"):
                lines.append(f"- [{'食べログ' if lang == 'ja' else 'Tabelog'}]({urls['tabelog']})")
            if urls.get("hotpepper"):
                lines.append(f"- [{'ホットペッパー' if lang == 'ja' else 'Hot Pepper'}]({urls['hotpepper']})")
            if urls.get("google_maps"):
                lines.append(f"- [Google Maps]({urls['google_maps']})")
            if urls.get("reservation_tabelog"):
                label = "食べログで予約" if lang == "ja" else "Reserve on Tabelog"
                lines.append(f"- [{label}]({urls['reservation_tabelog']})")
            if urls.get("reservation_hotpepper"):
                label = "ホットペッパーで予約" if lang == "ja" else "Reserve on Hot Pepper"
                lines.append(f"- [{label}]({urls['reservation_hotpepper']})")
            if phone:
                label = "電話で予約" if lang == "ja" else "Call to reserve"
                lines.append(f"- [{label}](tel:{phone}) (`{phone}`)")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def format_csv(restaurants: list[dict]) -> str:
    """Generate a CSV comparison report."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Rank", "Name", "Area", "Genre", "Composite", "Tabelog",
        "Google", "HotPepper", "Budget Min", "Budget Max",
        "Seats", "Features", "Tabelog URL", "HotPepper URL",
        "Google Maps URL", "Phone",
    ])

    for rank, r in enumerate(restaurants, 1):
        composite, _ = calculate_composite(r.get("ratings", {}))
        ratings = r.get("ratings", {})
        urls = r.get("urls", {})
        writer.writerow([
            rank,
            r.get("name", ""),
            r.get("area", ""),
            r.get("genre", ""),
            composite,
            ratings.get("tabelog", {}).get("score", ""),
            ratings.get("google", {}).get("score", ""),
            ratings.get("hotpepper", {}).get("score", ""),
            r.get("budget_min", ""),
            r.get("budget_max", ""),
            r.get("seats", ""),
            ", ".join(r.get("features", [])),
            urls.get("tabelog", ""),
            urls.get("hotpepper", ""),
            urls.get("google_maps", ""),
            r.get("phone", ""),
        ])

    return output.getvalue()


def format_json(restaurants: list[dict], search_params: dict | None) -> str:
    """Generate a JSON report with composite scores added."""
    result = []
    for rank, r in enumerate(restaurants, 1):
        composite, total_reviews = calculate_composite(r.get("ratings", {}))
        entry = {
            "rank": rank,
            "composite_score": composite,
            "total_reviews": total_reviews,
            **r,
        }
        result.append(entry)

    output = {
        "search_params": search_params,
        "results": result,
    }
    return json.dumps(output, ensure_ascii=False, indent=2)


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
        description="Format restaurant data into a comparison report."
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
        "--format",
        choices=["markdown", "csv", "json"],
        default="markdown",
        help="Output format (default: markdown)",
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
    parser.add_argument(
        "--lang",
        choices=["ja", "en"],
        default="ja",
        help="Output language (default: ja)",
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
    if args.format == "markdown":
        output = format_markdown(restaurants, search_params, args.lang)
    elif args.format == "csv":
        output = format_csv(restaurants)
    elif args.format == "json":
        output = format_json(restaurants, search_params)
    else:
        output = format_markdown(restaurants, search_params, args.lang)

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
