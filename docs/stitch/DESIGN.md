```markdown
# Design System Specification: The Cognitive Sanctuary

## 1. Overview & Creative North Star
In an era of digital distraction, this design system is built upon the North Star of **"The Cognitive Sanctuary."** Unlike traditional learning platforms that overwhelm users with dense grids and high-contrast borders, this system prioritizes deep focus through atmospheric depth, editorial spacing, and a "flow-state" layout.

We move beyond the "template" look by embracing **Intentional Asymmetry**. By utilizing generous whitespace (Scale 12–24) and overlapping "glass" layers, we create a UI that feels curated rather than generated. The goal is to make the student feel they are entering a premium, quiet space designed specifically for their intellectual growth.

---

## 2. Colors & The Surface Ethos
The palette is rooted in "Intelligence Blue" and "Success Green," but its execution relies on the sophisticated management of neutrals to prevent visual fatigue.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to define sections. Traditional "boxes" create mental barriers. Instead, boundaries must be defined through:
- **Tonal Shifts:** Placing a `surface_container_low` (#f3f4f5) element against a `surface` (#f8f9fa) background.
- **Negative Space:** Using the Spacing Scale to let elements breathe.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of fine paper and frosted glass.
- **Base Layer:** `surface` (#f8f9fa).
- **Secondary Regions:** `surface_container_low` (#f3f4f5) for sidebar or background utility areas.
- **Content Cards:** `surface_container_lowest` (#ffffff) for the highest focus.
- **Active Elements:** `primary_container` (#1a73e8) for subtle highlights.

### The "Glass & Gradient" Rule
To avoid a "flat" corporate feel, use subtle gradients for CTAs. A transition from `primary` (#005bbf) to `primary_container` (#1a73e8) at a 135-degree angle adds "soul" and dimension. Floating navigation elements should utilize a **Glassmorphism** effect: `surface` color at 70% opacity with a `20px` backdrop blur.

---

## 3. Typography: Editorial Authority
The typography system uses a pairing of **Manrope** for high-level editorial impact and **Inter** for functional clarity.

- **Display & Headlines (Manrope):** Use `display-lg` (3.5rem) and `headline-md` (1.75rem) to create a clear hierarchy. These should be set with tighter letter-spacing (-0.02em) to feel like a high-end magazine.
- **Body & Labels (Inter):** Use `body-lg` (1rem) for learning content to ensure maximum readability. Use `label-md` (0.75rem) for metadata, always in `on_surface_variant` (#414754) to reduce contrast harshness.

The typographic rhythm is the "heartbeat" of the app. Headlines should have a leading `24` spacing scale from the previous section to signify a new mental chapter.

---

## 4. Elevation & Depth
Hierarchy is conveyed through **Tonal Layering** rather than structural lines.

- **The Layering Principle:** Depth is achieved by stacking tiers. An "Active Lesson" card (`surface_container_lowest`) sits on a "Module" container (`surface_container_low`), which sits on the "App" background (`surface`). This creates a soft, natural lift.
- **Ambient Shadows:** For floating elements (Modals/Popovers), use a shadow tinted with `on_surface` (#191c1d) at 6% opacity. Blur should be expansive (32px–48px) to mimic natural, diffused light.
- **The "Ghost Border" Fallback:** If accessibility requires a stroke, use `outline_variant` (#c1c6d6) at 15% opacity. **Never use 100% opaque borders.**
- **Glassmorphism:** Apply to global headers. This allows the colors of the learning content to bleed through as the user scrolls, maintaining a sense of "place" and continuity.

---

## 5. Components

### Cards & Progress
- **The "Learning Card":** Use `rounded-md` (12px/0.75rem). No dividers. Separate the lesson title from the description using a `spacing-3` (1rem) vertical gap.
- **Flow Trackers:** Progress bars should use a `secondary` (#1b6d24) fill on a `secondary_container` (#a0f399) track. Add a soft glow to the progress tip using a 4px blur of the `secondary` color.

### Buttons
- **Primary:** Gradient fill (`primary` to `primary_container`), `rounded-full`, `on_primary` text. No shadow on rest; subtle `primary` glow on hover.
- **Secondary:** Transparent background with a "Ghost Border."
- **Tertiary:** Text-only, using `primary` color, for low-emphasis actions like "Skip."

### Input Fields
- Avoid heavy boxes. Use `surface_container_high` (#e7e8e9) as the fill with a bottom-only `outline` (#727785) that transitions to a 2px `primary` highlight on focus.

### Additional: The "Zen" Mode Toggle
A custom component that collapses the sidebar and shifts the layout to a centered, single-column editorial view (720px wide) to minimize peripheral cognitive load.

---

## 6. Do's and Don'ts

### Do:
- **Embrace Asymmetry:** Align headings to the left while keeping action buttons floated to the right to create a dynamic visual path.
- **Use Tonal Shifting:** Change the background color of the entire screen slightly when a user enters a "Success" state (e.g., shifting to a very pale version of `secondary_container`).
- **Prioritize Breathing Room:** When in doubt, increase the spacing scale. Learning requires mental "air."

### Don't:
- **Don't use 1px Dividers:** They cut the user's flow. Use white space or tonal blocks.
- **Don't use Pure Black:** Text should always be `on_surface` (#191c1d) to keep the experience "soft" and academic.
- **Don't Clutter with Icons:** Only use icons where they provide immediate functional clarity. A minimalist interface is an intuitive interface.

---

*Director's Note: This design system is not a set of constraints, but a philosophy. You are building a tool for the mind. Treat every pixel with the same respect you would give a physical study hall.*```