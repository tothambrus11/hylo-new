<script lang="ts">
  // What the compiler found, as it renders it; a click takes the editor to the site.
  import { playground } from '../state.svelte';
  import CircleX from '@lucide/svelte/icons/circle-x';
  import TriangleAlert from '@lucide/svelte/icons/triangle-alert';
  import Info from '@lucide/svelte/icons/info';

  let seq = 0;
  const diagnostics = $derived(playground.diagnostics);
</script>

<section class="pane" class:stale={playground.stale}>
  {#if diagnostics.length === 0}
    <p class="empty">{playground.result ? 'No diagnostics.' : ''}</p>
  {:else}
    <ul>
      {#each diagnostics as d, i (i)}
        <li class={d.level}>
          <button
            type="button"
            onclick={() => (playground.reveal = { line: d.site.line, column: d.site.column, seq: ++seq })}
          >
            <span class="icon">
              {#if d.level === 'error'}<CircleX size={15} />
              {:else if d.level === 'warning'}<TriangleAlert size={15} />
              {:else}<Info size={15} />{/if}
            </span>
            <span class="body">
              <span class="message">{d.message}</span>
              <span class="site">line {d.site.line}, column {d.site.column}</span>
              <pre>{d.rendered.split('\n').slice(1).join('\n').trimEnd()}</pre>
            </span>
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</section>

<style>
  .pane {
    height: 100%;
    overflow: auto;
    padding: 10px 12px;
    background: var(--surface-1);
    box-sizing: border-box;
    transition: opacity 0.15s;
  }
  .stale {
    opacity: 0.6;
  }
  .empty {
    color: var(--text-muted);
    padding: 8px;
    margin: 0;
  }
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  button {
    display: flex;
    gap: 10px;
    width: 100%;
    text-align: left;
    font: inherit;
    color: inherit;
    padding: 10px 12px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--page);
    cursor: pointer;
  }
  button:hover {
    border-color: var(--baseline);
  }
  button:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 1px;
  }
  .icon {
    flex: none;
    padding-top: 2px;
  }
  .error .icon {
    color: var(--error);
  }
  .warning .icon {
    color: var(--warn-ink);
  }
  .note .icon {
    color: var(--text-muted);
  }
  .body {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }
  .message {
    font-weight: 500;
  }
  .site {
    font-size: 12px;
    color: var(--text-muted);
  }
  pre {
    margin: 6px 0 0;
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-secondary);
    overflow: auto;
  }
</style>
