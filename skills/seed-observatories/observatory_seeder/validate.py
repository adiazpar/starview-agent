"""
Observatory image validation utilities.

Provides data structures and helpers for the validation workflow.
Actual image validation is done by Claude Code's vision capabilities.
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

from .config import TEMP_DIR, OUTPUT_FILE


@dataclass
class ValidationResult:
    """Result of validating a single image."""
    slug: str
    image_path: str
    accepted: bool
    notes: str = ""
    image_url: str | None = None  # For accepted images, the URL to use


def get_pending_validations() -> list[dict]:
    """
    Get list of observatories with downloaded images pending validation.

    Returns list of dicts with observatory metadata and image paths.
    """
    discovery_file = TEMP_DIR / "discovered.json"
    if not discovery_file.exists():
        return []

    with open(discovery_file) as f:
        data = json.load(f)

    pending = []
    for obs in data.get('observatories', []):
        slug = obs['slug']
        obs_dir = TEMP_DIR / slug

        if not obs_dir.exists():
            continue

        # Find all images for this observatory
        images = sorted(obs_dir.glob('*.jpg'))
        if not images:
            continue

        pending.append({
            **obs,
            'image_paths': [str(p) for p in images],
            'image_count': len(images),
        })

    return pending


def generate_validated_json(results: list[dict]) -> Path:
    """
    Generate the validated_observatories.json file from validation results.

    Args:
        results: List of validated observatory dicts with:
            - name, latitude, longitude
            - image_url: The validated image URL
            - validation_notes: Why it was accepted
        Note: country and elevation are provided by Mapbox during seeding

    Returns:
        Path to the generated JSON file
    """
    output = {
        "version": "3.0",
        "source": "Wikidata + Claude Code AI validation",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_validated": len(results),
        "observatories": results
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    return OUTPUT_FILE


def _truncate_coord(val: float, decimals: int = 3) -> float:
    """Truncate coordinate to N decimal places for consistent comparison."""
    multiplier = 10 ** decimals
    return int(val * multiplier) / multiplier


def _normalize_name(name: str) -> str:
    """Normalize observatory name for deduplication."""
    import re
    # Lowercase, remove special chars, collapse whitespace
    normalized = name.lower().strip()
    normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized


def _make_dedupe_key(obs: dict) -> tuple:
    """
    Create a deduplication key from observatory data.

    Uses truncated coordinates (3 decimals ~111m precision) + normalized name.
    This catches:
    - Same location with different names (coordinate match)
    - Same name at same location (both match)

    While allowing:
    - Same name at different locations (e.g., "Royal Observatory" Greenwich vs Edinburgh)
    """
    lat = _truncate_coord(obs.get('latitude', 0), 3)
    lon = _truncate_coord(obs.get('longitude', 0), 3)
    name = _normalize_name(obs.get('name', ''))
    return (lat, lon, name)


def merge_validated_observatories(new_observatories: list[dict]) -> tuple[Path, int, int]:
    """
    Merge new observatories into validated_observatories.json, avoiding duplicates.

    Reads existing file, merges new entries (deduping by name + coords),
    and writes combined result. This allows the JSON to accumulate over
    multiple skill runs for production deployment.

    Args:
        new_observatories: List of newly validated observatory dicts

    Returns:
        Tuple of (output_path, total_count, new_count)
    """
    existing = []
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            data = json.load(f)
            existing = data.get('observatories', [])

    # Build set of existing keys for deduplication
    existing_keys = {_make_dedupe_key(obs) for obs in existing}

    # Add only new observatories that don't already exist
    added = 0
    for obs in new_observatories:
        key = _make_dedupe_key(obs)
        if key not in existing_keys:
            existing.append(obs)
            existing_keys.add(key)
            added += 1

    # Sort by name for consistent ordering
    existing.sort(key=lambda x: x.get('name', '').lower())

    # Write merged result
    output = {
        "version": "3.0",
        "source": "Wikidata + Claude Code AI validation",
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_validated": len(existing),
        "observatories": existing
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    return OUTPUT_FILE, len(existing), added


def get_observatory_by_slug(slug: str) -> dict | None:
    """Get observatory metadata by slug from discovered.json."""
    discovery_file = TEMP_DIR / "discovered.json"
    if not discovery_file.exists():
        return None

    with open(discovery_file) as f:
        data = json.load(f)

    for obs in data.get('observatories', []):
        if obs['slug'] == slug:
            return obs

    return None


def list_observatory_images(slug: str) -> list[Path]:
    """List all downloaded images for an observatory."""
    obs_dir = TEMP_DIR / slug
    if not obs_dir.exists():
        return []
    return sorted(obs_dir.glob('*.jpg'))
