// Checks a packed package the way its users get it: installs the tarball `npm pack` produced in an
// empty project, then imports it by name, loads a compiler release over HTTP with it, compiles a
// program and runs it, and type-checks a program using its types.
//
//   node scripts/smoke-test-package.ts <tarball> <release>
//
// This catches what the tests, which import the sources, cannot: files left out of the package,
// exports that point nowhere, and declarations that don't resolve.

import { execFileSync, spawn } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const [tarball, release] = process.argv.slice(2).map((p) => path.resolve(p));
if (release === undefined) {
  console.error("usage: node smoke-test-package.ts <tarball> <release>");
  process.exit(2);
}
const here = path.dirname(fileURLToPath(import.meta.url));
const { name } = JSON.parse(readFileSync(path.join(here, "../package.json"), "utf8"));

/** Runs `command` with `args` in `directory`, showing its output. */
const sh = (directory: string, command: string, ...args: string[]): void => {
  execFileSync(command, args, { cwd: directory, stdio: "inherit" });
};

// The release, served as a web server would.
const types: Record<string, string> = { ".wasm": "application/wasm", ".json": "application/json" };
const server = createServer((request, response) => {
  const file = path.join(release, path.basename(new URL(request.url!, "http://x").pathname));
  try {
    const type = types[path.extname(file)] ?? "application/octet-stream";
    response.writeHead(200, { "content-type": type }).end(readFileSync(file));
  } catch {
    response.writeHead(404).end();
  }
});
await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
const address = server.address();
const baseUrl = `http://127.0.0.1:${typeof address === "object" ? address?.port : 0}/`;

const project = mkdtempSync(path.join(tmpdir(), "hylo-wasm-package-"));
try {
  writeFileSync(
    path.join(project, "package.json"),
    JSON.stringify({ name: "consumer", private: true, type: "module" }),
  );
  sh(project, "npm", "install", "--no-audit", "--no-fund", "--silent", tarball);

  writeFileSync(
    path.join(project, "use.mjs"),
    `import assert from "node:assert/strict";
import { load } from "${name}";

for (const entry of ["${name}/worker", "${name}/protocol"]) import.meta.resolve(entry);

const hylo = await load({ baseUrl: process.argv[2] });
const r = hylo.compile({ source: "public fun main() -> Int32 { 42 }", emit: ["executable", "llvm"] });
assert.deepEqual(r.diagnostics, []);
assert.match(r.artifacts.llvm, /define .*@main/);
assert.equal((await hylo.run(r.executable)).exitCode, 42);
console.log("${name}: loaded, compiled and ran a program");
`,
  );
  // Asynchronous: the server answering the program's requests runs in this process.
  await new Promise<void>((resolve, reject) => {
    const child = spawn(process.execPath, ["use.mjs", baseUrl], { cwd: project, stdio: "inherit" });
    child.on("exit", (code) =>
      code === 0 ? resolve() : reject(new Error(`use.mjs exited with ${code}`)),
    );
  });

  writeFileSync(
    path.join(project, "use.ts"),
    `import { load, type Compiler } from "${name}";
import type { CompileRequest, WorkerMessage } from "${name}/protocol";

const request: CompileRequest = { source: "public fun main() {}", emit: ["ir"] };
const hylo: Compiler = await load({ baseUrl: "https://example.com/" });
const ir: string | undefined = hylo.compile(request).artifacts.ir;
export const message: WorkerMessage | string | undefined = ir;
`,
  );
  writeFileSync(
    path.join(project, "tsconfig.json"),
    JSON.stringify({
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
  );
  sh(project, path.join(here, "../node_modules/.bin/tsc"), "-p", project);
  console.log(`${name}: its types check`);
} finally {
  server.close();
  rmSync(project, { recursive: true, force: true });
}
