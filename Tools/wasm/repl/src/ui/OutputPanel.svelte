<script lang="ts">
  // What running the program did, or why it could not run.
  import { playground } from '../state.svelte';
  import Check from '@lucide/svelte/icons/check';
  import X from '@lucide/svelte/icons/x';
  import Zap from '@lucide/svelte/icons/zap';
  import LoaderCircle from '@lucide/svelte/icons/loader-circle';

  const r = $derived(playground.result);
  const c = $derived(playground.compiler);
</script>

<section class="pane" class:stale={playground.stale && r !== null}>
  {#if c.kind === 'failed'}
    <p class="headline bad"><X size={18} /> The compiler failed to load.</p>
    <pre>{c.error}</pre>
  {:else if r === null}
    <p class="headline muted">
      <LoaderCircle size={18} class="spin" />
      {#if c.kind === 'loading' && c.total > 0 && c.loaded < c.total}
        Downloading the compiler… {Math.round((100 * c.loaded) / c.total)}%
      {:else}
        Compiling the standard library…
      {/if}
    </p>
    {#if c.kind === 'loading' && c.total > 0}
      <progress max={c.total} value={c.loaded}></progress>
      <p class="muted small">
        {(c.total / 1048576).toFixed(0)} MB, once: the whole Hylo compiler, LLVM included, runs in this
        page.
      </p>
    {/if}
  {:else if r.compile.error}
    <p class="headline bad"><X size={18} /> Internal error</p>
    <pre>{r.compile.error}</pre>
  {:else if r.run === null}
    <p class="headline bad"><X size={18} /> Does not compile</p>
    <p class="muted">
      {playground.errorCount} error{playground.errorCount === 1 ? '' : 's'}; see Diagnostics.
    </p>
  {:else if r.run.trap !== undefined}
    <p class="headline warn"><Zap size={18} /> The program trapped</p>
    <p class="muted mono">{r.run.trap}</p>
  {:else}
    <p class="headline" class:ok={r.run.exitCode === 0}>
      <Check size={18} /> Exited with status <span class="mono status">{r.run.exitCode}</span>
    </p>
  {/if}

  {#if r?.run?.stdout}
    <h3>Standard output</h3>
    <pre>{r.run.stdout}</pre>
  {/if}
  {#if r?.run?.stderr}
    <h3>Standard error</h3>
    <pre>{r.run.stderr}</pre>
  {/if}

  {#if r && !r.compile.error}
    <p class="muted small footer">
      Compiled{r.run ? ', linked and ran' : ''} in {r.compile.milliseconds?.toFixed(0)} ms{r.compile
        .executableBytes
        ? ` · ${r.compile.executableBytes.toLocaleString()} bytes of WebAssembly`
        : ''}{c.kind === 'ready'
        ? ` · standard library compiled in ${(c.standardLibraryMilliseconds / 1000).toFixed(1)} s at load`
        : ''}
    </p>
  {/if}
</section>

<style>
  .pane {
    height: 100%;
    overflow: auto;
    padding: 18px 20px;
    background: var(--surface-1);
    box-sizing: border-box;
    transition: opacity 0.15s;
  }
  .stale {
    opacity: 0.6;
  }
  .headline {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 0 0 8px;
    font-size: 17px;
    font-weight: 600;
  }
  .status {
    font-size: 20px;
  }
  .ok {
    color: var(--ok-ink);
  }
  .bad {
    color: var(--error);
  }
  .warn {
    color: var(--warn-ink);
  }
  .muted {
    color: var(--text-secondary);
  }
  .small {
    font-size: 12px;
  }
  .footer {
    margin-top: 24px;
  }
  .mono {
    font-family: var(--font-mono);
  }
  h3 {
    margin: 18px 0 6px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--text-muted);
  }
  pre {
    margin: 0;
    padding: 10px 12px;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--editor-bg);
    font-size: 12.5px;
    overflow: auto;
    white-space: pre-wrap;
  }
  progress {
    width: min(320px, 100%);
    accent-color: var(--accent);
  }
  .pane :global(.spin) {
    animation: hylo-spin 1s linear infinite;
  }
</style>
