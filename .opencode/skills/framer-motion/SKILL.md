---
name: framer-motion
description: Use when adding animations, transitions, gestures, and motion design in React applications with Framer Motion.
---

# Framer Motion Skill

## Instructions

1. Install Framer Motion: `npm install framer-motion`. The library is a single dependency with no other required packages.
2. Import the `motion` object: `import { motion } from "framer-motion"`. Prepend `motion.` to any HTML or SVG element to make it animatable.
3. Use the `animate` prop to define the target state of an animation: `<motion.div animate={{ x: 100, opacity: 1 }} />`.
4. Use the `initial` prop to set the starting state before the animation begins: `<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} />`.
5. Define reusable animation configurations using `variants`: named sets of animation states that can be referenced by `initial`, `animate`, `whileHover`, `whileTap`, etc.
6. Use `transition` prop to control timing: `transition={{ duration: 0.5, ease: "easeInOut", delay: 0.2 }}`.
7. Use `whileHover`, `whileTap`, `whileFocus`, `whileDrag`, `whileInView` for interaction-driven animations.
8. Use `AnimatePresence` to animate components when they mount or unmount from the React tree. Wrap the conditional rendering block.
9. Use `layout` prop for layout animations — Framer Motion automatically animates position and size changes when the layout shifts.
10. Use `useScroll` and `useTransform` for scroll-linked animations: `const { scrollY } = useScroll(); const y = useTransform(scrollY, [0, 500], [0, -200])`.
11. Use `useMotionValue` for reactive values that drive animations without triggering React re-renders.
12. Use `useSpring` to create spring-based motion values: `const x = useSpring(0, { stiffness: 300, damping: 30 })`.
13. Use `useDragControls` for complex drag interactions and `drag` prop for basic drag behavior: `<motion.div drag dragConstraints={{ left: 0, right: 300 }} />`.
14. Use `useMotionValueEvent` to listen to changes in motion values: `useMotionValueEvent(scrollY, "change", (latest) => {...})`.
15. Use `gesture` props: `onDrag`, `onDragEnd`, `onPan`, `onPanEnd`, `onHoverStart`, `onHoverEnd`.
16. Use `viewport` options with `whileInView`: `whileInView={{ opacity: 1 }} viewport={{ once: true, margin: "-100px" }}`.
17. Use SVG animation with `motion.path`, `motion.circle`, `motion.rect`, etc. Animate `pathLength`, `pathOffset`, `pathSpacing`.
18. Use `useAnimate` hook for imperative animations: `const [scope, animate] = useAnimate(); animate("li", { opacity: 1 }, { stagger: 0.1 })`.
19. Use `motion.create(MotionComponent)` to create custom motion components from any React component.
20. Use `Reorder` group for drag-to-reorder lists: `import { Reorder } from "framer-motion"`.

## Examples

### Basic Fade-In on Mount
```tsx
import { motion } from "framer-motion";

export function FadeIn() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <h1>Hello, World</h1>
    </motion.div>
  );
}
```

### Staggered List Animation with Variants
```tsx
import { motion } from "framer-motion";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1, delayChildren: 0.3 },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

export function StaggeredList() {
  return (
    <motion.ul variants={container} initial="hidden" animate="show">
      {items.map((item) => (
        <motion.li key={item.id} variants={item}>
          {item.name}
        </motion.li>
      ))}
    </motion.ul>
  );
}
```

### AnimatePresence for Exit Animations
```tsx
import { motion, AnimatePresence } from "framer-motion";

export function Notification({ show }: { show: boolean }) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, x: 100, scale: 0.9 }}
          animate={{ opacity: 1, x: 0, scale: 1 }}
          exit={{ opacity: 0, x: 100, scale: 0.9 }}
          transition={{ type: "spring", stiffness: 300, damping: 25 }}
        >
          Notification content
        </motion.div>
      )}
    </AnimatePresence>
  );
}
```

### Layout Animation (Auto-Animate Layout Changes)
```tsx
import { motion } from "framer-motion";
import { useState } from "react";

export function LayoutAnimation() {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <motion.div
      layout
      onClick={() => setIsExpanded(!isExpanded)}
      className={isExpanded ? "w-96 h-96" : "w-48 h-48"}
      style={{ backgroundColor: "var(--primary)" }}
      transition={{ type: "spring", stiffness: 300, damping: 25 }}
    >
      Click to toggle size
    </motion.div>
  );
}
```

### Scroll-Triggered Animation
```tsx
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";

export function ScrollAnimation() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });

  const scale = useTransform(scrollYProgress, [0, 1], [0.8, 1]);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [0, 1]);

  return (
    <motion.div ref={ref} style={{ scale, opacity }}>
      Content fades in and scales up as you scroll
    </motion.div>
  );
}
```

### Drag with Constraints
```tsx
import { motion } from "framer-motion";

export function DraggableCard() {
  return (
    <motion.div
      drag
      dragConstraints={{ left: -100, right: 100, top: -100, bottom: 100 }}
      dragElastic={0.1}
      whileDrag={{ scale: 1.05, boxShadow: "0 10px 30px rgba(0,0,0,0.2)" }}
      className="w-32 h-32 bg-blue-500 rounded-lg cursor-grab active:cursor-grabbing"
    />
  );
}
```

### SVG Path Drawing Animation
```tsx
import { motion } from "framer-motion";

export function SvgDraw() {
  return (
    <motion.svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <motion.circle
        cx="100"
        cy="100"
        r="80"
        stroke="var(--primary)"
        strokeWidth="4"
        fill="transparent"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 2, ease: "easeInOut" }}
      />
      <motion.path
        d="M 60 100 L 90 130 L 140 70"
        stroke="var(--primary)"
        strokeWidth="4"
        fill="transparent"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1.5, delay: 1, ease: "easeInOut" }}
      />
    </motion.svg>
  );
}
```

### Keyframes Animation
```tsx
<motion.div
  animate={{
    scale: [1, 1.1, 1],
    rotate: [0, 360, 0],
    borderRadius: ["0%", "50%", "0%"],
  }}
  transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
/>
```

### Shared Layout Animation (AnimateSharedLayout)
```tsx
import { motion } from "framer-motion";
import { useState } from "react";

export function SharedLayout() {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  return (
    <div className="grid grid-cols-3 gap-4">
      {items.map((item) => (
        <motion.div
          key={item.id}
          layoutId={`card-${item.id}`}
          onClick={() => setSelectedId(item.id === selectedId ? null : item.id)}
          className="bg-white rounded-lg p-4 shadow cursor-pointer"
        >
          {selectedId === item.id ? <ExpandedView item={item} /> : <CompactView item={item} />}
        </motion.div>
      ))}
    </div>
  );
}
```

## Best Practices

- Use `variants` for organizing complex animations. They keep animation logic declarative and reusable.
- Prefer `useTransform` and `useMotionValue` over React state for animation-driven values to avoid re-renders.
- Use `layout` animations instead of calculating position changes manually. Framer Motion handles the FLIP technique internally.
- Use `AnimatePresence` with `mode="wait"` to wait for exiting animations to complete before mounting new content.
- Use `spring` transitions for natural-feeling motion: `transition={{ type: "spring", stiffness: 300, damping: 25 }}`.
- Use `ease` transitions for UI animations that should feel precise: `transition={{ duration: 0.3, ease: [0.25, 0.1, 0.25, 1] }}`.
- Use `once: true` in `viewport` for scroll-triggered animations that should only play once.
- Use `useReducedMotion` hook to respect the user's `prefers-reduced-motion` setting: `const shouldReduceMotion = useReducedMotion()`.
- Use `DragControls` for complex drag scenarios where multiple elements should be draggable.
- Use `layoutDependency` to prevent layout animations on unrelated state changes.
- Use `onAnimationComplete` to trigger side effects after an animation finishes.
- Animate `opacity` and `transform` properties for best performance. These are compositor-only properties and do not trigger layout or paint.
- Avoid animating `width`, `height`, `top`, `left` directly; use `scale` or `layout` instead for better performance.
- Use `willChange` prop (Framer Motion sets this automatically) for GPU-accelerated animations.
- Keep animation durations under 300ms for UI transitions and 600ms for emphasis animations.
- Use `staggerChildren` for choreographed list or grid entrances with a consistent rhythm.

## Common Mistakes

- Animating `height` or `width` directly instead of using `scale` or the `layout` prop, causing layout thrashing.
- Not wrapping conditional renders with `AnimatePresence`, causing elements to disappear without an exit animation.
- Creating new variant objects on every render (inside the component body), breaking referential equality and causing re-renders.
- Using `animate` prop with objects that change reference on every render, causing animations to restart.
- Forgetting to set `mode="popLayout"` or `mode="wait"` on `AnimatePresence`, causing layout jumps.
- Using `useMotionValue` when React state would suffice, prematurely optimizing without understanding the cost.
- Not handling `prefers-reduced-motion`, causing discomfort for users with vestibular motion disorders.
- Using `drag` without `dragConstraints`, allowing elements to be dragged off-screen.
- Animating multiple properties simultaneously that cause layout thrashing (e.g., `width` + `left` + `transform`).
- Using `position: absolute` with layout animations without proper layout containers.
- Nesting `motion` components with conflicting `layout` updates, causing jarring jumps.
- Overusing `repeat: Infinity` on non-trivial animations, causing continuous CPU/GPU usage and battery drain.
- Using `onDrag` handlers that trigger expensive React state updates on every pixel of drag.
- Not using `layoutScroll` when layout animations need to account for scroll position.
- Applying `whileHover` on mobile without fallback behavior — hover does not exist on touch devices.

## Libraries and Tools

- **framer-motion**: The core animation library for React.
- **motion**: The standalone (non-React) version of Framer Motion for vanilla JS projects.
- **React**: Framer Motion is a React library and requires React 18+.
- **Framer**: The visual design tool that integrates with Framer Motion for handoff.
- **Lottie**: JSON-based animation format that can be used alongside Framer Motion for complex pre-authored animations.
- **react-spring**: Alternative physics-based animation library (evaluate tradeoffs if already using Framer Motion).
- **GSAP**: High-performance animation library for complex timeline-based animations (complementary to Framer Motion).
- **React Intersection Observer**: For scroll detection (native `IntersectionObserver`). Framer Motion's `useInView` wraps this.
- **React UseGesture**: Gesture handling library that can complement Framer Motion's gesture system.
- **Framer Motion DevTools**: Browser extension for debugging Framer Motion animations.
- **Remotion**: Programmatic video generation with React — uses Framer Motion concepts for frame-based animation.
- **Motion One**: Lightweight animation library by the Framer Motion team for simpler use cases.

## Design Principles

1. **Declarative Motion**: Animations should be declared alongside the component they animate, not in separate files. Keep motion logic co-located with presentation.
2. **Natural Motion through Physics**: Use spring animations for natural-feeling movement. The physical model (stiffness, damping, mass) produces more organic motion than linear or ease-based transitions.
3. **Performance-Conscious**: Framer Motion automatically optimizes which properties animate on the compositor thread. Avoid manual optimization that complicates code without measurable benefit.
4. **Accessibility-First**: Always respect `prefers-reduced-motion`. Animations should enhance the experience, not cause discomfort or distraction.
5. **Progressive Enhancement**: Animations should never block content from being visible. Content should appear immediately and animate as enhancement.
6. **Meaningful Motion**: Every animation should serve a purpose: provide feedback, guide attention, show relationships, or provide context. Decorative animation should be subtle and restrained.
7. **Layout as Animation**: Layout changes should animate smoothly. The `layout` prop treats layout as a first-class animated property, making state-driven layout changes fluid.
8. **Composability**: Animate individual components, not entire pages. Compose animation behaviors from small, focused motion components.

## Coding Standards

- Define `variants` objects outside the component or use `useMemo` to prevent referential changes on re-renders.
- Use TypeScript: `import { motion, type Variants, type Transition } from "framer-motion"`.
- Prefer camelCase for variant names: `hidden`, `visible`, `hover`, `tap`.
- Use `initial={false}` for components that should not animate on initial mount but should animate on subsequent updates.
- Use `layoutId` for shared layout animations between different components (route transitions, list/grid toggle).
- Use `key` prop with `AnimatePresence` to properly identify and animate elements entering/leaving.
- Set `removeFromTree` on `AnimatePresence` to `false` (default) to keep exited elements in the DOM during exit animation.
- Use `onUpdate` callback instead of `useMotionValueEvent` for simple value logging or side effects.
- Use `motion.create()` for third-party or custom components: `const MotionComponent = motion(Component)`.
- Use `useAnimationControls()` for imperative animation control: `const controls = useAnimationControls(); controls.start("visible")`.
- Use `useCycle` for cycling through animation states: `const [state, cycle] = useCycle("hidden", "visible")`.
- Use `useWillChange` to opt into automatic `will-change` management for hand-optimized scenarios.
- Handle reduced motion: `const prefersReduced = useReducedMotion(); const variants = prefersReduced ? reducedVariants : fullVariants`.
- Use `transition` as a prop on `motion` elements, not inside `animate` objects, for shared transition configuration.
- Use `custom` prop with variants to pass dynamic data: `variants={itemVariants} custom={index}` and access `custom` in variant functions.
- Keep animation durations consistent: 200-300ms for micro-interactions, 300-500ms for element transitions, 500-800ms for emphasis.
- Use `onDragEnd` with `velocity` to implement throw/snap gestures: `onDragEnd={(_, info) => handleThrow(info.velocity.x)}`.
- Use `layoutScroll` when a layout animation's target is in a scrollable container.
