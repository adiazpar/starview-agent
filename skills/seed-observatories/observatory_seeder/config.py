"""
Configuration for the observatory seeder pipeline.

This module centralizes all configuration constants for the pipeline,
including API endpoints, rate limiting settings, and file paths.

Paths are detected dynamically to work from either location:
- .claude/skills/seed-observatories/observatory_seeder/ (skill package)
- tools/observatory_seeder/ (legacy location)
"""

from pathlib import Path


def _find_project_root() -> Path:
    """
    Find the project root by looking for known markers.

    Searches upward from this file for directories containing:
    - seed_data/ (output directory)
    - manage.py (Django marker)
    - .git/ (repo root)

    Returns Path to project root.
    """
    current = Path(__file__).resolve().parent

    # Walk up the directory tree
    for _ in range(10):  # Max 10 levels to prevent infinite loop
        if (current / "seed_data").exists():
            return current
        if (current / "manage.py").exists():
            return current
        if (current / ".git").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent

    # Fallback: assume 4 levels up from skill location
    # .claude/skills/seed-observatories/observatory_seeder/config.py
    return Path(__file__).resolve().parent.parent.parent.parent.parent


# Wikidata SPARQL endpoint
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

# Wikimedia Commons API
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# User agent for API requests (required by Wikimedia)
USER_AGENT = "StarviewApp/1.0 (https://starview.app; observatory-seeding)"

# Rate limiting (seconds between requests)
WIKIDATA_DELAY = 1.0       # Wikidata is lenient
COMMONS_DELAY = 3.0        # Wikimedia Commons API is stricter
IMAGE_DOWNLOAD_DELAY = 10.0  # Base delay for image downloads (also used for retry backoff)

# Image processing
MAX_IMAGE_DIMENSION = 1920  # Max width/height for stored images
JPEG_QUALITY = 85          # Quality for compressed images
TARGET_IMAGES_PER_OBSERVATORY = 5  # Max images to collect per location

# Output paths (relative to project root)
PROJECT_ROOT = _find_project_root()
TEMP_DIR = PROJECT_ROOT / "seed_data" / "temp"
OUTPUT_FILE = PROJECT_ROOT / "seed_data" / "validated_observatories.json"

# Validation thresholds
MIN_IMAGE_WIDTH = 640
MIN_IMAGE_HEIGHT = 480

# License patterns (permissive only)
ALLOWED_LICENSE_PATTERNS = [
    'cc by', 'cc-by', 'cc by-sa', 'cc-by-sa', 'cc0',
    'public domain', 'pd', 'attribution'
]
