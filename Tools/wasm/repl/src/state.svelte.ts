// The playground's state: the source, what the compiler said about it, and the compiler itself.

import { THEMES, DEFAULT_DARK, DEFAULT_LIGHT, type Theme } from './core/themes';
import { EXAMPLES } from './examples';
import CompilerWorker from './compiler.worker?worker';

export interface Diagnostic {
  level: 'error' | 'warning' | 'note';
  message: string;
  rendered: string;
  site: { line: number; column: number; endLine: number; endColumn: number };
}

export interface Result {
  compile: {
    diagnostics?: Diagnostic[];
    artifacts?: Partial<Record<Artifact, string>>;
    error?: string;
    milliseconds?: number;
    executableBytes?: number;
  };
  run: { exitCode: number | null; trap?: string; stdout: string; stderr: string } | null;
}

export type Artifact = 'raw-ir' | 'ir' | 'llvm' | 'assembly';

export type CompilerState =
  | { kind: 'loading'; loaded: number; total: number }
  | { kind: 'ready'; standardLibraryMilliseconds: number }
  | { kind: 'failed'; error: string };

/** Reads `key` from local storage, which may be unavailable. */
function recall(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

/** Writes `value` to local storage, if it is available. */
function remember(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Not remembering is fine.
  }
}

const prefersDark = (): boolean => matchMedia('(prefers-color-scheme: dark)').matches;

class Playground {
  source = $state(recall('hylo-playground:source') ?? EXAMPLES[0].source);
  optimization = $state(Number(recall('hylo-playground:optimization') ?? 0));
  themeId = $state(recall('hylo-playground:theme') ?? (prefersDark() ? DEFAULT_DARK : DEFAULT_LIGHT));
  compiler: CompilerState = $state({ kind: 'loading', loaded: 0, total: 0 });
  result: Result | null = $state(null);
  /** Whether the source has changed since the result was computed, or a compile is running. */
  stale = $state(true);
  compiling = $state(false);

  /** A request to move the editor's caret, made by clicking a diagnostic. */
  reveal: { line: number; column: number; seq: number } | null = $state(null);

  theme: Theme = $derived(THEMES.find((t) => t.id === this.themeId) ?? THEMES[0]);
  diagnostics: Diagnostic[] = $derived(this.result?.compile.diagnostics ?? []);
  errorCount = $derived(this.diagnostics.filter((d) => d.level === 'error').length);

  #worker = new CompilerWorker();
  #sent = 0;
  #pending = false;
  #debounce: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    this.#worker.onmessage = ({ data }) => {
      if (data.type === 'progress') {
        this.compiler = { kind: 'loading', loaded: data.loaded, total: data.total };
      } else if (data.type === 'ready') {
        this.compiler = { kind: 'ready', standardLibraryMilliseconds: data.standardLibraryMilliseconds };
      } else if (data.type === 'failed') {
        this.compiler = { kind: 'failed', error: data.error };
        this.compiling = false;
      } else if (data.type === 'result' && data.id === this.#sent) {
        this.result = { compile: data.compile, run: data.run };
        this.compiling = false;
        this.stale = false;
        if (this.#pending) this.compileNow();
      }
    };
    this.compileNow();
  }

  /** Replaces the source, as typing does. */
  edit(text: string): void {
    if (text === this.source) return;
    this.source = text;
    this.stale = true;
    remember('hylo-playground:source', text);
    if (this.#debounce) clearTimeout(this.#debounce);
    this.#debounce = setTimeout(() => this.compileNow(), 350);
  }

  setOptimization(level: number): void {
    this.optimization = level;
    remember('hylo-playground:optimization', String(level));
    this.compileNow();
  }

  setTheme(id: string): void {
    this.themeId = id;
    remember('hylo-playground:theme', id);
  }

  /** Compiles and runs the source, after the compile in flight if there is one. */
  compileNow(): void {
    if (this.#debounce) clearTimeout(this.#debounce);
    if (this.compiling) {
      this.#pending = true;
      return;
    }
    this.#pending = false;
    this.compiling = true;
    this.#worker.postMessage({ id: ++this.#sent, source: this.source, optimization: this.optimization });
  }
}

export const playground = new Playground();

/** Applies `t`'s page colours, as ABI Explorer does. */
export function applyThemeTokens(t: Theme): void {
  const root = document.documentElement;
  for (const [k, v] of Object.entries(t.tokens)) root.style.setProperty(k, v);
  root.dataset['theme'] = t.mode;
  root.style.colorScheme = t.mode;
}
