# Challenge Observatory Images - Troubleshooting

Common issues and solutions for the challenge-observatory-images skill.

---

## rejected_observatories.json Not Found

**Symptom:** Skill exits with error about missing file

**Cause:** The seed-observatories skill hasn't been run, or no observatories were rejected

**Fix:**
```bash
# Run seed-observatories first
/seed-observatories --limit 25

# Check if file was created
ls -la seed_data/rejected_observatories.json
```

If seed-observatories ran successfully but no file exists, all observatories may have been accepted (good news!).

---

## Sub-Agent Can't Find Images

**Symptom:** Most/all observatories marked as "rejected" with few candidates checked

**Possible causes:**
1. Observatory is very obscure with minimal online presence
2. Non-English name causing search issues
3. Rate limiting from search providers

**Fixes:**
- Try adding location to search: "{name} {country} observatory"
- Use alternative name spellings from Wikidata
- Wait and retry if rate limited
- Accept that some observatories genuinely have no online images

---

## Chrome DevTools MCP Not Available

**Symptom:** Sub-agent errors about missing MCP tools

**Cause:** Chrome DevTools MCP not configured

**Fix:**
```bash
# Check if configured
claude mcp list | grep chrome

# If not, add it
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest
```

---

## Sub-Agent Didn't Create Checkpoint

**Symptom:** After sub-agent returns, checkpoint file doesn't exist

**Possible causes:**
1. Sub-agent encountered an error before writing
2. File path issue (wrong directory)
3. Sub-agent used different output format

**Fixes:**
1. Check sub-agent output for errors
2. Verify `seed_data/temp/` directory exists:
   ```bash
   mkdir -p seed_data/temp
   ```
3. Re-run the batch

---

## Too Few Confirming Images

**Symptom:** Observatory marked rejected with "Only N confirming image(s) found"

**Cause:** 3-image consensus requirement not met

**Options:**
1. **Accept the rejection** - some observatories truly lack online imagery
2. **Manual research** - you can manually find and add images
3. **Lower threshold** - if you trust 2 images, manually add to validated_observatories.json

---

## Wrong Observatory Identified

**Symptom:** Images in challenge_evidence show a different observatory

**Cause:** Common names like "National Observatory" exist in multiple countries

**Prevention:**
- Sub-agents should verify country/location matches
- Check coordinates in the image context if visible

**Fix:**
- Remove incorrect entry from challenged_observatories.json before merging
- Add to confirmed_rejected manually

---

## Web Search Rate Limiting

**Symptom:** Sub-agent reports rate limits or empty search results

**Cause:** Too many searches in short period

**Fixes:**
1. Wait 5-10 minutes and retry
2. Use smaller batch sizes (3-5 instead of 5-8)
3. Spread research across multiple sessions

---

## Session Crashed Mid-Research

**Symptom:** Partial checkpoint files, incomplete research

**This is expected behavior!** The skill has crash recovery:

```bash
# Just run the skill again
/challenge-observatory-images

# It will detect existing checkpoint files and ask to resume
```

---

## Too Many Browser Windows

**Symptom:** System slowdown, browser crashes

**Cause:** Sub-agent not closing pages between validations

**The sub-agent prompt explicitly states to close each page, but if this happens:**

1. Close Chrome manually
2. Clear any stuck state:
   ```bash
   # Kill Chrome processes if needed
   pkill -f Chrome
   ```
3. Re-run the batch

---

## Checkpoint Format Issues

**Symptom:** Error during consolidation about missing keys

**Cause:** Sub-agent used non-standard output format

**Fix:** Check the checkpoint file structure:
```python
import json
with open('seed_data/temp/challenge_batch_001.json') as f:
    data = json.load(f)
print(json.dumps(data, indent=2))
```

Expected structure:
```json
{
  "batch_num": 1,
  "results": {
    "slug": {
      "status": "accepted|rejected",
      ...
    }
  }
}
```

If format differs, manually convert or re-run the batch.

---

## Merging Fails After Review

**Symptom:** Error when running the merge command from Step 6

**Common causes:**
1. `observatory_seeder` not importable
2. File path issues

**Fix - run from project root with correct Python:**
```bash
cd /Users/adiaz/starview
djvenv/bin/python -c "
import json
from observatory_seeder import merge_validated_observatories
# ... rest of merge code
"
```
