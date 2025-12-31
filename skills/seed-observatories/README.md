# Observatory Seeder Skill

Self-contained Claude Code skill for seeding observatory locations from Wikidata with AI-validated images.

## Installation

**Automatic:** The skill self-installs on first run. No manual setup needed.

**Manual:** If you prefer to install explicitly:

```bash
# With a virtual environment
pip install -e .claude/skills/seed-observatories/

# Or specify your Python
python -m pip install -e .claude/skills/seed-observatories/
```

The skill auto-detects your Python environment:
1. Prefers `djvenv/bin/python` if it exists (Django projects)
2. Falls back to the current Python interpreter

## Usage

### Via Claude Code Skill

```bash
/seed-observatories --limit 20
```

### Via Command Line

```bash
# Discover observatories from Wikidata
observatory-seeder --discover --limit 25

# With filters
observatory-seeder --discover --limit 50 --country "Chile" --min-elevation 2000
```

### Via Python

```python
from observatory_seeder import (
    discover_observatories,
    merge_validated_observatories,
    search_wikimedia_commons,
)

# Discover observatories
observatories = discover_observatories(limit=10, require_image=True)

# Search for fallback images
results = search_wikimedia_commons("Keck Observatory")
```

## Package Contents

```
seed-observatories/
├── SKILL.md                 # Claude Code skill documentation
├── TROUBLESHOOTING.md       # Common issues and solutions
├── METRICS_TEMPLATES.md     # Output display templates
├── normalize_checkpoint.py  # Checkpoint normalization script
├── pyproject.toml           # Python package configuration
├── README.md                # This file
└── observatory_seeder/      # Python package
    ├── __init__.py          # Public API
    ├── config.py            # Configuration constants
    ├── discover.py          # Wikidata SPARQL queries
    ├── download.py          # Image downloading
    ├── run.py               # CLI entry point
    ├── url_validator.py     # URL validation with soft 404 detection
    └── validate.py          # Validation utilities
```

## Features

- **Wikidata Discovery**: Query 3,484+ observatories with coordinates, images, and metadata
- **Soft 404 Detection**: Multi-language URL validation catches fake error pages
- **AI Image Validation**: Sub-agents validate images show actual observatory structures
- **Crash Recovery**: Checkpoint-based system survives session interruptions
- **Rate Limiting**: Smart backoff for Wikimedia API compliance

## License

MIT
