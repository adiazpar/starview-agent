---
name: seed-observatories
description: Orchestrated pipeline for seeding observatory locations from Wikidata with AI-validated images. Use when adding observatories to the database, seeding from Wikidata, or running the observatory seeding pipeline. Trigger phrases: "seed observatories", "add observatories", "run observatory seeder".
---

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

## ⚠️ CRITICAL RULES FOR MANAGER

These rules prevent checkpoint corruption:

| Rule | Why |
|------|-----|
| **NEVER write to `batch_*.json` files** | Only sub-agents write checkpoints |
| **NEVER save batch input to files** | Pass batch data directly in sub-agent prompt |
| **ALWAYS normalize checkpoints** | Use `normalize_checkpoint()` to handle format variations |
| **NEVER validate images directly** | Manager has no vision - delegate to sub-agents |
| **Verify `validated` key exists** | After normalization, checkpoint must have `validated` dict |

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

Split observatories into batches of 10-15 each. Spawn sub-agents **sequentially**.

**For each batch, use this prompt template:**

---

#### SUB-AGENT PROMPT TEMPLATE

> **Note:** Minimal output format - sub-agents only return what they produce (validated URLs). Manager has all other data in discovered.json.

````
OBSERVATORY IMAGE VALIDATOR - Batch {batch_num}

INPUT (validate each):
{batch_json}

TASKS:
1. For each observatory, open image_url in Chrome and take screenshot
2. ACCEPT if shows: buildings, domes, telescopes, dishes, facilities
3. REJECT if shows: space objects only, empty landscapes, diagrams
4. If rejected, search for fallback image:
   ```python
   from tools.observatory_seeder import search_wikimedia_commons
   results = search_wikimedia_commons("{name}", limit=5)
   ```
   Then validate ONE AT A TIME:
   - Open first fallback URL, take screenshot, validate
   - If ACCEPT → use this URL, stop searching
   - If REJECT → close page, try next fallback
   - If all rejected → set validated[slug] = null
5. If no website in type_metadata, WebSearch "{name} official website"

IMPORTANT: Only have ONE image page open at a time. Close each page before opening the next.

OUTPUT - Write to seed_data/temp/batch_{batch_num:03d}.json:

```python
import json
output = {
    "batch_num": {batch_num},
    "validated": {
        "slug-1": "http://accepted-image-url.jpg",
        "slug-2": "http://fallback-image-url.jpg",
        "slug-3": null  # null = no valid image found
    },
    "websites_found": {
        "slug-1": "https://found-website.org"
    }
}
with open("seed_data/temp/batch_{batch_num:03d}.json", "w") as f:
    json.dump(output, f, indent=2)
```

RULES:
• "validated" = slug → accepted_image_url (or null if rejected)
• "websites_found" = slug → website_url (only for NEW websites found via search)
• Use exact slug from input as key
• DO NOT copy name, coords, or other fields - manager has them
````

---

#### CHECKPOINT NORMALIZATION

Sub-agents may return various formats. After each sub-agent returns, **run the normalization script**:

```bash
python .claude/skills/seed-observatories/normalize_checkpoint.py \
    seed_data/temp/batch_{batch_num:03d}.json {batch_num}
```

This script handles:
- Canonical format: `{"batch_num": N, "validated": {...}}`
- Old format: `{"batch_num": N, "results": [...]}`
- Array format: `[{slug, image_url, image_status}, ...]`

Then continue to next batch.

---

### Step 4: Consolidate Checkpoints

After all batches complete, merge checkpoints with discovered.json to build final output:

```python
import json
import glob
import os
from tools.observatory_seeder import merge_validated_observatories

# 1. Load discovered.json (has all observatory metadata)
with open('seed_data/temp/discovered.json') as f:
    discovered = {obs['slug']: obs for obs in json.load(f)['observatories']}

# 2. Collect all validation results from checkpoints
all_validated = {}      # slug → image_url
all_websites = {}       # slug → website_url
batch_files = sorted(glob.glob('seed_data/temp/batch_*.json'))

for batch_file in batch_files:
    with open(batch_file) as f:
        checkpoint = json.load(f)
        all_validated.update(checkpoint.get('validated', {}))
        all_websites.update(checkpoint.get('websites_found', {}))

# 3. Build final validated list by merging
validated = []
for slug, image_url in all_validated.items():
    if not image_url:  # Skip rejected (null)
        continue
    if slug not in discovered:
        print(f"Warning: {slug} not in discovered.json, skipping")
        continue

    obs = discovered[slug]
    entry = {
        "name": obs["name"],
        "latitude": obs["latitude"],
        "longitude": obs["longitude"],
        "image_url": image_url
    }

    # Merge type_metadata: original + any new website found
    type_metadata = obs.get("type_metadata", {}).copy()
    if slug in all_websites:
        type_metadata["website"] = all_websites[slug]
    if type_metadata:
        entry["type_metadata"] = type_metadata

    validated.append(entry)

print(f"Validated {len(validated)} observatories from {len(batch_files)} batches")

# 4. Merge into validated_observatories.json
path, total_count, added_count = merge_validated_observatories(validated)
print(f"Added {added_count} new, total now {total_count}")

# 5. Clean up temp directory
for batch_file in batch_files:
    os.remove(batch_file)
os.remove('seed_data/temp/discovered.json')
if not os.listdir('seed_data/temp'):
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

Display a summary of the seeding process. **Read `METRICS_TEMPLATES.md`** for the full templates.

- Use "prepare-only" template if `--prepare-only` flag was set
- Use "full seeding" template if database was updated

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

## Troubleshooting

**Read `TROUBLESHOOTING.md`** for common issues and solutions:
- Sub-agent uses different output format
- Checkpoint missing validation data
- Sub-agent doesn't create checkpoint
- Slug not found in discovered.json
- Chrome DevTools MCP not working
- Session crashed mid-validation
- Too many browser windows open

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
