<script lang="ts">
  // The shell: the top bar and the dock the panels live in.
  import { onMount } from 'svelte';
  import { playground, applyThemeTokens } from './state.svelte';
  import { setEditorTheme } from './ui/monaco';
  import TopBar from './ui/TopBar.svelte';
  import { mountDock, forgetLayout } from './ui/dock';

  let dockHost: HTMLElement;
  let dock: ReturnType<typeof mountDock> | null = null;

  $effect(() => {
    applyThemeTokens(playground.theme);
    setEditorTheme(playground.theme);
  });

  onMount(() => {
    dock = mountDock(dockHost);
    return () => dock?.dispose();
  });

  function resetLayout(): void {
    forgetLayout();
    dock?.dispose();
    dock = mountDock(dockHost);
  }
</script>

<div class="app">
  <TopBar onResetLayout={resetLayout} />
  <main class="dock" bind:this={dockHost}></main>
</div>

<style>
  .app {
    height: 100vh;
    height: 100dvh;
    display: flex;
    flex-direction: column;
  }
  .dock {
    flex: 1;
    min-height: 0;
    padding: 10px 12px;
  }
  @media (max-width: 760px) {
    .dock {
      padding: 6px 8px;
    }
  }
</style>
