import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
const target = new URL("../public/branding/", import.meta.url);
await mkdir(target, { recursive: true });
for (const name of ["eitr-wordmark.svg", "eitr-logo.svg", "eitr-rune-ring.svg"]) {
  await copyFile(
    new URL(`../../branding/svg/${name}`, import.meta.url),
    new URL(name, target),
  );
}

// A tight square crop and explicit light color keep the liquid mark legible
// at browser-tab sizes, independently of the browser's own appearance.
const logo = await readFile(new URL("eitr-logo.svg", target), "utf8");
const coordinates = [...logo.matchAll(/[ML](-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)/g)];
if (!coordinates.length) throw new Error("Logo must contain polygon path coordinates.");
const xs = coordinates.map((point) => Number(point[1]));
const ys = coordinates.map((point) => Number(point[2]));
const width = Math.max(...xs) - Math.min(...xs);
const height = Math.max(...ys) - Math.min(...ys);
const side = Math.max(width, height) * 1.04;
const x = (Math.min(...xs) + Math.max(...xs) - side) / 2;
const y = (Math.min(...ys) + Math.max(...ys) - side) / 2;
const favicon = logo
  .replace(/viewBox="[^"]+"/, `viewBox="${x} ${y} ${side} ${side}"`)
  .replace(/width="[^"]+"/, 'width="32"')
  .replace(/height="[^"]+"/, 'height="32"')
  // The same tarnished gold as the section headings' emphasis (.section h2 em).
  .replace('fill="currentColor"', 'fill="#c9a46a"')
  .replace("<title>Eitr logo</title>", "<title>Eitr favicon</title>");
await writeFile(new URL("eitr-favicon.svg", target), favicon);
// Scripts import the logo's geometry from src/; Vite serves public/ files as-is
// and does not let code import them.
await mkdir(new URL("../src/data/", import.meta.url), { recursive: true });
await copyFile(new URL("eitr-logo.svg", target), new URL("../src/data/eitr-logo.svg", import.meta.url));
