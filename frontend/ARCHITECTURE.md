# Frontend Architecture Guide

**Stack:** React 19 + Vite + TanStack Query + Django REST Backend
**Last Updated:** 2026-01-24 (Sprint 11)
**Status:** Folder-Based Architecture (Industry Standard)

---

## Directory Structure

```
starview_frontend/src/
├── components/
│   ├── shared/                    # Shared utility components
│   │   ├── Alert/
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── LoadingSpinner/
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── ErrorBoundary/
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── ImageCarousel/         # Swipe/arrow image carousel (1-5 images)
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── LocationAutocomplete/  # Mapbox autocomplete
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── ProfilePictureModal/
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── Toast/                 # Global toast notifications
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── MoonPhaseGraphic/      # SVG moon phase rendering with rotation
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── WeatherGraphic/        # Weather icon (clouds/sun/moon/rain)
│   │   │   └── index.jsx
│   │   ├── BortleSkySlider/       # Interactive Bortle comparison slider
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── DateNavigator/         # Date selection for calendar views
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── LocationChip/          # Tappable location indicator for sky page heroes
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   └── LocationModal/         # Full-screen modal for changing location
│   │       ├── index.jsx
│   │       └── styles.css
│   ├── CookieConsent/             # GDPR/analytics cookie consent
│   │   ├── index.jsx
│   │   └── CookiePreferencesButton.jsx
│   ├── home/                       # Home page components
│   │   ├── HeroCarousel/           # Background image carousel (5 random location images)
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   ├── PopularNearby/          # Horizontal location carousel near user
│   │   │   ├── index.jsx
│   │   │   └── styles.css
│   │   └── ProfileSetupCard/       # Onboarding card with profile completion progress
│   │       ├── index.jsx
│   │       └── styles.css
│   ├── badges/                    # Badge-related components
│   │   ├── BadgeCard/
│   │   ├── BadgeCompact/
│   │   ├── BadgeModal/
│   │   ├── BadgeSection/
│   │   └── PinnedBadges/
│   ├── profile/                   # Profile page components
│   │   ├── ProfileHeader/
│   │   ├── ProfileStats/
│   │   ├── ProfileSettings/
│   │   ├── BadgesTab/
│   │   ├── FavoritesTab/
│   │   ├── MyReviewsTab/
│   │   ├── SettingsTab/
│   │   ├── CollapsibleSection/
│   │   ├── ConnectedAccountsSection/
│   │   ├── PreferencesSection/
│   │   └── forms/
│   │       ├── PasswordForm/
│   │       ├── EmailForm/
│   │       ├── UsernameForm/
│   │       ├── PersonalInfoForm/
│   │       ├── ProfilePictureForm/
│   │       ├── BioForm/
│   │       └── LocationForm/
│   ├── explore/                   # Explore page components
│   │   ├── ExploreMap/            # Mapbox map with markers, navigation mode, route display
│   │   │   ├── index.jsx          # Main map component with controls
│   │   │   ├── MapCard.jsx        # Unified card: bottom (mobile) + popup (desktop)
│   │   │   └── styles.css
│   │   ├── ExploreFiltersModal/   # Filter modal (type, rating, distance, verified)
│   │   │   ├── index.jsx          # Full-screen on mobile, centered dialog on desktop
│   │   │   └── styles.css
│   │   ├── LocationCard/          # Location card with rating, distance, favorite
│   │   ├── VirtualizedLocationList/ # Windowed list for mobile infinite scroll
│   │   ├── Pagination/            # Desktop page navigation controls
│   │   └── ViewToggle/            # List/map view toggle button
│   ├── navbar/
│   │   ├── index.jsx
│   │   └── styles.css
│   ├── starfield/                 # Animated starfield background
│   │   ├── index.jsx
│   │   └── styles.css
│   ├── Footer/                    # Footer component (empty/placeholder)
│   ├── ProtectedRoute/
│   │   └── index.jsx
│   ├── GuestRoute/                # Redirects authenticated users from login/register
│   │   └── index.jsx
│   └── ScrollToTop/               # Scroll position management on navigation
│       └── index.jsx
├── pages/
│   ├── Home/
│   │   ├── index.jsx
│   │   └── styles.css
│   ├── Login/
│   ├── Register/
│   ├── Profile/
│   ├── PublicProfile/
│   ├── Explore/                   # Location discovery with list/map views
│   ├── VerifyEmail/
│   ├── EmailVerified/
│   ├── EmailConfirmError/
│   ├── SocialAccountExists/
│   ├── PasswordResetRequest/
│   ├── PasswordResetConfirm/
│   ├── Moon/                      # Moon phase educational page (lunar cycle, calendar link)
│   ├── Sky/                       # Sky conditions hub page (Tonight, Moon, Bortle, Weather)
│   ├── Tonight/                   # Tonight's stargazing conditions (Sky Score dashboard)
│   │   ├── index.jsx
│   │   ├── HourlyTimeline.jsx     # Interactive nighttime weather timeline
│   │   ├── CloudLayerBreakdown.jsx # Low/mid/high cloud layer visualization
│   │   └── utils.js               # Nighttime hour filtering utilities
│   ├── Bortle/                    # Bortle scale educational page
│   ├── Weather/                   # Weather factors educational page
│   ├── Terms/                     # Terms of service page
│   ├── Privacy/                   # Privacy policy page
│   ├── Accessibility/             # Accessibility statement page
│   ├── CCPA/                      # California privacy rights page
│   └── NotFound/
├── hooks/                         # Flat - no folders
│   ├── useTheme.js
│   ├── usePinnedBadges.js
│   ├── useFormSubmit.js
│   ├── usePasswordValidation.js
│   ├── useProfileData.js          # React Query hook for profile data
│   ├── useStats.js                # React Query hook for platform stats
│   ├── useLocations.js            # React Query hooks: useLocations (infinite), useLocationsPaginated, useToggleFavorite
│   ├── useMapMarkers.js           # React Query hook for map GeoJSON (30-min stale time, O(1) lookup via markerMap)
│   ├── useExploreData.js          # Unified data hook - switches between infinite (mobile) and paginated (desktop)
│   ├── useMoonPhases.js           # React Query hooks for moon phase data (useMoonPhases, useTodayMoonPhase, etc.)
│   ├── useWeather.js              # React Query hook for weather data (forecast, historical, historical_average)
│   ├── useNighttimeWeather.js     # Optimized hook for Tonight page (single API call for 6PM-6AM)
│   ├── useBortle.js               # React Query hook for Bortle scale (light pollution)
│   ├── useSEO.js                  # Dynamic page meta tags (title, description, canonical, OG)
│   ├── useAnimatedDropdown.js     # Dropdown state with CSS animation timing
│   ├── useIntersectionObserver.js # Viewport detection for infinite scroll
│   ├── useUserLocation.js         # Browser geolocation with profile location fallback
│   ├── useMediaQuery.js           # CSS media query detection (useIsDesktop helper)
│   └── useRequireAuth.js          # Auth guard - redirects to login with return URL
├── services/                      # Flat - no folders
│   ├── api.js
│   ├── auth.js
│   ├── profile.js
│   ├── locations.js
│   ├── moon.js                    # Moon phase API calls
│   ├── weather.js                 # Weather API (getForecast, getForecastRange)
│   ├── bortle.js                  # Bortle scale API
│   └── stats.js
├── context/
│   └── AuthContext.jsx
├── contexts/
│   ├── ToastContext.jsx           # Global toast notification system
│   ├── CookieConsentContext.jsx   # GDPR cookie consent state management
│   └── LocationContext.jsx        # Unified location state for sky pages and explore
├── utils/
│   ├── badges.js
│   ├── geo.js                     # Distance calculation, formatting (Haversine)
│   ├── navigation.js              # Duration formatting, navigation app deep links, geocoding
│   └── units.js                   # Unit formatting with user preference support
├── styles/
│   └── global.css                 # All design tokens, reset, and shared styles
├── App.jsx                        # Routes only
├── main.jsx                       # App entry: providers, ErrorBoundary, Navbar, Starfield
└── index.css                      # Imports global.css
```

---

## Component Pattern

> **Creating new components?** Read `STYLE_GUIDE.md` first for available utility classes (`.glass-card`, `.btn-primary`, `.empty-state`, etc.) and CSS variables. Never hardcode colors, spacing, or recreate existing patterns.

Each component lives in its own folder with:
- `index.jsx` - Component code
- `styles.css` - Component styles (if needed)

```
ComponentName/
├── index.jsx
└── styles.css
```

**Import pattern:**
```javascript
// Clean imports - no filename needed
import Alert from '../components/shared/Alert';
import Navbar from '../components/navbar';
import BadgeCard from '../components/badges/BadgeCard';
import ProfileSettings from '../components/profile/ProfileSettings';
import Starfield from '../components/starfield';
```

**CSS import inside component:**
```javascript
// In index.jsx
import './styles.css';
```

---

## Styles Architecture

All global styles consolidated in `styles/global.css`:

| Section | Contents |
|---------|----------|
| Design Tokens | CSS variables (colors, spacing, typography) - Linear-inspired |
| CSS Reset | Box-sizing, margins, body defaults |
| Layout | `.page-container` responsive class |
| Buttons | `.btn`, `.btn-icon` |
| Cards | `.card`, `.card-title`, `.card-body` |
| Forms | `.form-group`, `.form-label`, `.form-input`, `.form-textarea`, `.form-hint` |

Component-specific styles live in their own folders (e.g., `navbar/styles.css`).

**Design System:** See `STYLE_GUIDE.md` for complete design tokens, Linear-inspired principles, and component patterns.

---

## Data Flow

```
User Action
    ↓
Component (useState / custom hooks)
    ↓
Service Layer (services/*.js)
    ↓
API Client (services/api.js)
    ↓
Django Backend (http://127.0.0.1:8000/api/)
    ↓
Response
    ↓
Update State
    ↓
Re-render
```

---

## Key Files

### Services (Flat)

> **Connecting to a new backend endpoint?** The `starview-api-endpoint` skill guides through service functions, React Query hooks, and keeps API_GUIDE.md in sync.

| File | Purpose |
|------|---------|
| `api.js` | Axios client, CSRF, interceptors, 401 handling |
| `auth.js` | Login, logout, registration, checkStatus |
| `profile.js` | User profile, badges, favorites, social accounts (profileApi + publicUserApi) |
| `locations.js` | Location CRUD, hero carousel, popular nearby |
| `moon.js` | Moon phase data (getPhases, getCurrentWeek, getCurrentMonth) |
| `weather.js` | Weather data (getForecast, getForecastRange with date support) |
| `bortle.js` | Bortle scale data (getBortle) |
| `stats.js` | Platform statistics (locations, reviews, stargazers) |

### Hooks (Flat)

| File | Purpose |
|------|---------|
| `useFormSubmit.js` | Form submission with loading/error/success |
| `usePasswordValidation.js` | Password strength validation |
| `useTheme.js` | Theme switching (dark/light) with localStorage |
| `usePinnedBadges.js` | Pinned badges state management |
| `useProfileData.js` | React Query hook for profile data (badges, social accounts) |
| `useStats.js` | React Query hook for platform statistics |
| `useLocations.js` | React Query hooks: `useLocations` (infinite), `useLocationsPaginated`, `usePopularNearby`, `useToggleFavorite` |
| `useMapMarkers.js` | React Query hook for map GeoJSON with filter support; returns `{ geojson, markers, markerMap }` |
| `useExploreData.js` | Unified data fetching for Explore page - automatically uses infinite (mobile) or paginated (desktop) |
| `useAnimatedDropdown.js` | Dropdown state management with CSS close animation timing |
| `useIntersectionObserver.js` | Viewport detection for infinite scroll triggers |
| `useUnits.js` | Distance/elevation unit formatting with user preference (imperial/metric), backend sync |
| `useExploreFilters.js` | URL-based filter state for Explore page (search, type, rating, distance, verified, sort) |
| `useMediaQuery.js` | CSS media query subscription; `useIsDesktop()` returns true at 1024px+ |
| `useRequireAuth.js` | Auth guard for actions - redirects to login with return URL |
| `useMapboxDirections.js` | Driving directions with cascade fallback (Mapbox -> ORS -> geodesic), LRU cache |
| `useMoonPhases.js` | Moon phase data hooks: `useMoonPhases`, `useTodayMoonPhase`, `useWeeklyMoonPhases`, `useMonthlyMoonPhases` |
| `useWeather.js` | Weather data with source-aware responses (forecast/historical/historical_average) |
| `useNighttimeWeather.js` | Optimized Tonight page hook - single API call for 6PM-6AM data |
| `useBortle.js` | Bortle scale (light pollution) data hook |
| `useSEO.js` | Dynamic document meta tags (title, description, canonical, OG/Twitter cards) |

### Shared Components

| Component | Purpose |
|-----------|---------|
| `Alert` | Success/error/warning/info alerts with icons |
| `LoadingSpinner` | Reusable loading indicator (multiple sizes) |
| `ErrorBoundary` | App-wide error catching |
| `ImageCarousel` | Swipe (mobile) + arrow (desktop) image carousel with auto-play, lazy loading |
| `LocationAutocomplete` | Mapbox location search autocomplete |
| `ProfilePictureModal` | Modal for profile picture preview/zoom |
| `Toast` | Toast notifications (success, error, warning, info) |
| `MoonPhaseGraphic` | SVG moon phase with accurate shadow, texture, and rotation angle |
| `WeatherGraphic` | Weather icon (clouds/sun/moon/rain based on conditions) |
| `BortleSkySlider` | Interactive Bortle comparison slider showing sky quality differences |
| `DateNavigator` | Date selection with prev/next/today navigation |
| `LocationChip` | Tappable location indicator for sky page heroes, shows source icon |
| `LocationModal` | Full-screen modal for changing location (search, recent, current) |

### Explore Page Components (`components/explore/`)

| Component | Purpose |
|-----------|---------|
| `ExploreMap` | Mapbox GL map with clustered markers, navigation mode, route display |
| `MapCard` | Unified location card for map: bottom slide-up (mobile) + centered popup (desktop) |
| `LocationCard` | Mobile-first location card with image carousel, rating, distance, favorite toggle |
| `ExploreFiltersModal` | Full-screen filter modal: type, rating, distance, verified. Single-section mode for mobile chips |
| `VirtualizedLocationList` | Windowed/virtualized list for mobile infinite scroll (performance) |
| `Pagination` | Desktop page navigation controls |
| `ViewToggle` | List/map view toggle button |

---

## Routes

| Path | Page Component | Auth | Route Guard |
|------|----------------|------|-------------|
| `/` | Home | No | - |
| `/login` | Login | No | GuestRoute |
| `/register` | Register | No | GuestRoute |
| `/profile` | Profile | **Yes** | ProtectedRoute |
| `/users/:username` | PublicProfile | No | - |
| `/explore` | Explore | No | - |
| `/sky` | Sky (hub page) | No | - |
| `/tonight` | Tonight (Sky Score) | No | - |
| `/bortle` | Bortle (educational) | No | - |
| `/moon` | Moon (educational) | No | - |
| `/weather` | Weather (educational) | No | - |
| `/verify-email` | VerifyEmail | No | - |
| `/email-verified` | EmailVerified | No | - |
| `/email-confirm-error` | EmailConfirmError | No | - |
| `/social-account-exists` | SocialAccountExists | No | - |
| `/password-reset` | PasswordResetRequest | No | - |
| `/password-reset-confirm/:uidb64/:token` | PasswordResetConfirm | No | - |
| `/terms` | Terms | No | - |
| `/privacy` | Privacy | No | - |
| `/accessibility` | Accessibility | No | - |
| `/ccpa` | CCPA | No | - |
| `*` (404) | NotFound | No | - |

**Route Guards:**
- `ProtectedRoute`: Redirects to `/login` if not authenticated
- `GuestRoute`: Redirects to `/` if already authenticated

---

## Service Usage

```javascript
import authApi from '../services/auth';
import { profileApi, publicUserApi } from '../services/profile';
import { locationsApi } from '../services/locations';
import statsApi from '../services/stats';

// Auth
await authApi.login({ email, password });
await authApi.logout();
await authApi.register(userData);
await authApi.checkStatus(); // Returns { authenticated: boolean, user: {...} }

// Locations
await locationsApi.getAll(params);    // Paginated list
await locationsApi.getById(id);       // Single location
await locationsApi.getMapGeoJSON();   // GeoJSON FeatureCollection for Mapbox
await locationsApi.markVisited(id);   // Check-in to location
await locationsApi.unmarkVisited(id); // Remove check-in
await locationsApi.toggleFavorite(id); // Toggle favorite (add/remove)
await locationsApi.getHeroCarousel(); // Random images for home hero (daily rotation)
await locationsApi.getPopularNearby({ lat, lng, limit }); // Top-rated locations nearby

// Profile (authenticated user)
await profileApi.getMe();
await profileApi.updateName(data);
await profileApi.uploadProfilePicture(file);
await profileApi.removeProfilePicture();
await profileApi.updateBio(data);
await profileApi.updateLocation(data);
await profileApi.getFavorites();
await profileApi.getMyBadgeCollection(); // Full collection: earned, in_progress, locked
await profileApi.updatePinnedBadges({ pinned_badge_ids: [1, 2, 3] });
await profileApi.getSocialAccounts();
await profileApi.disconnectSocialAccount(accountId);

// Public User Profiles (no auth required)
await publicUserApi.getUser(username);
await publicUserApi.getUserReviews(username, page);
await publicUserApi.getUserBadges(username); // Only earned badges
await publicUserApi.followUser(username);
await publicUserApi.unfollowUser(username);
await publicUserApi.getFollowers(username, page);
await publicUserApi.getFollowing(username, page);

// Platform Stats
await statsApi.getPlatformStats(); // Returns { locations, reviews, stargazers }
```

---

## Form Pattern

```javascript
import { useState } from 'react';
import useFormSubmit from '../../hooks/useFormSubmit';
import Alert from '../../components/shared/Alert';

function SomeForm({ onSuccess }) {
  const [data, setData] = useState({ field: '' });

  const { loading, error, success, handleSubmit } = useFormSubmit({
    onSubmit: async () => await someApi.update(data),
    onSuccess,
    successMessage: 'Saved!'
  });

  return (
    <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
      {error && <Alert type="error" message={error} />}
      {success && <Alert type="success" message={success} />}
      {/* fields */}
      <button disabled={loading}>Save</button>
    </form>
  );
}
```

---

## State Management

### LocationContext
Unified location management for sky pages (Tonight, Weather, Bortle) and Explore page.

```javascript
import { useLocation } from '../contexts/LocationContext';

function MyComponent() {
  const {
    location,              // Current active location (changes with search)
    actualLocation,        // User's real location (stable, from IP/browser only)
    source,                // 'browser' | 'ip' | 'search'
    isLoading,
    permissionState,       // 'granted' | 'denied' | 'prompt' | null
    recentLocations,       // Last 5 searched locations (localStorage)
    setLocation,           // (lat, lng, name, source) => void
    requestCurrentLocation, // Triggers browser geolocation
    clearLocation,         // Reset to IP fallback
  } = useLocation();
}
```

**Resolution order:**
1. sessionStorage (existing active location)
2. Browser geolocation (if permission granted)
3. IP geolocation (`/api/geolocate/`)

**Two location states:**
- `location`: Current active location (changes with search/selection)
- `actualLocation`: User's real location (stable, for "near you" features)

### ToastContext
Global toast notification system for displaying user feedback.

```javascript
import { useToast } from '../contexts/ToastContext';

function MyComponent() {
  const { showToast } = useToast();

  const handleAction = () => {
    showToast('Action completed!', 'success');      // success, error, warning, info
    showToast('Something went wrong', 'error', 6000); // custom duration (ms)
  };
}
```

**Features:**
- Auto-dismisses after configurable duration (default 4s)
- One toast at a time (replaces existing)
- Fixed position top-right, below navbar
- Manual dismiss via close button

### AuthContext
Global authentication state using React Context API.

```javascript
import { useAuth } from '../context/AuthContext';

function MyComponent() {
  const { isAuthenticated, user, loading, logout, refreshAuth } = useAuth();

  // user object: { id, username, email, first_name, last_name, profile_picture_url, ... }

  if (loading) return <LoadingSpinner />;

  return <div>Welcome {user?.username}</div>;
}
```

**Features:**
- Single auth check on app mount (prevents N+1 API calls)
- Automatic state clearing on 401 responses
- Refresh function for manual state updates

### TanStack Query (React Query)

Used for server state caching and data fetching.

**Configuration** (main.jsx):
```javascript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,     // 5 minutes
      gcTime: 10 * 60 * 1000,        // 10 minutes (cache lifetime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

**Query Hooks:**
- `useProfileData()` - Badge collection + social accounts (parallel fetching)
- `usePlatformStats()` - Platform statistics with threshold logic
- `useLocations()` - Infinite scroll locations for mobile
- `useLocationsPaginated()` - Paginated locations for desktop
- `useExploreData()` - Unified hook that selects infinite/paginated based on viewport
- `useMapMarkers()` - Map GeoJSON with `markerMap` for O(1) lookups (30-min unfiltered, 5-min filtered)
- `useToggleFavorite()` - Mutation with optimistic cache updates (syncs infinite, paginated, and mapGeoJSON caches)
- `useMapboxDirections()` - Route fetching with cascading fallback (Mapbox -> OpenRouteService -> geodesic), 24hr LRU cache

**Benefits:**
- Automatic caching and deduplication
- Parallel query execution
- Optimistic updates
- Query invalidation on mutations

---

## Environment

**Environment Variables:**
Frontend uses shared `.env` file from project root (configured via `envDir: '..'` in `vite.config.js`).

| Variable | Purpose | Default |
|----------|---------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `/api` |
| `VITE_MAPBOX_TOKEN` | Mapbox access token for LocationAutocomplete | Required for location search |

**Development:**
- Backend: `http://127.0.0.1:8000` (Django)
- Frontend: `http://localhost:5173` (Vite dev server)
- Vite proxies `/api`, `/media`, `/accounts`, `/admin`, `/static` to Django backend

**Vite Proxy Configuration:**
All API calls, media files, and Django admin routes are proxied to the Django backend in development mode. This prevents CORS issues and mirrors production routing.

---

## Build

```bash
cd starview_frontend
npm install      # Install dependencies
npm run dev      # Development server (http://localhost:5173)
npm run build    # Production build
npm run preview  # Preview production build locally
npm test         # Run tests (vitest watch mode)
npm run test:run # Run tests once
```

**Build output:** `dist/` folder

**Production Build Features:**
- Code splitting with lazy-loaded routes
- Asset optimization
- Custom plugin copies `public/badges/` to `dist/badges/`
- Sourcemaps disabled for smaller bundle size

---

## Key Architectural Patterns

### 1. Lazy Loading & Code Splitting
All 12 page components are lazy-loaded using `React.lazy()` and `Suspense`:

```javascript
const HomePage = lazy(() => import('./pages/Home'));

<Suspense fallback={<LoadingSpinner size="lg" fullPage />}>
  <Routes>...</Routes>
</Suspense>
```

**Mapbox** (149 kB) is also lazy-loaded in `LocationForm` - only downloads when user edits location settings.

**Benefit:** Smaller initial bundle size, faster page loads.

### 2. Error Handling
- **API Interceptors:** Automatic 401 redirect to login
- **Form Errors:** `useFormSubmit` hook extracts and displays error messages
- **ErrorBoundary:** Catches React errors, displays "Houston, We Have a Problem" UI (integrated in main.jsx, wraps App)

### 3. Folder-Based Components
Each component lives in its own folder with co-located styles:
```
BadgeCard/
├── index.jsx    # Component logic
└── styles.css   # Component styles
```

### 4. Service Layer Pattern
All API calls go through dedicated service files:
```javascript
// Component never touches axios directly
import { profileApi } from '../services/profile';
const response = await profileApi.getMe();
```

**Benefits:**
- Single source of truth for API endpoints
- Easy to mock for testing
- Consistent error handling

### 5. Custom Hooks for Reusability
- `useFormSubmit` - Eliminates boilerplate for form handling
- `useTheme` - Dark/light mode with localStorage persistence
- `useProfileData` - React Query wrapper with optimistic updates

### 6. Authentication Flow
1. App loads → AuthContext checks `/api/auth/status/`
2. Stores auth state + user object in context
3. ProtectedRoute/GuestRoute guard routes based on state
4. 401 response → Auto-logout + redirect to login

---

## Visual Development with MCP

Three MCP servers available - see `docs/MCP_WORKFLOW.md`:

| Server | Use Case |
|--------|----------|
| chrome-devtools | Browser automation, debugging, performance |
| puppeteer | Alternative browser automation |
| figma | Design-to-code, design tokens extraction |

**Quick Example:**
```
mcp__chrome-devtools__navigate_page(url="http://localhost:5173")
mcp__chrome-devtools__take_screenshot()
mcp__chrome-devtools__list_console_messages()
```

---

## Dependencies

**Core:**
- `react` + `react-dom` ^19.1.1
- `react-router-dom` ^7.9.4
- `axios` ^1.13.1
- `@tanstack/react-query` ^5.90.5

**UI:**
- `@mapbox/search-js-react` ^1.5.0 - Location autocomplete

**Build:**
- `vite` ^7.1.7
- `@vitejs/plugin-react` ^5.0.4

**Testing:**
- `vitest` ^3.2.4
- `@testing-library/react` ^16.3.0
- `@testing-library/jest-dom` ^6.9.1
