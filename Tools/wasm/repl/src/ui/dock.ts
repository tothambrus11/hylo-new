// Panel management with dockview, styled and arranged the way ABI Explorer does it: the source
// on one side and what the compiler made of it, tabbed, on the other. Every panel can be dragged,
// split and tabbed; the arrangement is remembered.

import {
  createDockview,
  type DockviewApi,
  type DockviewTheme,
  type IContentRenderer,
  type ITabRenderer,
} from 'dockview';
import 'dockview/dist/styles/dockview.css';
import { mount, unmount, type Component } from 'svelte';
import EditorPane from './EditorPane.svelte';
import OutputPanel from './OutputPanel.svelte';
import DiagnosticsPanel from './DiagnosticsPanel.svelte';
import ArtifactPanel from './ArtifactPanel.svelte';
import PanelTab from './PanelTab.svelte';
import { TITLES, type PanelKind } from './panels';

const THEME: DockviewTheme = {
  name: 'abix',
  className: 'dockview-theme-abix',
  gap: 10,
  dndOverlayMounting: 'absolute',
  dndPanelOverlay: 'group',
  dndTabIndicator: 'line',
  dndOverlayBorder: '2px solid var(--dv-active-sash-color)',
};

const LAYOUT_KEY = 'hylo-playground:layout-v1';
/** Below this many pixels of dock, groups stack rather than share a row. */
const STACK_BELOW = 760;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const COMPONENTS: Record<PanelKind, [Component<any>, Record<string, unknown>]> = {
  source: [EditorPane, {}],
  output: [OutputPanel, {}],
  diagnostics: [DiagnosticsPanel, {}],
  'raw-ir': [ArtifactPanel, { kind: 'raw-ir' }],
  ir: [ArtifactPanel, { kind: 'ir' }],
  llvm: [ArtifactPanel, { kind: 'llvm' }],
  assembly: [ArtifactPanel, { kind: 'assembly' }],
};

const RESULTS: PanelKind[] = ['output', 'diagnostics', 'ir', 'raw-ir', 'llvm', 'assembly'];

/** Fills `container` with the panels; returns a function disposing them. */
export function mountDock(container: HTMLElement): { api: DockviewApi; dispose(): void } {
  const api = createDockview(container, {
    theme: THEME,
    createComponent: (options): IContentRenderer => {
      const element = document.createElement('div');
      element.className = 'dock-panel';
      let instance: Record<string, unknown> | null = null;
      return {
        element,
        init() {
          const [component, props] = COMPONENTS[options.name as PanelKind];
          instance = mount(component, { target: element, props });
        },
        dispose() {
          if (instance) void unmount(instance);
        },
      };
    },
    createTabComponent: (options): ITabRenderer => {
      const element = document.createElement('div');
      element.className = 'dock-tab';
      let instance: Record<string, unknown> | null = null;
      return {
        element,
        init() {
          // `options.name` is the tab component's; the panel is named by its id.
          instance = mount(PanelTab, { target: element, props: { kind: options.id as PanelKind } });
        },
        dispose() {
          if (instance) void unmount(instance);
        },
      };
    },
  });

  const addDefault = (): void => {
    const stacked = container.clientWidth < STACK_BELOW;
    api.addPanel({ id: 'source', component: 'source', tabComponent: 'tab', title: TITLES.source });
    for (const [i, kind] of RESULTS.entries()) {
      api.addPanel({
        id: kind,
        component: kind,
        tabComponent: 'tab',
        title: TITLES[kind],
        inactive: i > 0,
        position:
          i === 0
            ? { referencePanel: 'source', direction: stacked ? 'below' : 'right' }
            : { referencePanel: 'output', direction: 'within' },
      });
    }
  };

  let restored = false;
  try {
    const saved = localStorage.getItem(LAYOUT_KEY);
    if (saved) {
      api.fromJSON(JSON.parse(saved));
      // A layout missing a panel (say, from an older version) is not worth keeping.
      restored = [...RESULTS, 'source'].every((k) => api.getPanel(k) !== undefined);
      if (!restored) api.clear();
    }
  } catch {
    api.clear();
  }
  if (!restored) addDefault();

  const saving = api.onDidLayoutChange(() => {
    try {
      localStorage.setItem(LAYOUT_KEY, JSON.stringify(api.toJSON()));
    } catch {
      // Not remembering the arrangement is fine.
    }
  });

  return {
    api,
    dispose() {
      saving.dispose();
      api.dispose();
    },
  };
}

/** Throws away the stored arrangement. */
export function forgetLayout(): void {
  try {
    localStorage.removeItem(LAYOUT_KEY);
  } catch {
    // Nothing stored, then.
  }
}
