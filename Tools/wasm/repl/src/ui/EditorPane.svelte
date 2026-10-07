<script lang="ts">
  // The source editor: writes the buffer back on every keystroke and underlines what the
  // compiler found.
  import { onMount } from 'svelte';
  import { playground } from '../state.svelte';
  import { createEditor, type EditorHandle } from './monaco';

  let host: HTMLDivElement;
  let editor: EditorHandle | null = $state(null);

  onMount(() => {
    const e = createEditor(host, {
      value: playground.source,
      theme: playground.theme.id,
      language: 'hylo',
    });
    e.onChange(() => playground.edit(e.getValue()));
    e.onSubmit(() => playground.compileNow());
    editor = e;
    return () => e.dispose();
  });

  $effect(() => {
    editor?.setValue(playground.source);
  });
  $effect(() => {
    // Markers describe the source they were computed for; while it is being edited they would
    // point at the wrong places, so they are cleared until the next result.
    const stale = playground.stale;
    editor?.setMarkers(
      stale ? [] : playground.diagnostics.map((d) => ({ level: d.level, message: d.message, ...d.site })),
    );
  });
  $effect(() => {
    const r = playground.reveal;
    if (r) editor?.reveal(r.line, r.column);
  });
</script>

<section class="pane">
  <div class="editor" bind:this={host} role="region" aria-label="Hylo source"></div>
</section>

<style>
  .pane {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--surface-1);
    padding: 10px 12px;
    box-sizing: border-box;
  }
  .editor {
    flex: 1;
    min-height: 120px;
    width: 100%;
    overflow: hidden;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--editor-bg);
  }
  .editor:focus-within {
    border-color: var(--accent);
  }
  .editor :global(.monaco-editor),
  .editor :global(.monaco-editor .overflow-guard) {
    border-radius: 8px;
  }
</style>
