# Obsidian — High-Contrast Dark

## North Star: "Precision in Darkness"
Developer-grade dark UI. Near-black surfaces, high-contrast text, and precise accent colors. Clean, fast-feeling, and functional.

## Colors
- **Primary (`#a78bfa`):** Soft violet — interactive elements, links, focus rings.
- **Background (`#09090b`):** True near-black.
- **Tertiary (`#34d399`):** Emerald green — success states, positive indicators, code highlights.
- **Surface scale:** Zinc-based grays (`#0c0c0f` → `#27272a`). Very subtle increments.
- **Warning (`#facc15`):** Amber — warning states, yellow traffic light.
- Red (`#ef4444`) for errors only. No decorative color use.
- **Traffic light system:** Green (`#34d399`) → Yellow (`#facc15`) → Red (`#ef4444`). Used across all panels for status escalation.

## Typography
- **All fonts:** Geist — modern, clean, developer-friendly.
- Tight letter-spacing on headings (-0.02em). Standard on body.
- `#fafafa` for primary text, `#a1a1aa` for secondary. High contrast always.

## Elevation
- Minimal shadows. Use border-based separation: `1px solid #27272a`.
- Active/hover states: subtle background shifts to next surface tier.
- Focus rings: `2px solid #a78bfa` with `2px offset`.

## Components
- **Buttons:** Primary = solid violet fill. Secondary = transparent + border. Ghost = text only, visible on hover.
- **Cards:** `surface_container` background, thin `outline_variant` border, 8px radius.
- **Inputs:** `surface_container` fill, `outline_variant` border, violet focus ring.
- **Code blocks:** `surface_container_lowest` background, monospace font.

## Dashboard Components
- **Panel cards:** Full-width or half-width. `surface_container` bg, `outline_variant` border, 8px radius. Panel title in `#fafafa`, subtitle in `#a1a1aa`.
- **Traffic light dots:** 10px circles — `#34d399` / `#facc15` / `#ef4444`. Inline next to status text.
- **Gauge charts:** Horizontal bar with fill color mapped to traffic light. Background: `surface_container_lowest`.
- **Data tables:** Zebra striping with `surface_container` / `surface_container_lowest` alternation. Borders: `1px solid #27272a`.
- **Sparklines:** Thin line (2px) in `#a78bfa`. Area fill at 10% opacity.
- **Badge counts:** Pill shape, violet bg (`#a78bfa`) with `#09090b` text for counts. Red bg for urgent counts.
- **Progress bars:** Dual bar — progress in `#a78bfa`, spend in `#a1a1aa`. Overspend highlighted in `#ef4444`.
- **Empty state:** Centered `#a1a1aa` text + dashed `#27272a` border. No error styling.

## Rules
- Never use light backgrounds. Maintain zinc gray consistency.
- Borders over shadows for separation. Keep the interface flat and precise.
- Accent colors for function, never decoration.