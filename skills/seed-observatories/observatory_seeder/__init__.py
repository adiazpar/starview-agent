"""
Observatory Seeder Pipeline

A comprehensive pipeline for discovering observatories from Wikidata,
downloading images, and preparing data for AI validation.

Features:
    - Dynamic observatory discovery from Wikidata (3,484+ observatories)
    - Elevation unit detection and conversion (feet/meters)
    - Image downloading with rate limiting
    - Wikimedia Commons fallback for rejected images
    - AI validation via Claude Code vision
    - URL validation with soft 404 detection and web search fallback

Modules:
    config: Configuration constants
    discover: Wikidata SPARQL queries for observatory discovery
    download: Image downloading with rate limiting and fallback
    url_validator: Website URL validation with soft 404 detection
    run: Main orchestration script

Usage:
    python -m observatory_seeder.run --discover --limit 5
    observatory-seeder --discover --limit 5
"""

from .discover import (
    Observatory,
    discover_observatories,
    get_total_observatory_count,
    normalize_elevation,
)
from .download import (
    download_observatory_image,
    download_fallback_images,
    search_wikimedia_commons,
    cleanup_temp_directory,
    reset_rate_limit_state,
)
from .validate import (
    get_pending_validations,
    generate_validated_json,
    merge_validated_observatories,
    get_observatory_by_slug,
    list_observatory_images,
)
from .url_validator import (
    validate_website_url,
    search_observatory_website,
    find_best_website_url,
    SOFT_404_PATTERNS,
)
from .config import TEMP_DIR, OUTPUT_FILE
from .normalize_checkpoint import normalize_checkpoint, normalize_file

__all__ = [
    # Discovery
    'Observatory',
    'discover_observatories',
    'get_total_observatory_count',
    'normalize_elevation',
    # Download
    'download_observatory_image',
    'download_fallback_images',
    'search_wikimedia_commons',
    'cleanup_temp_directory',
    'reset_rate_limit_state',
    # Validation
    'get_pending_validations',
    'generate_validated_json',
    'merge_validated_observatories',
    'get_observatory_by_slug',
    'list_observatory_images',
    # URL Validation
    'validate_website_url',
    'search_observatory_website',
    'find_best_website_url',
    'SOFT_404_PATTERNS',
    # Config
    'TEMP_DIR',
    'OUTPUT_FILE',
    # Checkpoint normalization
    'normalize_checkpoint',
    'normalize_file',
]
