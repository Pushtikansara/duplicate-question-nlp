---
name: threejs
description: Use when creating 3D graphics, WebGL applications, 3D visualizations, or interactive 3D experiences with Three.js.
---

# Three.js Skill

## Instructions

1. Install Three.js: `npm install three`. For TypeScript types: `npm install -D @types/three`.
2. Create a basic scene: `const scene = new THREE.Scene(); const camera = new THREE.PerspectiveCamera(75, width/height, 0.1, 1000); const renderer = new THREE.WebGLRenderer({ antialias: true })`.
3. Append the renderer's DOM element: `document.body.appendChild(renderer.domElement)`. Set its size with `renderer.setSize(window.innerWidth, window.innerHeight)`.
4. Create geometry and material, then combine into a mesh: `const geometry = new THREE.BoxGeometry(1, 1, 1); const material = new THREE.MeshStandardMaterial({ color: 0x00ff00 }); const cube = new THREE.Mesh(geometry, material); scene.add(cube)`.
5. Add lighting to make materials visible: `const ambientLight = new THREE.AmbientLight(0xffffff, 0.5); scene.add(ambientLight); const directionalLight = new THREE.DirectionalLight(0xffffff, 1); directionalLight.position.set(5, 5, 5); scene.add(directionalLight)`.
6. Create an animation loop using `requestAnimationFrame` that updates objects and renders the scene: `function animate() { requestAnimationFrame(animate); cube.rotation.x += 0.01; renderer.render(scene, camera); }`.
7. Use `OrbitControls` for camera interaction: `import { OrbitControls } from "three/addons/controls/OrbitControls.js"; const controls = new OrbitControls(camera, renderer.domElement)`.
8. Handle window resize: `window.addEventListener("resize", () => { camera.aspect = window.innerWidth / window.innerHeight; camera.updateProjectionMatrix(); renderer.setSize(window.innerWidth, window.innerHeight); })`.
9. Use `THREE.Group` for grouping objects: apply transformations to the group to affect all children collectively.
10. Import 3D models using GLTF/GLB format with `GLTFLoader`: `import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js"`.
11. Use textures with `THREE.TextureLoader`: `const texture = new THREE.TextureLoader().load("path/to/texture.jpg")`.
12. Use `PointsMaterial` and `Points` for particle systems: `const particles = new THREE.Points(geometry, material)`.
13. Use shaders with `ShaderMaterial` for custom visual effects: vertex shaders manipulate geometry, fragment shaders manipulate pixels.
14. Use `Raycaster` for mouse/touch interaction: detect which 3D objects the user is pointing at.
15. Use `THREE.Fog` or `THREE.FogExp2` for atmospheric depth effects.
16. Optimize performance with LODs (Level of Detail), frustum culling, geometry merging, and instancing.
17. Use `RenderTarget` for offscreen rendering and post-processing effects.
18. Use post-processing pipeline via `EffectComposer` from three/addons: add passes like `UnrealBloomPass`, `GlitchPass`, `FilmPass`.
19. Use Environment maps (HDR/EXR) for realistic reflections and lighting with `HDRLoader` or `RGBELoader`.
20. Use `AnimationMixer` and `AnimationAction` for skeletal animations on loaded GLTF models.

## Examples

### Basic Scene Setup
```javascript
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1a2e);

const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 2, 5);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
document.body.appendChild(renderer.domElement);

// Lights
const ambient = new THREE.AmbientLight(0xffffff, 0.5);
scene.add(ambient);

const directional = new THREE.DirectionalLight(0xffffff, 1);
directional.position.set(5, 10, 7);
directional.castShadow = true;
scene.add(directional);

// Object
const geometry = new THREE.TorusKnotGeometry(1, 0.3, 100, 16);
const material = new THREE.MeshStandardMaterial({
  color: 0x6366f1,
  roughness: 0.3,
  metalness: 0.8,
});
const mesh = new THREE.Mesh(geometry, material);
mesh.castShadow = true;
scene.add(mesh);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

// Animation
function animate() {
  requestAnimationFrame(animate);
  mesh.rotation.x += 0.005;
  mesh.rotation.y += 0.01;
  controls.update();
  renderer.render(scene, camera);
}
animate();

// Resize
window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});
```

### Loading a GLTF Model
```javascript
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";

const loader = new GLTFLoader();
const dracoLoader = new DRACOLoader();
dracoLoader.setDecoderPath("https://www.gstatic.com/draco/versioned/decoders/1.5.6/");
loader.setDRACOLoader(dracoLoader);

loader.load(
  "/models/scene.glb",
  (gltf) => {
    const model = gltf.scene;
    model.scale.set(1, 1, 1);
    scene.add(model);

    // Play animations if present
    const mixer = new THREE.AnimationMixer(model);
    gltf.animations.forEach((clip) => {
      const action = mixer.clipAction(clip);
      action.play();
    });
  },
  (progress) => {
    console.log(`Loading: ${(progress.loaded / progress.total * 100).toFixed(0)}%`);
  },
  (error) => {
    console.error("Error loading model:", error);
  }
);
```

### Particle System
```javascript
import * as THREE from "three";

function createParticles(count = 5000) {
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);

  for (let i = 0; i < count * 3; i += 3) {
    positions[i] = (Math.random() - 0.5) * 50;
    positions[i + 1] = (Math.random() - 0.5) * 50;
    positions[i + 2] = (Math.random() - 0.5) * 50;

    colors[i] = Math.random();
    colors[i + 1] = Math.random();
    colors[i + 2] = Math.random();
  }

  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));

  const material = new THREE.PointsMaterial({
    size: 0.1,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    blending: THREE.AdditiveBlending,
    sizeAttenuation: true,
  });

  return new THREE.Points(geometry, material);
}
```

### Raycaster Mouse Interaction
```javascript
import * as THREE from "three";

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const objects = []; // Array of meshes to interact with

window.addEventListener("pointermove", (event) => {
  pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
  pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;

  raycaster.setFromCamera(pointer, camera);
  const intersects = raycaster.intersectObjects(objects);

  if (intersects.length > 0) {
    const first = intersects[0].object;
    first.material.emissive.setHex(0x444444);
    document.body.style.cursor = "pointer";
  } else {
    objects.forEach((obj) => obj.material.emissive.setHex(0x000000));
    document.body.style.cursor = "default";
  }
});

window.addEventListener("click", (event) => {
  pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
  pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;

  raycaster.setFromCamera(pointer, camera);
  const intersects = raycaster.intersectObjects(objects);

  if (intersects.length > 0) {
    console.log("Clicked:", intersects[0].object.name);
  }
});
```

### Post-Processing with EffectComposer
```javascript
import * as THREE from "three";
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";

const composer = new EffectComposer(renderer);
const renderPass = new RenderPass(scene, camera);
composer.addPass(renderPass);

const bloomPass = new UnrealBloomPass(
  new THREE.Vector2(window.innerWidth, window.innerHeight),
  0.5, // bloom strength
  0.4, // bloom radius
  0.85 // bloom threshold
);
composer.addPass(bloomPass);

composer.addPass(new OutputPass());

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  composer.render();
}
```

### Custom ShaderMaterial
```glsl
// Vertex Shader
varying vec2 vUv;
varying vec3 vPosition;
void main() {
  vUv = uv;
  vPosition = position;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
```
```glsl
// Fragment Shader
uniform vec3 uColor;
uniform float uTime;
varying vec2 vUv;

void main() {
  float wave = sin(vUv.x * 20.0 + uTime) * 0.5 + 0.5;
  float glow = 1.0 - abs(vUv.y - 0.5) * 2.0;
  vec3 color = uColor * (0.5 + wave * 0.5) * (0.3 + glow * 0.7);
  gl_FragColor = vec4(color, 1.0);
}
```
```javascript
const material = new THREE.ShaderMaterial({
  uniforms: {
    uColor: { value: new THREE.Color(0x6366f1) },
    uTime: { value: 0 },
  },
  vertexShader: vertexShader,
  fragmentShader: fragmentShader,
  side: THREE.DoubleSide,
  transparent: true,
});
```

## Best Practices

- Use `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))` to cap pixel ratio at 2 for performance on high-DPI screens.
- Use `BufferGeometry` (not `Geometry`, which was removed in r125). Always use typed arrays for position, normal, and UV data.
- Reuse geometries and materials when possible. Creating new geometries every frame will cause GC pressure and frame drops.
- Use `InstancedMesh` for rendering many copies of the same geometry (trees, particles, crowd).
- Use `LOD` (Level of Detail) for complex objects that are far from the camera.
- Use `FrustumCulled = true` (default) to let Three.js skip rendering objects outside the camera view.
- Use `Object3D.visible = false` or `scene.remove(obj)` to completely disable rendering of hidden objects.
- Use `GeometryUtils.mergeBufferGeometries` for merging static geometry into a single draw call.
- Use `DRACOLoader` for compressed GLTF files — significantly reduces load times for complex 3D models.
- Use HDR environments for realistic PBR lighting: `PMREMGenerator` + `RGBELoader` for .hdr files.
- Use `TextureLoader` with `texture.colorSpace = THREE.SRGBColorSpace` for proper color rendering.
- Use `MeshPhysicalMaterial` for production-grade rendering: it supports clearcoat, sheen, transmission, and anisotropy.
- Use `useFrame` in React Three Fiber (R3F) for per-frame updates instead of manual requestAnimationFrame.
- Use `Suspense` with `@react-three/drei`'s `useGLTF` for declarative model loading in React.
- Use `Leva` (GUI) for debugging Three.js parameters in development.
- Use `Stats.js` for monitoring FPS and draw calls during development.

## Common Mistakes

- Not setting `renderer.setSize()` on window resize, causing stretched or distorted rendering.
- Creating geometry and materials inside the animation loop, causing massive garbage collection overhead.
- Using `requestAnimationFrame` multiple times (nested) instead of a single animation loop.
- Forgetting to call `controls.update()` when using damping in OrbitControls.
- Not disposing of geometries, materials, and textures when removing objects from the scene, causing memory leaks.
- Using `MeshStandardMaterial` without providing any lights — standard material requires lighting to be visible.
- Loading textures without handling cross-origin issues when using external images.
- Setting `renderer.setPixelRatio(1)` on high-DPI displays, resulting in blurry rendering.
- Using `THREE.Mesh` for line rendering — use `THREE.Line` and `THREE.LineBasicMaterial` instead.
- Not normalizing normals after modifying BufferGeometry positions.
- Using `scale.set()` on every frame instead of modifying the object once — prefer matrixAutoUpdate with cached matrices.
- Forgetting to set `renderer.outputColorSpace = THREE.SRGBColorSpace` for correct color output.
- Using `THREE.SphereGeometry` with unnecessarily high segment counts for small or distant spheres.
- Not handling the case where WebGL is not supported — always provide a fallback message or 2D version.
- Using `renderer.shadowMap.enabled = true` without setting `shadow.castShadow` and `shadow.receiveShadow` on individual objects.
- Not using `Array.isArray()` before calling `raycaster.intersectObjects()` on a single object.

## Libraries and Tools

- **three**: Core Three.js library.
- **@react-three/fiber (R3F)**: React renderer for Three.js. Declarative, component-driven 3D scenes.
- **@react-three/drei**: Utility library for R3F with helpers (OrbitControls, useGLTF, Text, Html, Float, ScrollControls).
- **@react-three/postprocessing**: Post-processing effects for R3F.
- **@react-three/xr**: VR/AR support for R3F.
- **@react-three/cannon**: Physics engine integration for R3F.
- **@types/three**: TypeScript type definitions for Three.js.
- **Blender**: 3D modeling software. Export models as GLTF/GLB for use in Three.js.
- **Three.js Editor**: Visual editor for creating Three.js scenes.
- **Spline**: Design tool for 3D web experiences (exports to Three.js-compatible code).
- **Vectary**: Browser-based 3D design tool with Three.js export.
- **Polycam**: Photogrammetry app for creating 3D models from photos.
- **Ready Player Me**: Avatar system with Three.js-compatible exports.
- **Sketchfab**: 3D model marketplace. Download GLTF/GLB models.
- **AmbientCG**: Free PBR textures for Three.js materials.
- **Poly Haven**: Free HDR environments and PBR textures.
- **three-vite-template**: Vite starter template for Three.js projects.
- **TroisJS**: Vue 3 component library for Three.js.
- **Threlte**: Svelte 5 component library for Three.js.

## Design Principles

1. **Performance Budget**: 3D graphics are computationally expensive. Define a target framerate (60fps) and optimize to stay within budget. Use draw calls, polygon count, and texture memory as metrics.
2. **Progressive Disclosure**: Start with a simple, fast-loading 3D experience and progressively enhance with more detail as the browser and device capabilities allow.
3. **User Control**: Users should always be in control of 3D interactions. Provide OrbitControls or similar for camera manipulation. Do not force unwanted camera movement.
4. **Visual Hierarchy**: Guide the user's eye through the 3D scene using lighting, color, depth of field, and animation. Not everything in the scene should compete for attention.
5. **Physical Plausibility**: Even stylized 3D scenes should follow physical rules (gravity, momentum, light behavior) unless intentional stylization dictates otherwise.
6. **Accessibility in 3D**: Provide alternatives for 3D content. Screen readers cannot navigate 3D scenes. Offer 2D fallbacks or text descriptions of 3D content.
7. **Mobile Consideration**: Many users will view 3D on mobile devices with less GPU power and smaller screens. Reduce polygon counts, texture sizes, and effects for mobile.

## Coding Standards

- Use ES modules: `import * as THREE from "three"` and `import { OrbitControls } from "three/addons/controls/OrbitControls.js"`.
- Use `const` for Three.js objects that should not be reassigned (renderer, scene, camera).
- Name Three.js objects with `Three` prefix convention or context-appropriate naming: `scene`, `camera`, `renderer`, `mesh`, `material`, `geometry`.
- Use `object3D.name` property for debugging and raycaster identification: `mesh.name = "ground-plane"`.
- Organize scenes with groups: `const environment = new THREE.Group(); scene.add(environment)`.
- Use `eventDispatcher` pattern for Three.js event handling: `renderer.domElement.addEventListener(...)`.
- Dispose unused resources: `geometry.dispose(); material.dispose(); texture.dispose()`.
- Use `Object3D.traverse()` to apply operations to all children: `model.traverse((child) => { if (child.isMesh) child.castShadow = true; })`.
- Use `Vector3`, `Quaternion`, `Euler`, and `Matrix4` for mathematical operations. Avoid manual math where Three.js provides utilities.
- Use `.clone()` when reusing materials and geometries that need independent properties: `material.clone()`.
- Use `Color.setHex()`, `Color.setHSL()`, or `Color.set()` for color management. Never construct `THREE.Color` directly in loops.
- Use `getWorldPosition`, `getWorldQuaternion`, `getWorldScale` for accurate world-space transforms.
- Use `Box3` and `Sphere` for bounding volume calculations and frustum culling.
- Use `Raycaster` for all hit-testing. Do not implement manual ray-triangle intersection.
- Use `Clock` for time-based animations: `const delta = clock.getDelta(); mixer.update(delta)`.
- Use `MathUtils` for common math operations: `lerp`, `clamp`, `mapLinear`, `randInt`, `randFloat`.
- Use `PMREMGenerator` for environment map processing: do not load HDR directly as a texture.
- Use `SRGBColorSpace` on textures and `outputColorSpace` on renderer for correct color rendering.
- Use `EquirectangularReflectionMapping` for environment maps on scene.background for skydomes.

