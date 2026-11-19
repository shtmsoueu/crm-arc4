// @vitest-environment node
// Lê o arquivo de configuração do disco: precisa do ambiente node (no jsdom, import.meta.url não é file:).
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const config = JSON.parse(readFileSync(new URL('../vercel.json', import.meta.url), 'utf-8'));

describe('web/vercel.json', () => {
  it('repassa /api para a API antes do fallback da SPA', () => {
    const [api, spa] = config.rewrites;
    expect(api.source).toBe('/api/:path*');
    expect(api.destination).toMatch(/^https:\/\/.+\/api\/:path\*$/);
    expect(spa.destination).toBe('/index.html');
  });
});
