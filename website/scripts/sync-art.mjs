// Web copies of EITR artwork, generated from the desktop and official Store sources:
// selected Norse illustrations (theme wallpapers and website-only art in assets/norse), theme previews, full wallpapers and palettes, the
// current release from distro/release.json and the roadmap from distro/RELEASES.md.
// Outputs are ignored by Git.
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import sharp from "sharp";

const themes = new URL("../../themes/", import.meta.url);
const art = new URL("../public/art/", import.meta.url);
const data = new URL("../src/data/", import.meta.url);
const sibling = new URL("../../../eitr-themes/", import.meta.url);
const localStore = process.env.EITR_THEMES_DIR
  ? pathToFileURL(resolve(process.env.EITR_THEMES_DIR) + "/")
  : await readFile(new URL("eitr-catalog.json", sibling)).then(() => sibling, () => null);
const store = localStore ?? new URL("https://raw.githubusercontent.com/eitr-org/eitr-themes/main/");

async function storeFile(path) {
  const url = new URL(path, store);
  if (!url.href.startsWith(store.href)) throw new Error(`Invalid Store asset path: ${path}`);
  if (localStore) return readFile(url);
  const response = await fetch(url, { signal: AbortSignal.timeout(30_000) });
  if (!response.ok) throw new Error(`Unable to fetch Store artwork: ${response.status} ${path}`);
  return Buffer.from(await response.arrayBuffer());
}

const eitr = {
  mimir: "../assets/norse/03-mimir-well-of-wisdom.jpg",
  valkyrie: "../assets/norse/05-valkyrie.jpg",
  yggdrasil: "../assets/norse/yggdrasil.png",
  jormungandr: "../assets/norse/08-jormungandr.jpg",
};

await mkdir(new URL("themes/", art), { recursive: true });
await mkdir(data, { recursive: true });

const storeRows = JSON.parse(await storeFile("eitr-catalog.json"));
const ragnarok = storeRows.find((row) => row.id === "ragnarok");
if (!ragnarok) throw new Error("The official catalog is missing Ragnarök");
const ragnarokWallpaper = await storeFile(ragnarok.wallpapers[0].path);
await sharp(ragnarokWallpaper).resize({ width: 2400, withoutEnlargement: true })
  .webp({ quality: 80 }).toFile(new URL("ragnarok.webp", art).pathname);

for (const [name, file] of Object.entries(eitr)) {
  const source = new URL(file, import.meta.url).pathname;
  await sharp(source).resize({ width: 2400, withoutEnlargement: true }).webp({ quality: 80 }).toFile(new URL(`${name}.webp`, art).pathname);
}

const palette = (text) =>
  Object.fromEntries([...text.matchAll(/^(\w+)\s*=\s*"(#[0-9a-fA-F]{6})"/gm)].map(([, key, value]) => [key, value]));

async function addTheme(row, preview, wallpaper) {
  await sharp(preview).resize({ width: 900, height: 506, fit: "cover" })
    .webp({ quality: 76 }).toFile(new URL(`themes/${row.id}.webp`, art).pathname);
  await sharp(wallpaper).resize({ width: 2400, withoutEnlargement: true })
    .webp({ quality: 80 }).toFile(new URL(`themes/${row.id}-full.webp`, art).pathname);
  const { id, name, light, palette: colors } = row;
  return { id, name, light, swatches: ["background", "color1", "color2", "color3", "color4",
    "color5", "accent"].map((key) => colors[key]) };
}

const catalog = [];
for (const entry of (await readdir(themes, { withFileTypes: true })).filter((item) => item.isDirectory())) {
  const directory = new URL(`${entry.name}/`, themes);
  const wallpapers = (await readdir(new URL("backgrounds/", directory))).filter((file) => /\.(png|jpe?g|webp)$/i.test(file)).sort();
  if (!wallpapers.length) continue;
  const colors = palette(await readFile(new URL("colors.toml", directory), "utf8"));
  const name = (await readFile(new URL("display-name", directory), "utf8")).trim();
  const light = await readFile(new URL("light.mode", directory)).then(() => true, () => false);
  catalog.push(await addTheme({ id: entry.name, name, light, palette: colors },
    new URL("preview.png", directory).pathname, new URL(`backgrounds/${wallpapers[0]}`, directory).pathname));
}
for (const row of storeRows) {
  const [preview, wallpaper] = await Promise.all([
    storeFile(row.preview), row === ragnarok ? ragnarokWallpaper : storeFile(row.wallpapers[0].path),
  ]);
  catalog.push(await addTheme(row, preview, wallpaper));
}
catalog.sort((first, second) => (first.id === "eitr" ? -1 : second.id === "eitr" ? 1 : first.name.localeCompare(second.name)));
for (const name of ["skoll", "hati"]) {
  await sharp(new URL(`../assets/chase/${name}-bite.png`, import.meta.url).pathname)
    .resize({ width: 768, withoutEnlargement: true }).webp({ quality: 85 })
    .toFile(new URL(`${name}-bite.webp`, art).pathname);
}
// Preserve the aligned two-frame face atlas and its transparency.
await sharp(new URL("../assets/ragnarok/fenrir-bite.png", import.meta.url).pathname)
  .webp({ quality: 90, alphaQuality: 100 })
  .toFile(new URL("fenrir-bite.webp", art).pathname);
await writeFile(new URL("themes.json", data), JSON.stringify(catalog, null, 2) + "\n");
// The release (version, stage, codename) comes from the same file as the package and ISO.
await writeFile(new URL("release.json", data), await readFile(new URL("../../distro/release.json", import.meta.url)));
// The roadmap is the release table in distro/RELEASES.md:
// | Version | Codename | Stage | Milestone |
const releases = await readFile(new URL("../../distro/RELEASES.md", import.meta.url), "utf8");
const roadmap = [...releases.matchAll(/^\| *(\d+\.\d+\.\d+) *\| *([^|]+?) *\| *([a-z][a-z ]*?) *\| *([^|]+?) *\|$/gm)]
  .map(([, version, codename, stage, milestone]) => ({ version, codename, stage, milestone }));
if (!roadmap.length) throw new Error("No release table found in distro/RELEASES.md");
await writeFile(new URL("roadmap.json", data), JSON.stringify(roadmap, null, 2) + "\n");
console.log(`Synchronized ${Object.keys(eitr).length + 1} illustrations and ${catalog.length} themes.`);
