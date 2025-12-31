"""
URL Validation Module for Observatory Seeder

Provides three-tier URL validation:
1. Content-based validation with soft 404 detection
2. Web search fallback for missing/invalid URLs
3. AI vision validation (handled by sub-agents)

This module handles Tier 1 and Tier 2. Tier 3 is performed by sub-agents
with Chrome DevTools MCP access.
"""

import re
import requests
from urllib.parse import urlparse


# Soft 404 detection patterns (multi-language)
# These patterns indicate error pages that return HTTP 200
SOFT_404_PATTERNS = [
    # English
    r'\b404\b',
    r'not\s+found',
    r'page\s+not\s+found',
    r'error\s+page',
    r'does\s+not\s+exist',
    r'no\s+longer\s+available',
    r'page\s+missing',
    r'page\s+unavailable',
    r'content\s+not\s+found',
    r'resource\s+not\s+found',
    # Spanish
    r'p[aá]gina\s+no\s+encontrada',
    r'no\s+existe',
    r'error\s+404',
    r'no\s+disponible',
    # German
    r'seite\s+nicht\s+gefunden',
    r'fehler\s+404',
    # French
    r'page\s+introuvable',
    r'page\s+non\s+trouv[ée]e',
    # Generic indicators
    r'under\s+construction',
    r'coming\s+soon',
    r'domain\s+for\s+sale',
    r'parked\s+domain',
    r'this\s+domain',
    r'buy\s+this\s+domain',
    r'website\s+expired',
    r'account\s+suspended',
]

# Compile patterns for efficiency
SOFT_404_REGEX = re.compile(
    '|'.join(SOFT_404_PATTERNS),
    re.IGNORECASE
)

# Minimum content length to consider page valid (bytes)
MIN_CONTENT_LENGTH = 1000

# Request timeout in seconds
REQUEST_TIMEOUT = 10

# User agent for requests
USER_AGENT = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)


def validate_website_url(url: str, timeout: int = REQUEST_TIMEOUT) -> dict:
    """
    Validate a website URL with soft 404 detection.

    Performs HTTP GET request and analyzes response for:
    - HTTP status code (hard 404s, redirects, etc.)
    - Page content patterns indicating error pages
    - Content length (very short pages are suspicious)

    Args:
        url: The URL to validate
        timeout: Request timeout in seconds

    Returns:
        {
            'valid': bool,
            'status_code': int | None,
            'reason': str,
            'final_url': str | None,  # After redirects
            'is_soft_404': bool,
            'content_length': int,
        }
    """
    result = {
        'valid': False,
        'status_code': None,
        'reason': '',
        'final_url': None,
        'is_soft_404': False,
        'content_length': 0,
    }

    if not url:
        result['reason'] = 'No URL provided'
        return result

    # Ensure URL has scheme
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(
            url,
            timeout=timeout,
            headers=headers,
            allow_redirects=True
        )

        result['status_code'] = response.status_code
        result['final_url'] = response.url
        result['content_length'] = len(response.content)

        # Check HTTP status
        if response.status_code >= 400:
            result['reason'] = f'HTTP {response.status_code}'
            return result

        # Check for redirects to error pages
        if response.status_code in (301, 302, 303, 307, 308):
            # Redirect without following - suspicious
            result['reason'] = f'Redirect to {response.url}'
            return result

        # Get text content for pattern matching
        try:
            content = response.text.lower()
        except Exception:
            content = ''

        # Check content length
        if result['content_length'] < MIN_CONTENT_LENGTH:
            # Very short page - check if it's an error
            if SOFT_404_REGEX.search(content):
                result['is_soft_404'] = True
                result['reason'] = 'Soft 404 detected (short page with error content)'
                return result
            # Short but no error pattern - might be valid (some sites are minimal)

        # Check for soft 404 patterns in content
        # Look in first 5000 chars (usually where error messages appear)
        content_to_check = content[:5000]
        if SOFT_404_REGEX.search(content_to_check):
            # Found error pattern - but check if it's in navigation/footer
            # Count occurrences - multiple matches = likely error page
            matches = SOFT_404_REGEX.findall(content_to_check)
            if len(matches) >= 2 or '404' in content_to_check:
                result['is_soft_404'] = True
                result['reason'] = f'Soft 404 detected (found: {matches[:3]})'
                return result

        # Check page title for error indicators
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
        if title_match:
            title = title_match.group(1).lower()
            if SOFT_404_REGEX.search(title):
                result['is_soft_404'] = True
                result['reason'] = f'Error in page title: {title[:50]}'
                return result

        # All checks passed
        result['valid'] = True
        result['reason'] = 'Valid'
        return result

    except requests.exceptions.Timeout:
        result['reason'] = 'Request timeout'
        return result
    except requests.exceptions.SSLError:
        result['reason'] = 'SSL certificate error'
        return result
    except requests.exceptions.ConnectionError:
        result['reason'] = 'Connection failed'
        return result
    except requests.exceptions.RequestException as e:
        result['reason'] = f'Request error: {str(e)[:50]}'
        return result


def search_observatory_website(
    name: str,
    country: str | None = None,
    search_func=None
) -> list[dict]:
    """
    Search for observatory's official website.

    This function generates search queries but requires a search_func
    to be provided (typically Claude's WebSearch tool wrapper).

    Args:
        name: Observatory name
        country: Optional country for more specific search
        search_func: Callable that takes query string, returns search results
                    Expected format: [{'url': str, 'title': str, 'snippet': str}, ...]

    Returns:
        List of candidates with scores:
        [{'url': str, 'title': str, 'snippet': str, 'score': float}]
    """
    if not search_func:
        return []

    # Build search queries (try in order)
    queries = [
        f'"{name}" official website',
        f'"{name}" observatory',
    ]
    if country:
        queries.append(f'"{name}" {country} observatory')

    candidates = []
    seen_domains = set()

    for query in queries:
        try:
            results = search_func(query)
            if not results:
                continue

            for result in results:
                url = result.get('url', '')
                if not url:
                    continue

                # Extract domain for deduplication
                try:
                    domain = urlparse(url).netloc.lower()
                except Exception:
                    continue

                if domain in seen_domains:
                    continue
                seen_domains.add(domain)

                # Score the result
                score = _score_search_result(result, name)

                candidates.append({
                    'url': url,
                    'title': result.get('title', ''),
                    'snippet': result.get('snippet', ''),
                    'score': score,
                })

        except Exception:
            continue

    # Sort by score (highest first)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:5]  # Return top 5


def _score_search_result(result: dict, observatory_name: str) -> float:
    """
    Score a search result for likelihood of being official observatory website.

    Higher score = more likely to be official.
    """
    score = 0.0
    url = result.get('url', '').lower()
    title = result.get('title', '').lower()
    snippet = result.get('snippet', '').lower()
    name_lower = observatory_name.lower()

    # Extract domain
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
    except Exception:
        domain = ''

    # Domain type scoring
    if '.edu' in domain:
        score += 3.0  # University observatories
    elif '.gov' in domain:
        score += 3.0  # Government observatories
    elif '.org' in domain:
        score += 2.0  # Research institutions
    elif '.ac.' in domain:  # Academic domains (UK, Japan, etc.)
        score += 2.5

    # Penalize Wikipedia/reference sites (we want primary sources)
    if 'wikipedia' in domain:
        score -= 2.0
    if 'wikidata' in domain:
        score -= 2.0

    # Observatory name in domain
    name_words = name_lower.split()
    for word in name_words:
        if len(word) > 3 and word in domain:
            score += 1.5
            break

    # Observatory name in title
    if name_lower in title:
        score += 1.0
    else:
        # Partial match
        for word in name_words:
            if len(word) > 3 and word in title:
                score += 0.5
                break

    # Keywords indicating official site
    official_keywords = ['official', 'home', 'welcome', 'about us', 'visitor']
    for keyword in official_keywords:
        if keyword in title or keyword in snippet:
            score += 0.5
            break

    # Keywords indicating observatory content
    observatory_keywords = ['telescope', 'astronomy', 'observation', 'research']
    for keyword in observatory_keywords:
        if keyword in title or keyword in snippet:
            score += 0.3

    return score


def find_best_website_url(
    name: str,
    wikidata_url: str | None,
    country: str | None = None,
    search_func=None,
    prefer_https: bool = True
) -> dict:
    """
    Find the best valid website URL for an observatory.

    Process:
    1. If wikidata_url exists, validate it (Tier 1)
    2. If valid but HTTP, attempt HTTPS upgrade
    3. If invalid/missing, search for alternatives (Tier 2)
    4. Validate each search result until valid URL found

    Args:
        name: Observatory name
        wikidata_url: URL from Wikidata (may be None or invalid)
        country: Optional country for search context
        search_func: Callable for web search (see search_observatory_website)
        prefer_https: Attempt to upgrade HTTP URLs to HTTPS (default True)

    Returns:
        {
            'url': str | None,
            'source': 'wikidata' | 'search' | None,
            'validation': {...},  # Full validation details
        }
    """
    result = {
        'url': None,
        'source': None,
        'validation': None,
    }

    # Tier 1: Validate Wikidata URL if provided
    if wikidata_url:
        validation = validate_website_url(wikidata_url)
        if validation['valid']:
            url = validation['final_url'] or wikidata_url

            # Attempt HTTPS upgrade if URL is HTTP
            if prefer_https:
                url = _ensure_https(url)

            result['url'] = url
            result['source'] = 'wikidata'
            result['validation'] = validation
            return result

        # Wikidata URL failed - store validation for reference
        result['validation'] = validation

    # Tier 2: Search for alternatives
    if search_func:
        candidates = search_observatory_website(name, country, search_func)

        for candidate in candidates:
            validation = validate_website_url(candidate['url'])
            if validation['valid']:
                url = validation['final_url'] or candidate['url']

                # Attempt HTTPS upgrade if URL is HTTP
                if prefer_https:
                    url = _ensure_https(url)

                result['url'] = url
                result['source'] = 'search'
                result['validation'] = validation
                return result

    # No valid URL found
    return result


def _ensure_https(url: str, timeout: int = 5) -> str:
    """
    Ensure URL uses HTTPS if possible.

    If URL is already HTTPS or redirected to HTTPS, returns as-is.
    If HTTP, attempts HTTPS upgrade with HEAD request verification.
    Falls back to original URL if HTTPS fails.
    """
    if not url:
        return url

    parsed = urlparse(url)

    # Already HTTPS
    if parsed.scheme == 'https':
        return url

    # HTTP - try HTTPS version
    https_url = url.replace('http://', 'https://', 1)

    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.head(
            https_url,
            timeout=timeout,
            headers=headers,
            allow_redirects=True
        )
        if response.status_code < 400:
            return https_url
    except requests.RequestException:
        pass

    # HTTPS failed, keep HTTP
    return url


