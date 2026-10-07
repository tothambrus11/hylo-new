<script lang="ts">
  // A read-only view of one of the compiler's intermediate representations.
  import { onMount } from 'svelte';
  import { playground, type Artifact } from '../state.svelte';
  import { createEditor, type EditorHandle } from './monaco';

  const { kind }: { kind: Artifact } = $props();
  let host: HTMLDivElement;
  let editor: EditorHandle | null = $state(null);

  const text = $derived.by(() => {
    const r = playground.result;
    if (r === null) return '';
    const a = r.compile.artifacts?.[kind];
    if (a !== undefined) return a;
    if (r.compile.error) return `// Not produced: ${r.compile.error.split('\n')[0]}`;
    return playground.errorCount > 0 ? '// Not produced: the program does not compile.' : '';
  });

  onMount(() => {
    const e = createEditor(host, {
      value: text,
      theme: playground.theme.id,
      language: 'plaintext',
      readOnly: true,
    });
    editor = e;
    return () => e.dispose();
  });
  $effect(() => {
    editor?.setValue(text);
  });
</script>

<section class="pane" class:stale={playground.stale}>
  <div class="editor" bind:this={host} role="region" aria-label="Compiler output"></div>
</section>

<style>
  .pane {
    height: 100%;
    display: flex;
    background: var(--surface-1);
    padding: 10px 12px;
    box-sizing: border-box;
  }
  .editor {
    flex: 1;
    overflow: hidden;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--editor-bg);
    transition: opacity 0.15s;
  }
  .stale .editor {
    opacity: 0.6;
  }
  .editor :global(.monaco-editor),
  .editor :global(.monaco-editor .overflow-guard) {
    border-radius: 8px;
  }
</style>
