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

## Processing Approach

**1 observatory = 1 sub-agent** (using Haiku model)

| Count | Approach |
|-------|----------|
| 1-50 | Sequential Haiku sub-agents |
| 51+ | Multi-session (split across sessions) |

**Why 1-per-agent?**
- Prevents image context accumulation that causes API failures
- Each agent stays well under token limits
- If one fails, others still succeed
- Haiku is fast and sufficient for image validation

## Architecture: Manager + Sub-Agents

```
┌─────────────────────────────────────────────────────────────┐
│  MANAGER (main session)                                     │
│  - Loads rejected_observatories.json                        │
│  - Spawns 1 Haiku sub-agent per observatory (sequentially)  │
│  - Reads checkpoint files from sub-agents                   │
│  - Consolidates results into challenged_observatories.json  │
│                                                             │
│  ⚡ Manager orchestrates - sub-agents do the research       │
└─────────────────────────────────────────────────────────────┘
         │
         ├──► Haiku Agent 1 (Observatory A) → challenge_001.json
         ├──► Haiku Agent 2 (Observatory B) → challenge_002.json
         ├──► Haiku Agent 3 (Observatory C) → challenge_003.json
         └──► ... (1 agent per observatory)
```

**Key design choice:** Each sub-agent only handles ONE observatory, keeping image context minimal and preventing API failures from accumulated screenshots.

## File Locations

| File | Purpose |
|------|---------|
| `seed_data/rejected_observatories.json` | Input: observatories rejected by seed-observatories |
| `seed_data/temp/challenge_NNN.json` | Checkpoint: result from sub-agent N (1 observatory each) |
| `seed_data/challenged_observatories.json` | Output: confirmed rejected (no images exist) |

## ⚠️ CRITICAL RULES FOR MANAGER

| Rule | Why |
|------|-----|
| **NEVER write to `challenge_*.json`** | Only sub-agents write checkpoints |
| **Use `model: "haiku"` for sub-agents** | Cheaper, faster, sufficient for this task |
| **Process sequentially, not parallel** | Avoids browser conflicts with Chrome DevTools |
| **2+ confirming images to accept** | Relaxed from 3 for better amateur observatory coverage |

## Execution Steps

**IMPORTANT: Execute these steps automatically. Do not just display instructions.**

---

### Step 0: Self-Installation Check

Before running the pipeline, verify the `observatory_seeder` package is installed:

```python
import subprocess
import sys
import os
from pathlib import Path

def find_virtualenv():
    """
    Find a Python virtual environment.

    Detection order:
    1. VIRTUAL_ENV environment variable (already activated)
    2. Common venv directory names in current directory
    3. Search upward for venv directories
    4. Fall back to sys.executable
    """
    # 1. Check if a venv is already activated
    if os.environ.get("VIRTUAL_ENV"):
        venv_python = Path(os.environ["VIRTUAL_ENV"]) / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)

    # 2. Common virtual environment directory names (in priority order)
    venv_names = [
        "djvenv",      # Django convention
        ".venv",       # Python default / common
        "venv",        # Python default
        "env",         # Common shorthand
        ".env",        # Hidden variant (check it's a dir, not dotenv file)
        "virtualenv",  # Explicit name
    ]

    # Check current directory first
    cwd = Path.cwd()
    for name in venv_names:
        venv_path = cwd / name / "bin" / "python"
        if venv_path.exists():
            return str(venv_path)

    # 3. Search upward (max 5 levels) for project root with venv
    search_dir = cwd
    for _ in range(5):
        for name in venv_names:
            venv_path = search_dir / name / "bin" / "python"
            if venv_path.exists():
                return str(venv_path)
        parent = search_dir.parent
        if parent == search_dir:
            break
        search_dir = parent

    # 4. Fall back to current Python
    return sys.executable

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

        # Find Python executable
        python = find_virtualenv()
        print(f"Using Python: {python}")

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
existing_checkpoints = sorted(glob.glob('seed_data/temp/challenge_*.json'))

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

if existing_checkpoints:
    print(f"Found {len(existing_checkpoints)} checkpoint files from previous run")
    # Ask user: resume or start fresh?
```

If resuming, skip to Step 3 and continue from the next checkpoint number.

If starting fresh, clear old checkpoints:
```bash
rm -f seed_data/temp/challenge_*.json
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
```

If no observatories remain to challenge, exit early with a success message.

---

### Step 3: Web Research via Sub-Agents

For each observatory, spawn a **Haiku sub-agent** to do the research. Process **sequentially** (not parallel) to avoid browser conflicts.

```python
for idx, obs in enumerate(observatories):
    agent_num = idx + 1
    # Spawn Task with model="haiku" - see prompt template below
```

**For each observatory, use this prompt template:**

---

#### SUB-AGENT PROMPT TEMPLATE (1 observatory)

````
OBSERVATORY IMAGE CHALLENGER - #{agent_num}: {name}

GOAL: Find a valid facility image for this rejected observatory.
REQUIREMENT: 2+ confirming images from DIFFERENT sources to accept.

OBSERVATORY:
- Name: {name}
- Slug: {slug}
- Location: {latitude}, {longitude}
- Website: {website if exists}
- Rejection reason: {rejection_reason}

RESEARCH WORKFLOW:

1. WEB SEARCH - Run 2-3 searches:
   - WebSearch: "{name} observatory building photos"
   - WebSearch: "{name} telescope dome"
   - If website exists, check it for photos

2. VALIDATE CANDIDATES (up to 5):
   For each promising URL:
   a. mcp__chrome-devtools__new_page(url)
   b. mcp__chrome-devtools__resize_page(width=800, height=600)
   c. mcp__chrome-devtools__take_screenshot()
   d. Does this show observatory buildings, domes, or telescope facilities?
   e. mcp__chrome-devtools__close_page()

3. DECISION:
   - If 2+ images show the SAME facility → "accepted"
   - Otherwise → "rejected" with reason

IMAGE SELECTION: Prefer actual photos over renderings, clean images without text overlays.

OUTPUT - Write to seed_data/temp/challenge_{agent_num:03d}.json:

```python
import json
output = {
    "agent_num": {agent_num},
    "slug": "{slug}",
    "status": "accepted",  # or "rejected"
    "image_url": "https://best-image.jpg",  # if accepted
    "evidence": [
        {"url": "...", "confidence": "high", "description": "..."}
    ],  # if accepted
    "reason": "...",  # if rejected
    "candidates_checked": 4
}
with open("seed_data/temp/challenge_{agent_num:03d}.json", "w") as f:
    json.dump(output, f, indent=2)
print(f"Wrote checkpoint for {slug}")
```
````

---

**Task tool invocation:**

```python
Task(
    description=f"Challenge observatory {agent_num}",
    prompt=prompt_from_template_above,
    subagent_type="general-purpose",
    model="haiku"  # Use Haiku for cost efficiency
)
```

After each sub-agent returns, verify the checkpoint:

```python
import os
checkpoint = f'seed_data/temp/challenge_{agent_num:03d}.json'
if not os.path.exists(checkpoint):
    print(f"WARNING: Sub-agent did not create {checkpoint}")
    # May need to re-run this observatory
```

Then continue to the next observatory.

---

### Step 4: Consolidate Checkpoints

After all sub-agents complete, merge checkpoints into final output:

```python
import json
import glob
import os

# 1. Load rejected observatories (has metadata)
with open('seed_data/rejected_observatories.json') as f:
    rejected_data = json.load(f)
    rejected_by_slug = {obs['slug']: obs for obs in rejected_data['observatories']}

# 2. Collect all research results from checkpoints (1 per file now)
all_results = {}
checkpoint_files = sorted(glob.glob('seed_data/temp/challenge_*.json'))

for checkpoint_file in checkpoint_files:
    with open(checkpoint_file) as f:
        checkpoint = json.load(f)
        slug = checkpoint.get('slug')
        if slug:
            all_results[slug] = checkpoint

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
for checkpoint_file in checkpoint_files:
    os.remove(checkpoint_file)
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

**2-IMAGE CONSENSUS** - Relaxed from 3 to improve amateur observatory coverage:

| Criterion | Why |
|-----------|-----|
| 2+ confirming images | Balances accuracy with coverage for smaller observatories |
| "Same facility" check | Images must show the same physical complex |
| Multiple sources preferred | Cross-validates the identification |

**ACCEPT** when 2+ images show:
- Same observatory buildings/domes from different angles
- Different buildings clearly part of the same facility
- Consistent architectural style and surroundings

**REJECT** when:
- Fewer than 2 confirming images found
- Images show different observatories with similar names
- Only diagrams, maps, or logos found
- Entry is not actually an astronomical observatory (e.g., town, institute, tide gauge)

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
1. Detects existing `challenge_*.json` checkpoint files
2. Asks whether to resume or start fresh
3. If resuming, skips observatories that already have checkpoints
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
