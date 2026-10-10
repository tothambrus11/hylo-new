// Checks a packed package the way its users get it: installs the tarball `npm pack` produced in an
// empty project, then
//
// - in Node, imports it by name, compiles a program and runs it;
// - type-checks a program using its types;
// - bundles a page using it with Vite, both directly and through its worker, and runs the page in
//   Chromium (`CHROMIUM`, or the one Playwright installs), served as a static site would be.
//
//   node scripts/smoke-test-package.ts <tarball>
//
// This catches what the tests, which import the sources, cannot: files left out of the package,
// exports that point nowhere, declarations that don't resolve, and compiler files a bundler cannot
// find.

import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "playwright";
import { build } from "vite";

const [tarball] = process.argv.slice(2).map((p) => path.resolve(p));
if (tarball === undefined) {
  console.error("usage: node smoke-test-package.ts <tarball>");
  process.exit(2);
}
const here = path.dirname(fileURLToPath(import.meta.url));
const { name } = JSON.parse(readFileSync(path.join(here, "../package.json"), "utf8"));

/** Runs `command` with `args` in `directory`, showing its output. */
const sh = (directory: string, command: string, ...args: string[]): void => {
  execFileSync(command, args, { cwd: directory, stdio: "inherit" });
};

/** Writes `files`, by path relative to `directory`. */
const write = (directory: string, files: Record<string, string>): void => {
  for (const [file, text] of Object.entries(files)) writeFileSync(path.join(directory, file), text);
};

const project = mkdtempSync(path.join(tmpdir(), "hylo-wasm-package-"));
try {
  write(project, {
    "package.json": JSON.stringify({ name: "consumer", private: true, type: "module" }),
  });
  sh(project, "npm", "install", "--no-audit", "--no-fund", "--silent", tarball);

  // Node.
  write(project, {
    "use.mjs": `import assert from "node:assert/strict";
import { load } from "${name}";

for (const entry of ["${name}/compiler-worker", "${name}/program-worker", "${name}/protocol"]) {
  import.meta.resolve(entry);
}

const hylo = await load();
const r = hylo.compile({ source: "public fun main() -> Int32 { 42 }", emit: ["executable", "llvm"] });
assert.deepEqual(r.diagnostics, []);
assert.match(r.artifacts.llvm, /define .*@main/);
assert.equal((await hylo.run(r.executable)).exitCode, 42);
`,
  });
  sh(project, process.execPath, "use.mjs");
  console.log(`${name}: compiled and ran a program in Node`);

  // Types.
  write(project, {
    "use.ts": `import { load, type Compiler } from "${name}";
import type { CompileRequest, CompilerWorkerMessage } from "${name}/protocol";

const request: CompileRequest = { source: "public fun main() {}", emit: ["ir"] };
const hylo: Compiler = await load();
const ir: string | undefined = hylo.compile(request).artifacts.ir;
export const message: CompilerWorkerMessage | string | undefined = ir;
`,
    "tsconfig.json": JSON.stringify({
      compilerOptions: {
        target: "es2022",
        module: "nodenext",
        lib: ["es2022", "dom"],
        strict: true,
        noEmit: true,
        types: [],
      },
      files: ["use.ts"],
    }),
  });
  sh(project, path.join(here, "../node_modules/.bin/tsc"), "-p", project);
  console.log(`${name}: its types check`);

  // A page, bundled with Vite.
  write(project, {
    "index.html": `<!doctype html><script type="module" src="./main.js"></script>`,
    "main.js": `import { load } from "${name}";
import CompilerWorker from "${name}/compiler-worker?worker";
import ProgramWorker from "${name}/program-worker?worker";

const source = "public fun main() -> Int32 { 42 }";

async function direct() {
  const hylo = await load();
  const r = hylo.compile({ source });
  return (await hylo.run(r.executable)).exitCode;
}

// Resolves to the stages the worker reported, then the exit status.
function throughWorker() {
  return new Promise((resolve, reject) => {
    const w = new CompilerWorker();
    const stages = [];
    w.onerror = (e) => reject(new Error(e.message));
    w.onmessage = ({ data }) => {
      if (data.type === "failed") reject(new Error(data.error));
      if (data.type === "stage") stages.push(data.stage);
      if (data.type === "result") {
        resolve([...stages, data.execution?.exitCode ?? JSON.stringify(data.compilation)].join(" "));
      }
    };
    w.postMessage({ id: 1, request: { source, emit: ["ir", "executable"] } });
  });
}

// Resolves to the exit status of the program compiled by the compiler's worker without running it,
// and run by a program worker.
function throughProgramWorker() {
  return new Promise((resolve, reject) => {
    const compiler = new CompilerWorker();
    compiler.onerror = (e) => reject(new Error(e.message));
    compiler.onmessage = ({ data }) => {
      if (data.type === "failed") reject(new Error(data.error));
      if (data.type !== "result") return;
      if (!data.executable) return reject(new Error(JSON.stringify(data.compilation)));
      const program = new ProgramWorker();
      program.onerror = (e) => reject(new Error(e.message));
      program.onmessage = ({ data: ran }) =>
        ran.type === "ran" ? resolve(ran.execution.exitCode) : reject(new Error(ran.error));
      program.postMessage({ id: 2, executable: data.executable }, [data.executable.buffer]);
    };
    compiler.postMessage({ id: 1, request: { source }, run: false });
  });
}

window.outcome = Promise.all([direct(), throughWorker(), throughProgramWorker()]);
`,
  });
  await build({ root: project, logLevel: "warn", build: { outDir: "dist" } });

  const site = path.join(project, "dist");
  const types: Record<string, string> = {
    ".html": "text/html",
    ".js": "text/javascript",
    ".wasm": "application/wasm",
    ".json": "application/json",
  };
  const server = createServer((request, response) => {
    const file = path.join(site, path.normalize(new URL(request.url!, "http://x").pathname));
    try {
      const body = readFileSync(file.endsWith("/") ? path.join(file, "index.html") : file);
      const type = types[path.extname(file) || ".html"] ?? "application/octet-stream";
      response.writeHead(200, { "content-type": type }).end(body);
    } catch {
      response.writeHead(404).end();
    }
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address();
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });
  try {
    const page = await browser.newPage();
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(`http://127.0.0.1:${typeof address === "object" ? address?.port : 0}/`);
    const outcome = await page.evaluate(() => (window as unknown as { outcome: unknown }).outcome);
    if (JSON.stringify(outcome) !== '[42,"front-end back-end 42",42]' || errors.length > 0) {
      throw new Error(`the page ended with ${JSON.stringify(outcome)} ${errors.join("\n")}`);
    }
  } finally {
    await browser.close();
    server.close();
  }
  console.log(
    `${name}: compiled and ran a program in a page bundled with Vite, and in its workers`,
  );
} finally {
  rmSync(project, { recursive: true, force: true });
}
