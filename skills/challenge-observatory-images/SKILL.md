---
name: challenge-observatory-images
description: Challenge rejected observatories with deep web research to find valid images. Use when observatories were rejected for no valid image during seed-observatories. Trigger phrases: "challenge rejects", "find images for rejected", "challenge observatory images"
---

# Challenge Observatory Images

Deep web research skill to find valid images for observatories that were rejected during the main seeding pipeline.

## When to Use

Invoke this skill when:
- The `seed-observatories` skill rejected observatories for having no valid image
- You want to give rejected observatories a "second chance" through deeper research
- `seed_data/rejected_observatories.json` exists with entries

Trigger phrases: "challenge rejects", "find images for rejected", "challenge observatory images"

## Prerequisites

**Required:** `seed_data/rejected_observatories.json` must exist (created by `/seed-observatories`)

If the file doesn't exist, run `/seed-observatories` first to generate it.

## Arguments

Parse from user input:
- `--limit N` or just a number: How many rejected observatories to challenge (default: all)
- `--offset N`: Skip first N rejected observatories

## Batch Limits

| Limit | Approach | Why Smaller |
|-------|----------|-------------|
| 1-8 | Single sub-agent | Deep research is intensive |
| 9-25 | Orchestrated | Multiple sub-agents, 5-8 each |
| 26+ | Multi-session | Split across sessions |

**Smaller batches than seed-observatories** because web research requires multiple searches per observatory.

## Architecture: Manager + Sub-Agents

```
┌─────────────────────────────────────────────────────────────┐
│  MANAGER (main session)                                     │
│  - Loads rejected_observatories.json                        │
│  - Spawns research sub-agents (sequentially)                │
│  - Reads checkpoint files from sub-agents                   │
│  - Builds challenged_observatories.json                     │
│                                                             │
│  ⚡ Manager NEVER performs web research - only orchestrates │
└─────────────────────────────────────────────────────────────┘
         │
         ├──► Sub-Agent 1 → writes temp/challenge_batch_001.json
         ├──► Sub-Agent 2 → writes temp/challenge_batch_002.json
         └──► Sub-Agent 3 → writes temp/challenge_batch_003.json
```

## File Locations

| File | Purpose |
|------|---------|
| `seed_data/rejected_observatories.json` | Input: observatories rejected by seed-observatories |
| `seed_data/temp/challenge_batch_NNN.json` | Checkpoint: research results from sub-agent N |
| `seed_data/challenged_observatories.json` | Output: results for manual review |

## ⚠️ CRITICAL RULES FOR MANAGER

| Rule | Why |
|------|-----|
| **NEVER write to `challenge_batch_*.json`** | Only sub-agents write checkpoints |
| **NEVER perform web searches directly** | Delegate all research to sub-agents |
| **Prefix checkpoints with `challenge_`** | Avoid collision with seed-observatories batch files |
| **3-image consensus required** | Ensures we find the RIGHT observatory, not just any image |

## Execution Steps

**IMPORTANT: Execute these steps automatically. Do not just display instructions.**

---

### Step 0: Self-Installation Check

Before running the pipeline, verify the `observatory_seeder` package is installed:

```python
import subprocess
import sys
from pathlib import Path

def ensure_observatory_seeder():
    """Install observatory_seeder if not available."""
    try:
        import observatory_seeder
        print("✓ observatory_seeder is installed")
        return True
    except ImportError:
        print("observatory_seeder not found. Installing...")

        # Find the skill directory (relative to project root)
        skill_dir = Path(".claude/skills/seed-observatories")
        if not skill_dir.exists():
            print("ERROR: Skill directory not found at .claude/skills/seed-observatories/")
            return False

        # Find Python executable - prefer djvenv, fall back to current
        if Path("djvenv/bin/python").exists():
            python = "djvenv/bin/python"
        else:
            python = sys.executable

        # Install the package
        result = subprocess.run(
            [python, "-m", "pip", "install", "-e", str(skill_dir)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Installation failed: {result.stderr}")
            return False

        print("✓ observatory_seeder installed successfully")
        return True

# Run the check
if not ensure_observatory_seeder():
    print("Cannot proceed without observatory_seeder package")
    # Exit skill
```

This auto-installs the skill's Python tools on first run.

---

### Step 1: Check for Resume

First, check if there are existing checkpoint files from a previous crashed session:

```python
import glob
import json
from pathlib import Path

# Check for checkpoint files from previous run (crashed mid-challenge)
existing_batches = sorted(glob.glob('seed_data/temp/challenge_batch_*.json'))

# Check for confirmed_rejected (observatories we already tried and failed - don't retry)
confirmed_rejected_slugs = set()
challenged_file = Path('seed_data/challenged_observatories.json')
if challenged_file.exists():
    with open(challenged_file) as f:
        challenged_data = json.load(f)
    for obs in challenged_data.get('confirmed_rejected', []):
        confirmed_rejected_slugs.add(obs.get('slug'))
    if confirmed_rejected_slugs:
        print(f"Found {len(confirmed_rejected_slugs)} confirmed rejected (will skip)")

if existing_batches:
    print(f"Found {len(existing_batches)} checkpoint files from previous run")
    # Ask user: resume or start fresh?
```

If resuming, skip to Step 3 and continue from the next batch number.

If starting fresh, clear old checkpoints:
```bash
rm -f seed_data/temp/challenge_batch_*.json
```

---

### Step 2: Load Rejected Observatories

Load the rejected observatories file and filter out already-challenged ones:

```python
rejected_file = Path('seed_data/rejected_observatories.json')
if not rejected_file.exists():
    print("ERROR: seed_data/rejected_observatories.json not found!")
    print("Run /seed-observatories first to generate rejected observatories.")
    # Exit skill

with open(rejected_file) as f:
    data = json.load(f)

all_rejected = data['observatories']
print(f"Loaded {len(all_rejected)} rejected observatories")

# Filter out confirmed_rejected (already tried and failed - no point retrying)
observatories = [obs for obs in all_rejected if obs.get('slug') not in confirmed_rejected_slugs]
if len(observatories) < len(all_rejected):
    print(f"Skipping {len(all_rejected) - len(observatories)} confirmed rejected")
    print(f"Remaining to challenge: {len(observatories)}")

# Apply --limit and --offset if provided
# Split into batches of 5-8 each
```

If no observatories remain to challenge, exit early with a success message.

---

### Step 3: Web Research via Sub-Agents

Split observatories into batches of 5-8 each. Spawn sub-agents **sequentially**.

**For each batch, use this prompt template:**

---

#### SUB-AGENT PROMPT TEMPLATE

````
OBSERVATORY IMAGE CHALLENGER - Batch {batch_num}

GOAL: Find valid images for rejected observatories through deep web research.
REQUIREMENT: 3+ confirming images from DIFFERENT sources to accept.

INPUT (research each):
{batch_json}

RESEARCH WORKFLOW for each observatory:

1. WEB SEARCH - Run multiple searches:
   - WebSearch: "{name} observatory photos"
   - WebSearch: "{name} telescope building"
   - WebSearch: "{name} dome exterior"
   - WebSearch: "{name} astronomical observatory"

2. COLLECT CANDIDATES - From search results, identify 5-8 promising image URLs:
   - News articles with photos
   - Tourism/travel sites
   - University/institution pages
   - Astronomy community sites
   - Flickr, photo hosting sites

3. VALIDATE EACH CANDIDATE (up to 8):
   For each candidate URL:
   a. Navigate with Chrome DevTools: mcp__chrome-devtools__new_page
   b. Take screenshot: mcp__chrome-devtools__take_screenshot
   c. Vision analysis - answer these questions:
      - Does this image show observatory buildings, domes, or telescope facilities?
      - Can you confirm this is specifically "{name}"?
      - Describe what the image shows (e.g., "Main dome from southeast", "Aerial view of facility")
   d. Record result: {url, confidence: "high"/"medium"/"low", description}
   e. CLOSE PAGE before next: mcp__chrome-devtools__close_page

4. CONSENSUS CHECK:
   - If 3+ images with "high" or "medium" confidence showing SAME FACILITY:
     → Status: "accepted"
     → Select best quality image as primary (see IMAGE SELECTION PRIORITY below)
     → Include all confirming images as evidence
   - If fewer than 3 confirming images:
     → Status: "rejected"
     → Record reason and candidates checked

5. IMAGE SELECTION PRIORITY (for choosing primary image):
   When multiple valid images exist, prefer in this order:
   1. **Actual photographs** of the real facility (aerial photos, ground-level shots)
   2. **Clean images without text overlays** - no watermarks, logos, or edited text
   3. **High resolution** - larger images that show detail
   4. **Exterior shots** showing the full facility, domes, or telescope buildings

   AVOID as primary image:
   - Architectural renderings with text/labels overlaid
   - Images with "INTERNATIONAL..." or facility names edited onto them
   - Marketing materials with heavy graphic design elements
   - Low-resolution thumbnails

   If the best consensus image has text overlays, check if a cleaner version exists
   from the same source or other validated sources.

IMPORTANT:
- Only ONE browser page open at a time
- Close each page before opening the next
- "Same facility" means clearly the same observatory complex, even if different buildings/angles
- Extract actual image URLs (not page URLs) using evaluate_script when needed

OUTPUT - Write to seed_data/temp/challenge_batch_{batch_num:03d}.json:

```python
import json
output = {
    "batch_num": {batch_num},
    "results": {
        "observatory-slug-1": {
            "status": "accepted",
            "image_url": "https://best-quality-image.jpg",
            "evidence": [
                {"url": "https://...", "confidence": "high", "description": "Main dome from north"},
                {"url": "https://...", "confidence": "high", "description": "Aerial view of facility"},
                {"url": "https://...", "confidence": "medium", "description": "Telescope housing interior"}
            ]
        },
        "observatory-slug-2": {
            "status": "rejected",
            "reason": "Only 1 confirming image found",
            "candidates_checked": 6
        }
    }
}
with open("seed_data/temp/challenge_batch_{batch_num:03d}.json", "w") as f:
    json.dump(output, f, indent=2)
```
````

---

After each sub-agent returns, verify the checkpoint file was created:

```python
import os
checkpoint = f'seed_data/temp/challenge_batch_{batch_num:03d}.json'
if not os.path.exists(checkpoint):
    print(f"WARNING: Sub-agent did not create {checkpoint}")
    # May need to re-run this batch
```

Then continue to the next batch.

---

### Step 4: Consolidate Checkpoints

After all batches complete, merge checkpoints into final output:

```python
import json
import glob
from datetime import datetime

# 1. Load rejected observatories (has metadata)
with open('seed_data/rejected_observatories.json') as f:
    rejected_data = json.load(f)
    rejected_by_slug = {obs['slug']: obs for obs in rejected_data['observatories']}

# 2. Collect all research results from checkpoints
all_results = {}
batch_files = sorted(glob.glob('seed_data/temp/challenge_batch_*.json'))

for batch_file in batch_files:
    with open(batch_file) as f:
        checkpoint = json.load(f)
        all_results.update(checkpoint.get('results', {}))

# 3. Build output structure
challenged_accepted = []
confirmed_rejected = []

for slug, result in all_results.items():
    if slug not in rejected_by_slug:
        print(f"Warning: {slug} not in rejected_observatories.json, skipping")
        continue

    obs = rejected_by_slug[slug]

    if result['status'] == 'accepted':
        challenged_accepted.append({
            "slug": slug,  # For tracking/deduplication
            "name": obs["name"],
            "latitude": obs["latitude"],
            "longitude": obs["longitude"],
            "image_url": result["image_url"],
            "wikidata_id": obs.get("wikidata_id"),
            "type_metadata": obs.get("type_metadata", {}),
            "challenge_evidence": result.get("evidence", [])
        })
    else:
        confirmed_rejected.append({
            "name": obs["name"],
            "slug": slug,
            "reason": result.get("reason", "Unknown"),
            "candidates_checked": result.get("candidates_checked", 0)
        })

# 4. Auto-merge accepted observatories into validated_observatories.json
if challenged_accepted:
    from observatory_seeder import merge_validated_observatories

    # Format for validated_observatories.json (no challenge_evidence, no wikidata_id)
    to_merge = []
    for obs in challenged_accepted:
        entry = {
            "name": obs["name"],
            "latitude": obs["latitude"],
            "longitude": obs["longitude"],
            "image_url": obs["image_url"]
        }
        if obs.get("type_metadata"):
            entry["type_metadata"] = obs["type_metadata"]
        to_merge.append(entry)

    path, total_count, added_count = merge_validated_observatories(to_merge)
    print(f"Merged {added_count} challenged observatories into validated_observatories.json (total now {total_count})")

# 5. Update rejected_observatories.json (remove processed observatories)
processed_slugs = set()
for obs in challenged_accepted:
    processed_slugs.add(obs.get('slug'))
for obs in confirmed_rejected:
    processed_slugs.add(obs.get('slug'))

with open('seed_data/rejected_observatories.json') as f:
    rejected_data = json.load(f)

remaining = [obs for obs in rejected_data['observatories'] if obs.get('slug') not in processed_slugs]

if remaining:
    with open('seed_data/rejected_observatories.json', 'w') as f:
        json.dump({"observatories": remaining}, f, indent=2)
    print(f"Updated rejected_observatories.json ({len(remaining)} remaining)")
else:
    os.remove('seed_data/rejected_observatories.json')
    print("All observatories processed - deleted rejected_observatories.json")

# 6. Update challenged_observatories.json (remove merged, keep confirmed_rejected)
existing_challenged = {"observatories": [], "confirmed_rejected": []}
if os.path.exists('seed_data/challenged_observatories.json'):
    with open('seed_data/challenged_observatories.json') as f:
        existing_challenged = json.load(f)

# Accepted observatories are now in validated_observatories.json - don't keep them
# Only append confirmed_rejected (observatories that truly have no images)
existing_challenged['confirmed_rejected'].extend(confirmed_rejected)

if existing_challenged['confirmed_rejected']:
    # Keep file with only confirmed_rejected
    existing_challenged['observatories'] = []  # Clear any staged observatories
    with open('seed_data/challenged_observatories.json', 'w') as f:
        json.dump(existing_challenged, f, indent=2)
    print(f"Updated challenged_observatories.json ({len(existing_challenged['confirmed_rejected'])} confirmed rejected)")
elif os.path.exists('seed_data/challenged_observatories.json'):
    # No confirmed_rejected and no staged - delete the file
    os.remove('seed_data/challenged_observatories.json')
    print("All challenges successful - deleted challenged_observatories.json")

# 7. Clean up checkpoint files
for batch_file in batch_files:
    os.remove(batch_file)
print("Checkpoint files cleaned up")
```

---

### Step 5: Display Metrics

Display a summary of the challenge results. **Read `METRICS_TEMPLATES.md`** for the full template.

---

### Step 6: Summary

The skill automatically:
1. Merges accepted observatories into `validated_observatories.json`
2. Removes processed observatories from `rejected_observatories.json`
3. Keeps only `confirmed_rejected` in `challenged_observatories.json` (observatories with no images)
4. Deletes temp files when empty

**File lifecycle:**
```
rejected_observatories.json    → Deleted when all processed
challenged_observatories.json  → Deleted when no confirmed_rejected
validated_observatories.json   → Permanent (accepted observatories)
```

After completion, inform the user:

```
CHALLENGE COMPLETE

Results:
  - Accepted: Merged into validated_observatories.json
  - Confirmed rejected: Kept in challenged_observatories.json (no images exist)
  - rejected_observatories.json: [updated/deleted]
  - challenged_observatories.json: [updated/deleted]
```

---

## Validation Criteria

**3-IMAGE CONSENSUS REQUIRED** - This is stricter than seed-observatories:

| Criterion | Why |
|-----------|-----|
| 3+ confirming images | Prevents false positives from similar-named observatories |
| "Same facility" check | Images must show the same physical complex |
| Multiple sources preferred | Cross-validates the identification |

**ACCEPT** when 3+ images show:
- Same observatory buildings/domes from different angles
- Different buildings clearly part of the same facility
- Consistent architectural style and surroundings

**REJECT** when:
- Fewer than 3 confirming images found
- Images show different observatories with similar names
- Only diagrams, maps, or logos found

### Image Quality Standards

When selecting the primary image URL for an accepted observatory:

| Prefer | Avoid |
|--------|-------|
| Actual photographs | Architectural renderings |
| Clean images (no text overlays) | Images with facility names edited on |
| High resolution | Low-res thumbnails |
| Exterior facility shots | Interior-only or equipment close-ups |
| News/media photos | Heavy marketing graphics |

**Why this matters:** Renderings with text overlays look artificial and reduce credibility. Real photographs of the actual facility are more engaging and authentic for users.

---

## Crash Recovery

If session crashes mid-research, just run the skill again:

```bash
/challenge-observatory-images
```

The skill automatically:
1. Detects existing `challenge_batch_*.json` files
2. Asks whether to resume or start fresh
3. If resuming, continues from the next batch
4. Merges all checkpoints when complete

---

## Troubleshooting

**Read `TROUBLESHOOTING.md`** for common issues and solutions.

---

## Chrome Tools

**Requires Chrome DevTools MCP** for sub-agent browser automation.

Sub-agents use these MCP tools:
- `mcp__chrome-devtools__new_page` - Navigate to image URLs
- `mcp__chrome-devtools__take_screenshot` - Capture images for vision validation
- `mcp__chrome-devtools__close_page` - Clean up after each validation

Verify MCP is configured:
```bash
claude mcp list | grep chrome
```
