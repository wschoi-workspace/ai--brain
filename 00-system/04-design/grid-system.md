# AI GRID DESIGN SYSTEM

> Version 1.0 | 2026-05-20
> Companion to: [project-rent-design-guide.md](project-rent-design-guide.md)

---

## CORE PRINCIPLE

All layout decisions must be mathematically explainable.

This system prioritizes:
- structural consistency
- spatial balance
- vertical rhythm
- horizontal alignment
- modular composition
- predictable layout behavior
- adaptive component organization

The goal is NOT visual decoration.

The goal is: creating layouts that remain visually stable regardless of:
- content amount
- component count
- text length
- image ratio
- responsive scaling

Every object must exist within a clear spatial logic.
Structure comes before aesthetics.

---

## 1. GLOBAL GRID SYSTEM

### Primary Grid

- Use a **12-column** modular grid
- Maintain equal column width
- Maintain consistent gutter spacing
- Maintain fixed outer margins
- Never place objects outside the grid

### Default Values

| Context | Margin | Gutter | Columns | Base Unit |
|---------|--------|--------|---------|-----------|
| Slide (1920×1080) | 40–60px | 20px | 12 | 8px |
| Document / Web | 40–60px | 20px | 12 | 8px |
| Card / Component | — | 16px | auto | 8px |

> These values align with project-rent-design-guide.md Section 4.

### Column Span Reference

| Layout | Columns | Use |
|--------|---------|-----|
| Full width | 12 | Hero, cover, full-bleed |
| Two-thirds | 8 | Main content area |
| Half | 6 | Side-by-side comparison |
| One-third | 4 | Sidebar, KPI card |
| Quarter | 3 | Small card, thumbnail |

---

## 2. ALIGNMENT SYSTEM

### Horizontal Alignment

All objects must align to:
- column edges
- column centers
- or shared vertical axes

Avoid arbitrary positioning.
Objects must visually connect through alignment logic.

### Vertical Alignment

All typography and components must follow:
- baseline rhythm
- consistent vertical intervals
- predictable stacking structure

Avoid random vertical spacing.
Every section must feel mathematically related.

### Cross-Alignment Rule

When multiple rows of components exist:
- top edges must align horizontally
- left edges must align vertically
- internal content (labels, values, icons) must share baseline

---

## 3. SPACING RULES

### Spacing Scale (8px Base)

Only use spacing values derived from the 8px system:

| Token | Value | Use |
|-------|-------|-----|
| xs | 4px | Tight internal gaps |
| sm | 8px | Icon-to-text, inline spacing |
| md | 16px | Component internal padding (small) |
| lg | 24px | Component internal padding (default) |
| xl | 32px | Section gap (small) |
| 2xl | 48px | Section gap (large) |
| 3xl | 64px | Major section separation |

Never use arbitrary spacing values.

### Internal Component Padding

All components must maintain:
- equal internal padding on all sides
- symmetrical content spacing
- optical balance

| Component Size | Padding | Example |
|---------------|---------|---------|
| Small | 16px | Tag, badge |
| Medium | 24px | KPI card, button group |
| Large | 32px | Section container, hero |

> Consistent with project-rent-design-guide.md Section 5 (KPI card: 24px padding).

---

## 4. COMPONENT CONSTRUCTION

### Box Logic

Every component exists inside a clear rectangular boundary.

Rules:
- All content must be contained within a defined box
- Boxes must visually snap together along grid lines
- No floating objects outside box boundaries
- No irregular edge relationships

### Component Behavior

Components must:
- expand proportionally within their grid columns
- maintain internal structure at any width
- preserve alignment regardless of content amount
- keep consistent padding ratios when scaling

### Adaptive Layout Rule

**Component count should NOT break layout rhythm.**

When component count changes:
- preserve equal spacing between items
- preserve visual rhythm and proportion
- preserve grid continuity
- recalculate layout mathematically

| Count | Layout Strategy |
|-------|----------------|
| 1 | Center or full-width |
| 2 | 6+6 columns |
| 3 | 4+4+4 columns |
| 4 | 3+3+3+3 columns or 6+6 × 2 rows |
| 5+ | 4+4+4 × rows, or 3+3+3+3 × rows |

Never compress objects randomly. Recalculate mathematically.

### Equal Distribution Rule

When items share a row:
- all items must have equal width
- all gaps must be equal
- if items cannot divide evenly, use rows (e.g., 5 items → 3+2)
- the last row aligns left, maintaining the same item width

---

## 5. TYPOGRAPHY GRID INTEGRATION

### Baseline Rhythm

Typography must maintain:
- consistent line-height across all text blocks
- predictable paragraph spacing (multiples of 8px)
- baseline consistency between adjacent columns

| Level | Line Height | Paragraph Spacing |
|-------|------------|-------------------|
| Display | 1.0 | 32px after |
| H1–H3 | 1.2–1.3 | 24px after |
| Body | 1.5–1.6 | 16px after |
| Caption | 1.4 | 8px after |

> Values from project-rent-design-guide.md Section 3.

### Text Alignment

Default: **left-aligned only**

Exceptions (permitted):
- KPI numbers: center-aligned within their card
- Cover titles: center-aligned on full-bleed backgrounds
- Table cell numbers: right-aligned

Avoid:
- unnecessary center alignment in body text
- random text positioning
- mixed alignment within the same section

### Text Box Behavior

Text containers must:
- align to grid column edges
- preserve equal padding
- avoid unstable text wrapping

Avoid:
- orphan text (single word on last line)
- isolated short lines (< 30% of container width)
- uneven paragraph width between adjacent columns

---

## 6. IMAGE SYSTEM

### Image Placement

Images must:
- align to grid columns
- maintain proportional scaling
- preserve consistent cropping logic
- use consistent aspect ratios within the same section

### Aspect Ratio Standards

| Use | Ratio | Example |
|-----|-------|---------|
| Hero / Cover | 16:9 | Full-bleed background |
| Landscape | 3:2 | Case study, portfolio |
| Square | 1:1 | Profile, icon, thumbnail |
| Portrait | 2:3 | Product, person |

Avoid:
- random aspect ratio mixing within the same row
- decorative overlap without structural purpose
- unstable image placement outside grid

### Image Rhythm

Image blocks must maintain:
- equal visual weight across a row
- consistent spacing (same gutter as grid)
- compositional balance with adjacent text

---

## 7. VISUAL DENSITY CONTROL

### Density Principle

Layouts must feel:
- breathable
- calm
- intentional

Whitespace is part of the design system.
Do not fill empty space unnecessarily.

### Content Distribution

- Maximum content area: 70–80% of total space
- Minimum whitespace: 20–30% of total space
- No section should feel significantly heavier than another

Avoid:
- crowded clusters
- isolated heavy sections
- visual imbalance between left and right halves

### Information Hierarchy Through Space

| Priority | Spacing Around | Visual Weight |
|----------|---------------|---------------|
| Primary | Large (48–64px) | High contrast, large type |
| Secondary | Medium (24–32px) | Normal weight |
| Tertiary | Small (16px) | Reduced contrast, small type |

---

## 8. NEGATIVE RULES

STRICTLY AVOID:

- [ ] Random asymmetry without structural purpose
- [ ] Inconsistent spacing between similar elements
- [ ] Floating objects outside the grid
- [ ] Decorative positioning that breaks alignment
- [ ] Arbitrary scaling of components
- [ ] Misaligned text between columns
- [ ] Broken baseline rhythm
- [ ] Overcrowded composition
- [ ] Excessive visual noise (shadows, gradients, borders)
- [ ] Overlapping elements without clear z-order logic

---

## 9. AI LAYOUT EXECUTION ORDER

Before generating any design, follow this sequence:

```
1. Establish grid (12-column, margins, gutters)
2. Establish spacing rhythm (8px system)
3. Establish content hierarchy (primary → secondary → tertiary)
4. Place components within grid columns
5. Align all objects (horizontal + vertical + baseline)
6. Validate spatial balance (content vs whitespace ratio)
7. Validate visual rhythm (equal spacing, consistent sizing)
8. THEN apply visual styling (colors, typography, shadows)
```

Structure → Alignment → Rhythm → Style.
Never style before structure is validated.

---

## 10. DESIGN PHILOSOPHY

This system follows principles inspired by:
- Swiss grid systems (Josef Müller-Brockmann)
- Editorial design (newspaper/magazine column logic)
- Architectural composition (proportional systems)
- Museum spatial rhythm (breathing room, focal hierarchy)
- Retail environmental structure (wayfinding, information density)

Design should feel:
- **calm** — no visual anxiety
- **structured** — every element has a reason
- **premium** — confidence through restraint
- **balanced** — no section dominates without purpose
- **intentional** — nothing accidental

Never chaotic. Never arbitrary.

---

*This guide is a spatial behavior ruleset for AI-generated layouts.*
*For brand styling (colors, typography, tone): see [project-rent-design-guide.md](project-rent-design-guide.md)*
