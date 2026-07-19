---
name: animation-designer
description: Use when planning, designing, or implementing motion design, micro-interactions, transitions, or animation systems. Covers animation principles, timing, easing, and choreography.
---

# Animation Designer Skill

## Instructions

1. Define a motion design system before implementing animations. Establish animation tokens (duration, easing, delay, distance) as part of the design system.
2. Classify animations into categories: micro-interactions (button presses, toggles), transitional (page transitions, element mounts/unmounts), narrative (scroll-driven storytelling), ambient (background parallax, particle effects), and loading (skeleton screens, spinners).
3. Choose the appropriate animation library based on complexity: CSS transitions for simple micro-interactions, Framer Motion for React component animations, GSAP for complex timelines and scroll-driven narratives, Three.js for 3D motion.
4. Apply the 12 principles of animation from Disney to UI motion: squash and stretch, anticipation, staging, straight ahead, follow through, slow in/out, arcs, secondary action, timing, exaggeration, solid drawing, appeal.
5. Use cubic bezier curves for custom easing that matches the brand character. Common easings: ease-in (accelerate), ease-out (decelerate), ease-in-out (smooth start/end).
6. Define animation durations in a scale: 100ms (instant feedback), 200ms (micro-interaction), 300ms (element enter/exit), 500ms (emphasis), 700-1000ms (narrative).
7. Use spring physics for natural-feeling UI motion: lower stiffness for slower, bouncier motion; higher stiffness for snappy, precise motion. Damping controls how quickly the oscillation stops.
8. Choreograph multi-element animations with staggering: delay the start of each element by a consistent interval (50-150ms) for sequential reveals.
9. Respect the user's motion preferences: use `prefers-reduced-motion` media query to disable or simplify animations. Provide a reduced-motion alternative for all animated content.
10. Use motion to communicate relationships: elements that share a transition (shared layout animation) are perceived as the same element in a new state. Elements that stagger are perceived as a group.
11. Use motion to direct attention: animate elements that change state or require user action. Motion captures peripheral vision.
12. Use motion for spatial orientation: sliding directions should match spatial expectations (menu slides from left, sheet from bottom, notifications from top).
13. Use `will-change` to prepare the browser for animations on specific elements, but do not overuse — it consumes GPU memory.
14. Test animations on different devices: a 300ms transition on desktop may feel slow on mobile where interaction expectations are faster.
15. Use performance tools (Chrome DevTools Performance tab, FPS meter) to ensure animations run at 60fps.
16. Build a motion spec document that catalogs all animation behaviors with their timing, easing, and interactions.
17. Use tools like Principle, After Effects, or Rive for prototyping complex animations before implementation.
18. Implement animation states consistently: `idle`, `hover`, `active`, `focus`, `disabled`, `entering`, `exiting`, `error`.
19. Use animation composition: break complex animations into smaller, reusable animation components that can be combined.
20. Document animation decisions: why a specific easing was chosen, why a certain duration was used, how animations respond to user interaction.

## Examples

### Motion Design Tokens (CSS Custom Properties)
```css
:root {
  /* Duration Scale */
  --duration-instant: 100ms;
  --duration-fast: 200ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --duration-narrative: 1000ms;

  /* Easing Functions */
  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.27, 1.55);

  /* Motion Distances */
  --motion-slide-up: -20px;
  --motion-slide-down: 20px;
  --motion-scale-enter: 0.95;

  /* Stagger Delays */
  --stagger-fast: 50ms;
  --stagger-normal: 80ms;
  --stagger-slow: 120ms;
}

@media (prefers-reduced-motion: reduce) {
  :root {
    --duration-instant: 0ms;
    --duration-fast: 0ms;
    --duration-normal: 0ms;
    --duration-slow: 0ms;
    --duration-narrative: 0ms;
  }
}
```

### Micro-Interaction: Button Press
```css
.button {
  transition:
    transform var(--duration-fast) var(--ease-spring),
    box-shadow var(--duration-fast) var(--ease-out);
}

.button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.button:active {
  transform: translateY(0px) scale(0.98);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
  transition-duration: var(--duration-instant);
}
```

### Staggered List Reveal (Framer Motion)
```tsx
import { motion } from "framer-motion";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.2,
    },
  },
};

const itemVariants = {
  hidden: {
    opacity: 0,
    y: 20,
    scale: 0.95,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      duration: 0.5,
      ease: [0.16, 1, 0.3, 1], // custom ease-out
    },
  },
};

export function AnimatedList({ items }: { items: string[] }) {
  return (
    <motion.ul variants={containerVariants} initial="hidden" animate="visible">
      {items.map((item) => (
        <motion.li key={item} variants={itemVariants}>
          {item}
        </motion.li>
      ))}
    </motion.ul>
  );
}
```

### Page Transition (GSAP)
```javascript
import gsap from "gsap";

function pageEnter(container) {
  const tl = gsap.timeline({ defaults: { duration: 0.5, ease: "power3.out" } });

  tl.from(container, {
    opacity: 0,
    scale: 0.98,
    duration: 0.4,
  })
    .from(container.querySelectorAll("[data-animate]"), {
      y: 30,
      opacity: 0,
      stagger: 0.06,
    }, "-=0.2");

  return tl;
}

function pageLeave(container) {
  const tl = gsap.timeline({ defaults: { duration: 0.3 } });

  tl.to(container, {
    opacity: 0,
    scale: 0.98,
    ease: "power2.in",
  });

  return tl;
}
```

### Shared Element Transition (Morphing)
```tsx
import { motion } from "framer-motion";

export function ProductGrid({ products }: { products: Product[] }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {products.map((product) => (
        <motion.div
          key={product.id}
          layoutId={`product-card-${product.id}`}
          className="bg-white rounded-lg p-4 shadow cursor-pointer"
          whileHover={{ y: -4, boxShadow: "0 8px 24px rgba(0,0,0,0.12)" }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
        >
          <motion.img
            layoutId={`product-image-${product.id}`}
            src={product.image}
            alt={product.name}
          />
          <h3>{product.name}</h3>
          <motion.p
            layoutId={`product-price-${product.id}`}
            className="text-lg font-bold"
          >
            ${product.price}
          </motion.p>
        </motion.div>
      ))}
    </div>
  );
}
```

### Scroll-Driven Narrative
```javascript
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const sections = document.querySelectorAll(".story-section");

sections.forEach((section, i) => {
  const heading = section.querySelector("h2");
  const content = section.querySelector(".content");
  const visual = section.querySelector(".visual");

  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: section,
      start: "top 70%",
      end: "top 20%",
      toggleActions: "play none none reverse",
    },
  });

  tl.from(heading, { y: 40, opacity: 0, duration: 0.6 })
    .from(content, { y: 20, opacity: 0, duration: 0.4 }, "-=0.3")
    .from(visual, { scale: 0.8, opacity: 0, duration: 0.5, ease: "back.out(1.7)" }, "-=0.4");
});
```

## Best Practices

- Build a motion design system with documented tokens before implementing individual animations. Consistency is critical.
- Use `prefers-reduced-motion` globally and test with it enabled. Animations should never cause discomfort or nausea.
- Keep micro-interactions under 200ms. Users should perceive them as instant feedback, not as delays.
- Use entrance animations sparingly. Animating everything on page load creates a slow, frustrating experience.
- Use exit animations for elements that disappear unexpectedly (dialogs, notifications, alerts).
- Match animation direction to user expectation: menus slide from the edge they are anchored to, sheets slide up from bottom, modals scale in from center.
- Use overlapping motion (follow-through and overlapping action from Disney principles). Elements should not all start and stop at the same time.
- Use motion to reduce perceived loading time: skeleton animations, progress bars, and transitional animations make waits feel shorter.
- Test animations with real users. Motion that seems good in isolation may be annoying or disorienting in context.
- Use `content-visibility: auto` and `contain: layout style paint` on animated elements that are offscreen to reduce rendering cost.
- Use animation-play-state: paused for animation debugging and testing.
- Coordinate animation timing with interaction timing. A click should produce immediate feedback, not a delay.
- For drag interactions, the dragged element must follow the cursor/pinch without delay — inertia should only apply on release.

## Common Mistakes

- Animating all elements on page load with the same timing, creating a wall of simultaneous motion.
- Using animations that are too slow (300ms+ for simple micro-interactions feels sluggish).
- Using animations that are too fast (under 100ms may be imperceptible).
- Not respecting `prefers-reduced-motion`, causing accessibility issues for users with vestibular disorders.
- Creating animations that trigger layout thrashing by animating `width`, `height`, `top`, `left` instead of `transform`.
- Using different easings for related animations, creating a disjointed feel.
- Overusing bounce and spring easings for UI elements that should feel precise, not playful.
- Forgetting exit animations — elements that suddenly disappear are jarring and disorienting.
- Animating elements that should remain stable (backgrounds, persistent navigation).
- Using animations that interfere with usability (e.g., parallax that makes text hard to read).
- Not testing animations on low-end devices where they may stutter or cause performance issues.
- Creating animation dependency chains that cause visible delays before content appears.
- Using hover animations that have no mobile equivalent — touch devices do not have hover states.
- Animating too many elements simultaneously, overwhelming the user and causing cognitive load.

## Libraries and Tools

- **Framer Motion**: React animation library for declarative motion. Best for component-level animations in React.
- **GSAP**: High-performance animation library for complex timelines and scroll-driven narratives.
- **CSS Transitions and Animations**: Built into the browser. Best for simple, declarative animations.
- **Motion One**: Lightweight animation library by the Framer Motion team. Best for vanilla JS and simple use cases.
- **Lottie**: JSON-based animation format exported from After Effects. Best for complex, pre-authored animations.
- **Rive**: Interactive animation tool. Best for state-machine-driven animations with procedural blending.
- **Lenis**: Smooth scroll library. Best for consistent cross-browser smooth scrolling experiences.
- **ScrollTrigger (GSAP)**: Scroll-driven animation plugin. Best for narrative and parallax scrolling.
- **AutoAnimations**: Library for automatic FLIP animations during DOM changes.
- **React Spring**: Physics-based animation library for React. Alternative to Framer Motion.
- **Anime.js**: Lightweight JavaScript animation library for simple use cases.
- **Mo.js**: Motion graphics library for declarative, retro-style animations.
- **Three.js**: 3D rendering library for spatial motion and 3D transitions.
- **Remotion**: Programmatic video creation with React. Use for pre-rendered animated content.
- **Principle**: Mac app for prototyping complex animations and interactions.
- **After Effects**: Industry-standard motion design tool. Export to Lottie for web playback.
- **Haiku Animator**: Visual animation tool that exports to code (Framer Motion, GSAP).
- **Chrome DevTools Animations Panel**: Record, inspect, and debug animations in the browser.
- **Leva**: GUI panel for debugging animation parameters during development.

## Design Principles

1. **Motion Has Meaning**: Every animation must serve a purpose. If removing an animation does not affect usability, reconsider its inclusion. Motion should communicate state changes, spatial relationships, and hierarchy.
2. **The 12 Principles of Animation**:
   - **Squash and Stretch**: Give objects weight and flexibility by deforming them on impact.
   - **Anticipation**: A small backward movement before forward motion builds expectation.
   - **Staging**: Present the action clearly so it is unmistakable.
   - **Straight Ahead and Pose to Pose**: Plan key poses and interpolate between them.
   - **Follow Through and Overlapping Action**: Parts of an element continue moving after the main motion stops.
   - **Slow In and Slow Out**: Ease in and out of motion for natural acceleration/deceleration.
   - **Arcs**: Natural motion follows curved paths, not straight lines.
   - **Secondary Action**: Supporting actions that complement the primary motion.
   - **Timing**: The number of frames determines the perceived weight and speed.
   - **Exaggeration**: Amplify motion to make it more readable and expressive.
   - **Solid Drawing**: Maintain consistent volume and form throughout motion.
   - **Appeal**: Motion should be aesthetically pleasing and engaging.
3. **Easing Defines Character**: The easing curve determines the emotional quality of motion. Ease-out feels responsive and natural. Ease-in feels deliberate and slow. Spring/bounce feels playful and energetic. Linear feels mechanical and robotic.
4. **Duration Sets Pace**: Faster durations (100-200ms) create urgency and responsiveness. Slower durations (400-700ms) create calm and emphasis. Consistent duration scales create predictable motion patterns.
5. **Choreography over Chaos**: Multiple elements in motion should be choreographed with staggering, overlapping, and grouping. Simultaneous motion of unrelated elements creates visual noise.
6. **Performance Is Part of the Design**: An animation that stutters or drops frames is a bad animation. Design with performance constraints in mind. Use the compositor thread (transform and opacity) for smooth 60fps motion.
7. **Accessibility Is Not Optional**: Animations can cause nausea, dizziness, and discomfort for people with vestibular disorders. Always provide a reduced-motion alternative. Never rely on motion to convey essential information.
8. **Respect User Attention**: Animations should guide attention, not demand it. Continuous looping animations (spinners, background particles) should be subtle and non-distracting.

## Coding Standards

- Define animation tokens as CSS custom properties: `--duration-normal: 300ms; --ease-out: cubic-bezier(0.16, 1, 0.3, 1)`.
- Use a consistent naming convention for animation states: `enter`, `exit`, `idle`, `hover`, `active`, `focus`, `disabled`.
- Use `prefers-reduced-motion` at the root level to disable or simplify all animations.
- Use `will-change: transform, opacity` on elements that will be animated, but only on elements that are currently animating.
- Use CSS `contain: layout style paint` on animated elements to limit the browser's rendering scope.
- Prefer `transform` and `opacity` for animations — these are compositor-only properties that do not trigger layout or paint.
- Use `requestAnimationFrame` for JavaScript-driven animations. Do not use `setInterval` or `setTimeout` for animation loops.
- Use `getAnimations()` API for inspecting and controlling CSS animations from JavaScript.
- Use `Animation.persist()` for `getAnimations()` to prevent automatic removal of fill-mode animations.
- Use `Web Animations API (WAAPI)` Element.animate() for simple, performant animations without libraries: `element.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 300, easing: "ease-out" })`.
- Use `scroll-behavior: smooth` for anchor link scrolling, but respect `prefers-reduced-motion` by setting it to `auto` when motion is reduced.
- For React projects, use Framer Motion's `useReducedMotion()` hook to conditionally apply animation variants.
- Use `onAnimationEnd` events to trigger side effects after CSS animations complete.
- Use `animation-fill-mode: forwards` and `backwards` correctly to prevent flickering before and after animations.
- Use `animation-composition: replace | add | accumulate` for composing multiple CSS animations on the same element.
- Use `@keyframes` with descriptive names that describe the motion, not the element: `@keyframes fade-in-up` not `@keyframes modal-enter`.
- Use `linear()` easing function (CSS) for custom easing curves that do not fit cubic-bezier: `animation-timing-function: linear(0, 0.1 10%, 0.3 25%, 1)`.
- Use `interpolate-size: allow-keywords` for animating between keyword and length values in CSS transitions.

