// Puts the compiler of a release into the package, next to the loader, which loads it from there
// by default: the manifest and every file it names, but not the release's own bundled loaders.
//
//   node scripts/include-compiler.ts <release> [<dist>]
//
// `<dist>` is the package's `dist/` by default, which `npm run build` must have written first,
// since it empties it.

import { copyFileSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Manifest } from "../src/protocol.ts";

const here = path.dirname(fileURLToPath(import.meta.url));
const [release, dist = path.join(here, "../dist")] = process.argv.slice(2);
if (release === undefined) {
  console.error("usage: node include-compiler.ts <release> [<dist>]");
  process.exit(2);
}

const manifest = JSON.parse(readFileSync(path.join(release, "manifest.json"), "utf8")) as Manifest;
for (const name of ["manifest.json", ...Object.values(manifest.files).map((f) => f.path)]) {
  copyFileSync(path.join(release, name), path.join(dist, name));
}
console.log(`included compiler ${manifest.version} from ${release} in ${dist}`);
