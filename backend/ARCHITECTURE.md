# Backend Architecture Guide

**Last Updated:** 2026-01-25 | **Status:** 98% Complete | **Production:** https://starview.app

---

## Quick Reference

### Tech Stack
- Django 5.1.13 + DRF 3.15.2 + PostgreSQL 17.6 + Redis 7.0
- Cloudflare R2 (media.starview.app) + AWS SES (email)
- Celery 5.4.0 (optional async) + django-allauth (auth/OAuth)
- Security: django-axes, django-csp, bleach

### Production Infrastructure (Render.com ~$24/month)
- **Web:** `starview` - Django/Gunicorn
- **DB:** `starview-db` - PostgreSQL with daily backups
- **Cache:** `starview-cache` - Redis (caching, sessions, rate limiting)
- **Cronjobs:** 3 automated tasks (audit logs, email cleanup, user cleanup)
- **Media:** Cloudflare R2 (media.starview.app)

### Key Patterns
- **Service Layer:** Business logic in `starview_app/services/`
- **ContentTypes:** Generic voting/reporting on any model
- **Signals:** Auto file cleanup + badge awarding
- **Nested API:** `/api/locations/{id}/reviews/{id}/comments/`
- **Caching:** Redis with version-based map GeoJSON invalidation (O(1) for any user count)

---

## Database Models (17 total)

### Core Models (`starview_app/models/`)
| Model | File | Purpose |
|-------|------|---------|
| Location | `model_location.py` | Stargazing sites with auto-enrichment from Mapbox |
| LocationPhoto | `model_location_photo.py` | Creator-uploaded photos (max 5/location, auto-resized 1920x1920 + 300x300 thumbnails) |
| Review | `model_review.py` | User ratings (1-5 stars), unique per user/location |
| ReviewComment | `model_review_comment.py` | Threaded comments on reviews |
| ReviewPhoto | `model_review_photo.py` | Max 5/review, auto-resized to 1920x1920 |
| UserProfile | `model_user_profile.py` | OneToOne User extension, pinned badges |
| FavoriteLocation | `model_location_favorite.py` | M2M with optional nicknames |
| Vote | `model_vote.py` | Generic upvote/downvote (ContentTypes) |
| Report | `model_report.py` | Generic content reporting (ContentTypes) |
| Badge | `model_badge.py` | 27 achievements across 7 categories |
| UserBadge | `model_user_badge.py` | User awards with timestamps |
| LocationVisit | `model_location_visit.py` | Check-ins for badge progress |
| Follow | `model_follow.py` | User following relationships (social network) |
| AuditLog | `model_audit_log.py` | Security audit trail |

### Email Models (`models/email_events/`)
| Model | Purpose |
|-------|---------|
| EmailBounce | AWS SES bounce tracking (hard/soft/transient) |
| EmailComplaint | Spam complaint tracking |
| EmailSuppressionList | Master suppression list |

---

## API Endpoints

> **Adding new endpoints?** The `starview-api-endpoint` skill guides through the full backend-to-frontend workflow, including serializers, views, rate limiting, frontend services, and React Query hooks.

### Authentication (`views/views_auth.py`)
```
POST /api/auth/register/           - Register (sends verification email)
POST /api/auth/login/              - Login (email must be verified)
POST /api/auth/logout/             - Logout
GET  /api/auth/status/             - Check auth status
POST /api/auth/resend-verification/- Resend verification email
POST /api/auth/password-reset/     - Request password reset
POST /api/auth/password-reset-confirm/{uidb64}/{token}/
GET  /accounts/google/login/       - Google OAuth
```

### Locations (`views/views_location.py`)
```
GET    /api/locations/                      - List (paginated 20/page)
       ?search=<text>                       - Text search (name, address, region, country)
       ?type=<types>                        - Filter by type (comma-separated: dark_sky_site,observatory,etc)
       ?minRating=<1-5>                     - Minimum rating filter
       ?verified=true                       - Only verified locations
       ?near=<lat,lng>                      - Distance filter center (PostGIS ST_DWithin)
       ?radius=<miles>                      - Distance filter radius (default: 50)
       ?maxBortle=<1-9>                     - Maximum Bortle class filter
       ?sort=<field>                        - Sort order: -created_at, average_rating, distance, etc.
POST   /api/locations/                      - Create (auth required)
GET    /api/locations/{id}/                 - Detail
PUT    /api/locations/{id}/                 - Update (auth required)
DELETE /api/locations/{id}/                 - Delete (auth required)
GET    /api/locations/map_geojson/          - GeoJSON FeatureCollection for Mapbox (version-cached)
       (Supports same filter params as list endpoint)
GET    /api/locations/{id}/info_panel/      - Map popup data
POST   /api/locations/{id}/mark-visited/    - Check-in to location (creates LocationVisit)
DELETE /api/locations/{id}/unmark-visited/  - Remove check-in
POST   /api/locations/{id}/toggle_favorite/ - Toggle favorite status (add/remove)
POST   /api/locations/{id}/report/          - Report location
GET    /api/locations/hero_carousel/        - Random high-quality images for homepage (daily rotation)
GET    /api/locations/popular_nearby/       - Top-rated locations near coordinates
       ?lat=<lat>&lng=<lng>                 - User coordinates (required)
       ?limit=<n>                           - Max results (default: 8)
       ?radius=<miles>                      - Search radius (default: 500)
```

### Reviews (`views/views_review.py`)
```
GET    /api/locations/{id}/reviews/                       - List reviews
POST   /api/locations/{id}/reviews/                       - Create review
GET    /api/locations/{id}/reviews/{id}/                  - Review detail
PUT    /api/locations/{id}/reviews/{id}/                  - Update review
DELETE /api/locations/{id}/reviews/{id}/                  - Delete review
POST   /api/locations/{id}/reviews/{id}/add_photos/       - Upload photos (max 5)
DELETE /api/locations/{id}/reviews/{id}/photos/{photo_id}/ - Delete photo
POST   /api/locations/{id}/reviews/{id}/vote/             - Upvote/downvote review
POST   /api/locations/{id}/reviews/{id}/report/           - Report review
```

### Comments (`views/views_review.py` - nested under reviews)
```
GET    /api/locations/{id}/reviews/{id}/comments/           - List comments
POST   /api/locations/{id}/reviews/{id}/comments/           - Create comment
GET    /api/locations/{id}/reviews/{id}/comments/{id}/      - Comment detail
PUT    /api/locations/{id}/reviews/{id}/comments/{id}/      - Update comment
DELETE /api/locations/{id}/reviews/{id}/comments/{id}/      - Delete comment
POST   /api/locations/{id}/reviews/{id}/comments/{id}/vote/ - Upvote/downvote comment
POST   /api/locations/{id}/reviews/{id}/comments/{id}/report/ - Report comment
```

### User & Profile (`views/views_user.py`)
```
GET   /api/users/{username}/                    - Public profile
GET   /api/users/{username}/reviews/            - User's reviews
GET   /api/users/me/                            - Current user (private profile)
POST  /api/users/me/upload-picture/             - Upload profile picture
DELETE /api/users/me/remove-picture/            - Remove profile picture
PATCH /api/users/me/update-name/                - Update display name
PATCH /api/users/me/update-username/            - Update username
PATCH /api/users/me/update-email/               - Update email (requires verification)
PATCH /api/users/me/update-password/            - Change password
PATCH /api/users/me/update-bio/                 - Update bio
PATCH /api/users/me/update-location/            - Update location (with Mapbox autocomplete)
GET   /api/users/me/social-accounts/            - List connected OAuth accounts
DELETE /api/users/me/disconnect-social/{id}/    - Disconnect OAuth account
```

### Badges (`views/views_badge.py`)
```
GET   /api/users/{username}/badges/       - User badge progress (earned, in-progress, locked)
GET   /api/users/me/badges/collection/    - Current user's badge collection
PATCH /api/users/me/badges/pin/           - Pin/unpin badges (max 3 displayed on profile)
```

### Favorites (`views/views_favorite.py`)
```
GET    /api/favorite-locations/      - User's favorites
POST   /api/favorite-locations/      - Add favorite (with optional nickname)
GET    /api/favorite-locations/{id}/ - Favorite detail
PUT    /api/favorite-locations/{id}/ - Update nickname
DELETE /api/favorite-locations/{id}/ - Remove favorite
```

### Follow System (`views/views_follow.py`)
```
POST   /api/users/{username}/follow/       - Follow user
DELETE /api/users/{username}/follow/       - Unfollow user
GET    /api/users/{username}/is-following/ - Check if following
GET    /api/users/{username}/followers/    - List user's followers
GET    /api/users/{username}/following/    - List users being followed
```

### Platform Stats (`views/views_stats.py`)
```
GET /api/stats/                    - Platform-wide stats (locations, reviews, users)
```

### Webhooks (`views/views_webhooks.py`)
```
POST /api/webhooks/ses-bounce/     - AWS SNS bounce notifications
POST /api/webhooks/ses-complaint/  - AWS SNS spam complaints
```

### Moon, Weather & Light Pollution (`views/views_moon.py`, `views/views_weather.py`, `views/views_bortle.py`)
```
GET  /api/moon-phases/            - Moon phases (today or date range)
     ?start_date=YYYY-MM-DD       - Optional start date
     ?end_date=YYYY-MM-DD         - Optional end date
     ?lat=<lat>&lng=<lng>         - Optional location for moonrise/moonset + rotation angle
     ?key_dates_only=true         - Return only key phase dates
GET  /api/weather/                - Weather data with automatic source selection
     ?lat=<lat>&lng=<lng>         - Location coordinates (required)
     ?start_date=YYYY-MM-DD       - Optional start date (default: today)
     ?end_date=YYYY-MM-DD         - Optional end date (default: start_date)
     Sources: forecast (0-16 days), historical (past), historical_average (>16 days)
     Response: { current, daily[], sources, warnings }
GET  /api/bortle/                 - Light pollution / Bortle scale rating (1-9)
     ?lat=<lat>&lng=<lng>         - Location coordinates (required)
     Response: { bortle, sqm, description, quality, location }
     Corrections: Temporal (2.5%/year since 2015), Zenith-to-Bortle (+1 for SQM < 21)
```

### IP Geolocation (`views/views_geoip.py`)
```
GET  /api/geolocate/              - Get approximate location from IP address
     Response: { latitude, longitude, city, region, country, source: "ip" }
     Uses Cloudflare geolocation headers (Managed Transform)
     Returns null coordinates if headers unavailable
     Development: Returns San Francisco as fallback
```

### Directions Proxy (`views/views_routing.py`)
```
GET  /api/directions/             - Proxy to OpenRouteService directions API
     ?origin=<lat,lng>            - Starting coordinates (required)
     ?destination=<lat,lng>       - Ending coordinates (required)
     Response: GeoJSON with route geometry and summary
     Security: API key kept server-side, rate-limited via AnonRateThrottle
```

### Health (`views/views_health.py`)
```
GET /health/                       - DB, cache, Celery status
```

### Sitemaps (`sitemaps.py`)
```
GET /sitemap.xml                   - XML sitemap index for search engines
GET /llms.txt                      - AI language model context (llmstxt.org spec)
```
- **StaticViewSitemap:** Homepage and content pages (/, /explore, /sky, /tonight, /bortle, /moon, /weather)
- **UserProfileSitemap:** Public user profiles (priority 0.6, limit 1000)
- **Excluded:** Legal/utility pages (/terms, /privacy, /login, etc.) - not indexed
- Improves SEO and Google AI Overviews visibility
- Only exposes public URLs - no sensitive data
- **llms.txt:** Markdown file helping AI assistants understand the site (see `.claude/rules/seo.md`)

---

## Service Layer (`starview_app/services/`)

| Service | Purpose |
|---------|---------|
| `badge_service.py` | Badge checking/awarding, Redis-cached progress, profile completion config |
| `location_service.py` | Mapbox enrichment (address, elevation) |
| `moon_service.py` | Moon phase calculations using ephem library, moonrise/moonset times, rotation angles for accurate display |
| `weather_service.py` | Open-Meteo API integration with automatic source selection (forecast, historical, historical average) |
| `bortle_service.py` | Bortle scale from World Atlas 2015 GeoTIFF (views/views_bortle.py contains inline logic) |
| `vote_service.py` | Generic voting logic with toggle |
| `report_service.py` | Content reporting validation |
| `password_service.py` | Custom password validators |

### Profile Completion Configuration

The **Mission Ready** badge uses `PROFILE_COMPLETION_REQUIREMENTS` in `badge_service.py` as the single source of truth for what profile fields are required:

```python
PROFILE_COMPLETION_REQUIREMENTS = [
    ('location', lambda p: bool(p.location)),
    ('bio', lambda p: bool(p.bio)),
    ('profile_picture', lambda p: bool(p.profile_picture) and hasattr(p.profile_picture, 'url')),
    # Add new requirements here - badge logic automatically adapts
]
```

**To add a new profile requirement:**
1. Add tuple to `PROFILE_COMPLETION_REQUIREMENTS` with `(field_name, check_function)`
2. Add `BadgeService.check_profile_complete_badge(user)` to the new field's update endpoint

The badge award/revoke logic and progress display automatically adapt to new requirements.

---

## Signal Handlers (`starview_app/utils/signals.py`)

**File Cleanup (pre_delete):**
- `delete_user_profile_picture` - Cleanup profile pics
- `delete_review_photo_files` - Cleanup review images + thumbnails
- `delete_location_photo_files` - Cleanup location photos + thumbnails
- `cleanup_location_directory_structure` - Cleanup on Location CASCADE
- `cleanup_review_directory_structure` - Cleanup on Review CASCADE

**Badge Awarding (post_save):**
- `check_badges_on_visit` - LocationVisit created
- `check_badges_on_location_add` - Location created
- `check_badges_on_review` - Review created
- `check_badges_on_vote` - Vote received
- `check_badges_on_follow` - Follow created
- `check_badges_on_comment` - Comment created
- `check_badges_on_photo_upload` - Photo added

**Auto-creation:**
- `create_or_update_user_profile` - Create UserProfile for new Users
- `delete_email_confirmation_on_confirm` - Cleanup verification tokens

---

## Security Features

### Rate Limiting (`utils/throttles.py`)
| Endpoint | Limit |
|----------|-------|
| Login | 5/minute |
| Password Reset | 3/hour |
| Content Creation | 20/hour |
| Voting | 60/hour |
| Reporting | 10/hour |
| Anonymous API | 100/hour |
| Authenticated API | 1000/hour |

### Authentication
- **Email verification required** (django-allauth, 3-day token expiry)
- **Account lockout:** 5 failed attempts = 1 hour (django-axes)
- **Password reset:** Secure tokens, 1-hour expiry
- **Google OAuth:** Social login support
- **React SPA integration:** Custom adapters redirect allauth HTML pages to React frontend
- **Session idle timeout:** 30-minute inactivity timeout (configurable via `SESSION_IDLE_TIMEOUT`)

### Input Validation (`utils/validators.py`)
- File upload: 5MB max, extension whitelist, MIME check, Pillow verification
- XSS prevention: bleach HTML sanitization
- Geographic: lat (-90,90), lon (-180,180), elevation (-500m,9000m)

### Headers (A+ securityheaders.com)
- HSTS (1 year, preload)
- CSP with Mapbox/R2 allowlist
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff

---

## Allauth React Integration (`utils/adapters.py`)

Custom adapters and views that redirect django-allauth HTML pages to React frontend routes.

### Redirect Views (in `django_project/urls.py`)
| Allauth URL | Redirect To | Purpose |
|-------------|-------------|---------|
| `/accounts/login/` | `/login` | Login page |
| `/accounts/signup/` | `/register` | Registration page |
| `/accounts/logout/` | `/` | Logout (with session clear) |
| `/accounts/email/` | `/profile` | Email management |
| `/accounts/password/change/` | `/profile` | Password change |
| `/accounts/password/reset/` | `/password-reset` | Password reset request |
| `/accounts/confirm-email/<key>/` | `/email-verified` | Email confirmation |
| `/accounts/3rdparty/` | `/profile` | Social account connections |

### Custom Adapters
| Adapter | Purpose |
|---------|---------|
| `CustomAccountAdapter` | Email verification, login/logout/signup redirects to React |
| `CustomSocialAccountAdapter` | OAuth username generation (user######), email conflict prevention |
| `CustomConfirmEmailView` | Handles email verification + change, sends welcome emails |
| `CustomConnectionsView` | Social account connect/disconnect from profile |

### Key Features
- **Welcome emails:** Sent on first verification (email signup) or OAuth signup
- **Email change:** New email replaces old, old addresses cleaned up
- **OAuth conflicts:** Prevents duplicate email registration, shows helpful errors
- **Dev/prod aware:** Uses `localhost:5173` in DEBUG, relative URLs in production

---

## Email System

### Verification Flow
1. User registers → verification email sent
2. User clicks link → EmailAddress.verified = True
3. Login now allowed

### AWS SES Integration
- **Bounce tracking:** Hard bounces = immediate suppression, soft bounces = 3 strikes
- **Complaint tracking:** Immediate suppression
- **SNS webhooks:** Real-time notifications at `/api/webhooks/ses-*`
- **Suppression list:** Marketing blocked, transactional allowed

### Management Commands
```bash
# User & Content Maintenance
cleanup_unverified_users --days 30    # Delete old unverified accounts
cleanup_email_suppressions            # Weekly bounce/complaint cleanup
  --soft-bounce-days 30               #   Days before recovering soft bounces
  --stale-days 90                     #   Days before deleting stale records
  --dry-run                           #   Preview without making changes
  --report                            #   Generate health report to stdout
  --email-report user@example.com     #   Email weekly report
archive_audit_logs --days 30          # Archive old audit logs to R2
  --archive-dir PATH                  #   Local directory (development)
  --format json|txt|both              #   Output format (default: both)
cleanup_audit_archives --days 90      # Delete old R2 archives (privacy compliance)

# Badge System
audit_badges                          # Audit badge system integrity
award_pioneer_badges                  # Award early adopter badges

# Location Enrichment
enrich_locations                      # Re-enrich locations with Mapbox data
  --dry-run                           #   Preview without making changes
  --id 123                            #   Enrich specific location
  --type observatory                  #   Filter by location type
  --delay 0.5                         #   Delay between API calls (default: 0.5s)
  --elevation-only                    #   Only update elevation, skip geocoding
seed_locations                        # Seed locations from JSON files

# Cache & Deployment
warm_cache                            # Pre-warm Redis caches after deployment
  --dry-run                           #   Preview what would be cached
  --pages 5                           #   Number of list pages to warm (default: 5)

# Setup & Diagnostics
setup_google_oauth                    # Setup Google OAuth credentials
diagnose_db                           # Diagnose database issues
```

---

## Badge System (24 badges, 7 categories)

**Categories:** Exploration, Contribution, Quality, Review, Community, Tenure, Special

**Key Files:**
- `services/badge_service.py` - Checking/awarding logic
- `models/model_badge.py` - Badge definitions
- `models/model_user_badge.py` - User awards

**Performance:**
- Redis-cached progress (5-min TTL)
- 96% query reduction (17 → 0.7 queries)
- Signal-triggered awarding (no manual checks needed)

**Detailed docs:** `.claude/backend/docs/badge_system/`

---

## Performance Optimizations

### Query Optimization
- `select_related()` for ForeignKey (UserBadge → Badge)
- `prefetch_related()` for reverse relations
- `annotate()` for aggregations in single query
- Result: 99.3% query reduction on list endpoints

### Caching (Redis)
| Data | TTL | Precision | Impact |
|------|-----|-----------|--------|
| Location list | 15 min | -- | 10x faster |
| Location detail | 15 min | -- | 4x faster |
| Map GeoJSON | 30 min | -- | 60x faster (version-based O(1) invalidation) |
| Badge progress | 5 min | -- | 25x faster (cache hit) |
| Weather forecast | 30 min | ~11km (1 decimal) | External API rate limit protection |
| Weather historical | 7 days | ~11km (1 decimal) | Immutable past data |
| Weather hist avg | 30 days | ~11km (1 decimal) | Statistical averages stable |
| Moon phases | 24 hours | ~1km (2 decimal) | Location-specific; 7 days without location |
| Bortle scale | 30 days | ~1km (2 decimal) | Light pollution changes slowly |

**Cache Warming:** Use `python manage.py warm_cache` after deployments to pre-warm anonymous caches (map GeoJSON, location list pages, platform stats).

### Async Tasks (Celery, optional)
- Location enrichment runs in background
- FREE tier: sync fallback (2-5s delay)
- PAID tier: instant response ($7/month worker)

---

## File Structure

```
starview_app/
├── models/
│   ├── model_location.py           # 157 lines
│   ├── model_location_photo.py     # 169 lines - Creator-uploaded location photos
│   ├── model_review.py             # 162 lines
│   ├── model_review_comment.py     # 102 lines
│   ├── model_review_photo.py       # 210 lines
│   ├── model_user_profile.py       # 87 lines
│   ├── model_follow.py             # 58 lines
│   ├── model_badge.py              # 87 lines
│   ├── model_user_badge.py         # 52 lines
│   ├── model_location_favorite.py  # 49 lines
│   ├── model_location_visit.py     # 56 lines
│   ├── model_vote.py               # 66 lines
│   ├── model_report.py             # 100 lines
│   ├── model_audit_log.py          # 132 lines
│   └── email_events/
│       ├── model_email_bounce.py           # 6K lines
│       ├── model_email_complaint.py        # 5K lines
│       └── model_email_suppressionlist.py  # 7K lines
├── views/
│   ├── views_auth.py          # 827 lines - auth endpoints
│   ├── views_badge.py         # 225 lines - badge endpoints
│   ├── views_bortle.py        # 235 lines - Bortle scale / light pollution API
│   ├── views_comment.py       # Comment CRUD endpoints
│   ├── views_favorite.py      # 71 lines - favorite locations
│   ├── views_follow.py        # 176 lines - follow/unfollow system
│   ├── views_health.py        # 129 lines - health check endpoint
│   ├── views_location.py      # 987 lines - location CRUD + check-ins + hero_carousel + popular_nearby
│   ├── views_moon.py          # Moon phase API endpoint
│   ├── views_review.py        # 400 lines - review CRUD
│   ├── views_stats.py         # 85 lines - platform statistics
│   ├── views_user.py          # 647 lines - profile management
│   ├── views_vote.py          # Generic voting endpoints
│   └── views_weather.py       # Weather forecast API endpoint
├── services/
│   ├── badge_service.py       # Badge checking/awarding logic
│   ├── location_service.py    # Mapbox enrichment
│   ├── moon_service.py        # Moon phase calculations (ephem library)
│   ├── weather_service.py     # Weather data fetching
│   ├── vote_service.py        # Generic voting logic
│   ├── report_service.py      # Content reporting
│   └── password_service.py    # Password validation
├── serializers/
│   ├── serializer_location.py # 287 lines
│   ├── serializer_review.py   # 135 lines
│   ├── serializer_user.py     # 148 lines
│   ├── serializer_favorite.py
│   ├── serializer_vote.py
│   └── serializer_report.py
├── utils/
│   ├── signals.py             # 650+ lines - file cleanup, badges
│   ├── tasks.py               # Celery tasks
│   ├── validators.py          # Input validation
│   ├── throttles.py           # Rate limiting
│   ├── exception_handler.py   # DRF error handling
│   ├── adapters.py            # django-allauth customization (React redirects, OAuth adapters)
│   └── cache.py               # Redis cache keys, version-based invalidation
├── middleware/
│   └── session_timeout.py     # Session idle timeout (30-min default)
├── sitemaps.py                    # XML sitemaps for SEO
└── management/commands/
    ├── archive_audit_logs.py          # Archive old audit logs (R2 in prod, local in dev)
    ├── audit_badges.py
    ├── award_pioneer_badges.py
    ├── backfill_bortle.py             # Backfill Bortle values for existing locations
    ├── backfill_descriptions.py       # Backfill descriptions via AI
    ├── backfill_photo_dimensions.py   # Backfill photo width/height metadata
    ├── cleanup_audit_archives.py      # Delete old R2 archives (privacy compliance)
    ├── cleanup_email_suppressions.py
    ├── cleanup_unverified_users.py
    ├── diagnose_db.py
    ├── enrich_locations.py            # Re-enrich with Mapbox geocoding/elevation
    ├── seed_locations.py
    ├── setup_google_oauth.py
    └── warm_cache.py                  # Pre-warm Redis caches after deployment
```

---

## Configuration

### Environment Variables
```bash
# Core
DJANGO_SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=starview.app,www.starview.app

# Database (Render auto-provides DATABASE_URL)
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://...

# Cloudflare R2
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=starview-media
R2_PUBLIC_URL=https://media.starview.app

# AWS SES
AWS_SES_ACCESS_KEY_ID=...
AWS_SES_SECRET_ACCESS_KEY=...
DEFAULT_FROM_EMAIL=noreply@starview.app

# External APIs
MAPBOX_TOKEN=...
OPENROUTE_SERVICE_API_KEY=...         # Directions API (fallback for navigation)
DISABLE_EXTERNAL_APIS=False

# Security
SESSION_IDLE_TIMEOUT=1800             # Session idle timeout in seconds (default: 30 min)

# Optional
CELERY_ENABLED=False  # True for async tasks
GOOGLE_OAUTH_CLIENT_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=...
```

---

## Test Suites

**Location:** `.claude/backend/tests/`

```bash
# Run with Django venv
djvenv/bin/python .claude/backend/tests/phase1/test_rate_limiting.py
djvenv/bin/python .claude/backend/tests/phase4/test_celery_tasks.py
djvenv/bin/python .claude/backend/tests/phase5/test_health_check.py
```

| Phase | Focus | Tests |
|-------|-------|-------|
| phase1 | Security (rate limiting, XSS, file upload) | 44+ |
| phase2 | Performance (N+1, caching) | 10+ |
| phase4 | Infrastructure (lockout, audit, Celery) | 31+ |
| phase5 | Monitoring (health check) | 5+ |
| phase6 | Authentication (password reset) | 5+ |
| phase7 | Badge fixes | 10+ |

---

## Remaining Work

1. **Database indexes** (~2-3 hours)
   - Compound indexes on Review(location, created_at), Vote(content_type, object_id)

2. **Sentry** (optional, ~1 hour)
   - Error tracking for production

---

## Documentation Index

| Document | Purpose |
|----------|---------|
| `docs/CELERY_GUIDE.md` | Async tasks setup (FREE vs PAID) |
| `docs/STORAGE_CONFIGURATION.md` | R2/Cloudflare media storage |
| `docs/RENDER_CRON_SETUP.md` | Production cronjob setup |
| `docs/LOGGING_GUIDE.md` | Python logging best practices |
| `docs/EMAIL_SECURITY_SUMMARY.md` | OAuth/registration edge cases |
| `docs/badge_system/` | Badge system deep dive |
| `docs/email_monitoring/` | AWS SES bounce/complaint tracking |
