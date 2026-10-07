<script lang="ts">
  // The bar above the dock: what to compile, how, and the button to do it now.
  import { playground } from '../state.svelte';
  import { EXAMPLES } from '../examples';
  import { THEMES } from '../core/themes';
  import Play from '@lucide/svelte/icons/play';
  import LayoutGrid from '@lucide/svelte/icons/layout-grid';
  import Link from '@lucide/svelte/icons/link';
  import { encodeSource } from '../share';

  const { onResetLayout }: { onResetLayout: () => void } = $props();
  const mod = /Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl+';
  let example = $state('');
  let shared = $state(false);

  /** Copies a link that opens this playground with the current source. */
  async function share(): Promise<void> {
    const url = `${location.origin}${location.pathname}#code=${await encodeSource(playground.source)}`;
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      // No clipboard (an insecure origin, say): the address bar carries it instead.
      history.replaceState(null, '', url);
    }
    shared = true;
    setTimeout(() => (shared = false), 1500);
  }
</script>

<header class="topbar">
  <div class="brand">
    <span class="brand-mark" aria-hidden="true">H</span>
    <h1>Hylo Playground</h1>
  </div>
  <div class="controls">
    <select
      class="input small"
      aria-label="Load an example"
      bind:value={example}
      onchange={() => {
        const e = EXAMPLES.find((x) => x.name === example);
        if (e) playground.edit(e.source);
        playground.compileNow();
        example = '';
      }}
    >
      <option value="" disabled>Examples…</option>
      {#each EXAMPLES as e (e.name)}<option value={e.name}>{e.name}</option>{/each}
    </select>
    <select
      class="input small"
      aria-label="Optimization level"
      value={String(playground.optimization)}
      onchange={(e) => playground.setOptimization(Number(e.currentTarget.value))}
    >
      {#each [0, 1, 2, 3] as o (o)}<option value={String(o)}>-O{o}</option>{/each}
    </select>
  </div>
  <div class="actions">
    <select
      class="input small"
      aria-label="Theme"
      value={playground.themeId}
      onchange={(e) => playground.setTheme(e.currentTarget.value)}
    >
      {#each THEMES as t (t.id)}<option value={t.id}>{t.name}</option>{/each}
    </select>
    <button class="icon-btn" aria-label="Copy a link to this code" title={shared ? 'Link copied' : 'Copy a link to this code'} onclick={share}>
      <Link size={16} />
    </button>
    <button class="icon-btn" aria-label="Reset the panel layout" title="Reset the panel layout" onclick={onResetLayout}>
      <LayoutGrid size={16} />
    </button>
    <button
      class="btn run"
      disabled={playground.compiler.kind !== 'ready'}
      onclick={() => playground.compileNow()}
      title="Compile and run ({mod}Enter)"
    >
      <Play size={14} /> Run
    </button>
  </div>
</header>

<style>
  .topbar {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-wrap: wrap;
    padding: 10px 20px;
    background: var(--surface-1);
    border-bottom: 1px solid var(--border);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .brand-mark {
    display: inline-grid;
    place-items: center;
    width: 22px;
    height: 22px;
    border-radius: 6px;
    background: var(--accent);
    color: var(--on-accent);
    font-weight: 700;
    font-size: 13px;
  }
  h1 {
    font-size: 17px;
    margin: 0;
    font-weight: 650;
  }
  .controls {
    display: flex;
    gap: 8px;
    margin-right: auto;
  }
  .actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .run {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--accent);
    border-color: var(--accent);
    color: var(--on-accent);
    font-weight: 600;
  }
  .run:hover {
    border-color: var(--accent);
    filter: brightness(1.08);
  }
  .run:disabled {
    opacity: 0.5;
    cursor: default;
  }
  @media (max-width: 760px) {
    .topbar {
      padding: 6px 10px;
      gap: 8px;
    }
    h1 {
      display: none;
    }
  }
</style>
