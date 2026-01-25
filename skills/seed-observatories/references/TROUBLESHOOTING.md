# Troubleshooting Guide

Common issues and solutions for the seed-observatories skill.

---

## Self-installation failed

**Symptom:** Step 0 reports "Installation failed" with pip errors.

**Common causes:**
1. No write permissions to site-packages
2. Missing pip in the Python environment
3. Network issues downloading dependencies

**Fixes:**
```bash
# Check which Python is being used
which python

# Try manual installation
python -m pip install -e .claude/skills/seed-observatories/

# If permission error, check you're in a virtual environment
python -c "import sys; print(sys.prefix)"
```

---

## "ModuleNotFoundError: observatory_seeder"

**Symptom:** Import fails even after Step 0 says installation succeeded.

**Cause:** Python session needs restart after pip install, or wrong Python being used.

**Fixes:**
1. The skill should work - pip install was in-process
2. If running manually, ensure you use the same Python:
   ```bash
   # Check where it's installed
   pip show observatory-seeder

   # Use that Python
   djvenv/bin/python -c "from observatory_seeder import merge_validated_observatories"
   ```

---

## No virtual environment found

**Symptom:** Skill installs to system Python, causing permission errors.

**The skill auto-detects virtual environments in this order:**

1. `VIRTUAL_ENV` environment variable (already activated venv)
2. Common directory names in current directory:
   - `djvenv/` (Django convention)
   - `.venv/` (Python default)
   - `venv/`
   - `env/`
   - `.env/` (if it's a directory, not a file)
   - `virtualenv/`
3. Search upward (max 5 levels) for any of the above
4. Fall back to `sys.executable`

**If no venv exists**, create one first:
```bash
python -m venv .venv
.venv/bin/pip install -e .claude/skills/seed-observatories/
```

---

## Sub-agent uses different output format

**Symptom:** Checkpoint has unexpected structure (e.g., `image_status` instead of `validated`, array instead of object).

**This is expected.** Sub-agents may return various formats. The `normalize_checkpoint.py` script handles:
- Canonical format: `{"batch_num": N, "validated": {...}}`
- Old format: `{"batch_num": N, "results": [...]}`
- Array format: `[{slug, image_url, image_status}, ...]`

**If normalization fails:** Add a new case to `normalize_checkpoint.py` for the new format.

---

## Checkpoint missing validation data

**Symptom:** Checkpoint has observatory metadata but no acceptance/rejection indicators.

**Cause:** Sub-agent didn't actually validate images (just echoed input).

**Fix:**
1. Delete the checkpoint: `rm seed_data/temp/batch_NNN.json`
2. Re-run the skill (it will resume from missing batch)
3. Ensure Chrome DevTools MCP is working: `claude mcp list`

---

## Sub-agent doesn't create checkpoint

**Symptom:** Sub-agent returns but no `batch_NNN.json` file created.

**Causes:**
- Chrome DevTools MCP not configured
- Sub-agent encountered error and stopped early

**Fix:**
1. Check MCP is installed: `claude mcp list | grep chrome`
2. Check sub-agent's final output for errors
3. Manually create checkpoint if sub-agent provided validation info in text

---

## Slug not found in discovered.json

**Symptom:** During consolidation: `"Warning: {slug} not in discovered.json"`

**Cause:** Sub-agent modified or invented a slug that doesn't match input.

**Fix:** The warning is informational - that observatory is skipped. No action needed unless many slugs are missing.

---

## Chrome DevTools MCP not working

**Symptom:** Sub-agent can't open pages or take screenshots.

**Fix:**
```bash
# Check if installed
claude mcp list | grep chrome

# Install if missing
claude mcp add chrome-devtools npx chrome-devtools-mcp@latest
```

**Note:** Built-in Claude Chrome (`claude --chrome`) does NOT work for sub-agents since it's a CLI flag, not an inheritable tool. Only MCP tools are inherited by sub-agents.

---

## Session crashed mid-validation

**Symptom:** Validation stopped partway through.

**Fix:** Just re-run the skill:
```bash
/seed-observatories --limit 25
```

The skill automatically:
1. Detects existing `batch_*.json` checkpoint files
2. Asks whether to resume or start fresh
3. If resuming, continues from the next batch number

---

## Too many browser windows open

**Symptom:** Sub-agent opens multiple image pages simultaneously, causing slowdowns.

**Cause:** Sub-agent not following "one page at a time" rule for fallback validation.

**Fix:** The sub-agent prompt explicitly states:
> IMPORTANT: Only have ONE image page open at a time. Close each page before opening the next.

If this keeps happening, remind sub-agents in the prompt or add explicit close commands between validations.
