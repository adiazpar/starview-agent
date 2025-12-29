# Starview Frontend Style Guide

**Last Updated:** 2025-12-29
**Design System:** Linear-inspired glass-morphism
**Source of Truth:** `starview_frontend/src/styles/global.css`

---

## Quick Reference: What to Use

| Need | Use This |
|------|----------|
| Card with blur effect | `.glass-card` |
| Auth page layout | `.auth-page`, `.auth-page__content`, `.auth-page__card` |
| Primary button | `.btn-primary` |
| Secondary button | `.btn-secondary` |
| Icon-only button | `.btn-icon` |
| Form input | `.form-input` |
| Form group | `.form-group` + `.form-label` |
| Empty state | `.empty-state`, `.empty-state__icon`, `.empty-state__title` |
| Password toggle | `.password-toggle` |
| Loading spinner | `<LoadingSpinner />` component |

---

## Design Tokens

### Colors

```css
/* Background */
--bg-base: #111827;              /* Main background */
--glass-bg: rgba(255,255,255,0.02);      /* Card backgrounds */
--glass-bg-hover: rgba(255,255,255,0.04);

/* Text */
--text-primary: #f9fafb;         /* Main text */
--text-secondary: #d1d5db;       /* Secondary text */
--text-muted: #9ca3af;           /* Muted/hint text */

/* Accent (Blue in dark mode, Orange in light) */
--accent: #2563eb;
--accent-hover: #3b82f6;
--accent-light: #60a5fa;
--accent-border: rgba(37, 99, 235, 0.2);

/* Status */
--success: #22c55e;
--warning: #eab308;
--error: #ef4444;
--info: #0ea5e9;

/* Borders */
--border: #2f353e;
--glass-border: rgba(255,255,255,0.06);
--glass-border-hover: rgba(255,255,255,0.1);
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
--text-xs: 12px;
--text-label: 13px;    /* Form labels, small UI text */
--text-sm: 14px;
--text-base: 16px;
--text-lg: 18px;
--text-xl: 20px;
--text-2xl: 24px;
--text-3xl: 28px;
--text-4xl: 36px;

--font-family: 'Karla', sans-serif;      /* Body text */
--font-display: 'Montserrat', sans-serif; /* Headings */
```

### Border Radius

```css
--radius: 8px;
--radius-full: 9999px;

/* Common patterns */
border-radius: var(--radius);                    /* Default */
border-radius: calc(var(--radius) * 1.5);        /* 12px - cards */
border-radius: calc(var(--radius) * 2);          /* 16px - large cards */
border-radius: calc(var(--radius) / 2);          /* 4px - small elements */
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

/* Category Colors */
--category-exploration: #3b82f6;
--category-contribution: #10b981;
--category-quality: #f59e0b;
--category-review: #8b5cf6;
--category-community: #f97316;
--category-special: #ec4899;
--category-tenure: #a78bfa;
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

// Interactive (hover: bg change, border change, -2px lift)
<div className="glass-card glass-card--interactive">
  {/* content */}
</div>
```

**What `.glass-card` provides:**
- `background: var(--glass-bg)`
- `border: 1px solid var(--glass-border)`
- `border-radius: calc(var(--radius) * 2)` (16px)
- `backdrop-filter: blur(12px)`

**What `.glass-card--interactive` adds:**
- Hover: lighter background (`--glass-bg-hover`)
- Hover: lighter border (`--glass-border-hover`)
- Hover: `-2px` lift (`translateY(-2px)`)
- Smooth transition

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
- `min-height: calc(100lvh - var(--navbar-height))` (fills viewport below navbar)
- Mobile: uses `--navbar-height-mobile`

**What `.auth-page__content` provides:**
- Flexbox centering (horizontal and vertical)
- Padding: `--space-xl` on desktop, `--space-lg` on mobile

**What `.auth-page__card` provides:**
- `max-width: 420px` with `width: 100%`
- `padding: var(--space-xl)`
- `text-align: center` - all content centered by default
- `animation: fadeInUp 0.4s ease-out backwards` - entrance animation

**Note:** Combine `.auth-page__card` with `.glass-card` for the glass-morphism effect.

### Buttons

```jsx
// Primary action
<button className="btn-primary">Submit</button>
<button className="btn-primary btn-primary--full">Full Width</button>
<button className="btn-primary btn-primary--sm">Small</button>

// Secondary action
<button className="btn-secondary">Cancel</button>

// Icon only
<button className="btn-icon">
  <i className="fa-solid fa-gear"></i>
</button>
```

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
</div>
```

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

### Section Divider

```jsx
<div className="section-divider">
  <div className="section-divider__line"></div>
  <span className="section-divider__text">or</span>
  <div className="section-divider__line"></div>
</div>
```

### Animations

Utility classes for entrance animations and loading states.

**Fade In Up** - Elements fade in while sliding up 20px:

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
| `.animate-fade-in-up` | Fade in + 20px upward motion (0.6s ease-out) |
| `.animate-delay-1` | 0.1s delay |
| `.animate-delay-2` | 0.2s delay |
| `.animate-delay-3` | 0.3s delay |
| `.animate-delay-4` | 0.4s delay |

**Spin** - Infinite rotation for loading spinners:

```jsx
<i className="fa-solid fa-spinner animate-spin"></i>
```

| Class | Effect |
|-------|--------|
| `.animate-spin` | 360-degree rotation (1s linear infinite) |

**Accessibility:** All animations are automatically disabled when the user has `prefers-reduced-motion: reduce` enabled in their system settings.

**Staggered Card Animation** - LocationCard uses CSS custom properties for staggered entrance:

```css
/* In component CSS */
.location-card {
  animation: fadeInUp 0.5s ease-out backwards;
  animation-delay: calc(var(--card-index, 0) * 0.08s);
}

/* Set via inline style */
<article style={{ '--card-index': index }}>
```

**Dropdown Fade Animation** - For dropdowns with close animation timing:

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
@media (max-width: 767px) {
  /* Mobile styles */
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
--container-max: 1000px;
```

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
