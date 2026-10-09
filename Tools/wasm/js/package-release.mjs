// Turns what `build-compiler.sh` produced into a release: content-addressed files, plus the one
// mutable `manifest.json` naming them, plus the loader.
//
// Every file but `manifest.json` carries a hash of its contents in its name, so every file but
// `manifest.json` can be served as immutable, and two releases sharing a file share its URL.
//
//   node package-release.mjs <dist> <version> <out>

import { createHash } from "node:crypto";
import { copyFileSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const [dist, version, out] = process.argv.slice(2);
if (out === undefined) {
  console.error("usage: node package-release.mjs <dist> <version> <out>");
  process.exit(2);
}

rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });

const files = {};
const emit = (key, source, extra = {}) => {
  const bytes = readFileSync(source);
  const sha256 = createHash("sha256").update(bytes).digest("hex");
  const { name, ext } = path.parse(source);
  const published = `${name}-${sha256.slice(0, 12)}${ext}`;
  copyFileSync(source, path.join(out, published));
  files[key] = {
    path: published,
    sha256,
    bytes: bytes.length,
    gzip: gzipSync(bytes, { level: 9 }).length,
    ...extra,
  };
};

emit("compiler", path.join(dist, "hylo-wasm.wasm"));
emit("standardLibrary", path.join(dist, "stdlib.json"));
const lib = path.join(dist, "sysroot", "lib");
const sysroot = [];
for (const n of readdirSync(lib).sort()) {
  const key = `sysroot:${n}`;
  emit(key, path.join(lib, n), { name: n });
  sysroot.push(key);
}

// The loader keeps its plain name, and is bundled with its one dependency so that a page can
// import it straight from the release, without a bundler or an import map. The worker hosting it
// is bundled the same way, and finds the release from where it is served. Neither is
// content-addressed, since pages name them, but the manifest records what they hold.
const here = path.dirname(fileURLToPath(import.meta.url));
const { build } = await import("esbuild");
const loaders = {};
for (const entry of ["index.mjs", "worker.mjs"]) {
  const outfile = path.join(out, entry);
  await build({
    entryPoints: [path.join(here, entry)],
    bundle: true,
    format: "esm",
    target: "es2022",
    outfile,
    logLevel: "warning",
  });
  const bytes = readFileSync(outfile);
  loaders[entry] = { sha256: createHash("sha256").update(bytes).digest("hex"), bytes: bytes.length };
}

const manifest = {
  schemaVersion: 1,
  version,
  built: new Date().toISOString(),
  // What the build was made from.
  inputs: {
    hylo: process.env.GITHUB_SHA ?? null,
    llvm: process.env.LLVM_VERSION ?? null,
    llvmBuild: process.env.LLVM_BUILD_RELEASE ?? null,
    swift: process.env.SWIFT_VERSION ?? null,
  },
  files,
  // The keys of `files` that are linked into every executable, in the order a host should
  // install them under `/sysroot/lib`, by their `name`.
  sysroot,
  loaders,
};
writeFileSync(path.join(out, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");

const mb = (n) => `${(n / 1048576).toFixed(1)} MB`;
console.log("| file | size | gzip |\n|---|---:|---:|");
for (const f of Object.values(files)) console.log(`| \`${f.path}\` | ${mb(f.bytes)} | ${mb(f.gzip)} |`);
const total = Object.values(files).reduce((a, f) => a + f.gzip, 0);
console.log(`| **over the wire** | | **${mb(total)}** |`);
