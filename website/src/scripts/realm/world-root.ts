// Two static paths share one pointed scroll clip. Root geometry is calculated
// only on resize; the clip's tip follows cached trunk coordinates.
import { reducedMotion } from './motion';

const SVG = 'http://www.w3.org/2000/svg';
const start = document.querySelector<HTMLElement>('.rune-band');
const end = document.querySelector<HTMLElement>('.footer');
const wrap = document.querySelector<HTMLElement>('main .wrap');
type Point = [number, number];

function generator(seed: number) {
  return () => {
    seed = (seed * 1664525 + 1013904223) % 4294967296;
    return seed / 4294967296;
  };
}

function element<Name extends keyof SVGElementTagNameMap>(name: Name, attributes: Record<string, string> = {}) {
  const node = document.createElementNS(SVG, name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, value);
  return node;
}

function curve(points: Point[], first = 'M') {
  const format = (point: Point) => point.map(value => value.toFixed(1)).join(' ');
  let path = `${first}${format(points[0])}`;
  for (let index = 0; index < points.length - 1; index += 1) {
    const before = points[Math.max(0, index - 1)];
    const current = points[index];
    const next = points[index + 1];
    const after = points[Math.min(points.length - 1, index + 2)];
    path += ` C${format([current[0] + (next[0] - before[0]) / 6, current[1] + (next[1] - before[1]) / 6])}`;
    path += ` ${format([next[0] - (after[0] - current[0]) / 6, next[1] - (after[1] - current[1]) / 6])} ${format(next)}`;
  }
  return path;
}

if (start && end && wrap) {
  const svg = element('svg', { 'aria-hidden': 'true', class: 'world-root' });
  const definitions = element('defs');
  const clip = element('clipPath', { id: 'world-root-growth', clipPathUnits: 'userSpaceOnUse' });
  const reveal = element('polygon', { points: '0,0 0,0 0,0' });
  const group = element('g', { 'clip-path': 'url(#world-root-growth)' });
  const wood = element('path', { class: 'root-wood' });
  const bark = element('path', { class: 'root-bark' });
  clip.append(reveal);
  definitions.append(clip);
  group.append(wood, bark);
  svg.append(definitions, group);
  document.body.append(svg);
  let top = 0;
  let height = 1;
  let frame = 0;
  let buildFrame = 0;
  let geometry = '';
  let visible = false;
  let lastReached = -1;
  let width = 0;
  let trunk: Point[] = [];

  const trunkX = (y: number) => {
    const index = Math.min(trunk.length - 2, Math.floor(y / 48));
    const from = trunk[index];
    const to = trunk[index + 1];
    const fraction = Math.min(1, Math.max(0, (y - from[1]) / Math.max(1, to[1] - from[1])));
    return from[0] + (to[0] - from[0]) * fraction;
  };

  const grow = () => {
    frame = 0;
    if (!visible || document.hidden) return;
    const reached = reducedMotion.matches ? Math.ceil(height) : Math.round(Math.min(height, Math.max(0, scrollY + innerHeight * 0.72 - top)));
    if (reached === lastReached) return;
    lastReached = reached;
    const shoulder = Math.max(0, reached - 48);
    const shoulderX = trunkX(shoulder);
    const tipX = trunkX(Math.min(height, reached));
    reveal.setAttribute('points', reached <= 0 ? '0,0 0,0 0,0'
      : `0,0 ${width},0 ${width},${shoulder} ${shoulderX + 15},${shoulder} ${tipX},${reached} ${shoulderX - 15},${shoulder} 0,${shoulder}`);
    reveal.dataset.reached = String(reached);
  };

  const build = () => {
    buildFrame = 0;
    const gutter = wrap.getBoundingClientRect().left;
    top = start.getBoundingClientRect().bottom + scrollY;
    height = Math.max(1, end.getBoundingClientRect().top + scrollY - top);
    const nextGeometry = `${Math.round(gutter)}:${Math.round(top)}:${Math.round(height)}`;
    if (geometry === nextGeometry) return;
    geometry = nextGeometry;
    visible = gutter >= 60;
    svg.style.display = visible ? '' : 'none';
    if (!visible) return;
    width = Math.min(Math.round(gutter - 12), 220);
    svg.style.top = `${top}px`;
    svg.style.left = `${Math.round((gutter - width) / 2)}px`;
    svg.setAttribute('width', String(width));
    svg.setAttribute('height', String(height));
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    const random = generator(20261015);
    const shapes: string[] = [];
    const grain: string[] = [];

    const root = (points: Point[], radius: number, trunk = false) => {
      const left: Point[] = [];
      const right: Point[] = [];
      const ridge: Point[] = [];
      points.forEach((point, index) => {
        const before = points[Math.max(0, index - 1)];
        const after = points[Math.min(points.length - 1, index + 1)];
        const angle = Math.atan2(after[1] - before[1], after[0] - before[0]);
        const taper = trunk ? 1 - index / (points.length - 1) * 0.8 : 1 - index / (points.length - 1);
        const girth = Math.max(0.1, radius * taper * (0.86 + random() * 0.28));
        const normal: Point = [-Math.sin(angle), Math.cos(angle)];
        left.push([point[0] + normal[0] * girth, point[1] + normal[1] * girth]);
        right.push([point[0] - normal[0] * girth * 0.8, point[1] - normal[1] * girth * 0.8]);
        ridge.push([point[0] + normal[0] * girth * 0.3, point[1] + normal[1] * girth * 0.3]);
      });
      shapes.push(`${curve(left)} ${curve(right.reverse(), 'L')} Z`);
      if (radius > 2) grain.push(curve(ridge));
    };

    trunk = [];
    let x = width / 2;
    let drift = 0;
    for (let y = 0; y < height; y += 48) {
      drift = drift * 0.6 + (random() - 0.5) * 8 + (width / 2 - x) * 0.1;
      x = Math.max(width * 0.3, Math.min(width * 0.7, x + drift));
      trunk.push([x, y]);
    }
    trunk.push([x, height]);
    // Sparse side roots share exact points with the trunk and keep their
    // downward direction, so a single top-to-bottom clip reveals every fork.
    for (let index = 2; index < trunk.length - 1; index += 4 + Math.floor(random() * 3)) {
      const from = trunk[index];
      const direction = random() < 0.5 ? -1 : 1;
      const length = 36 + random() * 55;
      const branch: Point[] = [from];
      for (let step = 1; step <= 4; step += 1) {
        branch.push([Math.max(5, Math.min(width - 5, from[0] + direction * length * step / 5 + (random() - 0.5) * 8)), Math.min(height, from[1] + step * 19)]);
      }
      root(branch, 2 + (1 - index / trunk.length) * 2);
      if (random() < 0.6) {
        const fork = branch[2];
        root([fork, [fork[0] - direction * 8, fork[1] + 24], [fork[0] - direction * 19, fork[1] + 46]], 1.3);
      }
    }
    root(trunk, Math.min(9, width * 0.1), true);
    wood.setAttribute('d', shapes.join(' '));
    bark.setAttribute('d', grain.join(' '));
    lastReached = -1;
    grow();
  };

  const schedule = () => { if (!frame && !document.hidden) frame = requestAnimationFrame(grow); };
  addEventListener('scroll', schedule, { passive: true });
  new ResizeObserver(() => { if (!buildFrame) buildFrame = requestAnimationFrame(build); }).observe(document.body);
  reducedMotion.addEventListener('change', schedule);
  document.addEventListener('visibilitychange', schedule);
}
