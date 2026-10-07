// Monaco setup, after ABI Explorer's (src/ui/monaco.ts there): worker wiring, the themes, the Hylo
// language, and a small facade the panels drive.

import * as monaco from './monaco-slim';
import EditorWorker from 'monaco-editor/editor/editor.worker.js?worker';
import { THEMES, type Theme } from '../core/themes';
import { HYLO_LANGUAGE_ID, HYLO_TOKENS, HYLO_CONFIGURATION } from './hylo-language';

(self as unknown as { MonacoEnvironment: unknown }).MonacoEnvironment = {
  getWorker: () => new EditorWorker(),
};

const FONT = '"JetBrains Mono", ui-monospace, "SF Mono", Consolas, monospace';

monaco.languages.register({ id: HYLO_LANGUAGE_ID, extensions: ['.hylo'], aliases: ['Hylo'] });
monaco.languages.setLanguageConfiguration(HYLO_LANGUAGE_ID, HYLO_CONFIGURATION);
monaco.languages.setMonarchTokensProvider(HYLO_LANGUAGE_ID, HYLO_TOKENS);

for (const t of THEMES) monaco.editor.defineTheme(t.id, t.monaco);

/** Activates `t` in every editor on the page. */
export function setEditorTheme(t: Theme): void {
  monaco.editor.setTheme(t.id);
}

/** An issue to underline, at 1-based lines and columns. */
export interface Marker {
  level: string;
  message: string;
  line: number;
  column: number;
  endLine: number;
  endColumn: number;
}

/** What the app may ask of an editor. */
export interface EditorHandle {
  getValue(): string;
  /** Replaces the buffer as an edit, so undo reaches past it; not reported to `onChange`. */
  setValue(text: string): void;
  setMarkers(markers: Marker[]): void;
  /** Moves the caret to `line`:`column` and scrolls it into view. */
  reveal(line: number, column: number): void;
  onChange(cb: () => void): void;
  onSubmit(cb: () => void): void;
  dispose(): void;
}

let editorSeq = 0;

/**
 * Creates an editor in `container`. `language` is `hylo` for Hylo, or anything else for plain
 * text; a `readOnly` editor shows compiler output.
 */
export function createEditor(
  container: HTMLElement,
  opts: { value: string; theme: string; language: string; readOnly?: boolean },
): EditorHandle {
  const extension = opts.language === HYLO_LANGUAGE_ID ? 'hylo' : 'txt';
  const model = monaco.editor.createModel(
    opts.value,
    opts.language === HYLO_LANGUAGE_ID ? HYLO_LANGUAGE_ID : 'plaintext',
    monaco.Uri.parse(`inmemory://buffer-${String(++editorSeq)}.${extension}`),
  );
  const editor = monaco.editor.create(container, {
    model,
    theme: opts.theme,
    readOnly: opts.readOnly ?? false,
    domReadOnly: opts.readOnly ?? false,
    fontFamily: FONT,
    fontSize: opts.readOnly ? 12.5 : 13.5,
    fontLigatures: true,
    lineHeight: opts.readOnly ? 19 : 21,
    tabSize: 2,
    insertSpaces: true,
    minimap: { enabled: false },
    glyphMargin: !opts.readOnly,
    lineNumbersMinChars: 3,
    scrollBeyondLastLine: false,
    automaticLayout: true,
    renderLineHighlight: opts.readOnly ? 'none' : 'line',
    padding: { top: 12, bottom: 12 },
    smoothScrolling: true,
    cursorBlinking: 'smooth',
    cursorSmoothCaretAnimation: 'on',
    bracketPairColorization: { enabled: true },
    guides: { bracketPairs: 'active', indentation: true },
    scrollbar: { verticalScrollbarSize: 10, horizontalScrollbarSize: 10, useShadows: false },
    overviewRulerBorder: false,
    overviewRulerLanes: 0,
    hideCursorInOverviewRuler: true,
    fixedOverflowWidgets: true,
    quickSuggestions: false,
    suggestOnTriggerCharacters: false,
    wordBasedSuggestions: 'off',
    occurrencesHighlight: 'singleFile',
    stickyScroll: { enabled: false },
    wordWrap: 'off',
  });

  let suppress = false;
  const changeCbs: (() => void)[] = [];
  const submitCbs: (() => void)[] = [];
  model.onDidChangeContent(() => {
    if (!suppress) for (const cb of changeCbs) cb();
  });
  editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
    for (const cb of submitCbs) cb();
  });

  const severity: Record<string, monaco.MarkerSeverity> = {
    error: monaco.MarkerSeverity.Error,
    warning: monaco.MarkerSeverity.Warning,
    note: monaco.MarkerSeverity.Info,
  };

  return {
    getValue: () => model.getValue(),
    setValue(text) {
      if (text === model.getValue()) return;
      suppress = true;
      model.pushEditOperations([], [{ range: model.getFullModelRange(), text }], () => null);
      editor.setScrollTop(0);
      suppress = false;
    },
    setMarkers(markers) {
      const lines = model.getLineCount();
      monaco.editor.setModelMarkers(
        model,
        'hylo',
        markers
          .filter((m) => m.line >= 1 && m.line <= lines)
          .map((m) => ({
            severity: severity[m.level] ?? monaco.MarkerSeverity.Info,
            message: m.message,
            startLineNumber: m.line,
            startColumn: m.column,
            endLineNumber: Math.min(m.endLine, lines),
            // An empty range would draw nothing at all.
            endColumn:
              m.endLine === m.line ? Math.max(m.column + 1, m.endColumn) : m.endColumn,
            source: 'hylo',
          })),
      );
    },
    reveal(line, column) {
      editor.setPosition({ lineNumber: line, column });
      editor.revealLineInCenterIfOutsideViewport(line);
      editor.focus();
    },
    onChange(cb) {
      changeCbs.push(cb);
    },
    onSubmit(cb) {
      submitCbs.push(cb);
    },
    dispose() {
      editor.dispose();
      model.dispose();
    },
  };
}
