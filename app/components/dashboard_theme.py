from __future__ import annotations

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
  --bg-deep: #020203;
  --bg-base: #050506;
  --bg-elevated: #0a0a0c;
  --surface: rgba(255,255,255,0.04);
  --surface-hover: rgba(255,255,255,0.08);
  --foreground: #EDEDEF;
  --foreground-muted: #8A8F98;
  --accent: #5E6AD2;
  --accent-glow: rgba(94,106,210,0.2);
  --accent-secondary: #A78BFA;
  --border: rgba(255,255,255,0.08);
  --radius: 16px;
  --radius-sm: 10px;
  --radius-xs: 6px;
  --easing: cubic-bezier(0.16,1,0.3,1);
  --font: 'Inter', sans-serif;
  --shadow: 0 4px 24px rgba(0,0,0,0.3);
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.2);
  --success: #22C55E;
  --warning: #F59E0B;
  --error: #EF4444;
  --info: #3B82F6;
}

.stApp {
  background: var(--bg-deep) !important;
  font-family: var(--font) !important;
  color: var(--foreground) !important;
}

.main-header {
  background: linear-gradient(135deg, var(--bg-elevated) 0%, var(--bg-deep) 100%);
  border-bottom: 1px solid var(--border);
  padding: 1.5rem 2rem !important;
  margin: -3rem -1rem 1.5rem -1rem !important;
}

.main-header h1 {
  font-family: var(--font);
  font-weight: 700;
  font-size: 1.75rem;
  letter-spacing: -0.02em;
  color: var(--foreground);
  margin: 0;
}

.main-header p {
  font-family: var(--font);
  font-weight: 400;
  font-size: 0.85rem;
  color: var(--foreground-muted);
  margin: 0.25rem 0 0 0;
}

.glass-card {
  background: var(--surface);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.25rem;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s var(--easing);
}

.glass-card:hover {
  background: var(--surface-hover);
  border-color: rgba(255,255,255,0.12);
  box-shadow: var(--shadow);
}

.glass-card-sm {
  background: var(--surface);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
  transition: all 0.2s var(--easing);
}

.metric-value {
  font-family: var(--font);
  font-weight: 700;
  font-size: 1.5rem;
  color: var(--foreground);
  line-height: 1.2;
}

.metric-label {
  font-family: var(--font);
  font-weight: 400;
  font-size: 0.75rem;
  color: var(--foreground-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.accent-glow {
  color: var(--accent);
  text-shadow: 0 0 20px rgba(94,106,210,0.3);
}

.section-title {
  font-family: var(--font);
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--foreground);
  margin: 0 0 0.75rem 0;
  letter-spacing: -0.01em;
}

.section-subtitle {
  font-family: var(--font);
  font-weight: 400;
  font-size: 0.8rem;
  color: var(--foreground-muted);
  margin: -0.5rem 0 1rem 0;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.5rem;
  border-radius: 100px;
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.02em;
}

.badge-success {
  background: rgba(34,197,94,0.15);
  color: var(--success);
}

.badge-warning {
  background: rgba(245,158,11,0.15);
  color: var(--warning);
}

.badge-error {
  background: rgba(239,68,68,0.15);
  color: var(--error);
}

.badge-info {
  background: rgba(59,130,246,0.15);
  color: var(--info);
}

.badge-accent {
  background: rgba(94,106,210,0.15);
  color: var(--accent);
}

.pipeline-node {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.75rem;
  transition: all 0.3s var(--easing);
  position: relative;
  overflow: hidden;
}

.pipeline-node::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
  opacity: 0;
  transition: opacity 0.3s var(--easing);
}

.pipeline-node:hover::before {
  opacity: 1;
}

.pipeline-node:hover {
  background: var(--surface-hover);
  border-color: rgba(255,255,255,0.12);
}

.timeline-bar {
  height: 28px;
  border-radius: var(--radius-xs);
  background: var(--surface);
  overflow: hidden;
  position: relative;
}

.timeline-bar-fill {
  height: 100%;
  border-radius: var(--radius-xs);
  transition: width 1s var(--easing);
  position: relative;
}

.timeline-bar-fill::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 30px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2));
  border-radius: 0 var(--radius-xs) var(--radius-xs) 0;
}

.gauge-container {
  position: relative;
  width: 100%;
  height: 8px;
  background: var(--surface);
  border-radius: 100px;
  overflow: hidden;
}

.gauge-fill {
  height: 100%;
  border-radius: 100px;
  transition: width 1.5s var(--easing);
  position: relative;
}

.gauge-fill::after {
  content: '';
  position: absolute;
  top: 0;
  right: 0;
  width: 20px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3));
  border-radius: 0 100px 100px 0;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

@keyframes count-up {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slide-in-left {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

@keyframes draw-line {
  from { stroke-dashoffset: 1000; }
  to { stroke-dashoffset: 0; }
}

@keyframes node-enter {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.animate-count { animation: count-up 0.6s var(--easing) forwards; }
.animate-fade { animation: fade-in 0.5s var(--easing) forwards; }
.animate-slide { animation: slide-in-left 0.5s var(--easing) forwards; }

.shimmer {
  background: linear-gradient(90deg, var(--surface) 25%, var(--surface-hover) 50%, var(--surface) 75%);
  background-size: 200% 100%;
  animation: shimmer 2s infinite;
}

.execution-pulse {
  animation: pulse-glow 2s infinite;
}

.dag-node {
  fill: var(--surface);
  stroke: var(--border);
  stroke-width: 1;
  transition: all 0.2s var(--easing);
  cursor: pointer;
}

.dag-node:hover {
  fill: var(--surface-hover);
  stroke: var(--accent);
  stroke-width: 2;
  filter: drop-shadow(0 0 8px var(--accent-glow));
}

.dag-edge {
  stroke: var(--border);
  stroke-width: 1.5;
  fill: none;
  stroke-dasharray: 8 4;
}

.dag-edge-active {
  stroke: var(--accent);
  stroke-width: 2;
  stroke-dasharray: none;
}

.dag-label {
  fill: var(--foreground-muted);
  font-family: var(--font);
  font-size: 10px;
  font-weight: 500;
}

.json-viewer {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.75rem;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.75rem;
  line-height: 1.5;
  overflow-x: auto;
  color: var(--foreground-muted);
}

.json-viewer .key { color: var(--accent); }
.json-viewer .string { color: var(--success); }
.json-viewer .number { color: var(--warning); }
.json-viewer .boolean { color: var(--info); }
.json-viewer .null { color: var(--error); }

.dashboard-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--border), transparent);
  margin: 1.5rem 0;
}

.stButton > button {
  font-family: var(--font) !important;
  font-weight: 500 !important;
  border-radius: var(--radius-sm) !important;
  border: 1px solid var(--border) !important;
  background: var(--surface) !important;
  color: var(--foreground) !important;
  transition: all 0.2s var(--easing) !important;
}

.stButton > button:hover {
  background: var(--surface-hover) !important;
  border-color: var(--accent) !important;
  color: var(--foreground) !important;
}

.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--accent) 0%, #7C3AED 100%) !important;
  border: none !important;
  color: white !important;
  font-weight: 600 !important;
}

.stButton > button[kind="primary"]:hover {
  box-shadow: 0 0 20px var(--accent-glow) !important;
}

div[data-testid="stSelectbox"] label {
  font-family: var(--font) !important;
  color: var(--foreground-muted) !important;
  font-size: 0.75rem !important;
}

div[data-testid="stSelectbox"] div[data-baseweb="select"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
}

div[data-testid="stTextArea"] textarea,
div[data-testid="stTextInput"] input {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--foreground) !important;
  font-family: var(--font) !important;
}

div[data-testid="stMetricValue"] {
  font-family: var(--font) !important;
  font-weight: 700 !important;
  color: var(--foreground) !important;
}

div[data-testid="stMetricLabel"] {
  font-family: var(--font) !important;
  color: var(--foreground-muted) !important;
  font-size: 0.75rem !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

.stProgress > div > div > div > div {
  background: linear-gradient(90deg, var(--accent), #7C3AED) !important;
}

div[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  background: var(--surface) !important;
}

div[data-testid="stExpander"] summary {
  font-family: var(--font) !important;
  font-weight: 500 !important;
  color: var(--foreground) !important;
}

.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border-radius: var(--radius-sm) !important;
  padding: 0.15rem !important;
  gap: 2px !important;
}

.stTabs [data-baseweb="tab"] {
  font-family: var(--font) !important;
  font-weight: 500 !important;
  font-size: 0.8rem !important;
  color: var(--foreground-muted) !important;
  border-radius: var(--radius-xs) !important;
  padding: 0.4rem 0.75rem !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: var(--surface-hover) !important;
  color: var(--foreground) !important;
}

.stAlert {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--foreground) !important;
}

.stInfo {
  background: rgba(59,130,246,0.08) !important;
  border: 1px solid rgba(59,130,246,0.15) !important;
}

.stSuccess {
  background: rgba(34,197,94,0.08) !important;
  border: 1px solid rgba(34,197,94,0.15) !important;
}

.stWarning {
  background: rgba(245,158,11,0.08) !important;
  border: 1px solid rgba(245,158,11,0.15) !important;
}

.stError {
  background: rgba(239,68,68,0.08) !important;
  border: 1px solid rgba(239,68,68,0.15) !important;
}

div[data-testid="stSpinner"] {
  color: var(--accent) !important;
}

.streaming-text {
  overflow: hidden;
  white-space: pre-wrap;
  animation: fade-in 0.3s var(--easing);
}

.tooltip-custom {
  position: relative;
}

.tooltip-custom:hover::after {
  content: attr(data-tooltip);
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
  padding: 0.4rem 0.6rem;
  font-size: 0.7rem;
  color: var(--foreground);
  white-space: nowrap;
  z-index: 1000;
  font-family: var(--font);
}
</style>
"""

DAG_HTML_TEMPLATE = """
<div id="dag-container" style="width:100%;height:400px;background:var(--bg-elevated);border-radius:var(--radius-sm);border:1px solid var(--border);overflow:hidden;position:relative;">
  <svg id="dag-svg" width="100%" height="100%" style="cursor:grab;"></svg>
  <div id="dag-tooltip" style="display:none;position:absolute;background:var(--bg-elevated);border:1px solid var(--accent);border-radius:var(--radius-xs);padding:8px 12px;font-size:12px;color:var(--foreground);pointer-events:none;z-index:100;font-family:Inter,sans-serif;box-shadow:0 4px 12px rgba(0,0,0,0.4);">
    <div id="dag-tooltip-title" style="font-weight:600;margin-bottom:4px;"></div>
    <div id="dag-tooltip-body" style="color:var(--foreground-muted);"></div>
  </div>
</div>
<script>
(function() {{
  const container = document.getElementById('dag-container');
  const svg = document.getElementById('dag-svg');
  const tooltip = document.getElementById('dag-tooltip');
  const ns = 'http://www.w3.org/2000/svg';

  let nodes = {nodes};
  let edges = {edges};
  let scale = 1, tx = 40, ty = 40;
  let isPanning = false, startX, startY;

  const nodeW = 140, nodeH = 40, levelGap = 120, nodeGap = 20;

  function layout() {{
    const levels = {{}};
    const inDegree = {{}};
    nodes.forEach(n => {{ inDegree[n.id] = 0; }});
    edges.forEach(e => {{ inDegree[e.target] = (inDegree[e.target]||0)+1; }});
    let queue = nodes.filter(n => inDegree[n.id]===0).map(n=>n.id);
    let depth = 0;
    while(queue.length) {{
      levels[depth] = queue;
      const next = [];
      queue.forEach(nid => {{
        edges.filter(e=>e.source===nid).forEach(e=>{{
          inDegree[e.target]--;
          if(inDegree[e.target]===0) next.push(e.target);
        }});
      }});
      queue = next;
      depth++;
    }}
    const remaining = nodes.filter(n=>!(n.id in Object.values(levels).flat()));
    if(remaining.length) levels[depth] = remaining.map(n=>n.id);
    return levels;
  }}

  function draw() {{
    svg.innerHTML = '';
    const levels = layout();
    const defs = document.createElementNS(ns,'defs');
    const marker = document.createElementNS(ns,'marker');
    marker.setAttribute('id','arrowhead');
    marker.setAttribute('markerWidth','8');
    marker.setAttribute('markerHeight','6');
    marker.setAttribute('refX','8');
    marker.setAttribute('refY','3');
    marker.setAttribute('orient','auto');
    const arrow = document.createElementNS(ns,'polygon');
    arrow.setAttribute('points','0 0, 8 3, 0 6');
    arrow.setAttribute('fill','rgba(255,255,255,0.15)');
    marker.appendChild(arrow);
    defs.appendChild(marker);
    svg.appendChild(defs);

    const pos = {{}};
    let maxW = 0;
    Object.entries(levels).forEach(([lvl, nids]) => {{
      const y = parseInt(lvl) * levelGap + nodeH;
      nids.forEach((nid, i) => {{
        const x = i * (nodeW + nodeGap) + nodeGap;
        pos[nid] = {{x, y}};
        if(x+nodeW > maxW) maxW = x+nodeW;
      }});
    }});

    svg.setAttribute('viewBox', `0 0 ${{Math.max(maxW+40,400)}} ${{Object.keys(levels).length*levelGap+60}}`);

    edges.forEach(e => {{
      const src = pos[e.source], tgt = pos[e.target];
      if(!src||!tgt) return;
      const line = document.createElementNS(ns,'line');
      line.setAttribute('x1', src.x+nodeW/2);
      line.setAttribute('y1', src.y+nodeH/2);
      line.setAttribute('x2', tgt.x+nodeW/2);
      line.setAttribute('y2', tgt.y+nodeH/2);
      const status = e.status||'pending';
      line.setAttribute('stroke', status==='completed'?'rgba(94,106,210,0.5)':'rgba(255,255,255,0.08)');
      line.setAttribute('stroke-width', status==='completed'?'2':'1');
      line.setAttribute('stroke-dasharray', status==='completed'?'none':'6 4');
      line.setAttribute('marker-end','url(#arrowhead)');
      svg.appendChild(line);
    }});

    nodes.forEach(n => {{
      const p = pos[n.id];
      if(!p) return;
      const g = document.createElementNS(ns,'g');
      g.setAttribute('class','dag-node');

      const rect = document.createElementNS(ns,'rect');
      rect.setAttribute('x', p.x);
      rect.setAttribute('y', p.y);
      rect.setAttribute('width', nodeW);
      rect.setAttribute('height', nodeH);
      rect.setAttribute('rx', '8');
      rect.setAttribute('ry', '8');
      const status = n.status||'pending';
      if(status==='completed') {{
        rect.setAttribute('fill','rgba(94,106,210,0.15)');
        rect.setAttribute('stroke','rgba(94,106,210,0.4)');
      }} else if(status==='running') {{
        rect.setAttribute('fill','rgba(245,158,11,0.1)');
        rect.setAttribute('stroke','rgba(245,158,11,0.3)');
      }} else {{
        rect.setAttribute('fill','rgba(255,255,255,0.03)');
        rect.setAttribute('stroke','rgba(255,255,255,0.08)');
      }}
      g.appendChild(rect);

      const text = document.createElementNS(ns,'text');
      text.setAttribute('x', p.x + nodeW/2);
      text.setAttribute('y', p.y + nodeH/2 + 4);
      text.setAttribute('text-anchor','middle');
      text.setAttribute('fill','#EDEDEF');
      text.setAttribute('font-family','Inter,sans-serif');
      text.setAttribute('font-size','11px');
      text.setAttribute('font-weight','500');
      text.textContent = n.label||n.id;
      g.appendChild(text);

      g.addEventListener('mouseenter', (e) => {{
        tooltip.style.display = 'block';
        document.getElementById('dag-tooltip-title').textContent = n.label||n.id;
        let body = '';
        if(n.agent) body += '<div>Agent: '+n.agent+'</div>';
        if(n.duration) body += '<div>Duration: '+n.duration+'ms</div>';
        if(n.status) body += '<div>Status: '+n.status+'</div>';
        if(n.tool) body += '<div>Tool: '+n.tool+'</div>';
        document.getElementById('dag-tooltip-body').innerHTML = body;
        const r = container.getBoundingClientRect();
        tooltip.style.left = (e.clientX - r.left + 12)+'px';
        tooltip.style.top = (e.clientY - r.top - 10)+'px';
      }});
      g.addEventListener('mousemove', (e) => {{
        const r = container.getBoundingClientRect();
        tooltip.style.left = (e.clientX - r.left + 12)+'px';
        tooltip.style.top = (e.clientY - r.top - 10)+'px';
      }});
      g.addEventListener('mouseleave', () => {{
        tooltip.style.display = 'none';
      }});
      svg.appendChild(g);
    }});
  }}

  draw();

  container.addEventListener('mousedown', (e) => {{
    if(e.target.tagName==='svg'||e.target===container) {{
      isPanning=true; startX=e.clientX-tx; startY=e.clientY-ty;
      svg.style.cursor='grabbing';
    }}
  }});
  window.addEventListener('mousemove', (e) => {{
    if(isPanning) {{ tx=e.clientX-startX; ty=e.clientY-startY; svg.style.transform='translate('+tx+'px,'+ty+'px)'; }}
  }});
  window.addEventListener('mouseup', () => {{ isPanning=false; svg.style.cursor='grab'; }});

  container.addEventListener('wheel', (e) => {{
    e.preventDefault();
    const delta = e.deltaY>0?0.9:1.1;
    scale = Math.max(0.3, Math.min(3, scale*delta));
    svg.style.transform = 'translate('+tx+'px,'+ty+'px) scale('+scale+')';
    svg.style.transformOrigin = '0 0';
  }}, {{passive:false}});
}})();
</script>
"""


def inject_theme() -> None:
    import streamlit as st

    st.markdown(CSS, unsafe_allow_html=True)
