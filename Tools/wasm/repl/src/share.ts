// Code in a URL: `#code=` followed by the source, deflated and in base64url.
//
// The site's embedded snippets build these links to open themselves here, so the format is
// part of the playground's interface: keep `encodeSource` and the copy in hylo-lang.org's
// playground component in step.

/** Returns `source` encoded for a `#code=` fragment. */
export async function encodeSource(source: string): Promise<string> {
  const deflated = new Blob([source]).stream().pipeThrough(new CompressionStream('deflate-raw'));
  const bytes = new Uint8Array(await new Response(deflated).arrayBuffer());
  let binary = '';
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

/** Returns the source in `hash` (a URL's fragment), or null if it holds none. */
export async function decodeSource(hash: string): Promise<string | null> {
  const m = /(?:^#|&)code=([A-Za-z0-9_-]+)/.exec(hash);
  if (!m) return null;
  try {
    const binary = atob(m[1].replace(/-/g, '+').replace(/_/g, '/'));
    const bytes = Uint8Array.from(binary, (c) => c.charCodeAt(0));
    const inflated = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    return await new Response(inflated).text();
  } catch {
    return null;
  }
}
