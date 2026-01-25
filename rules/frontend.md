---
paths:
  - "**/starview_frontend/**/*.js"
  - "**/starview_frontend/**/*.jsx"
  - "**/starview_frontend/**/*.ts"
  - "**/starview_frontend/**/*.tsx"
  - "**/starview_frontend/**/*.css"
---

# Frontend Development Rules

## Development Server

- Vite dev server runs at `http://localhost:5173`
- Do NOT start the dev server - it's always running in a separate terminal
- Use Chrome DevTools MCP for browser automation

## React Patterns

### Components
- Functional components with hooks (no class components)
- Keep components focused - extract when >150 lines
- Use shared components from `components/shared/`

### State Management
- React Query for server state (`@tanstack/react-query`)
- React Context for global UI state
- Local state (`useState`) for component-specific state

### Data Fetching
- Services in `services/` directory handle API calls
- Custom hooks in `hooks/` wrap React Query
- Pattern: `useFeatureData.js` → `featureApi.js` → backend

## Styling

- Follow `.claude/frontend/STYLE_GUIDE.md` for design system
- CSS modules or global styles in `styles/`
- Use existing CSS variables for colors, spacing, typography

## File Organization

```
src/
├── components/     # Reusable UI components
│   └── shared/     # Cross-cutting components (LoadingSpinner, Alert)
├── pages/          # Route components
├── hooks/          # Custom React hooks
├── services/       # API service functions
├── styles/         # Global styles and CSS variables
└── utils/          # Helper functions
```

## Chrome DevTools MCP

- Always use `take_snapshot()` first to get element `uid` values
- Use `uid` values (NOT CSS selectors) for interactions
- Navigate to `http://localhost:5173` for local development
