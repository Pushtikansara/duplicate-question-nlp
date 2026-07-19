---
name: ui-ux-designer
description: Use when designing user interfaces, user experiences, wireframes, prototypes, or visual layouts. Covers UX research, interaction design, visual hierarchy, typography, color theory, and design tools.
---

# UI/UX Designer Skill

## Instructions

1. Start with user research and problem definition before any visual design work
2. Create low-fidelity wireframes to establish layout and information architecture
3. Build interactive prototypes to validate user flows before high-fidelity design
4. Apply visual hierarchy principles to guide user attention and improve scannability
5. Establish a consistent typography scale using modular scale ratios (1.25, 1.333)
6. Choose color palettes with sufficient contrast and semantic meaning
7. Use 8px or 4px grid systems for consistent spacing and alignment
8. Design with accessibility in mind from the start, not as an afterthought
9. Conduct usability testing with real users at multiple stages of the design process
10. Document design decisions and maintain a single source of truth for design assets

## Examples

1. User-centered design process: Research -> Define -> Ideate -> Prototype -> Test -> Implement
2. Wireframing: Start with low-fidelity black-and-white wireframes using Balsamiq or Figma before moving to high-fidelity mockups
3. Visual hierarchy: Use size (hero heading 48px), color (primary CTA), and spacing (32px section gaps) to guide attention
4. Typography scale: Establish a type scale with 6-8 sizes (12, 14, 16, 20, 24, 32, 40, 48px) using a 1.25 modular scale
5. Color system: Define primary (brand), secondary, neutral, success, warning, error, and info colors with proper contrast ratios
6. Layout grid: Use a 12-column grid with 24px gutters and 16px margins for responsive layouts
7. Spacing system: Implement a 4px base unit spacing scale (4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96, 128px)
8. Design system: Create and maintain a component library with documented patterns and usage guidelines
9. Prototyping: Build interactive prototypes in Figma with smart animate and overlays for user testing
10. Design handoff: Export assets, create redlines, and use tools like Zeplin or Figma Dev Mode for developer handoff

## Best Practices

1. Follow a user-centered design process: Empathize, Define, Ideate, Prototype, Test
2. Maintain visual consistency with a defined design system and component library
3. Use the 60-30-10 rule for color distribution (60% neutral, 30% primary, 10% accent)
4. Keep interactive elements at least 44x44px for touch targets
5. Limit line lengths to 60-75 characters for optimal readability
6. Use 8px grid spacing for consistency across all layouts
7. Design for the smallest screen first, then progressively enhance
8. Test designs with real users early and often, iterating based on feedback
9. Maintain a clear visual hierarchy with 3 levels of headings maximum
10. Use consistent iconography from a single icon set throughout the interface

## Common Mistakes

1. Skipping user research and jumping straight to visual design
2. Using too many font sizes and weights, creating visual noise
3. Ignoring accessibility requirements like color contrast and keyboard navigation
4. Designing only for ideal content states without considering empty, error, and loading states
5. Overcomplicating navigation with too many levels or unclear labels
6. Using low-contrast text that fails WCAG AA standards
7. Neglecting mobile-first design and only designing for desktop
8. Creating inconsistent spacing and alignment across screens
9. Overusing animations that slow down the user experience
10. Failing to document design decisions and component usage guidelines

## Libraries

1. Figma - Primary design and prototyping tool with collaborative features
2. Sketch - Vector-based design tool with extensive plugin ecosystem
3. Adobe XD - Design and prototyping tool with Adobe ecosystem integration
4. Framer - Interactive design tool with React component support
5. Zeplin - Design handoff and collaboration platform
6. Abstract - Version control for design files
7. Maze - User testing and analytics for prototypes
8. Hotjar - Heatmaps and user behavior analytics
9. UsabilityHub - Quick user testing and preference tests
10. Stark - Accessibility and contrast checking plugin for Figma/Sketch

## Design Principles

1. User-centered: Design decisions should be based on user needs, research, and testing rather than assumptions
2. Consistency: Use consistent patterns, components, and interactions throughout the interface
3. Hierarchy: Establish clear visual hierarchy through size, color, contrast, and spacing
4. Simplicity: Reduce cognitive load by removing unnecessary elements and complexity
5. Feedback: Provide clear feedback for every user action (hover, click, error, success)
6. Affordance: Design elements should suggest their functionality through visual cues
7. Accessibility: Ensure designs are usable by people of all abilities
8. Progressive disclosure: Show only what users need at each step, reveal more as needed
9. Recognition over recall: Make information visible rather than requiring users to remember it
10. Error prevention: Design interfaces that prevent errors before they happen

## Coding Standards

1. Use a consistent 8px spacing grid for margins, padding, and element sizing
2. Define typography using a modular scale with rem/em units for accessibility
3. Use semantic color tokens (--color-primary, --color-error) instead of raw hex values
4. Export designs with clear layer naming conventions (Button/Primary/Default, Button/Primary/Hover)
5. Group Figma layers into logical frames and sections with descriptive names
6. Use auto-layout in Figma for responsive component behavior
7. Define component variants for all interactive states (default, hover, active, disabled, focus)
8. Export assets at 1x, 2x, and 3x resolutions for retina displays
9. Document spacing, typography, and color values in a shared design token file
10. Use version control for design files with clear naming (v1.0, v1.1) and changelogs
