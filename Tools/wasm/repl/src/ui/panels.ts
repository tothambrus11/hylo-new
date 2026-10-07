// The dock's panels: one per view, each of the one source.

export type PanelKind = 'source' | 'output' | 'diagnostics' | 'raw-ir' | 'ir' | 'llvm' | 'assembly';

export const TITLES: Record<PanelKind, string> = {
  source: 'Source',
  output: 'Output',
  diagnostics: 'Diagnostics',
  'raw-ir': 'Raw Hylo IR',
  ir: 'Hylo IR',
  llvm: 'LLVM IR',
  assembly: 'WebAssembly',
};
