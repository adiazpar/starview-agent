# MCP Servers for Frontend Development

**Last Updated:** 2025-11-27

This document describes how to use the configured MCP servers for visual frontend development on Starview.

**Quick Start:** See [Quick Reference](#quick-reference-cheat-sheet) at the bottom for common commands.

---

## Overview

Three MCP servers available for visual development:

| Server | Package | Purpose |
|--------|---------|---------|
| **chrome-devtools** | `chrome-devtools-mcp` | DevTools integration (console, network, performance) |
| **puppeteer** | `@modelcontextprotocol/server-puppeteer` | Browser automation with incognito mode |
| **figma** | Figma MCP Server | Design-to-code workflow, design tokens |

---

## Configuration

**File:** `.mcp.json` (gitignored - local machine config)

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {
        "PUPPETEER_LAUNCH_OPTIONS": "{\"headless\":false,\"args\":[\"--incognito\",\"--disable-cache\",\"--disk-cache-size=0\"]}"
      }
    },
    "chrome-devtools": {
      "command": "npx",
      "args": ["-y", "chrome-devtools-mcp@latest", "--isolated"]
    }
  }
}
```

**Key Settings:**
- `headless: false` - Browser window is visible
- `--incognito` - Fresh session without cached data
- `--disable-cache` - No disk caching
- `--isolated` - Chrome DevTools uses temporary profile

---

## Prerequisites

1. **Node.js v20.19+** (current: v23.11.0)
2. **Chrome browser** (stable channel)
3. **Vite dev server running** at `http://localhost:5173`
4. **Django backend running** at `http://127.0.0.1:8000`

**Start the frontend:**
```bash
cd starview_frontend && npm run dev
```

---

## Chrome DevTools MCP Tools

### Navigation (6 tools)

| Tool | Description | Example |
|------|-------------|---------|
| `new_page` | Open new browser tab | `new_page(url="http://localhost:5173")` |
| `navigate_page` | Go to URL | `navigate_page(type="url", url="http://localhost:5173")` |
| `close_page` | Close tab by index | `close_page(pageIdx=0)` |
| `list_pages` | List all open tabs | `list_pages()` |
| `select_page` | Switch to tab by index | `select_page(pageIdx=0)` |
| `wait_for` | Wait for text to appear | `wait_for(text="Dashboard")` |

### Input/Interaction (8 tools)

| Tool | Description | Example |
|------|-------------|---------|
| `click` | Click element by uid | `click(uid="123")` |
| `fill` | Fill single input by uid | `fill(uid="456", value="test@test.com")` |
| `fill_form` | Fill multiple fields | `fill_form(elements=[{uid: "123", value: "test"}])` |
| `hover` | Hover over element by uid | `hover(uid="789")` |
| `drag` | Drag and drop by uid | `drag(from_uid="123", to_uid="456")` |
| `press_key` | Keyboard input | `press_key(key="Enter")` |
| `upload_file` | Upload file by uid | `upload_file(uid="123", filePath="/path/to/file")` |
| `handle_dialog` | Accept/dismiss alerts | `handle_dialog(action="accept")` |

### Debugging (5 tools)

| Tool | Description | Example |
|------|-------------|---------|
| `take_screenshot` | Capture visible page or element | `take_screenshot()` or `take_screenshot(uid="123")` |
| `take_snapshot` | Capture a11y tree structure | `take_snapshot()` or `take_snapshot(verbose=true)` |
| `list_console_messages` | Get all console logs | `list_console_messages()` |
| `get_console_message` | Get specific log by msgid | `get_console_message(msgid=0)` |
| `evaluate_script` | Run JavaScript function | `evaluate_script(function="() => document.title")` |

### Network (2 tools)

| Tool | Description | Example |
|------|-------------|---------|
| `list_network_requests` | List all requests with filtering | `list_network_requests()` or `list_network_requests(resourceTypes=["fetch", "xhr"])` |
| `get_network_request` | Get request details by reqid | `get_network_request(reqid=0)` or `get_network_request()` for selected |

### Performance (3 tools)

| Tool | Description | Example |
|------|-------------|---------|
| `performance_start_trace` | Begin recording with options | `performance_start_trace(reload=true, autoStop=false)` |
| `performance_stop_trace` | Stop recording | `performance_stop_trace()` |
| `performance_analyze_insight` | Get specific insight details | `performance_analyze_insight(insightSetId="...", insightName="LCPBreakdown")` |

### Emulation (2 tools)

| Tool | Description | Example |
|------|-------------|---------|
| `emulate` | Emulate network/CPU throttling | `emulate(networkConditions="Slow 3G")` or `emulate(cpuThrottlingRate=4)` |
| `resize_page` | Change viewport size | `resize_page(width=375, height=812)` |

---

## Puppeteer MCP Tools

| Tool | Description | Example |
|------|-------------|---------|
| `puppeteer_navigate` | Navigate to URL | `puppeteer_navigate(url="http://localhost:5173")` |
| `puppeteer_screenshot` | Take screenshot | `puppeteer_screenshot(name="homepage", width=1280, height=720)` |
| `puppeteer_click` | Click element by selector | `puppeteer_click(selector="button.login-btn")` |
| `puppeteer_fill` | Fill input field by selector | `puppeteer_fill(selector="#email", value="test@test.com")` |
| `puppeteer_select` | Select dropdown option | `puppeteer_select(selector="select#country", value="US")` |
| `puppeteer_hover` | Hover over element | `puppeteer_hover(selector=".menu-item")` |
| `puppeteer_evaluate` | Run JavaScript | `puppeteer_evaluate(script="document.title")` |

**Note:** Puppeteer uses **CSS selectors** while Chrome DevTools uses **`uid` values** from a11y tree.

---

## Chrome DevTools vs Puppeteer: Which to Use?

| Use Case | Recommended Server | Reason |
|----------|-------------------|--------|
| Visual verification | **Chrome DevTools** | Better screenshot quality, a11y tree snapshots |
| Console/Network debugging | **Chrome DevTools** | Access to DevTools panels, performance insights |
| Form testing (known selectors) | **Puppeteer** | Simpler with CSS selectors |
| Element interaction (unknown selectors) | **Chrome DevTools** | Use `take_snapshot()` to discover elements |
| Performance analysis | **Chrome DevTools** | Performance panel integration |
| Quick prototyping | **Puppeteer** | Faster with familiar CSS selectors |
| Accessibility testing | **Chrome DevTools** | Built on a11y tree |
| Multiple tabs/windows | **Chrome DevTools** | Better tab management |

**Recommendation:** Start with **Chrome DevTools** for comprehensive debugging. Use **Puppeteer** if you already know CSS selectors and want faster interactions.

---

## Important: Element Selection with `uid`

**Chrome DevTools MCP uses accessibility tree `uid` values, NOT CSS selectors.**

### How to Get `uid` Values

```
1. new_page(url="http://localhost:5173/login")
2. take_snapshot()  # Returns a11y tree with uid values
```

**Example snapshot output:**
```
<button uid="123">Login</button>
<textbox uid="456" name="Email"></textbox>
<textbox uid="789" name="Password"></textbox>
```

### Using `uid` Values

```
3. fill(uid="456", value="test@test.com")  # Fill email
4. fill(uid="789", value="password123")     # Fill password
5. click(uid="123")                         # Click login button
```

**Key Points:**
- `take_snapshot()` always returns the latest state with current `uid` values
- `uid` values can change when the DOM re-renders
- Use `take_snapshot(verbose=true)` for more detailed element information
- Puppeteer MCP uses CSS selectors instead of `uid` values

---

## Common Workflows

### 1. Visual Verification Before/After Changes

```
# Before editing CSS/JSX:
1. new_page(url="http://localhost:5173/profile")
2. take_screenshot()
3. list_console_messages()  # Check for errors

# After editing:
4. [Make code changes - Vite will auto-reload]
5. take_screenshot()  # Compare visually
6. list_console_messages()  # Check for new errors
```

**Note:** Use `take_snapshot()` first to get element `uid` values for interaction.

### 2. Debug API Issues

```
1. new_page(url="http://localhost:5173/login")
2. take_snapshot()  # Get uid values for form fields
3. fill(uid="<email-input-uid>", value="test@test.com")
4. fill(uid="<password-input-uid>", value="password123")
5. click(uid="<submit-button-uid>")
6. wait_for(text="Dashboard")  # or timeout
7. list_network_requests(resourceTypes=["fetch", "xhr"])  # See API calls to Django
8. get_network_request(reqid=X)  # Inspect failed request details
```

**Note:** API calls go to `http://127.0.0.1:8000/api/` - check network tab for 401/403/500 errors.

### 3. Test Responsive Design

```
1. new_page(url="http://localhost:5173")
2. take_screenshot()  # Desktop view (default 1280x720)

3. resize_page(width=375, height=812)  # iPhone 13 size
4. take_screenshot()  # Mobile view

5. resize_page(width=768, height=1024)  # iPad size
6. take_screenshot()  # Tablet view

7. resize_page(width=1920, height=1080)  # Full HD
8. take_screenshot()  # Large desktop
```

**Common Viewport Sizes:**
- Mobile: 375x812 (iPhone), 360x800 (Android)
- Tablet: 768x1024 (iPad), 1024x768 (iPad Landscape)
- Desktop: 1280x720, 1920x1080, 2560x1440

### 4. Performance Analysis

```
1. new_page(url="http://localhost:5173")
2. performance_start_trace(reload=true, autoStop=true)
   # Automatically records page load and stops
3. [Review insight sets returned - note the insightSetId]
4. performance_analyze_insight(insightSetId="<id>", insightName="LCPBreakdown")
   # Get detailed LCP (Largest Contentful Paint) metrics
5. performance_analyze_insight(insightSetId="<id>", insightName="DocumentLatency")
   # Get timing breakdown
```

**Common Insight Names:**
- `LCPBreakdown` - Largest Contentful Paint analysis
- `DocumentLatency` - Document load timing
- `RenderBlocking` - Render-blocking resources
- `SlowCSSSelector` - Expensive CSS selectors

### 5. Form Testing

```
1. new_page(url="http://localhost:5173/register")
2. take_snapshot()  # Get uid values for all form fields
3. fill_form(elements=[
     {uid: "<username-uid>", value: "testuser"},
     {uid: "<email-uid>", value: "test@example.com"},
     {uid: "<password-uid>", value: "SecurePass123!"}
   ])
4. click(uid="<submit-button-uid>")
5. wait_for(text="Registration successful")  # or error message
6. list_console_messages()  # Check for validation errors
7. take_screenshot()  # See result
```

**Note:** Use `take_snapshot()` to get the a11y tree with all `uid` values for elements.

---

## Starview-Specific URLs

| Page | URL | Purpose |
|------|-----|---------|
| Home | `http://localhost:5173/` | Landing page |
| Login | `http://localhost:5173/login` | Authentication |
| Register | `http://localhost:5173/register` | New user signup |
| Verify Email | `http://localhost:5173/verify-email` | Email verification prompt |
| Email Verified | `http://localhost:5173/email-verified` | Confirmation page |
| Password Reset | `http://localhost:5173/password-reset` | Request password reset |
| Profile | `http://localhost:5173/profile` | User settings (protected) |
| Public Profile | `http://localhost:5173/users/:username` | View user profile |
| Not Found | `http://localhost:5173/*` | 404 page |

**Backend API Base:** `http://127.0.0.1:8000/api/`

**Key API Endpoints:**
- `/api/health/` - Health check
- `/api/auth/login/` - Login
- `/api/auth/register/` - Register
- `/api/auth/logout/` - Logout
- `/api/auth/user/` - Current user info

---

## Troubleshooting

### Browser doesn't open
- Check Node.js version: `node --version` (need v20.19+)
- Check Chrome is installed
- Restart Claude Code to reload MCP servers
- Check `.mcp.json` configuration is valid

### Console shows CORS errors
- Ensure Django backend is running: `http://127.0.0.1:8000/api/health/`
- Check `CORS_ALLOWED_ORIGINS` in `.env` includes `http://localhost:5173`
- Verify Vite dev server is running on port 5173

### Screenshots are blank
- Wait for page to load: `wait_for(text="<visible-text>")`
- Check if there are JavaScript errors: `list_console_messages()`
- Increase timeout: `wait_for(text="...", timeout=5000)`

### Network requests not showing
- Call `list_network_requests()` after page actions complete
- Some requests may be cached - incognito mode is already configured
- Use `list_network_requests(resourceTypes=["fetch", "xhr"])` to filter

### Element not found / `uid` errors
- Always call `take_snapshot()` before interacting with elements
- `uid` values change when DOM re-renders - get fresh snapshot
- Use `take_snapshot(verbose=true)` to see more element details
- Check element is visible and not in a shadow DOM

### Figma authentication fails
- Run `mcp__figma__whoami()` to check authentication status
- Re-authenticate using `/mcp` command → Select `figma` → Authenticate
- Ensure you're logged into Figma in your browser

---

## Best Practices

1. **Always take a snapshot first** - Get `uid` values before any interaction
2. **Screenshot before and after** - Visual verification of UI changes
3. **Check console after navigation** - Catch JavaScript errors early
4. **Use `wait_for(text="...")` after clicks** - Ensure navigation/render completes
5. **Test mobile viewports** - Verify responsive design (375x812, 768x1024)
6. **Filter network requests** - Use `resourceTypes=["fetch", "xhr"]` for API calls only
7. **Isolated mode is automatic** - Incognito/temporary profile prevents cache issues
8. **Take verbose snapshots for debugging** - `take_snapshot(verbose=true)` shows more details
9. **Verify backend is running** - Check `http://127.0.0.1:8000/api/health/` first
10. **Use Puppeteer for CSS selectors** - If you prefer selectors over `uid` values

---

## Figma MCP Server

### Configuration (CONFIRMED WORKING)

**Remote Server:** Using HTTPS endpoint (no desktop app required)

**Configuration in `.mcp.json`:**
```json
{
  "mcpServers": {
    "figma": {
      "type": "http",
      "url": "https://mcp.figma.com/mcp"
    }
  }
}
```

### Authentication

**Setup Steps:**
1. Type `/mcp` inside Claude Code
2. Select `figma` from the list
3. Select "Authenticate"
4. Browser opens for Figma OAuth login
5. Click "Allow Access"
6. Returns "Authentication successful. Connected to figma"

**Verify Connection:**
```
mcp__figma__whoami()
```

---

### Available Figma MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `mcp__figma__get_design_context` | Get design code and metadata from node | `fileKey`, `nodeId`, `clientLanguages`, `clientFrameworks` |
| `mcp__figma__get_screenshot` | Get screenshot of a Figma node | `fileKey`, `nodeId` |
| `mcp__figma__get_metadata` | Get node metadata in XML format | `fileKey`, `nodeId` |
| `mcp__figma__get_variable_defs` | Get variable definitions (colors, spacing, etc.) | `fileKey`, `nodeId` |
| `mcp__figma__get_code_connect_map` | Get Code Connect mappings | `fileKey`, `nodeId`, `codeConnectLabel` |
| `mcp__figma__get_figjam` | Get FigJam board content | `fileKey`, `nodeId` |
| `mcp__figma__create_design_system_rules` | Generate design system rules | `nodeId` |
| `mcp__figma__whoami` | Check authenticated user | None |

---

### Using Figma URLs

**URL Format:**
```
https://figma.com/design/:fileKey/:fileName?node-id=:nodeId
```

**Extracting Parameters:**
- `fileKey` - Example: `VxMJeyp9P35Alv5e2O1JQC`
- `nodeId` - Convert `-` to `:` (e.g., `8-2` becomes `8:2`)

**Example:**
```
URL: https://figma.com/design/VxMJeyp9P35Alv5e2O1JQC/Linear-Design-System?node-id=8-2

Extract:
  fileKey = "VxMJeyp9P35Alv5e2O1JQC"
  nodeId = "8:2"
```

---

### Workflows for Starview

| Workflow | Description | Tool |
|----------|-------------|------|
| **Design Token Extraction** | Pull colors, typography, spacing from Linear system | `get_variable_defs` |
| **Component Code Generation** | Generate React/HTML/CSS from Figma frames | `get_design_context` |
| **Visual Comparison** | Screenshot Figma designs vs implemented components | `get_screenshot` |
| **Design System Rules** | Generate CSS custom properties from design tokens | `create_design_system_rules` |

---

### Linear Design System Reference

**URL:** https://www.figma.com/design/VxMJeyp9P35Alv5e2O1JQC/Linear-Design-System--Community-

**File Key:** `VxMJeyp9P35Alv5e2O1JQC`

**Use Cases:**
1. Extract design tokens for CSS custom properties
2. Generate component code that matches Linear's aesthetic
3. Compare Starview components against Linear patterns
4. Prototype new features using Linear's design language

**Note:** This is design inspiration for Starview's UI overhaul. FontAwesome Free icons only (fa-solid, fa-regular, fa-brands).

---

## Quick Reference Cheat Sheet

### Chrome DevTools - Most Common Commands

```bash
# Start workflow
new_page(url="http://localhost:5173")
take_snapshot()  # Get uid values
take_screenshot()

# Interact with elements
fill(uid="<uid>", value="text")
click(uid="<uid>")
wait_for(text="Success")

# Debug
list_console_messages()
list_network_requests(resourceTypes=["fetch", "xhr"])
get_network_request(reqid=X)

# Responsive testing
resize_page(width=375, height=812)  # iPhone
take_screenshot()
```

### Puppeteer - CSS Selector Based

```bash
# Navigate
puppeteer_navigate(url="http://localhost:5173")
puppeteer_screenshot(name="homepage")

# Interact
puppeteer_fill(selector="#email", value="test@test.com")
puppeteer_click(selector="button[type=submit]")
```

### Figma - Design Tokens & Code Gen

```bash
# Check authentication
mcp__figma__whoami()

# Get design context (fileKey from URL, nodeId with : not -)
mcp__figma__get_design_context(
  fileKey="VxMJeyp9P35Alv5e2O1JQC",
  nodeId="8:2",
  clientLanguages="javascript,css",
  clientFrameworks="react"
)

# Get design tokens
mcp__figma__get_variable_defs(
  fileKey="VxMJeyp9P35Alv5e2O1JQC",
  nodeId="8:2"
)
```

### Essential Starview URLs

```bash
# Frontend (Vite dev server)
http://localhost:5173/              # Home
http://localhost:5173/login         # Login
http://localhost:5173/register      # Register
http://localhost:5173/profile       # Profile settings (protected)
http://localhost:5173/users/username # Public profile

# Backend (Django)
http://127.0.0.1:8000/api/health/   # Health check
http://127.0.0.1:8000/api/auth/user/ # Current user
```

---

## Resources

- [Chrome DevTools MCP - GitHub](https://github.com/ChromeDevTools/chrome-devtools-mcp)
- [Puppeteer MCP - GitHub](https://github.com/modelcontextprotocol/servers/tree/main/src/puppeteer)
- [Figma MCP - Documentation](https://mcp.figma.com/)
- [MCP Protocol Docs](https://modelcontextprotocol.io/)
