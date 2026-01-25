# SEO & AI Discoverability Rules

These rules apply when working on features that affect SEO or AI discoverability.

## Files to Update

When adding new **public pages or features**, update these files:

| File | Purpose | When to Update |
|------|---------|----------------|
| `starview_frontend/public/llms.txt` | AI assistant context | New features, pages, or content types |
| `starview_app/sitemaps.py` | Search engine indexing | New indexable pages |
| `django_project/views.py` (robots_txt) | Crawler access control | New auth/utility pages to block |
| `django_project/views.py` (SEO_META_TAGS) | Social sharing previews | New pages needing custom meta |
| `django_project/views.py` (VALID_REACT_ROUTES) | 404 vs 200 status | New React routes |

## llms.txt Specification

The `llms.txt` file helps AI language models (ChatGPT, Claude, etc.) understand the site at inference time without parsing HTML. It follows the [llmstxt.org](https://llmstxt.org/) specification.

**Location:** `starview_frontend/public/llms.txt`

**Format:**
```markdown
# Project Name

> Short summary of the project

## Section
Detailed information...

## Links
- Page Name: https://www.starview.app/page
```

**Update when:**
- Adding new major features (e.g., new data types, user features)
- Adding new public pages
- Changing core functionality
- Adding new educational content

## Sitemap Configuration

**Location:** `starview_app/sitemaps.py`

**Current sitemaps:**
- `StaticViewSitemap` - Content pages (/, /explore, /sky, /tonight, /bortle, /moon, /weather)
- `UserProfileSitemap` - Public user profiles with activity

**Excluded (intentionally):**
- Legal pages (/terms, /privacy, /accessibility, /ccpa) - utility pages
- Auth pages (/login, /register, etc.) - blocked in robots.txt

**Update when:**
- Adding new indexable content pages
- Adding new content types (e.g., location detail pages)

## robots.txt Configuration

**Location:** `django_project/views.py` (robots_txt function)

**Currently blocked:**
- `/admin/`, `/api/`, `/accounts/` - Internal
- Auth pages: `/login`, `/register`, `/signup`, `/password-reset`, etc.
- Utility pages: `/profile`, `/verify-email`, `/email-verified`, etc.

**Update when:**
- Adding new auth or utility pages that shouldn't be indexed
- Adding new internal endpoints

## SEO Meta Tags

**Location:** `django_project/views.py` (SEO_META_TAGS dict)

Server-side meta tag injection for social media crawlers (they don't execute JS).

**Update when:**
- Adding new pages that need custom titles/descriptions
- Pages that will be shared on social media

## Checklist for New Pages

When adding a new public page:

1. [ ] Add route to `VALID_REACT_ROUTES` in `django_project/views.py`
2. [ ] Add meta tags to `SEO_META_TAGS` if page needs custom title/description
3. [ ] Add to sitemap if page should be indexed (content pages only)
4. [ ] Add to robots.txt `Disallow` if page should NOT be indexed
5. [ ] Update `llms.txt` if page represents new functionality
6. [ ] Add `useSEO()` hook call in the React page component
