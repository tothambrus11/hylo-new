/**
 * A Web Worker hosting the compiler, for pages that would rather not block their main thread on
 * it, and that may have several things to compile: one worker serves them all, and loads the
 * compiler once.
 *
 * With Vite, for example:
 *
 * ```ts
 * import HyloWorker from "@hylo-lang/hylo-wasm/worker?worker";
 *
 * const w = new HyloWorker();
 * w.postMessage({ id: 1, request: { source, emit: ["executable", "llvm"] } });
 * ```
 *
 * It answers every `WorkerRequest` with a `result` message, which `stage` messages may precede
 * with what compiling produced so far, and reports on loading with `progress`, `ready` and
 * `failed` messages; see `WorkerMessage`. A compiler that traps loses its instance, and with it
 * the compiled standard library; so does one that reports it cannot serve further requests. The request is then answered with an error and `compile.compilerUnusable`,
 * and the compiler is instantiated again for the next, which is announced by another `ready`.
 * Requests sent meanwhile wait for it. A compiler that fails to load (`failed`) is not loaded
 * again: every later request is answered with an error, and the page replaces the worker.
 *
 * @module
 */

import { type Compiler, instantiate, loadParts } from "./index.ts";
import type {
  CompileRequest,
  CompileResponse,
  Execution,
  WorkerMessage,
  WorkerRequest,
} from "./protocol.ts";

// The parts of a dedicated worker's global scope this uses, declared here rather than through the
// `webworker` library, which would change the globals of every program importing this module.
declare const self: {
  postMessage(message: WorkerMessage): void;
  onmessage: ((event: MessageEvent<WorkerRequest>) => void) | null;
};

/** Sends `message` to the page. */
const send = (message: WorkerMessage): void => self.postMessage(message);

// The compiler is downloaded once; one that must be replaced is instantiated anew from it.
const parts = loadParts({
  onProgress: ({ loaded, total }) => send({ type: "progress", loaded, total }),
});
let hylo: Promise<Compiler>;

/** Starts instantiating the compiler, anew. */
function start(): void {
  hylo = parts.then(instantiate);
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
      fail(id, error);
    });
};

/**
 * Compiles `request`, runs the result if `run` is set, and answers with what happened, sending
 * what each stage produced as soon as it is done; see `WorkerStage`.
 */
async function serve(id: number, request: CompileRequest, run: boolean): Promise<void> {
  let h: Compiler;
  try {
    h = await hylo;
  } catch (e) {
    const error = `the compiler failed to load: ${describe(e)}`;
    fail(id, error);
    return;
  }

  let compiled: CompileResponse;
  try {
    compiled = h.compile(request, {
      onFrontEnd: (compile) => send({ type: "stage", id, stage: "front-end", compile }),
    });
  } catch (e) {
    const error = `the compiler crashed (${describe(e)}); this is a compiler bug`;
    fail(id, error, { compilerUnusable: true });
    start();
    return;
  }
  if (!h.usable) start();

  const { executable, ...rest } = compiled;
  const compile = executable ? { ...rest, executableBytes: executable.length } : rest;
  let outcome: Execution | null = null;
  if (run && executable) {
    send({ type: "stage", id, stage: "back-end", compile });
    outcome = await h.run(executable);
  }
  send({ type: "result", id, compile, run: outcome });
}

/**
 * Answers request `id` with `error`, saying why it could not be served, and with
 * `compilerUnusable` if the compiler is being replaced because of it.
 */
function fail(id: number, error: string, { compilerUnusable = false } = {}): void {
  send({
    type: "result",
    id,
    compile: {
      diagnostics: [],
      artifacts: {},
      error,
      ...(compilerUnusable && { compilerUnusable }),
      milliseconds: 0,
    },
    run: null,
  });
}

/** Returns a description of `e`, a thrown value. */
function describe(e: unknown): string {
  return e instanceof Error ? (e.stack ?? e.message) : String(e);
}
