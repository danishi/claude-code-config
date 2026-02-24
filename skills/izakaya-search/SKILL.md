---
name: izakaya-search
description: >
  Search and recommend izakaya (Japanese-style pubs) and restaurants
  based on party size, budget, area, and additional preferences.
  Aggregates reviews from gourmet sites (Tabelog, Hot Pepper Gourmet, Gurunavi)
  and Google Maps, calculates composite ratings, and provides
  reservation links and Google Maps directions for quick booking.
---

# Izakaya Search - Japanese Restaurant Recommendation Skill

Interactively find the best izakaya and restaurants by hearing the user's
requirements and searching gourmet sites and Google Maps.

---

## Workflow

### Step 1: Interview the user

Ask the user the following questions using the `AskUserQuestion` tool.
Gather all required information before searching. If any additional context
is provided by the user (e.g., "quiet atmosphere", "private rooms",
"all-you-can-drink"), incorporate it into the search.

#### Required information

| Item | Question example | Notes |
|---|---|---|
| **Area / location** | "Which area or station are you looking for?" | Accept station names, city names, or landmarks |
| **Party size** | "How many people?" | Important for seat/room availability |
| **Budget per person** | "What is your budget per person?" | Accept ranges like "3,000-5,000 yen" |

#### Optional information (ask if not already provided)

| Item | Question example | Notes |
|---|---|---|
| **Date and time** | "When are you planning to go?" | Affects availability and course options |
| **Cuisine preferences** | "Any preferred cuisine type?" | e.g., Japanese, seafood, yakitori, Korean, etc. |
| **Must-have features** | "Any requirements?" | e.g., private rooms, smoking/non-smoking, all-you-can-drink, accessibility |
| **Occasion** | "What is the occasion?" | e.g., casual drinks, welcome/farewell party, date, business dinner |

### Step 2: Search for restaurants

Use `WebSearch` to search across multiple gourmet platforms. Execute
multiple searches in parallel when possible for efficiency.

#### Search queries to execute

Build search queries combining the user's requirements. Always search
at least these sources:

1. **Tabelog (食べログ)**
   ```
   "食べログ {area} 居酒屋 {cuisine} {features}"
   ```

2. **Hot Pepper Gourmet (ホットペッパーグルメ)**
   ```
   "ホットペッパー {area} 居酒屋 {party_size}名 {budget}"
   ```

3. **Gurunavi (ぐるなび)**
   ```
   "ぐるなび {area} 居酒屋 {features} {cuisine}"
   ```

4. **Google Maps**
   ```
   "Google Maps {area} 居酒屋 {cuisine} 口コミ"
   ```

#### Search strategy

- Run 3-5 parallel `WebSearch` calls with different query variations
- Include budget and party size keywords in queries
- Add optional preferences (private room, all-you-can-drink, etc.)
- Search for specific course/plan information when budget is specified
- If initial results are insufficient, refine queries and search again

### Step 3: Gather detailed information

Use `WebFetch` to visit the top candidate restaurant pages and collect:

- Restaurant name and address
- Business hours and regular holidays
- Review ratings from each source
- Course menus and pricing
- Seat count and room types (counter, table, private room, tatami)
- Reservation availability
- Direct reservation page URLs
- Notable features (all-you-can-drink plans, smoking policy, etc.)

### Step 4: Calculate composite review ratings

Compute a weighted composite score from available review sources:

| Source | Weight | Score range | Notes |
|---|---|---|---|
| Tabelog | 40% | 1.0 - 5.0 | Most trusted for food quality in Japan |
| Google Maps | 35% | 1.0 - 5.0 | Reflects general customer satisfaction |
| Hot Pepper / Gurunavi | 25% | 1.0 - 5.0 | Useful for atmosphere and service |

**Composite score formula:**

```
composite = (tabelog * 0.40) + (google * 0.35) + (hotpepper_or_gurunavi * 0.25)
```

- If a source is unavailable, redistribute its weight proportionally
  to the remaining sources
- Example: If only Tabelog (3.8) and Google (4.2) are available:
  - Tabelog weight: 0.40 / (0.40 + 0.35) = 0.533
  - Google weight: 0.35 / (0.40 + 0.35) = 0.467
  - Composite: (3.8 * 0.533) + (4.2 * 0.467) = 3.987
- Display scores rounded to 2 decimal places
- Include the number of reviews from each source when available

### Step 5: Format and present results

Use `scripts/format_report.py` to generate a formatted comparison report,
or format the results directly as follows.

Present **3 to 5 recommended restaurants** in the following format:

---

#### Recommendation output format

For each restaurant, present:

```markdown
## {rank}. {restaurant_name}

**Composite Rating: {composite_score}/5.00** ({total_reviews} reviews)

| Source | Rating | Reviews |
|---|---|---|
| Tabelog | {score}/5.0 | {count} reviews |
| Google Maps | {score}/5.0 | {count} reviews |
| Hot Pepper | {score}/5.0 | {count} reviews |

- **Genre:** {cuisine_type}
- **Area:** {area} ({nearest_station}, {walk_minutes} min walk)
- **Budget:** {budget_range} per person
- **Hours:** {business_hours}
- **Regular holiday:** {holidays}
- **Seats:** {seat_count} seats ({room_types})
- **Features:** {features}

### Recommended courses

| Course name | Price | Duration | Includes |
|---|---|---|---|
| {course_name} | {price} | {duration} | {description} |

### Quick links

- [Tabelog page]({tabelog_url})
- [Hot Pepper page]({hotpepper_url})
- [Google Maps]({google_maps_url})
- [Reserve on Tabelog]({tabelog_reservation_url})
- [Reserve on Hot Pepper]({hotpepper_reservation_url})
- [Call to reserve](tel:{phone_number})
```

---

### Step 6: Assist with reservation

After presenting results, ask the user:

- "Would you like more details about any of these restaurants?"
- "Shall I search for more options with different criteria?"
- "Would you like help narrowing down the choice?"

If the user selects a restaurant, provide:

1. Direct reservation page links (one-click access)
2. Phone number for telephone reservations
3. Google Maps link for directions
4. Recommended course based on their budget and party size

---

## Scripts

### `scripts/format_report.py` - Restaurant comparison report generator

Takes collected restaurant data as JSON and generates a formatted
Markdown comparison report.

#### Usage

```bash
python scripts/format_report.py -i restaurants.json -o report.md
```

#### From stdin (piped JSON)

```bash
echo '{"restaurants": [...]}' | python scripts/format_report.py -o report.md
```

#### Full options

```
usage: format_report.py [-h] [-i INPUT] [-o OUTPUT] [--format FORMAT]
                         [--top N] [--sort FIELD] [--lang LANG]

Options:
  -i, --input PATH    Input JSON file with restaurant data (default: stdin)
  -o, --output PATH   Output file path (default: stdout)
  --format FORMAT     Output format: markdown, csv, json (default: markdown)
  --top N             Number of top restaurants to include (default: 5)
  --sort FIELD        Sort by: composite, tabelog, google, budget (default: composite)
  --lang LANG         Output language: ja, en (default: ja)
```

#### Input JSON schema

```json
{
  "search_params": {
    "area": "新宿",
    "party_size": 6,
    "budget_min": 3000,
    "budget_max": 5000,
    "preferences": ["個室", "飲み放題"]
  },
  "restaurants": [
    {
      "name": "居酒屋 Example",
      "area": "新宿駅東口",
      "nearest_station": "新宿駅",
      "walk_minutes": 3,
      "genre": "居酒屋・和食",
      "budget_min": 3000,
      "budget_max": 5000,
      "hours": "17:00-24:00",
      "holidays": "日曜日",
      "seats": 80,
      "room_types": ["テーブル", "個室", "掘りごたつ"],
      "features": ["飲み放題", "個室", "禁煙"],
      "ratings": {
        "tabelog": { "score": 3.65, "count": 120 },
        "google": { "score": 4.1, "count": 350 },
        "hotpepper": { "score": 3.8, "count": 85 }
      },
      "courses": [
        {
          "name": "宴会コース",
          "price": 4000,
          "duration": "2.5h",
          "includes": "飲み放題付き 全8品"
        }
      ],
      "urls": {
        "tabelog": "https://tabelog.com/...",
        "hotpepper": "https://www.hotpepper.jp/...",
        "google_maps": "https://maps.google.com/...",
        "reservation_tabelog": "https://tabelog.com/.../reserve",
        "reservation_hotpepper": "https://www.hotpepper.jp/.../reserve"
      },
      "phone": "03-XXXX-XXXX"
    }
  ]
}
```

---

## Tips for Effective Searching

- **Area specificity matters:** "新宿駅東口" yields better results than "新宿"
- **Include occasion context:** Searching "歓送迎会" or "女子会" gives targeted results
- **Budget keywords help:** Include "3000円" or "飲み放題付き" to filter results
- **Verify recency:** Check that business hours and holiday info are current
- **Cross-reference ratings:** A restaurant with high ratings on both Tabelog and
  Google Maps is more reliably good than one with a high score on only one platform

See `references/search-guide.md` for a comprehensive search strategy reference.

---

## Error Handling

| Issue | Solution |
|---|---|
| No results found for area | Broaden the area (e.g., "新宿" instead of "新宿三丁目") |
| Budget too restrictive | Suggest adjusting budget range or removing course requirement |
| No reviews available | Note this to the user; rely on other available sources |
| Restaurant page unavailable | Try alternative gourmet site URLs |
| Outdated information suspected | Warn the user and suggest calling to confirm |
| All-you-can-drink not available | Suggest alternative plans or nearby options that offer it |
