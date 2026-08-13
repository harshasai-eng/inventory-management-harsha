---
name: saas-sidebar-redesign
description: Methodology for redesigning a Vue 3 app's UI into a modern SaaS-style interface with a left sidebar nav, consistent design-token-based spacing, and a polished visual system. Use when converting a top-nav Vue 3 app to a sidebar layout, introducing a design token system, or doing a UI polish pass on an existing Vue 3 app.
---

# SaaS Sidebar Redesign

A repeatable methodology for turning a Vue 3 app with a horizontal top nav into a
modern SaaS-style interface: a vertical left sidebar, a design-token system driving
consistent spacing/color/radius, and a general polish pass. Works on any Vue 3
codebase — the steps below are generic; adapt the illustrative values to what the
target app already has.

## When to use this skill

- The app has a top nav bar and the goal is a left sidebar instead.
- There's no design-token system (`var(--...)`) and spacing/colors are hardcoded,
  inconsistent literals scattered across files.
- Layout markup (page headers, card wrappers) is duplicated per view instead of
  centralized.
- General ask: "make this look like a modern SaaS product" / "clean up the UI."

## Methodology overview

```
Audit → Define tokens → Build the shell → Extract shared layout components
  → Apply spacing consistency → Polish pass → Verify
```

Each step is scoped deliberately narrow. This is a layout/nav/spacing pass, not a
full app rewrite — resist the urge to redesign every view's unique content
(charts, tables, forms) along the way.

## Step 1 — Audit

Before changing anything, establish the current state:

- Locate the root component (commonly `App.vue` / `src/App.vue`) and find where nav
  markup and global styles live.
- Grep for `var(--` across the source tree. If nothing turns up, this is a
  green-field token introduction, not a migration — no existing system to preserve.
- Inventory the current nav items (labels + routes) — this becomes the sidebar's
  link list, in the same order.
- List views/pages and look for repeated layout markup (page headers, stat grids,
  card wrappers) copy-pasted per view rather than centralized — these become
  extraction candidates in Step 4.
- Check the project's own instruction files (CLAUDE.md, AGENTS.md, README) for
  documented design-system conventions (colors, spacing rules, "no emojis," etc.) —
  a redesign should extend these, not contradict them.
- Note anything relocating out of the nav bar (profile menus, language switchers,
  filter bars, modal triggers) — each needs a new home in the shell (see Step 3).

## Step 2 — Define design tokens

Introduce CSS custom properties as the single source of truth for spacing, color,
radius, and shadow. This is illustrative *structure* — derive actual values from
the target app's existing palette (grep for the most-repeated hex values and
rem/px numbers) rather than pasting these literally and overwriting a real brand:

```css
:root {
  /* Spacing — 4px base grid */
  --space-1: 4px;   --space-2: 8px;   --space-3: 12px;
  --space-4: 16px;  --space-5: 20px;  --space-6: 24px;
  --space-8: 32px;  --space-10: 40px; --space-12: 48px;

  /* Radius */
  --radius-sm: 6px; --radius-md: 8px; --radius-lg: 12px; --radius-full: 9999px;

  /* Neutrals */
  --color-bg: #f8fafc;
  --color-surface: #ffffff;
  --color-border: #e2e8f0;
  --color-text-primary: #0f172a;
  --color-text-secondary: #64748b;

  /* Accent — swap for the app's actual brand color */
  --color-accent: #2563eb;
  --color-accent-subtle: #eff6ff;

  /* Status */
  --color-success: #059669; --color-success-subtle: #d1fae5;
  --color-warning: #ea580c; --color-warning-subtle: #fed7aa;
  --color-danger:  #dc2626; --color-danger-subtle:  #fecaca;

  /* Elevation */
  --shadow-sm: 0 1px 3px 0 rgba(0,0,0,0.05);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.06);

  /* Layout */
  --sidebar-width: 260px;
}
```

Put tokens in one canonical, load-order-first location: a dedicated file (e.g.
`src/styles/tokens.css`) imported once at the app's entry point, ahead of the root
component import — or, if the app has no separate global-CSS entry point, prepend
to the root component's global (non-scoped) style block. Prefer the dedicated file
when there's any existing global CSS entry point to hook into.

## Step 3 — Build the shell (sidebar layout)

- Root layout becomes a two-column flex/grid shell: a fixed-width vertical sidebar
  + a scrollable main content column (`flex: 1`). Replace the old
  header-then-content vertical stack.
- Sidebar structure: brand/logo header, nav link list, optional footer for
  secondary actions.
- **Fix the common anti-pattern**: if active-link state is done via manual
  `:class="{ active: $route.path === '/...' }"` comparisons, replace with
  vue-router's built-in `active-class` (and `exact-active-class` for the root
  route, so it doesn't stay highlighted on sub-paths).
- Icons, if used, must be inline SVG — never emoji — for a professional business
  UI. A text-only sidebar is a legitimate, lower-effort choice; don't feel
  obligated to add icons.
- Anything that lived in the old top nav besides the links themselves (profile
  menu, language switcher, modal triggers, an always-visible filter bar) needs an
  explicit new home — typically a slim top bar within the content column (safer:
  more width for dropdowns) or a sidebar footer (more "textbook SaaS," but check
  that any dropdown/menu width fits the sidebar's width before committing to it).

## Step 4 — Extract shared layout components

Pull the duplicated markup found in Step 1's audit (page headers, stat grids, card
shells) into small shared components or a slot-based layout wrapper, so spacing
and typography rules live in one place instead of drifting per view. Keep this
shallow: centralize chrome, don't attempt to unify each view's unique content.

## Step 5 — Apply spacing/token consistency

Sweep view-level styles for hardcoded spacing values and inline `style="..."`
attributes; replace with `var(--space-N)` tokens where there's a natural
structural fit (margins, padding, gaps between major blocks). Do not chase every
magic number — chart coordinates, SVG viewBox math, and other visualization
internals are out of scope for this pass.

## Step 6 — Polish pass

- Consistent card styling (radius/shadow/border tokens), consistent
  hover/transition timing, consistent heading scale.
- Audit color usage against the token set and fix any ad hoc one-off colors found
  along the way (a rogue gradient used in exactly one place, a stray hex not in
  the palette).
- Responsive behavior is a judgment call, not an assumption: if the app already
  has `@media` patterns elsewhere, match them (e.g. sidebar collapses behind a
  toggle below ~768px). If it has none and the task didn't explicitly ask for
  mobile support, ship a clean desktop-first result and note the gap as a
  follow-up rather than silently expanding scope into a responsive rebuild.

## Step 7 — Verify

- Visually check every route reachable from the new sidebar.
- Check the browser console for errors/warnings introduced by the refactor.
- Confirm everything relocated during the shell restructure (modals, menus,
  filters) still functions — opens, closes, updates state correctly.
- If browser automation tooling is available in the environment (e.g. a
  Playwright MCP server), use it to navigate each route and capture the console —
  don't assume it exists if it isn't configured.

## Delegating `.vue` edits

Check whether this project has a designated Vue/frontend subagent or persona
configured for `.vue` file changes — look at the project's CLAUDE.md/AGENTS.md and
`.claude/agents/` directory for a Vue-specialist agent and any mandatory-delegation
rule. If one is configured, route all `.vue` creation and edits through it and
follow that project's existing rules. If none exists, make the edits directly, but
still follow this methodology.

## Closing checklist

- Tokens defined before shell work begins.
- Sidebar active-state uses router-native primitives, not manual path comparisons.
- Icons (if any) are SVG, never emoji.
- Spacing sweep is layout-scoped, not exhaustive — chart/SVG internals untouched.
- Every route verified after the change; console is clean.
- Anything relocated out of the old nav (menus, filters, modals) still works.
- Project-specific `.vue` delegation rules were checked and respected.
