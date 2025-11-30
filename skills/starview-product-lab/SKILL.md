---
name: starview-product-lab
description: Product validation and feature planning using UX research. Use for brainstorming, sprint planning, feature validation, or product direction. Understands natural language requests, automatically extracts relevant research, and offers tiered outputs from conceptual direction to implementation plans to GitHub tasks.
---

# Starview Product Lab

An automated product validation pipeline. Speak naturally about what you want to explore, and Claude will:
1. Analyze your intent
2. Extract relevant research via subagents
3. Synthesize insights
4. Offer tiered outputs (concept → implementation → tasks)

## Architecture: Intent-Driven Automation

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOMATED WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER INPUT (Natural Language)                                  │
│  Examples:                                                      │
│  - "I want to add a safety scoring feature"                     │
│  - "What should we prioritize this sprint?"                     │
│  - "Is weather integration worth building?"                     │
│  - "Help me understand our astrophotographer users"             │
│                                                                 │
│      ↓                                                          │
│                                                                 │
│  STEP 1: INTENT ANALYSIS (Main Claude)                          │
│  - Parse request                                                │
│  - Determine research needs                                     │
│  - Decide which files to query                                  │
│                                                                 │
│      ↓                                                          │
│                                                                 │
│  STEP 2: RESEARCH EXTRACTION (Haiku Subagents)                  │
│  - Spawn targeted subagents                                     │
│  - Extract relevant insights                                    │
│  - Detect gaps                                                  │
│                                                                 │
│      ↓                                                          │
│                                                                 │
│  STEP 3: SYNTHESIS (Main Claude)                                │
│  - Combine findings                                             │
│  - Generate recommendations                                     │
│                                                                 │
│      ↓                                                          │
│                                                                 │
│  STEP 4: OUTPUT SELECTION (Ask User)                            │
│  - Conceptual direction                                         │
│  - Implementation plan                                          │
│  - Create GitHub tasks                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Intent Analysis

When user invokes this skill with a natural language request, analyze their intent:

### Intent Categories

| Intent Type | Signals | Research Needed |
|-------------|---------|-----------------|
| **Feature Exploration** | "add", "build", "implement", "create" | Pain points + personas + competitors |
| **Validation** | "should we", "is it worth", "validate" | Pain points + competitors |
| **Sprint Planning** | "prioritize", "this sprint", "what next" | All research (overview) |
| **User Understanding** | "understand users", "who are", "persona" | Positioning (personas) |
| **Competitive Question** | "competitors", "vs", "differentiate" | Competitors |
| **Positioning/Identity** | "brand", "position", "messaging", "tagline" | Positioning + competitors |
| **Market Question** | "market size", "opportunity", "trends" | Positioning (market data) |

### Decision Logic

Based on intent, decide which research files to query:

```
IF intent involves features/building:
  → Query: pain-points + positioning (personas)
  → Optional: competitors (for differentiation)

IF intent involves validation:
  → Query: pain-points + competitors
  → Look for: existing demand, competitive landscape

IF intent involves sprint planning:
  → Query: ALL files (overview mode)
  → Synthesize: prioritized recommendations

IF intent involves users/personas:
  → Query: positioning
  → Focus on: persona sections

IF intent involves competition:
  → Query: competitors
  → Focus on: specific competitor or landscape

IF intent involves positioning/identity:
  → Query: positioning + competitors
  → Focus on: market positioning, differentiation
```

---

## Step 2: Research Extraction

Based on intent analysis, spawn appropriate Haiku subagents.

### Universal Subagent Footer

ALL subagent prompts must include:

```
---
GAP DETECTION: If the research does NOT adequately cover the requested topic:
- State: "INSUFFICIENT DATA for [TOPIC]"
- List what specific information is missing
- Note what related topics ARE covered
```

### Subagent Prompts by Intent

**For Feature Exploration:**
```
Use Task tool with:
  subagent_type: "Explore"
  model: "haiku"
  prompt: |
    Read .claude/ux-research/gemini-output-pain-points-*.md

    USER'S FEATURE IDEA: [EXTRACTED FROM USER INPUT]

    Extract:
    1. Pain points this feature would address
    2. How severe/frequent are these pain points?
    3. What workarounds do users currently use?
    4. Any explicit feature requests related to this?

    Maximum 600 words.

    GAP DETECTION: If insufficient data, state what's missing.
```

```
Use Task tool with:
  subagent_type: "Explore"
  model: "haiku"
  prompt: |
    Read .claude/ux-research/gemini-output-positioning-*.md

    USER'S FEATURE IDEA: [EXTRACTED FROM USER INPUT]

    Extract:
    1. Which personas would benefit from this feature?
    2. How does it align with their needs?
    3. Willingness to pay indicators

    Maximum 400 words.

    GAP DETECTION: If insufficient data, state what's missing.
```

**For Validation Questions:**
```
Use Task tool with:
  subagent_type: "Explore"
  model: "haiku"
  prompt: |
    Read .claude/ux-research/gemini-output-pain-points-*.md
    Read .claude/ux-research/gemini-output-competitors-*.md

    USER'S QUESTION: [EXTRACTED FROM USER INPUT]

    Extract evidence FOR and AGAINST building this:
    - Pain point severity (is this a real problem?)
    - Existing solutions (do competitors solve this?)
    - User demand signals (are people asking for this?)

    Maximum 600 words. Be balanced - show both sides.

    GAP DETECTION: If insufficient data, state what's missing.
```

**For Sprint Planning:**
```
Use Task tool with:
  subagent_type: "Explore"
  model: "haiku"
  prompt: |
    Read ALL files in .claude/ux-research/gemini-output-*.md

    Extract a prioritized view:
    1. Top 5 pain points by severity
    2. Biggest competitive gaps/opportunities
    3. Underserved persona needs

    Format as actionable priorities. Maximum 800 words.

    GAP DETECTION: Note any major research gaps.
```

**For Persona Understanding:**
```
Use Task tool with:
  subagent_type: "Explore"
  model: "haiku"
  prompt: |
    Read .claude/ux-research/gemini-output-positioning-*.md

    USER'S FOCUS: [PERSONA TYPE FROM USER INPUT, or "all personas"]

    Extract comprehensive persona profile(s):
    - Demographics and psychographics
    - Key needs and motivations
    - Pain points specific to this segment
    - Tools they currently use
    - Willingness to pay

    Maximum 600 words.

    GAP DETECTION: If persona not covered, state what's missing.
```

**For Competitive Questions:**
```
Use Task tool with:
  subagent_type: "Explore"
  model: "haiku"
  prompt: |
    Read .claude/ux-research/gemini-output-competitors-*.md

    USER'S FOCUS: [COMPETITOR NAME or "landscape"]

    Extract:
    - Strengths and weaknesses
    - Pricing/business model
    - User complaints
    - Gaps we can exploit

    Maximum 600 words.

    GAP DETECTION: If competitor not covered, state what's missing.
```

---

## Step 3: Synthesis

After receiving subagent responses, synthesize findings:

### Synthesis Template

```markdown
## Research Findings: [User's Topic]

### Key Insights
- [Insight 1]
- [Insight 2]
- [Insight 3]

### Evidence Summary
[Synthesized findings from subagents]

### Recommendation
[Clear recommendation based on evidence]

### Confidence Level
- **High** - Strong evidence, clear direction
- **Medium** - Some evidence, reasonable confidence
- **Low** - Limited data, needs more research

### Research Gaps (if any)
[List any gaps detected by subagents]
```

---

## Step 4: Output Selection

After synthesis, ask the user what output level they need:

### Use AskUserQuestion

```
question: "How would you like to proceed with this?"
options:
  - label: "Conceptual Direction"
    description: "Summary and recommendation only - good for early exploration"
  - label: "Implementation Plan"
    description: "Detailed technical plan considering Starview's architecture"
  - label: "Create GitHub Tasks"
    description: "Generate issues in GitHub Projects for sprint planning"
```

---

## Output Level A: Conceptual Direction

Provide the synthesis as-is, with:

```markdown
## Conceptual Direction: [Topic]

### Summary
[2-3 paragraph summary of findings and recommendation]

### Next Steps
- [ ] [Suggested next action]
- [ ] [Suggested next action]

### Questions to Resolve
- [Open question that needs answering]
- [Open question that needs answering]
```

---

## Output Level B: Implementation Plan

When user selects implementation plan, spawn a Sonnet subagent to create an architecture-aware plan:

```
Use Task tool with:
  subagent_type: "Explore"
  model: "sonnet"
  prompt: |
    You are creating an implementation plan for Starview.

    FEATURE TO IMPLEMENT: [FROM SYNTHESIS]
    RESEARCH CONTEXT: [KEY FINDINGS FROM SYNTHESIS]

    First, read the project architecture:
    - .claude/backend/ARCHITECTURE.md
    - .claude/frontend/ARCHITECTURE.md

    Then create an implementation plan that:
    1. Identifies which existing models/services to extend
    2. Lists new models/endpoints needed
    3. Describes frontend components required
    4. Notes integration points with existing systems
    5. Highlights potential challenges

    Format as:

    ## Implementation Plan: [Feature Name]

    ### Backend Changes
    - Models: [new or modified]
    - Serializers: [new or modified]
    - Views/Endpoints: [new or modified]
    - Services: [new or modified]
    - Signals: [if needed]

    ### Frontend Changes
    - Components: [new or modified]
    - Hooks: [new or modified]
    - Services: [new or modified]
    - Routes: [if needed]

    ### Integration Points
    - [How this connects to existing systems]

    ### Migration/Data Considerations
    - [Database migrations needed]
    - [Data backfill requirements]

    ### Estimated Complexity
    - Backend: Low/Medium/High
    - Frontend: Low/Medium/High
    - Overall: Low/Medium/High

    ### Implementation Order
    1. [First step]
    2. [Second step]
    3. [etc.]

    Maximum 1000 words.
```

Present the implementation plan to the user.

---

## Output Level C: Create GitHub Tasks

When user selects GitHub tasks, create draft items directly in the **Starview Kanban** project board.

### Project Configuration

```
Owner: adiazpar
Project Number: 7
Project Name: Starview Kanban
```

### Task Generation Process

1. **Parse implementation plan** (or synthesis if no plan yet) into discrete tasks
2. **Format as draft items** with descriptions
3. **Ask user for confirmation** before creating
4. **Create draft items** via `gh project item-add`

### Draft Item Command

```bash
gh project item-add 7 \
  --owner adiazpar \
  --title "[Feature Area] Task title" \
  --body "## Description
[Task description]

## Acceptance Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Technical Notes
[Any technical context]

## Research Context
From Product Lab analysis on [date]

---
*Generated by starview-product-lab*"
```

### Task Breakdown Logic

For a feature implementation, generate these draft items:

| Task Type | Title Pattern | When to Create |
|-----------|---------------|----------------|
| Epic | `[Epic] Feature Name` | Always - parent task |
| Backend | `[Backend] Create X model/endpoint` | If backend changes needed |
| Frontend | `[Frontend] Create X component` | If frontend changes needed |
| Integration | `[Integration] Connect X to Y` | If integration work needed |
| Testing | `[Testing] Add tests for X` | Always |
| Docs | `[Docs] Document X feature` | If user-facing feature |

### Confirmation Before Creating

Always show the user what will be created:

```markdown
## GitHub Tasks to Create

I'll create the following draft items in **Starview Kanban** (Project #7):

1. **[Epic] Safety Scoring Feature**
2. **[Backend] Create SafetyScore model and endpoint**
3. **[Frontend] Create SafetyScoreDisplay component**
4. **[Testing] Add safety scoring tests**

All items will appear in your **Backlog** column.

**Create these draft items?**
```

Wait for user confirmation before executing.

### Execution

Run each command sequentially:

```bash
gh project item-add 7 --owner adiazpar --title "[Epic] Safety Scoring Feature" --body "..."
gh project item-add 7 --owner adiazpar --title "[Backend] Create SafetyScore model" --body "..."
# etc.
```

### Moving Items Between Columns

After creation, items land in Backlog. To move items (if user requests):

```bash
# First, get the item ID
gh project item-list 7 --owner adiazpar --format json

# Then update the status field
gh project item-edit --project-id PROJECT_ID --id ITEM_ID --field-id STATUS_FIELD_ID --single-select-option-id OPTION_ID
```

Note: Moving items requires field IDs which vary per project. For now, items are created in Backlog and user can drag them manually in the UI.

---

## Handling Research Gaps

If subagents report insufficient data:

1. **Acknowledge the gap** in synthesis
2. **Adjust confidence level** to Low
3. **Offer to generate Gemini prompt** for missing research

```markdown
### Research Gap Detected

The current research doesn't cover [TOPIC] adequately.

**Options:**
1. Proceed with limited data (lower confidence)
2. Generate new research first

**Gemini Prompt for Missing Research:**
[Provide appropriate template from Gemini Prompt Templates section]
```

---

## Gemini Prompt Templates

When gaps are detected, provide these ready-to-use prompts:

### Pain Points Research
```
Perform deep research on user pain points related to [TOPIC] in stargazing/astrophotography.

Sources: Reddit (r/astrophotography, r/darksky), Cloudy Nights forums, app store reviews

Extract:
- Pain points with severity ratings
- Direct user quotes
- Existing workarounds
- Feature requests

Format with categories and evidence.
```

### Competitor Research
```
Comprehensive analysis of [COMPETITOR] in the stargazing/dark sky space.

Extract: Features, pricing, user reviews (positive and negative), target audience, weaknesses.

Include specific quotes and evidence.
```

### Persona Research
```
Research [USER SEGMENT] who engage in stargazing.

Extract: Demographics, psychographics, needs, tools used, willingness to pay, barriers.

Include quotes illustrating their mindset.
```

### Feature Validation
```
Research user interest in [FEATURE IDEA] for stargazing apps.

Find: Explicit requests, workarounds, competitor implementations, concerns.

Provide: Evidence of demand, recommendation to build/not build.
```

---

## Quick Reference

### Invocation Examples

| User Says | Claude Does |
|-----------|-------------|
| "I want to add safety scoring" | Feature exploration → pain points + personas |
| "Should we build weather integration?" | Validation → pain points + competitors |
| "What should we prioritize this sprint?" | Sprint planning → all research overview |
| "Tell me about our astrophotographer users" | Persona deep dive → positioning |
| "How do we compare to Light Pollution Map?" | Competitive analysis → competitors |
| "Help me refine our positioning" | Identity workshop → positioning + competitors |

### Output Levels

| Level | Depth | Time | Use When |
|-------|-------|------|----------|
| Conceptual | Summary + recommendation | Fast | Early exploration, brainstorming |
| Implementation | Architecture-aware plan | Medium | Ready to build, need technical direction |
| GitHub Tasks | Draft items in Starview Kanban | Medium | Sprint planning, ready to assign work |

### GitHub Projects Config

```
Owner: adiazpar
Project: #7 (Starview Kanban)
Command: gh project item-add 7 --owner adiazpar --title "..." --body "..."
```

### Key Files

| File | Purpose |
|------|---------|
| `.claude/ux-research/gemini-output-*.md` | Research source files |
| `.claude/backend/ARCHITECTURE.md` | Backend architecture (for impl plans) |
| `.claude/frontend/ARCHITECTURE.md` | Frontend architecture (for impl plans) |

### Subagent Models

| Task | Model |
|------|-------|
| Research extraction | Haiku |
| Implementation planning | Sonnet |
| Gap detection | Haiku |
