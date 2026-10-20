// Web copies of EITR's own artwork, generated from the repository at build time:
// selected Norse illustrations (theme wallpapers and website-only art in assets/norse), theme preview wallpapers and palettes, the
// current release from distro/release.json and the roadmap from distro/RELEASES.md.
// Outputs are ignored by Git; edit the sources under ../themes instead.
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import sharp from "sharp";

const themes = new URL("../../themes/", import.meta.url);
const art = new URL("../public/art/", import.meta.url);
const data = new URL("../src/data/", import.meta.url);
const approvedArtwork = JSON.parse(await readFile(new URL("../../themes/artwork-batch-04.json", import.meta.url), "utf8"));

const norse = {
  mimir: "../../themes/norse/backgrounds/03-mimir-well-of-wisdom.jpg",
  valkyrie: "../../themes/norse/backgrounds/05-valkyrie.jpg",
  yggdrasil: "../assets/norse/yggdrasil.png",
  jormungandr: "../../themes/norse/backgrounds/08-jormungandr.jpg",
};

await mkdir(new URL("themes/", art), { recursive: true });
await mkdir(data, { recursive: true });

for (const [name, file] of Object.entries(norse)) {
  const source = new URL(file, import.meta.url).pathname;
  await sharp(source).resize({ width: 2400, withoutEnlargement: true }).webp({ quality: 80 }).toFile(new URL(`${name}.webp`, art).pathname);
}

const palette = (text) =>
  Object.fromEntries([...text.matchAll(/^(\w+)\s*=\s*"(#[0-9a-fA-F]{6})"/gm)].map(([, key, value]) => [key, value]));

const catalog = [];
for (const entry of (await readdir(themes, { withFileTypes: true })).filter((item) => item.isDirectory())) {
  const directory = new URL(`${entry.name}/`, themes);
  const wallpapers = (await readdir(new URL("backgrounds/", directory))).filter((file) => /\.(png|jpe?g|webp)$/i.test(file)).sort();
  if (!wallpapers.length) continue;
  const colors = palette(await readFile(new URL("colors.toml", directory), "utf8"));
  const name = (await readFile(new URL("display-name", directory), "utf8")).trim();
  const light = await readFile(new URL("light.mode", directory)).then(() => true, () => false);
  const selectedArtwork = approvedArtwork.previews[entry.name];
  const previewSource = selectedArtwork
    ? new URL(`../../${selectedArtwork}`, import.meta.url).pathname
    : new URL(`backgrounds/${entry.name === "norse" ? "04-huginn-muninn.jpg" : wallpapers[0]}`, directory).pathname;
  await sharp(previewSource)
    .resize({ width: 900, height: 506, fit: "cover" })
    .webp({ quality: 76 })
    .toFile(new URL(`themes/${entry.name}.webp`, art).pathname);
  // The full wallpaper for the theme viewer, loaded only when a theme is opened.
  await sharp(previewSource)
    .resize({ width: 2400, withoutEnlargement: true })
    .webp({ quality: 80 })
    .toFile(new URL(`themes/${entry.name}-full.webp`, art).pathname);
  catalog.push({
    id: entry.name,
    name,
    light,
    swatches: [colors.background, colors.color1, colors.color2, colors.color3, colors.color4, colors.color5, colors.accent],
  });
}
catalog.sort((a, b) => (a.id === "norse" ? -1 : b.id === "norse" ? 1 : a.name.localeCompare(b.name)));
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
const roadmap = [...releases.matchAll(/^\| *(\d+\.\d+\.\d+) *\| *([^|]+?) *\| *([a-z]+) *\| *([^|]+?) *\|$/gm)]
  .map(([, version, codename, stage, milestone]) => ({ version, codename, stage, milestone }));
if (!roadmap.length) throw new Error("No release table found in distro/RELEASES.md");
await writeFile(new URL("roadmap.json", data), JSON.stringify(roadmap, null, 2) + "\n");
console.log(`Synchronized ${Object.keys(norse).length} illustrations and ${catalog.length} themes.`);
