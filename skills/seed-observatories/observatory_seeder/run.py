#!/usr/bin/env python3
"""
Observatory Seeder Pipeline - Main Entry Point

This script discovers observatories from Wikidata and prepares data for
AI validation via Claude Code's seed-observatories skill.

Usage:
    python -m tools.observatory_seeder.run --discover --limit 25
    python -m tools.observatory_seeder.run --cleanup

The validation step is handled by Claude Code sub-agents with Chrome DevTools MCP.
Images are validated directly via browser, then downloaded during final seeding.
"""

import argparse
import json
import os
import sys
from pathlib import Path

from .config import TEMP_DIR, OUTPUT_FILE
from .discover import discover_observatories, get_total_observatory_count
from .download import cleanup_temp_directory


def _setup_django():
    """Initialize Django settings for database access."""
    import django
    from django.conf import settings
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
        django.setup()


def run_discovery(
    limit: int = 100,
    offset: int = 0,
    min_elevation: float | None = None,
    country: str | None = None,
) -> list[dict]:
    """
    Phase 1: Discover observatories from Wikidata.

    Returns list of observatory data ready for image download.
    """
    print("=" * 60)
    print("PHASE 1: OBSERVATORY DISCOVERY")
    print("=" * 60)

    total = get_total_observatory_count()
    print(f"\nTotal observatories in Wikidata: {total:,}")

    print(f"\nDiscovering observatories (limit={limit}, offset={offset})...")
    if min_elevation:
        print(f"  Filter: elevation >= {min_elevation}m")
    if country:
        print(f"  Filter: country = {country}")

    observatories = discover_observatories(
        limit=limit,
        offset=offset,
        min_elevation=min_elevation,
        require_image=True,  # Always require images for seeding
        country_filter=country,
    )

    print(f"\nFound {len(observatories)} observatories:\n")

    results = []
    for i, obs in enumerate(observatories, 1):
        print(f"{i:3}. {obs.name}")
        print(f"     Coords: {obs.latitude:.4f}, {obs.longitude:.4f}")
        print(f"     Image: {'Yes' if obs.image_url else 'No'}")

        # Build type_metadata with normalized phone (NO URL validation yet)
        # URL validation happens AFTER dedupe to avoid wasting time on duplicates
        type_metadata = obs.build_type_metadata(validate_urls=False)

        # Note: country and elevation are NOT included in output
        # Mapbox enrichment provides accurate values during seeding
        entry = {
            'wikidata_id': obs.wikidata_id,
            'slug': obs.slug,
            'name': obs.name,
            'latitude': obs.latitude,
            'longitude': obs.longitude,
            'image_url': obs.image_url,
        }
        if type_metadata:
            entry['type_metadata'] = type_metadata

        results.append(entry)

    # Save discovery results
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    discovery_file = TEMP_DIR / "discovered.json"
    with open(discovery_file, 'w') as f:
        json.dump({'observatories': results}, f, indent=2)

    print(f"\nSaved discovery results to: {discovery_file}")
    return results


def run_dedupe() -> list[dict]:
    """
    Phase 1.5: Remove observatories that already exist in the JSON file.

    Compares discovered observatories against validated_observatories.json
    and removes duplicates before validation. The seed_locations command
    handles database deduplication separately.
    """
    print("\n" + "=" * 60)
    print("PHASE 1.5: DEDUPE AGAINST JSON")
    print("=" * 60)

    discovery_file = TEMP_DIR / "discovered.json"
    if not discovery_file.exists():
        print("Error: No discovery file found. Run --discover first.")
        return []

    with open(discovery_file) as f:
        data = json.load(f)

    observatories = data.get('observatories', [])
    original_count = len(observatories)
    print(f"\nDiscovered observatories: {original_count}")

    # Load existing validated observatories from JSON
    existing_set = set()
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE) as f:
            existing_data = json.load(f)
            for obs in existing_data.get('observatories', []):
                # Use coordinates only (rounded to 2 decimals ~1km precision)
                # to catch duplicates with different names but same location
                lat = round(obs.get('latitude', 0), 2)
                lon = round(obs.get('longitude', 0), 2)
                existing_set.add((lat, lon))

    print(f"Existing observatories in JSON: {len(existing_set)}")

    # Filter out duplicates by coordinates
    new_observatories = []
    duplicates = []
    seen_coords = set()
    for obs in observatories:
        key = (round(obs['latitude'], 2), round(obs['longitude'], 2))
        if key in existing_set:
            duplicates.append(obs['name'])
        elif key in seen_coords:
            # Also dedupe within the discovered batch
            duplicates.append(f"{obs['name']} (duplicate coords in batch)")
        else:
            seen_coords.add(key)
            new_observatories.append(obs)

    # Save deduped results back
    with open(discovery_file, 'w') as f:
        json.dump({'observatories': new_observatories}, f, indent=2)

    print(f"\nDuplicates found: {len(duplicates)}")
    if duplicates:
        for name in duplicates[:10]:  # Show first 10
            print(f"  - {name}")
        if len(duplicates) > 10:
            print(f"  ... and {len(duplicates) - 10} more")

    print(f"\nNew observatories to process: {len(new_observatories)}")
    print(f"Saved deduped list to: {discovery_file}")

    return new_observatories


def run_url_validation() -> list[dict]:
    """
    Phase 2: Validate website URLs for new observatories (after dedupe).

    Only runs on observatories that passed dedupe - avoids wasting time
    validating URLs for observatories we're going to discard.
    """
    from .url_validator import validate_website_url

    print("\n" + "=" * 60)
    print("PHASE 2: URL VALIDATION (Soft 404 Detection)")
    print("=" * 60)

    discovery_file = TEMP_DIR / "discovered.json"
    if not discovery_file.exists():
        print("Error: No discovery file found.")
        return []

    with open(discovery_file) as f:
        data = json.load(f)

    observatories = data.get('observatories', [])
    if not observatories:
        print("No observatories to validate.")
        return []

    print(f"\nValidating URLs for {len(observatories)} new observatories...")

    valid_count = 0
    invalid_count = 0
    no_url_count = 0

    for obs in observatories:
        metadata = obs.get('type_metadata', {})
        website = metadata.get('website')

        if not website:
            no_url_count += 1
            continue

        result = validate_website_url(website)

        if result['valid']:
            valid_count += 1
            # Use final_url (after redirects) and try HTTPS upgrade
            final_url = result['final_url'] or website
            if final_url.startswith('http://'):
                https_url = final_url.replace('http://', 'https://', 1)
                https_result = validate_website_url(https_url, timeout=5)
                if https_result['valid']:
                    final_url = https_url
            metadata['website'] = final_url
        else:
            invalid_count += 1
            # Remove invalid URL from metadata
            del metadata['website']
            if not metadata:
                obs['type_metadata'] = None
            print(f"  Invalid: {obs['name'][:40]} - {result['reason']}")

        # Update type_metadata (might be empty now)
        if metadata:
            obs['type_metadata'] = metadata
        elif 'type_metadata' in obs:
            del obs['type_metadata']

    # Save validated results
    with open(discovery_file, 'w') as f:
        json.dump({'observatories': observatories}, f, indent=2)

    print(f"\nURL Validation Results:")
    print(f"  Valid:   {valid_count}")
    print(f"  Invalid: {invalid_count} (removed from metadata)")
    print(f"  No URL:  {no_url_count}")

    return observatories


def main():
    parser = argparse.ArgumentParser(
        description='Observatory Seeder Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Discover 25 observatories:
    python -m tools.observatory_seeder.run --discover --limit 25

  Discover with offset (pagination):
    python -m tools.observatory_seeder.run --discover --limit 25 --offset 50

  Clean up temp files:
    python -m tools.observatory_seeder.run --cleanup

Note: Discovery automatically dedupes against validated_observatories.json.
      Validation is handled by the /seed-observatories skill.
        """
    )

    parser.add_argument('--discover', action='store_true',
                        help='Discover observatories from Wikidata (auto-dedupes)')
    parser.add_argument('--cleanup', action='store_true',
                        help='Clean up temp directory')

    # Discovery options
    parser.add_argument('--limit', type=int, default=100,
                        help='Max observatories to discover (default: 100)')
    parser.add_argument('--offset', type=int, default=0,
                        help='Skip first N observatories (for pagination)')
    parser.add_argument('--min-elevation', type=float,
                        help='Filter by minimum elevation (meters)')
    parser.add_argument('--country', type=str,
                        help='Filter by country name')

    args = parser.parse_args()

    if args.cleanup:
        cleanup_temp_directory()
        return

    if not args.discover:
        parser.print_help()
        return

    if args.discover:
        run_discovery(
            limit=args.limit,
            offset=args.offset,
            min_elevation=args.min_elevation,
            country=args.country,
        )
        # Always dedupe after discovery
        remaining = run_dedupe()
        if not remaining:
            print("\nNo new observatories to process. Pipeline complete.")
            return

        # Validate URLs only for new observatories (after dedupe)
        run_url_validation()

    print("\n" + "=" * 60)
    print("NEXT STEP: Run AI validation via Claude Code")
    print("=" * 60)
    print("\nThe discovered observatories are ready for image validation.")
    print("Sub-agents will validate each image shows an actual observatory")
    print("structure (not astronomical images).\n")


if __name__ == "__main__":
    main()
