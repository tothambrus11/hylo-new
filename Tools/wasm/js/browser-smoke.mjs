// Checks that a packaged release works in a browser the way its consumers use it: a page imports
// the release's `index.mjs`, loads the compiler through `manifest.json`, compiles a program and
// runs it, all in Chromium.
//
//   node browser-smoke.mjs <release>
//
// Requires the `playwright` package, which is not a dependency of the loader: set
// PLAYWRIGHT_MODULE to its entry point if it is not resolvable from here, and CHROMIUM to a
// browser executable to use instead of Playwright's own.

import { readFileSync, existsSync } from "node:fs";
import { createServer } from "node:http";
import path from "node:path";

const release = process.argv[2];
if (release === undefined) {
  console.error("usage: node browser-smoke.mjs <release>");
  process.exit(2);
}
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE ?? "playwright");

const page = `<!doctype html>
<script type="module">
  import { load } from "./index.mjs";
  try {
    const hylo = await load({ baseUrl: "./" });
    const source = "public fun main() -> Int32 {\\n  var x = 40\\n  &x = x + 2\\n"
      + "  return if x == 42 { 42 } else { 1 }\\n}\\n";
    const r = hylo.compile({ source, emit: ["executable", "llvm"] });
    if (!r.executable) throw new Error(JSON.stringify({ error: r.error, diagnostics: r.diagnostics }));
    const x = await hylo.run(r.executable);
    window.result = {
      exitCode: x.exitCode, diagnostics: r.diagnostics, llvmIRLength: r.artifacts.llvm.length,
      standardLibraryMilliseconds: hylo.standardLibraryMilliseconds, compileMilliseconds: r.milliseconds,
    };
  } catch (e) {
    window.result = { error: String(e.stack ?? e) };
  }
</script>`;

const types = { ".mjs": "text/javascript", ".wasm": "application/wasm", ".json": "application/json" };
const server = createServer((request, response) => {
  const name = decodeURIComponent(new URL(request.url, "http://x").pathname.slice(1));
  if (name === "" || name === "index.html") {
    response.writeHead(200, { "content-type": "text/html" }).end(page);
    return;
  }
  const file = path.join(release, path.basename(name));
  if (!existsSync(file)) {
    response.writeHead(404).end();
    return;
  }
  const type = types[path.extname(file)] ?? "application/octet-stream";
  response.writeHead(200, { "content-type": type }).end(readFileSync(file));
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));

const browser = await chromium.launch(
  process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {},
);
try {
  const tab = await browser.newPage();
  await tab.goto(`http://127.0.0.1:${server.address().port}/`);
  await tab.waitForFunction(() => window.result !== undefined, null, { timeout: 120_000 });
  const result = await tab.evaluate(() => window.result);
  console.log(result);
  if (result.error !== undefined || result.exitCode !== 42 || result.diagnostics.length !== 0) {
    process.exitCode = 1;
  }
} finally {
  await browser.close();
  server.close();
}
