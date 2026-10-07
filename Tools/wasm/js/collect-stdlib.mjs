// Writes the Hylo standard library's sources as one JSON object, keyed by each file's path within
// the resource bundle at the given path.
//
//   node collect-stdlib.mjs <bundle> > stdlib.json

import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

const root = process.argv[2];
if (root === undefined) {
  console.error("usage: node collect-stdlib.mjs <standard library resource bundle>");
  process.exit(2);
}

const sources = {};
for (const e of readdirSync(root, { recursive: true, withFileTypes: true })) {
  if (e.isFile() && e.name.endsWith(".hylo")) {
    const p = path.join(e.parentPath, e.name);
    sources[path.relative(root, p).split(path.sep).join("/")] = readFileSync(p, "utf8");
  }
}
if (Object.keys(sources).length === 0) {
  console.error(`no .hylo sources under ${root}`);
  process.exit(1);
}
process.stdout.write(JSON.stringify(sources));
