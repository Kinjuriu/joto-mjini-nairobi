# Design rules (Stephane's no-vibe-coding guide)

Read this before writing any UI code. These rules are mandatory for this project. They summarise Stephane's full guide (her `no-vibe-coding` repo README).

Stephane's rules for web work, based on YC's Design Review episode on avoiding vibe coded sites (Aaron Epstein with Raphael Schaad, 6 March 2026) and her own newsroom-style dashboard practice. The full guide is the Project doc `claude/no-vibe-coding.md` and the README of her `no-vibe-coding` repo; read it for detail.

## Why

Language models learn most from well-linked sites, so a trend set by one good site (purple gradients, scroll effects, glowing cards) spreads to every new AI-built site within a week. Ubiquity removes the meaning and originality. Every choice must be deliberate.

## The hand-coding test (most important)

Before keeping any effect, animation or interaction, ask: if a person had to hand-code this over a day or a week, would they still choose to build it? Many AI-site effects exist only because they are free now. If the answer is no, remove it. Also ask: does it help the visitor understand or act; would anyone notice if it were gone; can I still remember the content after scrolling past it? Spend AI's speed on things that are worth a week of hand-coding: real demos, good maps, careful charts.

## Banned

- Purple or purple-to-pink gradients, decorative gradients, black-and-purple palettes, pinkish-purple accents, neon glows, orbs, blobs, glassmorphism or liquid glass
- Lines or paths that follow the scroll; cursor-following glows; buttons that chase the cursor; meteors or particles
- Fade-in or fade-out on scroll, slide-in reveals, parallax, scroll-jacking, double sticky headers, "scroll down to see more" cues, bouncing chevrons, animated arrows
- Hover effects that fade, shrink or hide the element; hover animations that move or tilt
- Stock icon sets (Lucide etc.), sparkle AI icons, emoji as UI
- Three-card feature rows, bento grids, hero with giant headline plus two CTA buttons
- Low-contrast grey text; blurry images or video posters; posters that do not match their video
- Non-standard navigation; company name inside the headline instead of beside the logo
- Pie, donut, 3D charts, dual axes, decorative KPI tiles with sparklines
- Inter, Poppins, Montserrat or system-ui as the primary typeface; em dashes and "not X, but Y" in copy

## Hover

The browser already shows a hand cursor on clickable things. Any extra effect makes the element more inviting (a shade lighter or darker, a stronger border, a small glow) and never makes it go away. Keep behaviour standard. Never hide critical information or functionality behind hover; phones have no hover and long press is undiscoverable. Every tooltip's content must also be reachable by tap, click and keyboard, and key numbers must be visible without interaction.

## Scrolling and motion

Native scrolling only. Content is present on arrival. Motion only shows that data changed (150 to 250ms), off under prefers-reduced-motion, no autoplay. Allowed exception: a thin, static reading progress indicator on long stories, because it answers a real reader question (how far into the book am I).

## Colour and brand

Start from the chosen palette, typefaces and references, then feed them to the tool; never start from the tool's output and tweak. Colours must complement the logo. Colour is for data in dashboards. Body text meets WCAG AA.

## Communicating value

A landing page is a customer acquisition channel, not the product. The first screen answers what it is, who it is for, why they should care, plus a call to action. For data stories and dashboards: the headline states the finding, the subtitle defines the measure, the key chart or number is on the first screen.

## Dashboards and data stories

One question per chart; title, subtitle, source and date on every chart; direct labels over legends; hand-built SVG over library defaults; squared geometry (0 to 2px radii, hairline rules); works with JavaScript off at its default state. References: AP, FT and NYT graphics desks.

## When briefing another model

Give it the palette with hex values, typefaces, references (screenshots and why), the page's purpose, what the first screen must show, and the banned list above. Require it to justify every effect with the hand-coding test in its report, take screenshots at 375px and 1440px, and list anything it is unsure of.

## Human QA before shipping

Click and tap every control, scroll slowly through transitions (especially sticky headers), check every image and video poster, use the page by keyboard only, test reduced motion, read every word aloud, and ask someone new to say what it is after ten seconds. Then run the pre-ship checklist in the full guide.