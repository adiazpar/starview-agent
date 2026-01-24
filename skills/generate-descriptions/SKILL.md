---
name: generate-descriptions
description: Generate descriptions for observatory locations. Reads validated_observatories.json and creates observatory_descriptions.json with AI-generated descriptions for each location.
---

# Observatory Description Generator

Generate research-backed descriptions for observatory locations using web search and sub-agents.

## Architecture

This skill uses a **sub-agent pattern** to preserve main conversation context:

```
Main Chat (Orchestrator)
    │
    └── Task: Explore/Research Agent (batch processor)
            │
            ├── WebSearch: "{observatory name} observatory"
            ├── WebFetch: Wikipedia/official site
            └── Write: Append to output JSON
```

## Execution Instructions

### Step 1: Read Source Data

First, read the observatory list:

```
Read: seed_data/validated_observatories.json
```

Extract the list of observatory names that need descriptions.

### Step 2: Check for Existing Progress

Check if `seed_data/observatory_descriptions.json` already exists with partial progress:

```
Read: seed_data/observatory_descriptions.json (if exists)
```

If it exists, identify which observatories still need descriptions.

### Step 3: Spawn Sub-Agent for Batch Processing

Use the **Task tool** to spawn a research sub-agent. Process in batches of 50 to manage context.

**IMPORTANT: Data Integrity**

Sub-agents should NOT copy coordinates or names - they can truncate floats or alter text. Instead:
- Orchestrator assigns each observatory an **index** (0, 1, 2...)
- Sub-agent receives **index + name only** (for research)
- Sub-agent returns **index + description only**
- Orchestrator merges descriptions with original data (preserving exact coordinates)

**Sub-agent prompt template:**

```
Research and generate descriptions for the following observatories. For each one:

1. Use WebSearch to search for "{name} observatory history"
2. If Wikipedia or official site found, use WebFetch to get details
3. Write a 2-4 sentence description including:
   - Founding date/history (if found)
   - Notable instruments, discoveries, or research focus
   - Geographic/atmospheric advantages for astronomy
   - Current status (active research, public access, etc.)

If web search yields no results, write a general description based on the name.

Observatories to research (index: name):
0: Lick Observatory
1: Keck Observatory
2: Mount Wilson Observatory
... (up to 50)

CRITICAL: Return ONLY the index and description. Do NOT include coordinates or copy the name.

Output format - return a JSON array:
[
  {"index": 0, "description": "Founded in 1888..."},
  {"index": 1, "description": "Located atop..."},
  ...
]
```

### Step 4: Merge Results (Orchestrator Responsibility)

After each sub-agent batch completes:
1. Parse the returned JSON array (index + description only)
2. **Orchestrator** looks up original observatory by index
3. **Orchestrator** copies exact name, latitude, longitude from source file
4. Append complete record to `seed_data/observatory_descriptions.json`

This ensures coordinates like `42.445949005` are preserved exactly, not truncated to `42.446`.

### Step 5: Final Output

The complete file should have this structure:

```json
{
  "version": "1.0",
  "generated_at": "2026-01-23T...",
  "generated_by": "Claude Code sub-agent with web research",
  "total": 946,
  "descriptions": [
    {
      "name": "Lick Observatory",
      "latitude": 37.3414,
      "longitude": -121.6429,
      "description": "Founded in 1888 atop Mount Hamilton in California, Lick Observatory was the first permanently occupied mountaintop observatory in the world. Home to the historic 36-inch Great Lick Refractor, it has contributed to discoveries including numerous moons of Jupiter and early exoplanet detection. The site's 4,265-foot elevation provides excellent seeing conditions and remains active for research and public programs.",
      "sources": ["wikipedia", "ucolick.org"]
    }
  ]
}
```

## Sub-Agent Configuration

**Recommended settings for the Task tool:**

- `subagent_type`: "general-purpose" (has WebSearch + WebFetch access)
- `model`: "haiku" (fast and cost-effective for research tasks)
- Process 50 observatories per batch (balance between context and efficiency)
- Run batches sequentially to avoid rate limits on web search

## Research Guidelines for Sub-Agent

### What to Search For
- `"{observatory name}" observatory history founded`
- `"{observatory name}" telescope research`

### Priority Sources
1. **Wikipedia** - Usually has founding date, instruments, notable discoveries
2. **Official observatory website** - Current programs, visitor info
3. **University/institution pages** - For academic observatories

### Description Quality Standards

**Good description includes:**
- When it was established (if known)
- What makes it notable (instruments, discoveries, location)
- Current purpose (research, education, public access)

**Example - Well-Known Observatory:**
> "Established in 1888, Lick Observatory sits atop Mount Hamilton in California's Diablo Range at 4,265 feet elevation. Home to the historic 36-inch Great Lick Refractor, the observatory has contributed to discoveries of numerous moons and exoplanets. Its remote mountain location provides excellent seeing conditions and dark skies, making it a premier destination for both research and public stargazing programs."

**Example - Lesser-Known Observatory:**
> "The A.C. Barnes Observatory is an educational facility located on the Ithaca College campus in New York. Primarily used for undergraduate astronomy education and public outreach, the observatory offers regular viewing sessions. Its position in the Finger Lakes region provides accessible dark skies for the college community."

**Example - Minimal Web Results:**
> "Located in the mountains of northern Italy near Trento, the Terrazza delle Stelle serves as a public astronomical observation facility. The alpine site offers visitors opportunities to observe the night sky from an elevated location away from urban light pollution."

### Handling No Results

If web search returns nothing useful:
1. Use coordinates to determine country/region
2. Infer purpose from name (e.g., "University Observatory" → educational)
3. Write a general but accurate description
4. Do NOT fabricate specific dates, discoveries, or instruments

## Rate Limiting

- Add 1-2 second delays between WebSearch calls
- Process batches of 50, then pause before next batch
- If rate limited, wait and retry

## Resume Support

The skill supports resumption:
1. Check existing `observatory_descriptions.json` for completed entries
2. Skip already-processed observatories
3. Continue from where it left off

## Verification

After all batches complete:

```bash
cat seed_data/observatory_descriptions.json | python -c "
import json, sys
d = json.load(sys.stdin)
print(f'Total descriptions: {len(d[\"descriptions\"])}')
print(f'Sample: {d[\"descriptions\"][0][\"name\"]}: {d[\"descriptions\"][0][\"description\"][:100]}...')
"
```

## Orchestrator Commands

The main chat orchestrator should:

1. **Initialize**: Read observatory list, check for existing progress
2. **Loop**: Spawn sub-agents for each batch of 50
3. **Merge**: Combine results after each batch
4. **Report**: Show progress (e.g., "Completed 150/946 observatories")
5. **Finalize**: Write complete JSON file when done
