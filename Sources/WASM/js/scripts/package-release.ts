// Turns what `build-compiler.sh` produced into a compiler release: content-addressed files, plus
// the one mutable `manifest.json` naming them, plus the loaders, bundled.
//
// Every file but `manifest.json` carries a hash of its contents in its name, so every file but
// `manifest.json` can be served as immutable, and two releases sharing a file share its URL.
//
//   node scripts/package-release.ts <dist> <version> <out>

import { mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";
import { build } from "tsdown";
import type { Manifest, ManifestFile } from "../src/protocol.ts";
import { distLayout, fingerprint } from "./dist.ts";

const [dist, version, out] = process.argv.slice(2);
if (out === undefined) {
  console.error("usage: node package-release.ts <dist> <version> <out>");
  process.exit(2);
}

rmSync(out, { recursive: true, force: true });
mkdirSync(out, { recursive: true });

const files: Record<string, ManifestFile> = {};
const emit = (key: string, source: string, extra: Partial<ManifestFile> = {}): void => {
  const compressed = extra.encoding === "gzip";
  const contents = readFileSync(source);
  const bytes = compressed ? gzipSync(contents, { level: 9 }) : contents;
  const { sha256 } = fingerprint(bytes);
  const { name, ext } = path.parse(source);
  const published = `${name}-${sha256.slice(0, 12)}${ext}${compressed ? ".gz" : ""}`;
  writeFileSync(path.join(out, published), bytes);
  files[key] = {
    path: published,
    ...fingerprint(bytes),
    gzip: compressed ? bytes.length : gzipSync(bytes, { level: 9 }).length,
    ...extra,
  };
};

// The compiler is stored compressed, which keeps a release within the 20 MB that package registries
// such as JSR accept, and needs nothing of the server; gzip is the one format that every browser's
// `DecompressionStream` reads.
emit("compiler", path.join(dist, distLayout.compiler), { encoding: "gzip" });
emit("standardLibrary", path.join(dist, distLayout.standardLibrary));
const lib = path.join(dist, distLayout.sysroot);
const sysroot: string[] = [];
for (const n of readdirSync(lib).sort()) {
  const key = `sysroot:${n}`;
  emit(key, path.join(lib, n), { name: n });
  sysroot.push(key);
}

// The loaders keep their plain names, and are bundled with their one dependency so that a page can
// import them straight from the release, without a bundler or an import map; the worker finds the
// release from where it is served. They are built one at a time, so that each is a single file.
// Neither is content-addressed, since pages name them, but the manifest records what they hold.
const here = path.dirname(fileURLToPath(import.meta.url));
const loaders: NonNullable<Manifest["loaders"]> = {};
for (const name of ["index", "worker"]) {
  await build({
    config: false,
    entry: { [name]: path.join(here, `../src/${name}.ts`) },
    format: "esm",
    platform: "browser",
    outDir: out,
    deps: { alwaysBundle: [/.*/] },
    dts: false,
    minify: true,
    clean: false,
    logLevel: "warn",
    outExtensions: () => ({ js: ".mjs" }),
  });
  loaders[`${name}.mjs`] = fingerprint(readFileSync(path.join(out, `${name}.mjs`)));
}

const manifest: Manifest = {
  schemaVersion: 2,
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

const mb = (n: number): string => `${(n / 1048576).toFixed(1)} MB`;
console.log("| file | size | gzip |\n|---|---:|---:|");
for (const f of Object.values(files))
  console.log(`| \`${f.path}\` | ${mb(f.bytes)} | ${mb(f.gzip)} |`);
const total = Object.values(files).reduce((a, f) => a + f.gzip, 0);
console.log(`| **over the wire** | | **${mb(total)}** |`);
