# Seed Observatories

Automated pipeline for seeding observatory locations from Wikidata with AI-validated images.

## When to Use

Invoke this skill when the user wants to:
- Add observatory locations to the database
- Seed observatories from Wikidata
- Run the observatory seeding pipeline

Trigger phrases: "seed observatories", "add observatories", "run observatory seeder"

## Arguments

Parse from user input:
- `--limit N` or just a number: How many observatories to discover (default: 10)
- `--offset N`: Skip first N observatories (for pagination to get different results)
- `--min-elevation N`: Filter by minimum elevation in meters
- `--country "Name"`: Filter by country name

## Recommended Limits

| Limit | Use Case | Session Time |
|-------|----------|--------------|
| 5-10 | Testing | ~5 min |
| **20** | **Recommended max per session** | ~15-20 min |

**Maximum batch size: 20 observatories per session**

Due to Claude API limits on multi-image requests (max 2000px per image when many images in context), larger batches can cause session crashes. Use pagination across fresh sessions:

```
Session 1: /seed-observatories --limit 20              # Gets #1-20
Session 2: /seed-observatories --limit 20 --offset 20  # Gets #21-40  (NEW SESSION)
Session 3: /seed-observatories --limit 20 --offset 40  # Gets #41-60  (NEW SESSION)
```

**IMPORTANT:** Start a **fresh Claude session** for each batch to avoid accumulating images in context.

**Max available**: ~3,484 observatories in Wikidata

## Chrome-Based Validation (Key Innovation)

This skill uses **Chrome DevTools MCP** to validate images BEFORE downloading. This eliminates unnecessary downloads:

**How it works:**
1. Wikidata provides image URLs in discovery metadata
2. Chrome navigates directly to the image URL
3. Screenshot is taken and validated with Claude's vision
4. Only ACCEPTED image URLs are stored in JSON
5. Seeding downloads directly from validated URLs

**Benefits:**
- **ZERO downloads during validation** - Chrome just views the URL
- **Only download accepted images** - during seeding only
- **Single download per image** - no temp files needed
- **Dramatically reduced Wikimedia API usage**

## Execution Steps

**IMPORTANT: Execute these steps automatically. Do not just display instructions.**

### Step 1: Discovery + Dedupe

Run discovery to get observatory metadata from Wikidata, then automatically dedupe against database:

```bash
djvenv/bin/python -m tools.observatory_seeder.run --discover --limit <N>
```

Add options if user specified:
- `--offset <N>` to skip first N observatories (for pagination)
- `--min-elevation <M>` if elevation filter requested
- `--country "<name>"` if country filter requested

This:
1. Queries Wikidata for observatory metadata (including image_url)
2. **Automatically dedupes** against existing database locations
3. Saves only NEW observatories to `discovered.json`

If all discovered observatories already exist, the pipeline exits early.

### Step 2: Chrome-Based Image Validation (NO DOWNLOAD)

Validate images using Chrome DevTools MCP WITHOUT downloading. Chrome navigates directly to the image URL.

**IMPORTANT - Viewport Size Failsafe:**
Before starting validation, resize the browser to ensure screenshots stay under Claude's 2000px limit:
```
mcp__chrome-devtools__resize_page(width=1600, height=900)
```

For each observatory in `discovered.json` with an `image_url`:

1. **Navigate to image URL:**
   ```
   mcp__chrome-devtools__navigate_page(url="{image_url}")
   ```

2. **Take screenshot:**
   ```
   mcp__chrome-devtools__take_screenshot()
   ```

3. **Read and validate with vision** - Classify using these criteria:

   **ACCEPT** if image shows:
   - Observatory buildings, domes, or telescope structures
   - Radio telescope dishes or antenna arrays
   - Control buildings with astronomical equipment
   - Observatory grounds from outside

   **REJECT** if image shows:
   - Astronomical objects (nebulae, galaxies, star fields)
   - Landscapes without visible structures
   - Diagrams or illustrations
   - Blurry or low-quality images

4. **Record result:** `{slug, image_url, accepted: true/false, notes: reason}`

**For efficiency:** Process sequentially - open page, screenshot, validate, close is not needed (browser handles tabs). Just open new pages for each image.

### Step 3: Search Fallback URLs for Rejected

For each REJECTED observatory, search Wikimedia Commons for alternative image URLs:

```python
from tools.observatory_seeder import search_wikimedia_commons
results = search_wikimedia_commons("{observatory_name}", limit=5)
# Returns list of {title, url} for potential images
```

### Step 4: Chrome-Validate Fallback URLs

For each rejected observatory with fallback URLs:
1. Navigate to each fallback URL
2. Screenshot and validate with vision
3. If any ACCEPTED, record that URL
4. If all rejected, mark observatory as "no valid image"

### Step 5: Merge into Validated JSON

**IMPORTANT:** Use merge, not overwrite. The JSON file accumulates over multiple runs.

```python
from tools.observatory_seeder import merge_validated_observatories

# Build list of validated observatories from this run
new_observatories = [
    {
        "name": "Observatory Name",
        "latitude": 19.823,
        "longitude": -155.476,
        "elevation": 4136,
        "country": "Country",
        "image_url": "https://upload.wikimedia.org/...",  # The validated URL
        "validation_notes": "Description of what image shows"
    },
    # ... more observatories
]

# Merge into existing JSON (dedupes by coords with 2 decimal precision)
path, total_count, added_count = merge_validated_observatories(new_observatories)
print(f"Added {added_count} new, total now {total_count}")
```

### Step 6: Seed to Database

```bash
djvenv/bin/python manage.py seed_locations --type=observatory
```

The seeder will:
1. Read validated_observatories.json
2. Download each image directly from the validated URL
3. Process and save to database with thumbnail generation

**Note:** This is the ONLY time images are downloaded - directly from validated URLs.

### Step 7: Display Final Metrics

**IMPORTANT:** After seeding completes, ALWAYS display these metrics:

```
╔══════════════════════════════════════════════════════════════╗
║              OBSERVATORY SEEDING COMPLETE                    ║
╠══════════════════════════════════════════════════════════════╣
║  DISCOVERY                                                   ║
║    Total from Wikidata:        {discovered}                  ║
║    Already in database:        {duplicates}                  ║
║    New to process:             {new_count}                   ║
║                                                              ║
║  CHROME VALIDATION (zero downloads)                          ║
║    Primary images accepted:    {primary_accepted}            ║
║    Primary images rejected:    {primary_rejected}            ║
║    Fallback URLs validated:    {fallback_accepted}           ║
║    No valid image found:       {no_valid_image}              ║
║                                                              ║
║  FINAL RESULTS                                               ║
║    Observatories validated:    {total_validated}             ║
║    Acceptance rate:            {acceptance_rate}%            ║
║    Locations seeded to DB:     {seeded_count}                ║
║    Images downloaded:          {seeded_count} (at seed time) ║
╚══════════════════════════════════════════════════════════════╝
```

**Expected acceptance rate:** 80-95% with fallback logic

## File Locations

| File | Purpose |
|------|---------|
| `tools/observatory_seeder/` | Python pipeline scripts |
| `seed_data/temp/discovered.json` | Temporary discovery data |
| `seed_data/validated_observatories.json` | Output file (commit for production) |

## Production Workflow

### Local Development (with Claude Code)

```bash
# Run the skill to discover, validate, and generate JSON
/seed-observatories --limit 25

# Commit the validated JSON to your repo
git add seed_data/validated_observatories.json
git commit -m "Add validated observatories"
git push
```

### Production Deployment (Render)

```bash
# Run via Render Shell (not on every deploy)
python manage.py seed_locations --type=observatory
```

This downloads images from URLs at runtime and uploads to R2 storage.

### Duplicate Handling

**Deduplication happens at TWO stages:**

1. **Discovery dedupe (Step 1):** Compares against database by coordinates (2 decimal precision ~1km)
2. **JSON merge dedupe (Step 5):** Compares against existing JSON by coordinates

```
Example: 5 observatories already in database

Run: /seed-observatories --limit 15
  → Discovers 15 from Wikidata
  → Dedupe: 5 already exist, removed from list
  → Chrome validates 10 URLs (ZERO downloads!)
  → 8 accepted, 2 rejected with no valid fallback
  → Merges 8 into JSON
  → Seeding: 8 created (downloads happen here)

Run again: /seed-observatories --limit 15
  → Discovers same 15 from Wikidata
  → Dedupe: 13 already exist, 2 remain
  → Chrome validates 2 URLs
  → Seeds to DB
```

### When to Run on Render

| Scenario | Run seed_locations? |
|----------|---------------------|
| First deploy | Yes (once) |
| Code-only deploy | No |
| New observatories added to JSON | Yes |
| Re-deploy same code | No (duplicates skipped anyway) |

**Tip:** Run manually via Render Shell rather than on every deploy.
