---
name: gsap
description: Use when creating high-performance web animations with GSAP (GreenSock Animation Platform). Covers timelines, tweens, scroll-triggered animations, and SVG animation.
---

# GSAP (GreenSock Animation Platform) Skill

## Instructions

1. Install GSAP: `npm install gsap`. For scroll-triggered animations, also install the ScrollTrigger plugin (included in the core package): `import { ScrollTrigger } from "gsap/ScrollTrigger"`.
2. Register GSAP plugins before use: `gsap.registerPlugin(ScrollTrigger, Draggable, MotionPathPlugin, TextPlugin)`.
3. Create basic animations with `gsap.to()`: `gsap.to(".element", { x: 100, duration: 1, opacity: 0.5 })`.
4. Use `gsap.from()` to animate from a specified state to the current state: `gsap.from(".element", { y: -50, opacity: 0, duration: 0.8 })`.
5. Use `gsap.fromTo()` for full control over start and end states: `gsap.fromTo(".element", { x: -100 }, { x: 100, duration: 1 })`.
6. Build complex, sequenced animations with `gsap.timeline()`: `const tl = gsap.timeline({ defaults: { duration: 0.5 } }); tl.to(".a", { x: 100 }).to(".b", { y: 50 }, "-=0.3")`.
7. Use ScrollTrigger for scroll-driven animations: `ScrollTrigger.create({ trigger: ".section", start: "top center", end: "bottom top", animation: tl, scrub: true })`.
8. Use GSAP's easing functions: `power1.inOut`, `power2.out`, `power3.in`, `power4.inOut`, `back.out(1.7)`, `elastic.out(1, 0.5)`, `bounce.out`, `steps(12)`.
9. Animate CSS variables: `gsap.to(":root", { "--primary-hue": 200, duration: 2 })`.
10. Animate SVG elements by targeting SVG attributes: `gsap.to("circle", { attr: { r: 50 }, duration: 1 })`.
11. Use `stagger` for animating multiple elements with a delay between each: `gsap.to(".items", { y: 0, stagger: 0.1, duration: 0.4 })`.
12. Use `keyframes` syntax for complex multi-step animations: `gsap.to(".element", { keyframes: [{ x: 100 }, { y: 100 }, { x: 0, y: 0 }], duration: 3 })`.
13. Use `gsap.matchMedia()` for responsive animations that behave differently at different viewport sizes.
14. Use `gsap.context()` for scoped animations that can be easily reverted (useful in React's `useEffect` cleanup).
15. Use `gsap.utils` helpers: `gsap.utils.clamp(0, 100)`, `gsap.utils.mapRange(0, 100, 0, 1)`, `gsap.utils.interpolate`.
16. Use `gsap.quickTo()` for high-performance mouse-following animations: `const xTo = gsap.quickTo(".element", "x", { duration: 0.4 })`.
17. Use `Draggable` plugin for drag interactions: `Draggable.create(".element", { type: "x,y", bounds: ".container" })`.
18. Use `MotionPathPlugin` for animating along SVG paths: `gsap.to(".element", { motionPath: { path: "#path", align: "#path" } })`.
19. Use `Flip` plugin for FLIP (First, Last, Invert, Play) animations when DOM layout changes: `const state = Flip.getState(".items"); /* change DOM */; Flip.from(state, { duration: 0.5 })`.
20. Use `ScrollTrigger` pinning for sticky sections: `ScrollTrigger.create({ trigger: ".panel", pin: true, start: "top top", end: "bottom top" })`.

## Examples

### Basic Animation
```javascript
import gsap from "gsap";

// Fade and slide in
gsap.from(".hero-title", {
  y: 60,
  opacity: 0,
  duration: 1,
  ease: "power3.out",
  delay: 0.2,
});

gsap.from(".hero-subtitle", {
  y: 40,
  opacity: 0,
  duration: 1,
  ease: "power3.out",
  delay: 0.4,
});
```

### Timeline with Stagger
```javascript
import gsap from "gsap";

const tl = gsap.timeline({ defaults: { duration: 0.6, ease: "power2.out" } });

tl.from(".header", { y: -100, opacity: 0 })
  .from(".logo", { scale: 0, rotation: -180 }, "-=0.3")
  .from(".nav-item", { y: -20, opacity: 0, stagger: 0.1 }, "-=0.4")
  .from(".hero-content", { y: 50, opacity: 0 }, "-=0.2")
  .from(".cta-button", { scale: 0.8, opacity: 0 }, "-=0.3");
```

### ScrollTrigger Parallax
```javascript
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

// Parallax section
gsap.to(".parallax-bg", {
  yPercent: -30,
  ease: "none",
  scrollTrigger: {
    trigger: ".parallax-section",
    start: "top bottom",
    end: "bottom top",
    scrub: true,
  },
});

// Reveal on scroll
gsap.from(".reveal-item", {
  y: 80,
  opacity: 0,
  rotation: 5,
  stagger: 0.15,
  duration: 1,
  ease: "power2.out",
  scrollTrigger: {
    trigger: ".reveal-section",
    start: "top 80%",
    end: "bottom 20%",
    toggleActions: "play none none reverse",
  },
});
```

### ScrollTrigger Pin Panel (Horizontal Scroll)
```javascript
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const panels = gsap.utils.toArray(".panel");
const wrapper = document.querySelector(".horizontal-wrapper");

const tl = gsap.timeline({
  scrollTrigger: {
    trigger: wrapper,
    pin: true,
    scrub: 1,
    start: "top top",
    end: () => `+=${wrapper.scrollWidth}`,
    invalidateOnRefresh: true,
  },
});

tl.to(panels, {
  xPercent: -100 * (panels.length - 1),
  ease: "none",
});
```

### SVG Animation
```javascript
import gsap from "gsap";
import { MotionPathPlugin } from "gsap/MotionPathPlugin";

gsap.registerPlugin(MotionPathPlugin);

// Draw SVG path
gsap.to(".path-line", {
  strokeDashoffset: 0,
  duration: 2,
  ease: "power2.inOut",
});

// Animate element along path
gsap.to(".flying-object", {
  duration: 4,
  ease: "power1.inOut",
  motionPath: {
    path: "#flight-path",
    align: "#flight-path",
    alignOrigin: [0.5, 0.5],
    autoRotate: true,
  },
  repeat: -1,
  yoyo: true,
});
```

### Draggable with Scrolling
```javascript
import gsap from "gsap";
import { Draggable } from "gsap/Draggable";
import { InertiaPlugin } from "gsap/InertiaPlugin";

gsap.registerPlugin(Draggable, InertiaPlugin);

Draggable.create(".carousel-track", {
  type: "x",
  bounds: ".carousel-container",
  inertia: true,
  edgeResistance: 0.65,
});
```

### Responsive Animations with matchMedia
```javascript
import gsap from "gsap";

const mm = gsap.matchMedia();

mm.add("(min-width: 1024px)", () => {
  const tl = gsap.timeline({
    scrollTrigger: {
      trigger: ".section",
      start: "top center",
      scrub: true,
    },
  });
  tl.to(".element", { x: 300, rotation: 360 });
  return () => tl.revert();
});

mm.add("(max-width: 1023px)", () => {
  // Simpler animation for mobile
  gsap.from(".element", { opacity: 0, y: 30 });
});
```

### FLIP Animation
```javascript
import gsap from "gsap";
import { Flip } from "gsap/Flip";

gsap.registerPlugin(Flip);

function toggleLayout() {
  const state = Flip.getState(".cards .card");
  // DOM re-arrangement
  container.classList.toggle("grid");
  container.classList.toggle("list");

  Flip.from(state, {
    duration: 0.6,
    ease: "power2.inOut",
    stagger: 0.05,
    absolute: true,
  });
}
```

## Best Practices

- Use `gsap.context()` in React/Vue/Svelte components to scope animations and easily revert them on unmount.
- Use `gsap.matchMedia()` for viewport-specific animations to avoid checking window width in event handlers.
- Prefer `gsap.quickTo()` for high-frequency events like mouse move — it bypasses normal GSAP processing overhead.
- Use `timeline` for sequences rather than nesting callbacks. Timelines are more readable and maintainable.
- Use negative `position` parameters in timelines for overlapping animations: `.to(".a", { x: 100 }).to(".b", { y: 50 }, "-=0.3")`.
- Use `defaults` in timelines: `gsap.timeline({ defaults: { duration: 0.5, ease: "power2.out" } })`.
- Always call `ScrollTrigger.refresh()` after DOM changes that affect layout (images loading, dynamic content).
- Use `ScrollTrigger`'s `invalidateOnRefresh` option when the end position might change dynamically.
- Batch DOM reads using `gsap.utils.toArray()` for better performance.
- Use `will-change: transform` on animated elements for GPU acceleration (GSAP handles this internally in most cases).
- Kill tweens that are no longer needed: `gsap.killTweensOf(".element")` or store tween references.
- Use `immediateRender: false` when creating from/to tweens that should not immediately set the start state.
- Use `overwrite: "auto"` (default) to automatically kill conflicting tweens on the same target.
- Test ScrollTrigger animations at different scroll speeds. Use `scrub: true` for smooth, scrub-controlled animations.
- Use `ScrollTrigger`'s `markers: true` during development to debug start/end positions.

## Common Mistakes

- Not registering plugins with `gsap.registerPlugin()`, causing runtime errors when using plugin features.
- Creating GSAP animations outside of `useEffect` in React (or `onMounted` in Vue), causing them to run before the DOM is ready.
- Not cleaning up animations on component unmount: always return a cleanup function that calls `tl.revert()` or `ctx.revert()`.
- Using ScrollTrigger without calling `ScrollTrigger.refresh()` after DOM layout changes.
- Animating properties that cause layout thrashing (width, height, top, left with non-transform properties).
- Using `position: fixed` elements with ScrollTrigger pinning, causing z-index and stacking context issues.
- Setting `scrub: true` without a timeline, causing choppy animations (scrub works best with timelines).
- Using `opacity: 0` on parent elements while trying to animate children opacity — GSAP can lose track of computed values.
- Forgetting to set `overflow: hidden` on pinned containers, causing horizontal scrollbars.
- Using CSS transitions alongside GSAP animations on the same properties, causing conflicts.
- Not accounting for images loading when calculating ScrollTrigger start/end positions.
- Using `gsap.to()` with values that require browser computation (e.g., `maxHeight: "100vh"`) without fallbacks.
- Creating deeply nested timelines that are hard to debug. Keep timelines flat and modular.
- Overusing `repeat: -1` and `yoyo: true` without performance considerations for mobile devices.

## Libraries and Tools

- **gsap**: Core GSAP library. Includes TweenLite, TweenMax, TimelineLite, TimelineMax (legacy), and the unified GSAP API.
- **ScrollTrigger**: Scroll-driven animation plugin. Included in the GSAP core npm package.
- **Draggable**: Drag-and-drop interaction plugin for mouse and touch.
- **InertiaPlugin**: Momentum-based physics for Draggable and other interactions.
- **MotionPathPlugin**: Animate elements along SVG or object path data.
- **FlipPlugin**: FLIP (First, Last, Invert, Play) animation for layout changes.
- **TextPlugin**: Animate text content changes (typing effect).
- **DrawSVGPlugin**: Animate SVGs being drawn (stroke length animation).
- **MorphSVGPlugin**: Morph one SVG shape into another.
- **CustomBounce**: Create custom bounce easing curves.
- **CustomEase**: Create custom bezier easing curves visually with a GUI.
- **GSAP DevTools**: Browser extension for debugging GSAP animations.
- **GSAP Club (Shockingly Green/GreenSock)**: Premium membership for business-use license and bonus plugins.
- **GSAP Premium Plugins**: SplitText, ScrollSmoother, Observer, DrawSVG, MorphSVG, Physics2D, PhysicsProps, PixiPlugin.
- **Lenis**: Smooth scroll library that pairs well with ScrollTrigger for silky-smooth scrolling.
- **Locomotive Scroll**: Another smooth scroll library (legacy; Lenis is now preferred).
- **GreenSock Forum**: Community support and plugin documentation.

## Design Principles

1. **Performance First**: GSAP is optimized for 60fps animations using requestAnimationFrame. Always prefer animating transform and opacity properties that run on the compositor thread.
2. **Timeline-Driven Sequencing**: Complex animations should be built as timelines — sequences of tweens that can be positioned, nested, and controlled as a unit.
3. **Scroll-Driven Storytelling**: ScrollTrigger enables scroll position to drive animation progress. This creates immersive, narrative-driven scrolling experiences.
4. **Easing Is Motion Quality**: The choice of easing function defines the character of the motion. Use `power1`-`power4` for natural acceleration/deceleration, `back` for overshoot, `elastic` for bouncy emphasis, `bounce` for playful landings, and `steps` for mechanical motion.
5. **Progressive Enhancement**: Animations should work across browsers. GSAP handles browser inconsistencies, but design animations that gracefully fall back on less capable browsers.
6. **Responsive Motion**: Animations should adapt to viewport size. Use `gsap.matchMedia()` to provide different animation strategies for mobile, tablet, and desktop.
7. **Separation of Concerns**: Keep animation logic separate from business logic. Animations are presentation-layer concerns.
8. **Control and Flexibility**: GSAP gives precise control over every frame. Use this power judiciously — not every interaction needs animation.

## Coding Standards

- Always register plugins at the app entry point: `gsap.registerPlugin(ScrollTrigger, Draggable, Flip, MotionPathPlugin)`.
- In React, use `useRef` for GSAP targets and `useEffect` with cleanup for creating animations:
  ```javascript
  useEffect(() => {
    const ctx = gsap.context(() => {
      gsap.from(ref.current, { opacity: 0, y: 20 });
    });
    return () => ctx.revert();
  }, []);
  ```
- Use `gsap.utils.toArray()` for selecting multiple targets: `gsap.utils.toArray(".item").forEach(...)`.
- Prefer function-based values for responsive animations: `x: () => window.innerWidth * 0.5`.
- Use object syntax for `vars` to improve readability in complex animations.
- Use `ease: "none"` for length-based easing (used with ScrollTrigger scrub).
- Use `overwrite: "auto"` (default) to prevent conflicts between multiple tweens on the same target.
- Use `yoyo: true` with `repeat: -1` for ping-pong looping animations.
- Use `repeatRefresh: true` on ScrollTrigger for animations that need recalculating on resize.
- Use `snap` in ScrollTrigger to snap scroll positions to specific points: `snap: 1 / (sections.length - 1)`.
- Use `toggleActions: "play none none reverse"` for animations that play when scrolling down and reverse when scrolling up.
- For horizontal scroll sections, use `end: () => "+=" + document.querySelector(".wrapper").scrollWidth`.
- Use CSS `will-change: transform` on elements animated by GSAP to prepare the browser for compositing.
- Use `clearProps: "all"` when resetting elements after animation: `gsap.set(".element", { clearProps: "all" })`.
- Use `delay` and `position` parameters for fine-grained timeline control instead of nested timeouts.
