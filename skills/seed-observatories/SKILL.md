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
- `--resume`: Resume from checkpoint files (skip discovery, continue validation)

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
| `seed_data/temp/discovered.json` | All discovered observatories (from Wikidata) |
| `seed_data/temp/batch_NNN.json` | Checkpoint: validated results from sub-agent N |
| `seed_data/validated_observatories.json` | Final output (cumulative, commit to repo) |

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
1. Queries Wikidata for observatory metadata (including image_url)
2. **Dedupes against database** (removes observatories that already exist)
3. Saves NEW observatories to `seed_data/temp/discovered.json`

If all discovered observatories already exist, exit early.

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
Validate observatory images and write results to a checkpoint file.

## INPUT - Observatory batch:
{batch_json}

Note: Input contains only essential fields (slug, name, latitude, longitude, image_url).
Country and elevation are NOT included - Mapbox provides these during seeding.

## VALIDATION PROCESS
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

## OUTPUT
Write results to checkpoint file: seed_data/temp/batch_{batch_num:03d}.json

**CRITICAL: Copy all metadata fields EXACTLY as provided. Do NOT modify slug, name, latitude, or longitude. Only set accepted, final_url, used_fallback, and notes.**

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

            # THESE ARE YOUR VALIDATION RESULTS:
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
        "no_valid_image": N
    }
}
with open('seed_data/temp/batch_{batch_num:03d}.json', 'w') as f:
    json.dump(results, f, indent=2)
```

After writing the file, output: "Checkpoint saved: batch_{batch_num:03d}.json"

CRITICAL RULES:
- DO NOT save screenshots to disk
- DO NOT modify metadata (slug, name, latitude, longitude) - copy exactly
- ONLY determine: accepted (true/false), final_url, and notes
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
validated = [
    {
        "name": r["name"],
        "latitude": r["latitude"],
        "longitude": r["longitude"],
        "image_url": r["final_url"],
        "validation_notes": r["notes"]
    }
    for r in all_results if r.get("final_url")
]

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

```bash
djvenv/bin/python manage.py seed_locations --type=observatory
```

The seeder:
1. Reads validated_observatories.json
2. Downloads each image from validated URL (ONLY time images are downloaded)
3. Creates Location records in database
4. Generates thumbnails

---

### Step 6: Display Final Metrics

```
╔══════════════════════════════════════════════════════════════╗
║              OBSERVATORY SEEDING COMPLETE                    ║
╠══════════════════════════════════════════════════════════════╣
║  DISCOVERY                                                   ║
║    Total from Wikidata:        {discovered}                  ║
║    Already in database:        {duplicates}                  ║
║    New to process:             {new_count}                   ║
║                                                              ║
║  VALIDATION                                                  ║
║    Sub-agent batches:          {batch_count}                 ║
║    Primary images accepted:    {primary_accepted}            ║
║    Fallback URLs used:         {fallback_used}               ║
║    No valid image found:       {no_valid_image}              ║
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

If session crashes mid-validation:

```bash
# Next session - check for checkpoints
/seed-observatories --resume
```

This will:
1. Find existing `batch_*.json` files
2. Determine which batch to continue from
3. Skip already-completed batches
4. Continue validation from where it left off

---

## Deduplication

Happens at TWO stages:

1. **Discovery dedupe**: Python script checks database, removes existing observatories
2. **JSON merge dedupe**: `merge_validated_observatories()` checks coordinates (2 decimal precision ~1km)

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
