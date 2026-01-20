# Starview API Integration Guide

**Last Updated:** 2026-01-19
**API Version:** 1.0
**Base URL:** `/api` (uses relative URLs via Axios configuration)
**Production:** `https://starview.app` | **Development:** `http://127.0.0.1:8000`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
   - [Health Check](#health-check)
   - [Platform Stats](#platform-stats)
   - [Stargazing Data Endpoints](#stargazing-data-endpoints)
   - [Authentication Endpoints](#authentication-endpoints)
   - [Location Endpoints](#location-endpoints)
   - [Review Endpoints](#review-endpoints)
   - [Comment Endpoints](#comment-endpoints)
   - [Favorite Location Endpoints](#favorite-location-endpoints)
   - [User Profile Endpoints](#user-profile-endpoints)
   - [Public User Endpoints](#public-user-endpoints)
   - [Badge Endpoints](#badge-endpoints)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Performance Characteristics](#performance-characteristics)
7. [Frontend Integration Patterns](#frontend-integration-patterns)

---

## Overview

The Starview API is a Django REST Framework-based API optimized for performance with **99.3% query reduction** through database annotations, prefetching, and caching strategies. The API supports session-based authentication and includes comprehensive security features like rate limiting, account lockout protection, and content validation.

### Key Features
- ✅ RESTful design with nested resources
- ✅ Session-based authentication with CSRF protection
- ✅ **Mandatory email verification** for all new users
- ✅ Multi-language support (English + Spanish emails)
- ✅ Google OAuth integration for social login
- ✅ Pagination (20 items per page)
- ✅ Rate limiting and throttling
- ✅ Redis caching for high-traffic endpoints
- ✅ Optimized for minimal database queries
- ✅ Generic voting and reporting system

---

## Authentication

All write operations require authentication. The API uses **session-based authentication** with CSRF protection.

### Frontend Implementation

The frontend uses **Axios** for all API requests with automatic CSRF token handling:

**Configuration** (`services/api.js`):
```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,  // Sends session cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor adds CSRF token
api.interceptors.request.use((config) => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method.toLowerCase())) {
    const csrfToken = getCookie('csrftoken');
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken;
    }
  }
  return config;
});

function getCookie(name) {
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [key, value] = cookie.trim().split('=');
    if (key === name) return decodeURIComponent(value);
  }
  return null;
}

export default api;
```

**Usage Example**:
```javascript
import api from './services/api';

// GET request
const response = await api.get('/locations/');

// POST request (CSRF token added automatically)
const response = await api.post('/locations/', {
  name: 'Dark Sky Park',
  latitude: 37.7749,
  longitude: -122.4194
});
```

---

## API Endpoints

### Health Check

#### `GET /health/`
System health check endpoint for monitoring and load balancer health checks.

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-30T12:34:56.789Z",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "celery": "ok"
  }
}
```

---

### Platform Stats

#### `GET /api/stats/`
Get platform-wide statistics (total locations, reviews, and users).

**Authentication:** Not required
**Cache:** 5 minutes

**Response:**
```json
{
  "locations": {
    "count": 1234,
    "formatted": "1.2K"
  },
  "reviews": {
    "count": 5678,
    "formatted": "5.7K"
  },
  "stargazers": {
    "count": 890,
    "formatted": "890"
  }
}
```

**Use Case:** Homepage hero stats display

**Frontend Service:** `statsApi.getPlatformStats()`

---

### Stargazing Data Endpoints

#### `GET /api/bortle/`
Get Bortle scale rating (light pollution index) for a location.

**Authentication:** Not required
**Cache:** 30 days (light pollution changes slowly)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | number | Yes | Latitude (-90 to 90) |
| `lng` | number | Yes | Longitude (-180 to 180) |

**Success Response (200):**
```json
{
  "bortle": 4,
  "sqm": 20.8,
  "description": "Rural/suburban transition",
  "quality": "good",
  "location": {
    "lat": 34.0522,
    "lng": -118.2437
  }
}
```

**Bortle Scale Values:**
| Class | SQM Range | Description | Quality |
|-------|-----------|-------------|---------|
| 1 | 21.99-25.0 | Excellent dark-sky site | excellent |
| 2 | 21.89-21.99 | Typical truly dark site | excellent |
| 3 | 21.69-21.89 | Rural sky | very_good |
| 4 | 20.49-21.69 | Rural/suburban transition | good |
| 5 | 19.50-20.49 | Suburban sky | moderate |
| 6 | 18.94-19.50 | Bright suburban sky | limited |
| 7 | 18.38-18.94 | Suburban/urban transition | poor |
| 8 | 17.80-18.38 | City sky | poor |
| 9 | <17.80 | Inner-city sky | very_poor |

**Error Responses:**
- **400:** Missing or invalid lat/lng parameters
- **404:** No data available (may be over water or outside coverage)
- **503:** GeoTIFF data unavailable

**Use Case:** ExploreMap light pollution overlay, location quality indicators

---

#### `GET /api/weather/`
Get weather data for a location with automatic source selection based on date.

**Authentication:** Not required
**Cache:** 30 min (forecast), 7 days (historical), 30 days (historical avg)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lat` | number | Yes | Latitude (-90 to 90) |
| `lng` | number | Yes | Longitude (-180 to 180) |
| `start_date` | string | No | Start date (YYYY-MM-DD, default: today) |
| `end_date` | string | No | End date (YYYY-MM-DD, default: start_date) |

**Success Response (200):**
```json
{
  "current": {
    "cloud_cover": 25,
    "humidity": 65,
    "wind_speed": 12,
    "temperature": 15,
    "precipitation_type": "none",
    "precipitation_probability": 10,
    "visibility": 10
  },
  "daily": [
    {
      "date": "2026-01-19",
      "data_type": "forecast",
      "confidence": "high",
      "summary": {
        "cloud_cover_avg": 30,
        "humidity_avg": 60
      },
      "hourly": [
        {
          "time": "2026-01-19T18:00:00",
          "cloud_cover": 25,
          "cloud_cover_low": 10,
          "cloud_cover_mid": 15,
          "cloud_cover_high": 5,
          "humidity": 65,
          "temperature": 12,
          "visibility": 10
        }
      ]
    }
  ],
  "sources": ["Open-Meteo Forecast API"],
  "location": { "lat": 34.0522, "lng": -118.2437 }
}
```

**Data Sources by Date:**
| Date Range | Source | Confidence |
|------------|--------|------------|
| Today to +16 days | Open-Meteo Forecast | high |
| Past dates | Open-Meteo Historical | high |
| +17 days and beyond | 5-year historical average | medium/low |

**Cache Precision:** ~11km (1 decimal place) - matches backend grid cells

**Frontend Service:** `weatherApi.getForecast({ lat, lng, date })`, `weatherApi.getForecastRange({ lat, lng, startDate, endDate })`

**Frontend Hook:** `useWeather({ lat, lng, date })`, `useNighttimeWeather({ lat, lng })`

---

### Authentication Endpoints

#### `POST /api/auth/register/`
Register a new user account.

**Authentication:** Not required
**Rate Limit:** 5 requests/minute

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password1": "SecurePassword123!",
  "password2": "SecurePassword123!"
}
```

**Success Response (201):**
```json
{
  "detail": "Account created successfully! Redirecting...",
  "redirect_url": "/"
}
```

**Important Notes:**
- ✉️ **Email verification required**: A verification email is automatically sent to the user's email address
- 🔒 **Cannot login until verified**: Users must click the verification link before they can login
- 🌐 **Multi-language emails**: Verification email sent in user's browser language (English or Spanish)
- ⏰ **Link expires in 3 days**: Verification links are valid for 3 days for security

**Error Response (400):**
```json
{
  "error": "validation_error",
  "message": "This username is already taken.",
  "status_code": 400
}
```

**Frontend Service:** `authApi.register(data)`

---

#### `POST /api/auth/login/`
Authenticate user with username or email.

**Authentication:** Not required
**Rate Limit:** 5 requests/minute
**Lockout:** 5 failed attempts = 1 hour lockout

**Request Body:**
```json
{
  "username": "johndoe",  // Can be username OR email
  "password": "SecurePassword123!",
  "next": "/locations/",  // Optional redirect URL
  "remember_me": true     // Optional: 30-day session vs browser-close
}
```

**Success Response (200):**
```json
{
  "detail": "Login successful! Redirecting...",
  "redirect_url": "/"
}
```

**Error Responses:**
```json
// Invalid credentials (401)
{
  "error": "authentication_failed",
  "message": "Invalid username or password.",
  "status_code": 401
}

// Email not verified (403)
{
  "error": "permission_denied",
  "message": "Please verify your email address before logging in. Check your inbox for the verification link.",
  "status_code": 403
}

// Account locked (403)
{
  "error": "permission_denied",
  "message": "Account temporarily locked due to too many failed login attempts. Please try again in 1 hour.",
  "status_code": 403
}
```

**Frontend Service:** `authApi.login(credentials)`

---

#### `POST /api/auth/logout/`
End the current user session.

**Authentication:** Required

**Success Response (200):**
```json
{
  "detail": "Logout successful.",
  "redirect_url": "/"
}
```

**Frontend Service:** `authApi.logout()`

---

#### `GET /api/auth/status/`
Check if the user is authenticated and retrieve user information.

**Authentication:** Not required (but returns different data based on auth status)
**Use Case:** Perfect for navbar/header components to conditionally render UI

**Success Response - Authenticated (200):**
```json
{
  "authenticated": true,
  "user": {
    "id": 5,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "profile_picture_url": "/media/profile_pics/user_5_abc123.jpg"
  }
}
```

**Success Response - Not Authenticated (200):**
```json
{
  "authenticated": false,
  "user": null
}
```

**Example Usage in React:**
```javascript
// Check auth status on component mount
useEffect(() => {
  async function checkAuth() {
    const response = await fetch('/api/auth/status/', {
      credentials: 'include'
    });
    const data = await response.json();

    if (data.authenticated) {
      setUser(data.user);
      setShowAuthLinks(true);
    } else {
      setShowAuthLinks(false);
    }
  }

  checkAuth();
}, []);
```

**Frontend Service:** `authApi.checkStatus()`

---

#### `POST /api/auth/resend-verification/`
Resend email verification link.

**Authentication:** Not required
**Rate Limit:** 1 request per 3 minutes (allauth rate limit)

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Success Response (200):**
```json
{
  "detail": "Verification email has been resent. Please check your inbox.",
  "status_code": 200
}
```

**Error Response (400):**
```json
{
  "error": "validation_error",
  "message": "This email address is already verified.",
  "status_code": 400
}
```

**Notes:**
- Generic success message returned even if email doesn't exist (user enumeration prevention)
- Email sent in user's browser language

**Frontend Service:** `authApi.resendVerificationEmail(data)`

---

#### `GET /accounts/confirm-email/{key}/`
Verify email address via one-click link.

**Authentication:** Not required
**Method:** GET (one-click verification)

**URL Parameters:**
- `key` - Email verification token (sent via email)

**Success Response:**
- Redirects to `/email-verified` (React frontend page)

**Error Responses:**
- Invalid/expired key → Redirects to `/verification-error`
- Already verified → Redirects to `/email-verified`

**Notes:**
- This is a django-allauth endpoint (handled by `CustomConfirmEmailView`)
- Token expires after 3 days
- Frontend should handle these redirect URLs appropriately

---

#### `GET /accounts/google/login/`
Initiate Google OAuth login flow.

**Authentication:** Not required

**Flow:**
1. User clicks "Login with Google"
2. Redirected to Google OAuth consent screen
3. User authorizes application
4. Google redirects back with authorization code
5. django-allauth exchanges code for access token
6. User profile retrieved (email, name)
7. If email matches existing user → Link accounts
8. If new email → Create new user account
9. EmailAddress created with `verified=True` (no verification needed for OAuth)
10. User logged in automatically

**Notes:**
- OAuth emails are pre-verified (no verification email sent)
- Automatic account creation if email is new
- Accounts with matching emails are automatically linked

---

#### Password Reset Flow

**Step 1: Request Reset**

`POST /api/auth/password-reset/`

Request a password reset email.

**Authentication:** Not required
**Rate Limit:** 3 requests/hour

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

**Success Response (200):**
```json
{
  "detail": "If an account with this email exists, a password reset link has been sent.",
  "status_code": 200
}
```

**Notes:**
- Generic success message (user enumeration prevention)
- Reset email sent in user's browser language (English or Spanish)
- Token expires in 1 hour
- Includes IP address and timestamp for security

**Frontend Service:** `authApi.requestPasswordReset(data)`

---

**Step 2: Confirm Reset**

`POST /api/auth/password-reset-confirm/{uidb64}/{token}/`

Reset password with token from email.

**Authentication:** Not required

**URL Parameters:**
- `uidb64` - Encoded user ID
- `token` - Password reset token

**Request Body:**
```json
{
  "password1": "NewSecurePassword456!",
  "password2": "NewSecurePassword456!"
}
```

**Success Response (200):**
```json
{
  "detail": "Password has been reset successfully. You can now log in with your new password.",
  "status_code": 200
}
```

**Error Responses:**
```json
// Invalid/expired token (400)
{
  "error": "validation_error",
  "message": "Invalid or expired password reset link.",
  "status_code": 400
}

// Weak password (400)
{
  "error": "validation_error",
  "message": "Password must contain at least 1 uppercase letter.",
  "status_code": 400
}
```

**Notes:**
- Token valid for 1 hour only
- Account lockout automatically cleared on successful reset
- Confirmation email sent after successful reset
- Password must meet strength requirements (uppercase, number, special character)

**Frontend Service:** `authApi.confirmPasswordReset(uidb64, token, data)`

---

### Location Endpoints

#### `GET /api/locations/`
List all locations with pagination.

**Authentication:** Optional (affects `is_favorited` field)
**Pagination:** 20 locations per page
**Cache:** 15 minutes (user-aware)

**Query Parameters:**
- `page` - Page number (default: 1)
- Filtering/search parameters supported by DRF

**Response:**
```json
{
  "count": 156,
  "next": "http://127.0.0.1:8000/api/locations/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Dark Sky Park",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "elevation": 1234.5,
      "formatted_address": "123 Main St, San Francisco, CA 94102",
      "description": "Amazing stargazing location with minimal light pollution.",
      "added_by": {
        "id": 5,
        "username": "johndoe",
        "first_name": "John",
        "last_name": "Doe"
      },
      "review_count": 23,
      "average_rating": 4.5,
      "is_favorited": true,
      "created_at": "2025-10-15T14:30:00Z",
      "updated_at": "2025-10-20T09:15:00Z"
    }
  ]
}
```

**Performance:** 4 database queries (optimized with annotations)

**Frontend Service:** `locationsApi.getAll(params)`

---

#### `POST /api/locations/`
Create a new location.

**Authentication:** Required
**Rate Limit:** 20 requests/hour (content creation)

**Request Body:**
```json
{
  "name": "Dark Sky Park",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "description": "Amazing stargazing location with minimal light pollution."
}
```

**Success Response (201):**
```json
{
  "id": 1,
  "name": "Dark Sky Park",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "elevation": 1234.5,  // Auto-enriched via Mapbox
  "formatted_address": "123 Main St, San Francisco, CA 94102",  // Auto-enriched
  "description": "Amazing stargazing location with minimal light pollution.",
  "added_by": {
    "id": 5,
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe"
  },
  "review_count": 0,
  "average_rating": null,
  "is_favorited": false,
  "created_at": "2025-10-30T12:00:00Z",
  "updated_at": "2025-10-30T12:00:00Z"
}
```

**Notes:**
- `elevation` and `formatted_address` are auto-enriched using Mapbox API (async if Celery enabled)
- Enrichment has 10-second timeout with graceful degradation

**Frontend Service:** `locationsApi.create(data)`

---

#### `GET /api/locations/{id}/`
Retrieve detailed location information with all reviews.

**Authentication:** Optional (affects `is_favorited` and `user_vote` fields)
**Cache:** 15 minutes (user-aware)

**Response:**
```json
{
  "id": 1,
  "name": "Dark Sky Park",
  "latitude": 37.7749,
  "longitude": -122.4194,
  "elevation": 1234.5,
  "formatted_address": "123 Main St, San Francisco, CA 94102",
  "description": "Amazing stargazing location with minimal light pollution.",
  "added_by": {
    "id": 5,
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe"
  },
  "review_count": 23,
  "average_rating": 4.5,
  "is_favorited": true,
  "reviews": [
    {
      "id": 101,
      "user": {
        "id": 8,
        "username": "janedoe",
        "profile_picture_url": "/media/profile_pics/jane.jpg"
      },
      "rating": 5,
      "comment": "Amazing spot for stargazing!",
      "photos": [
        {
          "id": 201,
          "image_url": "/media/review_photos/1/101/abc123.jpg",
          "thumbnail_url": "/media/review_photos/1/101/abc123_thumbnail.jpg",
          "order": 0
        }
      ],
      "upvote_count": 12,
      "downvote_count": 1,
      "user_vote": "up",  // "up", "down", or null
      "created_at": "2025-10-25T18:30:00Z",
      "updated_at": "2025-10-25T18:30:00Z"
    }
  ],
  "created_at": "2025-10-15T14:30:00Z",
  "updated_at": "2025-10-20T09:15:00Z"
}
```

**Performance:** 9 database queries with prefetching

**Frontend Service:** `locationsApi.getById(id)`

**⚠️ Scalability Note:** Currently returns ALL reviews nested (not paginated). For locations with 100+ reviews, consider using the separate `/api/locations/{id}/reviews/` endpoint instead.

---

#### `PATCH /api/locations/{id}/` or `PUT /api/locations/{id}/`
Update an existing location.

**Authentication:** Required (must be owner)
**Rate Limit:** 20 requests/hour (content creation)

**Request Body (partial update with PATCH):**
```json
{
  "description": "Updated description"
}
```

**Response:** Same as `GET /api/locations/{id}/`

**Frontend Service:** `locationsApi.update(id, data)`

---

#### `DELETE /api/locations/{id}/`
Delete a location.

**Authentication:** Required (must be owner)

**Success Response (204):** No content

**Frontend Service:** `locationsApi.delete(id)`

---

#### `GET /api/locations/map_geojson/`
Get GeoJSON FeatureCollection for map display, pre-generated by the backend.

**Authentication:** Optional (affects `is_favorited` field)
**Cache:** 30 minutes (version-based O(1) invalidation)
**Performance:** Single query, ready-to-use GeoJSON

**Response:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "id": 1,
        "name": "Dark Sky Park",
        "is_favorited": false,
        "location_type": "PARK",
        "location_type_display": "Park",
        "administrative_area": "California",
        "country": "United States",
        "elevation": 1234,
        "latitude": 37.7749,
        "longitude": -122.4194,
        "average_rating": 4.5,
        "review_count": 23,
        "images": [...]
      },
      "geometry": {
        "type": "Point",
        "coordinates": [-122.4194, 37.7749]
      }
    }
  ]
}
```

**Use Case:** Direct pass-through to Mapbox GL JS. No client-side transformation needed.

**Frontend Service:** `locationsApi.getMapGeoJSON()`

**Frontend Hook:** `useMapMarkers()` returns `{ geojson, markers, markerMap }` with O(1) lookup via `markerMap.get(id)`

---

#### `GET /api/locations/{id}/info_panel/`
Get optimized location data for map info panel/popup.

**Authentication:** Optional

**Response:**
```json
{
  "id": 1,
  "name": "Dark Sky Park",
  "formatted_address": "123 Main St, San Francisco, CA 94102",
  "average_rating": 4.5,
  "review_count": 23
}
```

**Use Case:** Displaying preview info when user clicks a map marker.

---

#### `POST /api/locations/{id}/mark-visited/`
Mark a location as visited (check-in). Awards badges if conditions are met.

**Authentication:** Required

**Success Response (200):**
```json
{
  "detail": "Location marked as visited!",
  "total_visits": 5,
  "newly_earned_badges": [
    {
      "id": 2,
      "name": "Globe Trotter",
      "description": "Visit 10 different locations",
      "icon": "/badges/globe-trotter.svg",
      "tier": "SILVER"
    }
  ]
}
```

**Frontend Service:** `locationsApi.markVisited(locationId)`

**Notes:**
- Each location can only be visited once per user
- Returns newly earned badges (if any)
- Total visit count reflects unique locations visited

---

#### `DELETE /api/locations/{id}/unmark-visited/`
Unmark a location as visited (remove check-in).

**Authentication:** Required

**Success Response (200):**
```json
{
  "detail": "Visit removed successfully.",
  "total_visits": 4
}
```

**Error Response (400):**
```json
{
  "error": "validation_error",
  "message": "You have not visited this location.",
  "status_code": 400
}
```

**Frontend Service:** `locationsApi.unmarkVisited(locationId)`

---

#### `POST /api/locations/{id}/toggle_favorite/`
Toggle favorite status for a location (add or remove from favorites).

**Authentication:** Required

**Success Response - Added (201):**
```json
{
  "is_favorited": true
}
```

**Success Response - Removed (200):**
```json
{
  "is_favorited": false
}
```

**Frontend Service:** `locationsApi.toggleFavorite(locationId)`

**Notes:**
- If not favorited, creates a FavoriteLocation record
- If already favorited, removes the FavoriteLocation record
- Invalidates user's location cache to update `is_favorited` field on refresh

---

#### `POST /api/locations/{id}/report/`
Report a problematic location.

**Authentication:** Required
**Rate Limit:** 10 requests/hour (report throttle)

**Request Body:**
```json
{
  "report_type": "SPAM",  // Options: SPAM, INAPPROPRIATE, MISINFORMATION, OTHER
  "description": "This location contains false information about accessibility."
}
```

**Success Response (201):**
```json
{
  "detail": "Location reported successfully"
}
```

**Error Responses:**
```json
// Self-reporting (400)
{
  "error": "validation_error",
  "message": "You cannot report your own content.",
  "status_code": 400
}

// Duplicate report (400)
{
  "error": "validation_error",
  "message": "You have already reported this content.",
  "status_code": 400
}
```

---

### Review Endpoints

#### `GET /api/locations/{location_id}/reviews/`
List reviews for a specific location.

**Authentication:** Optional (affects `user_vote` field)
**Pagination:** 20 reviews per page

**Query Parameters:**
- `page` - Page number (default: 1)

**Response:**
```json
{
  "count": 45,
  "next": "http://127.0.0.1:8000/api/locations/1/reviews/?page=2",
  "previous": null,
  "results": [
    {
      "id": 101,
      "user": {
        "id": 8,
        "username": "janedoe",
        "profile_picture_url": "/media/profile_pics/jane.jpg"
      },
      "location": 1,
      "rating": 5,
      "comment": "Amazing spot for stargazing!",
      "photos": [
        {
          "id": 201,
          "image_url": "/media/review_photos/1/101/abc123.jpg",
          "thumbnail_url": "/media/review_photos/1/101/abc123_thumbnail.jpg",
          "order": 0
        }
      ],
      "upvote_count": 12,
      "downvote_count": 1,
      "user_vote": "up",  // "up", "down", or null
      "created_at": "2025-10-25T18:30:00Z",
      "updated_at": "2025-10-25T18:30:00Z"
    }
  ]
}
```

**Performance:** 7 database queries with prefetching

**Frontend Service:** `locationsApi.getReviews(locationId)`

---

#### `POST /api/locations/{location_id}/reviews/`
Create a review for a location.

**Authentication:** Required
**Rate Limit:** 20 requests/hour (content creation)

**Request Body:**
```json
{
  "rating": 5,
  "comment": "Amazing spot for stargazing! Clear skies and minimal light pollution."
}
```

**Success Response (201):**
```json
{
  "id": 101,
  "user": {
    "id": 8,
    "username": "janedoe",
    "profile_picture_url": "/media/profile_pics/default.png"
  },
  "location": 1,
  "rating": 5,
  "comment": "Amazing spot for stargazing! Clear skies and minimal light pollution.",
  "photos": [],
  "upvote_count": 0,
  "downvote_count": 0,
  "user_vote": null,
  "created_at": "2025-10-30T12:00:00Z",
  "updated_at": "2025-10-30T12:00:00Z"
}
```

**Frontend Service:** `locationsApi.createReview(locationId, data)`

---

#### `GET /api/locations/{location_id}/reviews/{id}/`
Retrieve a specific review.

**Authentication:** Optional (affects `user_vote` field)

**Response:** Same structure as single review in list response

---

#### `PATCH /api/locations/{location_id}/reviews/{id}/` or `PUT`
Update an existing review.

**Authentication:** Required (must be owner)
**Rate Limit:** 20 requests/hour (content creation)

**Request Body (partial update):**
```json
{
  "rating": 4,
  "comment": "Updated review text"
}
```

**Response:** Same as `GET /api/locations/{location_id}/reviews/{id}/`

---

#### `DELETE /api/locations/{location_id}/reviews/{id}/`
Delete a review.

**Authentication:** Required (must be owner)

**Success Response (204):** No content

---

#### `POST /api/locations/{location_id}/reviews/{id}/add_photos/`
Upload photos to a review (max 5 total).

**Authentication:** Required (must be review owner)
**Max Photos:** 5 per review
**File Size Limit:** 5MB per image
**Allowed Formats:** .jpg, .jpeg, .png, .gif, .webp

**Request Body (multipart/form-data):**
```
images: [File, File, ...]  // or review_images
```

**Success Response (201):**
```json
{
  "detail": "2 photo(s) added successfully",
  "photos": [
    {
      "id": 201,
      "image_url": "/media/review_photos/1/101/abc123.jpg",
      "order": 0
    },
    {
      "id": 202,
      "image_url": "/media/review_photos/1/101/def456.jpg",
      "order": 1
    }
  ]
}
```

**Error Responses:**
```json
// No photos provided (400)
{
  "error": "validation_error",
  "message": "No images provided",
  "status_code": 400
}

// Too many photos (400)
{
  "error": "validation_error",
  "message": "You already have 5 photos. Delete some before adding more.",
  "status_code": 400
}

// File too large (400)
{
  "error": "validation_error",
  "message": "Invalid file \"large.jpg\": File size exceeds 5MB limit",
  "status_code": 400
}
```

**Notes:**
- Images are automatically resized to max 1920x1920px
- Thumbnails (300x300px) are auto-generated
- Files are validated for size, MIME type, and content

---

#### `DELETE /api/locations/{location_id}/reviews/{id}/photos/{photo_id}/`
Delete a photo from a review.

**Authentication:** Required (must be review owner)

**Success Response (200):**
```json
{
  "detail": "Photo deleted successfully"
}
```

**Error Response (404):**
```json
{
  "error": "not_found",
  "message": "Photo not found",
  "status_code": 404
}
```

---

#### `POST /api/locations/{location_id}/reviews/{id}/vote/`
Upvote or downvote a review.

**Authentication:** Required
**Rate Limit:** 60 requests/hour (vote throttle)

**Request Body:**
```json
{
  "vote_type": "up"
}
```

**Vote Type Options:**
- `"up"` - Upvote
- `"down"` - Downvote

**Success Response (200):**
```json
{
  "detail": "Vote processed successfully",
  "upvote_count": 13,
  "downvote_count": 1,
  "user_vote": "up"  // Current user's vote: "up", "down", or null
}
```

**Frontend Service:** `locationsApi.voteOnReview(locationId, reviewId, voteType)`

**Vote Logic:**
- Same vote type = remove vote (toggle)
- Different vote type = change vote
- Self-voting is prevented

**Error Response (400):**
```json
{
  "error": "validation_error",
  "message": "You cannot vote on your own content.",
  "status_code": 400
}
```

**Notes:**
- The actual frontend service doesn't pass vote_type as a parameter
- It's a simple POST that toggles the vote

---

#### `POST /api/locations/{location_id}/reviews/{id}/report/`
Report a problematic review.

**Authentication:** Required
**Rate Limit:** 10 requests/hour (report throttle)

**Request Body:**
```json
{
  "report_type": "INAPPROPRIATE",
  "description": "This review contains offensive language."
}
```

**Success Response (201):**
```json
{
  "detail": "Review reported successfully"
}
```

---

### Comment Endpoints

#### `GET /api/locations/{location_id}/reviews/{review_id}/comments/`
List comments for a specific review.

**Authentication:** Optional (affects `user_vote` field)
**Pagination:** 20 comments per page

**Response:**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 501,
      "user": {
        "id": 10,
        "username": "stargazer99",
        "profile_picture_url": "/media/profile_pics/default.png"
      },
      "review": 101,
      "content": "Thanks for the tip! I'll check it out this weekend.",
      "upvote_count": 5,
      "downvote_count": 0,
      "user_vote": null,
      "created_at": "2025-10-26T10:15:00Z",
      "updated_at": "2025-10-26T10:15:00Z"
    }
  ]
}
```

**Performance:** 5 database queries with prefetching

---

#### `POST /api/locations/{location_id}/reviews/{review_id}/comments/`
Create a comment on a review.

**Authentication:** Required
**Rate Limit:** 20 requests/hour (content creation)

**Request Body:**
```json
{
  "content": "Thanks for the tip! I'll check it out this weekend."
}
```

**Success Response (201):**
```json
{
  "id": 501,
  "user": {
    "id": 10,
    "username": "stargazer99",
    "profile_picture_url": "/media/profile_pics/default.png"
  },
  "review": 101,
  "content": "Thanks for the tip! I'll check it out this weekend.",
  "upvote_count": 0,
  "downvote_count": 0,
  "user_vote": null,
  "created_at": "2025-10-30T12:00:00Z",
  "updated_at": "2025-10-30T12:00:00Z"
}
```

---

#### `GET /api/locations/{location_id}/reviews/{review_id}/comments/{id}/`
Retrieve a specific comment.

**Authentication:** Optional

**Response:** Same structure as single comment in list response

---

#### `PATCH /api/locations/{location_id}/reviews/{review_id}/comments/{id}/` or `PUT`
Update an existing comment.

**Authentication:** Required (must be owner)

**Request Body:**
```json
{
  "content": "Updated comment text"
}
```

**Response:** Same as GET comment

---

#### `DELETE /api/locations/{location_id}/reviews/{review_id}/comments/{id}/`
Delete a comment.

**Authentication:** Required (must be owner)

**Success Response (204):** No content

---

#### `POST /api/locations/{location_id}/reviews/{review_id}/comments/{id}/vote/`
Vote on a comment.

**Authentication:** Required
**Rate Limit:** 60 requests/hour (vote throttle)

**Request Body:**
```json
{
  "vote_type": "up"  // Options: "up" or "down"
}
```

**Success Response (200):**
```json
{
  "detail": "Vote processed successfully",
  "upvote_count": 6,
  "downvote_count": 0,
  "user_vote": "up"
}
```

---

#### `POST /api/locations/{location_id}/reviews/{review_id}/comments/{id}/report/`
Report a problematic comment.

**Authentication:** Required
**Rate Limit:** 10 requests/hour (report throttle)

**Request Body:**
```json
{
  "report_type": "SPAM",
  "description": "This comment is spam advertising."
}
```

**Success Response (201):**
```json
{
  "detail": "Review comment reported successfully"
}
```

---

### Favorite Location Endpoints

#### `GET /api/favorite-locations/`
List current user's favorite locations.

**Authentication:** Required
**Pagination:** 20 favorites per page
**Sort Order:** Newest first (by creation date)

**Response:**
```json
{
  "count": 8,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 42,
      "user": 5,
      "location": {
        "id": 1,
        "name": "Dark Sky Park",
        "latitude": 37.7749,
        "longitude": -122.4194,
        "elevation": 1234.5,
        "formatted_address": "123 Main St, San Francisco, CA 94102",
        "description": "Amazing stargazing location",
        "added_by": {
          "id": 3,
          "username": "admin"
        },
        "review_count": 23,
        "average_rating": 4.5,
        "reviews": [...]  // Full nested reviews
      },
      "nickname": "My favorite spot",  // Optional user-defined nickname
      "created_at": "2025-10-28T15:00:00Z"
    }
  ]
}
```

**Performance:** 11 database queries with extensive prefetching

**Frontend Service:** `profileApi.getFavorites()`

---

#### `POST /api/favorite-locations/`
Add a location to favorites.

**Authentication:** Required

**Request Body:**
```json
{
  "location": 1,
  "nickname": "My favorite spot"  // Optional
}
```

**Success Response (201):**
```json
{
  "id": 42,
  "user": 5,
  "location": {
    "id": 1,
    "name": "Dark Sky Park",
    // ... full location data
  },
  "nickname": "My favorite spot",
  "created_at": "2025-10-30T12:00:00Z"
}
```

---

#### `GET /api/favorite-locations/{id}/`
Retrieve a specific favorite.

**Authentication:** Required (must be owner)

**Response:** Same structure as single favorite in list response

---

#### `PATCH /api/favorite-locations/{id}/` or `PUT`
Update a favorite's nickname.

**Authentication:** Required (must be owner)

**Request Body:**
```json
{
  "nickname": "Updated nickname"
}
```

**Response:** Same as GET favorite

---

#### `DELETE /api/favorite-locations/{id}/`
Remove a location from favorites.

**Authentication:** Required (must be owner)

**Success Response (204):** No content

**Frontend Service:** `profileApi.removeFavorite(id)`

---

### User Profile Endpoints

**Note:** All authenticated profile endpoints use the `/api/users/me/*` pattern.

#### `GET /api/users/me/`
Get authenticated user's full profile data (includes email and private information).

**Authentication:** Required

**Response:**
```json
{
  "id": 5,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "bio": "Stargazing enthusiast",
  "location": "San Francisco, CA",
  "profile_picture_url": "/media/profile_pics/user_5_abc123.jpg",
  "pinned_badge_ids": [1, 3, 5],
  "date_joined": "2025-10-15T14:30:00Z"
}
```

**Frontend Service:** `profileApi.getMe()`

---

#### `POST /api/users/me/upload-picture/`
Upload a new profile picture.

**Authentication:** Required
**File Size Limit:** 5MB
**Allowed Formats:** .jpg, .jpeg, .png, .gif, .webp

**Request Body (multipart/form-data):**
```
profile_picture: File
```

**Success Response (200):**
```json
{
  "detail": "Profile picture updated successfully",
  "image_url": "/media/profile_pics/user_5_abc123.jpg"
}
```

**Frontend Service:** `profileApi.uploadProfilePicture(file)`

**Notes:**
- Old profile picture is automatically deleted
- Images are auto-optimized

---

#### `DELETE /api/users/me/remove-picture/`
Remove profile picture and reset to default.

**Authentication:** Required

**Success Response (200):**
```json
{
  "detail": "Profile picture removed successfully",
  "default_image_url": "/media/default-avatar.png"
}
```

**Frontend Service:** `profileApi.removeProfilePicture()`

---

#### `PATCH /api/users/me/update-name/`
Update user's first and last name.

**Authentication:** Required

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe"
}
```

**Success Response (200):**
```json
{
  "detail": "Name updated successfully.",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Frontend Service:** `profileApi.updateName(data)`

---

#### `PATCH /api/users/me/update-username/`
Update user's username.

**Authentication:** Required

**Request Body:**
```json
{
  "new_username": "johndoe2024"
}
```

**Success Response (200):**
```json
{
  "detail": "Username updated successfully.",
  "username": "johndoe2024"
}
```

**Error Response (400):**
```json
{
  "error": "validation_error",
  "message": "This username is already taken.",
  "status_code": 400
}
```

**Frontend Service:** `profileApi.updateUsername(data)`

---

#### `PATCH /api/users/me/update-email/`
Update user's email address.

**Authentication:** Required

**Request Body:**
```json
{
  "new_email": "newemail@example.com"
}
```

**Success Response (200):**
```json
{
  "detail": "Email updated successfully.",
  "new_email": "newemail@example.com"
}
```

**Error Response (400):**
```json
{
  "error": "validation_error",
  "message": "This email address is already registered.",
  "status_code": 400
}
```

**Frontend Service:** `profileApi.updateEmail(data)`

---

#### `PATCH /api/users/me/update-password/`
Change user's password.

**Authentication:** Required

**Request Body:**
```json
{
  "current_password": "OldPassword123!",
  "new_password": "NewSecurePassword456!"
}
```

**Success Response (200):**
```json
{
  "detail": "Password updated successfully."
}
```

**Error Response (400):**
```json
{
  "error": "validation_error",
  "message": "Current password is incorrect.",
  "status_code": 400
}
```

**Frontend Service:** `profileApi.updatePassword(data)`

**Notes:**
- Session is automatically updated to prevent logout
- Password must meet strength requirements
- `current_password` is optional if user has no password set (OAuth users)

---

#### `PATCH /api/users/me/update-bio/`
Update user's bio/description.

**Authentication:** Required

**Request Body:**
```json
{
  "bio": "Passionate stargazer exploring dark sky locations across the country."
}
```

**Success Response (200):**
```json
{
  "detail": "Bio updated successfully.",
  "bio": "Passionate stargazer exploring dark sky locations across the country."
}
```

**Frontend Service:** `profileApi.updateBio(data)`

**Notes:**
- Maximum 500 characters
- Can be set to empty string

---

#### `PATCH /api/users/me/update-location/`
Update user's location.

**Authentication:** Required

**Request Body:**
```json
{
  "location": "San Francisco, CA"
}
```

**Success Response (200):**
```json
{
  "detail": "Location updated successfully.",
  "location": "San Francisco, CA"
}
```

**Frontend Service:** `profileApi.updateLocation(data)`

**Notes:**
- Maximum 100 characters
- Can be set to empty string

---

#### `GET /api/users/me/social-accounts/`
Get user's connected social accounts (Google OAuth, etc.).

**Authentication:** Required

**Response:**
```json
{
  "social_accounts": [
    {
      "id": 1,
      "provider": "google",
      "email": "john@gmail.com",
      "date_connected": "2025-10-15T14:30:00Z"
    }
  ],
  "count": 1
}
```

**Frontend Service:** `profileApi.getSocialAccounts()`

---

#### `DELETE /api/users/me/disconnect-social/{account_id}/`
Disconnect a social account.

**Authentication:** Required

**URL Parameters:**
- `account_id` - Social account ID to disconnect

**Success Response (200):**
```json
{
  "detail": "Google account disconnected successfully.",
  "provider": "google"
}
```

**Error Response (400):**
```json
{
  "error": "validation_error",
  "message": "Cannot disconnect your only login method. Please set a password first.",
  "status_code": 400
}
```

**Frontend Service:** `profileApi.disconnectSocialAccount(accountId)`

---

### Public User Endpoints

**Note:** These endpoints are for viewing public user profiles (no authentication required).

#### `GET /api/users/{username}/`
Get public profile for any user by username.

**Authentication:** Not required

**URL Parameters:**
- `username` - Username to fetch

**Response:**
```json
{
  "id": 8,
  "username": "janedoe",
  "first_name": "Jane",
  "last_name": "Doe",
  "bio": "Night sky photographer",
  "location": "Portland, OR",
  "profile_picture_url": "/media/profile_pics/user_8.jpg",
  "date_joined": "2025-09-20T10:00:00Z",
  "follower_count": 45,
  "following_count": 32,
  "review_count": 12,
  "location_count": 5
}
```

**Frontend Service:** `publicUserApi.getUser(username)`

**Notes:**
- Email is NOT included (private)
- Public view only

---

#### `GET /api/users/{username}/reviews/`
Get public reviews for any user by username (paginated).

**Authentication:** Not required
**Pagination:** 20 reviews per page

**URL Parameters:**
- `username` - Username to fetch reviews for

**Query Parameters:**
- `page` - Page number (default: 1)

**Response:**
```json
{
  "count": 12,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 101,
      "location": {
        "id": 1,
        "name": "Dark Sky Park"
      },
      "rating": 5,
      "comment": "Amazing spot!",
      "created_at": "2025-10-25T18:30:00Z"
    }
  ]
}
```

**Frontend Service:** `publicUserApi.getUserReviews(username, page)`

---

#### `GET /api/users/{username}/is-following/`
Check if authenticated user is following a specific user.

**Authentication:** Required

**URL Parameters:**
- `username` - Username to check

**Response:**
```json
{
  "is_following": true,
  "username": "janedoe"
}
```

**Frontend Service:** `publicUserApi.checkFollowStatus(username)`

---

#### `POST /api/users/{username}/follow/`
Follow a user.

**Authentication:** Required

**URL Parameters:**
- `username` - Username to follow

**Success Response (200):**
```json
{
  "detail": "You are now following janedoe.",
  "is_following": true
}
```

**Frontend Service:** `publicUserApi.followUser(username)`

---

#### `DELETE /api/users/{username}/follow/`
Unfollow a user.

**Authentication:** Required

**URL Parameters:**
- `username` - Username to unfollow

**Success Response (200):**
```json
{
  "detail": "You have unfollowed janedoe.",
  "is_following": false
}
```

**Frontend Service:** `publicUserApi.unfollowUser(username)`

**Notes:**
- The follow/unfollow endpoint is a toggle using POST/DELETE

---

#### `GET /api/users/{username}/followers/`
Get list of users who follow the specified user (paginated).

**Authentication:** Not required
**Pagination:** 20 users per page

**URL Parameters:**
- `username` - Username to get followers for

**Query Parameters:**
- `page` - Page number (default: 1)

**Response:**
```json
{
  "count": 45,
  "next": "http://127.0.0.1:8000/api/users/janedoe/followers/?page=2",
  "previous": null,
  "results": [
    {
      "id": 10,
      "username": "stargazer99",
      "profile_picture_url": "/media/profile_pics/user_10.jpg"
    }
  ]
}
```

**Frontend Service:** `publicUserApi.getFollowers(username, page)`

---

#### `GET /api/users/{username}/following/`
Get list of users that the specified user is following (paginated).

**Authentication:** Not required
**Pagination:** 20 users per page

**URL Parameters:**
- `username` - Username to get following list for

**Query Parameters:**
- `page` - Page number (default: 1)

**Response:**
```json
{
  "count": 32,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 5,
      "username": "johndoe",
      "profile_picture_url": "/media/profile_pics/user_5.jpg"
    }
  ]
}
```

**Frontend Service:** `publicUserApi.getFollowing(username, page)`

---

### Badge Endpoints

#### `GET /api/users/{username}/badges/`
Get user's PUBLIC badge display (for profile pages).

**Authentication:** Not required

**URL Parameters:**
- `username` - Username to get badges for

**Response:**
```json
{
  "earned": [
    {
      "id": 1,
      "name": "First Steps",
      "description": "Visited your first location",
      "icon": "/badges/first-steps.svg",
      "category": "EXPLORATION",
      "tier": "BRONZE",
      "date_earned": "2025-10-15T14:30:00Z"
    }
  ],
  "pinned_badge_ids": [1, 3, 5]
}
```

**Frontend Service:** `publicUserApi.getUserBadges(username)`

**Notes:**
- Returns only earned badges
- Same view for everyone (including profile owner)
- For authenticated users viewing their own profile, use the collection endpoint instead

---

#### `GET /api/users/me/badges/collection/`
Get authenticated user's FULL badge collection (earned, in-progress, locked).

**Authentication:** Required

**Response:**
```json
{
  "earned": [
    {
      "id": 1,
      "name": "First Steps",
      "description": "Visited your first location",
      "icon": "/badges/first-steps.svg",
      "category": "EXPLORATION",
      "tier": "BRONZE",
      "date_earned": "2025-10-15T14:30:00Z"
    }
  ],
  "in_progress": [
    {
      "id": 2,
      "name": "Globe Trotter",
      "description": "Visit 10 different locations",
      "icon": "/badges/globe-trotter.svg",
      "category": "EXPLORATION",
      "tier": "SILVER",
      "progress": 5,
      "required": 10,
      "progress_percentage": 50
    }
  ],
  "locked": [
    {
      "id": 3,
      "name": "Night Owl",
      "description": "Post 5 reviews between midnight and 4 AM",
      "icon": "/badges/night-owl.svg",
      "category": "COMMUNITY",
      "tier": "GOLD"
    }
  ],
  "pinned_badge_ids": [1]
}
```

**Frontend Service:** `profileApi.getMyBadgeCollection()`

**Use Case:** Private /profile/badges page showing all badges with progress tracking

---

#### `PATCH /api/users/me/badges/pin/`
Update user's pinned badges (max 3 badges).

**Authentication:** Required

**Request Body:**
```json
{
  "pinned_badge_ids": [1, 3, 5]
}
```

**Success Response (200):**
```json
{
  "detail": "Pinned badges updated successfully.",
  "pinned_badge_ids": [1, 3, 5],
  "pinned_badges": [
    {
      "id": 1,
      "name": "First Steps",
      "icon": "/badges/first-steps.svg"
    },
    {
      "id": 3,
      "name": "Globe Trotter",
      "icon": "/badges/globe-trotter.svg"
    },
    {
      "id": 5,
      "name": "Night Owl",
      "icon": "/badges/night-owl.svg"
    }
  ]
}
```

**Frontend Service:** `profileApi.updatePinnedBadges(data)`

**Notes:**
- Maximum 3 pinned badges
- Can only pin earned badges
- Order matters (displayed in the order provided)

---

## Error Handling

All API errors follow a consistent format:

### Error Response Structure

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "status_code": 400,
  "details": {}  // Optional additional context
}
```

### Common Error Codes

| Status | Error Code | Description |
|--------|-----------|-------------|
| 400 | `validation_error` | Invalid input data |
| 401 | `authentication_failed` | Invalid credentials |
| 401 | `not_authenticated` | Authentication required |
| 403 | `permission_denied` | Insufficient permissions |
| 404 | `not_found` | Resource not found |
| 429 | `throttled` | Rate limit exceeded |
| 500 | `server_error` | Internal server error |

### Example Error Handling

```javascript
async function handleApiRequest(url, options) {
  try {
    const response = await fetch(url, options);
    const data = await response.json();

    if (!response.ok) {
      // Handle error based on error code
      switch (data.error) {
        case 'authentication_failed':
          redirectToLogin();
          break;
        case 'permission_denied':
          showErrorMessage('You don\'t have permission to perform this action.');
          break;
        case 'throttled':
          showErrorMessage('Too many requests. Please try again later.');
          break;
        default:
          showErrorMessage(data.message);
      }
      return null;
    }

    return data;
  } catch (error) {
    console.error('Network error:', error);
    showErrorMessage('Network error. Please check your connection.');
    return null;
  }
}
```

---

## Rate Limiting

### Rate Limit Configuration

| User Type | Endpoint Type | Limit |
|-----------|--------------|-------|
| Anonymous | General | 100 requests/hour |
| Authenticated | General | 1000 requests/hour |
| All | Login/Register | 5 requests/minute |
| All | Password Reset | 3 requests/hour |
| All | Email Verification Resend | 1 request per 3 minutes |
| Authenticated | Content Creation | 20 requests/hour |
| Authenticated | Voting | 60 requests/hour |
| Authenticated | Reporting | 10 requests/hour |

### Rate Limit Headers

Rate limit information is included in response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 995
X-RateLimit-Reset: 1698765432
```

### Throttled Response

When rate limit is exceeded:

```json
{
  "error": "throttled",
  "message": "Request was throttled. Expected available in 3600 seconds.",
  "status_code": 429,
  "details": {
    "wait": 3600
  }
}
```

---

## Performance Characteristics

### Query Optimization Results

| Endpoint | Queries (Before) | Queries (After) | Reduction |
|----------|------------------|-----------------|-----------|
| Location list (20 items) | 548 | 4 | 99.3% |
| Location detail (5 reviews) | 32 | 9 | 71.9% |
| Review list (20 items) | 31 | 7 | 77.4% |
| Favorite locations (20) | 46 | 11 | 76.1% |

### Caching Strategy

| Endpoint | Cache Duration | Strategy | Performance Gain |
|----------|---------------|----------|------------------|
| `/api/locations/` | 15 min | User-aware per page | 10x faster |
| `/api/locations/{id}/` | 15 min | User-aware per location | 4x faster |
| `/api/locations/map_geojson/` | 30 min | Version-based O(1) invalidation | 60x faster |

### Response Sizes

| Endpoint | Per Item | 20 Items | 100 Items |
|----------|----------|----------|-----------|
| Map marker | ~30 bytes | ~600 bytes | ~3 KB |
| Location (list) | ~3 KB | ~60 KB | ~300 KB |
| Location (detail, 5 reviews) | ~7 KB | N/A | N/A |
| Review | ~1 KB | ~20 KB | ~100 KB |
| Comment | ~200 bytes | ~4 KB | ~20 KB |

---

## Frontend Integration Patterns

### Pattern 1: Map View with GeoJSON

```javascript
import { useMapMarkers } from '../hooks/useMapMarkers';

function ExploreMap() {
  const { geojson, markerMap, isLoading } = useMapMarkers();

  // Pass GeoJSON directly to Mapbox source
  // geojson = { type: 'FeatureCollection', features: [...] }

  // O(1) lookup for marker details
  const handleMarkerClick = (markerId) => {
    const markerData = markerMap.get(markerId);
    // markerData = { id, name, is_favorited, average_rating, images, ... }
    showBottomCard(markerData);
  };

  return (
    <Map>
      <Source id="locations" type="geojson" data={geojson} />
      <Layer {...clusterLayer} />
      <Layer {...unclusteredPointLayer} />
    </Map>
  );
}
```

**Performance:** GeoJSON pre-generated on backend, direct Mapbox pass-through

---

### Pattern 2: Location List with Infinite Scroll

```javascript
let currentPage = 1;
let hasMore = true;

async function loadMoreLocations() {
  if (!hasMore) return;

  const response = await fetch(`/api/locations/?page=${currentPage}`);
  const data = await response.json();

  appendLocations(data.results);

  hasMore = data.next !== null;
  currentPage++;
}

// Set up infinite scroll
window.addEventListener('scroll', () => {
  if (isNearBottom()) {
    loadMoreLocations();
  }
});
```

---

### Pattern 3: Location Detail (Scalable)

```javascript
// Recommended pattern for locations with many reviews
async function loadLocationDetail(locationId) {
  // Load location info and first page of reviews in parallel
  const [locationResponse, reviewsResponse] = await Promise.all([
    fetch(`/api/locations/${locationId}/`),
    fetch(`/api/locations/${locationId}/reviews/?page=1`)
  ]);

  const location = await locationResponse.json();
  const reviewsData = await reviewsResponse.json();

  return {
    location: location,
    reviews: reviewsData.results,
    totalReviews: reviewsData.count,
    hasMoreReviews: reviewsData.next !== null
  };
}

// Load more reviews when user scrolls
async function loadMoreReviews(locationId, page) {
  const response = await fetch(`/api/locations/${locationId}/reviews/?page=${page}`);
  const data = await response.json();
  return data.results;
}
```

---

### Pattern 4: Creating Content with Photos

```javascript
async function createReviewWithPhotos(locationId, reviewData, photoFiles) {
  // Step 1: Create the review
  const reviewResponse = await makeAuthenticatedRequest(
    `/api/locations/${locationId}/reviews/`,
    'POST',
    {
      rating: reviewData.rating,
      comment: reviewData.comment
    }
  );

  const review = await reviewResponse.json();

  // Step 2: Upload photos if provided
  if (photoFiles.length > 0) {
    const formData = new FormData();
    photoFiles.forEach(file => {
      formData.append('images', file);
    });

    const photoResponse = await fetch(
      `/api/locations/${locationId}/reviews/${review.id}/add_photos/`,
      {
        method: 'POST',
        credentials: 'include',
        headers: {
          'X-CSRFToken': getCsrfToken()
        },
        body: formData
      }
    );

    const photoData = await photoResponse.json();
    review.photos = photoData.photos;
  }

  return review;
}
```

---

### Pattern 5: Voting

```javascript
async function handleVote(contentType, locationId, contentId, voteType, additionalParams = {}) {
  let url;

  switch (contentType) {
    case 'review':
      url = `/api/locations/${locationId}/reviews/${contentId}/vote/`;
      break;
    case 'comment':
      url = `/api/locations/${locationId}/reviews/${additionalParams.reviewId}/comments/${contentId}/vote/`;
      break;
  }

  const response = await makeAuthenticatedRequest(url, 'POST', {
    vote_type: voteType  // "up" or "down"
  });

  // response = { detail, upvote_count, downvote_count, user_vote }
  return response;
}

// Usage
const voteData = await handleVote('review', 1, 101, 'up');
updateVoteDisplay(voteData);
```

---

### Pattern 6: Handling Authentication

```javascript
// Check if user is authenticated
async function isAuthenticated() {
  const response = await fetch('/api/profile/update-name/', {
    method: 'PATCH',
    credentials: 'include',
    headers: {
      'X-CSRFToken': getCsrfToken(),
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({})  // Empty body to test auth
  });

  return response.status !== 401;
}

// Login
async function login(username, password) {
  const response = await fetch('/api/auth/login/', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken()
    },
    body: JSON.stringify({ username, password })
  });

  const data = await response.json();

  if (response.ok) {
    window.location.href = data.redirect_url;
  } else {
    handleLoginError(data);
  }
}

// Logout
async function logout() {
  const response = await fetch('/api/auth/logout/', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'X-CSRFToken': getCsrfToken()
    }
  });

  const data = await response.json();
  window.location.href = data.redirect_url;
}
```

---

## Best Practices

### 1. Always Use Pagination
Don't try to load all items at once for list endpoints. Use the pagination links provided in responses.

### 2. Implement Optimistic UI Updates
Update the UI immediately, then sync with the server in the background. Roll back on failure.

```javascript
async function optimisticVote(reviewId, voteType) {
  // Update UI immediately
  const oldState = updateVoteUI(reviewId, voteType);

  try {
    // Sync with server
    const response = await handleVote('review', locationId, reviewId, voteType);

    // Update with actual counts from server
    updateVoteUI(reviewId, response);
  } catch (error) {
    // Rollback on failure
    updateVoteUI(reviewId, oldState);
    showErrorMessage('Failed to save vote');
  }
}
```

### 3. Cache Aggressively
Location data doesn't change often. Cache API responses client-side with appropriate TTL.

### 4. Prefetch on Hover
Start loading detail data when user hovers over a location to make navigation feel instant.

### 5. Handle Rate Limits Gracefully
Show friendly messages when rate limits are hit. Implement exponential backoff for retries.

### 6. Use Map-Optimized Endpoints
Always use `/api/locations/map_geojson/` for map displays, not the full location list endpoint.

### 7. Validate Before Submission
Validate form data client-side before making API requests to reduce unnecessary server load.

---

## Support

For bugs, feature requests, or questions:
- **GitHub Issues:** https://github.com/anthropics/claude-code/issues
- **Documentation:** https://docs.claude.com/en/docs/claude-code/

---

**Last Updated:** 2026-01-19
**API Version:** 1.0
**Production URL:** https://starview.app

---

## Frontend Service Layer

All API endpoints are accessed through service modules in `starview_frontend/src/services/`:

- **`api.js`** - Axios instance with CSRF token handling
- **`auth.js`** - Authentication endpoints (`authApi`)
- **`locations.js`** - Location endpoints (`locationsApi`)
- **`profile.js`** - User profile endpoints (`profileApi`, `publicUserApi`)
- **`stats.js`** - Platform stats (`statsApi`)
- **`weather.js`** - Weather data (`weatherApi`)
- **`bortle.js`** - Bortle scale/light pollution (`bortleApi`)
- **`moon.js`** - Moon phase data (`moonApi`)

**Example Import:**
```javascript
import { authApi } from './services/auth';
import { locationsApi } from './services/locations';
import { profileApi, publicUserApi } from './services/profile';
import statsApi from './services/stats';
import weatherApi from './services/weather';
import bortleApi from './services/bortle';
```
