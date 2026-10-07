// Runs the compiler off the page's main thread: loading it takes seconds, and so may compiling.
//
// In:  { id, source, optimization }
// Out: { type: 'progress', loaded, total } | { type: 'ready', standardLibraryMilliseconds }
//      | { type: 'failed', error } | { type: 'result', id, compile, run }

// @ts-expect-error: the loader is plain JavaScript.
import { load } from '../../js/index.mjs';

// The compiler's release is served beside the app, under `compiler/`.
const hylo = load({
  baseUrl: new URL('../compiler/', import.meta.url),
  onProgress: ({ loaded, total }: { loaded: number; total: number }) =>
    postMessage({ type: 'progress', loaded, total }),
});

hylo.then(
  (h: { standardLibraryMilliseconds: number }) =>
    postMessage({ type: 'ready', standardLibraryMilliseconds: h.standardLibraryMilliseconds }),
  (e: Error) => postMessage({ type: 'failed', error: String(e.stack ?? e) }),
);

onmessage = async ({ data: { id, source, optimization } }) => {
  const h = await hylo;
  let compile;
  try {
    compile = h.compile({
      source,
      optimization,
      emit: ['raw-ir', 'ir', 'llvm', 'assembly', 'executable'],
    });
  } catch (e) {
    // A trap in the compiler takes its instance with it; say so rather than hang.
    postMessage({ type: 'result', id, compile: { error: `The compiler crashed: ${String(e)}` } });
    return;
  }
  const run = compile.executable ? await h.run(compile.executable) : null;
  if (compile.executable) compile.executableBytes = compile.executable.length;
  delete compile.executable;
  postMessage({ type: 'result', id, compile, run });
};
