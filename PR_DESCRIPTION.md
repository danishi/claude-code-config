## Summary
- Add new `izakaya-search` skill that interviews users about party size, budget, and area to search and recommend izakaya/restaurants
- Aggregates review ratings from Tabelog (35%), Google Maps (45%), and Hot Pepper (20%) into a weighted composite score
- Includes fake review (sakura) detection for Google Maps with automatic score adjustment penalties
- Provides reservation links, course info, and Google Maps directions for quick booking
- Includes `format_report.py` for Markdown report generation and `search-guide.md` reference with query templates

## Files added/changed
- `skills/izakaya-search/SKILL.md` - Skill definition with 6-step workflow
- `skills/izakaya-search/.claude-plugin/plugin.json` - Plugin manifest
- `skills/izakaya-search/scripts/format_report.py` - Markdown report formatter
- `skills/izakaya-search/references/search-guide.md` - Search strategy reference
- `.claude-plugin/marketplace.json` - Registered new skill in marketplace
- `.gitignore` - Added `__pycache__/`

## Local testing instructions

### 1. Install the skill

```bash
# Clone the repository and checkout the branch
git clone https://github.com/danishi/claude-code-config.git
cd claude-code-config
git checkout claude/izakaya-search-skill-yIDn3

# Install as a Claude Code plugin (from the repo root)
claude plugin install ./skills/izakaya-search
```

### 2. Test the skill invocation

Once installed, invoke the skill in Claude Code:

```
/izakaya-search
```

Claude will begin the interview workflow:
1. Ask for area/station, party size, and budget
2. Search gourmet sites and Google Maps
3. Present 3-5 recommended restaurants with composite ratings

### 3. Test the format_report.py script

```bash
cat <<'SAMPLE' | python skills/izakaya-search/scripts/format_report.py
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
      "name": "居酒屋テスト",
      "area": "新宿駅東口",
      "nearest_station": "新宿駅",
      "walk_minutes": 3,
      "genre": "居酒屋・和食",
      "budget_min": 3000,
      "budget_max": 5000,
      "hours": "17:00-24:00",
      "holidays": "日曜日",
      "seats": 80,
      "room_types": ["テーブル", "個室"],
      "features": ["飲み放題", "個室"],
      "ratings": {
        "tabelog": { "score": 3.65, "count": 120 },
        "google": { "score": 4.1, "count": 350, "adjusted_score": 3.8 },
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
        "tabelog": "https://tabelog.com/example",
        "google_maps": "https://maps.google.com/example"
      },
      "phone": "03-1234-5678"
    }
  ]
}
SAMPLE
```

**Expected output:** Markdown report with composite rating, adjusted Google Maps score warning (⚠), course info, and links.

### 4. Verify composite score calculation

```bash
python3 -c "
import sys; sys.path.insert(0, 'skills/izakaya-search/scripts')
from format_report import calculate_composite

# Normal case: Google 45%, Tabelog 35%, HotPepper 20%
r = {'google': {'score': 4.1, 'count': 350}, 'tabelog': {'score': 3.65, 'count': 120}, 'hotpepper': {'score': 3.8, 'count': 85}}
print(f'Normal: {calculate_composite(r)}')  # (3.89, 555)

# With adjusted Google score (sakura detected)
r2 = {'google': {'score': 4.5, 'count': 500, 'adjusted_score': 4.0}, 'tabelog': {'score': 3.5, 'count': 100}}
print(f'Adjusted: {calculate_composite(r2)}')  # Uses 4.0 instead of 4.5

# Single source
r3 = {'tabelog': {'score': 3.8, 'count': 200}}
print(f'Single: {calculate_composite(r3)}')  # (3.8, 200)
"
```

## Test plan
- [ ] Run `format_report.py` with sample JSON data and verify Markdown output
- [ ] Verify composite score calculation with various rating combinations
- [ ] Verify adjusted score is used when `adjusted_score` field is present (sakura detection)
- [ ] Confirm skill appears in marketplace via `claude plugin list`
- [ ] Test skill invocation with `/izakaya-search` in Claude Code

https://claude.ai/code/session_015hiFnqtMykiCxUxh3GaDTT
