/**
 * A Web Worker running programs the compiler produced, one at a time, apart from the compiler's
 * worker (`compiler-worker.ts`): a page can terminate it to stop a program that runs too long, or whose
 * result is no longer wanted, without losing the compiler and its compiled standard library.
 *
 * With Vite, for example:
 *
 * ```ts
 * import ProgramWorker from "@hylo-lang/hylo-wasm/program-worker?worker";
 *
 * const worker = new ProgramWorker();
 * worker.postMessage({ id: 1, executable }, [executable.buffer]);
 * ```
 *
 * It answers every `ProgramWorkerRequest` with a `ProgramWorkerResult`; see `protocol.ts`.
 *
 * @module
 */

import { run } from "./core.ts";
import type { ProgramWorkerRequest, ProgramWorkerResult } from "./protocol.ts";

// The parts of a dedicated worker's global scope this uses; see `compiler-worker.ts`.
declare const self: {
  postMessage(message: ProgramWorkerResult): void;
  onmessage: ((event: MessageEvent<ProgramWorkerRequest>) => void) | null;
};

// Programs are run one at a time, in order.
let queue = Promise.resolve();
self.onmessage = ({
  data: { id, executable, args, stdin },
}: MessageEvent<ProgramWorkerRequest>) => {
  queue = queue.then(async () => {
    try {
      self.postMessage({ type: "ran", id, execution: await run(executable, { args, stdin }) });
    } catch (thrown) {
      const error = thrown instanceof Error ? (thrown.stack ?? thrown.message) : String(thrown);
      self.postMessage({ type: "failed", id, error });
    }
  });
};
