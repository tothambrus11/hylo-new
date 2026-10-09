/**
 * A Web Worker hosting the compiler, for pages that would rather not block their main thread on
 * it, and that may have several things to compile: one worker serves them all, and loads the
 * compiler once.
 *
 * The worker loads the compiler release named by its URL's `compiler` parameter, or the one in its
 * own directory, which is where a release ships it, bundled:
 *
 * ```ts
 * const w = new Worker(new URL("worker.mjs", releaseBase), { type: "module" });
 * w.postMessage({ id: 1, request: { source, emit: ["executable", "llvm"] } });
 * ```
 *
 * It answers every `WorkerRequest` with a `result` message, and reports on loading with
 * `progress`, `ready` and `failed` messages; see `WorkerMessage`. A compiler that traps loses its
 * instance, and with it the compiled standard library; so does one that reports it cannot serve
 * further requests. The request is then answered with an error, and the compiler is loaded again
 * for the next.
 *
 * @module
 */

import { type Compiler, load } from "./index.ts";
import type { WorkerMessage, WorkerRequest } from "./protocol.ts";

// The parts of a dedicated worker's global scope this uses, declared here rather than through the
// `webworker` library, which would change the globals of every program importing this module.
declare const self: {
  postMessage(message: WorkerMessage): void;
  onmessage: ((event: MessageEvent<WorkerRequest>) => void) | null;
};

const base = new URL(
  new URL(import.meta.url).searchParams.get("compiler") ?? "./",
  import.meta.url,
);
let hylo: Promise<Compiler>;

/** Sends `message` to the page. */
const send = (message: WorkerMessage): void => self.postMessage(message);

/** Starts loading the compiler, anew. */
function start(): void {
  hylo = load({
    baseUrl: base,
    onProgress: ({ loaded, total }) => send({ type: "progress", loaded, total }),
  });
  hylo.then(
    (h) => send({ type: "ready", standardLibraryMilliseconds: h.standardLibraryMilliseconds }),
    (e) => send({ type: "failed", error: describe(e) }),
  );
}
start();

// Requests are served one at a time, in order. A request that fails unexpectedly is still
// answered, and does not hold up the ones after it.
let queue = Promise.resolve();
self.onmessage = ({ data: { id, request, run = true } }: MessageEvent<WorkerRequest>) => {
  queue = queue
    .then(() => serve(id, request, run))
    .catch((e) => {
      const error = `the request could not be served: ${describe(e)}`;
      send({ type: "result", id, compile: { error }, run: null });
    });
};

/** Compiles `request`, runs the result if `run` is set, and answers with what happened. */
async function serve(id: number, request: WorkerRequest["request"], run: boolean): Promise<void> {
  let h: Compiler;
  try {
    h = await hylo;
  } catch (e) {
    const error = `the compiler failed to load: ${describe(e)}`;
    send({ type: "result", id, compile: { error }, run: null });
    return;
  }

  let compiled: ReturnType<Compiler["compile"]>;
  try {
    compiled = h.compile(request);
  } catch (e) {
    const error = `the compiler crashed (${describe(e)}); this is a compiler bug`;
    send({ type: "result", id, compile: { error }, run: null });
    start();
    return;
  }
  if (!h.usable) start();

  const { executable, ...compile } = compiled;
  const outcome = run && executable ? await h.run(executable) : null;
  send({
    type: "result",
    id,
    compile: executable ? { ...compile, executableBytes: executable.length } : compile,
    run: outcome,
  });
}

/** Returns a description of `e`, a thrown value. */
function describe(e: unknown): string {
  return e instanceof Error ? (e.stack ?? e.message) : String(e);
}
