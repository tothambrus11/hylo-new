// A Web Worker hosting the compiler, for pages that would rather not block their main thread on
// it, and that may have several things to compile: one worker serves them all, and loads the
// compiler once.
//
// A release ships it bundled next to `manifest.json`, which it loads from its own directory:
//
//   const w = new Worker(new URL("worker.mjs", releaseBase), { type: "module" });
//   w.postMessage({ id: 1, request: { source, emit: ["executable", "llvm"] }, run: true });
//
// Messages out:
//   { type: "progress", loaded, total }       while downloading
//   { type: "ready", standardLibraryMilliseconds }
//   { type: "failed", error }                 the compiler could not be loaded
//   { type: "result", id, compile, run }      `compile` as `hylo.compile` returns it, with the
//                                             executable's size in `executableBytes`; `run` as
//                                             `run` returns it, or null
//
// A compiler that traps loses its instance, and with it the compiled standard library. The
// request is then answered with `compile.error`, and the compiler is loaded again for the next.

import { load } from "./index.mjs";

const base = new URL("./", import.meta.url);
let hylo;

function start() {
  hylo = load({
    baseUrl: base,
    onProgress: ({ loaded, total }) => postMessage({ type: "progress", loaded, total }),
  });
  hylo.then(
    (h) => postMessage({ type: "ready", standardLibraryMilliseconds: h.standardLibraryMilliseconds }),
    (e) => postMessage({ type: "failed", error: String(e?.stack ?? e) }),
  );
}
start();

// Requests are served one at a time, in order.
let queue = Promise.resolve();
onmessage = ({ data: { id, request, run = true } }) => {
  queue = queue.then(() => serve(id, request, run));
};

async function serve(id, request, run) {
  let h;
  try {
    h = await hylo;
  } catch (e) {
    postMessage({ type: "result", id, compile: { error: `the compiler failed to load: ${e}` }, run: null });
    return;
  }
  let compile;
  try {
    compile = h.compile(request);
  } catch (e) {
    postMessage({
      type: "result",
      id,
      compile: { error: `the compiler crashed (${e?.message ?? e}); this is a compiler bug` },
      run: null,
    });
    start();
    return;
  }
  const executable = compile.executable;
  delete compile.executable;
  if (executable) compile.executableBytes = executable.length;
  const outcome = run && executable ? await h.run(executable) : null;
  postMessage({ type: "result", id, compile, run: outcome });
}
