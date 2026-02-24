# Izakaya Search Guide - Effective Search Strategies

## Search Query Templates

### By occasion

| Occasion | Japanese keyword | Query example |
|---|---|---|
| Casual drinks | 飲み会 | `{area} 居酒屋 飲み会 {人数}名` |
| Welcome/farewell party | 歓送迎会 | `{area} 歓送迎会 コース 飲み放題` |
| Year-end party | 忘年会 | `{area} 忘年会 プラン {予算}円` |
| New year party | 新年会 | `{area} 新年会 コース {人数}名` |
| Date | デート | `{area} デート 居酒屋 個室 おしゃれ` |
| Girls' night | 女子会 | `{area} 女子会 おしゃれ 居酒屋` |
| Business dinner | 接待 | `{area} 接待 個室 日本料理 高級` |
| Birthday | 誕生日 | `{area} 誕生日 サプライズ 居酒屋` |
| After-work drinks | 仕事帰り | `{area} 駅近 居酒屋 サクッと飲み` |

### By feature

| Feature | Japanese keyword | Query modifier |
|---|---|---|
| Private room | 個室 | `個室あり` |
| All-you-can-drink | 飲み放題 | `飲み放題付き` |
| All-you-can-eat | 食べ放題 | `食べ放題` |
| Smoking allowed | 喫煙可 | `喫煙可能` |
| Non-smoking | 禁煙 | `完全禁煙` |
| Late night | 深夜営業 | `深夜まで営業` |
| Tatami seating | 座敷 | `座敷あり` |
| Counter seating | カウンター | `カウンター席` |
| Terrace/outdoor | テラス | `テラス席` |
| Pet-friendly | ペット可 | `ペット同伴可` |
| Child-friendly | 子連れ | `子連れOK` |
| Wheelchair accessible | バリアフリー | `バリアフリー対応` |

### By cuisine type

| Cuisine | Japanese keyword | Typical budget |
|---|---|---|
| General izakaya | 居酒屋 | 2,500-4,000 |
| Yakitori | 焼き鳥 | 2,500-4,000 |
| Seafood | 海鮮・魚介 | 3,000-6,000 |
| Grilled meat | 焼肉 | 3,000-6,000 |
| Hot pot | 鍋 | 3,000-5,000 |
| Oden | おでん | 2,500-4,000 |
| Sushi | 寿司 | 4,000-10,000 |
| Tempura | 天ぷら | 3,000-6,000 |
| Ramen + drinks | ラーメン居酒屋 | 2,000-3,500 |
| Korean | 韓国料理 | 2,500-4,500 |
| Chinese | 中華料理 | 2,500-4,500 |
| Italian bar | イタリアンバル | 3,000-5,000 |
| Spanish bar | スペインバル | 3,000-5,000 |
| Beer garden | ビアガーデン | 3,000-5,000 |
| Standing bar | 立ち飲み | 1,500-3,000 |

---

## Gourmet Site Characteristics

### Tabelog (食べログ)
- **Strengths:** Most trusted food quality ratings in Japan; detailed user reviews
- **Rating scale:** 1.0-5.0 (3.5+ is considered good, 3.8+ is excellent)
- **URL pattern:** `https://tabelog.com/{prefecture}/A{area_code}/...`
- **Search URL:** `https://tabelog.com/{prefecture}/rstLst/?vs=1&sa={area}&sk=居酒屋`
- **Best for:** Food quality assessment, detailed menu information
- **Note:** Ratings tend to be stricter than other sites; 3.5 on Tabelog ≈ 4.0 on Google
- **WebFetch access:** ⚠ Frequently blocked (403). Individual store pages and ranking
  pages are often inaccessible. **Workaround:** Extract ratings and review counts from
  `WebSearch` snippets. Search result list pages (`rstLst`) are sometimes accessible
  when individual store pages are not.

### Hot Pepper Gourmet (ホットペッパーグルメ)
- **Strengths:** Online reservation; coupons; course/plan details
- **Rating scale:** 1.0-5.0
- **URL pattern:** `https://www.hotpepper.jp/str{id}/`
- **Best for:** Reservation, coupons, course menu details, party plans
- **Note:** Often has exclusive discount coupons and point rewards
- **WebFetch access:** ⚠ Frequently blocked (403) or returns 404 for changed store URLs.
  **Workaround:** Use `WebSearch` with `site:hotpepper.jp {restaurant_name}` to find
  current URLs. Area listing pages (e.g., `/SA11/Y005/...`) may also be blocked.

### Gurunavi (ぐるなび)
- **Strengths:** Detailed restaurant information; official restaurant pages
- **URL pattern:** `https://r.gnavi.co.jp/{id}/`
- **Best for:** Official menu and pricing, business dinner options
- **Note:** Strong in corporate/business dining listings
- **WebFetch access:** ⚡ Moderate success rate. Individual store pages (`r.gnavi.co.jp/{id}/`)
  sometimes work. Isolate in a separate fetch batch from unreliable sites.

### Google Maps
- **Strengths:** Location accuracy; real-time business hours; user photos
- **Rating scale:** 1.0-5.0
- **Search URL:** `https://www.google.com/maps/search/{area}+居酒屋`
- **Best for:** Location verification, real user photos, current business hours
- **Note:** Higher volume of reviews; more diverse reviewer base
- **WebFetch access:** ✅ Generally accessible. Search result pages and individual
  place pages work reliably. Prioritize Google Maps fetches as the most dependable source.

### Other sites (discovered through WebSearch)
- **aumo, さんたつ, ヒトサラ, TripAdvisor:** ✅ SSR article pages are generally
  accessible via `WebFetch` and provide useful curated recommendations
- **RETRIP (rtrp.jp):** ⚠ Blocked (403). Skip `WebFetch`; use snippets only
- **JS-rendered SPA sites (colmo, etc.):** ❌ Returns empty content. Skip `WebFetch`

---

## Budget Guidelines (per person, Tokyo area)

| Range | Category | Typical offerings |
|---|---|---|
| ~2,000 yen | Budget-friendly | Chain izakaya, standing bars, limited menu |
| 2,000-3,500 yen | Standard | General izakaya, basic courses, drinks extra |
| 3,500-5,000 yen | Mid-range | All-you-can-drink courses, varied menu |
| 5,000-8,000 yen | Upper mid-range | Private rooms, premium courses, quality food |
| 8,000-12,000 yen | High-end | Premium ingredients, exclusive atmosphere |
| 12,000+ yen | Luxury | High-end Japanese cuisine, omakase, kaiseki |

---

## Area Naming Conventions

When searching, use the most specific area name possible:

### Tokyo examples

| Broad area | Specific areas |
|---|---|
| 新宿 | 新宿駅東口, 新宿駅西口, 歌舞伎町, 新宿三丁目, 西新宿 |
| 渋谷 | 渋谷駅前, 道玄坂, 宮益坂, 渋谷センター街 |
| 池袋 | 池袋東口, 池袋西口, 南池袋 |
| 銀座 | 銀座一丁目, 銀座四丁目, 有楽町, 新橋 |
| 上野 | 上野駅前, 御徒町, アメ横 |
| 品川 | 品川駅前, 品川港南口, 大崎 |
| 東京駅 | 八重洲, 丸の内, 日本橋 |

---

## Composite Rating Interpretation

| Composite Score | Interpretation |
|---|---|
| 4.5+ | Exceptional - top-tier dining experience |
| 4.0-4.49 | Excellent - highly recommended |
| 3.5-3.99 | Good - solid choice with reliable quality |
| 3.0-3.49 | Average - acceptable but unremarkable |
| Below 3.0 | Below average - consider alternatives |

---

## Tips for Cross-referencing

1. **Tabelog 3.5+ AND Google 4.0+** = Highly reliable recommendation
2. **Large review count difference** between sites may indicate
   tourist-popular (high Google) vs. local favorite (high Tabelog)
3. **Recent reviews** (within 3 months) are more reliable for
   current quality and service
4. **Photo reviews** give the best indication of actual portion
   sizes and presentation
5. **Check for "net reservation" (ネット予約)** availability
   for convenience - both Tabelog and Hot Pepper support this

---

## WebFetch Execution Guidelines

### Batch execution order

Execute `WebFetch` calls in the following order to maximize data
collection even when some sites fail:

**Batch 1 (reliable sites, 2-3 calls):**
- Google Maps restaurant pages
- aumo / ヒトサラ / さんたつ article pages

**Batch 2 (moderate risk, 1-2 calls):**
- ぐるなび store pages

**Batch 3 (high risk, 1 call each — sequential):**
- 食べログ store pages (expect 403)
- ホットペッパー store pages (expect 403/404)

### Maximizing WebSearch snippet value

When `WebFetch` is blocked, `WebSearch` snippets often contain:
- **Tabelog ratings** — snippets usually include "★3.52" or "3.52点"
- **Review counts** — "口コミ 128件" appears in snippet text
- **Budget info** — "予算 3,000〜3,999円" is common in snippets
- **Address** — typically shown in the URL structure or snippet
- **Business hours** — sometimes included for Google results

Design `WebSearch` queries to maximize snippet information:
```
"{restaurant_name} 食べログ 口コミ 点数"
"{restaurant_name} ホットペッパー コース 飲み放題"
"{restaurant_name} Google Maps 口コミ"
```
