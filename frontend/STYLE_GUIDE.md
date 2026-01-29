# Starview Frontend Style Guide

**Last Updated:** 2026-01-29
**Design System:** Observatory-themed glass-morphism (cyan/teal accent)
**Source of Truth:** `starview_frontend/src/styles/global.css`

---

## Quick Reference: What to Use

| Need | Use This |
|------|----------|
| Card with blur effect | `.glass-card` |
| Clickable card | `.glass-card .glass-card--interactive` |
| Auth page layout | `.auth-page`, `.auth-page__content`, `.auth-page__card` |
| Primary button | `.btn-primary` |
| Secondary button | `.btn-secondary` |
| Danger button | `.btn-danger` |
| Social login button | `.btn-social` |
| Icon-only button | `.btn-icon` |
| Form input | `.form-input` |
| Form textarea | `.form-textarea` |
| Form group | `.form-group` + `.form-label` |
| Checkbox | `.form-checkbox` |
| Empty state | `.empty-state`, `.empty-state__icon`, `.empty-state__title` |
| Password toggle | `.password-toggle` |
| Section divider | `.section-divider` |
| Section accent (subtitle) | `.section-accent` |
| Loading spinner | `<LoadingSpinner />` component |
| Toast notification | `useToast()` hook from `ToastContext` |

---

## Design Tokens

### Colors (Dark Theme - Default)

```css
/* Background - Deep space observatory */
--bg-base: #0a0f1a;                           /* Main background */
--bg-elevated: #0d1320;                       /* Elevated surfaces */
--starfield-gradient: linear-gradient(to top, transparent 0%, #080c14 20%, #0a0f1a 100%);
--navbar-bg: hsla(220, 40%, 8%, 0.85);        /* Navbar backdrop */

/* Text - High contrast for readability */
--text-primary: #f0f4f8;                      /* Main text */
--text-secondary: #94a3b8;                    /* Secondary text */
--text-muted: #64748b;                        /* Muted/hint text */

/* Accent (Cyan/Teal - Observatory instrument glow) */
--accent: #00d4aa;
--accent-hover: #00e4b8;
--accent-light: #5eead4;
--accent-bg: rgba(0, 212, 170, 0.1);
--accent-border: rgba(0, 212, 170, 0.25);

/* Status Colors - Instrument readouts */
--success: #22c55e;
--success-bg: rgba(34, 197, 94, 0.1);
--success-border: rgba(34, 197, 94, 0.3);
--warning: #f59e0b;
--warning-bg: rgba(245, 158, 11, 0.1);
--warning-border: rgba(245, 158, 11, 0.3);
--error: #ef4444;
--error-bg: rgba(239, 68, 68, 0.1);
--error-border: rgba(239, 68, 68, 0.3);
--info: #06b6d4;
--info-bg: rgba(6, 182, 212, 0.1);
--info-border: rgba(6, 182, 212, 0.3);

/* Stars & Favorites */
--star-filled: #fbbf24;
--star-empty: #334155;
--favorite: #ec4899;
--favorite-hover: #db2777;

/* Elevation indicator */
--elevation: #f87171;

/* Borders - Subtle instrument panel lines */
--border: #1e293b;
--border-focus: #00d4aa;

/* Glass Card - Instrument panel surfaces */
--glass-bg: rgba(15, 23, 42, 0.6);
--glass-bg-hover: rgba(15, 23, 42, 0.8);
--glass-border: rgba(0, 212, 170, 0.08);
--glass-border-hover: rgba(0, 212, 170, 0.15);

/* Decorative - Cyan glow effects */
--glow-primary: rgba(0, 212, 170, 0.2);
--glow-secondary: rgba(6, 182, 212, 0.1);
--gradient-accent: linear-gradient(135deg, #00d4aa 0%, #06b6d4 100%);
--shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
--shadow-accent: 0 0 20px rgba(0, 212, 170, 0.3), 0 0 40px rgba(0, 212, 170, 0.1);
--shadow-accent-hover: 0 0 30px rgba(0, 212, 170, 0.4), 0 0 60px rgba(0, 212, 170, 0.15);

/* Overlay */
--overlay-bg: rgba(0, 0, 0, 0.6);

/* Pinned Badge Glow */
--pinned-badge-glow: drop-shadow(0 0 4px rgba(255, 255, 255, 0.4));
--pinned-badge-glow-hover: drop-shadow(0 0 6px rgba(255, 255, 255, 0.6));
```

### Colors (Light Theme)

Applied via `[data-theme="light"]` selector:

```css
/* Background - Clean twilight observatory */
--bg-base: #f8fafc;
--bg-elevated: #ffffff;
--starfield-gradient: linear-gradient(to bottom, #ffffff 0%, #f1f5f9 50%, #e2e8f0 100%);
--navbar-bg: rgba(255, 255, 255, 0.92);

/* Text */
--text-primary: #0f172a;
--text-secondary: #475569;
--text-muted: #64748b;

/* Accent (Deep indigo - twilight sky) */
--accent: #4f46e5;
--accent-hover: #4338ca;
--accent-light: #818cf8;
--accent-bg: rgba(79, 70, 229, 0.08);
--accent-border: rgba(79, 70, 229, 0.2);

/* Borders */
--border: #e2e8f0;
--border-focus: #4f46e5;
--star-empty: #cbd5e1;

/* Glass Card - Frosted panel surfaces */
--glass-bg: rgba(255, 255, 255, 0.7);
--glass-bg-hover: rgba(255, 255, 255, 0.9);
--glass-border: rgba(15, 23, 42, 0.08);
--glass-border-hover: rgba(15, 23, 42, 0.12);

/* Decorative - Twilight glow effects */
--glow-primary: rgba(79, 70, 229, 0.12);
--glow-secondary: rgba(99, 102, 241, 0.06);
--gradient-accent: linear-gradient(135deg, #818cf8 0%, #4f46e5 100%);
--shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
--shadow-accent: 0 4px 20px rgba(79, 70, 229, 0.2);
--shadow-accent-hover: 0 6px 28px rgba(79, 70, 229, 0.28);

/* Overlay */
--overlay-bg: rgba(15, 23, 42, 0.5);

/* Pinned Badge Glow - Darker for light mode */
--pinned-badge-glow: drop-shadow(0 0 4px rgba(0, 0, 0, 0.2));
--pinned-badge-glow-hover: drop-shadow(0 0 6px rgba(0, 0, 0, 0.3));
```

### Spacing

```css
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-20: 20px;
--space-lg: 24px;
--space-xl: 32px;
```

**Usage:**
```css
/* DO */
padding: var(--space-md);
gap: var(--space-sm);
margin-bottom: var(--space-lg);

/* DON'T */
padding: 16px;
gap: 8px;
margin-bottom: 24px;
```

### Typography

```css
/* Font Families */
--font-family: 'Karla', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;  /* Body text */
--font-display: 'Outfit', 'Montserrat', sans-serif;  /* Headings */
--font-technical: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;  /* Data displays */

/* Font Sizes */
--text-2xs: 10px;
--text-xs: 12px;
--text-label: 13px;    /* Form labels, small UI text */
--text-sm: 14px;
--text-base: 16px;
--text-lg: 18px;
--text-xl: 20px;
--text-2xl: 24px;
--text-3xl: 28px;
--text-4xl: 36px;

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;

/* Font Weights */
--font-medium: 500;
--font-semibold: 600;
```

### Border Radius

```css
--radius: 8px;
--radius-full: 9999px;

/* Common patterns */
border-radius: var(--radius);                    /* Default - 8px */
border-radius: calc(var(--radius) * 1.5);        /* 12px - cards */
border-radius: calc(var(--radius) * 2);          /* 16px - large cards */
border-radius: calc(var(--radius) / 2);          /* 4px - small elements */
border-radius: var(--radius-full);               /* Pills, circles */
```

### Transitions, Animation & Z-Index

```css
/* Transition Duration */
--transition: 0.15s;

/* Animation Duration (for fadeInUp, etc.) */
--animation-duration: 0.25s;

/* Z-Index Scale */
--z-navbar: 30;
--z-modal: 50;
```

### Layout

```css
--navbar-height: 72px;
--navbar-height-mobile: 64px;
--navbar-filters-height: 58px;
--container-max: 1000px;
```

### Badge Colors

```css
/* Tier Colors */
--tier-bronze: #cd7f32;
--tier-silver: #c0c0c0;
--tier-gold: #ffd700;
--tier-diamond: hsl(191, 100%, 86%);
--tier-elite: hsl(23, 100%, 50%);
--tier-purple: hsl(271, 91%, 65%);

/* Tier Glow Colors (for box-shadow) */
--tier-diamond-glow: hsla(191, 100%, 86%, 0.4);
--tier-elite-glow: hsla(23, 100%, 50%, 0.4);
--tier-purple-glow: hsla(271, 91%, 65%, 0.4);

/* Category Colors */
--category-exploration: #3b82f6;
--category-contribution: #10b981;
--category-quality: #f59e0b;
--category-review: #8b5cf6;
--category-community: #f97316;
--category-special: #ec4899;
--category-tenure: #a78bfa;

/* Category Background Colors */
--category-exploration-bg: rgba(59, 130, 246, 0.15);
--category-contribution-bg: rgba(16, 185, 129, 0.15);
--category-quality-bg: rgba(245, 158, 11, 0.15);
--category-review-bg: rgba(139, 92, 246, 0.15);
--category-community-bg: rgba(249, 115, 22, 0.15);
--category-special-bg: rgba(236, 72, 153, 0.15);
--category-tenure-bg: rgba(167, 139, 250, 0.15);
```

---

## Utility Classes

### Glass Card

Use for any card with the glass-morphism effect.

```jsx
// Standard glass card (static, no hover effect)
<div className="glass-card">
  {/* content */}
</div>

// Interactive (hover: bg change, border change, glow effect)
<div className="glass-card glass-card--interactive">
  {/* content */}
</div>
```

**What `.glass-card` provides:**
- `background: var(--glass-bg)`
- `border: 1px solid var(--glass-border)`
- `border-radius: var(--radius)` (8px)
- `backdrop-filter: blur(16px)`
- Subtle top gradient accent line (instrument panel aesthetic)

**What `.glass-card--interactive` adds:**
- `cursor: pointer`
- Hover: lighter background (`--glass-bg-hover`)
- Hover: accent border (`--accent-border`)
- Hover: cyan glow (`0 0 20px var(--glow-primary)`)
- Smooth transition (0.2s ease)

**When to use `--interactive`:**
- Clickable cards (stat cards, feature cards)
- Cards that navigate somewhere on click
- Cards with actions

**When NOT to use `--interactive`:**
- Container cards (profile header, settings panel)
- Tab containers
- Static content wrappers

### Auth Page Layout

Use for authentication pages (login, register, password reset, etc.).

```jsx
<div className="auth-page">
  <div className="auth-page__content">
    <div className="auth-page__card glass-card">
      {/* form content */}
    </div>
  </div>
</div>
```

**What `.auth-page` provides:**
- `display: flex` with column direction
- `min-height: calc(100lvh - var(--navbar-total-height))` (fills viewport below navbar)

**What `.auth-page__content` provides:**
- Flexbox centering (horizontal and vertical)
- Padding: `--space-xl` horizontal, `--space-lg` vertical

**What `.auth-page__card` provides:**
- `max-width: 420px` with `width: 100%`
- `padding: var(--space-xl)`
- `text-align: center` - all content centered by default
- `animation: fadeInUp var(--animation-duration) ease-out backwards` - entrance animation

**Note:** Combine `.auth-page__card` with `.glass-card` for the glass-morphism effect.

### Buttons

```jsx
// Primary action - Accent color with glow
<button className="btn-primary">Submit</button>
<button className="btn-primary btn-primary--full">Full Width</button>
<button className="btn-primary btn-primary--sm">Small</button>

// Secondary action - Transparent with border
<button className="btn-secondary">Cancel</button>
<button className="btn-secondary btn-secondary--icon">
  <i className="fa-solid fa-gear"></i>
</button>

// Danger action - Red with glow
<button className="btn-danger">Delete</button>
<button className="btn-danger btn-danger--sm">Small Delete</button>

// Social login buttons
<button className="btn-social btn-social--google">
  <i className="fa-brands fa-google btn-social__icon"></i>
</button>
<button className="btn-social btn-social--apple">
  <i className="fa-brands fa-apple btn-social__icon"></i>
</button>
<button className="btn-social btn-social--microsoft">
  <i className="fa-brands fa-microsoft btn-social__icon"></i>
</button>

// Icon only
<button className="btn-icon">
  <i className="fa-solid fa-gear"></i>
</button>
```

**Button specs:**
- `.btn-primary`: `padding: 16px 32px`, `font-size: 14px`, uppercase, accent background with glow
- `.btn-primary--sm`: `padding: 8px 20px`, `font-size: 13px`
- `.btn-secondary`: transparent background, glass border, hover shows glass-bg
- `.btn-secondary--icon`: square aspect ratio with `--space-sm` padding
- `.btn-danger`: error color background with red glow
- `.btn-danger--sm`: `padding: 8px 20px`, `font-size: 13px`
- `.btn-social`: `flex: 1`, glass background, 12px padding
- `.btn-icon`: 32x32px, transparent background, glass border

### Forms

```jsx
<div className="form-group">
  <label className="form-label">Email</label>
  <input
    type="email"
    className="form-input"
    placeholder="you@example.com"
  />
</div>

<div className="form-group">
  <label className="form-label">Message</label>
  <textarea className="form-textarea" />
</div>

// With validation hints
<div className="form-hints">
  <span className="form-hint form-hint--valid">
    <i className="fa-solid fa-check"></i> 8+ characters
  </span>
  <span className="form-hint form-hint--error">
    <i className="fa-solid fa-xmark"></i> Needs uppercase
  </span>
  <span className="form-hint form-hint--info">
    <i className="fa-solid fa-info"></i> Optional
  </span>
</div>

// Checkbox
<label className="form-checkbox">
  <input type="checkbox" />
  <span className="form-checkbox-label">Remember me</span>
</label>
```

**Form specs:**
- `.form-label`: `font-family: --font-technical`, `font-size: 11px`, uppercase, `--text-muted`
- `.form-input`: `padding: 12px 16px`, `font-size: 15px`, glass background
- `.form-input:focus`: accent border with glow ring
- `.form-input.error`: error border color
- `.form-textarea`: same as input, `min-height: 120px`, no resize
- `.form-hint`: `font-size: --text-xs`, icons colored by state (success/error/info), text stays muted
- `.form-checkbox`: 16x16px custom checkbox with accent fill when checked

### Empty State

```jsx
<div className="empty-state">
  <i className="fa-solid fa-star empty-state__icon"></i>
  <p className="empty-state__title">No favorites yet</p>
  <p className="empty-state__description">
    Start exploring and save your favorite spots
  </p>
</div>
```

**Empty state specs:**
- `.empty-state`: centered, `padding: 64px` (2x --space-xl)
- `.empty-state__icon`: `font-size: 48px`, muted color, 50% opacity
- `.empty-state__title`: `--text-secondary`
- `.empty-state__description`: `--text-sm`, `--text-muted`

### Password Toggle

```jsx
<div className="password-input-wrapper" style={{ position: 'relative' }}>
  <input
    type={showPassword ? 'text' : 'password'}
    className="form-input has-toggle"
  />
  <button
    type="button"
    className="password-toggle"
    onClick={() => setShowPassword(!showPassword)}
  >
    <i className={`fa-solid fa-eye${showPassword ? '-slash' : ''}`}></i>
  </button>
</div>
```

**Password toggle specs:**
- `.password-toggle`: absolute positioned, `right: 4px`, 36x36px, centered icon
- Hover: `--text-secondary` color

### Section Divider

```jsx
<div className="section-divider">
  <div className="section-divider__line"></div>
  <span className="section-divider__text">or</span>
  <div className="section-divider__line"></div>
</div>
```

**Section divider specs:**
- `.section-divider`: flex with gap, `margin: --space-lg 0`
- `.section-divider__line`: 1px glass border color
- `.section-divider__text`: `--text-xs`, muted, lowercase

### Section Accent

Subtle accent subtitle for section headers with observatory "coordinate readout" aesthetic.

```jsx
// Left-aligned (default)
<span className="section-accent">Explore</span>

// Centered variant
<span className="section-accent section-accent--centered">Featured</span>

// Light variant (for accent backgrounds)
<span className="section-accent section-accent--light">Discover</span>
```

**Section accent specs:**
- `.section-accent`: inline-flex, technical font, `--text-2xs`, uppercase, 0.2em letter-spacing
- Gradient line before text (24px wide, cyan glow)
- `.section-accent--centered`: removes left line, adds right line instead
- `.section-accent--light`: white text for use on accent-colored backgrounds

### Typography Utilities

```jsx
// Font families
<span className="font-technical">DATA-2024</span>
<h2 className="font-display">Starview</h2>

// Text styles
<span className="text-body">Regular body text</span>
<span className="text-small">Smaller secondary text</span>
<span className="text-muted">Muted hint text</span>

// Accent text
<span className="text-accent">Highlighted text</span>
<span className="text-accent-glow">Glowing accent text</span>
<span className="text-gradient">Gradient text</span>
```

**Typography utility specs:**
- `.font-technical`: JetBrains Mono with 0.02em letter-spacing
- `.font-display`: Outfit/Montserrat with -0.01em letter-spacing
- `.text-body`: base font, 16px, normal line-height
- `.text-small`: 14px, secondary color
- `.text-muted`: muted color
- `.text-accent`: accent color
- `.text-accent-glow`: accent with text-shadow glow
- `.text-gradient`: gradient background clipped to text

### Data Display

```jsx
// Technical data readout (for stats, numbers)
<div className="data-readout">42.7</div>
<div className="data-label">BORTLE INDEX</div>

// Status indicator dot
<span className="status-indicator"></span>
<span className="status-indicator status-indicator--success"></span>
<span className="status-indicator status-indicator--warning"></span>
<span className="status-indicator status-indicator--error"></span>
```

**Data display specs:**
- `.data-readout`: `--font-technical`, `--text-2xl`, `--font-semibold`, accent color
- `.data-label`: `--font-technical`, `--text-xs`, uppercase, 0.1em letter-spacing, muted
- `.status-indicator`: 8x8px circle with glow, accent color by default
- Variants: `--success`, `--warning`, `--error` with matching glow colors

### Glow Effects

```jsx
// Apply accent glow to any element
<div className="glass-card glow">Glowing card</div>
<div className="glass-card glow-hover">Glow on hover</div>
```

---

## Animations

### Fade In Up

Elements fade in while sliding up 20px:

```jsx
// Single element
<div className="animate-fade-in-up">Content</div>

// Staggered entrance (e.g., auth page cards)
<div className="animate-fade-in-up animate-delay-1">First</div>
<div className="animate-fade-in-up animate-delay-2">Second</div>
<div className="animate-fade-in-up animate-delay-3">Third</div>
<div className="animate-fade-in-up animate-delay-4">Fourth</div>
```

| Class | Effect |
|-------|--------|
| `.animate-fade-in-up` | Fade in + 20px upward motion (uses `--animation-duration`, default 0.25s) |
| `.animate-delay-1` | 0.1s delay |
| `.animate-delay-2` | 0.2s delay |
| `.animate-delay-3` | 0.3s delay |
| `.animate-delay-4` | 0.4s delay |

### Spin

Infinite rotation for loading spinners:

```jsx
<i className="fa-solid fa-spinner animate-spin"></i>
```

| Class | Effect |
|-------|--------|
| `.animate-spin` | 360-degree rotation (1s linear infinite) |

### Pulse

Subtle opacity pulse for status indicators:

```jsx
<div className="status-indicator animate-pulse"></div>
```

| Class | Effect |
|-------|--------|
| `.animate-pulse` | Opacity 1 to 0.5 (2s ease-in-out infinite) |

### Accessibility

All animations are automatically disabled when the user has `prefers-reduced-motion: reduce` enabled in their system settings.

### Staggered Card Animation

LocationCard uses CSS custom properties for staggered entrance:

```css
/* In component CSS */
.location-card {
  animation: fadeInUp 0.5s ease-out backwards;
  animation-delay: calc(var(--card-index, 0) * 0.08s);
}

/* Set via inline style */
<article style={{ '--card-index': index }}>
```

### Dropdown Fade Animation

For dropdowns with close animation timing:

```css
.dropdown {
  --dropdown-animation-duration: 0.1s;
  animation: dropdownFadeIn var(--dropdown-animation-duration) ease-out forwards;
}

.dropdown--closing {
  animation: dropdownFadeOut var(--dropdown-animation-duration) ease-out forwards;
}

@keyframes dropdownFadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes dropdownFadeOut { from { opacity: 1; } to { opacity: 0; } }
```

Use with `useAnimatedDropdown` hook for coordinated close timing.

### WebView Browser & Viewport Height

WebView browsers (Google Search app, Instagram, Facebook, TikTok in-app browsers) have buggy viewport unit implementations where `svh` behaves like `dvh`, causing layout shifts when browser UI shows/hides during scroll.

**Detection:** In `index.html`, we detect WebView browsers via user agent and add `.webview-browser` class to `<html>`:
```javascript
var isWebView = /GSA\/|FBAN|FBAV|Instagram|TikTok|\bwv\b|WebView/i.test(ua);
```

**The Problem:**
- `vh` - Fixed to initial viewport, can be taller than visible area on mobile
- `svh` - Should be stable (smallest viewport), but **broken in in-app browsers** where it acts like `dvh`
- `dvh` - Dynamic, updates with browser UI changes → causes layout shifts
- `lvh` - Largest viewport, may cut off content when UI shows

**Our Solution:**
1. Use plain `vh` globally (not `dvh`/`svh`/`lvh`) for stable viewport height
2. Set `--actual-vh` CSS variable once on page load using `window.innerHeight`
3. Only update `--actual-vh` on `orientationchange`, NOT on `resize` (browser UI changes trigger resize events)

```javascript
// From index.html - set once, update only on orientation change
var setViewportHeight = function() {
  document.documentElement.style.setProperty('--actual-vh', window.innerHeight + 'px');
};
setViewportHeight();

window.addEventListener('orientationchange', function() {
  setTimeout(setViewportHeight, 100); // Delay for browser to settle
});
```

**Usage in CSS:**
```css
/* For pages needing accurate viewport height in WebViews */
html.webview-browser .my-fullscreen-section {
  min-height: var(--actual-vh, 100vh);
}

/* Or use static padding as fallback */
html.webview-browser .hero-section {
  min-height: auto;
  padding-top: 80px;
  padding-bottom: 80px;
}
```

**Tradeoff:** Setting viewport height once means if page loads with browser UI visible and user scrolls (UI hides), there may be extra space at bottom. This is acceptable to prevent jarring layout shifts.

**References:**
- [Solving SVH Viewport Issues in Mobile In-App Browsers](https://medium.com/@python-javascript-php-html-css/solving-svh-viewport-issues-in-mobile-in-app-browsers-8808cb4faa3f)
- [web.dev: The large, small, and dynamic viewport units](https://web.dev/blog/viewport-units)

---

## Component Patterns

### Creating a New Component

1. Create folder: `components/{category}/ComponentName/`
2. Create files: `index.jsx` + `styles.css`
3. Import styles in component: `import './styles.css';`

```jsx
// ComponentName/index.jsx
import './styles.css';

function ComponentName({ children }) {
  return (
    <div className="component-name glass-card">
      {children}
    </div>
  );
}

export default ComponentName;
```

```css
/* ComponentName/styles.css */
.component-name {
  padding: var(--space-lg);
  /* Additional styles specific to this component */
}
```

### DO and DON'T

```css
/* DO: Use CSS variables */
.my-component {
  padding: var(--space-md);
  color: var(--text-secondary);
  border-radius: var(--radius);
  gap: var(--space-sm);
}

/* DON'T: Hardcode values */
.my-component {
  padding: 16px;
  color: #d1d5db;
  border-radius: 8px;
  gap: 8px;
}
```

```css
/* DO: Use utility classes */
<div className="glass-card">

/* DON'T: Recreate glass card styling */
.my-card {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: calc(var(--radius) * 2);
  backdrop-filter: blur(12px);
}
```

```css
/* DO: Use existing button classes */
<button className="btn-primary">Submit</button>

/* DON'T: Create custom button styling */
.my-button {
  background: var(--accent);
  padding: var(--space-md) var(--space-xl);
  /* ... recreating btn-primary ... */
}
```

---

## Responsive Breakpoints

```css
/* Mobile first approach */
@media (max-width: 480px) {
  /* Small mobile */
}

@media (max-width: 767px) {
  /* Mobile */
}

@media (max-width: 768px) {
  /* Mobile/tablet boundary */
}

@media (min-width: 640px) {
  /* Small tablet and up */
}

@media (min-width: 768px) {
  /* Tablet and up */
}

@media (min-width: 1024px) {
  /* Desktop */
}
```

**Key responsive variables:**
```css
--navbar-height: 72px;
--navbar-height-mobile: 64px;
--navbar-filters-height: 58px;
--container-max: 1000px;
```

---

## Layout Classes

### Page Wrapper

```jsx
<div className="page-wrapper">
  <main className="main-content">
    <div className="page-container">
      {/* Page content */}
    </div>
  </main>
</div>
```

**Layout specs:**
- `.page-wrapper`: accounts for navbar height, fills viewport
- `.main-content`: flex-grow to fill available space
- `.page-container`: max-width 1000px, centered, responsive padding

---

## Theme Support

All colors use CSS variables that automatically adapt to light/dark mode via `[data-theme="light"]` selector.

When adding new colors:
1. Define in `:root` for dark theme (default)
2. Override in `[data-theme="light"]` for light theme

```css
:root {
  --my-color: #blue-for-dark;
}

[data-theme="light"] {
  --my-color: #blue-for-light;
}
```

---

## Checklist: Before Creating New Styles

1. Can I use an existing utility class? (`.glass-card`, `.btn-primary`, etc.)
2. Am I using CSS variables for all colors, spacing, and typography?
3. Does my component support both dark and light themes?
4. Is the component folder structure correct? (`ComponentName/index.jsx` + `styles.css`)
5. Have I checked `global.css` for existing patterns I can reuse?
