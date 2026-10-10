/**
 * A Web Worker hosting the compiler, for pages that would rather not block their main thread on
 * it, and that may have several things to compile: one worker serves them all, and loads the
 * compiler once.
 *
 * With Vite, for example:
 *
 * ```ts
 * import CompilerWorker from "@hylo-lang/hylo-wasm/compiler-worker?worker";
 *
 * const worker = new CompilerWorker();
 * worker.postMessage({ id: 1, request: { source, emit: ["executable", "llvm"] } });
 * ```
 *
 * It answers every `CompilerWorkerRequest` with a `result` message (with the executable instead
 * of what running it did, if the request asks not to `run` it), which `stage` messages may
 * precede with what compiling produced so far, and reports on loading with `progress`, `ready`
 * and `failed` messages; see `CompilerWorkerMessage`. A compiler that traps loses its instance,
 * and with it the compiled standard library; so does one that reports it cannot serve further
 * requests. The request is then answered with an error and `compilation.compilerUnusable`, and
 * the compiler is instantiated again for the next, which is announced by another `ready`.
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
  CompilerWorkerMessage,
  CompilerWorkerRequest,
} from "./protocol.ts";

// The parts of a dedicated worker's global scope this uses, declared here rather than through the
// `webworker` library, which would change the globals of every program importing this module.
declare const self: {
  postMessage(message: CompilerWorkerMessage, transfer?: Transferable[]): void;
  onmessage: ((event: MessageEvent<CompilerWorkerRequest>) => void) | null;
};

/** Sends `message` to the page. */
const send = (message: CompilerWorkerMessage): void => self.postMessage(message);

// The compiler is downloaded once; one that must be replaced is instantiated anew from it.
const compilerParts = loadParts({
  onProgress: ({ loaded, total }) => send({ type: "progress", loaded, total }),
});
/** The compiler, once instantiated; replaced by `instantiateCompiler`. */
let instantiation: Promise<Compiler>;

/** Starts instantiating the compiler, anew, and says when it is ready or why it failed. */
function instantiateCompiler(): void {
  instantiation = compilerParts.then(instantiate);
  instantiation.then(
    (compiler) =>
      send({ type: "ready", standardLibraryMilliseconds: compiler.standardLibraryMilliseconds }),
    (error) => send({ type: "failed", error: describe(error) }),
  );
}
instantiateCompiler();

// Requests are served one at a time, in order. A request that fails unexpectedly is still
// answered, and does not hold up the ones after it.
let queue = Promise.resolve();
self.onmessage = ({ data: { id, request, run = true } }: MessageEvent<CompilerWorkerRequest>) => {
  queue = queue
    .then(() => serve(id, request, run))
    .catch((error) => answerWithError(id, `the request could not be served: ${describe(error)}`));
};

/**
 * Compiles `request`, runs the result if `run` is set, and answers with what happened (with the
 * executable instead, if `run` is not set), sending what each stage produced as soon as it is
 * done; see `CompilerWorkerStage`.
 */
async function serve(id: number, request: CompileRequest, run: boolean): Promise<void> {
  let compiler: Compiler;
  try {
    compiler = await instantiation;
  } catch (error) {
    answerWithError(id, `the compiler failed to load: ${describe(error)}`);
    return;
  }

  let response: CompileResponse;
  try {
    response = compiler.compile(request, {
      onFrontEnd: (compilation) => send({ type: "stage", id, stage: "front-end", compilation }),
    });
  } catch (error) {
    const reason = `the compiler crashed (${describe(error)}); this is a compiler bug`;
    answerWithError(id, reason, { compilerUnusable: true });
    instantiateCompiler();
    return;
  }
  if (!compiler.usable) instantiateCompiler();

  const { executable, ...rest } = response;
  const compilation = executable ? { ...rest, executableByteCount: executable.length } : rest;
  if (!run && executable) {
    // Handed over rather than copied.
    const result = { type: "result", id, compilation, execution: null, executable } as const;
    self.postMessage(result, [executable.buffer]);
    return;
  }
  let execution: Execution | null = null;
  if (executable) {
    send({ type: "stage", id, stage: "back-end", compilation });
    execution = await compiler.run(executable);
  }
  send({ type: "result", id, compilation, execution });
}

/**
 * Answers request `id` with `error`, saying why it could not be served, and with
 * `compilerUnusable` if the compiler is being replaced because of it.
 */
function answerWithError(id: number, error: string, { compilerUnusable = false } = {}): void {
  send({
    type: "result",
    id,
    compilation: {
      diagnostics: [],
      artifacts: {},
      error,
      ...(compilerUnusable && { compilerUnusable }),
      milliseconds: 0,
    },
    execution: null,
  });
}

/** Returns a description of `thrown`, a thrown value. */
function describe(thrown: unknown): string {
  return thrown instanceof Error ? (thrown.stack ?? thrown.message) : String(thrown);
}
