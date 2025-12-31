"""
Image downloading with rate limiting, compression, and batch processing.

Downloads images from Wikimedia Commons URLs with smart rate limit handling:
- Global cooldown when rate limited (backs off all requests)
- Batch breaks every 5 downloads to prevent rate limit accumulation
- Exponential backoff for individual retry attempts

Includes fallback search on Wikimedia Commons when primary image is rejected.
"""

import io
import time
from pathlib import Path

import requests
from PIL import Image

from .config import (
    USER_AGENT,
    COMMONS_API,
    COMMONS_DELAY,
    IMAGE_DOWNLOAD_DELAY,
    MAX_IMAGE_DIMENSION,
    JPEG_QUALITY,
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
    ALLOWED_LICENSE_PATTERNS,
    TEMP_DIR,
)


# Global rate limit state
_rate_limit_state = {
    'downloads_since_break': 0,
    'last_429_time': 0,
    'global_cooldown_until': 0,
}

# Batch configuration
BATCH_SIZE = 5           # Downloads before mandatory break
BATCH_BREAK_SECONDS = 60  # Seconds to pause between batches
GLOBAL_COOLDOWN_SECONDS = 180  # 3-minute cooldown after 429


def _check_global_cooldown():
    """Wait if we're in a global cooldown period."""
    now = time.time()
    if now < _rate_limit_state['global_cooldown_until']:
        wait_time = _rate_limit_state['global_cooldown_until'] - now
        print(f"    Global cooldown active. Waiting {wait_time:.0f}s...")
        time.sleep(wait_time)


def _trigger_global_cooldown():
    """Trigger a global cooldown after hitting rate limit."""
    _rate_limit_state['last_429_time'] = time.time()
    _rate_limit_state['global_cooldown_until'] = time.time() + GLOBAL_COOLDOWN_SECONDS
    print(f"    Triggering {GLOBAL_COOLDOWN_SECONDS}s global cooldown...")
    time.sleep(GLOBAL_COOLDOWN_SECONDS)


def _check_batch_break():
    """Check if we need a batch break and take it if so."""
    _rate_limit_state['downloads_since_break'] += 1
    if _rate_limit_state['downloads_since_break'] >= BATCH_SIZE:
        print(f"    Batch break: pausing {BATCH_BREAK_SECONDS}s after {BATCH_SIZE} downloads...")
        time.sleep(BATCH_BREAK_SECONDS)
        _rate_limit_state['downloads_since_break'] = 0


def reset_rate_limit_state():
    """Reset the global rate limit state. Call at start of new pipeline run."""
    _rate_limit_state['downloads_since_break'] = 0
    _rate_limit_state['last_429_time'] = 0
    _rate_limit_state['global_cooldown_until'] = 0


def download_image(url: str, max_retries: int = 3) -> bytes | None:
    """
    Download an image from a URL with retry logic for rate limiting.

    Uses exponential backoff when hitting 429 (Too Many Requests) errors.
    On first 429, triggers a global cooldown to let rate limits reset.

    Args:
        url: The image URL to download
        max_retries: Maximum retry attempts for rate limit errors

    Returns:
        Image bytes or None if download failed
    """
    # Check if we're in global cooldown
    _check_global_cooldown()

    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                url,
                headers={'User-Agent': USER_AGENT},
                timeout=60
            )
            response.raise_for_status()
            return response.content

        except requests.exceptions.HTTPError as e:
            # Check if rate limited (429)
            if hasattr(e, 'response') and e.response is not None and e.response.status_code == 429:
                if attempt == 0:
                    # First 429 - trigger global cooldown
                    _trigger_global_cooldown()
                    continue
                elif attempt < max_retries:
                    # Subsequent retries use shorter backoff
                    wait_time = 30 * (attempt + 1)  # 60s, 90s
                    print(f"    Still rate limited. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"    Rate limited (429). Max retries exceeded.")
                    return None
            else:
                print(f"    Download error: {e}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"    Download error: {e}")
            return None

        except Exception as e:
            print(f"    Unexpected error: {e}")
            return None

    return None


def compress_image(image_bytes: bytes) -> bytes | None:
    """
    Compress image to reasonable size while maintaining quality.

    Args:
        image_bytes: Raw image bytes

    Returns:
        Compressed JPEG bytes or None if processing failed
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Skip if too small
        if img.width < MIN_IMAGE_WIDTH or img.height < MIN_IMAGE_HEIGHT:
            print(f"    Image too small: {img.width}x{img.height}")
            return None

        # Convert to RGB if needed (handles PNG/RGBA)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                background.paste(img, mask=img.split()[-1])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Resize if too large
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)

        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=JPEG_QUALITY, optimize=True)
        return output.getvalue()

    except Exception as e:
        print(f"    Compression error: {e}")
        return None


def search_wikimedia_commons(search_term: str, limit: int = 10) -> list[dict]:
    """
    Search Wikimedia Commons for images matching a search term.

    This is used as a fallback when the primary Wikidata image is rejected.
    Searches for CC-licensed images with good resolution.

    Args:
        search_term: Observatory name or search query
        limit: Maximum results to return

    Returns:
        List of image metadata dicts with 'url', 'title', 'width', 'height', 'license'
    """
    # Add "observatory" or "telescope" to improve relevance
    enhanced_terms = [
        f"{search_term} observatory",
        f"{search_term} telescope",
        f"{search_term} dome",
        search_term,
    ]

    results = []
    seen_urls = set()

    for term in enhanced_terms:
        if len(results) >= limit:
            break

        params = {
            'action': 'query',
            'generator': 'search',
            'gsrnamespace': '6',  # File namespace
            'gsrsearch': f'filetype:bitmap {term}',
            'gsrlimit': str(min(limit, 10)),
            'prop': 'imageinfo',
            'iiprop': 'url|size|extmetadata|mime',
            'format': 'json',
        }

        try:
            response = requests.get(
                COMMONS_API,
                params=params,
                headers={'User-Agent': USER_AGENT},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            print(f"    Commons search error: {e}")
            continue

        if 'query' not in data or 'pages' not in data['query']:
            continue

        for page in data['query']['pages'].values():
            if 'imageinfo' not in page:
                continue

            info = page['imageinfo'][0]
            metadata = info.get('extmetadata', {})

            # Check license
            license_short = metadata.get('LicenseShortName', {}).get('value', '').lower()
            is_allowed = any(p in license_short for p in ALLOWED_LICENSE_PATTERNS)
            if not is_allowed:
                continue

            # Check size
            width = info.get('width', 0)
            height = info.get('height', 0)
            if width < MIN_IMAGE_WIDTH or height < MIN_IMAGE_HEIGHT:
                continue

            # Check mime type
            mime = info.get('mime', '')
            if not mime.startswith('image/') or 'svg' in mime:
                continue

            url = info.get('url')
            if url in seen_urls:
                continue
            seen_urls.add(url)

            results.append({
                'url': url,
                'title': page.get('title', ''),
                'width': width,
                'height': height,
                'license': license_short,
                'description': metadata.get('ImageDescription', {}).get('value', '')[:200],
            })

        time.sleep(COMMONS_DELAY)

    # Sort by resolution (higher is better)
    results.sort(key=lambda x: x['width'] * x['height'], reverse=True)
    return results[:limit]


def download_fallback_images(
    observatory_name: str,
    observatory_slug: str,
    max_images: int = 5,
) -> list[Path]:
    """
    Search Wikimedia Commons and download candidate images for an observatory.

    Used when the primary Wikidata image is rejected during validation.

    Args:
        observatory_name: Full name of the observatory
        observatory_slug: Slug for directory naming
        max_images: Maximum images to download

    Returns:
        List of paths to downloaded images
    """
    print(f"    Searching Wikimedia Commons for fallback images...")

    candidates = search_wikimedia_commons(observatory_name, limit=max_images * 2)
    print(f"    Found {len(candidates)} candidates")

    downloaded = []
    for i, candidate in enumerate(candidates):
        if len(downloaded) >= max_images:
            break

        path = download_observatory_image(
            observatory_slug,
            candidate['url'],
            image_number=len(downloaded) + 1,
        )
        if path:
            downloaded.append(path)

    return downloaded


def download_observatory_image(
    observatory_slug: str,
    image_url: str,
    image_number: int = 1,
) -> Path | None:
    """
    Download and save an observatory image to temp directory.

    Includes batch break logic - pauses every 5 downloads to avoid rate limits.

    Args:
        observatory_slug: Slug for the observatory (used in path)
        image_url: URL to download from
        image_number: Sequential number for the image

    Returns:
        Path to saved image or None if failed
    """
    # Create observatory temp directory
    obs_dir = TEMP_DIR / observatory_slug
    obs_dir.mkdir(parents=True, exist_ok=True)

    # Download
    print(f"    Downloading image {image_number}...")
    image_bytes = download_image(image_url)
    if not image_bytes:
        return None

    # Compress
    compressed = compress_image(image_bytes)
    if not compressed:
        return None

    # Save
    filename = f"{image_number:02d}.jpg"
    filepath = obs_dir / filename
    filepath.write_bytes(compressed)

    size_kb = len(compressed) / 1024
    print(f"    Saved: {filename} ({size_kb:.0f}KB)")

    # Standard delay + check for batch break
    time.sleep(IMAGE_DOWNLOAD_DELAY)
    _check_batch_break()

    return filepath


def cleanup_temp_directory():
    """Remove all files from the temp directory."""
    import shutil
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
        print(f"Cleaned up temp directory: {TEMP_DIR}")


if __name__ == "__main__":
    # Test download
    test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/3/37/Keck_Observatory_2019.jpg/1280px-Keck_Observatory_2019.jpg"
    print("Testing image download...")
    path = download_observatory_image("test-observatory", test_url, 1)
    if path:
        print(f"Success: {path}")
    cleanup_temp_directory()
