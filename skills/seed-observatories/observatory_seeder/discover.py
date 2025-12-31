"""
Observatory discovery via Wikidata SPARQL queries.

Queries Wikidata for astronomical observatories with coordinates,
images, and metadata. No hardcoded observatories - everything is
discovered dynamically from Wikidata's knowledge graph.

Includes elevation unit detection/conversion and data validation.
"""

import re
import time
import requests
from dataclasses import dataclass, field

from .config import WIKIDATA_ENDPOINT, USER_AGENT, WIKIDATA_DELAY
from .url_validator import validate_website_url

# Elevation constants
FEET_TO_METERS = 0.3048
MIN_VALID_ELEVATION = -500  # Dead Sea area observatories
MAX_VALID_ELEVATION = 9000  # Higher than Everest = likely bad data
FEET_THRESHOLD = 9000  # If elevation > this, likely in feet


def normalize_elevation(raw_elevation: float | None, name: str = "") -> tuple[float | None, str]:
    """
    Normalize elevation to meters, detecting and converting feet if necessary.

    Wikidata P2044 should be in meters, but some entries have incorrect units.
    This function detects likely feet values and converts them.

    Args:
        raw_elevation: Raw elevation value from Wikidata
        name: Observatory name for logging

    Returns:
        Tuple of (normalized_elevation_meters, conversion_note)
    """
    if raw_elevation is None:
        return None, "no_elevation"

    # If within valid range, assume it's correct (meters)
    if MIN_VALID_ELEVATION <= raw_elevation <= MAX_VALID_ELEVATION:
        return raw_elevation, "meters"

    # If above threshold, check if converting from feet gives a valid value
    if raw_elevation > FEET_THRESHOLD:
        converted = raw_elevation * FEET_TO_METERS
        if MIN_VALID_ELEVATION <= converted <= MAX_VALID_ELEVATION:
            return round(converted, 1), "converted_from_feet"

    # If below minimum (very negative), might be inverted or wrong
    if raw_elevation < MIN_VALID_ELEVATION:
        # Try absolute value
        if MIN_VALID_ELEVATION <= abs(raw_elevation) <= MAX_VALID_ELEVATION:
            return abs(raw_elevation), "corrected_sign"

    # Value is invalid even after conversion attempts
    # Return None to let the seeder skip or handle
    return None, f"invalid_value_{raw_elevation}"


def normalize_phone(phone: str | None) -> tuple[str | None, str | None]:
    """
    Normalize phone number to E.164 format for tel: links.

    Returns tuple of (e164_format, display_format).
    """
    if not phone:
        return None, None

    # Remove all non-digit characters except leading +
    digits = re.sub(r'\D', '', phone)

    if not digits:
        return None, None

    # Reconstruct E.164 format
    e164 = f'+{digits}'

    # Create display format with dashes
    if len(digits) >= 10:
        if len(digits) == 10:
            # US/Canada format: +1-XXX-XXX-XXXX
            display = f'+1-{digits[:3]}-{digits[3:6]}-{digits[6:]}'
            e164 = f'+1{digits}'
        elif len(digits) == 11 and digits.startswith('1'):
            # US/Canada with country code
            display = f'+{digits[0]}-{digits[1:4]}-{digits[4:7]}-{digits[7:]}'
            e164 = f'+{digits}'
        else:
            # International: keep original formatting
            display = phone
            e164 = f'+{digits}'
    else:
        display = phone
        e164 = f'+{digits}'

    return e164, display


@dataclass
class Observatory:
    """Represents an observatory discovered from Wikidata."""
    wikidata_id: str
    name: str
    latitude: float
    longitude: float
    elevation: float | None
    country: str
    image_url: str | None
    website: str | None
    phone: str | None = None
    elevation_note: str = field(default="")  # Track if elevation was converted

    @property
    def slug(self) -> str:
        """
        Generate a URL-friendly slug from the name + wikidata_id suffix.

        The wikidata_id suffix prevents slug collisions for observatories
        with identical names (e.g., "Royal Observatory" in Greenwich vs Edinburgh).
        """
        import re
        slug = self.name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')[:50]
        # Add wikidata_id suffix to prevent collisions (e.g., "royal-observatory-q188759")
        wikidata_suffix = self.wikidata_id.lower() if self.wikidata_id else ''
        return f"{slug}-{wikidata_suffix}" if wikidata_suffix else slug

    @property
    def is_elevation_valid(self) -> bool:
        """Check if elevation is within valid range."""
        if self.elevation is None:
            return True  # No elevation is OK
        return MIN_VALID_ELEVATION <= self.elevation <= MAX_VALID_ELEVATION

    def build_type_metadata(self, validate_urls: bool = True) -> dict | None:
        """
        Build type_metadata dict with normalized phone and validated website.

        Website URLs are validated with soft 404 detection. Invalid URLs
        (soft 404s, connection errors) are excluded from metadata.
        Sub-agents can search for alternatives during validation phase.

        Args:
            validate_urls: If True, validate website URL with soft 404 detection.
                          If False, include URL as-is (for testing).

        Returns None if no phone or valid website available.
        """
        metadata = {}

        if self.phone:
            e164, display = normalize_phone(self.phone)
            if e164:
                metadata['phone_number'] = e164
                metadata['phone_display'] = display

        if self.website:
            if validate_urls:
                # Validate URL with soft 404 detection
                validation = validate_website_url(self.website)
                if validation['valid']:
                    # Use final_url (after redirects) or original
                    url = validation['final_url'] or self.website
                    # Prefer HTTPS if available
                    if url.startswith('http://'):
                        https_url = url.replace('http://', 'https://', 1)
                        https_validation = validate_website_url(https_url)
                        if https_validation['valid']:
                            url = https_url
                    metadata['website'] = url
                # If validation failed, website is excluded from metadata
                # Sub-agents can search for alternatives
            else:
                metadata['website'] = self.website

        return metadata if metadata else None


def discover_observatories(
    limit: int = 100,
    offset: int = 0,
    min_elevation: float | None = None,
    require_image: bool = False,
    country_filter: str | None = None,
) -> list[Observatory]:
    """
    Query Wikidata for astronomical observatories.

    Args:
        limit: Maximum number of observatories to return
        offset: Skip this many results (for pagination through all observatories)
        min_elevation: Filter to observatories above this elevation (meters)
        require_image: Only return observatories with images
        country_filter: Filter to specific country (English name)

    Returns:
        List of Observatory objects with validated data
    """
    # Build SPARQL query dynamically based on filters
    filters = []

    if min_elevation is not None:
        filters.append(f"FILTER(?elevation >= {min_elevation})")

    if require_image:
        filters.append("FILTER(BOUND(?image))")

    if country_filter:
        filters.append(f'FILTER(?countryLabel = "{country_filter}")')

    filter_clause = "\n  ".join(filters)

    query = f"""
    SELECT DISTINCT ?observatory ?observatoryLabel ?coord ?image ?countryLabel ?elevation ?website ?phone WHERE {{
      ?observatory wdt:P31/wdt:P279* wd:Q62832 .  # instance of astronomical observatory
      ?observatory wdt:P625 ?coord .               # has coordinates
      ?observatory rdfs:label ?observatoryLabel .
      FILTER(LANG(?observatoryLabel) = "en")

      OPTIONAL {{ ?observatory wdt:P18 ?image }}
      OPTIONAL {{
        ?observatory wdt:P17 ?country .
        ?country rdfs:label ?countryLabel .
        FILTER(LANG(?countryLabel) = "en")
      }}
      OPTIONAL {{ ?observatory wdt:P2044 ?elevation }}
      OPTIONAL {{ ?observatory wdt:P856 ?website }}
      OPTIONAL {{ ?observatory wdt:P1329 ?phone }}

      {filter_clause}
    }}
    ORDER BY DESC(?elevation)
    LIMIT {limit}
    OFFSET {offset}
    """

    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/sparql-results+json'
    }

    response = requests.get(
        WIKIDATA_ENDPOINT,
        params={'query': query, 'format': 'json'},
        headers=headers,
        timeout=60
    )
    response.raise_for_status()

    results = response.json().get('results', {}).get('bindings', [])
    observatories = []

    for r in results:
        # Parse coordinates from "Point(lon lat)" format
        coord = r.get('coord', {}).get('value', '')
        if not coord.startswith('Point('):
            continue

        parts = coord[6:-1].split()
        lon, lat = round(float(parts[0]), 3), round(float(parts[1]), 3)

        # Extract Wikidata ID from URI
        uri = r.get('observatory', {}).get('value', '')
        wikidata_id = uri.split('/')[-1] if uri else ''

        # Parse and normalize elevation
        elev_str = r.get('elevation', {}).get('value')
        raw_elevation = float(elev_str) if elev_str else None
        name = r.get('observatoryLabel', {}).get('value', 'Unknown')
        elevation, elevation_note = normalize_elevation(raw_elevation, name)

        obs = Observatory(
            wikidata_id=wikidata_id,
            name=name,
            latitude=lat,
            longitude=lon,
            elevation=elevation,
            country=r.get('countryLabel', {}).get('value', 'Unknown'),
            image_url=r.get('image', {}).get('value'),
            website=r.get('website', {}).get('value'),
            phone=r.get('phone', {}).get('value'),
            elevation_note=elevation_note,
        )
        observatories.append(obs)

    time.sleep(WIKIDATA_DELAY)
    return observatories


def get_total_observatory_count() -> int:
    """Get the total count of observatories with coordinates in Wikidata."""
    query = """
    SELECT (COUNT(DISTINCT ?observatory) as ?count) WHERE {
      ?observatory wdt:P31/wdt:P279* wd:Q62832 .
      ?observatory wdt:P625 ?coord .
    }
    """

    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'application/sparql-results+json'
    }

    response = requests.get(
        WIKIDATA_ENDPOINT,
        params={'query': query, 'format': 'json'},
        headers=headers,
        timeout=60
    )
    response.raise_for_status()

    count = response.json()['results']['bindings'][0]['count']['value']
    return int(count)


if __name__ == "__main__":
    # Test discovery
    print(f"Total observatories in Wikidata: {get_total_observatory_count()}")
    print("\nDiscovering top 10 observatories by elevation...")

    observatories = discover_observatories(limit=10, require_image=True)
    for obs in observatories:
        print(f"  {obs.name} ({obs.country}) - {obs.elevation}m")
        print(f"    Coords: {obs.latitude}, {obs.longitude}")
        print(f"    Image: {'Yes' if obs.image_url else 'No'}")
        print()
