// Checks that a packaged release is complete and intact: every file its manifest names is there
// with the contents the manifest records, and the release has the version it should.
//
//   node scripts/verify-release.ts <release> <version>
//
// Needs nothing but Node, so that a release can be checked where it is published, away from the
// toolchain that built it.

import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import type { Manifest } from "../src/protocol.ts";

const [release, version] = process.argv.slice(2);
if (version === undefined) {
  console.error("usage: node verify-release.ts <release> <version>");
  process.exit(2);
}

const problems: string[] = [];
const manifest = JSON.parse(readFileSync(path.join(release, "manifest.json"), "utf8")) as Manifest;
if (manifest.schemaVersion !== 2) {
  problems.push(`the manifest's schema is version ${manifest.schemaVersion}, not 2`);
}
if (manifest.version !== version) {
  problems.push(`the release is version ${manifest.version}, not ${version}`);
}

/** Checks that the file at `name` holds `expected.bytes` bytes hashing to `expected.sha256`. */
function check(name: string, expected: { sha256: string; bytes: number }): void {
  let bytes: Buffer;
  try {
    bytes = readFileSync(path.join(release, name));
  } catch {
    problems.push(`${name} is missing`);
    return;
  }
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  if (bytes.length !== expected.bytes || sha256 !== expected.sha256) {
    problems.push(`${name} does not have the contents the manifest records`);
  }
}

for (const f of Object.values(manifest.files)) check(f.path, f);
for (const [name, f] of Object.entries(manifest.loaders ?? {})) check(name, f);
for (const key of manifest.sysroot) {
  if (manifest.files[key]?.name === undefined) problems.push(`no file named by sysroot ${key}`);
}
for (const required of ["compiler", "standardLibrary"]) {
  if (manifest.files[required] === undefined) problems.push(`no ${required} in the manifest`);
}
for (const required of ["index.mjs", "worker.mjs"]) {
  if (manifest.loaders?.[required] === undefined) problems.push(`no ${required} in the manifest`);
}

const named = new Set([
  "manifest.json",
  ...Object.values(manifest.files).map((f) => f.path),
  ...Object.keys(manifest.loaders ?? {}),
]);
for (const n of readdirSync(release)) {
  if (!named.has(n)) problems.push(`${n} is not named by the manifest`);
}

for (const p of problems) console.error(p);
if (problems.length > 0) process.exit(1);
console.log(`${release}: version ${version}, ${named.size} files, all intact`);
