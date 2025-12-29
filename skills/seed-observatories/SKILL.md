# Seed Observatories

Orchestrated pipeline for seeding observatory locations from Wikidata with AI-validated images.

## When to Use

Invoke this skill when the user wants to:
- Add observatory locations to the database
- Seed observatories from Wikidata
- Run the observatory seeding pipeline

Trigger phrases: "seed observatories", "add observatories", "run observatory seeder"

## Arguments

Parse from user input:
- `--limit N` or just a number: How many observatories to discover (default: 10)
- `--offset N`: Skip first N observatories (for pagination)
- `--min-elevation N`: Filter by minimum elevation in meters
- `--country "Name"`: Filter by country name
- `--prepare-only`: Skip database seeding (Step 5). Updates validated_observatories.json only. Use this to prepare data locally, commit it, then run `seed_locations` on production.

**Resume behavior:** If checkpoint files exist (`batch_*.json`), the skill automatically detects them in Step 1 and asks whether to resume or start fresh. No flag needed.

## Batch Limits

| Limit | Approach | Context Impact |
|-------|----------|----------------|
| 1-15 | Single sub-agent | One validation batch |
| 16-50 | **Orchestrated** | Multiple sub-agents handle batches |
| 51+ | Multi-session | Split across sessions |

**Max available**: ~3,484 observatories in Wikidata

**IMPORTANT:** The manager NEVER performs image validation directly. All validation is delegated to sub-agents which have access to Chrome DevTools MCP tools.

## Architecture: Manager + Sub-Agents

```
┌─────────────────────────────────────────────────────────────┐
│  MANAGER (main session)                                     │
│  - Runs discovery                                           │
│  - Spawns validation sub-agents (sequentially)              │
│  - Reads checkpoint files from sub-agents                   │
│  - Merges checkpoints → validated_observatories.json        │
│  - Runs seed command                                        │
│                                                             │
│  ⚡ Manager NEVER sees images - only JSON text              │
└─────────────────────────────────────────────────────────────┘
         │
         ├──► Sub-Agent 1 → writes temp/batch_001.json
         ├──► Sub-Agent 2 → writes temp/batch_002.json
         └──► Sub-Agent 3 → writes temp/batch_003.json
```

**Key benefits:**
- Images stay in sub-agent contexts, manager stays lightweight
- Checkpoint files survive session crashes
- Can resume from last successful batch

## File Locations

| File | Purpose |
|------|---------|
| `seed_data/temp/discovered.json` | Discovered observatories with type_metadata (from Wikidata) |
| `seed_data/temp/batch_NNN.json` | Checkpoint: validated results from sub-agent N |
| `seed_data/validated_observatories.json` | Final output (cumulative, commit to repo) |

## type_metadata Usage

Observatory `type_metadata` enables frontend features:
- **Call button**: Uses `phone_number` (E.164) for `tel:` links, `phone_display` for UI
- **Website button**: Uses `website` URL (validated with soft 404 detection)

These buttons appear in the ExploreMap location popup for observatory locations.

## URL Validation (Three-Tier System)

Website URLs undergo tiered validation to ensure they're valid:

| Tier | Phase | What It Does |
|------|-------|--------------|
| **Tier 1** | Discovery | Soft 404 detection - checks page content for error patterns |
| **Tier 2** | Sub-agent | Web search fallback - finds alternative URLs if missing |
| **Tier 3** | Sub-agent | AI vision - verifies page looks like real observatory site |

**Tier 1 runs automatically during discovery.** Invalid URLs (soft 404s, connection errors) are excluded from `type_metadata`. Sub-agents can optionally run Tier 2 search for observatories missing website URLs.

## Execution Steps

**IMPORTANT: Execute these steps automatically. Do not just display instructions.**

---

### Step 1: Check for Resume

First, check if there are existing checkpoint files (previous crashed session):

```python
import glob
existing_batches = sorted(glob.glob('seed_data/temp/batch_*.json'))
if existing_batches:
    print(f"Found {len(existing_batches)} checkpoint files from previous run")
    # Ask user: resume or start fresh?
```

If resuming, skip to Step 3b and continue from the next batch number.

If starting fresh, clear old checkpoints:
```bash
rm -f seed_data/temp/batch_*.json
```

---

### Step 2: Discovery + Dedupe

Run discovery to get observatory metadata from Wikidata:

```bash
djvenv/bin/python -m tools.observatory_seeder.run --discover --limit <N> --offset <M>
```

This:
1. Queries Wikidata SPARQL for observatory metadata:
   - Name, coordinates, image_url
   - Phone (P1329) and website (P856) for `type_metadata`
2. **Enriches type_metadata** during discovery:
   - Phone numbers normalized to E.164 format (`+12505551234`) with display format (`+1-250-555-1234`)
   - Website URLs validated with **soft 404 detection** (Tier 1):
     - Detects pages returning HTTP 200 but showing error content
     - Multi-language patterns: "404", "not found", "página no encontrada", etc.
     - Invalid URLs excluded from type_metadata (sub-agents can search for alternatives)
     - Valid URLs upgraded to HTTPS when available
3. **Dedupes against validated_observatories.json** (removes observatories already in JSON)
4. Saves NEW observatories to `seed_data/temp/discovered.json`

**type_metadata structure:**
```json
{
  "phone_number": "+12505551234",
  "phone_display": "+1-250-555-1234",
  "website": "https://observatory.example.org"
}
```

Note: The `seed_locations` command handles database deduplication separately during seeding.

If all discovered observatories already exist in the JSON, exit early.

---

### Step 3: Validation via Sub-Agents

Read discovered.json and count observatories:

```python
import json
with open('seed_data/temp/discovered.json') as f:
    observatories = json.load(f)['observatories']
count = len(observatories)
```

**IMPORTANT:** The manager NEVER validates images directly. All validation is delegated to sub-agents which have Chrome DevTools MCP access for browser automation.

Split observatories into batches of 10-15 each. Spawn sub-agents **sequentially**.

**For each batch:**

```python
batch_num = 1  # increment for each batch
batch_data = observatories[start:end]  # slice for this batch
```

**Sub-agent prompt:**

```
You are an OBSERVATORY IMAGE VALIDATION AGENT.

## YOUR TASK
Validate observatory images and optionally find website URLs.

## INPUT - Observatory batch:
{batch_json}

Note: Input contains essential fields (slug, name, latitude, longitude, image_url).
May include type_metadata (phone, website) - preserve and potentially enhance.
Country and elevation are NOT included - Mapbox provides these during seeding.

## VALIDATION PROCESS

### Image Validation (Required)
For each observatory:
1. Navigate Chrome to the image_url
2. Take screenshot (DO NOT save screenshot to file)
3. Validate using vision:
   - ACCEPT: Observatory buildings, domes, telescopes, radio dishes, facility grounds
   - REJECT: Astronomical objects only (nebulae, galaxies, star fields), landscapes without structures, diagrams

4. For REJECTED images, search Wikimedia Commons for alternatives:
   ```python
   from tools.observatory_seeder import search_wikimedia_commons
   results = search_wikimedia_commons("{observatory_name}", limit=5)
   ```
   Validate each fallback URL until one is ACCEPTED.

### Website Search (Required - Tier 2)
If type_metadata is missing `website` field, search for official website:
1. Use WebSearch: `"{observatory_name}" official website`
2. Look for .edu, .gov, .org domains (universities, government, research institutions)
3. Navigate Chrome to top candidate, take screenshot, verify it's a real page (not error page)
4. If valid, add to type_metadata: `"website": "https://..."`
5. If no valid website found, leave website field empty

## OUTPUT
Write results to checkpoint file: seed_data/temp/batch_{batch_num:03d}.json

**CRITICAL: Copy all metadata fields EXACTLY as provided. Do NOT modify slug, name, latitude, or longitude.**

```python
import json
results = {
    "batch_num": {batch_num},
    "results": [
        {
            # COPY THESE EXACTLY FROM INPUT - DO NOT MODIFY:
            "slug": "observatory-slug",
            "name": "Observatory Name",
            "latitude": 12.345,
            "longitude": -67.890,
            "original_url": "http://...",

            # type_metadata: COPY FROM INPUT, may add website if found via search
            "type_metadata": {
                "phone_number": "+1234567890",
                "phone_display": "+1-234-567-890",
                "website": "https://..."  # From discovery OR added via Tier 2 search
            },

            # IMAGE VALIDATION RESULTS:
            "final_url": "http://...",  # original if accepted, fallback if found, null if none
            "accepted": True,
            "used_fallback": False,
            "notes": "Shows observatory dome on mountain"
        }
    ],
    "stats": {
        "total": N,
        "accepted": N,
        "rejected": N,
        "fallback_found": N,
        "no_valid_image": N,
        "websites_found": N  # Count of websites added via Tier 2 search
    }
}
with open('seed_data/temp/batch_{batch_num:03d}.json', 'w') as f:
    json.dump(results, f, indent=2)
```

After writing the file, output: "Checkpoint saved: batch_{batch_num:03d}.json"

CRITICAL RULES:
- DO NOT save screenshots to disk
- DO NOT modify metadata (slug, name, latitude, longitude) - copy exactly
- Image validation is REQUIRED
- Website search is REQUIRED if type_metadata has no website field
```

**After each sub-agent completes:**
- Verify checkpoint file was created
- Log progress: "Batch X/Y complete"
- Continue to next batch

---

### Step 4: Consolidate Checkpoints

After all batches complete, merge checkpoint files into final JSON:

```python
import json
import glob
from tools.observatory_seeder import merge_validated_observatories

# Read all checkpoint files
all_results = []
batch_files = sorted(glob.glob('seed_data/temp/batch_*.json'))

for batch_file in batch_files:
    with open(batch_file) as f:
        batch_data = json.load(f)
        all_results.extend(batch_data['results'])

# Build validated list (only those with final_url)
# Note: country and elevation are NOT included - Mapbox provides during seeding
validated = []
for r in all_results:
    if not r.get("final_url"):
        continue
    entry = {
        "name": r["name"],
        "latitude": r["latitude"],
        "longitude": r["longitude"],
        "image_url": r["final_url"],
        "validation_notes": r["notes"]
    }
    # Preserve type_metadata (phone, website) from discovery
    if r.get("type_metadata"):
        entry["type_metadata"] = r["type_metadata"]
    validated.append(entry)

# Merge into validated_observatories.json
path, total_count, added_count = merge_validated_observatories(validated)
print(f"Added {added_count} new, total now {total_count}")

# Clean up temp directory
for batch_file in batch_files:
    os.remove(batch_file)
if os.path.exists('seed_data/temp/discovered.json'):
    os.remove('seed_data/temp/discovered.json')
if os.path.exists('seed_data/temp') and not os.listdir('seed_data/temp'):
    os.rmdir('seed_data/temp')
print("Temp directory cleaned up")
```

---

### Step 5: Seed to Database

**Skip this step if `--prepare-only` flag is set.**

```bash
djvenv/bin/python manage.py seed_locations --type=observatory
```

The seeder:
1. Reads validated_observatories.json
2. Skips locations that already exist in database (by name + coordinates)
3. Downloads each image from validated URL (ONLY time images are downloaded)
4. Creates Location records in database
5. Generates thumbnails

---

### Step 6: Display Final Metrics

**If `--prepare-only` was used**, display this version (no seeding stats):

```
╔══════════════════════════════════════════════════════════════╗
║           OBSERVATORY VALIDATION COMPLETE                    ║
║                  (--prepare-only mode)                       ║
╠══════════════════════════════════════════════════════════════╣
║  DISCOVERY                                                   ║
║    Total from Wikidata:        {discovered}                  ║
║    Already in JSON:            {duplicates}                  ║
║    New to process:             {new_count}                   ║
║                                                              ║
║  IMAGE VALIDATION                                            ║
║    Sub-agent batches:          {batch_count}                 ║
║    Primary images accepted:    {primary_accepted}            ║
║    Fallback URLs used:         {fallback_used}               ║
║    No valid image found:       {no_valid_image}              ║
║                                                              ║
║  WEBSITE VALIDATION                                          ║
║    Valid from Wikidata:        {wikidata_valid}              ║
║    Soft 404s rejected:         {soft_404_rejected}           ║
║    Found via search:           {search_found}                ║
║                                                              ║
║  RESULTS                                                     ║
║    Observatories validated:    {total_validated}             ║
║    Acceptance rate:            {acceptance_rate}%            ║
║    Added to JSON:              {added_to_json}               ║
║    Total in JSON:              {total_in_json}               ║
║                                                              ║
║  NEXT STEP                                                   ║
║    Commit validated_observatories.json, then on production:  ║
║    python manage.py seed_locations --type=observatory        ║
╚══════════════════════════════════════════════════════════════╝
```

**If full seeding was performed**, display this version:

```
╔══════════════════════════════════════════════════════════════╗
║              OBSERVATORY SEEDING COMPLETE                    ║
╠══════════════════════════════════════════════════════════════╣
║  DISCOVERY                                                   ║
║    Total from Wikidata:        {discovered}                  ║
║    Already in JSON:            {duplicates}                  ║
║    New to process:             {new_count}                   ║
║                                                              ║
║  IMAGE VALIDATION                                            ║
║    Sub-agent batches:          {batch_count}                 ║
║    Primary images accepted:    {primary_accepted}            ║
║    Fallback URLs used:         {fallback_used}               ║
║    No valid image found:       {no_valid_image}              ║
║                                                              ║
║  WEBSITE VALIDATION                                          ║
║    Valid from Wikidata:        {wikidata_valid}              ║
║    Soft 404s rejected:         {soft_404_rejected}           ║
║    Found via search:           {search_found}                ║
║                                                              ║
║  FINAL RESULTS                                               ║
║    Observatories validated:    {total_validated}             ║
║    Acceptance rate:            {acceptance_rate}%            ║
║    Locations seeded to DB:     {seeded_count}                ║
╚══════════════════════════════════════════════════════════════╝
```

---

## Validation Criteria

**ACCEPT** if image shows:
- Observatory buildings or domes
- Telescope structures (optical or radio)
- Antenna arrays or dishes
- Facility grounds with visible structures

**REJECT** if image shows:
- Astronomical objects only (nebulae, galaxies, star fields)
- Landscapes without visible structures
- Diagrams, charts, or illustrations
- Unrelated images

---

## Crash Recovery

If session crashes mid-validation, just run the skill again:

```bash
/seed-observatories --limit 25
```

The skill automatically:
1. Detects existing `batch_*.json` checkpoint files
2. Asks whether to resume or start fresh
3. If resuming, skips discovery and continues from the next batch
4. Merges all checkpoints when complete

---

## Deduplication

Happens at THREE stages:

1. **Discovery dedupe**: Python script checks `validated_observatories.json`, removes observatories already in JSON
2. **JSON merge dedupe**: `merge_validated_observatories()` checks coordinates (2 decimal precision ~1km)
3. **Seeding dedupe**: `seed_locations` command checks database by name + coordinates, skips existing locations

---

## Chrome Tools

**Requires Chrome DevTools MCP** for sub-agent browser automation.

Sub-agents inherit MCP tools from the parent session, so Chrome DevTools MCP must be configured:

```bash
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest
```

The sub-agents use these MCP tools:
- `mcp__chrome-devtools__new_page` - Navigate to image URL
- `mcp__chrome-devtools__take_screenshot` - Capture image for vision validation
- `mcp__chrome-devtools__close_page` - Clean up after validation

**Note:** Built-in Claude Chrome (`claude --chrome`) does NOT work for sub-agents since it's a CLI flag, not an inheritable tool. Only MCP tools are inherited by sub-agents.
