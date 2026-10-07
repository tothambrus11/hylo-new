<script lang="ts">
  // A dock tab carrying its panel's state, as in ABI Explorer: whether the source compiled sits on
  // the Source tab, and how many errors there are on the Diagnostics tab.
  import { playground } from '../state.svelte';
  import Check from '@lucide/svelte/icons/check';
  import X from '@lucide/svelte/icons/x';
  import Zap from '@lucide/svelte/icons/zap';
  import LoaderCircle from '@lucide/svelte/icons/loader-circle';
  import { TITLES, type PanelKind } from './panels';

  const { kind }: { kind: PanelKind } = $props();

  const status = $derived.by(() => {
    const r = playground.result;
    if (playground.compiling || playground.compiler.kind === 'loading') return 'running';
    if (r === null) return 'idle';
    if (r.compile.error || r.run === null) return 'error';
    return r.run.trap !== undefined ? 'trap' : 'ok';
  });
  const statusText = $derived(
    { running: 'compiling…', idle: '', error: 'does not compile', trap: 'compiled; trapped', ok: 'compiled and ran' }[
      status
    ],
  );
</script>

<span class="tab">
  {#if kind === 'source'}
    <span class="status {status}" role="status" aria-live="polite" aria-label={statusText} title={statusText}>
      {#if status === 'running'}<LoaderCircle size={13} class="spin" />
      {:else if status === 'ok'}<Check size={13} />
      {:else if status === 'trap'}<Zap size={13} />
      {:else if status === 'error'}<X size={13} />{/if}
    </span>
  {/if}
  <span class="title">{TITLES[kind]}</span>
  {#if kind === 'diagnostics' && playground.diagnostics.length > 0}
    <span class="count" class:bad={playground.errorCount > 0}>[{playground.diagnostics.length}]</span>
  {/if}
</span>

<style>
  .tab {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    min-width: 0;
    padding: 0 6px;
    user-select: none;
    -webkit-user-select: none;
  }
  .title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .status {
    display: inline-flex;
    align-items: center;
    color: var(--text-muted);
  }
  .status.ok {
    color: var(--ok-ink);
  }
  .status.trap {
    color: var(--warn-ink);
  }
  .status.error,
  .count.bad {
    color: var(--error);
  }
  .count {
    font-size: 11px;
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
  }
</style>
